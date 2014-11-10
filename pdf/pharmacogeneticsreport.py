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
        canvas.drawString(0.5*inch, 11.4*inch, "Drug responses");

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
        canvas.drawString(0.5*inch, 11.4*inch, "Drug responses");

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
        variant_table.append(['Your genotype for this variant is associated with a weak protective effect'])
        variant_style.append(('BACKGROUND', (0, 3), (-1, 3), self.weak_effect_protective))
        variant_table.append(['Your genotype for this variant is associated with a weak risk'])
        variant_style.append(('BACKGROUND', (0, 4), (-1, 4), self.weak_effect_risk))
        variant_table.append(['Your genotype for this variant is associated with a risk'])
        variant_style.append(('BACKGROUND', (0, 5), (-1, 5), self.strong_effect_risk))

        table = Table(variant_table, [500], hAlign='CENTER', style=variant_style)
        story.append(table)


    def ProcessVariantList(self, story, title):

        variant_table = [['Gene', 'Identifier', 'Effect', 'You', 'Description']] # this is the header row
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
                story.append(Paragraph(variant.note_generic, h2));
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
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.weak_effect_protective))
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

        table = Table(variant_table, [75, 60, 30, 25, 350], hAlign='CENTER', style=variant_style)
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

        story.append(Spacer(1,0.25*inch))

        story.append(Paragraph("This is your personalized pharmacogenetic (drug response) report. \
        The information below describes how you may respond to certain types of commonly prescribed \
        drugs based on your unique genotype.  If you are currently taking one of the types of drugs \
        described in this report and you have a variant in a gene related to response to that drug, \
        we encourage you to take this report to your physician to discuss appropriate steps.", h2))

        story.append(Spacer(1,0.25*inch))

        story.append(Paragraph("<strong>IMPORTANT: This report is for research purposes only and should not be construed as clinical/medical \
        information.  You should never stop taking prescription medication, or change the amount you are taking, \
        without the advice of your doctor. If you have any questions about this information, please discuss them with \
        a qualified healthcare provider.</strong>", h2))

        story.append(Spacer(1,0.25*inch))

        self.Legend(story)

        # Add logo
        #src = './images/pioneerLogo_ISBLogo.png'
        #img = Image(src, 450, 75)
        #img.hAlign = "CENTER"
        #story.append(img)

        story.append(Spacer(1,0.5*inch))

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
        story.append(Spacer(1,0.5*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO HIV MEDICATIONS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "Abacavir"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        title = "Azathioprine"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        # Header section
        story.append(Paragraph("RESPONSE TO PAIN MEDICATIONS", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        title = "Codeine"
        self.ProcessVariantList(story, title)
        story.append(Spacer(1,0.5*inch))

        # Header section
        story.append(Paragraph("RISK FOR MALIGNANT HYPOTHERMIA", h1));
        story.append(Spacer(1, 5));
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))


        variant_table = [['Gene', 'Identifier', 'Effect', 'You', 'Description']] # this is the header row
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

        variant_table.append([Paragraph("RYR1, CACNA1S", h2), '-', '-', '-', Paragraph("You do not have any known variants associated with malignant hypothermia", h2)])

        variant_style.append(('VALIGN', (0,count), (-1,count), 'MIDDLE'))
        variant_style.append(('ALIGN',(0,count),(-1,count),'CENTER'))
        variant_style.append(('LINEABOVE',(0,count),(-1,count),0.5,colors.black))
        variant_style.append(('LINEBELOW',(0,count),(-1,count),0.5,colors.black))
        variant_style.append(('LINEBEFORE',(0,count),(-1,count),0.5,colors.black))
        variant_style.append(('LINEAFTER',(0,count),(-1,count),0.5,colors.black))

        variant_style.append(('BACKGROUND', (0, count), (-1, count), self.no_effect))
        table = Table(variant_table, [75, 60, 30, 25, 350], hAlign='CENTER', style=variant_style)
        story.append(table)

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
