#!/usr/bin/env python

# System imports
import argparse

# Import the database class
from database import Database
from participant import ParticipantDB
from qs import QS

def ArgParser():
    parser = argparse.ArgumentParser()
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

    qs.AnalyzeQS(participants)


if __name__ == "__main__":
    main(ArgParser())

