"""
    __init__.py "

    Author: Andrew Magis
    Date: July 29th, 2014

"""

from pharmacogenomicsvariant import PharmacogenomicsVariant
from trait import Trait
from errors import MyError

class PharmacogenomicsDB(object):

    def __init__(self, dbsnp, genome):

        self.db = {}
        self.ids = []
        self.dbsnp = dbsnp
        self.genome = genome

        self.filename = './db/100i.Pharmacogenomics.Variants.txt'

    def Load(self):

        update = False
        with open(self.filename, 'Ur') as f:
            next(f)  # Skip the header line
            for line in f:
                self.AddVariant(line)

    def AddVariant(self, line):

        if (len(line.strip()) == 0):
            return False

        # Create the variant
        var = PharmacogenomicsVariant(line)

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
            return None;
            print("Trait '%s' does not exist" % (trait))

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


