
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

# Codebase imports
from p100.errors import MyError
from p100.utils.dataframeops import DataFrameOps

l_logger = logging.getLogger("p100.metabolomics")

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
        SELECT mo.username, mo.round, imputed as value, biochemical as metabolite_name,
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
        var_tup = tuple( var_tup )
        return self.database.GetDataFrame( q_string, tuple(var_tup) )

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
