#!/usr/bin/env python

# System imports
import time, sys, argparse

# PDF reports
from pdf import GeneticsReport

# Import the genetics processing library
from gwasdb import GwasDB
from actionabledb import ActionableDB
from pharmacogenomicsdb import PharmacogenomicsDB

# Import genome class
from genome import Genome

# Import DBSnp class
from dbsnp import DBSnp
from clinvar import Clinvar

# Import the database class
from database import Database

from trait import Trait

# Import the individual participant
from participant import ParticipantDB

def ArgParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--trait', required=True, default=None, help="Trait")
    parser.add_argument('-m', '--measurement', required=True, default=None, help="Measurement")
    args = parser.parse_args()
    return args

def main(parser):

    # Set the output directory
    output_dir = './results'

    # Open connection to MySQL database
    database = Database()

    # Load the DBSnp database
    dbsnp = DBSnp(database)

    # Open connection to Clinvar database
    clinvar_db = Clinvar(database)

    # Create the participant DB from the database
    participants = ParticipantDB(database, None, None, None, clinvar_db, dbsnp)

    print "Trait: %s"%(parser.trait)
    print "Measurement: %s"%(parser.measurement)

    # Loop over all the participants, and get the R1 and R2 metabolite + genetic score
    data = participants.MetaboliteTraitCorrelation('Vitamin D insufficiency', 'VITAMIN_D')
    print data


if __name__ == "__main__":
    main(ArgParser())

