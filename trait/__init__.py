from errors import MyError
from variant import Variant

class Trait:

    def __init__(self, trait, pvalue):
        self.trait = trait
        self.variants = {}
        self.scores = []
        self.unit = None
        self.actual_unit = None
        self.display = None
        self.counts = []
        self.count = 0
        self.score = None
        self.pvalue = pvalue

    def Load(self, database):

        command = "SELECT * FROM variant WHERE trait='" + self.trait + "'"
        results = database.Command(command)

        for result in results:
            variant = Variant(*result)
            if (float(variant.pval) <= float(self.pvalue)):
                self.AddVariant(variant)

    def AddVariant(self, variant):

        if (not variant.rsid in self.variants):
            self.variants[variant.rsid] = variant
            return True
        else:
            print "Warning! Variant %s already exists in trait %s" % (variant.rsid, self.trait)
            return False

    def ProcessVCF(self, vcf, suppress_errors):

        # Error check
        if (vcf is None):
            return False

        self.score = 0.0

        # For each variant in this trait, query the VCF file
        for key in self.variants.keys():

            try:

                # Query the VCF file for this position, suppressing errors
                results = vcf.Query(key, suppress_errors)

                # If there is no variant at this position, this still means I am
                # homozygous reference, which is important to know!
                if (len(results)==0):
                    self.variants[key].Genotype(None)

                # If there is one result, I am either heterozygous alt or homozygous alt
                elif (len(results)==1):
                    self.variants[key].Genotype(results[0])

                else:
                    raise MyError('Found multiple variants at using rsid=%s in VCF file %s'%(key, vcf.filename))

                #self.variants[key].Print()

                # Accumulate the score for this trait
                self.score += self.variants[key].score

            except MyError as e:
                # Do not add the score in for any exception. Not perfect, but what else can we do.
                e.Print()

        return True

    def Print(self):
        for key in sorted(self.variants.keys()):
            self.variants[key].Print()

    def WriteFiltered(self, f):
        for key in sorted(self.variants.keys()):
            self.variants[key].Write(f)