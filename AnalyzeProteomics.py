#!/usr/bin/env python

# System imports
import argparse

# Import the database class
from database import Database
from participant import ParticipantDB
from qs import QS
from proteomics import Proteomics

# Import DBSnp class
from dbsnp import DBSnp
from clinvar import Clinvar

def ArgParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', default=None, help="Proteomics input filename")
    parser.add_argument('-c', '--category', default=None)
    args = parser.parse_args()
    return args

def main(parser):

    # Open connection to MySQL database
    database = Database()

    # Create the QS object
    prots = Proteomics(database)

    if (not parser.filename is None):
        prots.LoadData(parser.filename, parser.category)
        return

    result = prots.GetNormalized('9691870', 1)
    return

    # Load the DBSnp database
    dbsnp = DBSnp(database)

    # Open connection to Clinvar database
    clinvar_db = Clinvar(database)

    # Load the participants
    participants = ParticipantDB(database, None, None, None, clinvar_db, dbsnp)

    # Now we can analyze the proteomics data



if __name__ == "__main__":
    main(ArgParser())

