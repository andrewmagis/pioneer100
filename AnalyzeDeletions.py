#!/usr/bin/env python

# System imports
import time, sys, argparse, math
import numpy as np
from scipy import stats

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

    # Open connection to Clinvar database
    clinvar_db = Clinvar(database)

    # Create the participant DB from the database
    participants = ParticipantDB(database, None, None, None, clinvar_db, dbsnp)

    # Load the data
    with open('db/deletions.txt', 'rU') as f:
        for line in f:
            print line

    """
    print "Trait: %s"%(parser.trait)
    print "Measurement: %s"%(parser.measurement)

    # Loop over all the participants, and get the R1 and R2 metabolite + genetic score
    x = participants.MetaboliteTraitCorrelation('Vitamin D 2', 'VITAMIN_D')

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
    for (prt, round1, round2, score) in x:

        # Get the compliance for vitamin D and supplementation level
        compliance = participants.participants[prt].compliance['vitD_compliance']
        amount = participants.participants[prt].compliance['vitD_amount']
        data.append((prt, round1, round2, score, compliance, amount))

    x = np.array(data, dtype=[('Username', np.str, 10), ('Round1', float), ('Round2', float), ('Score', float), ('Compliance', float), ('Amount', float)])

    # The next is to select subsets of the data based on the supplementation level
    dat1000 = x[:][x['Amount']==1000]
    dat2000 = x[:][x['Amount']==2000]
    dat3000 = x[:][x['Amount']==3000]
    dat4000 = x[:][x['Amount']==4000]
    dat5000 = x[:][x['Amount']==5000]
    dat6000 = x[:][x['Amount']==6000]
    dat10000 = x[:][x['Amount']==10000]

    print dat1000.size, dat2000.size, dat3000.size, dat4000.size, dat5000.size, dat6000.size, dat10000.size

    d4000 = []

    # Start with 4000
    for (prt, round1, round2, score, compliance, amount) in x:

        if (compliance == 0):
            continue
        if (np.isnan(amount)):
            continue
        if (np.isnan(round1)):
            continue
        if (np.isnan(round2)):
            continue

        d4000.append((prt, round1, round2, round2-round1, score, amount))


    x4000 = np.array(d4000, dtype=[('Username', np.str, 10), ('Round1', float), ('Round2', float), ('Diff', float), ('Score', float), ('Amount', float)])
    print x4000

    (R, P) = stats.pearsonr(x4000['Diff'], x4000['Score'])
    print R, P

    for (username, round1, round2, diff, score, amount) in x4000:
        print username, round1, round2, diff, score, amount
    """

if __name__ == "__main__":
    main(ArgParser())

