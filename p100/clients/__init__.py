import sys, gzip
import numpy as np
from scipy import stats

from p100.errors import MyError
from p100.vcf import VCF
from p100.trait import Trait
from p100.dbsnp import DBSnp

class Client(object):

    def __init__(self, username, database):

        self.username = username
        self.database = database
        self.traits = {}

        cursor = self.database.GetCursor()
        command = "SELECT path, assembly FROM prt_participant WHERE username='" + self.username + "'"
        cursor.execute(command)
        results = list(cursor.fetchall())
        if (len(results) == 0):
            self.path = None
            self.assembly = None
        elif (len(results) > 1):
            raise MyError('Returned multiple results for participant %s'%(username))
        else:
            (self.path,self.assembly) = results[0]

        """
        for result in results:
            variant = Variant(*result)
            if (float(variant.pval) <= float(self.pvalue)):
                self.AddVariant(variant)
        """

        # Open my vcf file
        self.vcf = None
        if (not self.path is None):
            self.vcf = VCF(self.username, self.path, self.assembly, DBSnp(database))


    def LoadTrait(self, trait, pvalue, suppress_errors):

        # Create the trait and pull the required variants from the database
        trait_object = Trait(trait, pvalue)

        # Pull the required variant information from the database
        trait_object.Load(self.database)

        # Genotype the trait from this participant's VCF file
        if (trait_object.ProcessVCF(self.vcf, suppress_errors)):
            self.traits[trait] = trait_object
            return trait_object
        return None