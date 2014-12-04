
# System imports
from datetime import date, datetime, timedelta as td
import logging

import fitbit
from p100.errors import MyError

import numpy as np
import scipy
import math, re
import pandas, pandas.io

# Codebase imports
from p100.errors import MyError

logger = logging.getLogger("p100.metabolomics")
class Metabolomics(object):
    def __init__(self, database):
        logger.debug("Creating a Metabolomics object")
        self.database = database

    def GetData(self, username=None, round=None):
        """
        Returns a dataframe with the metabolomic data for
        a given user and round(if provided).
        """
        logger.debug("GetData( %s, %s )" %(username, round))
        q_string = """
        SELECT mo.username, mo.round, imputed as value, biochemical as metabolite_name,
                super_pathway, sub_pathway, hmdb
        FROM meta_values mv, meta_observation mo, meta_metabolite mm
        WHERE mm.metabolite_id = mv.metabolite_id
        and mo.observation_id = mv.observation_id"""
        if username is None:
            var_tup = []
        else:
            q_string += " and mo.username = %s "
            var_tup = [username]

        if round is not None:
            q_string += " and mo.round = %s"
            var_tup += [round]
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

