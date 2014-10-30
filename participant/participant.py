import sys, gzip
import numpy as np
from scipy import stats

from participantvariant import ParticipantVariant
from participanttrait import ParticipantTrait
from errors import MyError
from vcf import VCF
from trait import Trait

class Participant(object):

    def __init__(self, username, gender, race, fitbit_key, fitbit_secret, genome_id, path, assembly, database, ranges, actionable_db, gwas_db, pharm_db, clinvar_db, dbsnp):

        # Save variables that we need
        self.username = username
        self.gender = gender
        self.race = race
        self.fitbit_key = fitbit_key
        self.fitbit_secret = fitbit_secret
        self.genome_id = genome_id
        self.path = path
        self.assembly = assembly
        self.ranges = ranges
        self.actionable_db = actionable_db
        self.clinvar_db = clinvar_db
        self.gwas_db = gwas_db
        self.pharm_db = pharm_db
        self.dbsnp = dbsnp
        self.database = database
        self.gwas_loaded = False
        self.actionable_loaded = False

        # To be populated
        self.variants = {}
        self.traits = {}

        # What changed in me
        self.changed = [];

        # Open my vcf file
        self.vcf = None
        if (not self.path is None):
            self.vcf = VCF(self.username, self.path, self.assembly, self.dbsnp)

        # Load data for me from database
        self.LoadData()
        self.LoadCompliance()

        # Base paths for Gestalt
        self.gestalt_path = '/local/gestalt/private/IndividualGenomeAssembly/'

    def LoadData(self):

        # Get my data from the database
        self.data = self.database.GetData(self.username)

    def LoadCompliance(self):

        # Get the compliance data
        self.compliance = self.database.GetCompliance(self.username)

    def MetaboliteTraitCorrelation(self, trait, measurement, pvalue):

        # Load the trait
        self.LoadTrait(trait, pvalue, True)

        if (not trait in self.traits):
            return None

        # Get the measurement
        (dates, values, range) = self.GetMeasurement(measurement)

        """
        # Check for CHOLESTEROL, DIABETES, or HYPERTENSION
        if ("CHOLESTEROL" in measurement):
            (med_dates, med_values, med_range) = self.GetMeasurement("MEDICATION_CHOLESTEROL")
            print med_dates, med_values
            if (med_values.size == 1) and (med_values == 1):
                return None
            if (med_values.size == 2) and (med_values[1]==1):
                return None

        # Check for CHOLESTEROL, DIABETES, or HYPERTENSION
        if ("GLUCOSE" in measurement):
            (med_dates, med_values, med_range) = self.GetMeasurement("MEDICATION_DIABETES")
            print med_dates, med_values
            if (med_values.size == 1) and (med_values == 1):
                return None
            if (med_values.size == 2) and (med_values[1]==1):
                return None
        """

        if (values.size == 0):
            return None

        elif (values.size == 1):

            if (np.isnan(values)):
                return None
            elif (dates == 1):
                return (self.username, values, np.nan, self.traits[trait].score)
            elif (dates == 2):
                return (self.username, np.nan, values, self.traits[trait].score)
            else:
                raise MyError('More than 2 values in measurement')

        elif (values.size == 2):

            if (np.isnan(values[0])) and (np.isnan(values[1])):
                return None
            elif (np.isnan(values[0])):
                return (self.username, np.nan, values[1], self.traits[trait].score)
            elif (np.isnan(values[1])):
                return (self.username, values[0], np.nan, self.traits[trait].score)
            else:
                return (self.username, values[0], values[1], self.traits[trait].score)

        else:
            raise MyError('More than 2 values in measurement')

    def LoadTrait(self, trait, pvalue, suppress_errors):

        # Create the trait and pull the required variants from the database
        trait_object = Trait(trait, pvalue)

        # Pull the required variant information from the database
        trait_object.Load(self.database)

        # Genotype the trait from this participant's VCF file
        if (trait_object.ProcessVCF(self.vcf, suppress_errors)):
            self.traits[trait] = trait_object

    def Correlations(self):

        data = {};

        for measurement in self.ranges.keys():

            values = self.data[measurement];
            if (values.size<2):
                continue;

            if (measurement == "LDL_PATTERN_QUEST"):
                temp = self.data[measurement];
                #print self.username, "LDL Pattern", self.data[measurement]
                if (temp[0]<50) and (temp[1]>=50):
                    print self.username, "A to B";
                    return 0
                elif (temp[0]>=50) and (temp[1]<50):
                    print self.username, "B to A"
                    return 1
                elif (temp[0]=='A') and (temp[1]=='A'):
                    print self.username, 'A', "No change"
                    return 2
                elif (temp[0]=='B') and (temp[1]=='B'):
                    print self.username, 'B', "No change"
                    return 3
                else:
                    return -1;


            if (np.isnan(values[0])):
                continue;
            if (np.isnan(values[1])):
                continue;
            if (values[0] == 0):
                continue;
            if (values[1] == 0):
                continue;

            if (measurement == "TOTAL_CHOLESTEROL"):
                data[measurement] = self.data[measurement];
                #print self.username, "TC", self.data[measurement]
            if (measurement == "LDL_CHOLESTEROL"):
                data[measurement] = self.data[measurement];
            if (measurement == "TRIGLYCERIDES"):
                data[measurement] = self.data[measurement];


            change = values[1]-values[0];
            var = stats.variation(values)

            # Get the stdev of this measurement
            stdev = self.ranges[measurement].stdev;
            #if (np.abs(change)>(stdev*2)):
            if (var > 0.2):
                self.ranges[measurement].changed += 1;
                self.changed.append((measurement, values[0], values[1], var));

            self.ranges[measurement].avg_change.append(change);
            self.ranges[measurement].sum_change += (change)

        # Print the changes for me
        #print self.username, self.changed
        #return data;

    def CheckLead(self):
        (dates, values, range) = self.GetMeasurement("LEAD");

        if (values.size == 1):
            if (values > range[1]):
                print self.username, dates, values, range[1]

        else:
            if (values[0] > range[1]) or (values[1] > range[1]):
                print self.username, dates, values, range[1]

    def GetMeasurement(self, measurement):

        if (not measurement in self.data):
            raise MyError('Unknown measurement'%(measurement))

        range = []
        dates = self.data['ROUND']
        values = self.data[measurement]

        if (self.gender == "M"):
            range.append(self.ranges[measurement].male_low)
            if (not self.ranges[measurement].male_med is None):
                range.append(self.ranges[measurement].male_med)
            range.append(self.ranges[measurement].male_high)

        if (self.gender == "F"):
            range.append(self.ranges[measurement].female_low)
            if (not self.ranges[measurement].female_med is None):
                range.append(self.ranges[measurement].female_med)
            range.append(self.ranges[measurement].female_high)

        return (dates, values, range)

    def AnalyzeACMG(self, fout, suppress_errors):
        self.clinvar_db.QueryACMGWithVCF(fout, self.vcf, suppress_errors)

    def AddACMGVariants(self, fout):

        if (self.assembly is None):
            return

        self.acmg = {};
        acmg_filename = self.gestalt_path + self.assembly + '/analyses/ACMGvariants.out.gz'

        try:
            with gzip.open(acmg_filename) as f:
                for line in f:
                    variant = ParticipantVariant(line)
                    if (not variant.dbsnp in self.acmg):

                        # If the quality is good enough
                        if (variant.quality == "PASS"):

                            # Now get this variant from clinvar
                            clinvar = self.clinvar_db.Get(variant.dbsnp)

                            if (clinvar is None):
                                raise MyError('Variant %s not found in clinvar database'%(variant.dbsnp));

                            # Check to see if the variant type is the same at least
                            if (variant.Compare(clinvar)):
                                self.acmg[variant.dbsnp] = (variant, clinvar)

                    else:
                        print "Warning, ACMG variant %s already exists in participant %s" % (variant.dbsnp, self.username)
        except:
            print "Error loading ACMG variants for participant %s"%(self.username)

        # Write them to the file
        for key in self.acmg.keys():
            (var, clinvar) = self.acmg[key]
            fout.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(self.username, var.chr, var.start,
                var.end, var.dbsnp, var.ref, var.alt, var.info, '/'.join(var.alleles), clinvar.geneinfo, clinvar.vc, '/'.join(clinvar.alt), ','.join(clinvar.clnsig), ','.join(clinvar.clndbn)))

    def AddActionableVariants(self):

        if (self.assembly is None):
            return

        #actionable_filename = self.gestalt_path + self.assembly + '/analyses/ActionableVariants.out.gz'
        actionable_filename = self.gestalt_path + self.assembly + '/analyses/DNAlysisVariants.out.gz'

        try:
            with gzip.open(actionable_filename) as f:
                for line in f:
                    self.AddVariant(line)
            self.Stats()
            self.actionable_loaded = True;
        except:
            print "Error loading actionable variants for participant %s"%(self.username)

    def AddGWASVariants(self):

        if (self.assembly is None):
            return

        gwas_filename = self.gestalt_path + self.assembly + '/analyses/GWASvariants.out.gz'

        try:
            with gzip.open(gwas_filename) as f:
                for line in f:
                    self.AddVariant(line)
            self.Stats()
            self.gwas_loaded = True;
        except:
            print "Error loading GWAS variants for participant %s"%(self.username)

    def AddVariant(self, line):
        variant = ParticipantVariant(line)

        if (variant.quality == "NOCALL"):
            #print "Warning, variant %s is NOCALL. Not adding"%(variant.dbsnp)
            return

        if (not variant.dbsnp in self.variants):
            self.variants[variant.dbsnp] = variant
        else:
            print "Warning, variant %s already exists in participant %s" % (variant.dbsnp, self.username)

    def AddMetabolites(self, metabolites, date, tokens):
        for metabolite, value in zip(metabolites, tokens):
            self.AddMetabolite(metabolite.strip('"').strip(), date, value.strip())

    def PrintMetabolites(self):
        print self.metabolites

    def AddMetabolite(self, metabolite, date, value):

        # Check to see if this date already exists
        if (not date in self.metabolites):

            # Add the new dictionary
            self.metabolites[date] = {}

            try:
                self.metabolites[date][metabolite] = float(value)
            except:
                self.metabolites[date][metabolite] = value

        # If the metabolite exists, check for the date
        else:

            if (not metabolite in self.metabolites[date]):
                try:
                    self.metabolites[date][metabolite] = float(value)
                except:
                    self.metabolites[date][metabolite] = value
            else:
                print "Warning: metabolite %s already exists for date %s in participant %s" % (
                metabolite, date, self.username)

    def ProcessAPOE(self):

        # Here is where we check for bad variants
        if (var.dbsnp == "rs429358"):
            self.rs429358 = var.alleles

        if (var.dbsnp == "rs7412"):
            self.rs7412 = var.alleles

    def TempAnalysis(self, measurement, trait):

        # Go through my traits
        if not trait in self.traits:
            return;

        (dates, values, range) = self.GetMeasurement(measurement);

        # Get the score for each participant
        #print self.username, metabolite, self.traits[metabolite].score,
        return (self.traits[trait].score, values, dates)

    def ProcessMetabolites(self):

        # Go through each metabolite in this individual
        for measurement in self.data.keys():

            transition = False
            prev = set()
            values = []

            dates = self.data['ROUND']
            values = self.data[measurement]

            print measurement, values;

            """

            # Go through each date
            for date in sorted(self.metabolites[metabolite].keys()):

                value = self.metabolites[metabolite][date]
                if (value != "NA") and (self.ranges[metabolite].is_range):
                    values.append(value)

                result = self.ranges[metabolite].OutOfRange(value, self.gender)
                if (not result is None):
                    prev.add(result)

                    #if (result < 0):
                    #    print self.username, metabolite, value, "LOW"
                    #elif (result > 0):
                    #    print self.username, metabolite, value, "HIGH"

            # At the end of each metabolite, if there has been a transition, then
            # there are multiple values in the prev set
            if (len(prev)>1):

                print self.username, "\t", metabolite,
                for date in sorted(self.metabolites[metabolite]):
                    print "\t", date, "\t", self.metabolites[metabolite][date],
                print

                #print "Transition: %s %s %s"%(self.username, metabolite, self.metabolites[metabolite])
            """

            """
            # Calculate variance
            if (len(values)>1):
                cv = stats.variation(values)
                if (cv > 0.2):
                    print self.username, "\t", metabolite,
                    for date in sorted(self.metabolites[metabolite]):
                        print "\t", date, "\t", self.metabolites[metabolite][date],
                    print "CV"
            """

    def ProcessDNAlysis(self, actionable_db):

        # Only process if I have variants
        if (len(self.variants)==0):
            return

        print "Processing %d DNAlysis variants for %s"%(len(self.variants), self.username)
        my_traits = [];
        for key in actionable_db.db.keys():
            atrait = self.ProcessActionable(key)
            my_traits.append(atrait);

        GSTT1 = None;
        GSTM1 = None;

        # Load the GSTM variants
        gstm = self.gestalt_path + self.assembly + '/analyses/GSTtm1.out'
        with open(gstm) as fin:
            for line in fin:
                tokens = line.split('\t');

                if (tokens[0] == "GSTT1"):
                    if (tokens[1] == "null"):
                        GSTT1 = 0;
                    elif (tokens[1] == "hemi"):
                        GSTT1 = 1;
                    elif (tokens[1] == "normal"):
                        GSTT1 = 2;
                    else:
                        print "WARNING: Unknown value %s"%tokens[1];
                elif (tokens[0] == "GSTM1"):
                    if (tokens[1] == "null"):
                        GSTM1 = 0;
                    elif (tokens[1] == "hemi"):
                        GSTM1 = 1;
                    elif (tokens[1] == "normal"):
                        GSTM1 = 2;
                    else:
                        print "WARNING: Unknown value %s"%tokens[1];
                else:
                    print "WARNING: Unknown gene %s"%(tokens[0])

        # Now open the output file and write them out
        with open("./results/" + self.username + ".DNAlysis.variants.txt", "w") as f:
            f.write("rsID\tsymbol\tchr\tstart\tend\t%s\n"%(self.username))
            for trait in my_traits:
                trait.WriteAllelesForDNAlysis(f);
            f.write("%s\t%s\t%s\t%d\t%d\t%d\n"%("N/A", "GSTM1", "1", 110230418, 110236367, GSTM1));
            f.write("%s\t%s\t%s\t%d\t%d\t%d\n"%("N/A", "GSTT1", "22", 24376139, 24384284, GSTT1));

    def ProcessGWASTrait(self, trait_name):

        if (not self.gwas_loaded):
            return

        # Get the trait
        trait = self.gwas_db.GetTrait(trait_name)

        if (trait_name in self.traits):
            print "Warning, trait %s already exists for participant" % (trait_name)

        print "Processing trait %s with %d variants" % (trait_name, len(trait.variants))

        # Create this trait for the participant
        ptrait = ParticipantTrait(trait_name)

        # Collect all the variants related to this trait and determine the
        # number of alleles present in this individual
        ptrait = self.ProcessTrait(trait, ptrait)

        # Score the trait
        ptrait.Score()

        # Add the trait to the db
        #print "Adding trait %s" % (trait_name)
        self.traits[trait_name] = ptrait

        # Return the participant trait, in case the calling function needs it
        return ptrait

    def ProcessActionable(self, trait_name):

        #if (not self.actionable_loaded):
        #    return

        # Get the trait
        trait = self.actionable_db.GetTrait(trait_name)

        if (trait is None):
            return None

        if (trait_name in self.traits):
            print "Warning, trait %s already exists for participant" % (trait_name)

        # Create this trait for the participant
        ptrait = ParticipantTrait(trait_name)

        # Collect all the variants related to this trait and determine the
        # number of alleles present in this individual
        ptrait = self.ProcessTrait(trait, ptrait)

        ptrait.Print()

        # Score the trait
        ptrait.Score()

        # Add the trait to the db
        self.traits[trait_name] = ptrait

        # Return the participant trait, in case the calling function needs it
        return ptrait

    def ProcessActionableAPOE(self, trait_name):

        #if (not self.actionable_loaded):
        #    return

        # Get the trait
        trait = self.actionable_db.GetTrait(trait_name)

        if (trait is None):
            return None

        if (trait_name in self.traits):
            print "Warning, trait %s already exists for participant" % (trait_name)

        # Create this trait for the participant
        ptrait = ParticipantTrait(trait_name)

        # Collect all the variants related to this trait and determine the
        # number of alleles present in this individual
        ptrait = self.ProcessTrait(trait, ptrait)

        ptrait.Print()

        # Score the trait
        ptrait.Score()
        print "About to calculate"

        # We can just do the calculation here for now. Later we will have
        # some analysis code to do this in a general way
        if (ptrait.variants['rs7412_C'].effect == 0):

            if (ptrait.variants['rs429358_C'].effect == 0):

                # rs7412(T) and rs429358(T) <- E2
                # rs7412(T) and rs429358(T) <- E2
                genotype = "ApoE2/ApoE2"
                ptrait.score = 0

            elif (ptrait.variants['rs429358_C'].effect == 1):

                # rs7412(T) and rs429358(C) <- unobserved haplotype
                # rs7412(T) and rs429358(T) <- E2
                raise MyError('This is a previously unobserved haplotype')

            elif (ptrait.variants['rs429358_C'].effect == 2):

                # rs7412(T) and rs429358(C) <- unobserved haplotype
                # rs7412(T) and rs429358(C) <- unobserved haplotype
                raise MyError('This is a previously unobserved haplotype')

            else:
                raise MyError("Unknown haplotype for APOE")

        elif (ptrait.variants['rs7412_C'].effect == 1):
            if (ptrait.variants['rs429358_C'].effect == 0):

                # rs7412(C) and rs429358(T) <- E3
                # rs7412(T) and rs429358(T) <- E2
                genotype = "ApoE2/ApoE3"
                ptrait.score = 1

            elif (ptrait.variants['rs429358_C'].effect == 1):

                # Remember that
                # rs7412(T) and rs429358(C) is not observed, so the
                # rs7412(T) and rs429358(C)
                # rs7412(C) and rs429358(T) arrangement is not possible

                # rs7412(C) and rs429358(C) <- E4
                # rs7412(T) and rs429358(T) <- E2
                genotype = "ApoE2/ApoE4"
                ptrait.score = 2

            elif (ptrait.variants['rs429358_C'].effect == 2):

                # rs7412(C) and rs429358(C) <- E4
                # rs7412(T) and rs429358(C) <- unobserved haplotype
                raise MyError('This is a previously unobserved haplotype')

            else:
                raise MyError("Unknown haplotype for APOE")

        elif (ptrait.variants['rs7412_C'].effect == 2):
            if (ptrait.variants['rs429358_C'].effect == 0):

                # rs7412(C) and rs429358(T) <- E3
                # rs7412(C) and rs429358(T) <- E3
                genotype = "ApoE3/ApoE3"
                ptrait.score = 3

            elif (ptrait.variants['rs429358_C'].effect == 1):

                # rs7412(C) and rs429358(C) <- E4
                # rs7412(C) and rs429358(T) <- E3
                genotype = "ApoE3/ApoE4"
                ptrait.score = 4

            elif (ptrait.variants['rs429358_C'].effect == 2):

                # rs7412(C) and rs429358(C) <- E4
                # rs7412(C) and rs429358(C) <- E4
                genotype = "ApoE4/ApoE4"
                ptrait.score = 5

            else:
                raise MyError("Unknown haplotype for APOE")

        print genotype
        # Add the trait to the db
        self.traits[trait_name] = ptrait

        # Return the participant trait, in case the calling function needs it
        return ptrait

    def GetGWASTraitScore(self, trait_name):

        if (not trait_name in self.traits):
            print "Warning, trait %s does not exist for participant" % (trait_name)
            return None

        return self.traits[trait_name].score
        #print "%s\t%s\t%.3f"%(self.username, trait_name, self.traits[trait_name].score)

    def WriteGWASTraitScores(self, fout):

        fout.write("%s" % self.username)
        for trait in sorted(self.traits.keys()):
            fout.write("\t%.2f" % (self.traits[trait].score))
        fout.write('\n')

    def ProcessGWAS(self):

        print "Processing %s" % (self.username)
        for trait in sorted(self.gwas_db.db.keys()):
            print "Processing trait", trait
            self.ProcessGWASTrait(trait)

    def ProcessPharmacogeneticsTrait(self, trait_name):

        if (not self.gwas_loaded):
            return

        # Get the trait
        trait = self.pharm_db.GetTrait(trait_name)

        if (trait is None):
            return

        if (trait_name in self.traits):
            print "Warning, trait %s already exists for participant" % (trait_name)

        #print "Processing trait %s with %d variants" % (trait_name, len(trait.variants))

        # Create this trait for the participant
        ptrait = ParticipantTrait(trait_name)

        # Copy over values that I want
        ptrait.display = trait.display;
        ptrait.actual_unit = trait.actual_unit

        # Collect all the variants related to this trait and determine the
        # number of alleles present in this individual
        ptrait = self.ProcessTrait(trait, ptrait)

        # Score the trait
        ptrait.Score()

        # Add the trait to the db
        #print "Adding trait %s" % (trait_name)
        self.traits[trait_name] = ptrait

        # Return the participant trait, in case the calling function needs it
        return ptrait

    def ProcessTrait(self, trait, atrait):

        # Go through each actionable variant
        for key in trait.variants.keys():

            # Get this variant
            actionable_var = trait.variants[key]

            # Check to make sure this variant has been assigned
            if (actionable_var.risk_allele_is_reference is None):
                print "Error: variant %s has not been properly vetted" % (trait_var.dbsnp)
                sys.exit(1)

            # If the risk allele is the reference
            if (actionable_var.risk_allele_is_reference):

                # If I have the variant, and the risk allele is the reference
                if (actionable_var.dbsnp in self.variants):

                    # Get my version of this variant
                    my_variant = self.variants[actionable_var.dbsnp]

                    # If the risk allele is in my variant alleles
                    if (actionable_var.risk_allele in my_variant.alleles):

                        # If I only have one allele, this is an unexplained issue
                        if (len(my_variant.alleles) == 1):
                            atrait.AddBadVariant(actionable_var, my_variant.alleles)

                        # If I have multiple alleles, only one of which is the reference
                        # then I am heterozygous for the reference risk allele
                        else:

                            if (actionable_var.risk_model == "recessive"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            elif (actionable_var.risk_model == "dominant"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 2)
                            elif (actionable_var.risk_model == "heterozygous"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 2)
                            elif (actionable_var.risk_model == "additive"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 1)
                            elif (actionable_var.risk_model == "switch"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            elif (actionable_var.risk_model == "haplotype"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            else:
                                print actionable_var.risk_model
                                raise MyError("Warning, unknown risk model: %s"%(actionable_var.risk_model))

                    # If the risk allele is not in my variant alleles
                    else:
                        atrait.AddVariant(actionable_var, my_variant.alleles, 0)

                # If I do not have the variant, then I am homozygous for the reference risk allele
                else:

                    if (actionable_var.risk_model == "recessive"):
                        atrait.AddVariant(actionable_var, set(actionable_var.ref), 2)
                    elif (actionable_var.risk_model == "dominant"):
                        atrait.AddVariant(actionable_var, set(actionable_var.ref), 2)
                    elif (actionable_var.risk_model == "heterozygous"):
                        atrait.AddVariant(actionable_var, set(actionable_var.ref), 0)
                    elif (actionable_var.risk_model == "additive"):
                        atrait.AddVariant(actionable_var, set(actionable_var.ref), 2)
                    elif (actionable_var.risk_model == "switch"):
                        atrait.AddVariant(actionable_var, set(actionable_var.ref), 0)
                    elif (actionable_var.risk_model == "haplotype"):
                        atrait.AddVariant(actionable_var, set(actionable_var.ref), 0)
                    else:
                        print actionable_var.risk_model
                        raise MyError("Warning, unknown risk model: %s"%(actionable_var.risk_model))

            # If the risk allele is not the reference
            else:

                # If I have the variant, then I may have the alt risk allele
                if (actionable_var.dbsnp in self.variants):

                    # Get my version of this variant
                    my_variant = self.variants[actionable_var.dbsnp]

                    if (actionable_var.risk_allele in my_variant.alleles):

                        # If I only have one allele, then I am homozygous for the alt risk allele
                        if (len(my_variant.alleles) == 1):

                            if (actionable_var.risk_model == "recessive"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 2)
                            elif (actionable_var.risk_model == "dominant"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 2)
                            elif (actionable_var.risk_model == "heterozygous"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            elif (actionable_var.risk_model == "additive"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 2)
                            elif (actionable_var.risk_model == "switch"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            elif (actionable_var.risk_model == "haplotype"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            else:
                                print actionable_var.risk_model
                                raise MyError("Warning, unknown risk model: %s"%(actionable_var.risk_model))

                        # If I have multiple alleles, then I am heterozygous for the alt risk allele
                        else:

                            if (actionable_var.risk_model == "recessive"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            elif (actionable_var.risk_model == "dominant"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 2)
                            elif (actionable_var.risk_model == "heterozygous"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 2)
                            elif (actionable_var.risk_model == "additive"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 1)
                            elif (actionable_var.risk_model == "switch"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            elif (actionable_var.risk_model == "haplotype"):
                                atrait.AddVariant(actionable_var, my_variant.alleles, 0)
                            else:
                                print actionable_var.risk_model
                                raise MyError("Warning, unknown risk model: %s"%(actionable_var.risk_model))

                    # If my ref allele matches the risk allele, this is bad
                    elif (my_variant.ref == actionable_var.risk_allele):

                        # This means the reference from dbSNP and the reference from the genome sequence do not
                        # agree. This can happen! See rs4430796
                        print "Error: %s alt allele matches reference my_ref: %s my_alt: %s risk: %s" % (
                        actionable_var.dbsnp, my_variant.ref, my_variant.alt, actionable_var.risk_allele)

                    # If my alt allele does not match. We assume no effect for this variant, though this might not be
                    # a good assumption
                    else:
                        atrait.AddUnknownVariant(actionable_var, my_variant.alleles)
                        atrait.AddVariant(actionable_var, my_variant.alleles, 0);

                else:
                    # If I do not have the variant, there is no effect
                    atrait.AddVariant(actionable_var, set(actionable_var.ref), 0)

        #atrait.Stats()
        return atrait

    def Stats(self):
        print "Loaded %d variants in participant %s" % (len(self.variants), self.username)

