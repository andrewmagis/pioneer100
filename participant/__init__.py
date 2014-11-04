from range import Range
from errors import MyError
from participant import Participant
import numpy as np
from scipy import stats
import math

# Reports that I can generate
from pdf.pharmacogeneticsreport import PharmacogeneticsReport
from pdf.diseasereport import DiseaseReport
from pdf import TransitionsReport

class ParticipantDB(object):

    def __init__(self, database, actionable_db, gwas_db, pharm_db, clinvar_db, dbsnp):

        self.database = database
        self.participants = {}
        self.actionable_db = actionable_db
        self.gwas_db = gwas_db
        self.pharm_db = pharm_db
        self.clinvar_db = clinvar_db
        self.dbsnp = dbsnp
        self.measurements = set()

        # Load the ranges
        self.LoadMeasurements()
        self.ranges = database.LoadRanges()
        self.LoadParticipants()

    def AddParticipant(self, username, gender, race, fitbit_key, fitbit_secret, genome_id, path, assembly):

            # Check to see if participant already exists
        if (not username in self.participants):
            self.participants[username] = Participant(username, gender, race, fitbit_key, fitbit_secret, genome_id, path, assembly, self.database, self.ranges, self.actionable_db, self.gwas_db, self.pharm_db, self.clinvar_db, self.dbsnp)
        else:
            raise MyError("Warning: participant %s already exists!" % (username))

    def MeasurementStats(self, measurement):

        round1 = []
        round2 = []

        for prt in sorted(self.participants.keys()):

            (dates, values, range) = self.participants[prt].GetMeasurement(measurement);

            if (values.size == 1):
                if (not np.isnan(values)):
                    if (int(dates)==1):
                        round1.append(int(values));
                    else:
                        round2.append(int(values));
            else:
                if (not np.isnan(values[0])):
                    round1.append(values[0]);
                if (not np.isnan(values[1])):
                    round2.append(values[1]);

        # Now convert to numpy array
        round1 = np.array(round1)
        round2 = np.array(round2)

        # Assign the mean and std dev to range
        self.ranges[measurement].mean = np.nanmean(round1)
        self.ranges[measurement].sd = np.nanstd(round1)
        #print measurement, self.ranges[measurement].mean, self.ranges[measurement].sd

    def LoadParticipants(self):

        # Get participants from the database
        cursor = self.database.GetAll('participants')

        for (username, gender, race, fitbit_key, fitbit_secret, genome_id, path, assembly) in cursor:
            self.AddParticipant(username, gender, race, fitbit_key, fitbit_secret, genome_id, path, assembly)
        print "Loaded %d participants" % (len(self.participants))

        # Now calculate the mean and sd for each measurement
        for measurement in sorted(self.ranges.keys()):
            self.MeasurementStats(measurement)

    def LoadMeasurements(self):

        # Retrieve all measurements from the database
        results = self.database.Command("SELECT measurement from ranges")
        for measurement in results:
            self.measurements.add(measurement)
        print "Loaded %d measurements" % (len(self.measurements))

    def LoadTrait(self, trait, suppress_errors=True):
        for key in self.participants.keys():
            self.participants[key].LoadTrait(trait, suppress_errors)

    def MetaboliteTraitCorrelation(self, trait, measurement, pvalue, suppress_errors=True):

        usernames = []
        round1 = []
        round2 = []
        scores = []

        data = []

        for key in sorted(self.participants.keys()):

            result = self.participants[key].MetaboliteTraitCorrelation(trait, measurement, pvalue)

            if (not result is None):
                data.append(result)

            print "Processed %s"%(key)

        # Build numpy structured array of scores
        x = np.array(data, dtype=[('Username', np.str, 10), ('Round1', float), ('Round2', float), ('Score', float)])

        # Start by calculating the correlation
        (R, P) = stats.pearsonr(x['Round1'], x['Score'])
        print R, P

        # Sort by the score column
        x = np.sort(x, axis=-1, kind='quicksort', order=['Score'])

        # Generate histogram of the score column
        (probability, bins) = np.histogram(x['Score'], bins=3)

        print probability
        print bins

        print
        print "Round1"

        # Now calculate the average
        start = bins[0]
        count = 1
        for end in bins[1:]:

            count += 1

            # Get the subset of indices for these values
            if (count == len(bins)):
                indices = (x['Score'] >= start) & (x['Score'] <= end)
            else:
                indices = (x['Score'] >= start) & (x['Score'] < end)

            # Get the values of round1 for these indices
            subset = x['Round1'][indices]
            subind = x['Score'][indices]

            # Calculate the mean and stdev of these values
            mean = np.nanmean(subset)
            sd = np.nanstd(subset)
            stderr = sd / math.sqrt(len(subset))

            print mean, stderr

            start = end

        print
        print "Round2";

        # Now calculate the average
        start = bins[0]
        count = 1
        for end in bins[1:]:

            count += 1

            # Get the subset of indices for these values
            if (count == len(bins)):
                indices = (x['Score'] >= start) & (x['Score'] <= end)
            else:
                indices = (x['Score'] >= start) & (x['Score'] < end)

            # Get the values of round1 for these indices
            subset = x['Round2'][indices]
            subind = x['Score'][indices]


            # Calculate the mean and stdev of these values
            mean = np.nanmean(subset)
            sd = np.nanstd(subset)
            stderr = sd / math.sqrt(len(subset))

            print end, mean, sd

            print mean, stderr

        print x['Username']
        print x['Round1']
        print x['Round2']
        print x['Score']

        # Return the array
        return x

    def AddActionableVariants(self):
        for key in sorted(self.participants.keys()):
            self.participants[key].AddActionableVariants()

    def ProcessActionable(self, trait):
        for key in sorted(self.participants.keys()):
            self.participants[key].ProcessActionable(trait)

    def ProcessDNAlysis(self):
        for key in sorted(self.participants.keys()):
            self.participants[key].ProcessDNAlysis(self.actionable_db)

    def AnalyzeACMG(self):

        # Strictness settings
        no_conflict = False
        min_submitters = 1
        suppress_errors = True

        # Openhe output file
        fout = open('results/ACMG.filtered.' + str(no_conflict) + '.' + str(min_submitters) + '.txt', 'w')

        # Load the ACMG variants
        self.clinvar_db.LoadACMGVariants(no_conflict, min_submitters)

        for key in sorted(self.participants.keys()):
            print "Analyzing %s"%(key)
            self.participants[key].AnalyzeACMG(fout, suppress_errors);

        fout.close()

    def AnalyzeClinVar(self):

        # Strictness settings
        no_conflict = True
        min_submitters = 1
        suppress_errors = True

        # Openhe output file
        fout = open('results/ClinVar.filtered.' + str(no_conflict) + '.' + str(min_submitters) + '.txt', 'w')

        # Load the ACMG variants
        self.clinvar_db.LoadClinvarVariants(no_conflict, min_submitters)

        for key in sorted(self.participants.keys()):
            print "Analyzing %s"%(key)
            self.participants[key].AnalyzeACMG(fout, suppress_errors);

        fout.close()

    def ProcessDNAlysisIllumina(self):

        # Load GSTM/GSTT first
        data = {}
        filename = '/local/gestalt/tmp/GSTM1-GSTT1.Illumina.66-samples';
        with open(filename) as f:
            next(f)  # Skip the header line
            for line in f:

                tokens = line.strip().split('\t')

                username = None
                for key in self.participants.keys():
                    if (tokens[0] == self.participants[key].assembly):
                        username = self.participants[key].id

                if (username is None):
                    print username
                    raise MyError("Could not find username");

                # Now add to dictionary
                data[username] = (tokens[1], tokens[2])

        filename = '/local/gestalt/tmp/jointVCF.DNAlysis';

        header = None
        usernames = []

        fout = open('./results/DNAlysis.Illumina.txt', "w")

        # Open the DNAlysis file
        with open(filename) as f:
            for line in f:

                if (header is None):
                    header = line.strip().split('\t');

                    # Match the usernames up with the sample names
                    for sample in header:
                        found = False
                        for key in self.participants.keys():
                            if (sample == self.participants[key].assembly):
                                usernames.append(key)
                                found = True
                        if not found:
                            usernames.append(sample)

                    fout.write("%s\t%s\t%s\t%s\n"%('rsid', 'chr', 'pos', '\t'.join(usernames[4:])))

                else:

                    tokens = line.strip().split('\t');

                    chr = tokens[0].strip();
                    pos = int(tokens[1].strip());
                    ref = tokens[2].strip();
                    alt = tokens[3].strip();

                    print chr, pos, ref, alt

                    dbsnp = None
                    for key in self.actionable_db.variants.keys():
                        current = self.actionable_db.variants[key];
                        if (current.chr == chr) and (current.start == pos):
                            dbsnp = current.dbsnp;

                    if (dbsnp is None):
                        raise MyError("ERROR: Could not find variant")

                    # Write out the initial stuff
                    fout.write("%s\t%s\t%s"%(dbsnp, chr, str(pos)));

                    # Now we have the rsid.
                    for token in tokens[4:]:

                        genotype = []
                        temp = token.split('/')
                        for f in temp:
                            if (f == "0"):
                                genotype.append(ref);
                            elif (f == '1'):
                                genotype.append(alt)
                            elif (f == '.'):
                                genotype.append('?')
                            else:
                                raise MyError("ERROR: Unknown allele")

                        fout.write("\t%s"%('/'.join(genotype)))

                    fout.write("\n");

            # Now add in the final two lines
            fout.write("%s\t%s\t%s"%("GSTM1", "1", "110230418"))
            for user in usernames[4:]:
                (gstm, gstt) = data[user]
                fout.write("\t%s"%(gstm))
            fout.write('\n')

            # Now add in the final two lines
            fout.write("%s\t%s\t%s"%("GSTT1", "22", "24376139"))
            for user in usernames[4:]:
                (gstm, gstt) = data[user]
                fout.write("\t%s"%(gstt))
            fout.write('\n')

        fout.close()


    def AddGWASVariants(self):
        print "Adding GWAS"
        for key in sorted(self.participants.keys()):
            self.participants[key].AddGWASVariants()

    def AddACMGVariants(self):

        with open('./results/ACMG.variants.txt', 'w') as f:
            for key in sorted(self.participants.keys()):
                self.participants[key].AddACMGVariants(f)

    def ProcessMetabolites(self):
        for key in sorted(self.participants.keys()):
            self.participants[key].ProcessMetabolites()


    """
    def TempAnalysis(self, metabolite, trait):

        round1 = [];
        round2 = [];
        scores1 = [];
        scores2 = [];
        vitD_amounts = []
        vitD_compliants = []

        for key in sorted(self.participants.keys()):

            result = self.participants[key].TempAnalysis(metabolite, trait)

            if (result is None):
                continue;

            (score, values, dates) = result

            # Filter the data
            #if (values.size<2):
            #    continue;
            #if (np.isnan(values[0])):
            #    continue;
            #if (np.isnan(values[1])):
            #    continue;

            if (values.size == 1):

                if (not np.isnan(values)):

                    if (int(dates)==1):
                        scores1.append(score);
                        round1.append(int(values));
                    else:
                        scores2.append(score);
                        round2.append(int(values));

            else:

                if (not np.isnan(values[0])):
                    scores1.append(score);
                    round1.append(values[0]);
                if (not np.isnan(values[1])):
                    round2.append(values[1]);
                    scores2.append(score);

        print round1
        print scores1

        print round2
        print scores2

        round1 = np.array(round1);
        scores1 = np.array(scores1);
        round2 = np.array(round2);
        scores2 = np.array(scores2);

        (rvalue1, pvalue_corr1) = stats.pearsonr(round1, scores1)
        (rvalue2, pvalue_corr2) = stats.pearsonr(round2, scores2)

        print metabolite, "Round1", rvalue1, pvalue_corr1;
        print metabolite, "Round2", rvalue2, pvalue_corr2;
    """

    def TempAnalysis(self, metabolite, trait):

        round1_low = []
        round1_med = []
        round1_high = []

        round2_low = []
        round2_med = []
        round2_high = []

        scores1_low = []
        scores1_med = []
        scores1_high = []

        scores2_low = []
        scores2_med = []
        scores2_high = []

        for key in sorted(self.participants.keys()):

            """
            (dates, values, range) = self.participants[key].GetMeasurement('AGE')
            if (values.size == 1):
                age = values
            else:
                age = values[0]

            if (age < 40) or (age > 65):
                continue
            """

            result = self.participants[key].TempAnalysis(metabolite, trait)

            if (result is None):
                continue;

            (score, values, dates) = result

            if (values.size == 1):

                if (not np.isnan(values)):

                    if (int(dates)==1):

                        if (score == 0):
                            scores1_low.append(score);
                            round1_low.append(float(values));
                        elif (score == 1):
                            scores1_med.append(score);
                            round1_med.append(float(values));
                        elif (score == 2):
                            scores1_high.append(score);
                            round1_high.append(float(values));
                        else:
                            print "Failed"

                    else:

                        if (score == 0):
                            scores2_low.append(score);
                            round2_low.append(float(values));
                        elif (score == 1):
                            scores2_med.append(score);
                            round2_med.append(float(values));
                        elif (score == 2):
                            scores2_high.append(score);
                            round2_high.append(float(values));
                        else:
                            print "Failed"

            else:

                if (not np.isnan(values[0])):

                    if (score == 0):
                        scores1_low.append(score);
                        round1_low.append(float(values[0]));
                    elif (score == 1):
                        scores1_med.append(score);
                        round1_med.append(float(values[0]));
                    elif (score == 2):
                        scores1_high.append(score);
                        round1_high.append(float(values[0]));
                    else:
                        print "Failed"

                if (not np.isnan(values[1])):

                    if (score == 0):
                        scores2_low.append(score);
                        round2_low.append(float(values[1]));
                    elif (score == 1):
                        scores2_med.append(score);
                        round2_med.append(float(values[1]));
                    elif (score == 2):
                        scores2_high.append(score);
                        round2_high.append(float(values[1]));
                    else:
                        print "Failed"

        round1_low = np.array(round1_low)
        round1_med = np.array(round1_med)
        round1_high = np.array(round1_high)

        round2_low = np.array(round2_low)
        round2_med = np.array(round2_med)
        round2_high = np.array(round2_high)

        (score_comp12, pvalue1_comp12) = stats.ranksums(round1_low, round1_med)
        (score_comp13, pvalue1_comp13) = stats.ranksums(round1_low, round1_high)
        (score_comp23, pvalue1_comp23) = stats.ranksums(round1_med, round1_high)

        (score_comp12, pvalue2_comp12) = stats.ranksums(round2_low, round2_med)
        (score_comp13, pvalue2_comp13) = stats.ranksums(round2_low, round2_high)
        (score_comp23, pvalue2_comp23) = stats.ranksums(round2_med, round2_high)

        print "Round", "Mean_No_effect_(%s,%s)"%(round1_low.size,round2_low.size), "Mean_Het_effect_(%s,%s)"%(round1_med.size,round2_med.size), "Mean_Hom_effect_(%s,%s)"%(round1_high.size,round2_high.size), "Std_No_effect", "Std_Het_effect", "Std_Hom_effect"
        print "Round1", np.nanmean(round1_low), np.nanmean(round1_med), np.nanmean(round1_high), np.nanstd(round1_low), np.nanstd(round1_med), np.nanstd(round1_high), pvalue1_comp12, pvalue1_comp13, pvalue1_comp23
        print "Round2", np.nanmean(round2_low), np.nanmean(round2_med), np.nanmean(round2_high), np.nanstd(round2_low), np.nanstd(round2_med), np.nanstd(round2_high), pvalue2_comp12, pvalue2_comp13, pvalue2_comp23


    def TempAnalysisAPOE(self, metabolite, trait):

        round1_low = []
        round1_med = []
        round1_high = []
        round1_high2 = []
        round1_high3 = []
        round1_high4 = []

        round2_low = []
        round2_med = []
        round2_high = []
        round2_high2 = []
        round2_high3 = []
        round2_high4 = []

        scores1_low = []
        scores1_med = []
        scores1_high = []
        scores1_high2 = []
        scores1_high3 = []
        scores1_high4 = []

        scores2_low = []
        scores2_med = []
        scores2_high = []
        scores2_high2 = []
        scores2_high3 = []
        scores2_high4 = []

        for key in sorted(self.participants.keys()):

            result = self.participants[key].TempAnalysis(metabolite, trait)

            if (result is None):
                continue;

            (score, values, dates) = result
            print score

            if (values.size == 1):

                if (not np.isnan(values)):

                    if (int(dates)==1):

                        if (score == 0):
                            scores1_low.append(score);
                            round1_low.append(float(values));
                        elif (score == 1):
                            scores1_med.append(score);
                            round1_med.append(float(values));
                        elif (score == 2):
                            scores1_high.append(score);
                            round1_high.append(float(values));
                        elif (score == 3):
                            scores1_high2.append(score);
                            round1_high2.append(float(values));
                        elif (score == 4):
                            scores1_high3.append(score);
                            round1_high3.append(float(values));
                        elif (score == 5):
                            scores1_high4.append(score);
                            round1_high4.append(float(values));
                        else:
                            print "Failed"

                    else:

                        if (score == 0):
                            scores2_low.append(score);
                            round2_low.append(float(values));
                        elif (score == 1):
                            scores2_med.append(score);
                            round2_med.append(float(values));
                        elif (score == 2):
                            scores2_high.append(score);
                            round2_high.append(float(values));
                        elif (score == 3):
                            scores2_high2.append(score);
                            round2_high2.append(float(values));
                        elif (score == 4):
                            scores2_high3.append(score);
                            round2_high3.append(float(values));
                        elif (score == 5):
                            scores2_high4.append(score);
                            round2_high4.append(float(values));
                        else:
                            print "Failed"

            else:

                if (not np.isnan(values[0])):

                    if (score == 0):
                        scores1_low.append(score);
                        round1_low.append(float(values[0]));
                    elif (score == 1):
                        scores1_med.append(score);
                        round1_med.append(float(values[0]));
                    elif (score == 2):
                        scores1_high.append(score);
                        round1_high.append(float(values[0]));
                    elif (score == 3):
                        scores1_high2.append(score);
                        round1_high2.append(float(values[0]));
                    elif (score == 4):
                        scores1_high3.append(score);
                        round1_high3.append(float(values[0]));
                    elif (score == 5):
                        scores1_high4.append(score);
                        round1_high4.append(float(values[0]));
                    else:
                        print "Failed"

                if (not np.isnan(values[1])):

                    if (score == 0):
                        scores2_low.append(score);
                        round2_low.append(float(values[1]));
                    elif (score == 1):
                        scores2_med.append(score);
                        round2_med.append(float(values[1]));
                    elif (score == 2):
                        scores2_high.append(score);
                        round2_high.append(float(values[1]));
                    elif (score == 3):
                        scores2_high2.append(score);
                        round2_high2.append(float(values[1]));
                    elif (score == 4):
                        scores2_high3.append(score);
                        round2_high3.append(float(values[1]));
                    elif (score == 5):
                        scores2_high4.append(score);
                        round2_high4.append(float(values[1]));
                    else:
                        print "Failed"

        round1_low = np.array(round1_low)
        round1_med = np.array(round1_med)
        round1_high = np.array(round1_high)
        round1_high2 = np.array(round1_high2)
        round1_high3 = np.array(round1_high3)
        round1_high4 = np.array(round1_high4)

        round2_low = np.array(round2_low)
        round2_med = np.array(round2_med)
        round2_high = np.array(round2_high)
        round2_high2 = np.array(round2_high2)
        round2_high3 = np.array(round2_high3)
        round2_high4 = np.array(round2_high4)

        (score_comp12, pvalue1_comp12) = stats.ranksums(round1_low, round1_med)
        (score_comp13, pvalue1_comp13) = stats.ranksums(round1_low, round1_high)
        (score_comp23, pvalue1_comp23) = stats.ranksums(round1_med, round1_high)

        (score_comp12, pvalue2_comp12) = stats.ranksums(round2_low, round2_med)
        (score_comp13, pvalue2_comp13) = stats.ranksums(round2_low, round2_high)
        (score_comp23, pvalue2_comp23) = stats.ranksums(round2_med, round2_high)

        #print "Round", "Mean_No_effect_(%s,%s)"%(round1_low.size,round2_low.size), "Mean_Het_effect_(%s,%s)"%(round1_med.size,round2_med.size), "Mean_Hom_effect_(%s,%s)"%(round1_high.size,round2_high.size), "Std_No_effect", "Std_Het_effect", "Std_Hom_effect"
        print "E2/E2_(%s,%s)"%(round1_low.size,round2_low.size),"E2/E3_(%s,%s)"%(round1_med.size,round2_med.size),"E2/E4_(%s,%s)"%(round1_high.size,round2_high.size),"E3/E3_(%s,%s)"%(round1_high2.size,round2_high2.size),"E3/E4_(%s,%s)"%(round1_high3.size,round2_high3.size),"E4/E4_(%s,%s)"%(round1_high4.size,round2_high4.size)
        print "Round1", np.nanmean(round1_low), np.nanmean(round1_med), np.nanmean(round1_high), np.nanmean(round1_high2), np.nanmean(round1_high3),np.nanmean(round1_high4), np.nanstd(round1_low), np.nanstd(round1_med), np.nanstd(round1_high), np.nanstd(round1_high2), np.nanstd(round1_high3), np.nanstd(round1_high4),pvalue1_comp12, pvalue1_comp13, pvalue1_comp23
        print "Round2", np.nanmean(round2_low), np.nanmean(round2_med), np.nanmean(round2_high), np.nanmean(round2_high2), np.nanmean(round2_high3),np.nanmean(round2_high4), np.nanstd(round2_low), np.nanstd(round2_med), np.nanstd(round2_high), np.nanstd(round2_high2), np.nanstd(round2_high3), np.nanstd(round2_high4),pvalue2_comp12, pvalue2_comp13, pvalue2_comp23

    def CheckLead(self):
        for key in sorted(self.participants.keys()):
            self.participants[key].CheckLead();

    def Inflammation(self):

        prts = set(['2627674', '8112973', '5532227', '3007543'])

        for key in sorted(self.participants.keys()):

            if (key in prts):

                current = self.participants[key]
                (dates, values, range) = current.GetMeasurement('BODY_MASS_INDEX');
                print key, dates, values, range

    def BuildTransitionReports(self, force=None):

        for key in sorted(self.participants.keys()):

            if (not force is None):
                if (force == key):
                    print "Forcing transition report for participant %s"%(key)
                    report = TransitionsReport(self.participants[key]);
                    report.go(True)
            else:

                print "Building transition report for participant %s"%(key)
                report = TransitionsReport(self.participants[key])
                report.go()

    def BuildPharmacogeneticsReports(self, force=None):

        for key in sorted(self.participants.keys()):

            if (not force is None):
                if (force == key):
                    print "Forcing pharmacogenetics report for participant %s"%(key)
                    report = PharmacogeneticsReport(self.participants[key]);
                    report.go(True)
            else:

                print "Building pharmacogenetics report for participant %s"%(key)
                report = PharmacogeneticsReport(self.participants[key]);
                report.go(True)

    def BuildDiseaseReports(self, force=None):

        for key in sorted(self.participants.keys()):

            if (not force is None):
                if (force == key):
                    print "Forcing disease report for participant %s"%(key)
                    report = DiseaseReport(self.participants[key]);
                    report.BuildAlzheimersReport(True)
                    report.BuildParkinsonsReport(True)
            else:

                print "Building disease report for participant %s"%(key)
                report = DiseaseReport(self.participants[key]);
                report.BuildAlzheimersReport(True)
                report.BuildParkinsonsReport(True)

    def BuildDNAlysis(self):

        variants = None

        for key in sorted(self.participants.keys()):
            print "Loading %s"%(key)
            self.participants[key].LoadTrait('DNAlysis', 1, True)

            if (variants is None):
                variants = self.participants[key].traits['DNAlysis'].variants.keys()

        # Open the output file
        with open('results/DNAlysis.final.txt', 'w') as f:

            for key in sorted(self.participants.keys()):

                if (not 'DNAlysis' in self.participants[key].traits):
                    continue

                f.write("\t%s"%(key))
            f.write('\n')

            for rsid in sorted(variants):

                f.write("%s"%(rsid))

                for key in sorted(self.participants.keys()):

                    if (not 'DNAlysis' in self.participants[key].traits):
                        continue

                    f.write("\t%s"%(self.participants[key].traits['DNAlysis'].variants[rsid].genotype))
                f.write('\n')

    def MetaboliteStats(self):

        usernames = []
        data = []

        for username in sorted(self.participants.keys()):

            for metabolite in sorted(self.metabolites):
                (dates, values, range) = self.participants[username].GetMetabolites(metabolite)
                print username, metabolite, values, range

    def ComplianceFishOil(self):

        ldl_compliance = []
        ldl_noncompliance = []

        # Go through each participant, write out the delta vitD values, and then
        # write out the compliance metric (if present)
        for prt in sorted(self.participants.keys()):

            # Get the measurement
            (dates, values, range) = self.participants[prt].GetMeasurement("LDL_CHOLESTEROL");

            if (values.size<2):
                continue;
            if (np.isnan(values[0])):
                continue;
            if (np.isnan(values[1])):
                continue;
            if (values[0] == 0):
                continue;
            if (values[1] == 0):
                continue;

            # We are going to swap these
            first_value = values[0]
            second_value = values[1]

            # Now get the compliance
            fishoil_recommended = self.participants[prt].compliance['fishoil_recommended']
            if (fishoil_recommended is None):
                continue;

            fishoil_compliance = self.participants[prt].compliance['fishoil_compliance']
            if (fishoil_compliance is None):
                continue;

            difference = second_value - first_value

            if (fishoil_compliance == 1):

                ldl_compliance.append(difference)

            else:
                print prt
                ldl_noncompliance.append(difference)

        ldl_avg_compliance = np.nanmean(ldl_compliance)
        ldl_std_compliance = np.nanstd(ldl_compliance)
        ldl_avg_noncompliance = np.nanmean(ldl_noncompliance)
        ldl_std_noncompliance = np.nanstd(ldl_noncompliance)

        print ldl_compliance
        print ldl_noncompliance

        print "FishOil", ldl_avg_compliance, ldl_std_compliance
        print "None", ldl_avg_noncompliance, ldl_std_noncompliance

    def Classification(self):

        # Open output file
        fout = open('results/classification_exercise.txt', 'w')

        # Write headers
        #fout.write("USERNAME\tVITD\tVITD_COMP");
        fout.write("USERNAME\tFISHOIL_REC\tFISHOIL_COMP");

        for measurement in sorted(self.ranges.keys()):
            if (measurement == "LDL_PATTERN_QUEST"):
                continue
            fout.write("\t%s"%(measurement));
        fout.write('\n');

        # For each participant
        for prt in sorted(self.participants.keys()):

            print prt

            """
            # Now get the compliance
            vitD_recommended = self.participants[prt].compliance['vitD_recommended']
            if (vitD_recommended is None):
                continue;

            vitD_amount = self.participants[prt].compliance['vitD_amount']
            if (vitD_amount is None):
                continue;

            vitD_compliance = self.participants[prt].compliance['vitD_compliance']
            if (vitD_compliance is None):
                continue;
            """

            """
            fishoil_recommended = self.participants[prt].compliance['fishoil_recommended']
            if (fishoil_recommended is None):
                continue;

            fishoil_compliance = self.participants[prt].compliance['fishoil_compliance']
            """

            fishoil_recommended = self.participants[prt].compliance['exercise_changed']
            if (fishoil_recommended is None):
                continue;

            fishoil_compliance = -1

            # Write to the file
            fout.write("%s\t%d\t%s"%(prt, fishoil_recommended, fishoil_compliance))

            # For each measurement
            for measurement in sorted(self.ranges.keys()):

                if (measurement == "LDL_PATTERN_QUEST"):
                    continue

                difference = []

                # Get the data
                (dates, values, range) = self.participants[prt].GetMeasurement(measurement);

                # Filter the data
                if (values.size<2):
                    fout.write("\t%s"%('NULL'))
                elif (np.isnan(values[0])):
                    fout.write("\t%s"%('NULL'))
                elif (np.isnan(values[1])):
                    fout.write("\t%s"%('NULL'))
                else:

                    # Get the change that has taken place
                    fout.write("\t%.2f"%(values[1]-values[0]))

            fout.write('\n');

    def Compliance(self):

        sum_2000 = []
        sum_3000 = []
        sum_4000 = []
        sum_5000 = []
        sum_6000 = []
        sum_10000 = []
        noncompliant = []

        # Go through each participant, write out the delta vitD values, and then
        # write out the compliance metric (if present)
        for prt in sorted(self.participants.keys()):

            # Get the measurement
            (dates, values, range) = self.participants[prt].GetMeasurement("VITAMIN_D");

            if (values.size<2):
                continue;
            if (np.isnan(values[0])):
                continue;
            if (np.isnan(values[1])):
                continue;

            # TAKE THIS AWAY WITH NEW LOADED DATA
            if (values[0] == 0):
                continue;
            if (values[1] == 0):
                continue;

            # We are going to swap these
            first_value = values[0]
            second_value = values[1]

            # Now get the compliance
            vitD_recommended = self.participants[prt].compliance['vitD_recommended']
            if (vitD_recommended is None):
                continue;

            vitD_amount = self.participants[prt].compliance['vitD_amount']
            if (vitD_amount is None):
                continue;

            vitD_compliance = self.participants[prt].compliance['vitD_compliance']
            if (vitD_compliance is None):
                continue;

            difference = second_value - first_value


            if (vitD_compliance == 1):

                if (vitD_amount <= 2000):
                    sum_2000.append(difference)
                elif (vitD_amount <= 3000):
                    sum_3000.append(difference)
                elif (vitD_amount <= 4000):
                    sum_4000.append(difference)
                elif (vitD_amount <= 5000):
                    sum_5000.append(difference)
                elif (vitD_amount <= 6000):
                    sum_6000.append(difference)
                elif (vitD_amount == 10000):
                    sum_10000.append(difference);
                else:
                    print "Unknown amount", vitD_amount

            else:
                noncompliant.append(difference)
                print self.participants[prt].id, first_value, second_value, second_value-first_value, vitD_recommended, vitD_amount, vitD_compliance

        avg_2000 = np.nanmean(sum_2000)
        std_2000 = np.nanstd(sum_2000)
        avg_3000 = np.nanmean(sum_3000)
        std_3000 = np.nanstd(sum_3000)
        avg_4000 = np.nanmean(sum_4000)
        std_4000 = np.nanstd(sum_4000)
        avg_5000 = np.nanmean(sum_5000)
        std_5000 = np.nanstd(sum_5000)
        avg_6000 = np.nanmean(sum_6000)
        std_6000 = np.nanstd(sum_6000)
        avg_10000 = np.nanmean(sum_10000)
        std_10000 = np.nanstd(sum_10000)
        avg_non = np.nanmean(noncompliant)
        std_non = np.nanstd(noncompliant)

        print "None", len(noncompliant), avg_non, std_non
        print "2000", len(sum_2000), avg_2000, std_2000
        print "3000", len(sum_3000), avg_3000, std_3000
        print "4000", len(sum_4000), avg_4000, std_4000
        print "5000", len(sum_5000), avg_5000, std_5000
        print "6000", len(sum_6000), avg_6000, std_6000
        print "10000", len(sum_10000), avg_10000, std_10000

    def KristinStats(self):

        data = {}

        # Build numpy array for a metabolite
        for prt in sorted(self.participants.keys()):

            # Create the data dictionary for this participant
            data[prt] = {}
            data[prt]['SigAbove'] = set()
            data[prt]['BadAbove'] = set()
            data[prt]['NoAbove'] = set()
            data[prt]['InRange'] = set()
            data[prt]['SigBelow'] = set()
            data[prt]['BadBelow'] = set()
            data[prt]['NoBelow'] = set()

            count = 0
            for measurement in sorted(self.ranges.keys()):

                # Get the measurement from this participant
                (dates, values, range) = self.participants[prt].GetMeasurement(measurement);

                if (measurement == "LDL_PATTERN_QUEST"):
                    if (values.size<2):
                        continue

                    # We are going to swap these
                    first_value = values[0]
                    second_value = values[1]

                    if (first_value == 'A'):
                        if (second_value == 'A'):
                            data[prt]['InRange'].add(measurement)
                        elif (second_value == 'B'):
                            data[prt]['BadAbove'].add(measurement)
                        else:
                            print "Unknown Pattern"
                    elif (first_value == 'B'):
                        if (second_value == 'A'):
                            data[prt]['SigAbove'].add(measurement)
                        elif (second_value == 'B'):
                            data[prt]['NoAbove'].add(measurement)
                        else:
                            print "Unknown Pattern"

                else:

                    if (values.size<2):
                        continue;
                    if (np.isnan(values[0])):
                        continue;
                    if (np.isnan(values[1])):
                        continue;

                    # We are going to swap these
                    first_value = values[0]
                    second_value = values[1]

                    # Check to see if first value is out of range
                    out1 = self.ranges[measurement].OutOfRange(first_value, self.participants[prt].gender);
                    out2 = self.ranges[measurement].OutOfRange(second_value, self.participants[prt].gender);

                    if (first_value != 0):
                        diff = (second_value-first_value) / first_value;
                    else:
                        diff = 0
                    sd = 0.05

                    #diff = second_value - first_value;
                    #sd = self.ranges[measurement].sd * 0.5

                    # We are above the reference range
                    if (out1 >= 1):

                        # More than 10% change towards the reference range is good
                        if (diff <= -sd):
                            data[prt]['SigAbove'].add(measurement)

                        # More than 10% change away from the reference range is bad
                        elif (diff >= sd):
                            data[prt]['BadAbove'].add(measurement)

                        # We are out of range but no sig change
                        else:
                            data[prt]['NoAbove'].add(measurement)

                    elif (out1 == 0):

                        data[prt]['InRange'].add(measurement)

                        pass
                        """
                        # Only count as bad if out2 is out of range
                        if (out2 < 0):

                            data[prt]['BadBelow'].add(measurement)

                        elif (out2 > 0):

                            data[prt]['BadAbove'].add(measurement)
                        """

                    if (out1 == -1):

                        # More than 10% change is always significant
                        if (diff >= sd):
                            data[prt]['SigBelow'].add(measurement)

                        elif (diff <= -sd):
                            data[prt]['BadBelow'].add(measurement)

                        # We are out of range but no sig change
                        else:
                            data[prt]['NoBelow'].add(measurement)


        #used = set(['TOTAL_CHOLESTEROL', 'LDL_CHOLESTEROL', 'TRIGLYCERIDES', 'FERRITIN_QUEST', 'VITAMIN_D', 'ZINC', 'BODY_MASS_INDEX', 'HS_CRP', 'INTERLEUKIN_IL_6', 'INTERLEUKIN_IL_8', 'TNFALPHA', 'PAI_1', 'AVERAGE_INFLAMMATION_SCORE', 'GLUCOSE', 'INSULIN', 'HEMOGLOBIN_A1C', 'HOMA_IR'])
        cv = set(['TOTAL_CHOLESTEROL', 'LDL_CHOLESTEROL', 'TRIGLYCERIDES', 'LDL_PATTERN_QUEST'])
        db = set(['GLUCOSE', 'INSULIN', 'HEMOGLOBIN_A1C', 'HOMA_IR'])
        inf = set(['HS_CRP', 'INTERLEUKIN_IL_6', 'INTERLEUKIN_IL_8', 'TNFALPHA', 'PAI_1', 'AVERAGE_INFLAMMATION_SCORE'])
        vit = set(['FERRITIN_QUEST', 'VITAMIN_D', 'ZINC', 'BODY_MASS_INDEX'])

        # Now go through the data structure and print out those in the Sig category
        prts = []
        cv_scores = []
        db_scores = []
        inf_scores = []
        vit_scores = []

        for prt in sorted(data.keys()):
            prts.append(prt)
            self.LinkMeasurements(prt, data, cv, cv_scores)
            self.LinkMeasurements(prt, data, db, db_scores)
            self.LinkMeasurements(prt, data, inf, inf_scores)
            self.LinkMeasurements(prt, data, vit, vit_scores)

        with open('results/kristin.scores.txt', 'w') as fout:

            fout.write("Username\tCardiovascular\tDiabetes\tInflammation\tVitamin\n");

            for e, f, g, h, i in zip(prts, cv_scores, db_scores, inf_scores, vit_scores):
                fout.write("%s\t%s\t%s\t%s\t%s\n"%(e, f, g, h, i))

    def LinkMeasurements(self, prt, data, mset, mset_scores):

        state = set()

        # Intersect each category with the set
        intersect = data[prt]['SigAbove'].intersection(mset)
        if (len(intersect)) >= math.ceil(float(len(mset))/2.0):
            state.add('AboveGood2')
        elif (len(intersect)>0):
            state.add('AboveGood1')

        # Intersect each category with the set
        intersect = data[prt]['BadAbove'].intersection(mset)
        if (len(intersect)) >= math.ceil(float(len(mset))/2.0):
            state.add('AboveBad2')
        elif (len(intersect)>0):
            state.add('AboveBad1')

        # Intersect each category with the set
        intersect = data[prt]['NoAbove'].intersection(mset)
        if (len(intersect)) >= math.ceil(float(len(mset))/2.0):
            state.add('AboveNo2')
        elif (len(intersect)>0):
            state.add('AboveNo1')

        # Intersect each category with the set
        intersect = data[prt]['SigBelow'].intersection(mset)
        if (len(intersect)) >= math.ceil(float(len(mset))/2.0):
            state.add('BelowGood2')
        elif (len(intersect)>0):
            state.add('BelowGood1')

        # Intersect each category with the set
        intersect = data[prt]['BadBelow'].intersection(mset)
        if (len(intersect)) >= math.ceil(float(len(mset))/2.0):
            state.add('BelowBad2')
        elif (len(intersect)>0):
            state.add('BelowBad1')

        # Intersect each category with the set
        intersect = data[prt]['NoBelow'].intersection(mset)
        if (len(intersect)) >= math.ceil(float(len(mset))/2.0):
            state.add('BelowNo2')
        elif (len(intersect)>0):
            state.add('BelowNo1')

        if (len(state)==0):
            mset_scores.append('InRange')
        elif (len(state)==1):
            mset_scores.append(state.pop())
        else:
            mset_scores.append('/'.join(list(state)))

    def Round1VsRound2VitaminD(self):

        for measurement in sorted(self.ranges.keys()):

            round1 = []
            round2 = []
            nochange1 = []
            nochange2 = []

            if (measurement == "LDL_PATTERN_QUEST"):
                continue

            for prt in sorted(self.participants.keys()):

                (dates, values, range) = self.participants[prt].GetMeasurement(measurement);

                if (values.size<2):
                    continue;
                if (np.isnan(values[0])):
                    continue;
                if (np.isnan(values[1])):
                    continue;

                # Get the fishoil compliance status
                vitD_amount = self.participants[prt].compliance['vitD_amount']
                if (vitD_amount is None):
                    continue

                # Get the fishoil compliance status
                vitD_compliance = self.participants[prt].compliance['vitD_compliance']
                if (vitD_amount is None):
                    continue

                if (vitD_compliance == 0):

                    nochange1.append(values[0])
                    nochange2.append(values[1])

                elif (vitD_amount >= 4000):

                    round1.append(values[0])
                    round2.append(values[1])


            # At the end of all participants, convert to Numpy
            round1 = np.array(round1)
            round2 = np.array(round2)
            nochange1 = np.array(nochange1)
            nochange2 = np.array(nochange2)

            # Calculate the stats between round1 and round2
            (score_comp, pvalue_comp) = stats.ranksums(round1, round2)
            (score_non, pvalue_non) = stats.ranksums(nochange1, nochange2)

            if (pvalue_comp < 0.05):
                print measurement, stats.nanmean(round1), stats.nanmean(round2), pvalue_comp, stats.nanmean(nochange1), stats.nanmean(nochange2), pvalue_non

    def Round1VsRound2Exercise(self):

        for measurement in sorted(self.ranges.keys()):

            round1 = []
            round2 = []
            nochange1 = []
            nochange2 = []

            if (measurement == "LDL_PATTERN_QUEST"):
                continue

            for prt in sorted(self.participants.keys()):

                (dates, values, range) = self.participants[prt].GetMeasurement(measurement);

                if (values.size<2):
                    continue;
                if (np.isnan(values[0])):
                    continue;
                if (np.isnan(values[1])):
                    continue;

                # Get the fishoil compliance status
                exercise_changed = self.participants[prt].compliance['exercise_changed']
                if (exercise_changed is None):
                    continue

                if (exercise_changed == 0):

                    nochange1.append(values[0])
                    nochange2.append(values[1])

                elif (exercise_changed == 1):

                    round1.append(values[0])
                    round2.append(values[1])


            # At the end of all participants, convert to Numpy
            round1 = np.array(round1)
            round2 = np.array(round2)
            nochange1 = np.array(nochange1)
            nochange2 = np.array(nochange2)

            # Calculate the stats between round1 and round2
            (score_comp, pvalue_comp) = stats.ranksums(round1, round2)
            (score_non, pvalue_non) = stats.ranksums(nochange1, nochange2)

            if (pvalue_comp < 0.05) and (pvalue_non > 0.05):
                print measurement, stats.nanmean(round1), stats.nanmean(round2), pvalue_comp, stats.nanmean(nochange1), stats.nanmean(nochange2), pvalue_non

    def Round1VsRound2FishOil(self):

        for measurement in sorted(self.ranges.keys()):

            round1 = []
            round2 = []
            notrecommended1 = []
            notrecommended2 = []
            noncompliance1 = []
            noncompliance2 = []

            if (measurement == "LDL_PATTERN_QUEST"):
                continue

            for prt in sorted(self.participants.keys()):

                (dates, values, range) = self.participants[prt].GetMeasurement(measurement);

                if (values.size<2):
                    continue;
                if (np.isnan(values[0])):
                    continue;
                if (np.isnan(values[1])):
                    continue;

                # Get the fishoil compliance status
                recommended = self.participants[prt].compliance['multiVit_recommended']
                compliance = self.participants[prt].compliance['multiVit_compliance']

                if (recommended == 0):

                    notrecommended1.append(values[0])
                    notrecommended2.append(values[1])

                elif (recommended == 1):

                    if (compliance is None):
                        continue;

                    elif (compliance == 0):
                        noncompliance1.append(values[0])
                        noncompliance2.append(values[1])

                    elif (compliance == 1):
                        round1.append(values[0])
                        round2.append(values[1])


            # At the end of all participants, convert to Numpy
            round1 = np.array(round1)
            round2 = np.array(round2)
            notrecommended1 = np.array(notrecommended1)
            notrecommended2 = np.array(notrecommended2)
            noncompliance1 = np.array(noncompliance1)
            noncompliance2 = np.array(noncompliance2)

            # Calculate the stats between round1 and round2
            (score_comp, pvalue_comp) = stats.ranksums(round1, round2);
            (score_non, pvalue_non) = stats.ranksums(notrecommended1, notrecommended2);

            if (pvalue_comp < 0.05) and (pvalue_non >= 0.05):
                print measurement, stats.nanmean(round1), stats.nanmean(round2), pvalue_comp, stats.nanmean(notrecommended1), stats.nanmean(notrecommended2), pvalue_non


    def Correlations(self):

        for measurement in self.ranges.keys():

            if (measurement == "LDL_PATTERN_QUEST"):
                continue;

            round1 = []
            round2 = []
            prts = []
            sum1 = 0;
            sum2 = 0;

            prts_above = []
            round1_above = []
            above_inrange = []

            prts_above_male = []
            round1_above_male = []
            above_inrange_male = []
            prts_above_female = []
            round1_above_female = []
            above_inrange_female = []

            prts_below = []
            round1_below = []
            below_inrange = []

            prts_below_male = []
            round1_below_male = []
            below_inrange_male = []
            prts_below_female = []
            round1_below_female = []
            below_inrange_female = []

            # Build numpy array for a metabolite
            for prt in sorted(self.participants.keys()):

                # Get the measurement
                (dates, values, range) = self.participants[prt].GetMeasurement(measurement);

                if (values.size<2):
                    continue;
                if (np.isnan(values[0])):
                    continue;
                if (np.isnan(values[1])):
                    continue;

                # We are going to swap these
                first_value = values[0]
                second_value = values[1]

                # Append all values
                prts.append(prt)
                round1.append(first_value)
                round2.append(second_value)

                # Check to see if first value is out of range
                out1 = self.ranges[measurement].OutOfRange(first_value, self.participants[prt].gender);

                # Now check to see if we have crossed a reference range or not
                if (out1 == 2):

                    prts_above.append(prt)
                    round1_above.append(first_value)
                    above_inrange.append(second_value)

                    if (self.participants[prt].gender == "M"):
                        prts_above_male.append(prt)
                        round1_above_male.append(first_value)
                        above_inrange_male.append(second_value)
                    else:
                        prts_above_female.append(prt)
                        round1_above_female.append(first_value)
                        above_inrange_female.append(second_value)

                if (out1 == -2):

                    prts_below.append(prt)
                    round1_below.append(first_value)
                    below_inrange.append(second_value)

                    if (self.participants[prt].gender == "M"):
                        prts_below_male.append(prt)
                        round1_below_male.append(first_value)
                        below_inrange_male.append(second_value)
                    else:
                        prts_below_female.append(prt)
                        round1_below_female.append(first_value)
                        below_inrange_female.append(second_value)

            # Create numpy arrays
            round1 = np.array(round1)
            round2 = np.array(round2)
            round1_above = np.array(round1_above)
            above_inrange = np.array(above_inrange)
            round1_below = np.array(round1_below)
            below_inrange = np.array(below_inrange)

            round1_above_male = np.array(round1_above_male)
            above_inrange_male = np.array(above_inrange_male)
            round1_above_female = np.array(round1_above_female)
            above_inrange_female = np.array(above_inrange_female)

            round1_below_male = np.array(round1_below_male)
            below_inrange_male = np.array(below_inrange_male)
            round1_below_female = np.array(round1_below_female)
            below_inrange_female = np.array(below_inrange_female)

            """
            if (round1.size > 40):
                (rvalue, pvalue_corr) = stats.pearsonr(round1, round2)
                (score, pvalue) = stats.wilcoxon(round1, round2);

                # Print out the values for all participants
                print measurement, round1.size, stats.nanmean(round1), stats.nanmean(round2), stats.nanstd(round1), stats.nanstd(round2), score, pvalue, rvalue, pvalue_corr
            """

            if (round1_above.size >= 3):

                # Print major measurement
                (score, pvalue) = stats.wilcoxon(round1, round2);
                print "ALL", measurement, round1.size, stats.nanmean(round1), stats.nanmean(round2), stats.nanstd(round1), stats.nanstd(round2), pvalue,

                (score_above, pvalue_above) = stats.wilcoxon(round1_above, above_inrange)
                print "ABOVE", measurement, round1_above.size, stats.nanmean(round1_above), stats.nanmean(above_inrange), stats.nanstd(round1_above), stats.nanstd(above_inrange), pvalue_above,

                try:
                    if (round1_above_male.size > 0):
                        (score_above_male, pvalue_above_male) = stats.wilcoxon(round1_above_male, above_inrange_male)
                        print "MALE", round1_above_male.size, stats.nanmean(round1_above_male), stats.nanmean(above_inrange_male), stats.nanstd(round1_above_male), stats.nanstd(above_inrange_male), pvalue_above_male,
                    else:
                        print "MALE", round1_above_male.size, 0, 0, 0, 0, 0,
                except:
                    print "FAILED", 0, 0, 0, 0, 0, 0,

                try:
                    if (round1_above_female.size > 0):
                        (score_above_female, pvalue_above_female) = stats.wilcoxon(round1_above_female, above_inrange_female)
                        print "FEMALE", round1_above_female.size, stats.nanmean(round1_above_female), stats.nanmean(above_inrange_female), stats.nanstd(round1_above_female), stats.nanstd(above_inrange_female), pvalue_above_female,
                    else:
                        print "FEMALE", round1_above_female.size, 0, 0, 0, 0, 0,
                    print
                except:
                    print "FAILED", 0, 0, 0, 0, 0, 0

            if (round1_below.size >= 3):

                # Print major measurement
                (score, pvalue) = stats.wilcoxon(round1, round2);
                print "ALL", measurement, round1.size, stats.nanmean(round1), stats.nanmean(round2), stats.nanstd(round1), stats.nanstd(round2), pvalue,

                (score_below, pvalue_below) = stats.wilcoxon(round1_below, below_inrange)
                print "BELOW", measurement, round1_below.size, stats.nanmean(round1_below), stats.nanmean(below_inrange), stats.nanstd(round1_below), stats.nanstd(below_inrange), pvalue_below,

                try:
                    if (round1.size > 0):
                        (score_below_male, pvalue_below_male) = stats.wilcoxon(round1_below_male, below_inrange_male)
                        print "MALE", round1_below_male.size, stats.nanmean(round1_below_male), stats.nanmean(below_inrange_male), stats.nanstd(round1_below_male), stats.nanstd(below_inrange_male), pvalue_below_male,
                    else:
                        print "MALE", round1_below_male.size, 0, 0, 0, 0, 0,
                except:
                    print "FAILED", 0, 0, 0, 0, 0, 0,

                try:
                    if (round1_below_female.size > 0):
                        (score_below_female, pvalue_below_female) = stats.wilcoxon(round1_below_female, below_inrange_female)
                        print "FEMALE", round1_below_female.size, stats.nanmean(round1_below_female), stats.nanmean(below_inrange_female), stats.nanstd(round1_below_female), stats.nanstd(below_inrange_female), pvalue_below_female,
                    else:
                        print "FEMALE", round1_below_female.size, 0, 0, 0, 0, 0,
                    print
                except:
                    print "FAILED", 0, 0, 0, 0, 0, 0

            # Set this value in the range class
            #self.ranges[measurement].rvalue = rvalue;
            #self.ranges[measurement].pvalue = pvalue;
            #self.ranges[measurement].mean = stats.nanmean(round1);
            #self.ranges[measurement].stdev = stats.nanstd(round1);

        """
        A = 0;
        B = 0;
        A2B = 0
        B2A = 0;

        # For each participant, now find the values that change between round 1 and round2
        for prt in self.participants.keys():
            result = self.participants[prt].Correlations();

        # Now print the number of changes for each measurement
        for measurement in self.ranges.keys():
            avg_change = np.array(self.ranges[measurement].avg_change);
            print measurement, self.ranges[measurement].changed, self.ranges[measurement].sum_change, stats.nanmean(avg_change);

        # Calculate the correlation with Cholesterol
        beta_coeff = [];
        round1 = [];
        round2 = [];
        for prt in self.participants.keys():

            beta = self.participants[prt].GetGWASTraitScore("CHOLESTEROL, TOTAL");

            if (beta is None):
                continue;

            print "Got beta score for prt %s"%(prt)

            (dates, values, range) = self.participants[prt].GetMeasurement("TOTAL_CHOLESTEROL");
            #(dates, values, range) = self.participants[prt].GetMeasurement("LDL_SMALL_QUEST");

            if (values.size<2):
                continue;
            if (np.isnan(values[0])):
                continue;
            if (np.isnan(values[1])):
                continue;
            if (values[0] == 0):
                continue;
            if (values[1] == 0):
                continue;

            round1.append(values[0]);
            round2.append(values[1]);
            beta_coeff.append(beta);



        scores = np.array(beta_coeff);

        print scores;
        print round1
        print round2
        print stats.pearsonr(scores, round1);
        print stats.pearsonr(scores, round2);
        """

    def ProcessGWAS(self):

        # Open output file
        with open("./results/gwas_matrix.txt", "w") as f:

            # Write out the traits
            for key in sorted(self.gwas_db.db.keys()):
                f.write("\t%s" % (key))
            f.write('\n')

            for key in sorted(self.participants.keys()):
                self.participants[key].ProcessGWAS()
                self.participants[key].WriteGWASTraitScores(f)

                #self.ProcessGWASTrait("Alzheimer's disease (late onset)")
                #self.ProcessGWASTrait("Psoriasis")

    def ProcessGWASTrait(self, trait):

        for key in sorted(self.participants.keys()):
            self.participants[key].ProcessGWASTrait(trait)

    def AddMetabolites(self, filename):

        # Get list of participants from the participants table
        results = self.database.Command("SELECT username FROM participants")

        # We have already loaded the measurements from the range table
        for measurement in self.measurements:
            results = self.database.Command("SELECT " + measurement + " FROM data WHERE ")


