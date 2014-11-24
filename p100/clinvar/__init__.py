"""
    __init__.py "

    Author: Andrew Magis
    Date: July 29th, 2014

"""
import time, gzip, sys
from errors import MyError

class ClinvarEntry(object):

    def __init__(self, rsid, chr, pos, ref, alt, geneinfo, wgt, vc, clnalle, clnhgvs, clnsrc, clnsrcid, clnsig, clndsdb, clndsdbid, clndbn, clnrevstat, clnacc, caf, common):

        self.chr = chr
        self.pos = pos
        self.rsid = rsid
        self.ref = ref
        self.alt = alt.split(',')

        self.geneinfo = geneinfo

        # Split by |
        self.genes = set()
        self.ncbi = set()

        if (not geneinfo is None):
            for gene in geneinfo.split('|'):
                temp = gene.split(':')
                symbol = temp[0].strip()
                ncbi = temp[1].strip()
                self.genes.add(symbol)
                self.ncbi.add(ncbi)

        self.wgt = wgt
        self.vc = vc
        self.clnalle = clnalle.split(',')
        self.clnhgvs = clnhgvs.split(',')
        self.clnsrc = clnsrc.split(',')
        self.clnsrcid = clnsrcid.split(',')
        self.clnsig = clnsig.split(',')
        self.clndsdb = clndsdb.split(',');
        self.clndsdbid = clndsdbid.split(',')
        self.clndbn = clndbn.split(',')
        self.clnrevstat = clnrevstat.split(',')
        self.clnacc = clnacc.split(',')
        self.caf = caf
        self.common = common

        # Add reference to set of possible alleles
        self.alleles = list(self.alt)
        self.alleles.insert(0, self.ref)

        # These are the valid alleles to compare to
        self.valid_alleles = None
        self.valid_sigs = None
        self.submitters = None
        self.quality = None
        self.inheritance = None

    def CheckOMIM(self, omim_disease):

        omim_present = False
        for clndsdb,clndsdbid in zip(self.clndsdb,self.clndsdbid):
            if ("OMIM" in clndsdb):
                omim_present = True
                if (omim_disease in clndsdbid):
                    return True

        # If OMIM was found but our omim_disease was not, return False
        if (omim_present):
            return False;
        # If OMIM was not present, we assume it is correct in the clinvar entry
        return True

    def Validate(self, sigs, no_conflict, min_submitters, inheritance = None):

        self.valid_alleles = []
        self.valid_sigs = []
        self.submitters = []
        self.quality = []
        self.inheritance = inheritance

        # clnsig == 2 is 'non-pathogenic', 3 is 'probable non-pathogenic'
        in_conflict = set(['2', '3'])

        for index,sig in zip(self.clnalle, self.clnsig):

            # Get the effect allele. Note that we include the reference
            # as a possible effect allele
            allele = self.alleles[int(index)]

            # Get the number of submitters for this variant
            sig_values = sig.split('|')

            # For each element in the sig set, count the number of occurrences
            submitters = 0
            for sig_value in sigs:
                submitters += sig_values.count(sig_value)

            # Get the set of significance values for this allele
            sig_values = set(sig_values)

            # These are what we consider significant
            good_sigs = set(sigs)

            # First check: that the good_sigs intersects with the set of sigs that I want
            # Always do this filter
            if (len(sig_values.intersection(good_sigs))==0):
                continue

            # Second check, if the number of submitters is at least what I request
            if (submitters < min_submitters):
                continue

            # Final check, if there is NO CONFLICTING INFORMATION for this clinical allele
            if (len(sig_values.intersection(in_conflict)) == 0):
                quality = "NO_CONFLICT"
            else:
                quality = "CONFLICT"

            if (no_conflict) and (quality == "CONFLICT"):
                continue

            self.valid_alleles.append(allele)
            self.valid_sigs.append(sig)
            # Number of submitters for this clinical allele
            self.submitters.append(submitters)
            self.quality.append(quality)

        # If there are any valid alleles with significance values
        if (len(self.valid_alleles)>0):
            return True
        return False

    """
    def Validate(self, sigs, no_conflict, min_submitters, inheritance = None):

        self.valid_alleles = []
        self.valid_sigs = []
        self.submitters = []
        self.quality = []
        self.inheritance = inheritance

        # clnsig == 2 is 'non-pathogenic', 3 is 'probable non-pathogenic'
        in_conflict = set(['2', '3'])

        for index,sig in zip(self.clnalle, self.clnsig):

            # Get the effect allele. Note that we include the reference
            # as a possible effect allele
            allele = self.alleles[int(index)]

            # Get the number of submitters for this variant
            sig_values = sig.split('|')

            # For each element in the sig set, count the number of occurrences
            submitters = 0
            for sig_value in sigs:
                submitters += sig_values.count(sig_value)

            # Get the set of significance values for this allele
            sig_values = set(sig_values)

            # These are what we consider significant
            good_sigs = set(sigs)

            # First check: that the good_sigs intersects with the set of sigs that I want
            # Always do this filter
            if (len(sig_values.intersection(good_sigs))==0):
                continue

            # Second check, if the number of submitters is at least what I request
            if (submitters < min_submitters):
                continue

            # Final check, if there is NO CONFLICTING INFORMATION for this clinical allele
            if (len(sig_values.intersection(in_conflict)) == 0):
                quality = "NO_CONFLICT"
            else:
                quality = "CONFLICT"

            if (no_conflict) and (quality == "CONFLICT"):
                continue

            self.valid_alleles.append(allele)
            self.valid_sigs.append(sig)
            # Number of submitters for this clinical allele
            self.submitters.append(submitters)
            self.quality.append(quality)

        # If there are any valid alleles with significance values
        if (len(self.valid_alleles)>0):
            return True
        return False
    """

    def CheckInheritance(self, variant):

        # If there is no inheritance information, just return True
        if (self.inheritance is None):
            return True

        # If inheritance is dominant, as long as one allele matches, we report it
        elif (self.inheritance == "AD"):
            return True

        # If inheritance is semidominant, I will report it
        elif (self.inheritance == "SD"):
            return True

        # If inheritance is X-linked, I will report it (male/female check?)
        elif (self.inheritance == "XL"):
            return True

        # If inheritance is recessive, I will only report if variant is homozygous
        elif (self.inheritance == "AR"):

            if (variant.zygosity == "HOMOZYGOUS"):
                return True
            else:
                return False

        else:
            raise MyError('Unknown inheritance type: %s'%(self.inheritance))

    def CheckAlleles(self, variant):

        # If they are not the same type, do not return true
        if (self.vc != variant.vc):
            return False;

        # If this is a SNV, we compare the risk alleles
        if (self.vc == "SNV"):

            # Check if any of the alleles in the variant match the valid alleles
            # in this clinvar variant
            if (self.valid_alleles is None):
                raise MyError("This ClinVar variant has not been validated: no valid alleles")

            # Sanity check: make sure the references match. If they do not there might be
            # a strandedness issue (should not happen, but you never know)
            if (self.ref != variant.ref):
                raise MyError('Reference %s != %s'%(self.ref, variant.ref))

            variant_alleles = set(variant.alleles)
            for e in self.valid_alleles:
                if (e in variant_alleles):
                    return True
            return False

        elif (self.vc == "DIV"):

            # All we require here is that the deletion overlap a known deleterious deletion
            return True;

        elif (self.vc == "MNV"):

            # I don't know what to do with these, so I'm going to throw an error and figure it out
            # if I evern find one
            raise MyError('Figure out what to do with MNV variants!');

        # Should not get here
        raise MyError('Unknown variant type');

    def Print(self):
        print self.rsid, self.chr, self.pos, self.ref, self.alt, self.geneinfo, self.genes, self.wgt, self.vc, self.clnalle, self.clnhgvs, self.clnsrc, self.clnsrcid, self.clnsig, self.clndsdb, self.clndsdbid, self.clndbn, self.clnacc, self.caf, self.common, self.quality

    def Write(self, fout):
        #fout.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(self.rsid, self.chr, str(self.pos), self.ref, ','.join(self.alt), self.geneinfo, ','.join(self.genes), str(self.wgt), str(self.vc), ','.join(self.clnalle), ','.join(self.clnhgvs), ','.join(self.clnsrc), ','.join(self.clnsrcid), ','.join(self.clnsig), ','.join(self.clndsdb), ','.join(self.clndsdbid), ','.join(self.clndbn), ','.join(self.clnacc), self.caf, str(self.common), ','.join(self.valid_alleles), ','.join(self.valid_sigs), ','.join(self.submitters), ','.join(self.quality)))
        fout.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(self.rsid, self.chr, str(self.pos), self.ref, ','.join(self.alt), self.geneinfo, ','.join(self.genes), str(self.wgt), str(self.vc), ','.join(self.clnalle), ','.join(self.clnhgvs), ','.join(self.clnsrc), ','.join(self.clnsrcid), ','.join(self.clnsig), ','.join(self.clndsdb), ','.join(self.clndsdbid), ','.join(self.clndbn), ','.join(self.clnacc), self.caf, str(self.common), ','.join(self.valid_alleles), ','.join(self.valid_sigs), ','.join([str(x) for x in self.submitters]), ','.join(self.quality)))

class ACMGDisorder(object):

    def __init__(self, symbol, name, inheritance, report, omim_disorder, omim_gene):
        self.symbol = symbol
        self.name = name
        self.inheritance = inheritance
        self.report = set(report.split(','))
        self.omim_disorder = omim_disorder
        self.omim_gene = omim_gene

    def Print(self):
        print self.symbol, self.name, self.inheritance, self.report, self.omim_disorder, self.omim_gene

class Clinvar(object):

    def __init__(self, database):
        self.database = database
        self.acmg = []
        self.acmg_variants = None
        self.LoadACMGDisorders()

    def LoadACMGDisorders(self):

        cursor = self.database.GetAll('acmg')
        for (entry, symbol, name, inheritance, report, mim_disorder, mim_gene) in cursor:
            self.acmg.append(ACMGDisorder(symbol, name, inheritance, report, mim_disorder, mim_gene))

    def LoadACMGVariants(self, no_conflict, min_submitters):

        print "Loading ACMG variants from database"
        self.acmg_variants = {}
        for disorder in self.acmg:
            self.acmg_variants[disorder] = self.GetACMGVariants(disorder, no_conflict, min_submitters)

    def LoadClinvarVariants(self, no_conflict=True, min_submitters=1):

        self.acmg_variants = {}
        results = []
        sig_values = set(["KP", "EP"])

        # Convert significance to ClinVar numbers
        sigs = []
        for sig in sig_values:
            if (sig == "KP"):
                sigs.append('5')
            elif (sig == "EP"):
                sigs.append('4')

        # Construct a query for this disorder
        command = "SELECT * FROM clinvar WHERE (NOT clnsig LIKE '%255%') AND ("
        command += "clnsig LIKE '%" + sigs[0] + "%'"
        for sig in sigs[1:]:
            command += " OR clnsig LIKE '%" + sig + "%'"
        command += ")"

        result = self.database.Command(command)

        for (rsid, chr, pos, ref, alt, geneinfo, wgt, vc, clnalle, clnhgvs, clnsrc, clnsrcid, clnsig, clndsdb, clndsdbid, clndbn, clnrevstat, clnacc, caf, common) in result:

            try:

                # Create the clinvar object
                var = ClinvarEntry(rsid, chr, pos, ref, alt, geneinfo, wgt, vc, clnalle, clnhgvs, clnsrc, clnsrcid, clnsig, clndsdb, clndsdbid, clndbn, clnrevstat, clnacc, caf, common)

                # Validate the result
                if (not var.Validate(sigs, no_conflict, min_submitters)):
                    continue

                # If it validates, keep it
                results.append(var)

            except:
                print rsid, geneinfo

        print "Loaded %d variants"%(len(results))
        self.acmg_variants['clinvar'] = results

    def CountACMGVariants(self):

        for disorder in self.acmg:
            result = self.GetACMGVariants(disorder)
            print "%s|%s|%d"%(disorder.symbol, disorder.name, len(result))

    def QueryACMGWithVCF(self, fout, vcf, suppress_errors):

        if (vcf is None):
            return

        if (self.acmg_variants is None):
            raise MyError("ACMG variants are not loaded. Call LoadACMGVariants before performing a query")

        count = 0
        for disorder in self.acmg_variants.keys():

            #if (disorder.name != "Marfan's syndrome"):
            #    continue

            #print "Processing ACMG disorder: %s"%(disorder.name)

            result = self.acmg_variants[disorder]

            for variant in result:
                records = vcf.Query(variant.rsid, suppress_errors)

                for record in records:

                    # Perform the allele comparison and inheritance comparison
                    if (variant.CheckAlleles(record) and variant.CheckInheritance(record)):
                        fout.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t"%(vcf.username, record.chr, record.pos, record.ref, record.alt, record.zygosity, record.vc, record.quality, record.genotype, '/'.join(record.alleles)))
                        variant.Write(fout)
                        fout.write('\n')

            if (count == 1):
                break;

    def GetPharmacogeneticVariants(self):

        # Construct a query for this disorder
        command = "SELECT * FROM clinvar WHERE (clnsig LIKE '%6%')";
        results = self.database.Command(command)
        for element in results:
            print element

    def GetACMGVariants(self, disorder, no_conflict=True, min_submitters=1):

        results = []

        # Convert significance to ClinVar numbers
        sigs = []
        for sig in disorder.report:
            if (sig == "KP"):
                sigs.append('5')
            elif (sig == "EP"):
                sigs.append('4')

        # Construct a query for this disorder
        command = "SELECT rsid FROM clinvar WHERE (geneinfo LIKE '%" + disorder.symbol + "%') AND (NOT clnsig LIKE '%255%') AND ("
        command += "clnsig LIKE '%" + sigs[0] + "%'"
        for sig in sigs[1:]:
            command += " OR clnsig LIKE '%" + sig + "%'"
        command += ")"

        result = self.database.Command(command)

        for (rsid) in result:

            # Get the result
            result = self.Get(rsid)

            # Verify that if OMIM is in the clndsdb column, the OMIM ID is in the clndsdbid column
            if (not result.CheckOMIM(str(disorder.omim_disorder))):
                continue

            # Verify that this variant does not have conflicting information for the effect allele
            if (not result.Validate(sigs, no_conflict, min_submitters, disorder.inheritance)):
                continue

            results.append(result)

        return results

    def Get(self, rsid):

        # Retrieve from database
        cursor = self.database.Get('clinvar', 'rsid', rsid)

        results = []
        for (rsid, chr, pos, ref, alt, geneinfo, wgt, vc, clnalle, clnhgvs, clnsrc, clnsrcid, clnsig, clndsdb, clndsdbid, clndbn, clnrevstat, clnacc, caf, common) in cursor:
            results.append(ClinvarEntry(rsid, chr, pos, ref, alt, geneinfo, wgt, vc, clnalle, clnhgvs, clnsrc, clnsrcid, clnsig, clndsdb, clndsdbid, clndbn, clnrevstat, clnacc, caf, common))

        cursor.close()

        # Check the results before we return them
        if (len(results)==0):
            return None
        if (len(results)>1):
            raise MyError('MySQL database query returned %d results for %s'%(len(results), rsid))
        return results[0]

    def LoadVCF(self):

        print "Disabled this function"
        return

        #filename = '/local/gestalt/public/ReferenceGenome/hg19/annot/clinvar_00-latest.vcf.gz'
        filename = 'db/clinvar-latest.vcf.gz'

        start_time = time.time()

        cursor = self.database.GetCursor();

        # Create the table
        command = ""
        command += "CREATE TABLE clinvar (rsid VARCHAR(16) PRIMARY KEY, chr VARCHAR(16) NOT NULL, pos INT(10) NOT NULL, ref VARCHAR(256) NOT NULL, alt VARCHAR(256) NOT NULL, "
        command += "geneinfo VARCHAR(512), wgt INT(10), vc VARCHAR(16), clnalle VARCHAR(16), clnhgvs VARCHAR(256), clnsrc VARCHAR(256),  "
        command += "clnsrcid VARCHAR(512), clnsig VARCHAR(256), clndsdb VARCHAR(512), clndsdbid VARCHAR(512), clndbn VARCHAR(512), clnrevstat VARCHAR(512), clnacc VARCHAR(256), "
        command += "caf VARCHAR(256), common INT(1))"

        count = 0
        cursor.execute(command);

        count = 0
        with gzip.open(filename) as f:
            for line in f:

                if (line[0] == '#'):
                    continue

                tokens = line.split('\t')
                chr = tokens[0].strip()
                pos = tokens[1].strip()
                rsid = tokens[2].strip()
                ref = tokens[3].strip()
                alt = tokens[4].strip()

                geneinfo = None
                wgt = None
                vc = None
                clnalle = None
                clnhgvs = None
                clnsrc = None
                clnsrcid = None
                clnsig = None
                clndsdb = None;
                clndsdbid = None
                clndbn = None
                clnrevstat = None
                clnacc = None
                caf = None;
                common = 0

                # Get the rest
                for token in tokens[7].split(';'):

                    temp = token.split('=');
                    if (len(temp)==1):
                        continue;
                    if (len(temp)>2):
                        raise MyError("%d tokens in VCF file"%(len(temp)))

                    key = temp[0].strip();
                    value = temp[1].strip();

                    if (key == "GENEINFO"):
                        geneinfo = value
                    elif (key == "WGT"):
                        wgt = value
                    elif (key == "VC"):
                        vc = value
                    elif (key == "CLNALLE"):
                        clnalle = value
                    elif (key == "CLNHGVS"):
                        clnhgvs = value
                    elif (key == "CLNSRC"):
                        clnsrc = value
                    elif (key == "CLNSRCID"):
                        clnsrcid = value
                    elif (key == "CLNSIG"):
                        clnsig = value
                    elif (key == "CLNDSDB"):
                        clndsdb = value
                    elif (key == "CLNDSDBID"):
                        clndsdbid = value
                    elif (key == "CLNDBN"):
                        clndbn = value
                    elif (key == "CLNREVSTAT"):
                        clnrevstat = value
                    elif (key == "CLNACC"):
                        clnacc = value
                    elif (key == "CAF"):
                        caf = value
                    elif (key == "COMMON"):
                        common = value

                # Build the command
                cursor.execute("INSERT INTO clinvar (rsid, chr, pos, ref, alt, geneinfo, wgt, vc, clnalle, clnhgvs, clnsrc, clnsrcid, clnsig, clndsdb, clndsdbid, clndbn, clnrevstat, clnacc, caf, common) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               (rsid, chr, pos, ref, alt, geneinfo, wgt, vc, clnalle, clnhgvs, clnsrc, clnsrcid, clnsig, clndsdb, clndsdbid, clndbn, clnrevstat, clnacc, caf, common))

                count += 1
                if (count % 10000 == 0):
                    self.database.Commit();
                    cursor = self.database.GetCursor()
                    elapsed_time = time.time() - start_time
                    print "Completed %d elements (%.3f s)" % (count, elapsed_time)
                    sys.stdout.flush()

        # Commit the final lines
        self.database.Commit()
        elapsed_time = time.time() - start_time
        print "FINISHED %d elements (%.3f s)" % (count, elapsed_time)