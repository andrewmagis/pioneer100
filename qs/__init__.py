
from datetime import date, datetime, timedelta as td
import fitbit
from errors import MyError

import numpy as np
import scipy
import math

OWNER_KEY = '0fcad4c11b0944e790b9043effd5ef41'
OWNER_SECRET = 'b90405040b274d93b4c504052489e1a9'
FIRST_FITBIT_DATE=datetime(2014, 04, 20);

class QS(object):

    def __init__(self, database):
        self.database = database

    def get_average(self, username, start=None, stop=None):

        if (start is None) and (end is None):
            pass

        elif (start is None):
            pass

        elif (stop is None):
            pass

        # Get the data within a range
        else:
            cursor = self.database.GetCursor()
            cursor.execute("SELECT ACTIVITYCALORIES FROM qs WHERE USERNAME = (%s) AND DATE >= (%s) AND DATE <= (%s)", (username,start,stop,))

            return np.array(list(cursor.fetchall()), dtype=[(username, float)])


    def GetActivity(self, username):

        cursor = self.database.Get('qs', 'username', username, ['USERNAME', 'DATE', 'CALORIESOUT', 'ACTIVITYCALORIES'], 'DATE')
        active_cals = []

        for (username, date, caloriesout, activitycalories) in cursor:
            active_cals.append(activitycalories)

        active_cals = np.array(active_cals)
        mean_cals = scipy.nanmean(active_cals)
        return mean_cals

    def GetActivityRange(self, username, start_range, end_range):

        if (start_range is None):
            return None
        if (end_range is None):
            return None

        cursor = self.database.Get('qs', 'username', username, ['USERNAME', 'DATE', 'CALORIESOUT', 'ACTIVITYCALORIES'], 'DATE')

        active_cals = []

        for (username, date, caloriesout, activitycalories) in cursor:

            if (date >= start_range) and (date <= end_range):
                active_cals.append(activitycalories)

        days = (end_range-start_range).days

        active_cals = np.array(active_cals)

        index = active_cals > 100
        if (np.sum(index) < 40):
            return None

        mean_cals = scipy.nanmean(active_cals[index])
        return mean_cals

    def GetWeightLossIndividuals(self, username):

        cursor = self.database.Get('weight', 'username', username, ['USERNAME', 'DATE', 'WEIGHT'], 'DATE')

        start_date = None
        end_date = None
        start_weight = None
        end_weight = None

        for (username, date, weight) in cursor:
            if (start_date is None) or (date < start_date):
                start_date = date
                start_weight = weight
            if (end_date is None) or (date > end_date):
                end_date = date
                end_weight = weight

        if (end_date is None):
            return (None, None, None, None)
        if (start_date is None):
            return (None, None, None, None)

        return (start_date, end_date, start_weight, end_weight)

    def GetHeartRateIndividuals(self, username):

        cursor = self.database.Get('heartrate', 'username', username, ['USERNAME', 'DATE', 'HEARTRATE'], 'DATE')

        start_date = None
        end_date = None
        start_hr = None
        end_hr = None

        for (username, date, heartrate) in cursor:
            if (start_date is None) or (date < start_date):
                start_date = date
                start_weight = heartrate
            if (end_date is None) or (date > end_date):
                end_date = date
                end_weight = heartrate

        if (end_date is None):
            return (None, None, None, None)
        if (start_date is None):
            return (None, None, None, None)

        return (start_date, end_date, start_weight, end_weight)

    def AnalyzeQSMeasurement(self, participants, title, measurement, pvalue=1):

        SECOND_BLOOD_DRAW=datetime(2014, 9, 30)

        results = []
        for prt in participants.participants.keys():

            gender = participants.participants[prt].gender

            trait = participants.participants[prt].LoadTrait(title, pvalue, True)

            if (trait is None):
                continue

            #(dates, values, range) = participants.participants[prt].GetMeasurement('AGE')
            (dates, values, range) = participants.participants[prt].GetMeasurement(measurement)

            if (values.size < 2):
                continue
            if (np.isnan(values[0])):
                continue
            if (np.isnan(values[1])):
                continue

            diff = values[1] - values[0]

            mean_cals = self.GetActivityRange(prt, FIRST_FITBIT_DATE, SECOND_BLOOD_DRAW)
            if (not mean_cals is None) and (mean_cals < 2000) and (trait.score > 0.0):
                results.append((prt, gender, values[0], values[1], values[1]-values[0], trait.score, mean_cals))

      # Build numpy structured array of scores
        x = np.array(results, dtype=[('Username', np.str, 10), ('Gender', np.str, 1), ('Round1', float), ('Round2', float), ('Diff', float), ('Score', float), ('Activity', float)])

        # Start by calculating the correlation
        (R, P) = scipy.stats.pearsonr(x['Diff'], x['Activity'])
        print R, P

        # Sort by the score column
        x = np.sort(x, axis=-1, kind='quicksort', order=['Activity'])

        print x

        # Generate histogram of the score column
        (probability, bins) = np.histogram(x['Activity'], bins=5)

        print probability
        print bins

        print
        print "Diff"

        # Now calculate the average
        start = bins[0]
        count = 1
        for end in bins[1:]:

            count += 1

            # Get the subset of indices for these values
            if (count == len(bins)):
                indices = (x['Activity'] >= start) & (x['Activity'] <= end)
            else:
                indices = (x['Activity'] >= start) & (x['Activity'] < end)

            # Get the values of round1 for these indices
            subset = x['Diff'][indices]
            subind = x['Activity'][indices]

            # Calculate the mean and stdev of these values
            mean = np.nanmean(subset)
            sd = np.nanstd(subset)
            stderr = sd / math.sqrt(len(subset))

            print mean, stderr
            start = end

            #if (not mean_cals is None):
            #    print prt, gender, FIRST_FITBIT_DATE, SECOND_BLOOD_DRAW, mean_cals, values[0], values[1], diff, trait.score

    def AnalyzeQS(self, participants, title, pvalue=1):

        for prt in participants.participants.keys():

            gender = participants.participants[prt].gender

            trait = participants.participants[prt].LoadTrait(title, pvalue, True)

            if (trait is None):
                continue

            (dates, values, range) = participants.participants[prt].GetMeasurement('AGE')
            #(dates, values, range) = participants.participants[prt].GetMeasurement('GLUCOSE')

            #(start_range, end_range, start_weight, end_weight) = self.GetWeightLossIndividuals(prt)
            (start_range, end_range, start_weight, end_weight) = self.GetHeartRateIndividuals(prt)

            if (start_range is None):
                continue

            # Make sure the distance is greater than 2 months
            time_elapsed = (end_range - start_range).days
            if (time_elapsed > 60):

                #print start_range, end_range, start_weight, end_weight, gender, time_elapsed

                mean_cals = self.GetActivityRange(prt, start_range, end_range)

                if (not mean_cals is None):
                    print prt, gender, values, start_range, end_range, start_weight, end_weight, end_weight-start_weight, mean_cals, trait.score



        """
        cursor = self.database.Get('qs', 'username', username, ['USERNAME', 'DATE', 'CALORIESOUT'], 'DATE')
        for items in cursor:
            print items

        cursor = self.database.Get('weight', 'username', username, '*', 'DATE')
        for items in cursor:
            print items
        """

    def Update(self, username):

        # Get today's date
        today = datetime.now().date()

        (key, secret) = self.GetFitbitAuth(username);
        if (key is None):
            print "No key authentication information for %s"%(username)
            return False
        if (secret is None):
            print "No secret authentication information for %s"%(username)
            return False

        # Get auth client
        client = fitbit.Fitbit(OWNER_KEY, OWNER_SECRET, resource_owner_key=key, resource_owner_secret=secret)

        # Get current date
        current_date = self.GetLastDate('qs', username)
        if (current_date is None):
            current_date = FIRST_FITBIT_DATE

        # Get the delta
        delta = today - current_date.date()

        for day in range(delta.days + 1):

            # Increment the current day
            current_date = current_date + td(days=1)

            # If the date is today, do not download it
            if (current_date.date() >= today):
                return True

            try:
                print "%s obtaining date: %s"%(username, current_date)
                activities = client._COLLECTION_RESOURCE('activities', date=current_date)
                sleep = client._COLLECTION_RESOURCE('sleep', date=current_date)
            except:
                # Probably ran out of days to download
                return False

            data = {}
            data['caloriesOut'] = activities[u'summary'][u'caloriesOut']
            data['caloriesBMR'] = activities[u'summary'][u'caloriesBMR']
            data['marginalCalories'] = activities[u'summary'][u'marginalCalories']
            data['sedentaryMinutes'] = activities[u'summary'][u'sedentaryMinutes']
            data['lightlyActiveMinutes'] = activities[u'summary'][u'lightlyActiveMinutes']
            data['fairlyActiveMinutes'] = activities[u'summary'][u'fairlyActiveMinutes']
            data['veryActiveMinutes'] = activities[u'summary'][u'veryActiveMinutes']
            data['activityCalories'] = activities[u'summary'][u'activityCalories']
            data['steps'] = activities[u'summary'][u'steps']

            # Get sleep data
            mainSleep = None
            for sleep in sleep[u'sleep']:
                if (sleep[u'isMainSleep']):
                    mainSleep = sleep

            if (not mainSleep is None):
                data['minutesToFallAsleep'] = mainSleep[u'minutesToFallAsleep']
                data['awakeningsCount'] = mainSleep[u'awakeningsCount']
                data['minutesAwake'] = mainSleep[u'minutesAwake']
                data['timeInBed'] = mainSleep[u'timeInBed']
                data['minutesAsleep'] = mainSleep[u'minutesAsleep']
                data['awakeDuration'] = mainSleep[u'awakeDuration']
                data['efficiency'] = mainSleep[u'efficiency']
                data['startTime'] = datetime.strptime(mainSleep[u'startTime'], "%Y-%m-%dT%H:%M:%S.000")
                data['restlessCount'] = mainSleep[u'restlessCount']
                data['restlessDuration'] = mainSleep[u'restlessDuration']

            # Now add the data to the database
            self.InsertData('qs', username, current_date, data)

        # Finished successfully
        print "Somehow got all the data to today without getting today's data"
        return False

    def UpdateAll(self, participants):

        for prt in sorted(participants.participants.keys()):

            status = self.Update(prt)
            if (status):
                print "%s finished updating to yesterday's data"%(prt)
            else:
                print "%s did not finish updating (try again in an hour)"%(prt)

    def GetLastDate(self, table, username):

        cursor = self.database.Get(table, 'username', username, ['USERNAME','DATE'], orderby='DATE')
        final_date = None
        for (username, date) in cursor:
            #print "%s skipping date: %s"%(username, date)
            final_date = date
        return final_date

    def CheckDate(self, table, username, query_date):

        cursor = self.database.Get(table, 'username', username, ['USERNAME','DATE'], orderby='DATE')
        final_date = None
        for (username, date) in cursor:
            if (date == query_date):
                return False
        return True

    def GetFitbitAuth(self, username):

        key = None
        secret = None

        result = self.database.Get('participants', 'username', username)
        for (username, assembly, gender, race, fitbit_key, fitbit_secret) in result:
            if (key is None):
                key = fitbit_key
            else:
                raise MyError('Multiple usernames in participants table')
            if (secret is None):
                secret = fitbit_secret
            else:
                raise MyError('Multiple usernames in participants table')
        return (key, secret)

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

    def LoadHeartRateData(self, filename, participants):

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

                    data = {'HEARTRATE': weight}

                    # Check to see if this date is after the last date in the database
                    if (self.CheckDate('heartrate', username, dt)):
                        self.InsertData('heartrate', username, dt, data);

                except:
                    pass

    def LoadBloodPressureData(self, filename, participants):

        with open(filename, 'Ur') as f:
            for line in f:

                tokens = line.split('\t')
                if (len(tokens)<11):
                    print tokens
                    continue

                try:

                    username = tokens[6].strip()
                    if (not username in participants.participants):
                        continue

                    systolic = float(tokens[7].strip())
                    diastolic = float(tokens[8].strip())
                    date = tokens[9].strip() + ' ' + tokens[10].strip()
                    dt = datetime.strptime(date, "%m/%d/%y %I:%M %p")

                    data = {'SYSTOLIC': systolic, 'DIASTOLIC': diastolic}

                    # Check to see if this date is after the last date in the database
                    if (self.CheckDate('bloodpressure', username, dt)):
                        self.InsertData('bloodpressure', username, dt, data);

                except:
                    pass

    def CreateWeightTable(self):

        command = ""
        command += "CREATE TABLE weight (ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, DATE DATETIME NOT NULL, WEIGHT FLOAT NOT NULL)"

        # First create columns
        self.database.Command(command)

    def CreateHeartRateTable(self):

        command = ""
        command += "CREATE TABLE heartrate (ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, DATE DATETIME NOT NULL, HEARTRATE INT NOT NULL)"

        # First create columns
        self.database.Command(command)

    def CreateBloodPressureTable(self):

        command = ""
        command += "CREATE TABLE bloodpressure (ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, DATE DATETIME NOT NULL, SYSTOLIC INT NOT NULL, DIASTOLIC INT NOT NULL)"

        # First create columns
        self.database.Command(command)

    def CreateTable(self):

        command = ""
        command += "CREATE TABLE qs(ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, DATE DATETIME NOT NULL, \
                   CALORIESOUT INT, CALORIESBMR INT, MARGINALCALORIES INT, SEDENTARYMINUTES INT, LIGHTLYACTIVEMINUTES INT, FAIRLYACTIVEMINUTES INT, \
                   VERYACTIVEMINUTES INT, ACTIVITYCALORIES INT, STEPS INT, MINUTESTOFALLASLEEP INT, AWAKENINGSCOUNT INT, MINUTESAWAKE INT, \
                   TIMEINBED INT, MINUTESASLEEP INT, AWAKEDURATION INT, EFFICIENCY INT, STARTTIME DATETIME, RESTLESSCOUNT INT, RESTLESSDURATION INT)"

        # First create columns
        self.database.Command(command)