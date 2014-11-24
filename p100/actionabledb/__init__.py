"""
    __init__.py "

    Author: Andrew Magis
    Date: July 29th, 2014

"""

from actionablevariant import ActionableVariant
from p100.trait import Trait
from p100.errors import MyError

class ActionableDB(object):
    def __init__(self, dbsnp, genome):

        self.db = {}
        self.variants = {}
        self.ids = []
        self.dbsnp = dbsnp
        self.genome = genome

        # Counters
        self.failed = 0
        self.passed = 0
        self.failed_nogene = 0
        self.failed_nostrand = 0
        self.failed_posstrand = 0
        self.passed_negstrand = 0
        self.failed_negstrand = 0

    def Load(self, filename):

        update = False
        with open(filename, 'Ur') as f:
            next(f)  # Skip the header line
            for line in f:
                self.AddVariant(line)

    def AddVariant(self, line):

        if (len(line.strip()) == 0):
            return False

        # Create the variant
        var = ActionableVariant(line)

        # Validate the variant using superclass
        (isvalid, reason) = var.IsValid(self.dbsnp, self.genome)
        print var.dbsnp, isvalid, reason

        # If returns invalid because missing from database, set the flag
        # to update the database and reload
        if (not isvalid) and (reason == 6):
            return True

        # If it is valid, add the variant
        if (isvalid):

            # Add the variant to the variant database
            if (not var.key in self.variants):
                self.variants[var.key] = var

            # Get the trait for this variant
            if (not var.trait in self.db):
                trait = Trait(var.trait)
                trait.AddVariant(var)
                self.db[var.trait] = trait
            else:
                self.db[var.trait].AddVariant(var)

        return False

    def GetTrait(self, trait):
        if (trait in self.db):
            return self.db[trait]
        else:
            print ("Trait '%s' does not exist" % (trait))
            return None
