
# System imports
from datetime import date, datetime, timedelta as td
import logging

import fitbit
from p100.errors import MyError

import numpy as np
import scipy
import math, re
import pandas, pandas.io
import statsmodels
import scipy.stats as scistats

# Codebase imports
from p100.errors import MyError
from p100.utils.dataframeops import DataFrameOps
from multiprocessing import Pool

l_logger = logging.getLogger("p100.metabolomics")

def partition_dataframe(dataframe,  username_set_1, username_set_2=None):
    limited_df = dataframe.set_index('username', drop=False)
    set_1_limited_df = limited_df.loc[username_set_1]
    #remove where we have no record for usernames, otherwise fubars difference
    set_1_limited_df = set_1_limited_df.dropna(axis=0) 
    if username_set_2 is None:
        set_2_limited_df = limited_df.drop(set_1_limited_df.index)
    else:
        set_2_limited_df = limited_df.loc[username_set_2]
        #remove where we have no record for usernames
        set_2_limited_df = set_2_limited_df.dropna(axis=0) 
    return (set_1_limited_df, set_2_limited_df )

def sub_part( args ):
    def _map_uname_rnd( row):
        #print row
        return "%s-%i" % (row['username'], row['round'])
    df, met_id, username_set_1, username_set_2, round = args
    limited_df = df[df.metabolite_id == met_id]
    if round is None:
        cut_dfs = []
        for rnd in limited_df['round'].unique():
            rnd_df = limited_df[limited_df['round'] == rnd]
            (s1l_df, s2l_df) = partition_dataframe( rnd_df, username_set_1, username_set_2 )
            s1l_df['uname_rnd'] = s1l_df.apply( _map_uname_rnd, axis=1 )
            s2l_df['uname_rnd'] = s2l_df.apply( _map_uname_rnd, axis=1 )
            s1l_df = s1l_df.set_index('uname_rnd')
            s2l_df = s2l_df.set_index('uname_rnd')
            cut_dfs.append(( s1l_df, s2l_df ))
        set_1_limited_df = pandas.concat( [a for a,_ in cut_dfs], axis=0 )
        set_2_limited_df = pandas.concat( [b for _,b in cut_dfs], axis=0 )
    else:
        (s1l_df, s2l_df) = partition_dataframe( limited_df, username_set_1, username_set_2 )

        s1l_df['uname_rnd'] = s1l_df.apply( _map_uname_rnd, axis=1 )
        s2l_df['uname_rnd'] = s2l_df.apply( _map_uname_rnd, axis=1 )
        s1l_df = s1l_df.set_index('uname_rnd')
        s2l_df = s2l_df.set_index('uname_rnd')

        set_1_limited_df, set_2_limited_df = s1l_df, s2l_df
    return (set_1_limited_df, set_2_limited_df)
            
class Metabolomics(DataFrameOps):

    def __init__(self, database):
        l_logger.debug("Creating a Metabolomics object")
        self.database = database

    def GetData(self, username=None, round=None, metabolite_id=None):
        """
        Returns a dataframe with the metabolomic data for
        a given user and round(if provided).
        """
        l_logger.debug("GetData( %s, %s )" %(username, round))
        q_string = """
        SELECT mo.observation_id, mo.username, mo.round, imputed as value, biochemical as metabolite_name,
                super_pathway, sub_pathway, hmdb, mm.metabolite_id
        FROM meta_values mv, meta_observation mo, meta_metabolite mm
        WHERE mm.metabolite_id = mv.metabolite_id
        and mo.observation_id = mv.observation_id
        """

        conditions = []
        var_tup = []
        if username is not None:
            conditions.append("mo.username = %s ")
            var_tup += [username]
        if round is not None:
            conditions.append("mo.round = %s")
            var_tup += [round]
        if metabolite_id is not None:
            conditions.append("mm.metabolite_id = %s")
            var_tup += [metabolite_id]
        q_string = ' and '.join( [ q_string ] + conditions )
        return self.database.GetDataFrame( q_string, tuple(var_tup) )

    def GetAssociationsByUsername(self, username_set_1, username_set_2=None, round=None, nprocs=5):
        """
        Given a set(or 2 sets) of usernames, return the t-test and ranksums
        for that partitioning. Also returns the benjamini-hochberg corrections for both


        Given a single username set, returns comparison for that set and the difference of the whole set.

        round - restricts the results to a single round

        Returns a dataframe containing results for each metabolite
        
        Note on z/t-scores:
            if negative then set_1 has the higher values and vice-versa
        """
        met_results = []
        l_logger.debug("Partitioning tables")
        partitions = self.GetPartitionsByUsername( username_set_1, username_set_2, round, nprocs=nprocs )
        l_logger.debug("Calculating statistics")
        for set_1_limited_df, set_2_limited_df in partitions:
            zstat, pval = scistats.ranksums( set_2_limited_df['value'], set_1_limited_df['value'] )
            tscore, tpval = scistats.ttest_ind( set_2_limited_df['value'], set_1_limited_df['value'] )
            met_info = {'met_id': set_2_limited_df['metabolite_id'][0], 
             'met_name':set_2_limited_df['metabolite_name'][0], 
             'n_set_1': len(set_1_limited_df['metabolite_name']),
             'n_set_2': len(set_2_limited_df['metabolite_name']),
             'rsum_p_value': pval,
             'rsum_zstat':zstat,
             'ttest_p_value': tpval,
             'ttest_t_score': tscore,
             'set_1_mean' : set_1_limited_df['value'].mean(),
             'set_2_mean' : set_2_limited_df['value'].mean()
             }
            met_results.append(met_info)
        met_df = pandas.DataFrame(met_results)
        #shortcut
        mt = statsmodels.sandbox.stats.multicomp.multipletests
        (accepted, corrected, unused1, unused2) = mt(met_df['rsum_p_value'].fillna(1), method="fdr_bh")
        met_df['rsum_corrected'] = corrected
        met_df['rsum_rejected'] = accepted
        (accepted, corrected, unused1, unused2) =mt(met_df['ttest_p_value'].fillna(1), method="fdr_bh")
        met_df['ttest_corrected'] = corrected
        met_df['ttest_rejected'] = accepted

        return met_df

    def GetPartitionsByUsername( self, username_set_1, username_set_2=None, round=None, met_id = None, df=None, nprocs=5):
        """
        Given a set(or 2 sets) of usernames for thatr returns a list of dataframe pairs for that partitioning.

        i.e. [(set_1_df_met_1, set_2_df_met_1),(set_1_df_met_2, set_2_df_met_2), ... ]

        Options
        -------
        Given a single username set, returns comparison for that set and the difference of the whole set.
        met_id - only performs partitioning for that metabolite (default:all)
        round - restricts the results to a single round (default:all)
        df - performs partitioning on given dataframe (i.e. you have your own subset)
        """


        l_logger.debug("GetPartitionsByUsername(%r,%r,%r,%r,%r,%r)" %(username_set_1, username_set_2,
                round, met_id , df, nprocs))
        if df is None:
            df = self.GetData(round=round,metabolite_id=met_id)
        ids = df.metabolite_id.unique()
        p = Pool(nprocs)
        #note the sub_part function is declared at the top of the module and is not
        #part of the class.
        #this is necessary in order to get the subprocess map to work
        #from some cheap hand tuning, appears to top out at 5
        return p.map( sub_part, [  (df, met_id, username_set_1, username_set_2, round) for met_id in ids ] )

    def _map_uname_rnd(self, row):
        #print row
        return "%s-%i" % (row['username'], row['round'])

    def _get_field_by_name(self, round, field_name):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username, v.imputed "
                       "FROM meta_observation as o, meta_values as v, meta_metabolite as m "
                       "WHERE o.round = (%s) "
                       "AND m.biochemical = (%s) "
                       "AND v.metabolite_id = m.metabolite_id "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY o.username", (round,field_name,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('username', str, 8), (field_name, float)])

        # Build pandas Series
        return pandas.DataFrame(array[field_name], index=array['username'], columns=[field_name])

    def _get_field_by_id(self, round, field_id):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username, v.imputed "
                       "FROM meta_observation as o, meta_values as v "
                       "WHERE o.round = (%s) "
                       "AND v.metabolite_id = (%s) "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY o.username", (round,field_id,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('username', str, 8), (str(field_id), float)])

        # Build pandas Series
        return pandas.DataFrame(array[str(field_id)], index=array['username'], columns=[str(field_id)])

    def _get_all_signrank(self, roundA, roundB):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT biochemical "
                       "FROM meta_metabolite")

        headers = np.array(list(cursor.fetchall()), dtype=[('name', str, 128)])

        result = []
        names = []
        # Now loop over the database and retrieve all of it for this round
        for name in headers['name']:

            # Perform the signed rank test (non-parametric)
            result.append(self._get_signrank_by_name(roundA, roundB, name))
            names.append(name)

        # Create the np array
        array = np.array(result, dtype=[('z_value', float), ('p_value', float), ('meanA', float), ('meanB', float), ('stdA', float), ('stdB', float)])
        (accepted, corrected, unused1, unused2) = statsmodels.sandbox.stats.multicomp.multipletests(array['p_value'], method="fdr_bh")

        # Build pandas dataframe with corrected p-values
        temp = pandas.DataFrame(array, index=names, columns=['z_value', 'p_value', 'fdr', 'meanA', 'meanB', 'stdA', 'stdB'])
        temp['fdr'] = pandas.Series(corrected, index=temp.index)
        return temp.sort('fdr', ascending=True)

    def _get_all_fields(self, round):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT biochemical "
                       "FROM meta_metabolite")

        headers = np.array(list(cursor.fetchall()), dtype=[('name', str, 128)])

        result = None
        # Now loop over the database and retrieve all of it for this round
        for name in headers['name']:

            current = self._get_field_by_name(round, name)
            if (result is None):
                result = current
            else:
                result = result.join(current, how='outer')

        return result

    def _get_participant_by_name(self, round, username):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT c.biochemical, v.imputed "
                       "FROM meta_observation as o, meta_values as v, meta_metabolite as c "
                       "WHERE o.round = (%s) "
                       "AND o.username = (%s) "
                       "AND v.metabolite_id = c.metabolite_id "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY c.biochemical", (round,username,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('metabolite', str, 128), (str(username), float)])

        # Build pandas Series
        return pandas.DataFrame(array[str(username)], index=array['metabolite'], columns=[str(username)])

    def _get_all_participants(self, round):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT username "
                       "FROM participants")

        headers = np.array(list(cursor.fetchall()), dtype=[('username', str, 128)])

        result = None
        # Now loop over the database and retrieve all of it for this round
        for username in headers['username']:

            current = self._get_participant_by_name(round, username)
            if (result is None):
                result = current
            else:
                result = result.join(current, how='outer')

        return result
