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
    parser.add_argument('-g', '--gwas', default='./db/Alzheimers.txt', help="GWAS Catalog file")
    parser.add_argument('-a', '--actionable', default='./db/100i.Actionable.Variants.txt')
    parser.add_argument('-f', '--force', default=None, help="Force comparison report")
    parser.add_argument('-c', '--comparison_reports', action='store_true', help="Create comparison reports")
    parser.add_argument('-p', '--pharmacogenetics_reports', action='store_true', help="Create pharmacogenenetics reports");
    parser.add_argument('-r', '--genetic_reports', action='store_true', help='Create genetics reports')
    parser.add_argument('-d', '--disease_reports', action='store_true', help='Create disease reports')
    args = parser.parse_args()
    return args


class DBSnpEntry:
    def __init__(self, line):
        tokens = line.split('\t')
        self.chr = tokens[0].strip()
        self.pos = tokens[1].strip()
        self.dbsnp = tokens[2].strip()
        self.ref = tokens[3].strip()
        self.alt = tokens[4].strip()

    def Print(self):
        print self.chr, self.pos, self.dbsnp, self.ref, self.alt;


class Gene:
    def __init__(self, line):
        tokens = line.split('\t');
        self.chr = tokens[0];
        self.source = tokens[1];
        self.feature = tokens[2];
        self.start = int(tokens[3]);
        self.end = int(tokens[4]);
        self.strand = tokens[6];


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

    # Load the genome class
    genome = Genome()
    #genome.Load()

    # Load the actionable database
    actionable_db = ActionableDB(dbsnp, genome)
    #actionable_db.Load(parser.actionable)

    # Now load the GWAS database
    gwas_db = GwasDB(dbsnp, genome)
    #gwas_db.Load(parser.gwas)

    # Load the pharmacogenomics database
    pharm_db = PharmacogenomicsDB(dbsnp, genome)
    #pharm_db.Load()

    # Create the participant DB from the database
    participants = ParticipantDB(database, actionable_db, gwas_db, pharm_db, clinvar_db)

    #participants.Round1VsRound2FishOil()
    #participants.Round1VsRound2Exercise()
    participants.Round1VsRound2VitaminD()

    # Run the classification function
    #participants.Classification()
    participants.KristinStats()

if __name__ == "__main__":
    main(ArgParser())

