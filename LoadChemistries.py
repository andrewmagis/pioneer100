#!/usr/bin/env python

# System imports
import argparse

# Import the database class
from database import Database
from chemistries import Chemistries


def ArgParser():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    return args

def main(parser):

    # Open connection to MySQL database
    database = Database()

    # If necessary, build the data table
    #database.CreateDataTable()

    chem = Chemistries(database)

    quest_files = ["./db/QuestSpreadsheets/Quest.5.11212014/all.quest.csv"]

    #for file in quest_files:
    #    chem.LoadQuest(file)

    # Load the data <- allocate some time to do this! It takes a while!
    #genova_files = ["./db/GenovaSpreadsheets/Genova.3.09232014/Hood.Nutreval.Binary.9.15.14 C.txt",
    #         "./db/GenovaSpreadsheets/Genova.3.09232014/Hood.Metsyn.Binary.9.15.14 C.txt",
    #         "./db/GenovaSpreadsheets/Genova.3.09232014/Hood.VitaminD.Binary.9.15.14 C.txt",
    #         "./db/GenovaSpreadsheets/Genova.3.09232014/Hood.NutrientToxicElements.Binary.9.15.14 C.txt"]

    #genova_files = ["./db/GenovaSpreadsheets/Genova.4.11122014/Hood.NutrEval.Binary.11.10.14.txt",
    #         "./db/GenovaSpreadsheets/Genova.4.11122014/Hood.MetSyn.Binary.11.10.14.txt",
    #         "./db/GenovaSpreadsheets/Genova.4.11122014/Hood.VitaminD.Binary.11.10.14.txt",
    #         "./db/GenovaSpreadsheets/Genova.4.11122014/Hood.NutrientToxicElements.Binary.11.10.14.txt"]

    """
    genova_files = ["./db/GenovaSpreadsheets/Genova.5.11212014/Hood.NutrEval.Binary.11.21.14.txt",
             "./db/GenovaSpreadsheets/Genova.5.11212014/Hood.MetSyn.Binary.11.21.14.txt",
             "./db/GenovaSpreadsheets/Genova.5.11212014/Hood.VitD.Binary.11.21.14.txt",
             "./db/GenovaSpreadsheets/Genova.5.11212014/Hood.NutrientToxicElements.Binary.11.21.14.txt"]
    """
    genova_files = ["./db/GenovaSpreadsheets/Genova.5.11212014/final.txt"]


    for f in genova_files:
        print "Loading file", f
        chem.LoadGenova(f)


if __name__ == "__main__":
    main(ArgParser())

