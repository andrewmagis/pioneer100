"""
    __init__.py

    VCF Parser

    Author: Andrew Magis
    Date: October 16th, 2014

"""

# Exceptions
from p100.errors import MyError
from p100.utils.botoops import BotoOps

import tabix
import gzip, os, sys

class VCFObject(object):

    def __init__(self, tokens):

        self.good = True

        # Do a quality check on this set of tokens
        self.chr = tokens[0].strip('chr')
        self.start = tokens[1].strip()
        self.pos = self.start
        self.end = tokens[2].strip()
        self.ref = tokens[3].strip()
        self.alt = tokens[4].strip().split(',')
        self.score = tokens[5].strip()

        try:
            test = float(self.score)
        except:
            self.score = -1.0

        self.quality = tokens[6].strip()
        self.info = tokens[7].strip()
        self.flags = tokens[8].strip()
        self.genotype = tokens[9].strip()
        self.zygosity = None

        # Calculate zygosity
        temp = self.genotype.split(':')
        genotype = temp[0].split('/')
        if (len(genotype) == 1):
            genotype = genotype[0].split('|')
        if (len(genotype) == 1):

            # This is ok if we are on the X or Y chromosome
            if (self.chr == 'X'):
                pass
            elif (self.chr == 'Y'):
                pass
            elif (self.chr == 'M'):
                pass
            else:
                #print "Warning, irregular genotype %s"%(temp)
                self.good = False
                return

        self.alleles = set([])
        for e in genotype:
            # Reference allele
            if (e == '0'):
                self.alleles.add(self.ref)
            # Alternate allele
            elif (e == '1'):
                self.alleles.add(self.alt[0])
            elif (e == '2'):
                self.alleles.add(self.alt[1])
            # Nocall
            elif (e == '.'):
                self.alleles.add('?')
            else:
                print "[%s %s] Warning, unknown genotype %s" % (self.chr, self.pos, genotype)

        # Check to see if the genotype is completely undefined

        if (len(self.alleles)==1):
            self.zygosity = "HOMOZYGOUS"

            # CGI data has lots of lines with no alleles. Do not upload to database
            if (list(self.alleles)[0] == '?'):
                self.good = False
                return

        elif (len(self.alleles)==2):
            self.zygosity = "HETEROZYGOUS"
        else:
            self.zygosity = "HETEROZYGOUS_MULTIPLE"

        # Get quality score
        if (len(temp)<3):
            self.quality = "NOCALL";
        elif (self.quality == '.'):
            self.quality = temp[2].strip();

        # Get the length of the alternate allles.
        self.length = None
        for e in self.alt:
            if self.length is None:
                self.length = len(e);
            else:
                # Take the longer of the two
                if (len(e)>self.length):
                    self.length = len(e);

        # Now calculate the type
        self.vc = None
        if len(self.ref) > self.length:
            self.vc = "DIV"
        elif len(self.ref) < self.length:
            self.vc = "DIV"
        elif (self.length == 1):
            self.vc = "SNV"
        else:
            self.vc = "MNV"

        # Truncate genotype field if it gets too long
        if (len(self.genotype)>65535):
            self.genotype = self.genotype[0:65535]
        if (len(self.info)>65535):
            self.info = self.info[0:65535]
        if (len(self.flags)>65535):
            self.flags = self.flags[0:65535]

    def Print(self):
        print self.chr, self.start, self.end, self.ref, self.alt, self.vc, self.quality, self.genotype, self.alleles, self.zygosity

    def WriteUsername(self, fout, username):
        fout.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(username, self.chr, self.start, self.end,
                    self.ref, ','.join(self.alt), self.score, self.quality, self.info, self.flags, self.genotype, self.vc,
                    ','.join(self.alleles), self.zygosity))

    def Compare(self, clinvar):

        # If they are not the same type, do not return true
        if (self.vc != clinvar.vc):
            return False;

        # If this is a SNV, we compare the risk alleles
        if (self.vc == "SNV"):

            # Loop over the clinical alleles
            for allele_index, sig in zip(clinvar.clnalle, clinvar.clnsig):

                # Get the current clinical allele
                allele = clinvar.alt[int(allele_index)-1]

                # Split the clnsig by '|', because there may be multiple submitters
                sigs = set(sig.split('|'));

                # Now compare the current variant alleles to the clinical allele
                for myallele in self.alt:
                    if (myallele == allele):
                        return True;

            print "RETURNING FALSE", self.dbsnp, self.alt, self.vc, clinvar.alt, clinvar.clnalle, clinvar.clnsig
            return False;

        elif (self.vc == "DIV"):

            # All we require here is that the deletion overlap a known deleterious deletion
            return True;

        elif (self.vc == "MNV"):

            # I don't know what to do with these, so I'm going to throw an error and figure it out
            # if I evern find one
            raise MyError('Figure out what to do with MNV variants!');

        # Should not get here
        raise MyError('Unknown variant type');

class VCF(object):

    def __init__(self, username, filename, assembly, dbsnp):

        self.username = username
        self.filename = filename
        self.assembly = assembly
        self.dbsnp = dbsnp
        #self.tb = tabix.open(filename)

    def Query(self, rsid, suppress_errors=False):

        # Query dbSNP with the rsid to get the appropriate coordinates for my assembly
        dbsnp_entry = self.dbsnp.Get(rsid, self.assembly)

        vcfs = []

        if (dbsnp_entry is None):
            print "[%s] not found in dbsnp database"%(rsid)
            return vcfs

        # Perform a tabix query on the VCF file
        records = self.tb.query(dbsnp_entry.chr, int(dbsnp_entry.pos)-1, int(dbsnp_entry.pos)+1)

        # For each record, create a VCFObject
        for record in records:

            # Create the VCFObject
            vcf = VCFObject(record)

            if (vcf.chr != dbsnp_entry.chr):
                raise MyError('Bad chromosome in search: %s'%(vcf.chr))

            if (int(vcf.pos) != int(dbsnp_entry.pos)):
                continue

            # Filter for a pass quality
            # TODO: Allow for VLQ variants as well (if the user requests)
            if (vcf.quality == "PASS"):
                vcfs.append(vcf)

        # Return the set of discovered variants
        return vcfs

    def ReformatVCF(self):

        # Download the data to the ephemeral workspace
        filename = BotoOps().copy_s3_to_ephemeral(self.filename, '100i-wgs-data')
        fout = gzip.open('/scratch/processed.gz', 'w')

        # Process the file
        count = 0
        with gzip.open(filename, 'Ur') as f:
            for line in f:

                if (line.startswith('#')):
                    continue

                v = VCFObject(line.strip().split('\t'))

                if (v.good):
                    v.WriteUsername(fout, self.username)

                count += 1
                if (count % 100000 == 0):
                    print "Processed %d lines"%(count)
                    sys.stdout.flush()

        fout.close()

        # Upload the process file to S3
        path = os.path.dirname(self.filename)
        BotoOps().copy_ephemeral_to_s3('processed.gz', '100i-wgs-data', path)

        # Now delete the files
        os.remove(filename)
        os.remove('/scratch/processed.gz')

