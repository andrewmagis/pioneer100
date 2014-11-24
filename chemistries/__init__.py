
from datetime import date, datetime, timedelta as td
from errors import MyError

import numpy as np
import scipy
import math

class Chemistries(object):

    def __init__(self, database):
        self.database = database

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

    def Clean(self, value):

        temp = value.strip('<').strip('>').strip(' ').strip('.').strip("NR");

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
            print temp
            temp = '0'
        elif (temp.upper() == 'B'):
            print temp
            temp = '1'
        elif (temp.upper() == "NO"):
            print temp
            temp = '0'
        elif (temp.upper() == "YES"):
            print temp
            temp = '1'

        return temp;

    def LoadQuest(self, filename):

        # Create regular expression for the measurement
        id_reg = re.compile(r"\([0-9]{8}\)");
        #username_reg = re.compile(r"[0-9]{7}(?!\S)");
        username_reg = re.compile(r"[0-9]{7}");

        cursor = self.db.cursor()
        cursor.execute("SELECT name,vendor_id FROM chem_chemistries WHERE vendor = 'Quest'");
        mapping = {};
        for (measurement, id) in cursor:
            mapping[id] = measurement

        print mapping
        return

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

                # Get the value for this date and round
                result = self.GetMeasurementByRound('DATE', username, round);
                if (not result is None):

                    # There is data, skip insertion
                    #print "Found round %d for username %s"%(round, username);

                    # Get the associated date
                    db_date = result[0];
                    if (db_date is None):
                        raise MyError('No date for username %s and round %d'%(username, round));

                    # Update data one at a time (yes inefficient, so shoot me)
                    self.UpdateData(username, round, db_date, date_ordered, {id: value}, mapping)

                # There was no row found, so insert a new row!
                else:

                    # Insert new row
                    print "Cannot insert rows from Quest data [%s %s]"%(username, date_ordered)
                    #raise MyError('Cannot insert data from Quest - add Genova first!');