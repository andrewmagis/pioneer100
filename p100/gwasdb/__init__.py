"""
    __init__.py "

    Author: Andrew Magis
    Date: July 29th, 2014

"""

from gwasvariant import GwasVariant
from p100.trait import Trait
from p100.errors import MyError

class GwasDB(object):
    def __init__(self, dbsnp, genome):

        self.db = {}
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
        var = GwasVariant(line)

        # Validate the variant using superclass
        (isvalid, reason) = var.IsValid(self.dbsnp, self.genome)
        print var.dbsnp, isvalid, reason

        # If returns invalid because missing from database, set the flag
        # to update the database and reload
        if (not isvalid) and (reason == 6):
            return True

        # If it is valid, add the variant
        if (isvalid):

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
            raise MyError("Trait '%s' does not exist" % (trait))

    def Stats(self):
        count = 0

        for key in self.db.keys():
            count += len(self.db[key].variants)
            # print key, len(self.db[key].variants)

        print "Lines: %d" % (self.attempted)
        print "Failed !Format: %d !Gene: %d !Strand: %d !Pos: %d !Neg: %d Dups: %d" % (
        self.failed, self.failed_nogene, self.failed_nostrand, self.failed_posstrand, self.failed_negstrand,
        self.failed_duplicate)
        print "Passed: Normal: %d Neg: %d" % (self.passed, self.passed_negstrand)
        print "%d variants in %d traits" % (count, len(self.db))

    def WriteFiltered(self):
        with open('./db/gwascatalog.filtered.txt', "w") as f:
            for trait in sorted(self.db.keys()):
                self.db[trait].WriteFiltered(f)


