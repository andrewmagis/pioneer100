
from datetime import date, datetime, timedelta as td
import fitbit
from errors import MyError

import numpy as np
import scipy
import math

class Metabolomics(object):

    def __init__(self, database):
        self.database = database

    def Compile(self):

        username = '2682430'
        round = 1

        # Make a really big matrix of round 1 and round 2 for all participants
        result = self.GetData(username)

        columns = [d[0] for d in cursor.description]
        r1 = np.array([x for x in cursor])
        print r1

        for key in sorted(self.participants.keys()):

            result = self.participants[key].MetaboliteTraitCorrelation(trait, measurement, pvalue)

            if (not result is None):
                data.append(result)

            print "Processed %s"%(key)

        # Build numpy structured array of scores
        x = np.array(data, dtype=[('Username', np.str, 10), ('Gender', np.str, 1), ('Round1', float), ('Round2', float), ('Round3', float), ('Score', float)])


    def GetData(self, username):

        # Get the cursor
        cursor = self.database.GetCursor();

        cursor.execute("SELECT * FROM metabolomics WHERE username = (%s) ORDER BY ROUND", (username,))
        result = None
        columns = [d[0] for d in cursor.description]

        # Concatenate all the tuples together
        result = []
        for row in cursor:
            result.append(row)

        if (len(result)>0):
            result = zip(*result)

        if (result is None):
            return {}

        if (len(result)==0):
            return {}

        # Now convert each value into a numpy array
        final = {}
        for key, values in zip(columns, result):
            if (key == "USERNAME"):
                continue;
            if (key == "ROUND"):
                final[key] = np.array(values, dtype=np.object)
                continue;

            try:
                final[key] = np.array(values, dtype=np.float)
            except:
                final[key] = np.array(values, dtype=np.object)
        return final

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

                # Get the cursor
                cursor = self.database.GetCursor();
                cursor.execute(command, tuple(tdata))
                self.database.Commit()

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
