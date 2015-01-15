
# System imports
from datetime import date, datetime, timedelta as td
import numpy as np
import scipy
import math, re
import pandas, pandas.io
from csv import reader

# Codebase imports
from p100.errors import MyError
from p100.range import Range
from p100.participant import Participants
from p100.utils.dataframeops import DataFrameOps

FIRST_BLOOD_DRAW=datetime(2014, 6, 24)
SECOND_BLOOD_DRAW=datetime(2014, 9, 30)

class Chemistries(DataFrameOps):

    def __init__(self, database):
        self.database = database

    def GetData(self, username=None, round=None, chemistry_id=None):
        """
        Returns a dataframe with the BMI data for
        a given user and round(if provided).
        """
        l_logger.debug("GetData( %s, %s, %s )" %( username, round, chemistry_id ))
        q_string = """
        SELECT co.username, co.round, value, name, cv.chemistry_id
        FROM chem_values cv, chem_observations co, chem_chemistries cc
        WHERE cc.chemistry_id = cv.chemistry_id
        and co.observation_id = cv.observation_id
        """
        conditions = []
        var_tup = []
        if username is not None:
            conditions.append("co.username = %s ")
            var_tup += [username]
        if round is not None:
            conditions.append("co.round = %s")
            var_tup += [round]
        if chemistry_id is not None:
            conditions.append("cc.chemistry_id = %s")
            var_tup += [chemistry_id]
        q_string = ' and '.join( [ q_string ] + conditions )
        var_tup = tuple( var_tup )
        return self.database.GetDataFrame( q_string, tuple(var_tup) )

    def _get_unit_by_name(self, field_name):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT unit "
                       "FROM chem_chemistries "
                       "WHERE name = (%s) ", (field_name,))

        result = list(cursor.fetchall())
        if (len(result)==0):
            return None
        else:
            (unit,) = result[0]
            return unit

    def _get_range_by_name(self, field_name):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT r.min_value, r.max_value, r.range_type, r.range_level, r.gender "
                       "FROM chem_ranges as r, chem_chemistries as c "
                       "WHERE c.name = (%s) "
                       "AND r.chemistry_id = c.chemistry_id "
                       "ORDER BY r.min_value", (field_name,))

        return Range(list(cursor.fetchall()))

    def _get_field_by_name(self, round, field_name):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username, v.value "
                       "FROM chem_observations as o, chem_values as v, chem_chemistries as c "
                       "WHERE o.round = (%s) "
                       "AND c.name = (%s) "
                       "AND v.chemistry_id = c.chemistry_id "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY o.username", (round,field_name,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('username', str, 8), (str(field_name), float)])

        # Build pandas Series
        return pandas.DataFrame(array[str(field_name)], index=array['username'], columns=[field_name])

    def _get_participant_by_name(self, round, username):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT c.name, v.value "
                       "FROM chem_observations as o, chem_values as v, chem_chemistries as c "
                       "WHERE o.round = (%s) "
                       "AND o.username = (%s) "
                       "AND v.chemistry_id = c.chemistry_id "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY c.name", (round,username,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('chemistry', str, 128), (str(username), float)])

        # Build pandas Series
        return pandas.DataFrame(array[str(username)], index=array['chemistry'], columns=[str(username)])

    def _get_out_of_range(self, round, field_name):

        prts = Participants(self.database)
        prt_data = prts._get_all_participants()
        r = self._get_range_by_name(field_name)
        data = self._get_field_by_name(round, field_name)

        # Now find those individuals that are out of range
        oor1 = []
        for prt in data.index:
            value = data.loc[prt,field_name]
            gender = prt_data.loc[prt, 'gender']
            (rtype, rlevel) = r.state(value, gender);
            if (rtype=='R' or rtype=='Y') and (rlevel=='HIGH'):
                oor1.append((prt, value))

        array = np.array(oor1, dtype=[('username', str, 8), ('round1', float)])
        oor1 = pandas.DataFrame(array['round1'], index=array['username'], columns=['round1'])
        return oor1


    def _get_all_participants(self, round):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT username "
                       "FROM participants")

        headers = np.array(list(cursor.fetchall()), dtype=[('username', str, 128)])

        result = None
        # Now loop over the database and retrieve all of it for this round
        for username in headers['username']:

            current = self._get_participant_by_name(round, username)
            if (result is None):
                result = current
            else:
                result = result.join(current, how='outer')

        return result

    def _get_field_by_id(self, round, field_id):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username, v.value "
                       "FROM chem_observations as o, chem_values as v "
                       "WHERE o.round = (%s) "
                       "AND v.chemistry_id = (%s) "
                       "AND v.observation_id = o.observation_id "
                       "ORDER BY o.username", (round,field_id,))

        # Create the np array
        array = np.array(list(cursor.fetchall()), dtype=[('username', str, 8), (str(field_id), float)])

        # Build pandas Series
        return pandas.DataFrame(array[str(field_id)], index=array['username'], columns=[str(field_id)])

    def _get_all_fields(self, round):

        cursor = self.database.GetCursor()
        cursor.execute("SELECT name "
                       "FROM chem_chemistries")

        headers = np.array(list(cursor.fetchall()), dtype=[('name', str, 128)])

        result = None
        # Now loop over the database and retrieve all of it for this round
        for name in headers['name']:

            current = self._get_field_by_name(round, name)
            if (result is None):
                result = current
            else:
                result = result.join(current, how='outer')

        return result

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
                date_ordered = datetime.strptime(submitted_date, "%m/%d/%Y");
                if (date_ordered <= FIRST_BLOOD_DRAW):
                    round = 1
                elif (date_ordered <= SECOND_BLOOD_DRAW):
                    round = 2
                else:
                    round = 3

                # Make sure this is in the mapping
                if (not id in mapping):
                    continue

                # Convert value
                new_value = self.Clean(value)

                # Do not insert Nones
                if (new_value is None):
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
                    cursor.execute("INSERT INTO chem_values (observation_id, chemistry_id, value) VALUES (%s,%s, %s)", (cursor.lastrowid, mapping[id], new_value))

                elif (len(result) == 1):

                    # Get the associated date
                    (old_value, old_date, chem_values_id, observation_id) = list(result)[0]

                    if (old_date is None):
                        raise MyError('No date for username %s and round %d'%(username, round));

                    elif (date_ordered > old_date):

                        print "Update username: %s round %s from (%s, %s) with (%s, %s)"%(username, round, str(old_value), old_date, new_value, date_ordered)
                        cursor.execute("UPDATE chem_observations "
                                       "SET date = (%s) "
                                       "WHERE observation_id = (%s)", (date_ordered, observation_id))

                        cursor.execute("UPDATE chem_values "
                                       "SET value = (%s) "
                                       "WHERE chem_values_id = (%s)", (new_value, chem_values_id))

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
                    date_ordered = datetime.strptime(current['Date Ordered'], "%m/%d/%y");
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

                        # Convert value
                        new_value = self.Clean(current[id])

                        # Do not insert Nones
                        if (new_value is None):
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
                            cursor.execute("INSERT INTO chem_values (observation_id, chemistry_id, value) VALUES (%s,%s, %s)", (cursor.lastrowid, mapping[id], new_value))

                        elif (len(result) == 1):

                            # Get the associated date
                            (old_value, old_date, chem_values_id, observation_id) = list(result)[0]

                            if (old_date is None):
                                raise MyError('No date for username %s and round %d'%(username, round));

                            elif (date_ordered > old_date):

                                print "Update username: %s round %s from (%s, %s) with (%s, %s)"%(username, round, str(old_value), old_date, new_value, date_ordered)
                                cursor.execute("UPDATE chem_observations "
                                               "SET date = (%s) "
                                               "WHERE observation_id = (%s)", (date_ordered, observation_id))

                                cursor.execute("UPDATE chem_values "
                                               "SET value = (%s) "
                                               "WHERE chem_values_id = (%s)", (new_value, chem_values_id))

                        else:
                            raise MyError('More than one entry! Bad!')

        # Insert the observations
        #result = cursor.executemany("INSERT INTO chem_values (observation_id, chemistry_id, value) VALUES (%s,%s, %s)", data)
        self.database.Commit()
