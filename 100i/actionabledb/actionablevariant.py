from variant import Variant
from errors import MyError


class ActionableVariant(Variant):
    def __init__(self, line):
        # Initialize the parent class
        super(Variant, self).__init__()

        tokens = line.split('\t')
        self.dbsnp = tokens[0].strip()
        self.reported_genes = tokens[1].strip()
        self.chr = tokens[2].strip()
        self.start = int(tokens[3].strip())
        self.end = int(tokens[4].strip())
        self.type = tokens[5].strip()
        self.gmaf = tokens[6].strip()
        self.assembly = tokens[7].strip()
        self.pubmed = tokens[8].strip()
        self.risk_allele = tokens[9].strip()
        self.risk_model = tokens[10].strip()
        self.risk_type = tokens[11].strip()
        self.risk_codon = tokens[12].strip()
        self.risk_aa = tokens[13].strip()
        self.or_beta = tokens[14].strip()
        self.confidence95 = tokens[15].strip()
        self.pval = tokens[16].strip()
        self.in_gwas = tokens[17].strip()
        self.trait = tokens[18].strip()
        self.interaction = tokens[19].strip()
        self.intervention = tokens[20].strip()
        self.gender = tokens[21].strip()
        self.notes = tokens[22].strip().strip('"')

        self.unit = None
        self.range = None
        self.direction = None

        self.actual_unit = None
        self.display = None
        self.variant_notes = None
        self.range = None


        self.key = self.dbsnp + '_' + self.risk_allele

        # Does the risk allele match the reference?
        self.risk_allele_is_reference = None
