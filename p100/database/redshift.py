REGION = 'us-west-2'
BUCKET = 'p100-analytics'
CREDENTIALS = 'redshift-credentials-2015-02-26'

import logging
from psycopg2 import ProgrammingError, OperationalError, InterfaceError, InternalError
import psycopg2 as mdb
import pandas

import numpy as np
import datetime, re
from csv import reader

from p100.database import Database
from p100.errors import MyError
from p100.utils.botoops import BotoOps

l_logger = logging.getLogger("p100.database.redshift")

class Redshift(Database):

    def __init__(self, host=None, user=None, passwd=None, db=None,
                    port=None, credentials=CREDENTIALS, bucket=BUCKET, region=REGION):
        if user is None and credentials is not None:
            cred = BotoOps().get_credentials( credentials, bucket, region)
            self.host = cred['host']
            self.user = cred['user']
            self.passwd = cred['password']
            self.port = cred['port']
            self.db_name = cred['database']
        else:
            self.host, self.user, self.passwd, self.db_name, self.port = host,user,passwd,db,port
        self._db = None
        l_logger.debug( "DataBase %s,%s,%s" % (self.host, self.user, self.db_name ))

    def __del__(self):
        # Close the database
        self.db.close()

    def Test(self):

        cursor = self.db.cursor()

        cursor.execute("SELECT chrom, pos, ref, alt FROM vcf WHERE chrom= '1' AND pos > 1000000 AND pos < 1001000")

        for e in cursor:
            print e