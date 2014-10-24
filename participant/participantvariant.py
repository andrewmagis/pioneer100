class ParticipantVariant():

    def __init__(self, line):

        tokens = line.split('\t')
        self.chr = tokens[0].strip('chr')
        self.start = tokens[1].strip()
        self.end = tokens[2].strip()
        self.dbsnp = tokens[3].strip()
        self.ref = tokens[4].strip()
        self.alt = tokens[5].strip().split(',')
        self.info = tokens[8].strip()
        self.flags = tokens[9].strip()
        self.genotype = tokens[10].strip()
        self.key = self.dbsnp + '_' + ','.join(self.alt)

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
                print "%s Warning, irregular genotype %s" % (self.dbsnp, temp)

        self.alleles = set()
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
                print "%s Warning, unknown genotype %s" % (self.dbsnp, genotype)

        # Get quality score
        if (len(temp)<3):
            self.quality = "NOCALL";
        else:
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

    def Print(self):
        print self.chr, self.start, self.end, self.dbsnp, self.ref, self.alt, self.vc, self.quality, self.genotype, self.alleles

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
                    if (myallele == allele) and (('5' in sigs) or ('4' in sigs)):
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

