from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib import colors
from reportlab.platypus import PageBreak, Flowable
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Image as Image2
from reportlab.graphics.shapes import *

PAGE_HEIGHT=defaultPageSize[1]
PAGE_WIDTH=defaultPageSize[0]
styles = getSampleStyleSheet()

from theme import DefaultTheme
from util import calc_table_col_widths
from common import *
import numpy as np

from operator import attrgetter

class MyTheme(DefaultTheme):
    doc = {
        'leftMargin': 25,
        'rightMargin': 25,
        'topMargin': 20,
        'bottomMargin': 0,
        'allowSplitting': False
        }

centered = PS(name = 'centered',
    fontSize = 30,
    leading = 16,
    alignment = 1,
    spaceAfter = 20)

h1 = PS(
    name = 'Heading1',
    fontSize = 14,
    leading = 16)


h2 = PS(name = 'Heading2',
    fontFace = 'Helvetica',
    fontSize = 10,
    leading = 14)

h4 = PS(name = 'Heading4',
    fontFace = 'Helvetica',
    fontColor = '#00467E',
    fontSize = 15,
    leading = 14)

h0 = PS(
     name = 'Heading3',
    fontFace = 'Helvetica-Bold',
    fontSize = 22,
    leading = 14)

class MCLine(Flowable):

   def __init__(self,width):
      Flowable.__init__(self)
      self.width = width

   def __repr__(self):
      return "Line(w=%s)" % self.width

   def draw(self):
      self.canv.line(0,0,self.width,0)

class PharmacogeneticsReport(object):

    def __init__(self, participant):

        self.participant = participant

        self.theme = MyTheme
        self.title = "Research results - Drug responses"
        self.author = "Do not distribute"
        self.buildme = False

        # Colors
        self.header = colors.Color(0.5, 0.5, 0.5, alpha=0.5)
        self.no_effect = colors.Color(0.7, 0.7, 0.7, alpha=0.1)

        self.strong_effect_protective = colors.Color(0.0, 1.0, 0.0, alpha=0.8)
        self.weak_effect_protective = colors.Color(0.0, 1.0, 0.0, alpha=0.4)

        self.strong_effect_risk = colors.Color(1.0, 0.0, 0.0, alpha=0.5)
        self.weak_effect_risk = colors.Color(1.0, 1.0, 0.0, alpha=0.5)

        self.bad_variant = colors.Color(0.0, 0.0, 0.0, alpha=1.0)

    def myFirstPage(self, canvas, doc):

        canvas.saveState()

        canvas.setFont('Helvetica',14)
        canvas.drawString(4.0*inch, 11.4*inch, "%s"%(self.participant.username));
        #canvas.drawString(0.5*inch, 11.4*inch, "Drug responses");

        #canvas.drawString(6.5*inch, 11.4*inch, self.title)
        #canvas.drawString(6.5*inch, 11.2*inch, self.author)

        canvas.setFont('Helvetica',8)
        #canvas.drawString(0.25*inch, 0.25*inch, "Page %d"%(doc.page))
        canvas.drawString(2.5*inch, 0.20*inch, u"\u00A9 2014 Hundred Person Wellness Project. All Rights Reserved.")

        canvas.restoreState()

    def myLaterPages(self, canvas, doc):

        canvas.saveState()

        canvas.setFont('Helvetica',14)
        canvas.drawString(4.0*inch, 11.4*inch, "%s"%(self.participant.username));
        #canvas.drawString(0.5*inch, 11.4*inch, "Drug responses");

        #canvas.drawString(6.5*inch, 11.4*inch, self.title)
        #canvas.drawString(6.5*inch, 11.2*inch, self.author)

        canvas.setFont('Helvetica',8)
        canvas.drawString(7.75*inch, 0.25*inch, "%d"%(doc.page))
        canvas.drawString(2.5*inch, 0.25*inch, u"\u00A9 2014 Hundred Person Wellness Project. All Rights Reserved.")

        canvas.restoreState();

    def Legend(self, story):

        variant_table = []
        variant_style = []

        variant_table.append(["Legend for color codes"])
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'MIDDLE'))
        variant_style.append(('ALIGN',(0,0),(-1,-1),'CENTER'))
        variant_style.append(('LINEABOVE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEBELOW',(0,0),(-1,0),1.0,colors.black))
        variant_style.append(('LINEBEFORE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEAFTER',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('BACKGROUND', (0, 0), (-1, 0), self.header))

        variant_table.append(['You do not have a form of this variant that exerts a positive or negative effect'])
        variant_style.append(('BACKGROUND', (0, 1), (-1, 1), self.no_effect))
        variant_table.append(['Your genotype for this variant is associated with a protective effect'])
        variant_style.append(('BACKGROUND', (0, 2), (-1, 2), self.strong_effect_protective))
        variant_table.append(['Your genotype for this variant is associated with a weak risk'])
        variant_style.append(('BACKGROUND', (0, 3), (-1, 4), self.weak_effect_risk))
        variant_table.append(['Your genotype for this variant is associated with a risk'])
        variant_style.append(('BACKGROUND', (0, 4), (-1, 5), self.strong_effect_risk))

        table = Table(variant_table, [500], hAlign='CENTER', style=variant_style)
        story.append(table)


    def ProcessVariantList(self, story, title):

        variant_table = [['Gene', 'Identifier', 'Effect Allele', 'Your Genotype', 'Description']] # this is the header row
        variant_style = []
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'MIDDLE'))
        variant_style.append(('ALIGN',(0,0),(-1,-1),'CENTER'))
        variant_style.append(('LINEABOVE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEBELOW',(0,0),(-1,0),1.0,colors.black))
        variant_style.append(('LINEBEFORE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEAFTER',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('BACKGROUND', (0, 0), (-1, 0), self.header))

        # Get this variant
        self.participant.LoadTrait(title, 1, True)
        if (not title in self.participant.traits):
            return
        trait = self.participant.traits[title]

        count = 1
        header = False
        for key in trait.variants.keys():
            variant = trait.variants[key]

            if (not header):
                story.append(Paragraph(variant.note_generic.decode('unicode-escape'), h2));
                story.append(Spacer(1, 5));
                story.append(MCLine(7.3*inch))
                header = True

            # Based on the effect value, set the colors
            if (variant.effect == 2):

                variant_table.append([Paragraph(variant.gene, h2), variant.rsid, variant.allele, variant.genotype, Paragraph(variant.note_effect2, h2)])

                variant_style.append(('VALIGN', (0,count), (-1,count), 'MIDDLE'))
                variant_style.append(('ALIGN',(0,count),(-1,count),'CENTER'))
                variant_style.append(('LINEABOVE',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEBELOW',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEBEFORE',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEAFTER',(0,count),(-1,count),0.5,colors.black))

                # If the variant is protective
                if (variant.effect_type == "protective"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.strong_effect_protective))
                elif (variant.effect_type == "risk"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.strong_effect_risk))
                elif (variant.effect_type == "response"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.no_effect))
                else:
                    print "Warning, unknown risk value: %s"%(variant.effect_type)
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.bad_variant))

            elif (variant.effect == 1):

                variant_table.append([Paragraph(variant.gene, h2), variant.rsid, variant.allele, variant.genotype, Paragraph(variant.note_effect1, h2)])

                variant_style.append(('VALIGN', (0,count), (-1,count), 'MIDDLE'))
                variant_style.append(('ALIGN',(0,count),(-1,count),'CENTER'))
                variant_style.append(('LINEABOVE',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEBELOW',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEBEFORE',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEAFTER',(0,count),(-1,count),0.5,colors.black))

                # If the variant is protective
                if (variant.effect_type == "protective"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.strong_effect_protective))
                elif (variant.effect_type == "risk"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.weak_effect_risk))
                elif (variant.effect_type == "response"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.no_effect))
                else:
                    print "Warning, unknown risk value: %s"%(variant.effect_type)
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.bad_variant))

            else:

                variant_table.append([Paragraph(variant.gene, h2), variant.rsid, variant.allele, variant.genotype, Paragraph(variant.note_effect0, h2)])

                variant_style.append(('VALIGN', (0,count), (-1,count), 'MIDDLE'))
                variant_style.append(('ALIGN',(0,count),(-1,count),'CENTER'))
                variant_style.append(('LINEABOVE',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEBELOW',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEBEFORE',(0,count),(-1,count),0.5,colors.black))
                variant_style.append(('LINEAFTER',(0,count),(-1,count),0.5,colors.black))

                variant_style.append(('BACKGROUND', (0, count), (-1, count), self.no_effect))
            count += 1

        table = Table(variant_table, [60, 60, 75, 75, 270], hAlign='CENTER', style=variant_style)
        story.append(table)


    def ProcessPlot(self, story, trait, do_score=True):

        variant_table = [['You', 'Description']] # this is the header row
        variant_style = []
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'MIDDLE'))
        variant_style.append(('ALIGN',(0,0),(-1,-1),'LEFT'))
        variant_style.append(('LINEABOVE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEBELOW',(0,0),(-1,0),1.0,colors.black))
        variant_style.append(('LINEBEFORE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEAFTER',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('BACKGROUND', (0, 0), (-1, 0), self.header))

        temp = "Min: %.3f Max: %.3f"%(trait.min_score, trait.max_score);

        if (trait.unit == "OR"):
            score = trait.GetZScore();
            min_score = 0
            max_score = 1
        else:
            score = trait.GetScore();
            min_score = trait.min_score
            max_score = trait.max_score

        #variant_table.append([Paragraph(variant.reported_genes, h2), variant.dbsnp, variant.risk_allele, variant.genotype, Paragraph(variant.notes, h2)])
        #variant_table.append([Paragraph("Trait goes here", h2), "X2", "X3", trait.GetZScore(), Paragraph(temp, h2)])
        variant_table.append([self.AddGraph(score, trait.actual_unit, min_score, max_score), Paragraph(trait.notes, h2)])

        table = Table(variant_table, [190, 350], hAlign='CENTER', style=variant_style)
        story.append(table)

    def ProcessTrait(self, story, title):

        trait = self.participant.ProcessPharmacogeneticsTrait(title)
        if (trait is None):
            print "Skipping trait %s"%(title)
            return

        story.append(Paragraph(title, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        if (trait.display == "plot"):
            #story.append(Paragraph(trait.notes, h2))
            story.append(Spacer(1,5))
            self.ProcessPlot(story, trait)
        elif (trait.display == "list"):
            story.append(Paragraph(trait.notes, h2))
            story.append(Spacer(1,5))
            self.ProcessVariantList(story, trait)
        else:
            pass;

    def go(self, force=False):

        #if (not self.generate):
        #    print "*** Skipping %s ***"%(self.id)
        #    return

        story = []

        # Add logo
        src = './images/pg_cover1.png'
        img = Image2(src, 625, 400)
        img.hAlign = "CENTER";
        story.append(img)

        story.append(Spacer(1,0.25*inch))

        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>PHARMACOGENETICS</strong></font> is a component of personalized medicine that focuses \
        on how genetic factors influence individual responses to different medications that may affect drug efficacy, drug side effects, \
        and adverse events related to drug therapy. This area of study can play an important role in identifying responders and non-responders \
        to medications and thus avoid adverse events and optimize drug dosage."

        story.append(Paragraph(blurb, h4))
        story.append(Spacer(1,0.25*inch))

        blurb = "This report includes analysis of drug responses related to the following conditions: <br/><br/> \
        <font color='#db881e'>- <strong>Cancer</strong></font><br/><br/> \
        <font color='#db881e'>- <strong>Cardiovascular/anti-clotting</strong></font><br/><br/> \
        <font color='#db881e'>- <strong>Depression/mood stabilization</strong></font><br/><br/> \
        <font color='#db881e'>- <strong>Hepatitis C</strong></font><br/><br/> \
        <font color='#db881e'>- <strong>HIV</strong></font><br/><br/> \
        <font color='#db881e'>- <strong>Immunosuppression</strong></font><br/><br/> \
        <font color='#db881e'>- <strong>Malignant hyperthermia</strong></font><br/><br/> \
        <font color='#db881e'>- <strong>Pain</strong></font><br/>"

        story.append(Paragraph(blurb, h4))

        story.append(PageBreak())

        story.append(Spacer(1,0.25*inch))

        story.append(Paragraph("<font color='#db881e'><strong>Overview</strong></font>", h0))
        story.append(Spacer(1, 0.5*inch))

        blurb = "You may have had an experience where a particular medication didn't work for you, even if it worked well for \
        someone else. Or perhaps a certain medication causes you to have severe side effects whereas someone else does fine with it. \
        Differences in response to medications are common and are influenced by age, lifestyle and health.  But your genes also play \
        an important role in influencing your response to medications."

        story.append(Paragraph(blurb, h4))

        blurb = "There is considerable research underway looking to match specific gene variations with responses to particular medications. " \
                "Using this kind of information allows doctors to tailor treatments to individuals. This is the science of <strong>pharmacogenetics.</strong>"

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(blurb, h4))

        blurb = "This is a very exciting new field because pharmacogenetics offers the promise of predicting whether a medication is likely \
        to be beneficial or harmful - before you ever take it."

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(blurb, h4))

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph("<font color='#db881e'><strong>The Right Medicine, The Right Dose</strong></font>", h0))

        blurb = "Every person is genetically and biochemically unique. This means that your body's reaction to many things in your environment \
        - including foods, toxins, and medications - is unique to you. Pharmacogenetics looks at how you are able to metabolize medications based \
        on your genetic makeup."

        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(blurb, h4))

        blurb = "For example, one pharmacogenetic test looks at a group of enzymes that are responsible for breaking down and eliminating \
        more than 30 types of medications, including anti-depressants, chemotherapy drugs and heart medications.Some people, because of their \
        genetic makeup, aren't able to break down these medications fast enough. This means the medications build up in the body and can cause \
        severe side effects. Conversely, some people break down these medications too quickly - before they have a chance to work."

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(blurb, h4))

        blurb = "<strong>Thus, an individual can experience 'adverse effects' due to either too rapid or too slow metabolism of a drug.</strong> \
        Knowing your genetic makeup, your doctor can determine the best dose of medication for you - or whether a different medication \
        altogether may be more appropriate."

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(blurb, h4))

        blurb = "Although pharmacogenetics has much promise, it's still in its early stages. Millions of genetic variations exist, \
        and identifying which of the variants affect your drug responses could take many years. Research is under way, however, and \
        pharmacogenetics will someday soon be part of routine medical care."

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(blurb, h4))

        blurb = "For more information please visit: <u><a href='http://www.genome.gov/27530645'>http://www.genome.gov/27530645</a></u>."

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(blurb, h4))

        story.append(PageBreak())

        story.append(Spacer(1,0.5*inch))

        story.append(Paragraph("<font color='#db881e'><strong>YOUR REPORT</strong></font>", h0))
        story.append(Spacer(1, 0.5*inch))

        blurb = "In your report, you will see tests for a number of common variants related to drug response that have been \
        evaluated and validated by a group called The Clinical Pharmacogenetics Implementation Consortium (CPIC). CPIC's goal \
        is to address some of the barriers to implementation of pharmacogenetic tests into clinical practice."

        story.append(Paragraph(blurb, h4))

        blurb = "In general, the results in your report fall into two categories: <br/><br/> \
        <font color='#db881e'>1. <strong>Increased (or decreased) risk for <u>side effects</u> due to a certain medication, or</strong></font><br/> \
        <font color='#db881e'>2. <strong>Increased (or decreased) ability to metabolize a medication, leading to potential need for your \
        physician to <u>adjust the dosage</u> to avoid side effects or optimize drug effectiveness.</strong></font><br/>"

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(blurb, h4))

        blurb = "IMPORTANT: This report is for research purposes only and should not be construed as clinical/medical information. \
        You should never stop taking prescription medication, or change the amount you are taking, without the advice of your doctor. \
        If you have questions about this information, please discuss them with a qualified healthcare provider."

        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(blurb, h4))

        story.append(Spacer(1, 0.5*inch))

        self.Legend(story)

        story.append(Spacer(1,0.25*inch))

        story.append(Paragraph("<font color='#db881e'><strong>Definitions</strong></font>", h0))
        story.append(Spacer(1, 0.25*inch));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.1*inch))

        blurb = "<font color='#db881e'><strong>Gene</strong></font> - this is a standardized symbol geneticists use to identify a gene.<br/><br/> \
        <font color='#db881e'><strong>Identifer</strong></font> - this is a code that uniquely identifies to a geneticist a specific location in the genome; it refers to a database of known genomic variants, also known as Single Nucleotide Polymorphisms (SNPs).<br/><br/> \
        <font color='#db881e'><strong>Effect Allele</strong></font> - an allele is a specific version (variant) that has been observed in a given location in the genome; the effect allele is the version that has been associated with modified effects.<br/><br/> \
        <font color='#db881e'><strong>Your Genotype</strong></font> - this field shows you which alleles you have at this location in the genome. If your genotype contains one or two copies of the 'effect allele', it suggests you may have altered function in this gene."

        story.append(Paragraph(blurb, h4))

        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO ANTI-CANCER DRUGS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "Capecitabine"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "Fluorouracil"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "Tegafur"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "Mercaptopurine or thioguanine"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        story.append(PageBreak())
        story.append(Spacer(1,0.25*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO CARDIOVASCULAR AND ANTI-CLOTTING DRUGS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "Simvastatin"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "Clopidogrel"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "Warfarin"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO ANTIDEPRESSANTS AND MOOD STABILIZERS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "Carbamazepine"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "Tricyclic antidepressants"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        story.append(PageBreak())
        story.append(Spacer(1,0.25*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO HEPATITIS C MEDICATIONS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "PEG-interferon-alpha"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "PEG-interferon-alpha-2a"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "PEG-interferon-alpha-2b"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "Telaprevir"
        self.ProcessVariantList(story, title)

        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO HIV MEDICATIONS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "Abacavir"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO IMMUNOSUPPRESSANT DRUGS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "Azathioprine"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        # Header section
        story.append(Paragraph("RISK FOR MALIGNANT HYPERTHERMIA", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        variant_table = [['Gene', 'Identifier', 'Effect Allele', 'Your Genotype', 'Description']] # this is the header row
        variant_style = []
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'MIDDLE'))
        variant_style.append(('ALIGN',(0,0),(-1,-1),'CENTER'))
        variant_style.append(('LINEABOVE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEBELOW',(0,0),(-1,0),1.0,colors.black))
        variant_style.append(('LINEBEFORE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEAFTER',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('BACKGROUND', (0, 0), (-1, 0), self.header))

        story.append(Paragraph("Malignant hyperthermia is a rare, life-threatening inherited condition that causes a fast rise in body temperature and  severe muscle contractions when the affected person gets certain drugs for general anesthesia.  When exposed to these drugs, affected individuals will experience circulatory collapse and death if not treated quickly.", h2));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        header = True
        count = 0

        variant_table.append([Paragraph("RYR1, CACNA1S", h2), '-', '-', '-', Paragraph("You do not have any known variants associated with malignant hyperthermia", h2)])

        variant_style.append(('VALIGN', (0,count), (-1,count), 'MIDDLE'))
        variant_style.append(('ALIGN',(0,count),(-1,count),'CENTER'))
        variant_style.append(('LINEABOVE',(0,count),(-1,count),0.5,colors.black))
        variant_style.append(('LINEBELOW',(0,count),(-1,count),0.5,colors.black))
        variant_style.append(('LINEBEFORE',(0,count),(-1,count),0.5,colors.black))
        variant_style.append(('LINEAFTER',(0,count),(-1,count),0.5,colors.black))

        variant_style.append(('BACKGROUND', (0, count), (-1, count), self.no_effect))
        table = Table(variant_table, [60, 60, 75, 75, 270], hAlign='CENTER', style=variant_style)
        story.append(table)
        story.append(Spacer(1,0.5*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO PAIN MEDICATIONS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "Codeine"
        self.ProcessVariantList(story, title)

        #story.append(PageBreak())

        output_dir = './results';
        output_filename = output_dir + '/' + self.participant.username + '.pharmacogenetics.pdf';

        # Only build the report if I haven't found any issues with the data
        if (self.buildme or force):
            doc_template_args = self.theme.doc_template_args()
            doc = SimpleDocTemplate(output_filename, title=self.title, author=self.author, **doc_template_args)
            doc.build(story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)
        else:
            print "Skipping report for %s"%(self.participant.username);
