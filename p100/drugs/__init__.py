# System imports
from datetime import date, datetime, timedelta as td
import logging

from p100.errors import MyError

import numpy as np
import scipy
import math, re
import pandas, pandas.io

# Codebase imports
from p100.errors import MyError
import time

l_logger = logging.getLogger("p100.drugs")

class Drugs(object):
    def __init__( self, database ):
        l_logger.debug("Creating a Drugs object")
        self.database = database

    def GetData( self, username=None, round=None, observation_id= None,
            drug_name=None, drug_id=None, rxNormIds=None):
        """
        Returns a dataframe with the drug data for a given user and
        round(if provided).

        drug_id - a single drug id (database key) 
        rxNormIds - a list of rxnormIds

        """
        
        l_logger.debug("GetData( %s, %s, %s )" % ( username, round, observation_id  ))
        q_string = """SELECT ro.observation_id, ro.username, ro.round, rd.name, rd.drug_id,
        rd.rxNormID, rv.raw as raw_name
        FROM rx_observations ro, rx_drugs rd, rx_values rv
        WHERE ro.observation_id = rv.observation_id AND
            rd.drug_id = rv.drug_id
        """
        conditions = []
        var_tup = []
        if username is not None:
            conditions.append('ro.username = %s')
            var_tup.append(username)
        if round is not None:
            conditions.append('ro.round = %s')
            var_tup.append(round)
        if observation_id is not None:
            conditions.append('ro.observation_id = %s')
            var_tup.append( observation_id )
        if drug_name is not None:
            conditions.append('rd.name = %s')
            var_tup.append(drug_name)
        if drug_id is not None:
            conditions.append('rd.drug_id = %s')
            var_tup.append( drug_id )
        if rxNormIds is not None:
            temp_str = ','.join(['%s' for x in rxNormIds])
            conditions.append('rd.rxNormID in (' + temp_str + ')')
            var_tup += rxNormIds

        q_string = ' and '.join( [q_string] + conditions )
        var_tup = tuple( var_tup )
        return self.database.GetDataFrame( q_string, var_tup )

    
