"""
    __init__.py
    
    Superclass for variants

    Author: Andrew Magis
    Date: July 29th, 2014

"""
import math

# Exceptions
from errors import MyError

class Variant(object):

    def __init__(self, entry=None, rsid=None, trait=None, chr=None, start=None, end=None, gene=None, vc=None, assembly=None, pubmed=None, allele=None,
                 reference=None, inheritance=None, effect_type=None, haplotype=None, odds_beta=None, unit=None, pval=None,
                 interaction=None, intervention=None, gender=None, ancestry=None, note_generic=None, note_effect0=None, note_effect1=None, note_effect2=None):

        self.rsid = rsid
        self.chr = chr
        self.start = start
        self.end = end
        self.gene = gene
        self.vc = vc
        self.assembly = assembly
        self.pubmed = pubmed
        self.allele = allele
        self.reference = reference
        self.inheritance = inheritance
        self.effect_type = effect_type
        self.haplotype = haplotype
        self.odds_beta = odds_beta
        self.unit = unit
        self.pval = pval
        self.trait = trait
        self.interaction = interaction
        self.intervention = intervention
        self.gender = gender
        self.ancestry = ancestry
        self.note_generic = note_generic
        self.note_effect0 = note_effect0
        self.note_effect1 = note_effect1
        self.note_effect2 = note_effect2

        # Additional values that do not exist until a genotype is added
        self.vcf = None
        self.effect = None
        self.score = None
        self.genotype = None
        self.allele_is_reference = None

    def Genotype(self, vcfobject):

        # Store the vcf
        self.vcf = vcfobject

        # I am homozygous reference
        if (vcfobject is None):

            self.genotype = self.effect + '/' + self.effect

            # If this variant's effect allele is the reference, then I am homozygous for the effect allele
            if (self.allele_is_reference):

                # TODO: Update these categories
                if (self.inheritance == "recessive"):
                    self.effect = 2
                elif (self.inheritance == "dominant"):
                    self.effect = 2
                elif (self.inheritance == "heterozygous"):
                    self.effect = 0
                elif (self.inheritance == "additive"):
                    self.effect = 2

            # If this variant's effect allele is not the reference, then I am homozygous for the non-effect allele
            else:
                self.effect = 0

        # I am not homozygous reference
        else:

            if (len(self.vcf.alleles)==1):
                allele = list(self.vcf.alleles)[0]
                self.genotype = allele + '/' + allele
            else:
                self.genotype = '/'.join(self.vcf.alleles)

            # If this variant's effect allele is the reference
            if (self.allele_is_reference):

                # Check to see if my effect allele is in the list of alleles for this vcfobject
                if (self.allele in self.vcf.alleles):

                    # This is an error - should not be possible to be homozygous for an allele that is
                    # present in the VCF when the allele is also the reference
                    if (self.vcf.zygosity == "HOMOZYGOUS"):
                        raise MyError('Found VCF entry for homozygous genotype but allele should be reference [%s]'%(self.rsid))

                    elif (self.vcf.zygosity == "HETEROZYGOUS"):

                         # TODO: Update these categories
                        if (self.inheritance == "recessive"):
                            self.effect = 0
                        elif (self.inheritance == "dominant"):
                            self.effect = 2
                        elif (self.inheritance == "heterozygous"):
                            self.effect = 2
                        elif (self.inheritance == "additive"):
                            self.effect = 1

                    elif (self.vcf.zygosity == "HETEROZYGOUS_MULTIPLE"):

                        # Not sure if this will arise
                        print "Warning: found a HETEROZYGOUS_MULTIPLE allele for rsid %s"%(self.rsid)

                         # TODO: Update these categories
                        if (self.inheritance == "recessive"):
                            self.effect = 0
                        elif (self.inheritance == "dominant"):
                            self.effect = 2
                        elif (self.inheritance == "heterozygous"):
                            self.effect = 2
                        elif (self.inheritance == "additive"):
                            self.effect = 1

                    else:
                        raise MyError('Unknown zygosity: %s'%(self.vcf.zygosity))

                # None of my alleles are in the alleles for this variant, meaning I am homozygous for the non-effect allele
                else:
                    self.effect = 0

            # The effect allele is not the reference
            else:

                # Check to see if my effect allele is in the list of alleles for this vcfobject
                if (self.allele in self.vcf.alleles):

                    # I am homozygous for the effect allele
                    if (self.vcf.zygosity == "HOMOZYGOUS"):

                        # TODO: Update these categories
                        if (self.inheritance == "recessive"):
                            self.effect = 2
                        elif (self.inheritance == "dominant"):
                            self.effect = 2
                        elif (self.inheritance == "heterozygous"):
                            self.effect = 0
                        elif (self.inheritance == "additive"):
                            self.effect = 2

                    elif (self.vcf.zygosity == "HETEROZYGOUS"):

                         # TODO: Update these categories
                        if (self.inheritance == "recessive"):
                            self.effect = 0
                        elif (self.inheritance == "dominant"):
                            self.effect = 2
                        elif (self.inheritance == "heterozygous"):
                            self.effect = 2
                        elif (self.inheritance == "additive"):
                            self.effect = 1

                    elif (self.vcf.zygosity == "HETEROZYGOUS_MULTIPLE"):

                        # Not sure if this will arise
                        print "Warning: found a HETEROZYGOUS_MULTIPLE allele for rsid %s"%(self.rsid)

                         # TODO: Update these categories
                        if (self.inheritance == "recessive"):
                            self.effect = 0
                        elif (self.inheritance == "dominant"):
                            self.effect = 2
                        elif (self.inheritance == "heterozygous"):
                            self.effect = 2
                        elif (self.inheritance == "additive"):
                            self.effect = 1

                    else:
                        raise MyError('Unknown zygosity: %s'%(self.vcf.zygosity))

                # None of my alleles are in the alleles for this variant
                else:
                    raise MyError('Warning, unknown alleles for rsid %s'%(self.rsid))

        # If this is an odds ratio, return the log
        if (self.unit is None):

            # We take the log of the odds ratio so they can be summed
            try:
                #self.score = self.effect * math.log(float(self.odds_beta)) * -math.log(float(self.pval))
                self.score = self.effect * math.log(float(self.odds_beta))
            except:
                self.score = 0.0

        # If this is a beta coefficient
        else:
            #self.score = self.effect * float(self.odds_beta) * -math.log(float(self.pval))
            self.score = self.effect * float(self.odds_beta)

    def Validate(self, dbsnp, genome):

        # If this rsID is invalid
        if (not 'rs' in self.rsid):
            return (False, "Invalid rsID")

        # If pvalue does not meet criteria
        try:
            self.pval = float(self.pval)
        except:
            return (False, "Invalid Pvalue")

        if (self.pval > 1e-6):
            return (False, "Pvalue is not significant")

        # Get the dbsnp variant from the database
        #TODO: Install dbSNP GRCh38 and update
        dbsnp_var = dbsnp.Get(self.rsid, "GRCh37")
        if (dbsnp_var is None):
            return (False, "Variant not found in dbSNP")

        # If there is no risk allele
        if (self.allele == '?') or (len(self.allele.strip())==0):

            minor_allele = dbsnp_var.GetMinorAllele()

            # Get risk allele as minor allele from dbSNP
            if (not minor_allele is None):
                self.allele = minor_allele
                print "[%s] Risk allele not present. Used dbSNP minor allele = %s"%(self.rsid, minor_allele)
            else:
                return (False, "Unable to set effect allele from dbSNP")

        # If the risk allele is set, compare it to the minor allele
        else:

            minor_allele = dbsnp_var.GetMinorAllele()

            if (not self.allele == minor_allele):
                print "[%s] Risk allele = %s does not match minor allele in dbSNP = %s"%(self.rsid, self.allele, minor_allele)

        # If there is no odds ratio or beta coefficient
        try:
            self.odds_beta = float(self.odds_beta)
        except:
            return (False, "No odds ratio or beta coefficient")

        # If there is no start or end
        try:
            self.start = int(self.start)
            self.end = int(self.end)
        except:

            # Get the information from dbSNP and set GRCh37 as assembly
            self.start = int(dbsnp_var.pos)
            self.end = int(dbsnp_var.pos)
            self.assembly = "GRCh37";
            print "[%s] Position not present. Used dbSNP pos = %s"%(self.rsid, self.start)

        # If chr == 23, this is X chromosome. Sigh.
        if (self.chr == '23'):
            self.chr = 'X'

        # If there is no chr
        if (self.chr is None):
            self.chr = dbsnp_var.chr;
            print "[%s] Chr not present. Used dbSNP chr = %s"%(self.rsid, self.chr)

        # Set the assembly in the genome and get the base at this position
        genome.SetAssembly(self.assembly)
        self.reference = genome.Sequence(self.chr, self.start, self.end, '+')

        # If I cannot get the sequence due to some error
        if (len(self.reference)==0):
            return (False, "Invalid sequence for variant")

        # If there is no gene
        if (self.gene is None):
            genes = genome.Gene(self.chr, self.start, self.end);
            if (len(genes)==0):
                self.gene = "intergenic"
            else:
                temp = set();
                for gene in genes:
                    temp.add(gene.attributes.get('gene_name', 'unknown'));
                self.gene = ','.join(temp)

        # If the risk allele matches what is in dbsnp
        if (self.allele == self.reference):
            self.allele_is_reference = True
            return (True, 0)

        # If the alternative allele matches what is in dbsnp
        elif (self.allele in dbsnp_var.alt):
            self.allele_is_reference = False
            return (True, 0)

        # The risk allele does not match either the reference or the alternate allele
        else:

            # Get the strand at this position
            strand = genome.Strand(self.chr, self.start)

            # If strand is unknown, any inconsistency between the risk allele
            # and the dbsnp alleles cannot be resolved. Return 1
            if (strand == '.'):
                return (False, "Unknown strand, cannot resolve inconsistent alleles")

            # If the strand is known
            else:

                # If the gene strandedness is positive, this is still an inconsistency
                if (strand == '+'):
                    # Return 3 if alleles are inconsistent and we have a gene on the + strand
                    return (False, "Inconsistent alleles but gene on + strand")

                else:

                    # Here we check to make sure the reason there is an inconsistency 
                    # is that the risk allele is relative to negative strand and the 
                    # gene is on the positive strand

                    # CHANGE the risk allele to be the reverse complement of what it is
                    if (self.allele == 'T'):
                        self.allele = 'A'
                    elif (self.allele == 'A'):
                        self.allele = 'T'
                    elif (self.allele == 'C'):
                        self.allele = 'G'
                    elif (self.allele == 'G'):
                        self.allele = 'C'
                    else:
                        raise MyError("Unknown risk allele: %s" % (self.risk_allele))

                    # If the risk allele matches what is in dbsnp
                    if (self.allele == self.reference):
                        self.allele_is_reference = True
                        self.validated = True
                        return (True, 4)

                    elif (self.allele in dbsnp_var.alt):
                        self.allele_is_reference = False
                        self.validated = True
                        return (True, 4)

                    else:
                        # Not sure this can ever happen, but just in case...
                        raise MyError("Error, should not ever get here!")

        raise MyError("Error processing variant: %s" % (self.dbsnp))

    def Print(self):
        print "%s\t%s\t%s\t%s\t%s\t%s"%(self.rsid, self.trait, self.allele, self.reference, self.effect, str(self.score))
        if (not self.vcf is None):
            self.vcf.Print()

    def VariantExistsForTrait(self, database):

        # Get a result from the database
        cursor = database.GetCursor();
        cursor.execute("SELECT * FROM variant WHERE rsid = (%s) AND trait = (%s)", (self.rsid,self.trait))

        for result in cursor:
            return True
        return False

    def InsertData(self, database):

        # Make sure this variant is validated before we do anything with the database
        if (self.allele_is_reference is None):
            raise MyError("[%s] Variant has not been validated"%(self.rsid))

        if (self.VariantExistsForTrait(database)):
            print "Variant %s already exists for trait %s"%(self.rsid, self.trait)
            return

        command = "INSERT INTO variant (rsid, trait, chr, start, end, gene, vc, assembly, pubmed, allele, reference, inheritance, effect_type, haplotype, " \
                  "odds_beta, unit, pval, interaction, intervention, gender, ancestry, note_generic, note_effect0, note_effect1, note_effect2) VALUES " \
                  "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

        data = (self.rsid, self.trait, self.chr, self.start, self.end, self.gene, self.vc, self.assembly, self.pubmed, self.allele, self.reference, self.inheritance, self.effect_type,
                self.haplotype, self.odds_beta, self.unit, self.pval, self.interaction, self.intervention, self.gender, self.ancestry,
                self.note_generic, self.note_effect0, self.note_effect1, self.note_effect2)

        cursor = database.GetCursor()
        cursor.execute(command, data)
        database.Commit()

    def CreateTable(self, database):

        command = ""
        command += "CREATE TABLE variant (entry INT PRIMARY KEY AUTO_INCREMENT, rsid VARCHAR(16) NOT NULL, trait VARCHAR(512) NOT NULL, chr VARCHAR(16) NOT NULL, start INT NOT NULL, \
                    end INT NOT NULL, gene VARCHAR(512), vc VARCHAR(16) NOT NULL, assembly VARCHAR(16) NOT NULL, pubmed VARCHAR(512) NOT NULL, allele VARCHAR(512) NOT NULL, \
                    reference VARCHAR(512) NOT NULL, inheritance VARCHAR(16), effect_type VARCHAR(16) NOT NULL, haplotype INT, odds_beta FLOAT NOT NULL, unit VARCHAR(16), \
                    pval DOUBLE NOT NULL,  interaction VARCHAR(512), intervention VARCHAR(512), gender VARCHAR(16), ancestry VARCHAR(128), \
                    note_generic TEXT, note_effect0 TEXT, note_effect1 TEXT, note_effect2 TEXT)"

        # First create columns
        database.Command(command)
        database.Commit()