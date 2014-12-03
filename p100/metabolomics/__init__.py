
# System imports
from datetime import date, datetime, timedelta as td
import numpy as np
import scipy
import math, re
import pandas, pandas.io

# Codebase imports
from p100.errors import MyError

class Metabolomics(object):

    def __init__(self, database):
        self.database = database

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

