
from datetime import date, datetime, timedelta as td
from errors import MyError

import numpy as np
import scipy
import math

class Proteomics(object):

    def __init__(self, database):
        self.database = database

    def _get_field(self, round, field_id):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username, v.value "
                       "FROM prot_observations as o, prot_values as v "
                       "WHERE o.round = (%s) "
                       "AND v.chemistry_id = (%s) "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY o.username", (round,field_id,))

        return np.array(list(cursor.fetchall()), dtype=[('username', str, 8), (str(field_id), float)])

    def _get_val(self, username, round):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT v.norm_value FROM prot_observations as o, prot_values as v "
                       "WHERE o.username = (%s) AND o.round = (%s) AND v.observation_id = o.observation_id "
                       "ORDER BY o.observation_id", (username,round,))

        # Build numpy array out of result
        return np.array(list(cursor.fetchall()), dtype=[(username, float)])

    def _get_diff(self, username, round1, round2):

        r1 = self._get_val(username, round1)
        r2 = self._get_val(username, round2)

        # Build numpy array out of result
        return np.array(r2[username]-r1[username], dtype=[(username, float)])

    # Ignore this function
    def GetNormalized(self, username, round):

        # Get the protein control ids as well as the ct values
        cursor = self.database.GetCursor()
        cursor.execute("SELECT v.protein_id, v.ct_value FROM prot_observations as o, prot_values as v "
                       "WHERE o.username = (%s) AND o.round = (%s) AND v.observation_id = o.observation_id "
                       "ORDER BY o.observation_id", (username,round,))

        # Create an array with the control ids and the values
        temp = np.array(list(cursor.fetchall()), dtype=[('protein_id', int), ('ct_value', float)])

        # Get the control values for each protein
        controls = []
        for protein_id in temp['protein_id']:
            cursor.execute("SELECT c.negative_control,c.interplate_control "
                           "FROM prot_controls as c "
                           "WHERE c.protein_id = (%s)", (protein_id,))
            controls.append(list(cursor.fetchall()))

        controls = np.array(controls, dtype=[('negative_control', float), ('interplate_control', float)])

        # Calculate the mean negative control value
        mean_negative_controls = np.mean(controls['negative_control'], axis=1)

    def Clean(self, value):

        new_value = value.strip().strip("'").strip('"')
        if (len(new_value) == 0):
            return None
        return new_value

    def LoadData(self, filename, category=None):

        # Ignore this function
        raise MyError('LoadData function disabled')

        header = None
        category = None
        alldata = {}
        neg_control = []
        interplate_control = []

        # Load all the data into a data structure to start
        with open(filename, 'rU') as f:
            for line in f:

                # Get header row
                if (header is None):
                    header = line.strip().split('\t')
                    header = [x.split('_')[1].strip().replace('-', '_').replace(' ', '_') for x in header[2:]]

                # Get category row next
                elif (category is None):
                    category= line.strip().split('\t')[2:]

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
                        alldata[username][round] = np.array(tokens[2:], dtype=float)

        mean_neg_control_array = np.mean(np.array(neg_control, dtype=float), axis=0)
        mean_interplate_control_array = np.mean(np.array(interplate_control, dtype=float), axis=0)

        # Insert the proteins
        cursor = self.database.GetCursor()
        data = []
        for p,c in zip(header, category):
            data.append((p, c))

        # Insert into table
        result = cursor.executemany("INSERT INTO prot_proteins (abbreviation, category) VALUES (%s,%s)", data)
        self.database.Commit()

        # Next add in the controls
        cursor = self.database.GetCursor()
        data = []
        for negative, plate in zip(neg_control, interplate_control):
            for protein, cat, neg_value, plate_value, in zip(header, category, negative, plate):

                # Get the protein_id for this abbreviation
                cursor.execute("SELECT protein_id FROM prot_proteins WHERE abbreviation = (%s) and category = (%s) LIMIT 1", (protein,cat,))

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

                # Get normalized data
                norm_data = np.power(2, np.subtract(mean_neg_control_array, alldata[username][round]))

                # Loop over the observations
                for protein, cat, value, norm in zip(header, category, alldata[username][round], norm_data):

                    # Get the protein_id for this abbreviation
                    cursor.execute("SELECT protein_id FROM prot_proteins WHERE abbreviation = (%s) AND category = (%s) LIMIT 1", (protein,cat,))
                    protein_id = cursor.fetchone()

                    # Get the control id
                    cursor.execute("SELECT prot_control_id FROM prot_controls WHERE protein_id = (%s) LIMIT 1", protein_id)
                    prot_control_id = cursor.fetchone()

                    # Get the observation id
                    cursor.execute("SELECT observation_id FROM prot_observations WHERE username = (%s) AND round = (%s) LIMIT 1", (username,round))
                    observation_id = cursor.fetchone()

                    # Append variables to tuple
                    data.append((observation_id, protein_id, prot_control_id, value, norm))

        # Insert the observation values
        result = cursor.executemany("INSERT INTO prot_values (observation_id, protein_id, prot_control_id, ct_value, norm_value) VALUES (%s,%s,%s,%s,%s)", data)
        self.database.Commit()
