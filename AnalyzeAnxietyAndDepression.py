#!/usr/bin/env python

# System imports
import time, sys, argparse, math
import numpy as np
from scipy import stats

# Import the database class
from dbsnp import DBSnp
from database import Database

# Import the individual participant
from participant import ParticipantDB

def ArgParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--trait', default="Vitamin D", help="Trait")
    parser.add_argument('-m', '--measurement', default="VITAMIN_D", help="Measurement")
    args = parser.parse_args()
    return args

def main(parser):

    # Set the output directory
    output_dir = './results'

    # Open connection to MySQL database
    database = Database()

    # Load the DBSnp database
    dbsnp = DBSnp(database)

    # Create the participant DB from the database
    participants = ParticipantDB(database, None, None, None, None, dbsnp)

    print "Trait: %s"%(parser.trait)
    print "Measurement: %s"%(parser.measurement)

    # Loop over all the participants, and get the R1 and R2 metabolite + genetic score
    #x = participants.MetaboliteTraitCorrelation('Homocysteine levels', 'HOMOCYSTEINE_CARDIOVASCULAR_QUEST', 1e-50)
    x = participants.MetaboliteTraitCorrelation('COMT', 'HOMOCYSTEINE_CARDIOVASCULAR_QUEST', 1)
    data = []

    # Now we get the supplementation level for each of these people
    for username, gender, round1, round2, round3, score in x:

        # Get the compliance for vitamin D and supplementation level
        gender = participants.participants[prt].gender
        anxiety = participants.participants[prt].compliance['anxiety']
        depression = participants.participants[prt].compliance['depression']
        stress = participants.participants[prt].compliance['chronic_stress']

        print anxiety, depression, stress

        if (anxiety is None):
            anxiety = 0
        if (depression is None):
            depression = 0
        if (stress is None):
            stress = 0

        data.append((prt, gender, round1, round2, score, anxiety, depression, stress))

    x = np.array(data, dtype=[('Username', np.str, 10), ('Gender', np.str, 1), ('Round1', float), ('Round2', float), ('Score', float), ('Anxiety', float), ('Depression', float), ('Stress', float)])

    for (username, gender, round1, round2, score, anxiety, depression, stress) in x:
        print username, gender, round1, round2, score, anxiety, depression, stress

if __name__ == "__main__":
    main(ArgParser())

