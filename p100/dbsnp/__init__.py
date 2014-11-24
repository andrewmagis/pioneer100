"""
    __init__.py "

    Author: Andrew Magis
    Date: July 29th, 2014

"""

import gzip, sys, time
from p100.errors import MyError

class DBSnpEntry(object):

    def __init__(self, rsid, chr, pos, ref, alt, caf, vc, common):
        self.rsid = rsid
        self.chr = chr
        self.pos = pos
        self.ref = ref
        self.alt = alt.split(',')

        self.caf = caf
        temp = []
        if not self.caf is None:
            for x in caf.split(','):
                try:
                    temp.append(float(x))
                except:
                    temp.append(None)
            self.caf = temp

        self.vc = vc
        self.common = common

    def GetMinorAllele(self):

        # Prepend the ref to the list of alleles
        alleles = self.alt
        alleles.insert(0, self.ref);

        minor_allele = None
        maf = float("inf")

        if (not self.caf is None):
            for allele,freq in zip(alleles, self.caf):
                if (not freq is None) and (freq < maf):
                    minor_allele = allele;
                    maf = freq

        return minor_allele

    def Print(self):
        print self.chr, self.pos, self.rsid, self.ref, self.alt, self.caf, self.vc, self.common

class DBSnpVCF(object):

    def __init__(self, line):

        tokens = line.strip().split('\t')
        self.chr = tokens[0].strip()
        self.pos = tokens[1].strip()
        self.rsid = tokens[2].strip()
        self.ref = tokens[3].strip()
        self.alt = tokens[4].strip()

        self.caf = None
        self.vc = None
        self.common = None

        # Get the specific attributes
        for token in tokens[7].split(';'):
            temp = token.split('=');
            if (len(temp)>1):
                key = temp[0];
                value = temp[1];
            else:
                continue

            if (key == "CAF"):
                self.caf = value.strip('[').strip(']')
            elif (key == "VC"):
                self.vc = value
            elif (key == "COMMON"):
                self.common = value

    def Print(self):
        print self.rsid, self.chr, self.pos, self.ref, self.alt, self.caf, self.vc, self.common

class DBSnp(object):

    def __init__(self, database):

        self.database = database
        self.filename = './db/snp141_GRCh37p13.vcf.gz'

    def Get(self, rsid, assembly):

        if (assembly == "GRCh37"):

            # Retrieve from database
            cursor = self.database.Get('dbsnp', 'rsid', rsid)

            results = []
            for result in cursor:
                results.append(DBSnpEntry(*result))

            cursor.close()

            # Check the results before we return them
            if (len(results)==0):
                return None
            if (len(results)>1):
                raise MyError('MySQL database query returned %d results for %s'%(len(results), rsid))
            return results[0]

        # To be added to the database and implemented
        elif (assembly == "GRCh38"):
            raise MyError("GRCh38 is not loaded - to be implemented")

        # To be implemented
        else:
            raise MyError('Unknown DBSnp assembly %s'%(assembly))

    def Update(self):

        print "Disabled this function"
        return

        start_time = time.time()
        cursor = self.database.GetCursor()

        # Go through each line in the file
        count = 0
        with gzip.open(self.filename) as f:
            for line in f:

                if (line[0] == '#'):
                    continue

                vcf = DBSnpVCF(line)

                # Now update the database
                if (not vcf.caf is None):
                    command = "UPDATE dbsnp SET %s = '%s' WHERE rsid = '%s'"%('caf', vcf.caf, vcf.rsid)
                    cursor.execute(command);

                count += 1
                if (count % 10000 == 0):
                    self.database.Commit();
                    cursor = self.database.GetCursor()
                    elapsed_time = time.time() - start_time
                    print "Completed %d elements (%.3f s)" % (count, elapsed_time)
                    sys.stdout.flush()

        # At the end we commit the final bit
        self.database.Commit()
        elapsed_time = time.time() - start_time
        print "FINISHED %d elements (%.3f s)" % (count, elapsed_time)

    def LoadVCF(self):

        print "Disabled this function"
        return

        # Open MySQL connection
        db = MySQLdb.connect(host=HOSTNAME, user=USERNAME, passwd=PASSWORD, db=DB)

        cursor = db.cursor()

        start_time = time.time()

        count = 0
        with gzip.open(self.dbsnp_vcf_filename) as f:
            for line in f:

                if (line[0] == '#'):
                    continue

                tokens = line.split('\t')
                chr = tokens[0].strip()
                pos = tokens[1].strip()
                rsid = tokens[2].strip()
                ref = tokens[3].strip()
                alt = tokens[4].strip()

                cursor.execute("INSERT INTO dbsnp (rsid, chr, pos, ref, alt) VALUES (%s, %s, %s, %s, %s)",
                               (rsid, chr, pos, ref, alt))

                count += 1
                if (count % 10000 == 0):
                    db.commit()
                    cursor = db.cursor()
                    elapsed_time = time.time() - start_time
                    print "Completed %d elements (%.3f s)" % (count, elapsed_time)
                    sys.stdout.flush()

        # Commit the final lines
        db.commit()
        db.close()
        elapsed_time = time.time() - start_time
        print "FINISHED %d elements (%.3f s)" % (count, elapsed_time)
