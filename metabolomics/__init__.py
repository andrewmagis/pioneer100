
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

    def Clean(self, value):

        new_value = value.strip().strip("'").strip('"')
        if (len(new_value) == 0):
            return None
        return new_value

    def LoadMetabolomicsData(self, filename):

        data = {}
        mets = []
        date_mapping = {}

        with open(filename, 'rU') as f:
            for line in f:

                tokens = line.split('\t')
                if (tokens[12]=='CLIENT IDENTIFIER'):
                    usernames = line.strip().split('\t')[1:]
                    usernames = [x.split('-')[0] for x in usernames]

                elif (tokens[12]=='DRAW NO'):
                    rounds = line.strip().split('\t')[1:]

                elif (tokens[12]=='COLLECTION DATE'):
                    dates = line.strip().split('\t')[1:]

                    dates_final = []
                    for date in dates:
                        try:
                            d = datetime.strptime(date, "%d/%m/%y")
                        except:
                            d = datetime.strptime(date, "%d-%m-%y")
                        dates_final.append(d)

                elif (len(tokens[0])>0) and (tokens[0] != "PATHWAY SORTORDER"):

                    mets.append('M' + tokens[4])
                    mdata = tokens[13:]

                    # Add this data to the dictionary by round
                    for username, round, date, d in zip(usernames, rounds, dates_final, mdata):

                        if (not username in data):
                            data[username] = {}

                        if (not round in data[username]):
                            data[username][round] = []

                        # Now append to the list
                        data[username][round].append(d)

                        if (not username in date_mapping):
                            date_mapping[username] = {}

                        if (not round in date_mapping[username]):
                            date_mapping[username][round] = date

        # Now zip up the data
        for username in data:

            for round in data[username]:

                # Zip up the data with the metabolite names
                current = dict(zip(mets, data[username][round]))

                # Now build the insertion statement
                command = "INSERT INTO metabolomics (USERNAME, DATE, ROUND"
                for key in current.keys():
                    command += ',' + key.upper()
                command += ") VALUES (%s, %s, %s";

                # Build tuple for parameterization
                tdata = [username, date_mapping[username][round], round]

                for key in current.keys():
                    command += ',' + '%s';
                    tdata.append(self.Clean(current[key]));

                command += ")";

                print command
                return

                # Get the cursor
                #cursor = self.database.GetCursor();
                #cursor.execute(command, tuple(tdata))
                #self.database.Commit()


    def CreateMetabolomicsTable(self, filename):

        command = "";
        command += "CREATE TABLE metabolomics (ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, DATE DATETIME, ROUND INT NOT NULL"

        cursor = self.database.GetCursor();
        result = cursor.execute("SELECT COMP_ID from metabolites")
        for comp_id in cursor:
            command += ", %s FLOAT"%(comp_id)
        command += ")"

        print command
        cursor.execute(command)
        self.database.Commit()

    def CreateMetabolitesTable(self, filename):

        command = ""
        command += "CREATE TABLE metabolites (COMP_ID VARCHAR(16) PRIMARY KEY, BIOCHEMICAL VARCHAR(256), SUPER_PATHWAY VARCHAR(256), " \
                   "SUB_PATHWAY VARCHAR(256), PLATFORM  VARCHAR(256), CHEMICAL_ID INT, RI FLOAT, MASS FLOAT, CAS VARCHAR(256)," \
                   "PUBCHEM INT, KEGG VARCHAR(256), HMDB VARCHAR(256))"

        self.database.Command(command)

        keys = ['BIOCHEMICAL', 'SUPER_PATHWAY', 'SUB_PATHWAY', 'COMP_ID', 'PLATFORM', 'CHEMICAL_ID', 'RI', 'MASS', 'CAS', 'PUBCHEM', 'KEGG', 'HMDB']

        with open(filename, 'rU') as f:
            for line in f:

                tokens = line.split('\t')
                try:
                    comp_id = int(tokens[4])

                except:
                    continue

                # Zip the data up
                data = dict(zip(keys, tokens[1:13]))

                # Build the insertion statement
                command = "INSERT INTO metabolites (COMP_ID"
                for key in data.keys()[1:]:
                    command += ',' + key.upper()
                command += ") VALUES (%s";

                # Build tuple for parameterization
                tdata = ['M'+data['COMP_ID']]

                for key in data.keys()[1:]:
                    command += ',' + '%s';
                    tdata.append(self.Clean(data[key]));

                command += ")";

                # Get the cursor
                cursor = self.database.GetCursor();
                cursor.execute(command, tuple(tdata))
                self.database.Commit()
