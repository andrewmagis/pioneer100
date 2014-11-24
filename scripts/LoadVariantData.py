#!/usr/bin/env python

# System imports
import argparse, re

# Import the database class
from p100.database import Database
from p100.variant import Variant
from p100.genome import Genome
from p100.dbsnp import DBSnp
from p100.errors import MyError

def ArgParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', '-f', default=None)
    parser.add_argument('--actionable', '-a', action='store_true')
    parser.add_argument('--gwas', '-g', action='store_true')
    args = parser.parse_args()
    return args

def main(parser):

    # Open connection to MySQL database
    database = Database()

    # Create the table
    #Variant().CreateTable(database)

    # Load the DBSnp database
    dbsnp = DBSnp(database)

    # Create a genome object
    genome = Genome()
    genome.Load()

    if (parser.actionable):

        # Load the database that is provided
        with open(parser.filename, 'Ur') as f:
            for line in f:

                tokens = line.split('\t')
                if (tokens[0] == 'rsid'):
                    continue

                rsid = tokens[0].strip()
                trait = tokens[1].strip().strip('"').strip("'").replace('"', '').replace("'", '')
                chr = tokens[2].strip()
                start = tokens[3].strip()
                end = tokens[4].strip()
                reported_genes = ','.join([x.strip() for x in tokens[5].strip('"').split(',')])
                vc = tokens[6].strip()
                assembly = tokens[7].strip()
                pubmed = tokens[8].strip().strip('"')
                allele = tokens[9].strip()
                reference = None
                inheritance = tokens[11].strip()
                effect_type = tokens[12].strip()
                haplotype = tokens[13].strip()
                odds_beta = tokens[14].strip()
                unit = tokens[15].strip()
                pval = tokens[16].strip()
                interaction = tokens[17].strip()
                intervention = tokens[18].strip()
                gender = tokens[19].strip()
                ancestry = tokens[20].strip()
                note_generic = tokens[21].strip().strip('"')
                note_effect0 = tokens[22].strip().strip('"')
                note_effect1 = tokens[23].strip().strip('"')
                note_effect2 = tokens[24].strip().strip('"')

                # If there is no odds ratio or beta coefficient
                try:
                    odds_beta = float(odds_beta)
                except:
                    raise MyError("[%s] No odds ratio or beta coefficient"%(rsid))

                entry = None
                if (len(haplotype.strip())==0):
                    haplotype = None
                if (len(unit.strip())==0):
                    unit = None
                if (len(interaction.strip())==0):
                    interaction = None
                if (len(intervention.strip())==0):
                    intervention = None
                if (len(gender.strip())==0):
                    gender = None
                if (len(ancestry.strip())==0):
                    ancestry = None
                if (len(note_generic.strip())==0):
                    note_generic = None
                if (len(note_effect0.strip())==0):
                    note_effect0 = None
                if (len(note_effect1.strip())==0):
                    note_effect1 = None
                if (len(note_effect2.strip())==0):
                    note_effect2 = None
                if (len(chr.strip())==0):
                    chr = None
                if (len(start.strip())==0):
                    start = None
                if (len(end.strip())==0):
                    end = None

                variant = Variant(entry, rsid, trait, chr, start, end, reported_genes, vc, assembly, pubmed, allele, reference, inheritance,
                                  effect_type, haplotype, str(odds_beta), unit, pval, interaction, intervention, gender, ancestry, note_generic,
                                  note_effect0, note_effect1, note_effect2)

                (is_valid, message) = variant.Validate(dbsnp, genome)
                if (not is_valid):
                    print "[%s] %s"%(variant.rsid, message)
                else:
                    variant.InsertData(database)

    elif (parser.gwas):

        # Load the database that is provided
        with open(parser.filename, 'Ur') as f:
            for line in f:

                tokens = line.split('\t')
                line = line.strip()
                date_added = tokens[0].strip()
                pubmed = tokens[1].strip()
                author = tokens[2].strip()
                date_published = tokens[3].strip()
                journal = tokens[4].strip()
                link = tokens[5].strip()
                title = tokens[6].strip()
                trait = tokens[7].strip().strip('"').strip("'").replace('"', '').replace("'", '')
                initial_sample_size = tokens[8].strip()
                replication_sample_size = tokens[9].strip()
                region = tokens[10].strip()
                chr = tokens[11].strip()
                start = tokens[12].strip()
                end = start
                reported_genes = ','.join([x.strip() for x in tokens[13].strip('"').split(',')])
                mapped_genes = tokens[14].strip()
                upstream_geneid = tokens[15].strip()
                downstream_geneid = tokens[16].strip()
                snp_geneid = tokens[17].strip()
                upstream_gene_distance = tokens[18].strip()
                downstream_gene_distance = tokens[19].strip()

                tokens2 = tokens[20].strip().split('-')
                if (len(tokens2) == 2):
                    rsid = tokens2[0].strip()
                    risk_allele = tokens2[1].strip()
                else:
                    rsid = tokens2[0].strip()
                    risk_allele = '?'

                snps = tokens[21].strip()
                merged = tokens[22].strip()
                snp_id_current = tokens[23].strip()
                context = tokens[24].strip()
                intergenic = tokens[25].strip()
                risk_allele_frequency = tokens[26].strip()
                pval = tokens[27].strip()
                pval_mlog = tokens[28].strip()
                pval_txt = tokens[29].strip()
                odds_beta = tokens[30].strip()
                confidence95 = tokens[31].strip()
                platform = tokens[32].strip()
                cnv = tokens[33].strip()

                size = re.compile("[1-9](?:\d{0,2})(?:,\d{3})*(?:\.\d*[1-9])?|0?\.\d*[1-9]|0")

                # Get the size of the study
                total = 0
                temp = size.findall(initial_sample_size)
                for e in temp:
                    total += int(e.replace(',', ''))

                initial_size_total = total

                # Get the size of the study
                total = 0
                temp = size.findall(replication_sample_size)
                for e in temp:
                    total += int(e.replace(',', ''))

                replication_size_total = total
                count = 0

                unit = None
                actual_unit = None
                display = None
                variant_notes = None
                range = None

                # Get the ancestry information
                ancestry = set()

                # Get ancestry information
                if ("european" in initial_sample_size.lower()):
                    ancestry.add("european")
                if ("japanese" in initial_sample_size.lower()):
                    ancestry.add("japanese")
                if ("mexican" in initial_sample_size.lower()):
                    ancestry.add("mexican")
                if ("indian asian" in initial_sample_size.lower()):
                    ancestry.add("indian")
                if ("asian indian" in initial_sample_size.lower()):
                    ancestry.add("indian")
                if ("chinese" in initial_sample_size.lower()):
                    ancestry.add("chinese")
                if ("dutch" in initial_sample_size.lower()):
                    ancestry.add("dutch")
                if ("finnish" in initial_sample_size.lower()):
                    ancestry.add("finnish")
                if ("iceland" in initial_sample_size.lower()):
                    ancestry.add("icelandic")
                if ("korean" in initial_sample_size.lower()):
                    ancestry.add("korean")
                if ("german" in initial_sample_size.lower()):
                    ancestry.add("german")
                if ("romanian" in initial_sample_size.lower()):
                    ancestry.add("romanian")
                if ("caucasian" in initial_sample_size.lower()):
                    ancestry.add("caucasian")
                if ("african american" in initial_sample_size.lower()):
                    ancestry.add("african american")
                if ("french" in initial_sample_size.lower()):
                    ancestry.add("french")
                if ("filipino" in initial_sample_size.lower()):
                    ancestry.add("filipino")

                # Risk models are all additive for GWAS variants
                inheritance = "additive"
                notes = ""
                effect_type = "risk"
                assembly = "GRCh38"
                vc = "SNV"
                haplotype = None
                interaction = None
                intervention = None
                gender = None
                ancestry = None
                note_generic = None
                note_effect0 = None
                note_effect1 = None
                note_effect2 = None

                # If there is no odds ratio or beta coefficient
                try:
                    odds_beta = float(odds_beta)
                except:
                    raise MyError("[%s] No odds ratio or beta coefficient"%(rsid))

                # Before we insert, we must validate
                if (len(confidence95.strip()) == 0):
                    raise MyError("[%s] No confidence interval"%(rsid))

                tokens = confidence95.split(']')
                range = tokens[0] + ']'
                direction = "None"

                if (len(tokens) == 1):
                    raise MyError("[%s] Invalid confidence interval"%(rsid))
                elif (len(tokens) == 2):
                    temp = tokens[1].strip()
                    if (len(temp) == 0):
                        unit = None
                    else:
                        # Get the unit/direction
                        unit = tokens[1].strip();
                else:
                    raise MyError("[%s] Cannot parse confidence95 field: %s"%(rsid, confidence95))

                # Get the increase or decrease
                direction = None
                if (not unit is None):

                    if ("increase" in unit):
                        direction = 1
                        unit = unit.strip('increase').strip()
                    elif ("higher" in unit):
                        direction = 1
                        unit = unit.strip('higher').strip()
                    elif ("decrease" in unit):
                        direction = -1
                        unit = unit.strip('decrease').strip()
                    elif ("lower" in unit):
                        direction = -1
                        unit = unit.strip('lower').strip()

                # If this is a beta coefficient but there is no direction
                if (not unit is None) and (direction is None):
                    raise MyError("[%s] No direction for beta coefficient: %s"%(rsid, confidence95))
                elif (not unit is None):
                    odds_beta *= direction

                if (len(chr.strip())==0):
                    chr = None
                if (len(start.strip())==0):
                    start = None
                if (len(end.strip())==0):
                    end = None

                entry = None
                reference = None
                variant = Variant(entry, rsid, trait, chr, start, end, reported_genes, vc, assembly, pubmed, risk_allele, reference, inheritance,
                                  effect_type, haplotype, str(odds_beta), unit, pval, interaction, intervention, gender, ancestry, note_generic,
                                  note_effect0, note_effect1, note_effect2)

                (is_valid, message) = variant.Validate(dbsnp, genome)
                if (not is_valid):
                    print "[%s] %s"%(variant.rsid, message)
                else:
                    variant.InsertData(database)


if __name__ == "__main__":
    main(ArgParser())

