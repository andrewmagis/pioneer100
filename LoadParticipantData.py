#!/usr/bin/env python

# System imports
import argparse

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
    args = parser.parse_args()
    return args


def main(parser):

    # Open connection to MySQL database
    database = Database()

    # If necessary, build the data table
    database.CreateDataTable()

    # Load the data <- allocate some time to do this! It takes a while!
    genova_files = ["./db/GenovaSpreadsheets/Genova.3.09232014/Hood.Nutreval.Binary.9.15.14 C.txt",
             "./db/GenovaSpreadsheets/Genova.3.09232014/Hood.Metsyn.Binary.9.15.14 C.txt",
             "./db/GenovaSpreadsheets/Genova.3.09232014/Hood.VitaminD.Binary.9.15.14 C.txt",
             "./db/GenovaSpreadsheets/Genova.3.09232014/Hood.NutrientToxicElements.Binary.9.15.14 C.txt"]

    for f in genova_files:
        print "Loading file", f
        database.LoadGenova(f)

    quest_files = ["./db/QuestSpreadsheets/Quest.3.09232014/all.quest.csv"]

    for f in quest_files:
        print "Loading file", f
        database.LoadQuest(f)

if __name__ == "__main__":
    main(ArgParser())

