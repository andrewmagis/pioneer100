
from datetime import date, datetime, timedelta as td
from errors import MyError

import numpy as np
import scipy
import math

class Proteomics(object):

    def __init__(self, database):
        self.database = database

    def Get(self, username, round):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT v.ct_value FROM prot_observations as o, prot_values as v WHERE o.username = (%s) AND o.round = (%s) AND v.observation_id = o.observation_id ORDER BY o.observation_id", (username,round,))

        # Build numpy array out of result
        return np.array(cursor.fetchall(), dtype=[('ct_value', float), ('dummy', np.str, 8)])

    #def GetNormalized(self, username, round):

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

    def LoadData(self, filename, category=None):

        # Ignore this function
        raise MyError('LoadData function disabled')

        header = None
        alldata = {}
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

                    # Get controls
                    if (username == "Negative Control"):
                        neg_control.append(tokens[2:])
                    elif (username == "Interplate Control"):
                        interplate_control.append(tokens[2:])
                    else:

                        round = int(tokens[1].strip())
                        if (not username in alldata):
                            alldata[username] = {}
                        if (not round in alldata[username]):
                            alldata[username][round] = None
                        alldata[username][round] = tokens[2:]


        # Insert the proteins
        cursor = self.database.GetCursor()
        data = []
        for p in header:
            data.append((p, category))

        # Insert into table
        result = cursor.executemany("INSERT INTO prot_proteins (abbreviation, category) VALUES (%s,%s)", data)
        self.database.Commit()

        # Next add in the controls
        cursor = self.database.GetCursor()
        data = []
        for negative, plate in zip(neg_control, interplate_control):
            for protein, neg_value, plate_value, in zip(header, negative, plate):

                # Get the protein_id for this abbreviation
                cursor.execute("SELECT protein_id FROM prot_proteins WHERE abbreviation = (%s) LIMIT 1", (protein,))

                # Append variables to tuple
                tup = cursor.fetchone() + (neg_value, plate_value)

                # Build the tuples
                data.append(tup)

        # Insert the control values
        result = cursor.executemany("INSERT INTO prot_controls (protein_id, negative_control, interplate_control) VALUES (%s,%s,%s)", data)
        self.database.Commit()

        # Dates for blood draws for proteomics
        FIRST_BLOOD_DRAW=datetime(2014, 5, 1)
        SECOND_BLOOD_DRAW=datetime(2014, 8, 1)
        THIRD_BLOOD_DRAW=datetime(2014, 11, 1)

        # Now add in the observations
        cursor = self.database.GetCursor()
        data = []
        for username in alldata.keys():
            for round in alldata[username].keys():
                if (round == 1):
                    data.append((username, round, FIRST_BLOOD_DRAW))
                elif (round == 2):
                    data.append((username, round,  SECOND_BLOOD_DRAW))
                else:
                    data.append((username, round, THIRD_BLOOD_DRAW))

        # Insert the observation values
        result = cursor.executemany("INSERT INTO prot_observations (username, round, date) VALUES (%s,%s,%s)", data)
        self.database.Commit()

        # Finally add the observations
        cursor = self.database.GetCursor()
        data = []

        for username in alldata.keys():
            for round in alldata[username].keys():

                # Loop over the observations
                for protein, value in zip(header, alldata[username][round]):

                    # Get the protein_id for this abbreviation
                    cursor.execute("SELECT protein_id FROM prot_proteins WHERE abbreviation = (%s) LIMIT 1", (protein,))
                    protein_id = cursor.fetchone()

                    # Get the control id
                    cursor.execute("SELECT prot_control_id FROM prot_controls WHERE protein_id = (%s) LIMIT 1", protein_id)
                    prot_control_id = cursor.fetchone()

                    # Get the observation id
                    cursor.execute("SELECT observation_id FROM prot_observations WHERE username = (%s) AND round = (%s) LIMIT 1", (username,round))
                    observation_id = cursor.fetchone()

                    # Append variables to tuple
                    data.append((observation_id, protein_id, prot_control_id, self.Clean(value)))

        # Insert the observation values
        result = cursor.executemany("INSERT INTO prot_values (observation_id, protein_id, prot_control_id, ct_value) VALUES (%s,%s,%s,%s)", data)
        self.database.Commit()
