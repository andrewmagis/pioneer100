"""
    __init__.py "

    Author: Andrew Magis
    Date: July 29th, 2014

"""

import gzip

from intervalQuery import IntervalQuery
from fastaParser import FastaParser
from errors import MyError

class Gene:
    def __init__(self, line):
        tokens = line.split('\t')
        self.chr = tokens[0]
        self.source = tokens[1]
        self.feature = tokens[2]
        self.start = int(tokens[3])
        self.end = int(tokens[4])
        self.strand = tokens[6]
        self.line = line;
        self.attributes = {}

        # Get attributes
        tokens = tokens[8].split(';')
        for token in tokens:
            temp = token.strip().split(' ')
            if (len(temp)==2):
                key = temp[0].strip().strip('"')
                value = temp[1].strip().strip('"')
                self.attributes[key] = value

class Genome(object):
    def __init__(self):

        # GRCh37 files
        self.GRCh37_fasta_filename = './db/Homo_sapiens.GRCh37.68.genome.fa'
        self.GRCh37_gene_filename = './db/Homo_sapiens.GRCh37.75.gene.gtf.gz'
        self.GRCh37_gtf_filename = './db/Homo_sapiens.GRCh37.75.gtf.gz'

        self.GRCh38_fasta_filename = './db/Homo_sapiens.GRCh38.76.genome.fa'
        self.GRCh38_gene_filename = './db/Homo_sapiens.GRCh38.76.gene.gtf.gz'
        self.GRCh38_gtf_filename = './db/Homo_sapiens.GRCh38.76.gtf.gz'

        # Data structures for the GRCh37 assembly
        self.GRCh37_gene = None
        self.GRCh37_fasta = None
        self.GRCh37_gtf = None

        # Data structures for the GRCh38 assembly
        self.GRCh38_gene = None
        self.GRCh38_fasta = None
        self.GRCh38_gtf = None

        # 'Current' assembly
        self.gene = None
        self.fasta = None
        self.gtf = None

    def Load(self):
        self.LoadGRCh37()
        self.LoadGRCh38()

    def SetAssembly(self, assembly):

        if (assembly == "GRCh37"):
            self.gene = self.GRCh37_gene
            self.fasta = self.GRCh37_fasta
            self.gtf = self.GRCh37_gtf

        elif (assembly == "GRCh38"):
            self.gene = self.GRCh38_gene
            self.fasta = self.GRCh38_fasta
            self.gtf = self.GRCh38_gtf
        else:
            raise MyError('Unknown assembly: %s' % (assembly))

    def LoadGRCh37(self):

        # Load the data for GRCh37 queries
        self.GRCh37_fasta = FastaParser()
        self.GRCh37_fasta.Load(self.GRCh37_fasta_filename)

        # Load refseq gene models
        self.GRCh37_gene = IntervalQuery()
        with gzip.open(self.GRCh37_gene_filename) as f:

            for line in f:

                # Skip over commented lines
                if (line[0] == '#'):
                    continue

                # Load the line
                current = Gene(line)

                # Add to interval tree
                self.GRCh37_gene.Add(current.chr.strip('chr'), current.start, current.end, current.strand, current)

                # Not loading full GTF because no need at this time

    def LoadGRCh38(self):

        # Load the data for GRCh38 queries
        self.GRCh38_fasta = FastaParser()
        self.GRCh38_fasta.Load(self.GRCh38_fasta_filename)

        # Load refseq gene models
        self.GRCh38_gene = IntervalQuery()
        with gzip.open(self.GRCh38_gene_filename) as f:

            for line in f:

                # Skip over commented lines
                if (line[0] == '#'):
                    continue

                # Load the line
                current = Gene(line)

                # Add to interval tree
                self.GRCh38_gene.Add(current.chr.strip('chr'), current.start, current.end, current.strand, current)

    def Sequence(self, chr, start, end, strand='+'):

        if (self.fasta is None):
            raise MyError('Assembly not set. Please set before querying sequence')

        # Strip 'chr' from the chromosome if it is present
        return self.fasta.Query(chr.strip('chr'), start, end, strand)

    def Gene(self, chr, start, end):

        if (self.gene is None):
            raise MyError('Assembly not set. Please set before querying gene')

        # Query the tree for this position
        return self.gene.Query(chr.strip('chr'), start, end)

    def Strand(self, chr, pos):

        if (self.gene is None):
            raise MyError('Assembly not set. Please set before querying strand')

        # Query the tree for this position
        results = self.gene.Query(chr.strip('chr'), pos, pos)

        # If there are no genes, return nothing
        # TODO: look some distance upstream and downstream?
        if (len(results) == 0):
            return '.'

        # If there is a single result, return that 
        elif (len(results) == 1):
            return results[0].strand

        # If there are multiple results
        else:

            strands = set()
            for result in results:
                if (result.source == "protein_coding"):
                    strands.add(result.strand)

            # If all strands agree, return that
            if (len(strands) == 1):
                return strands.pop()

            # If strands do not agree, return unknown.
            # TODO: make this smarter!
            else:
                return '.'