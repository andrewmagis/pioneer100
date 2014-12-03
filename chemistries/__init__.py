
from datetime import date, datetime, timedelta as td
from errors import MyError

import datetime, re
from csv import reader

import numpy as np
import scipy
import math

FIRST_BLOOD_DRAW=datetime.datetime(2014, 6, 24)
SECOND_BLOOD_DRAW=datetime.datetime(2014, 9, 30)

class Chemistries(object):

    def __init__(self, database):
        self.database = database

    def _get_field(self, round, field_id):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username, v.value "
                       "FROM chem_observations as o, chem_values as v "
                       "WHERE o.round = (%s) "
                       "AND v.chemistry_id = (%s) "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY o.username", (round,field_id,))

        return np.array(list(cursor.fetchall()), dtype=[('username', str, 8), (str(field_id), float)])

    def _get_fields(self, round, fields):

        # Make sure this is a list
        assert isinstance(fields, (list, tuple))

        cursor = self.database.GetCursor()

        # Get the field ids for these chemistries
        formatted = ','.join(['%s'] * len(fields))
        cursor.execute("SELECT chemistry_id FROM chem_chemistries as c "
                       "WHERE c.name IN (%s)" % formatted, tuple(fields))

        result = cursor.fetchall();
        data = []

        # Loop over each id
        for id in result:
            data.append(self._get_field(round, id))

        print data

        # Build numpy array out of result
        #return np.array(list(cursor.fetchall()), dtype=[(username, float)])

    def _get_diff(self, username, round1, round2):

        r1 = self._get_val(username, round1)
        r2 = self._get_val(username, round2)

        # Build numpy array out of result
        return np.array(r2[username]-r1[username], dtype=[(username, float)])

    def Clean(self, value):

        temp = value.strip().strip('<').strip('>').strip(' ').strip('.');

        if (temp == "NR"):
            return None

        # If there is nothing left, return NULL
        if (len(temp)==0):
            return None # Return null value

        # This is to handle the Quest NOT APPLICABLE issue
        if ("OT" in temp.upper()):
            return None

        # Below detectable limit. Return 0
        if ("DL" in temp.upper()):
            temp = '0'

        # Set A/B and binary entries to integers
        elif (temp.upper() == 'A'):
            temp = '0'
        elif (temp.upper() == 'B'):
            temp = '1'
        elif (temp.upper() == "NO"):
            temp = '0'
        elif (temp.upper() == "YES"):
            temp = '1'

        return temp;

    def LoadQuest(self, filename):

        # Create regular expression for the measurement
        id_reg = re.compile(r"\([0-9]{8}\)");
        #username_reg = re.compile(r"[0-9]{7}(?!\S)");
        username_reg = re.compile(r"[0-9]{7}");

        cursor = self.database.GetCursor()
        cursor.execute("SELECT vendor_id,chemistry_id FROM chem_chemistries WHERE vendor = 'Quest'");
        mapping = {};
        for (vendor_id, chem_id) in cursor:
            mapping[vendor_id] = chem_id

        observations = []
        data = []

        with open(filename, 'rU') as f:
            for tokens in reader(f):

                if (len(tokens)<2):
                    continue;

                id = id_reg.findall(tokens[1]);
                if (len(id)==0):
                    #print "Warning: No ID in Quest measurement"
                    continue
                if (len(id)>1):
                    #print "Warning: Multiple IDs in Quest measurement"
                    continue

                # Get the actual id
                id = id[0].strip('(').strip(')')

                # Must split the value int two
                temp = tokens[2].split(' ');
                value = temp[0].strip();

                # Search fields 3 and 4 for usernames
                temp1 = username_reg.findall(tokens[3])

                usernames = set();
                for e in temp1:
                    usernames.add(e);
                if (len(usernames)==0):
                    print "Error, no username for Quest measurement"
                    print tokens;
                    print temp1, temp2
                    continue;
                if (len(usernames)>1):
                    print "Error multiple usernames for Quest measurement"
                    print temp1, temp2
                    continue;

                # Actually get the username
                username = usernames.pop();
                submitted_date = tokens[9];

                # Convert submitted date to datetime
                date_ordered = datetime.datetime.strptime(submitted_date, "%m/%d/%Y");
                if (date_ordered <= FIRST_BLOOD_DRAW):
                    round = 1
                elif (date_ordered <= SECOND_BLOOD_DRAW):
                    round = 2
                else:
                    round = 3

                # Make sure this is in the mapping
                if (not id in mapping):
                    continue

                # Try to find this chem id in the values table
                cursor.execute("SELECT v.value, o.date, v.chem_values_id, o.observation_id "
                               "FROM chem_values as v, chem_observations as o "
                               "WHERE o.username = (%s) AND o.round = (%s) and v.chemistry_id = (%s) and v.observation_id = o.observation_id", (username, round, mapping[id]))

                result = cursor.fetchall()

                # There was no row found, so insert a new row!
                if (len(result) == 0):

                    # Just insert the observation
                    cursor.execute("INSERT INTO chem_observations (username, round, date) VALUES (%s,%s, %s)", (username, round, date_ordered))

                    # Insert the data
                    cursor.execute("INSERT INTO chem_values (observation_id, chemistry_id, value) VALUES (%s,%s, %s)", (cursor.lastrowid, mapping[id], self.Clean(value)))

                elif (len(result) == 1):

                    # Get the associated date
                    (old_value, old_date, chem_values_id, observation_id) = list(result)[0]

                    if (old_date is None):
                        raise MyError('No date for username %s and round %d'%(username, round));

                    elif (date_ordered > old_date):

                        print "Update username: %s round %s from (%s, %s) with (%s, %s)"%(username, round, str(old_value), old_date, self.Clean(value), date_ordered)
                        cursor.execute("UPDATE chem_observations "
                                       "SET date = (%s) "
                                       "WHERE observation_id = (%s)", (date_ordered, observation_id))

                        cursor.execute("UPDATE chem_values "
                                       "SET value = (%s) "
                                       "WHERE chem_values_id = (%s)", (self.Clean(value), chem_values_id))

                else:
                    raise MyError('More than one entry! Bad!')

        # Insert the observations
        #result = cursor.executemany("INSERT INTO chem_values (observation_id, chemistry_id, value) VALUES (%s,%s, %s)", data)
        self.database.Commit()

    def LoadGenova(self, filename):

        titles = None
        headers = None

        cursor = self.database.GetCursor()
        cursor.execute("SELECT vendor_id,chemistry_id FROM chem_chemistries WHERE vendor = 'Genova'");
        mapping = {};
        for (vendor_id, chem_id) in cursor:
            mapping[vendor_id] = chem_id

        observations = []
        data = []

        with open(filename, 'rU') as f:
            for line in f:

                # Load the headers, removing the final 9 columns
                if (titles is None):
                    titles = line.strip().split('\t')[:-9]

                # Next load the identifiers, removing the final 9 columns
                elif (headers is None):
                    headers = line.strip().split('\t')[:-9]
                    print headers

                # Finally, load the data, removing the final 9 columns
                else:

                    tokens = line.strip().split('\t')[:-9]

                    # Convert into dictionary
                    current = dict(zip([x.strip() for x in headers], [x.strip() for x in tokens]))

                    # Get username from this row
                    username = current["Last Name"]

                    # Get date from this row
                    date_ordered = datetime.datetime.strptime(current['Date Ordered'], "%m/%d/%y");
                    if (date_ordered <= FIRST_BLOOD_DRAW):
                        round = 1
                    elif (date_ordered <= SECOND_BLOOD_DRAW):
                        round = 2
                    else:
                        round = 3

                    # Now we must loop over the ids
                    for id in current.keys():

                        # Make sure this is in the mapping
                        if (not id in mapping):
                            continue

                        # Try to find this chem id in the values table
                        cursor.execute("SELECT v.value, o.date, v.chem_values_id, o.observation_id "
                                       "FROM chem_values as v, chem_observations as o "
                                       "WHERE o.username = (%s) AND o.round = (%s) and v.chemistry_id = (%s) and v.observation_id = o.observation_id", (username, round, mapping[id]))

                        result = cursor.fetchall()

                        # There was no row found, so insert a new row!
                        if (len(result) == 0):

                            # Just insert the observation
                            cursor.execute("INSERT INTO chem_observations (username, round, date) VALUES (%s,%s, %s)", (username, round, date_ordered))

                            # Insert the data
                            cursor.execute("INSERT INTO chem_values (observation_id, chemistry_id, value) VALUES (%s,%s, %s)", (cursor.lastrowid, mapping[id], self.Clean(current[id])))

                        elif (len(result) == 1):

                            # Get the associated date
                            (value, old_date, chem_values_id, observation_id) = list(result)[0]

                            if (old_date is None):
                                raise MyError('No date for username %s and round %d'%(username, round));

                            elif (date_ordered > old_date):

                                print "Update username: %s round %s from (%s, %s) with (%s, %s)"%(username, round, str(value), old_date, self.Clean(current[id]), date_ordered)
                                cursor.execute("UPDATE chem_observations "
                                               "SET date = (%s) "
                                               "WHERE observation_id = (%s)", (date_ordered, observation_id))

                                cursor.execute("UPDATE chem_values "
                                               "SET value = (%s) "
                                               "WHERE chem_values_id = (%s)", (self.Clean(current[id]), chem_values_id))

                        else:
                            raise MyError('More than one entry! Bad!')

        # Insert the observations
        #result = cursor.executemany("INSERT INTO chem_values (observation_id, chemistry_id, value) VALUES (%s,%s, %s)", data)
        self.database.Commit()
