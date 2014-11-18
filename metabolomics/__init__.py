
from datetime import date, datetime, timedelta as td
import fitbit
from errors import MyError

import numpy as np
import scipy
import math

FIRST_FITBIT_DATE=datetime(2014, 04, 20);

class Metabolomics(object):

    def __init__(self, database):
        self.database = database

    def InsertData(self, table, username, date, data):

        # Build the insertion statement
        command = "INSERT INTO " + table + " (USERNAME,DATE";
        for key in data.keys():
            command += ','+key.upper();
        command += ") VALUES (%s, %s";

        # Build tuple for parameterization
        tdata = (username, date)

        for key in data.keys():
            command += ', %s';
            tdata += (data[key],);

        command += ")";

        # Get the cursor
        cursor = self.database.GetCursor();
        cursor.execute(command, tdata)
        self.database.Commit()

    def LoadWeightData(self, filename, participants):

        with open(filename, 'Ur') as f:
            for line in f:

                tokens = line.split('\t')
                if (len(tokens)<10):
                    continue

                try:

                    username = tokens[6].strip()
                    if (not username in participants.participants):
                        continue

                    weight = float(tokens[7].strip())
                    date = tokens[8].strip() + ' ' + tokens[9].strip()
                    dt = datetime.strptime(date, "%m/%d/%y %I:%M %p")

                    data = {'WEIGHT': weight}

                    # Check to see if this date is after the last date in the database
                    if (self.CheckDate('weight', username, dt)):
                        self.InsertData('weight', username, dt, data);

                except:
                    pass

    def CreateMetabolitesTable(self, filename):

        command = ""
        command += "CREATE TABLE metabolites (COMP_ID INT PRIMARY KEY, BIOCHEMICAL VARCHAR(256), SUPER_PATHWAY VARCHAR(256), " \
                   "SUB_PATHWAY VARCHAR(256), PLATFORM  VARCHAR(256), CHEMICAL_ID INT, RI FLOAT, MASS FLOAT, CAS VARCHAR(256)," \
                   "PUBCHEM INT, KEGG VARCHAR(256), HMDB VARCHAR(256))"

        #self.database.Command(command)

        keys = ['BIOCHEMICAL', 'SUPER_PATHWAY', 'SUB_PATHWAY', 'COMP_ID', 'PLATFORM', 'CHEMICAL_ID', 'RI', 'MASS', 'CAS', 'PUBCHEM', 'KEGG', 'HMDB']

        with open(filename, 'rU') as f:
            for line in f:

                tokens = line.split('\t')
                try:
                    comp_id = int(tokens[4])

                except:
                    continue

                # Zip the data up
                data = dict(zip(keys, tokens[1:12]))

                print data

                """
                # Build the insertion statement
                command = "INSERT INTO " + table + " (COMP_ID, BIOCHEMICAL, SUPER_PATHWAY, SUB_PATHWAY, PLATFORM, CHEMICAL_ID, RI, MASS, CAS, PUBCHEM, KEGG, HMDB""
                for key in data.keys():
                    command += ','+key.upper();
                command += ") VALUES (%s, %s";

                # Build tuple for parameterization
                tdata = (username, date)

                for key in data.keys():
                    command += ', %s';
                    tdata += (data[key],);

                command += ")";

                # Get the cursor
                cursor = self.database.GetCursor();
                cursor.execute(command, tdata)
                self.database.Commit()
                """


        #command = ""
        #command += "CREATE TABLE metabolomics (ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, DATE DATETIME NOT NULL, \

        # First create columns
        #self.database.Command(command)