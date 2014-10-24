import math

class ParticipantTraitVariant():
    # This class will store gwas trait information as well as my genotype
    # and be capable of writing it out to a report

    def __init__(self, gwas_var, my_alleles, effect):

        # Get GWAS information that I may need to report
        self.trait = gwas_var.trait
        self.pubmed = gwas_var.pubmed
        self.dbsnp = gwas_var.dbsnp
        self.reported_genes = gwas_var.reported_genes
        self.risk_allele = gwas_var.risk_allele
        self.pval = gwas_var.pval
        self.or_beta = gwas_var.or_beta
        self.confidence95 = gwas_var.confidence95
        self.notes = gwas_var.notes
        self.variant_notes = gwas_var.variant_notes

        self.effect = effect
        self.risk_type = gwas_var.risk_type

        self.chr = gwas_var.chr
        self.start = gwas_var.start
        self.end = gwas_var.end

        self.unit = gwas_var.unit
        #self.range = gwas_var.range
        self.direction = gwas_var.direction

        # Get genotype information     
        self.genotype = '?/?'
        if (len(my_alleles) == 1):
            self.genotype = list(my_alleles)[0] + '/' + list(my_alleles)[0]
        else:
            self.genotype = '/'.join([x for x in sorted(my_alleles)])

    def Score(self, effect=None):

        # Get my effect if none specified
        if (effect is None):
            effect = self.effect;

        if (effect == 0):
            return 0.0
        elif (self.or_beta == 0):
            return 0.0
        else:

            # If this is an odds ratio, return the log
            if (self.unit == "OR"):

                # Let's just try combining them all
                #if (self.or_beta < 1):
                #    return -self.effect;
                #else:
                #    return self.effect;

                try:
                    #print "Returning", effect * math.log(self.or_beta)
                    return effect * math.log(self.or_beta)
                    #return effect

                except:
                    return 0.0


            # If this is a beta coefficient, just return it
            else:
                return effect * self.or_beta * self.direction
                #return self.direction * self.effect;

    def Print(self):
        print self.dbsnp, self.reported_genes, self.risk_allele, self.or_beta, self.genotype, self.effect

    def WriteAllelesForDNAlysis(self, fout):
        fout.write("%s\t%s\t%s\t%d\t%d\t%s\n"%(self.dbsnp, self.reported_genes, self.chr, self.start, self.end, self.genotype))

class ParticipantTrait(object):
    def __init__(self, trait):

        self.variants = {}

        self.trait = trait
        self.harmless_variants = {}
        self.bad_variants = {}
        self.unknown_variants = {}

        self.score = None
        self.unit = None
        self.actual_unit = None
        self.notes = None

    def GetScore(self):
        # Return string representation truncated to 2 sig digits
        #return '%s'%float('%.3g' % self.score);
        return self.score

    def GetZScore(self):
        #Return string representation of normalized score
        #return '%s'%float('%.3g' % ((self.score - self.min_score) / (self.max_score - self.min_score)))
        return (self.score - self.min_score) / (self.max_score - self.min_score)

    def Score(self):

        self.score = 0.0
        self.max_score = None
        self.min_score = None
        # Loop over each variant in this participant
        #print self.trait
        for key in self.variants.keys():

            self.score += self.variants[key].Score()

            # Calculate running min and max scores for this trait
            min_score = self.variants[key].Score(0)
            max_score = self.variants[key].Score(2)

            if (min_score > max_score):
                if (self.min_score is None):
                    self.min_score = max_score
                elif (self.min_score+max_score < self.min_score):
                    self.min_score += max_score;

                if (self.max_score is None):
                    self.max_score = min_score
                elif (self.max_score+min_score > self.max_score):
                    self.max_score += min_score;

            if (max_score > min_score):
                if (self.min_score is None):
                    self.min_score = min_score
                elif (self.min_score+min_score < self.min_score):
                    self.min_score += min_score;

                if (self.max_score is None):
                    self.max_score = max_score
                elif (self.max_score+max_score > self.max_score):
                    self.max_score += max_score;

            #self.variants[key].Print();
        #print self.score
        return self.score

    def AddVariant(self, gwas_var, my_alleles, effect):

        if (self.unit is None):
            self.unit = gwas_var.unit
        if (self.notes is None):
            self.notes = gwas_var.notes

        if (not gwas_var.key in self.variants):
            self.variants[gwas_var.key] = ParticipantTraitVariant(gwas_var, my_alleles, effect)
        else:
            print "Warning, Het %s already exists in participant trait %s" % (gwas_var.key, self.trait)

    def AddHarmlessVariant(self, gwas_var, my_alleles):

        if (not gwas_var.key in self.harmless_variants):
            self.harmless_variants[gwas_var.key] = ParticipantTraitVariant(gwas_var, my_alleles, None)
        else:
            print "Warning, Harmless %s already exists in participant trait %s" % (gwas_var.key, self.trait)

    def AddBadVariant(self, gwas_var, my_alleles):

        if (not gwas_var.key in self.bad_variants):
            self.bad_variants[gwas_var.key] = ParticipantTraitVariant(gwas_var, my_alleles, None)
        else:
            print "Warning, BAD VARIANT %s already exists in participant trait %s" % (gwas_var.key, self.trait)

    def AddUnknownVariant(self, gwas_var, my_alleles):

        if (not gwas_var.key in self.unknown_variants):
            self.unknown_variants[gwas_var.key] = ParticipantTraitVariant(gwas_var, my_alleles, None)
        else:
            print "Warning, UNKNOWN VARIANT %s already exists in participant trait %s" % (gwas_var.key, self.trait)

    def Stats(self):
        print "Trait: %s"%(self.trait)
        print "%d Variants" % (len(self.variants))
        print "%d BAD variants" % (len(self.bad_variants))
        print "%d UNKNOWN variants" % (len(self.unknown_variants))

    def Print(self):
        print "Variants"
        for key in self.variants:
            self.variants[key].Print()

    def WriteAllelesForDNAlysis(self, fout):
        for key in self.variants.keys():
            self.variants[key].WriteAllelesForDNAlysis(fout)
