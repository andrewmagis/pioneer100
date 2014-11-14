#!/usr/bin/env python

# System imports
import argparse

# Import the database class
from database import Database
from participant import ParticipantDB
from qs import QS

def ArgParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--weight', default=None)
    parser.add_argument('-r', '--heartrate', default=None)
    parser.add_argument('-b', '--bloodpressure', default=None)
    parser.add_argument('-f', '--fitbit', default=None, action='store_true', help="Update Fitbit data")
    args = parser.parse_args()
    return args

def main(parser):

    # Open connection to MySQL database
    database = Database()

    # Create the QS object
    qs = QS(database)

    # Load the participants
    participants = ParticipantDB(database, None, None, None, None, None)

    # Pull Fitbit data via the API
    if (parser.fitbit):
        #qs.CreateTable()
        qs.UpdateAll(participants)

    elif (not parser.weight is None):
        #qs.CreateWeightTable()
        qs.LoadWeightData(parser.weight, participants)

    elif (not parser.heartrate is None):
        #qs.CreateHeartRateTable()
        qs.LoadHeartRateData(parser.heartrate, participants)

    elif (not parser.bloodpressure is None):
        #qs.CreateBloodPressureTable()
        qs.LoadBloodPressureData(parser.bloodpressure, participants)

    else:
        print "No QS data to load"


if __name__ == "__main__":
    main(ArgParser())

