
# System imports
from datetime import date, datetime, timedelta as td
import logging

import fitbit
from p100.errors import MyError

import numpy as np
import scipy
import math, re
import pandas, pandas.io
from ete2 import Tree

# Codebase imports
from p100.errors import MyError
from p100.utils.dataframeops import DataFrameOps
import time

l_logger = logging.getLogger("p100.microbiome")

class Microbiome(DataFrameOps):
    tax = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
    def __init__(self, database):
        l_logger.debug("Creating a Microbiome object")
        self.database = database

    def GetData(self,username=None, rnd=None, agg_to='species',
            perc=True, observation_id=None, vectorize=False,
            correlize=False):
        """
        Returns a dataframe with the microbiomic data for
        a given user and round(if provided) aggregated to the agg_to
        level.  If perc is true, the it returns the aggregated
        percentages, otherwise the counts.
        """

        l_logger.debug("GetData( %s, %s, %s, %s  )" %( username, rnd,  agg_to, perc))
        cut = self.tax.index(agg_to) + 1
        #the trimmed list of taxonomies
        tr_tax = self.tax[:cut]
        #this part puts together the bits needed to get the taxonomic
        #SELECT .
        #select_stmt = ['%s.tax_label AS %s' % (t[:3], t) for t in tr_tax]#labels
        select_stmt = ['tx.%s as %s_id' % (t,t) for t in tr_tax]#ids
        select_stmt += [ 'obs.observation_id', 'obs.username', 'obs.round' ]
        group_stmt = ['tx.%s' % (t,) for t in tr_tax]#ids
        group_stmt += [ 'obs.observation_id', 'obs.username', 'obs.round' ]

        if perc:
            select_stmt += ["SUM(lvl.percentage) as value"]
        else:
            select_stmt += ["SUM(lvl.read_counts) as value"]
        #FROM
        from_stmt = ['mb_observation obs', 'mb_taxonomy tx', 'mb_levels lvl']
        #WHERE
        where_stmt = ['obs.observation_id = lvl.observation_id', 
                       'tx.taxonomy_id = lvl.taxonomy_id', 'lvl.read_counts > 0']
        #GROUP
        #group_stmt = [ "obs.observation_id" ] + ['%s_id' % t for  t in tr_tax]

        #variables
        var_list = []

        if observation_id:
            where_stmt +=  ["obs.observation_id"]
            var_list += [int(observation_id)]
        if username:
            where_stmt +=  ["obs.username = %s"]
            var_list += [str(int(username))]
        if rnd:
            where_stmt +=  ["obs.round = %s"]
            var_list += [int(rnd)]
        var_tup = tuple( var_list )

        statements = (', '.join( select_stmt ), ', '.join( from_stmt ), 
                ' and '.join( where_stmt ), ', '.join( group_stmt ) )

        q_string = """
        SELECT %s
        FROM %s
        WHERE %s
        GROUP BY %s
        """ % (', '.join( select_stmt ), ', '.join( from_stmt ), 
                ' and '.join( where_stmt ), ', '.join( group_stmt ) )

        res = self.database.GetDataFrame(q_string, var_tup)
        #reorder the columns, they get messy
        column_order = ['observation_id', 'username', 'round']
        #column_order += tr_tax 
        column_order += ["%s_id" % x for x in tr_tax]
        column_order += ['value']
        column_order += [x for x in res.columns if x not in column_order]
        
        in_str = '(' + ','.join( ['%s' for x in tr_tax] ) + ')'
        q_string = """
        SELECT tax_label_id, tax_label
        FROM mb_taxonomy_labels
        WHERE tax_level IN %s """ % in_str
        df = self.database.GetDataFrame( q_string, tuple( tr_tax ) )
        for tax in tr_tax:
            df.columns = [tax, 'tax_label_id']
            res = res.join(df.set_index('tax_label_id'), on='%s_id' % tax)

        column_order = ['observation_id', 'username', 'round']
        column_order += tr_tax 
        column_order += ["%s_id" % x for x in tr_tax]
        column_order += ['value']
        column_order += [x for x in res.columns if x not in column_order]
        result = res[column_order]
        if vectorize:
            return self.username_vectors( result ).transpose()
        elif correlize:
            return self.correlize(result)
        else:
            return result

    def correlize(self,dataframe ):
        utax =  [x for x in self.tax if x in dataframe.columns]
        final = ["%s_id" %x for x in utax]
        dataframe = dataframe.copy()
        dataframe['uname_rnd'] = dataframe.apply(lambda x: x['username'] + '_' +str(x['round']), axis=1)
        dataframe['unique_row'] = dataframe.apply(lambda x: ','.join([str(x[f]) for f in final]), axis=1)
        return  dataframe[['uname_rnd','unique_row' , 'value']].pivot(index='uname_rnd', columns='unique_row', values='value')

    def get_correlize_map( self, agg_to='phylum' ):
        dataframe = self.GetData( agg_to=agg_to )
        sub_tax = [x for x in self.tax if x in dataframe.columns and x != agg_to ]
        dataframe['unique_row'] = dataframe.apply(lambda row: '>'.join([row['%s'%x][:3] for x in sub_tax] + [row[agg_to]]), axis=1)
        mymap = {}
        sub_tax += [agg_to]
        sub_tax += ["%s_id"%x for x in sub_tax]
        for i, row in dataframe.iterrows():
            mm = mymap[row['unique_row']] = {}
            for st in sub_tax:
                mm[st] = row[st]
        return mymap

    def _compress_mb(self,row, agg_to):
        sub_tax = [x for x in self.tax if x in row.columns and x != agg_to ]

        return '>'.join([row['%s'%x][:3] for x in sub_tax] + [row[agg_to]])

    def get_taxonomy_names(self, up_to=None):
        if up_to:
            return self.tax[:(self.tax.index(up_to) + 1)]
        else:
            return self.tax

    def username_vectors( self, dataframe):
        """
        Given a dataframe as generated by GetData,
            return a new dataframe where the index
            is a string representation of the full path to the
            taxa and the column name is the username,
            or username-round in the case of multiple rounds
        """
        utax =  [x for x in self.tax if x in dataframe.columns]
        unames = dataframe.username.unique()
        rnds = dataframe['round'].unique()

        result = {}
        for uname in unames:
            for rnd in rnds:
                udf = dataframe[(dataframe.username == uname) &
                        (dataframe['round'] == rnd)]
                if len(udf.index)>0:
                    d = udf[utax + ['value']].to_dict(orient="split")['data']
                    if len(rnds) > 1:
                        key = "%s_%i" % (uname, rnd)
                    else:
                        key = uname
                    result[key] = {}
                    for row in d:
                        trimmed = [a[:3] for a in row[:-2]] + row[-2:-1]
                        sub_key = '>'.join( trimmed )
                        result[key][sub_key] =  row[-1]
        return pandas.DataFrame.from_dict( result )

    def GetUnifracScore(self, observation_ids = None, usernames = None,
            rounds = None, weighted=True):
        """
        returns the unifrac scores associated with the given by the
        inputs
        Note, it is observation_ids or usernames or usernames and
        rounds

        for example to compare username 555 between r1 and r2

        uf = mic.GetUnifracScore( usernames=('555', '555'),
        rounds=(1,2) )

        to get 2 different observations

        uf = miv.GetUnifracScore( observation_ids=(1,2) )
        """

        q_string = """
        SELECT   o1.observation_id as observation_id1, o1.username as username1, o1.round as round1, 
                 o2.observation_id as observation_id2, o2.username as username2, o2.round as round2, 
                 u.weighted as value
        FROM mb_observation o1, mb_observation o2, mb_unifrac u
        WHERE o1.observation_id = u.observation_id_1 and
        o2.observation_id = u.observation_id_2"""
        where_stmt = []
        forward = []
        backward = []
        if usernames is not None and len(usernames) == 2:
            where_stmt.append("( (o1.username = %s) and (o2.username = %s))")
            forward += list( usernames )
            backward += list(  usernames[::-1] )
        if rounds is not None and len(rounds) == 2:
            where_stmt.append( "( (o1.round = %s )  and (o2.round = %s))")
            forward += list(  rounds )
            backward += list(  rounds[::-1] )
        if observation_ids is not None and len(observation_ids) == 2:
            where_stmt.append( "( (o1.observation_id = %s )  and (o2.observation_id = %s))")
            forward += list(  observation_ids )
            backward += list(  observation_ids[::-1] )

        forward_stmt = '(' + ' AND '.join( where_stmt) + ')' 
        forward_stmt += ' OR ' + forward_stmt 
        if len(forward) > 0:
            q_string += ' AND (' + forward_stmt + ')'    
        args = tuple( forward + backward )
        return self.database.GetDataFrame( q_string, args )

    def GetUnifracMatrix(self, by_uname_rnd=False):
        """
        Returns the complete unifrac matrix

        if by_uname_rnd
            returns the matrix indexed by username-round
        """
        def map1_name_rnd( row):
            return "%s-%i" % (row.username1, row.round1)
        def map2_name_rnd( row ):
            return "%s-%i" % (row.username2, row.round2)
        uf = self.GetUnifracScore()
        if by_uname_rnd:
            uf['ur1'] = uf.apply(map1_name_rnd, axis=1)
            uf['ur2'] = uf.apply(map2_name_rnd, axis=1)
            new_us = uf.pivot(index='ur1',
                columns='ur2', values='value')
        else:
            new_us = uf.pivot(index='observation_id1',
                columns='observation_id2', values='value')
        new_us[new_us.index[0]] = np.nan
        new_us = new_us[new_us.index.tolist()].fillna(0.0)
        new_us = new_us + new_us.transpose()
        return new_us
