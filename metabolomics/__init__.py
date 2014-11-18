
from datetime import date, datetime, timedelta as td
import fitbit
from errors import MyError

import numpy as np
import scipy
import math

FIRST_FITBIT_DATE=datetime(2014, 04, 20);

class Metobolomics(object):

    def __init__(self, database):
        self.database = database

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

    def CreateTable(self):

        command = ""
        command += "CREATE TABLE qs(ENTRY INT PRIMARY KEY AUTO_INCREMENT, USERNAME VARCHAR(16) NOT NULL, DATE DATETIME NOT NULL, \
                   CALORIESOUT INT, CALORIESBMR INT, MARGINALCALORIES INT, SEDENTARYMINUTES INT, LIGHTLYACTIVEMINUTES INT, FAIRLYACTIVEMINUTES INT, \
                   VERYACTIVEMINUTES INT, ACTIVITYCALORIES INT, STEPS INT, MINUTESTOFALLASLEEP INT, AWAKENINGSCOUNT INT, MINUTESAWAKE INT, \
                   TIMEINBED INT, MINUTESASLEEP INT, AWAKEDURATION INT, EFFICIENCY INT, STARTTIME DATETIME, RESTLESSCOUNT INT, RESTLESSDURATION INT)"

        # First create columns
        self.database.Command(command)