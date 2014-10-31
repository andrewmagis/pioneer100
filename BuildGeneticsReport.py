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

# Import the individual participant
from participant import ParticipantDB

def ArgParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', default=None, help="Force comparison report")
    parser.add_argument('-c', '--comparison_reports', action='store_true', help="Create comparison reports")
    parser.add_argument('-p', '--pharmacogenetics_reports', action='store_true', help="Create pharmacogenenetics reports");
    parser.add_argument('-r', '--genetic_reports', action='store_true', help='Create genetics reports')
    parser.add_argument('-d', '--disease_reports', action='store_true', help='Create disease reports')
    parser.add_argument('-a', '--DNAlysis_reports', action='store_true', help='Create DNALysis output file')
    args = parser.parse_args()
    return args

def BuildGeneticReports(participants):
    for key in participants.participants.keys():
        report = GeneticsReport(participants.participants[key]);
        report.go();

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

    # Build the comparison reports if requested, and do nothing else
    if (parser.comparison_reports):
        participants.BuildTransitionReports(parser.force)
        return
    elif (parser.pharmacogenetics_reports):
        participants.BuildPharmacogeneticsReports(parser.force)
        return
    elif (parser.genetic_reports):
        BuildGeneticReports(participants)
        return
    elif (parser.disease_reports):
        participants.BuildDiseaseReports(parser.force)
        return
    elif (parser.DNAlysis_reports):
        participants.BuildDNAlysis()
    else:
        print "Unknown report option"


if __name__ == "__main__":
    main(ArgParser())

