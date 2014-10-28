#!/usr/bin/env python

# System imports
import time, sys, argparse, math
import numpy as np

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
    x = participants.MetaboliteTraitCorrelation('Vitamin D insufficiency', 'VITAMIN_D')

    # Generate histogram of the score column
    (probability, bins) = np.histogram(x['Score'], bins=5)

    print probability
    print bins

    # Now calculate the average
    start = bins[0]
    count = 1
    for end in bins[1:]:

        count += 1

        # Get the subset of indices for these values
        if (count == len(bins)):
            indices = (x['Score'] >= start) & (x['Score'] <= end)
        else:
            indices = (x['Score'] >= start) & (x['Score'] < end)

        # Get the values of round1 for these indices
        subset = x['Round2'][indices]
        subind = x['Score'][indices]

        # Calculate the mean and stdev of these values
        mean = np.nanmean(subset)
        sd = np.nanstd(subset)
        stderr = sd / math.sqrt(len(subset))

        print mean, stderr

        start = end

    data = []

    # Now we get the supplementation level for each of these people
    for prt in x['Username']:

        # Get the compliance for vitamin D and supplementation level
        compliance = participants.participants[prt].compliance['vitD_compliance']
        amount = participants.participants[prt].compliance['vitD_amount']
        data.append((x[prt]['Username'], prt, compliance, amount))

    x = np.array(data, dtype=[('Username', np.str, 10), ('Username2', np.str, 10), ('Compliance', float), ('Amount', float)])
    print x

if __name__ == "__main__":
    main(ArgParser())

