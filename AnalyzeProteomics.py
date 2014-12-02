#!/usr/bin/env python

# System imports
import argparse
from datetime import datetime

# Import the database class
from database import Database
from participant import ParticipantDB
from qs import QS
from proteomics import Proteomics
from chemistries import Chemistries

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

    # Get proteomics object
    prots = Proteomics(database)

    # Get chemistry object
    chem = Chemistries(database)

    # Create the QS object
    qs = QS(database)

    if (not parser.filename is None):
        prots.LoadData(parser.filename, parser.category)
        return

    print "Getting chemistry data"
    result = chem._get_val('1115268', 1, ('3_hydroxyisovaleric_acid'))
    return

    print "Getting proteomics data"
    result = prots._get_diff('1115268', 1, 2)
    print result

    print "Getting qs data"
    # Dates for blood draws for proteomics
    FIRST_BLOOD_DRAW=datetime(2014, 5, 1)
    SECOND_BLOOD_DRAW=datetime(2014, 8, 1)
    THIRD_BLOOD_DRAW=datetime(2014, 11, 1)

    result = qs.get_val('1115268', FIRST_BLOOD_DRAW)
    print result['1115268']





if __name__ == "__main__":
    main(ArgParser())

