
# System imports
from datetime import date, datetime, timedelta as td
import numpy as np
import scipy
from scipy import stats
import statsmodels
import math
import pandas, pandas.io

# Codebase imports
from p100.errors import MyError
from p100.utils.dataframeops import DataFrameOps

class Proteomics(DataFrameOps):

    def __init__(self, database):
        self.database = database

    def _get_field_by_name(self, round, field_name, category):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username, v.norm_value "
                       "FROM prot_observations as o, prot_values as v, prot_proteins as p "
                       "WHERE o.round = (%s) "
                       "AND p.abbreviation = (%s) "
                       "AND p.category = (%s) "
                       "AND v.protein_id = p.protein_id "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY o.username", (round,field_name,category,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('username', str, 8), (field_name, float)])

        # Build pandas Series
        return pandas.DataFrame(array[field_name], index=array['username'], columns=[field_name])

    def _get_field_by_id(self, round, field_id):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username, v.norm_value "
                       "FROM prot_observations as o, prot_values as v "
                       "WHERE o.round = (%s) "
                       "AND v.protein_id = (%s) "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY o.username", (round,field_id,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('username', str, 8), (str(field_id), float)])

        # Build pandas Series
        return pandas.DataFrame(array[str(field_id)], index=array['username'], columns=[str(field_id)])

    def _get_all_fields(self, round, category="Inflammation"):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT abbreviation "
                       "FROM prot_proteins "
                       "WHERE category = (%s)", (category,))

        headers = np.array(list(cursor.fetchall()), dtype=[('name', str, 128)])

        result = None
        # Now loop over the database and retrieve all of it for this round
        for name in headers['name']:

            if ("Ctrl" in name):
                continue

            current = self._get_field_by_name(round, name, category)
            if (result is None):
                result = current
            else:
                result = result.join(current)

        return result

    def _get_signrank_by_name(self, roundA, roundB, field_name, category = "Inflammation"):

        r1 = self._get_field_by_name(roundA, field_name, category)
        r2 = self._get_field_by_name(roundB, field_name, category)

        # Merge the two in a dataframe
        data = r1.join(r2, lsuffix='_r1', rsuffix='_r2')

        # Drop rows with NaN values
        data.dropna()

        # Separate out the data
        d1 = data[field_name+'_r1']
        d2 = data[field_name+'_r2']

        z_stat, p_val = stats.ranksums(d1, d2)
        return (z_stat, p_val, np.mean(d1), np.mean(d2), np.std(d1), np.std(d2))

    def _get_all_signrank(self, roundA, roundB, category="Inflammation"):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT abbreviation "
                       "FROM prot_proteins "
                       "WHERE category = (%s)", (category,))

        headers = np.array(list(cursor.fetchall()), dtype=[('name', str, 128)])

        result = []
        names = []
        # Now loop over the database and retrieve all of it for this round
        for name in headers['name']:

            # Perform the signed rank test (non-parametric)
            result.append(self._get_signrank_by_name(roundA, roundB, name))
            names.append(name)

        # Create the np array
        array = np.array(result, dtype=[('z_value', float), ('p_value', float), ('meanA', float), ('meanB', float), ('stdA', float), ('stdB', float)])
        (accepted, corrected, unused1, unused2) = statsmodels.sandbox.stats.multicomp.multipletests(array['p_value'], method="fdr_bh")

        # Build pandas dataframe with corrected p-values
        temp = pandas.DataFrame(array, index=names, columns=['z_value', 'p_value', 'fdr', 'meanA', 'meanB', 'stdA', 'stdB'])
        temp['fdr'] = pandas.Series(corrected, index=temp.index)
        return temp.sort('fdr', ascending=True)

    def _get_all_diff(self, roundA, roundB, category="Inflammation"):

        # Get these two rounds
        dataA = self._get_all_fields(roundA, category)
        dataB = self._get_all_fields(roundB, category)

        # Now take the difference of the rounds and drop any that have data missing
        return (dataB - dataA)

    def _get_diff_by_id(self, roundA, roundB, field_id):

        # Get these two rounds
        dataA = self._get_field_by_id(roundA, field_id)
        dataB = self._get_field_by_id(roundB, field_id)

        # Now take the difference of the rounds and drop any that have data missing
        return (dataB - dataA).dropna()

    def _get_diff_by_name(self, roundA, roundB, field_name, category):

        # Get these two rounds
        dataA = self._get_field_by_name(roundA, field_name, category)
        dataB = self._get_field_by_name(roundB, field_name, category)

        # Now take the difference of the rounds and drop any that have data missing
        return (dataB - dataA).dropna()

    def _get_participant_by_name(self, round, username, category):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT c.abbreviation, v.norm_value "
                       "FROM prot_observations as o, prot_values as v, prot_proteins as c "
                       "WHERE o.round = (%s) "
                       "AND c.category = (%s) "
                       "AND o.username = (%s) "
                       "AND v.protein_id = c.protein_id "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY c.abbreviation", (round,category,username,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('metabolite', str, 128), (str(username), float)])

        # Build pandas Series
        return pandas.DataFrame(array[str(username)], index=array['metabolite'], columns=[str(username)])

    def _get_all_participants(self, round, category="Inflammation"):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT username "
                       "FROM participants")

        headers = np.array(list(cursor.fetchall()), dtype=[('username', str, 128)])

        result = None
        # Now loop over the database and retrieve all of it for this round
        for username in headers['username']:

            current = self._get_participant_by_name(round, username, category)
            if (result is None):
                result = current
            else:
                result = result.join(current)

        return result

    def _get_all_diff_participant(self, roundA, roundB, category="Inflammation"):

        # Get these two rounds
        dataA = self._get_all_participants(roundA, category)
        dataB = self._get_all_participants(roundB, category)

        # Now take the difference of the rounds and drop any that have data missing
        return (dataB - dataA)

    def Clean(self, value):

        new_value = value.strip().strip("'").strip('"')
        if (len(new_value) == 0):
            return None
        return new_value

    def LoadData(self, filename, category):

        # Ignore this function
        #raise MyError('LoadData function disabled')

        header = None
        alldata = {}
        neg_control = []
        interplate_control = []
        ext_control_index = None

        # Load all the data into a data structure to start
        with open(filename, 'rU') as f:
            for line in f:

                # Get header row
                if (header is None):
                    header = line.strip().split('\t')
                    header = [x.split('_')[1].strip().replace('-', '_').replace(' ', '_') for x in header[2:]]

                    # Get index of ext control
                    ext_control_index = header.index('Ext_Ctrl')
                    print "Extension control: ", ext_control_index

                else:

                    tokens = line.strip().split('\t')
                    username = tokens[0].strip()

                    # Get controls
                    if (username == "Negative Control"):

                        # Create a numpy array out of this
                        temp = np.array(tokens[2:],dtype=float)

                        # Subtract out the ext_control
                        temp -= temp[ext_control_index]

                        # Now append the negative control
                        neg_control.append(temp)

                    elif (username == "Interplate Control"):

                        # Create a numpy array out of this
                        temp = np.array(tokens[2:],dtype=float)

                        # Subtract out the ext_control
                        temp -= temp[ext_control_index]

                        # Now append the negative control
                        interplate_control.append(temp)

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
        for p in header:

            # Try to find this protein first
            cursor.execute("SELECT protein_id FROM prot_proteins WHERE abbreviation = (%s) AND category = (%s)", (p, category))
            results = cursor.fetchall()

            # If I don't find, it, insert it
            if (len(results)==0):
                data.append((p, category))

        # Insert into table
        if (len(data)>0):
            result = cursor.executemany("INSERT INTO prot_proteins (abbreviation, category) VALUES (%s,%s)", data)
            self.database.Commit()

        # Next add in the controls
        cursor = self.database.GetCursor()
        data = []
        for negative, plate in zip(neg_control, interplate_control):
            for protein, neg_value, plate_value, in zip(header, negative, plate):

                # Get the protein_id for this abbreviation
                cursor.execute("SELECT protein_id FROM prot_proteins WHERE abbreviation = (%s) and category = (%s) LIMIT 1", (protein,category,))

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
            for round in sorted(alldata[username].keys()):
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

        for username in sorted(alldata.keys()):
            for round in sorted(alldata[username].keys()):

                # Make a copy
                temp = np.array(alldata[username][round])

                # Subtract the extension control from this entire row
                temp -= temp[ext_control_index]

                # Subtract the dIPC from this entire row (already normalized by extension control)
                temp -= mean_interplate_control_array

                # Subtract this value from the negative control
                temp = mean_neg_control_array-temp

                # Get normalized data
                norm_data = np.power(2, temp)

                # Loop over the observations
                for protein, value, norm in zip(header, alldata[username][round], norm_data):

                    # Get the protein_id for this abbreviation
                    cursor.execute("SELECT protein_id FROM prot_proteins WHERE abbreviation = (%s) AND category = (%s) LIMIT 1", (protein,category,))
                    protein_id = list(cursor.fetchone())[0]

                    # Get the control id
                    cursor.execute("SELECT prot_control_id FROM prot_controls WHERE protein_id = (%s) LIMIT 1", protein_id)
                    prot_control_id = list(cursor.fetchone())[0]

                    # Get the observation id
                    cursor.execute("SELECT observation_id FROM prot_observations WHERE username = (%s) AND round = (%s) LIMIT 1", (username,round))
                    observation_id = list(cursor.fetchone())[0]

                    # Append variables to tuple
                    data.append((observation_id, protein_id, prot_control_id, value, norm))

        # Insert the observation values
        result = cursor.executemany("INSERT INTO prot_values (observation_id, protein_id, prot_control_id, ct_value, norm_value) VALUES (%s,%s,%s,%s,%s)", data)
        self.database.Commit()
