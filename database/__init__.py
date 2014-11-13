# MySQL information (clearly insecure)
HOSTNAME = 'localhost'
USERNAME = 'amagis'
PASSWORD = '3bbByr62ZqhdksVkH7Wy'
DB = '100i'

import MySQLdb
import numpy as np
import datetime, re
from csv import reader
from range import Range

from errors import MyError

FIRST_BLOOD_DRAW=datetime.datetime(2014, 6, 24)
SECOND_BLOOD_DRAW=datetime.datetime(2014, 9, 30)

class Database(object):

    def __init__(self):

        # Open MySQL connection
        self.db = MySQLdb.connect(host=HOSTNAME, user=USERNAME, passwd=PASSWORD, db=DB)

    def __del__(self):

        # Close the database
        self.db.close()

    def Get(self, table, key, value, field='*', orderby=None):

        # Get the cursor
        cursor = self.db.cursor()

        if (orderby is None):
            cursor.execute("SELECT " + ','.join(field) + " FROM " + table + " WHERE " + key + " = (%s)", (value,))
        else:
             cursor.execute("SELECT " + ','.join(field) + " FROM " + table + " WHERE " + key + " = (%s) ORDER BY " + orderby, (value,))
        return cursor

    def GetCursor(self):
        return self.db.cursor();

    def Commit(self):
        self.db.commit();

    def GetCompliance(self, username):

        cursor = self.db.cursor()

        # Get the cursor
        cursor = self.db.cursor();

        cursor.execute("SELECT * FROM compliance WHERE username = (%s)", (username,))
        result = None
        columns = [d[0] for d in cursor.description]

        # Concatenate all the tuples together
        for row in cursor:
            if (result is None):
                result = row
            else:
                result = zip(result, row)

        if (result is None):
            return {}

        if (len(result)==0):
            return {}

        # Now convert each value into a numpy array
        final = {}
        for key, values in zip(columns, result):
            if (key == "USERNAME"):
                continue;
            try:
                final[key] = int(values)
            except:
                final[key] = values
        return final

    def GetData(self, username):

        # Get the cursor
        cursor = self.db.cursor();

        cursor.execute("SELECT * FROM data4 WHERE username = (%s) ORDER BY ROUND", (username,))
        result = None
        columns = [d[0] for d in cursor.description]

        # Concatenate all the tuples together
        result = []
        for row in cursor:
            result.append(row)
        result = zip(*result)
        print result

        """
        # Concatenate all the tuples together
        for row in cursor:
            if (result is None):
                result = (row)
            else:
                result = zip(*result, row)
        """

        if (result is None):
            return {}

        if (len(result)==0):
            return {}

        print columns
        print result

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

    def GetAll(self, table):

         # Get the cursor
        cursor = self.db.cursor()

        cursor.execute("SELECT * FROM " + table)
        return cursor

    def Command(self, command):

        cursor = self.db.cursor()
        cursor.execute(command);
        return cursor;

    def GetHeaders(self, table):

        # Get the cursor
        cursor = self.db.cursor();

        cursor.execute("SELECT * FROM " + table + " LIMIT 1");
        columns = [d[0] for d in cursor.description];
        return columns;

    def GetInternalIDMapping(self):

        cursor = self.db.cursor()
        cursor.execute("SELECT MEASUREMENT,INTERNAL_ID FROM ranges");
        mapping = {};
        for (measurement, id) in cursor:
            mapping[id] = measurement
        return mapping

    def GetMeasurementByRound(self, measurement, username, round):

        cursor = self.db.cursor()
        cursor.execute("SELECT " + measurement + " FROM data4 WHERE USERNAME = (%s) and ROUND = (%s)", (username,round))
        results = [];
        for row in cursor:
            results.append(row)

        # Return nothing if it is not filled in
        if (len(results)==0):
            return None

        # Error if there are multiple results
        if (len(results)>1):
            raise MyError('Multiple results back from database for %s %s %s'%(measurement, username, str(round)))

        # Return the actual value
        return results[0]

    def GetMeasurementByDate(self, measurement, username, date):

        cursor = self.db.cursor()
        cursor.execute("SELECT " + measurement + " FROM data4 WHERE USERNAME = (%s) and DATE = (%s)", (username,date))
        results = [];
        for row in cursor:
            results.append(row)

        # Return nothing if it is not filled in
        if (len(results)==0):
            return None

        # Error if there are multiple results
        if (len(results)>1):
            raise MyError('Multiple results back from database for %s %s %s'%(measurement, username, str(date)))

        # Return the actual value
        return results[0]

    def LoadRanges(self):

        # Dictionary to store the results
        ranges = {};

        # Retrieve all the ranges from the database
        results = self.Command("SELECT * FROM ranges")

        for (measurement, unit, male_low, male_med, male_high, female_low, female_med, female_high, hmdb, internal_id) in results:
            range = Range(measurement, unit, male_low, male_med, male_high, female_low, female_med, female_high, hmdb, internal_id)
            if (not range.measurement in ranges):
                ranges[range.measurement] = range
            else:
                raise MyError("Warning: range for measurement %s already exists" % range.measurement)
        print "Loaded %d reference ranges" % len(ranges)
        return ranges;

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

    def UpdateData(self, username, round, db_date, date_ordered, data, mapping):

        # For this we check each value individually. If data is missing at a position, we fill it in.
        # Otherwise, we only update it if date_ordered is more recent than db_date
        update = False
        if (date_ordered > db_date):
            update = True

        # Go through each data point in my dictionary
        for key in data.keys():

            # Get the new value
            new_value = self.Clean(data[key]);

            # Do not insert a null value
            if (new_value is None):
                continue;

            # Skip the key if we don't have a place for it
            if (not key in mapping):
                continue;

            # Get the value from this row for the old date
            original_value = self.GetMeasurementByDate(mapping[key], username, db_date)

            # If it returns None, this is an error. This function is for updating, not inserting
            if (original_value is None):
                raise MyError('Attempted insertion in UpdateData with username %s and round %d'%(username, round));

            # Otherwise, get the value
            original_value = original_value[0];

            # If this is None or update = True, we can set the value
            if (original_value is None) or (update):

                command = "UPDATE data4 SET %s = '%s' WHERE USERNAME = '%s' AND DATE = '%s'"%(mapping[key], new_value, username, db_date)
                self.Command(command);

            """
            elif (original_value != new_value):

                # Take this away
                command = "UPDATE data SET %s = '%s' WHERE USERNAME = '%s' AND DATE = '%s'"%(mapping[key], new_value, username, db_date)
                print command
                self.Command(command);
            """

        # Finally, update the date so we don't repeat ourselves
        # TODO: I'm not sure how this will affect Quest additions, so leave it off for now.
        if (update):
            command = "UPDATE data4 SET %s = '%s' WHERE USERNAME = '%s' AND DATE = '%s'"%('DATE', date_ordered, username, db_date)
            #print command
            #self.Command(command);

    def InsertData(self, username, round, date_ordered, data, mapping):

        # Build the insertion statement
        command = "INSERT INTO data4 (USERNAME,ROUND,DATE";
        for key in data.keys():

            if (not key in mapping):
                continue;

            command += ','+mapping[key];

        command += ") VALUES (%s, %s, %s";

        # Build tuple for parameterization
        tdata = (username, round, date_ordered.strftime('%Y-%m-%d %H:%M:%S'))

        for key in data.keys():

            if (not key in mapping):
                continue;

            command += ', %s';
            tdata += (self.Clean(data[key]),);

        command += ")";

        # Get the cursor
        cursor = self.db.cursor();
        cursor.execute(command, tdata)

    def LoadQuest(self, filename):

        # Create regular expression for the measurement
        id_reg = re.compile(r"\([0-9]{8}\)");
        #username_reg = re.compile(r"[0-9]{7}(?!\S)");
        username_reg = re.compile(r"[0-9]{7}");

        # Get the headers from the data table
        mapping = self.GetInternalIDMapping()

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


    def LoadGenova(self, filename):

        titles = None
        headers = None

        # Get the headers from the data table
        mapping = self.GetInternalIDMapping()

        with open(filename, 'rU') as f:
            for line in f:

                # Load the headers, removing the final 9 columns
                if (titles is None):
                    titles = line.strip().split('\t')[:-9]

                # Next load the identifiers, removing the final 9 columns
                elif (headers is None):
                    headers = line.strip().split('\t')[:-9]

                # Finally, load the data, removing the final 9 columns
                else:
                    tokens = line.strip().split('\t')[:-9]

                    # Convert into dictionary
                    data = dict(zip([x.strip().upper() for x in headers], [x.strip().upper() for x in tokens]))

                    # Get username from this row
                    username = data["LAST NAME"]

                    print tokens
                    print username

                    # Get date from this row
                    date_ordered = datetime.datetime.strptime(data['DATE ORDERED'], "%m/%d/%y");
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
                        print "Found round %d for username %s"%(round, username);

                        # Get the associated date
                        db_date = result[0];
                        if (db_date is None):
                            raise MyError('No date for username %s and round %d'%(username, round));

                        # Update data
                        self.UpdateData(username, round, db_date, date_ordered, data, mapping)

                    # There was no row found, so insert a new row!
                    # TODO: we could check to see if the date already exists as well
                    else:

                        # Insert new row
                        print "Inserting for username %s date %s"%(username, date_ordered)
                        self.InsertData(username, round, date_ordered, data, mapping)

    def CreateDataTable(self):

        # Get the ranges, which will determine what we load in
        ranges = self.LoadRanges();

        command = ""
        command += "CREATE TABLE data4 (ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, DATE DATETIME, ROUND INT NOT NULL"
        count = 0

        for key in sorted(ranges.keys()):
                command += ", " + key.upper().replace('-','_').replace('/','_').replace(' ', '_').replace('.','_') + " FLOAT"
        command += ")"

        # First create columns
        self.Command(command)





