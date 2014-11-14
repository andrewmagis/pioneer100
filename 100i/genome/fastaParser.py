# System code
import sys, os, math, re, gzip


class FastaIndex:
    def __init__(self, line):
        tokens = line.split('\t');
        if (len(tokens) != 5):
            raise InputError(line);

        self.chr = tokens[0].strip();
        self.length = int(tokens[1].strip());
        self.start = int(tokens[2].strip());
        self.seqlen = int(tokens[3].strip());
        self.linelen = int(tokens[4].strip());


class FastaParser:
    def __init__(self):
        self.fin = None;
        self.chr = None;
        self.header = None;
        self.chromosome = None;
        self.genome_length = 0;

        self.index = {};
        self.indexlist = list();

    def Load(self, filename):

        # Open the input file1
        try:
            self.fin = open(filename, "r")
        except IOError as e:
            print("({})".format(e))
            sys.exit(1);

        # Also load index file
        self.LoadIndex(filename);

    def LoadIndex(self, filename):

        # Open the index file
        index_filename = filename + ".fai";
        try:
            fin = open(index_filename, "r");
        except IOError as e:
            print("({})".format(e))
            sys.exit(1);

        print "Loading file '%s'" % (index_filename);
        line = fin.readline();
        while line:
            try:

                current = FastaIndex(line);
                self.index[current.chr] = current;
                self.indexlist.append(current);
                self.genome_length = self.genome_length + current.length;

            except InputError as e:
                print("Invalid line: %s" % (e.value));
            line = fin.readline();

    def GetPosition(self, pos):

        # Make sure this position is within the bounds of the genome length
        if (pos < 1) or (pos > self.genome_length):
            raise InputError("Pos %d exceeds bound of genome length (%d)" % (pos, self.genome_length));

        # Get the chromosome element at this position
        current = None;
        chr = None;
        current_place = 0;
        for e in self.indexlist:
            chr = e.chr;
            # print "pos %d current: %s start: %d end: %d"%(pos, e.chr, current_place, current_place+e.length);
            if (pos > current_place) and (pos <= (current_place + e.length)):
                break;
            current_place = current_place + e.length;

        # Now convert this position into a relative chromosome position
        chr_pos = (pos - current_place);
        return (chr, chr_pos);

    def Query(self, chr, start, end, strand):

        reverse = False;
        if (strand == '-'):
            reverse = True;

        # First get the element from the index
        if (not chr in self.index):
            print("Index %s not found in FASTA index file, returning empty string" % (chr));
            return "";
        current = self.index[chr];

        if (start > end):
            raise InputError("Query [%d %d] is invalid query (start > end)" % (start, end));

            # Check to make sure we are not going off the end of the chromosome
        if (start > current.length):
            # raise InputError("Query [%d %d] exceeds bounds of chromosome %s (length: %d)"%(start, end, chr, current.length));
            print "Warning: Query [%d %d] exceeds bounds of chromosome %s (length: %d)" % (
            start, end, chr, current.length);
            start = current.length;

        # Check to make sure we are not going off the end of the chromosome
        if (end > current.length):
            # raise InputError("Query [%d %d] exceeds bounds of chromosome %s (length: %d)"%(start, end, chr, current.length));
            print "Warning: Query [%d %d] exceeds bounds of chromosome %s (length: %d)" % (
            start, end, chr, current.length);
            end = current.length;

        # Check to make sure we are not going off the end of the chromosome
        if (start < 1):
            # raise InputError("Query [%d %d] exceeds bounds of chromosome %s (length: %d)"%(start, end, chr, current.length));
            print "Warning: Query [%d %d] exceeds bounds of chromosome %s (length: %d)" % (
            start, end, chr, current.length);
            start = 1;

        # Check to make sure we are not going off the end of the chromosome
        if (end < 1):
            # raise InputError("Query [%d %d] exceeds bounds of chromosome %s (length: %d)"%(start, end, chr, current.length));
            print "Warning: Query [%d %d] exceeds bounds of chromosome %s (length: %d)" % (
            start, end, chr, current.length);
            end = 1;

        # Get the position of the first line in the start sequence.  This is important to accurately
        # calculate the number of newline characters we are going to read.  zero-centered
        start_linepos = (start - 1) % current.seqlen;

        # Get the number of newline characters between the start and end position
        num_newlines = int(math.floor(float(((end - 1) - ((start - 1) - start_linepos))) / float(current.seqlen)));

        # Seek to the correct start position in the file
        num_lines = int(math.floor(float(start - 1) / float(current.seqlen)));
        seek_start = num_lines * current.linelen + (start - 1) - num_lines * current.seqlen;
        self.fin.seek(current.start + seek_start, os.SEEK_SET);

        # Read the correct number of characters, and strip out newlines
        seq = self.fin.read((end - start) + num_newlines + 1);
        newseq = re.sub(r'\s', '', seq)

        # print "Query: %s %d-%d %s"%(chr, start, end, newseq);

        if (reverse):
            return self.Reverse(newseq);
        else:
            return newseq;

    def Reverse(self, seq):

        # If we want reverse complement
        seq_list = list();
        seqrev = seq[::-1];
        for c in seqrev:
            cu = c.upper();
            if (cu == 'A'):
                seq_list.append('T');
            elif (cu == 'T'):
                seq_list.append('A');
            elif (cu == 'C'):
                seq_list.append('G');
            elif (cu == 'G'):
                seq_list.append('C');
            elif (cu == 'N'):
                seq_list.append('N');
            elif (cu == '-'):
                seq_list.append('-');
            else:
                print ("WARNING: Unknown base character: '%s'.  Replacing with 'N'" % (cu));
                seq_list.append('N');

        return ''.join(seq_list);

    def ReadFasta(self, filename):

        headers = [];
        seqs = [];

        # Write out to file, one sample per column
        try:
            fin = open(filename, "r");
        except IOError as e:
            print("({})".format(e))
            sys.exit(1);

        current = '';

        try:
            line = fin.readline();
            while (line):

                if ( (line.startswith('#')) or (len(line.strip()) == 0) ):
                    line = fin.readline();
                    continue;

                elif (line.startswith('>')):
                    if (len(headers) > 0):
                        seqs.append(current.strip());
                        current = '';
                    headers.append(line.strip().strip('>'));
                else:
                    current = current + line.strip();
                line = fin.readline();

        except InputError as e:
            print("Invalid line: %s" % (e.value));
        fin.close();

        # At the end, add the final sequence
        if (len(current) > 0):
            seqs.append(current);

        if (len(headers) != len(seqs)):
            print "Warning: number of headers (%d) is not equal to number of sequences (%d)" % (
            len(headers), len(seqs));
        print "Loaded file '%s' (%d sequences)" % (filename, len(headers));
        return (headers, seqs);

    def WriteFasta(self, filename, headers, seqs):

        # Write out to file, one sample per column
        try:
            fout = open(filename, "w");
        except IOError as e:
            print("({})".format(e))
            sys.exit(1);

        for e, f in zip(headers, seqs):
            fout.write(">%s\n%s\n" % (e, f));
        fout.close();


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg

    def Print(self):
        print self.msg;
			
