from p100.variant import Variant

import re

class GwasVariant(Variant):

    def __init__(self, line):

        # Initialize the parent class
        super(Variant, self).__init__()

        tokens = line.split('\t')
        self.line = line.strip()
        self.date_added = tokens[0].strip()
        self.pubmed = tokens[1].strip()
        self.author = tokens[2].strip()
        self.date_published = tokens[3].strip()
        self.journal = tokens[4].strip()
        self.link = tokens[5].strip()
        self.title = tokens[6].strip()
        self.trait = tokens[7].strip().strip('"')
        self.initial_sample_size = tokens[8].strip()
        self.replication_sample_size = tokens[9].strip()
        self.region = tokens[10].strip()
        self.chr = tokens[11].strip()
        self.start = tokens[12].strip()
        self.end = self.start
        self.reported_genes = tokens[13].strip()
        self.mapped_genes = tokens[14].strip()
        self.upstream_geneid = tokens[15].strip()
        self.downstream_geneid = tokens[16].strip()
        self.snp_geneid = tokens[17].strip()
        self.upstream_gene_distance = tokens[18].strip()
        self.downstream_gene_distance = tokens[19].strip()

        tokens2 = tokens[20].strip().split('-')
        if (len(tokens2) == 2):
            self.dbsnp = tokens2[0].strip()
            self.risk_allele = tokens2[1].strip()
        else:
            self.dbsnp = tokens2[0].strip()
            self.risk_allele = '?'

        self.snps = tokens[21].strip()
        self.merged = tokens[22].strip()
        self.snp_id_current = tokens[23].strip()
        self.context = tokens[24].strip()
        self.intergenic = tokens[25].strip()
        self.risk_allele_frequency = tokens[26].strip()
        self.pval = tokens[27].strip()
        self.pval_mlog = tokens[28].strip()
        self.pval_txt = tokens[29].strip()
        self.or_beta = tokens[30].strip()
        self.confidence95 = tokens[31].strip()
        self.platform = tokens[32].strip()
        self.cnv = tokens[33].strip()

        size = re.compile("[1-9](?:\d{0,2})(?:,\d{3})*(?:\.\d*[1-9])?|0?\.\d*[1-9]|0")

        # Get the size of the study
        total = 0
        temp = size.findall(self.initial_sample_size)
        for e in temp:
            total += int(e.replace(',', ''))

        self.initial_size_total = total

        # Get the size of the study
        total = 0
        temp = size.findall(self.replication_sample_size)
        for e in temp:
            total += int(e.replace(',', ''))

        self.replication_size_total = total
        self.count = 0

        self.unit = None
        self.actual_unit = None
        self.display = None
        self.variant_notes = None
        self.range = None

        # Get the ancestry information            
        self.ancestry = set()

        # Get ancestry information
        if ("european" in self.initial_sample_size.lower()):
            self.ancestry.add("european")
        if ("japanese" in self.initial_sample_size.lower()):
            self.ancestry.add("japanese")
        if ("mexican" in self.initial_sample_size.lower()):
            self.ancestry.add("mexican")
        if ("indian asian" in self.initial_sample_size.lower()):
            self.ancestry.add("indian")
        if ("asian indian" in self.initial_sample_size.lower()):
            self.ancestry.add("indian")
        if ("chinese" in self.initial_sample_size.lower()):
            self.ancestry.add("chinese")
        if ("dutch" in self.initial_sample_size.lower()):
            self.ancestry.add("dutch")
        if ("finnish" in self.initial_sample_size.lower()):
            self.ancestry.add("finnish")
        if ("iceland" in self.initial_sample_size.lower()):
            self.ancestry.add("icelandic")
        if ("korean" in self.initial_sample_size.lower()):
            self.ancestry.add("korean")
        if ("german" in self.initial_sample_size.lower()):
            self.ancestry.add("german")
        if ("romanian" in self.initial_sample_size.lower()):
            self.ancestry.add("romanian")
        if ("caucasian" in self.initial_sample_size.lower()):
            self.ancestry.add("caucasian")
        if ("african american" in self.initial_sample_size.lower()):
            self.ancestry.add("african american")
        if ("french" in self.initial_sample_size.lower()):
            self.ancestry.add("french")
        if ("filipino" in self.initial_sample_size.lower()):
            self.ancestry.add("filipino")

        self.key = self.dbsnp + '_' + self.risk_allele

        # Does the risk allele match the reference?
        self.risk_allele_is_reference = None

        # Risk models are all additive for GWAS variants
        self.risk_model = "additive"
        self.notes = ""
        self.risk_type = "risk"
        self.assembly = "GRCh38"

    def Write(self, f):
        f.write("%s\n" % (self.line))

    def Score(self, calc_unit=None):

        if (calc_unit is None):
            score = 0.0
            for value in self.or_beta:
                score += float(value)
            score /= len(self.or_beta)

            if (self.direction == "decrease"):
                score *= -1.0
            return score

        else:

            score = 0.0
            count = 0
            for value, unit in zip(self.or_beta, self.unit):
                if (unit == calc_unit):
                    score += float(value)
                    count += 1.0
                if (count > 0.0):
                    score /= count
            if (self.direction == "decrease"):
                score *= -1.0
            return score

    def Print(self):
        print "%s\t%s\t%s" % (self.trait, self.dbsnp, self.risk_allele)
