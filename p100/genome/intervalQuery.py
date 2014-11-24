# System code
import sys, math

# 3rd party code
from quicksect import Feature, IntervalTree;


class IntervalObject:
    def __init__(self, _start, _end, _chr, _strand, _object):
        self.start = _start;
        self.end = _end;
        self.chr = _chr;
        self.strand = _strand;
        self.object = _object;

    def Print(self):
        self.object.Print();

        # print "%s [%d - %d] %s %s"%(self.chr, self.start, self.end, self.strand, type(self.object));


class IntervalQuery:
    # Constructor to define class variables
    def __init__(self):
        self.tree = IntervalTree();

    def Add(self, chr, start, end, strand, object):

        # Create a new object
        # object = IntervalObject(start, end, chr, strand, object);
        object = (start, end, chr, strand, object);

        # Add the object to the tree
        self.tree.insert(Feature(start, end, info={"object": object}));

    def Query(self, chr, start, end, strand='.'):

        # Query the tree for overlaps
        overlaps = self.tree.find(Feature(start, end));
        results = [];

        if (overlaps == None):
            return results;

        # For each overlap
        for o in overlaps:

            # Get the IntervalObject
            (object_start, object_end, object_chr, object_strand, object_object) = o.info["object"];

            # Make sure the chromosome matches
            if (chr != object_chr):
                continue;

            # Make sure the strand matches (if '.' we don't care)
            if (strand == ".") or (object_strand == '.'):
                results.append(object_object);
            else:
                if (strand == object_strand):
                    results.append(object_object);

        return results;
	
	
