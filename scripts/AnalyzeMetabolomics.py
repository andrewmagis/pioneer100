#!/usr/bin/env python

# System imports
import argparse

# Import the database class
from database import Database
from participant import ParticipantDB
from qs import QS
from metabolomics import Metabolomics

# Import DBSnp class
from dbsnp import DBSnp
from clinvar import Clinvar

def ArgParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', default=None, help="Metabolomics input filename")
    args = parser.parse_args()
    return args

def main(parser):

    # Open connection to MySQL database
    database = Database()

    # Create the QS object
    mets = Metabolomics(database)

    if (not parser.filename is None):
        #mets.CreateMetabolitesTable(parser.filename)
        #mets.CreateMetabolomicsTable(parser.filename)
        #mets.LoadMetabolomicsData(parser.filename)
        pass

    mets.Compile()

    return

    # Load the DBSnp database
    dbsnp = DBSnp(database)

    # Open connection to Clinvar database
    clinvar_db = Clinvar(database)

    # Load the participants
    participants = ParticipantDB(database, None, None, None, clinvar_db, dbsnp)



if __name__ == "__main__":
    main(ArgParser())

