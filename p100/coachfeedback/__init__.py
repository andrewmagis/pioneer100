

# System imports
from datetime import date, datetime, timedelta as td
import logging

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
l_logger = logging.getLogger("p100.coachfeedback")

class Feedback(DataFrameOps):
    def __init__(self, database):
        l_logger.debug("Creating a feedback object")
        self.database = database

    def GetData( self, username=None, round=None, feedback_id=None):
        l_logger.debug("GetData(%s, %s, %s)" % (username, round, feedback_id) )
        q_string = """
            SELECT cfo.username, cfo.round, cfv.value, cfd.datatype, cf.description, cf.feedback_id,
                cfv.cf_values_id, cfd.datatype_id, cfo.observation_id
            FROM coach_feedback_datatype cfd,
            coach_feedback cf,
            coach_feedback_values cfv,
            coach_feedback_observations cfo
            WHERE cfd.datatype_id = cf.datatype_id AND
                cf.feedback_id = cfv.feedback_id AND
                cfo.observation_id = cfv.observation_id
        """
        conditions = []
        var_tup = []
        if username is not None:
            conditions.append('cfo.username = %s')
            var_tup += [username]
        if round is not None:
            conditions.append('cfo.round = %s')
            var_tup += [round]
        if feedback_id is not None:
            conditions.append( 'cf.feedback_id = %s' )
            var_tup += [feedback_id]

        q_string = ' and '.join( [ q_string ] + conditions )
        return self.database.GetDataFrame( q_string, tuple(var_tup) )

    def GetDatatypes( self ):
        """
        returns a dict of the available datatypes, {datatype_id, Datatype}
        """
        q_string = """SELECT datatype_id, datatype from coach_feedback_datatype"""
        dt_df = self.database.GetDataFrame( q_string ).set_index('datatype_id')
        return dt_df.to_dict()['datatype']

    def GetCategories(self, feedback_id):
        q_string = """ 
            SELECT DISTINCT value 
            FROM coach_feedback_values
            WHERE feedback_id = %s
        """
        return self.database.GetDataFrame( q_string, ( feedback_id ) )

    def GetFeedbackDescriptions( self, feedback_id=None ):
        q_string = """
        SELECT cf.feedback_id, cf.description, cf.datatype_id, cfd.datatype
        FROM coach_feedback cf, coach_feedback_datatype cfd
        WHERE cfd.datatype_id = cf.datatype_id"""
        if feedback_id is not None:
            q_string += " and feedback_id = %s"
            var_tup = (feedback_id,)
        else:
            var_tup = None

        return self.database.GetDataFrame( q_string,var_tup )

    def _check_datatype( self,  value, datatype_id=None,feedback_id=None):
        if feedback_id is not None:
            q_string = """ SELECT datatype_id from coach_feedback where feedback_id = %s """
            curr = self.database.GetDataFrame(q_string,  (feedback_id, ))
            if curr is not None:
                datatype_id = curr['datatype_id'].unique()[0]
        if datatype_id is None:
            raise MyError("Datatype_id and feedback_id invalid[%s,%s]" % ( datatype_id, feedback_id) )
        elif datatype_id == 1:#INTEGER
            try:
                v = "%i" % int(value)
            except ValueError:
                raise MyError("Expected integer and received [%s]" % (value))
        elif datatype_id == 2:#BINARY
            try:
                v = "%i" % int(value)
                if int(v) not in [0,1]:
                    raise MyError("Expected binary {0,1} and received [%s]" % (value))
            except ValueError:
                raise MyError("Expected binary {0,1} and received [%s]" % (value))
        elif datatype_id == 3:#Float
            try:
                v = "%f" % float(value)
            except ValueError:
                raise MyError("Expected real and received [%s]" % (value))
        elif datatype_id == 4: #categorical
            v = value.strip()
        else:
            raise MyError("Unknown datatype_id [%s]" % datatype_id )
        return v

    def AddObservation( self, username, round ):
        q_string = """SELECT distinct observation_id 
                    from coach_feedback_observations
                    WHERE username = %s and round = %s
                    """
        curr = self.database.GetDataFrame(q_string,  (username, round))
        if curr is not None:
            return curr['observation_id'].unique()[0]
        cursor = self.database.GetCursor()
        q_string = """INSERT into coach_feedback_observations( username, round ) VALUES( %s, %s ) RETURNING observation_id"""
        cursor.execute( q_string, (username, round ))
        return cursor.fetchone()[0]

    def AddFeedback(self, description, datatype_id):
        description = description.strip()
        datatype_id = int(datatype_id)
        assert datatype_id in self.GetDatatypes().iterkeys(), "datatype_id is bad"

        q_string = """SELECT feedback_id 
                    from coach_feedback
                    WHERE description = %s and datatype_id=%s
                    """
        curr = self.database.GetDataFrame(q_string, (description, datatype_id))
        if curr is not None:
            return curr['feedback_id'].unique()[0]
        cursor = self.database.GetCursor()
        q_string = """INSERT into coach_feedback( description, datatype_id ) VALUES( %s, %s ) RETURNING feedback_id"""
        cursor.execute( q_string,  (description, datatype_id))
        return cursor.fetchone()[0]


    def AddValue( self, feedback_id, observation_id, value):
        self._check_datatype( value=value, feedback_id=feedback_id)

        q_string = """SELECT cf_values_id
                    from coach_feedback_values cfv, coach_feedback cf
                    WHERE cfv.feedback_id = %s and cfv.observation_id=%s and cf.datatype_id != 4
                    and cfv.feedback_id = cf.feedback_id
                    """
        curr = self.database.GetDataFrame(q_string, ( feedback_id, observation_id))
        if curr is not None:
            vid =  curr['cf_values_id'].unique()[0]
            q_string = """
            UPDATE coach_feedback_values
            SET value = %s
            WHERE cf_values_id = %s """
            tup = ( vid, value )
            l_logger.debug( "%s, %r" % (q_string, tup) )
            cursor = self.database.GetCursor()
            cursor.execute( q_string,tup )
            return vid
        else:
            q_string = """INSERT INTO coach_feedback_values(observation_id, feedback_id, value )
                VALUES(%s,%s,%s)
                RETURNING cf_values_id
                """
            tup =  (observation_id, feedback_id, value)
            cursor = self.database.GetCursor()
            cursor.execute( q_string,tup )
            return cursor.fetchone()[0]

    def DeleteValue( self, cf_values_id ):
        q_string = """
        DELETE
        FROM coach_feedback_values
        WHERE cf_values_id = %s"""
        tup = ( int(cf_values_id), )
        l_logger.debug( "%s, %r" % (q_string, tup) )
        cursor = self.database.GetCursor()
        cursor.execute( q_string,tup )


    def _cleanup(self):
        q_string = """DELETE from coach_feedback_values WHERE 1=1"""
        cursor = self.database.GetCursor()
        cursor.execute( q_string, None )
        q_string = """DELETE from coach_feedback WHERE 1=1"""
        cursor.execute( q_string, None )
        q_string = """DELETE from coach_feedback_observations WHERE 1=1"""
        cursor.execute( q_string, None )



