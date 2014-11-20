
from datetime import date, datetime, timedelta as td
from errors import MyError

import numpy as np
import scipy
import math

class Proteomics(object):

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

    def LoadProteomicsData(self, filename):

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

    def LoadData(self, filename, category=None):

        header = None
        data = {}
        neg_control = []
        interplate_control = []

        # Load all the data into a data structure to start
        with open(filename, 'rU') as f:
            for line in f:

                # Get header row
                if (header is None):
                    header = line.strip().split('\t')
                    header = [x.split('_')[1].replace('-', '_').replace(' ', '_') for x in header[2:]]

                else:

                    tokens = line.strip().split('\t')
                    username = tokens[0].strip()
                    round = tokens[1].strip()
                    # Get controls
                    if (username == "Negative Control"):
                        neg_control.append(tokens[2:])
                    elif (username == "Interplate Control"):
                        interplate_control.append(tokens[2:])
                    else:
                        if (not username in data):
                            data[username] = {}
                        if (not round in data[username]):
                            data[username][round] = None
                        data[username][round] = tokens[2:]

        """
        # Get the cursor to insert
        cursor = self.database.GetCursor()

        # Add to the proteins table
        for p in header:
            command = "INSERT INTO prot_proteins (abbreviation, category) VALUES (%s, %s)"
            cursor.execute(command, (p,category))
        """

        # Next add in the controls
        for negative, plate in zip(neg_control, interplate_control):
            for protein, neg_value, plate_value, in zip(header, negative, plate):
                print protein, neg_value, plate_value


        # Finalize
        self.database.Commit()


    def CreateProteinTable(self, filename, category = None):

        command = ""
        command += "CREATE TABLE proteins (PROTEIN VARCHAR(16) PRIMARY KEY, CATEGORY VARCHAR(16), NAME VARCHAR(256))"
        self.database.Command(command)

        header = None
        alldata = {}
        neg_control = []
        interplate_control = []

        with open(filename, 'rU') as f:
            for line in f:

                if (header is None):
                    header = line.strip().split('\t')
                    header = [x.split('_')[1].replace('-', '_').replace(' ', '_') for x in header[2:]]

                    cursor = self.database.GetCursor()

                    # Add to the proteins table
                    for p in header:
                        command = "INSERT INTO proteins (PROTEIN, CATEGORY) VALUES (%s, %s)"
                        cursor.execute(command, (p,category))

                    self.database.Commit()

                    command = "";
                    command += "CREATE TABLE proteomics (ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, ROUND INT NOT NULL"

                    cursor = self.database.GetCursor();
                    result = cursor.execute("SELECT PROTEIN from proteins")
                    for protein in cursor:
                        command += ", %s FLOAT"%(protein)
                    command += ")"

                    cursor.execute(command)
                    self.database.Commit()

                else:

                    tokens = line.strip().split('\t')
                    username = tokens[0].strip()
                    round = tokens[1].strip()
                    # Get controls
                    if (username == "Negative Control"):
                        neg_control.append(tokens[2:])
                    elif (username == "Interplate Control"):
                        interplate_control.append(tokens[2:])
                    else:

                        data = np.array(tokens[2:], dtype=float)
                        if (not username in alldata):
                            alldata[username] = {}
                        if (not round in alldata[username]):
                            alldata[username][round] = None
                        alldata[username][round] = data

        # At the end, make a numpy array out of controls
        neg_control = np.array(neg_control, dtype=float)
        interplate_control = np.array(interplate_control, dtype=float)

        # Get mean of the controls
        neg_control_mean = np.mean(neg_control, axis=0)
        interplate_control_mean = np.mean(interplate_control, axis=0)

        # Finally, add this data to the protein table
        for username in alldata:
            for round in alldata[username]:

                # Now normalize the values based on the neg controls
                alldata[username][round] = np.power(2, neg_control_mean - alldata[username][round])

                # Build the insertion statement
                command = "INSERT INTO proteomics (USERNAME, ROUND"
                for key in header:
                    command += ',' + key.upper()
                command += ") VALUES (%s,%s";

                # Build tuple for parameterization
                tdata = [username, round]

                for value in alldata[username][round]:
                    command += ',' + '%s';
                    tdata.append(value);

                command += ")";

                # Get the cursor
                cursor = self.database.GetCursor();
                cursor.execute(command, tuple(tdata))
                self.database.Commit()
