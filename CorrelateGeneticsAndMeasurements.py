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
    parser.add_argument('-p', '--pvalue', required=False, default=1, type=float, help="Pvalue")
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

    # Load the genome class
    genome = Genome()
    #genome.Load()

    # Create the participant DB from the database
    participants = ParticipantDB(database, None, None, None, clinvar_db, dbsnp)

    # Load the trait
    #participants.LoadTrait('Fasting glucose-related traits')

    result = database.GetData('7890752')
    print result
    return

    print "Trait: %s"%(parser.trait)
    print "Measurement: %s"%(parser.measurement)
    participants.MetaboliteTraitCorrelation(parser.trait, parser.measurement, parser.pvalue)

    #participants.MetaboliteTraitCorrelation('Fasting glucose-related traits', 'GLUCOSE_QUEST')
    #participants.MetaboliteTraitCorrelation('Homocysteine levels', 'HOMOCYSTEINE_CARDIOVASCULAR_QUEST')
    #participants.MetaboliteTraitCorrelation('Cholesterol, total', 'TOTAL_CHOLESTEROL')
    #participants.MetaboliteTraitCorrelation('LDL Cholesterol', 'LDL_CHOLESTEROL')
    #participants.MetaboliteTraitCorrelation('Vitamin D insufficiency', 'VITAMIN_D')

    # Add the GWAS variants for participants
    #participants.AddGWASVariants()
    #participants.ProcessGWAS()

    #participants.TempAnalysis('Fasting glucose-related traits', 'GLUCOSE_QUEST')

    # Add all the actionable variants for participants
    #participants.AddActionableVariants()
    #participants.ProcessActionable('FERRITIN')
    #participants.TempAnalysis('FERRITIN_QUEST', 'FERRITIN')

    # Measurement/Trait comparisons
    # This is working.  LDL Cholesterol vs LDL Cholesterol variants give the best results
    # Feel free to expand this out and include more traits
    #
    #participants.TempAnalysis('LDL_CHOLESTEROL', 'LDL_CHOLESTEROL')
    #participants.TempAnalysis('HDL_CHOLESTEROL', 'HDL_CHOLESTEROL')
    #participants.TempAnalysis('LDL_PARTICLE', 'TOTAL_CHOLESTEROL')
    #participants.TempAnalysis('BODY_MASS_INDEX', 'BODY_MASS_INDEX')


if __name__ == "__main__":
    main(ArgParser())

