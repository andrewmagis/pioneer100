from variant import Variant

import re

class PharmacogenomicsVariant(Variant):

    def __init__(self, line):

        # Initialize the parent class
        super(Variant, self).__init__()

        tokens = line.split('\t')
        self.trait = tokens[0].strip().strip('"')
        self.dbsnp = tokens[1].strip().strip('"')
        self.risk_allele = tokens[2].strip().strip('"')
        self.or_beta = tokens[3].strip().strip('"')
        self.confidence95 = tokens[4].strip().strip('"')
        self.actual_unit = tokens[5].strip().strip('"')
        self.pval = tokens[6].strip().strip('"')
        self.display = tokens[7].strip().strip('"')
        self.risk_model = tokens[8].strip().strip('"')
        self.risk_type = tokens[9].strip().strip('"')
        self.notes = tokens[10].strip().strip('"')
        self.variant_notes = tokens[11].strip().strip('"')

        # Variables to be retrieved from database
        self.chr = None
        self.start = None
        self.end = None
        self.pubmed = None
        self.reported_genes = None

        self.key = self.dbsnp + '_' + self.risk_allele

        # Does the risk allele match the reference?
        self.risk_allele_is_reference = None

        # Risk models are all additive for GWAS variants
        self.assembly = "GRCh37"

