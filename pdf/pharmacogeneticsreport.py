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

        """
        trait = "Insulin Resistance/Type 2 Diabetes"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Type 2 diabetes, once known as adult-onset or noninsulin-dependent diabetes, \
        is a chronic condition that affects the way your body metabolizes sugar (glucose), your body's important \
        source of fuel. With type 2 diabetes, your body either resists the effects of insulin - a hormone that \
        regulates the movement of sugar into your cells - or doesn't produce enough insulin to maintain a normal glucose level.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(PageBreak())
        story.append(Spacer(1,0.5*inch))

        trait = "Snacking"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Snacking can be a healthy or unhealthy behavior. Snacking on balanced foods, \
containing healthy fats, lean protein, fiber and low glycemic index carbohydrates, \
in small portions, throughout the day can help control hunger cravings and reduce \
total caloric intake, while snacking on junk food can have negative health effects. \
If you have a predisposition for snacking, you may want to curtail the negative effects by choosing healthy \
snacks, eating slowly and reducing the size or calories of snacks.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1,0.25*inch))

        trait = "Satiety/Feeling Full"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Satiety can be described as the feeling of fullness after you eat. The FTO (fat mass \
and obesity-associated) gene is known to be an important factor that predisposes \
a person to a healthy or unhealthy level of body weight. People who \
experience difficulty in feeling full tend to eat more without feeling satisfied. \
To help manage this outcome, you could increase the amount of fiber in your diet \
and balance meals and snacks throughout the day. Examples of foods high in \
fiber include whole wheat bread, oatmeal, barley, lentils, black beans, artichokes, \
raspberries, and peas.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1,0.25*inch))

        trait = "Cholesterol"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Low-density lipoprotein (LDL) is the type of cholesterol that can become dangerous \
if you have too much of it. Like gunk clogging up your kitchen drain, LDL \
cholesterol can form plaque and build up in the walls of your arteries. This can \
make your arteries narrower and less flexible, putting you at risk for conditions like \
a heart attack or stroke. High-density lipoprotein (HDL) cholesterol is known as good cholesterol, because \
high levels of HDL cholesterol seem to protect against heart attack, while low \
levels of HDL cholesterol (less than 40 mg/dL) increase the risk of heart disease. \
While multiple mechanisms are known to account for this, the major one is thought \
to be the role of HDL in transporting excess cholesterol away from the arteries and \
back to the liver, where it is passed from the body", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(PageBreak())
        story.append(Spacer(1,0.5*inch))

        trait = "Oxidative Stress"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Your body constantly reacts with oxygen as you breathe and your cells produce energy. \
        As a consequence of this activity, highly reactive molecules are produced within our cells known as free radicals \
and oxidative stress occurs. When our protein-controlled anti-oxident response doesn't keep up, oxidative stress causes damage \
that has been implicated in the cause of many diseases, as well as impacting the body's aging process.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1,0.25*inch))

        trait = "Vitamin D"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Vitamin D is important for the absorption and utilization of calcium, which is \
beneficial for maintaining good bone health. Exposure to sunlight is an important \
determinant of a person's vitamin D level, since there are few natural dietary \
sources of vitamin D. While sunscreen use blocks skin production of vitamin D, \
excessive sun exposure is a risk factor for skin cancer and related conditions, and \
is not recommended. Dietary sources of vitamin D include some fatty fish, fish \
liver oils, and milk or cereals fortified with vitamin D. The recommended intake of \
vitamin D for most adults is 600 IUs per day. About 115 IUs of vitamin D is found in \
one cup of vitamin D-fortified, non-fat, fluid milk.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Vitamin B6"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Vitamin B6, also called pyridoxine, helps your body's neurological system \
to function properly, promotes red blood cell health, and is involved in sugar \
metabolism. Vitamin B6 is found naturally in many foods, including beans, whole grains, meat, eggs and fish. Most \
people receive sufficient amounts of vitamin B6 from a healthy diet, and B6 \
deficiency is rare in the United States.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch))

        trait = "Vitamin B12"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Vitamin B12 plays an important role in how your brain and nervous system \
function. It helps to keep red blood cells healthy and is a critical component for \
synthesis and regulation of your DNA. Vitamin B12 is found naturally in foods \
of animal origin including meat, fish, poultry, eggs and milk products. A healthy \
diet will typically provide sufficient B12, although vegetarians, vegans, older \
people, and those with problems absorbing B12 due to digestive system disorders \
may be deficient. Symptoms of vitamin B12 deficiency can vary, but may include \
fatigue, weakness, bloating, or numbness and tingling in the hands and feet. The \
recommended intake for adults is 2.4 micrograms per day.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Vitamin C"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Vitamin C, or L-ascorbic acid, must be acquired from dietary sources, as humans \
are unable to synthesize it. Some dietary sources of vitamin C include lemons, \
oranges, red peppers, watermelons, strawberries and citrus juices or juices \
fortified with vitamin C. While a severe deficiency of vitamin C ultimately leads \
to scurvy, variations in vitamin C levels have also been associated with a wide \
range of chronic complex diseases, such as atherosclerosis, type 2 diabetes and \
cancer. These associations are thought to result from a contribution of vitamin \
C as an antioxidant, as well as its role in the synthesis of collagen and various \
hormones. After ingestion, the vitamin C in one's diet gets transported across the \
cell membrane via transport proteins, one of which is SLC23A1", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Folate"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Folate is found in many foods, such as green leafy vegetables like chard or kale, \
as well as beans, lentils, fruits and fortified grains. This nutrient plays a role in \
protein metabolism, as well as DNA repair. Folate can lower the blood level \
of homocysteine, a substance linked to cardiovascular disease at high levels. \
Genetic mutations in the gene MTHFR are the most \
commonly known inherited risk factor for elevated homocysteine levels. \
Folate is particularly important early in pregnancy for preventing some \
birth defects. For this reason, pregnant women or women intending to become \
pregnant are advised an elevated recommended daily intake of 600 micrograms of \
folate. The recommended intake of folate for most adults is 400 micrograms per \
day.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch))

        trait = "Vitamin E"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Vitamin E is a group of eight antioxidant molecules, of which alpha-tocopherol is \
the most abundant in the body. Vitamin E functions to promote a strong immune \
system and regulates other metabolic processes. The recommended intake \
of vitamin E for most adults is 15 milligrams per day. Note that synthetic varieties \
of vitamin E found in some fortified foods and supplements are less biologically \
active. Sources of naturally-occurring vitamin E in foods are vegetable oils, green \
leafy vegetables, eggs and nuts. Most adults normally do not \
take in adequate amounts of vitamin E on a daily basis, so keeping an eye on \
your vitamin E intake is good advice for anyone.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Iron"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Hereditary hemochromatosis causes your body to absorb too much iron from \
        the food you eat. The excess iron is stored in your organs, especially your liver, heart and pancreas. The excess \
        iron can poison these organs, leading to life-threatening conditions such as cancer, heart \
        arrhythmias and cirrhosis. Many people inherit the faulty genes that cause hemochromatosis - it is the most \
        common genetic disease in Caucasians. But only a minority of those with the genes develop serious \
        problems. Hemochromatosis is more likely to be serious in men. Signs and symptoms of hereditary hemochromatosis \
        usually appear in midlife. Iron can be dropped to safe levels by regularly removing blood from your body.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Lactose"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Lactose intolerance is the inability to digest lactose, \
                    the sugar found in milk and milk products. This \
                    condition is caused by the lack of an enzyme called \
                    lactase. The rs4988235 variant lies close to the \
                    lactase (LCT) gene, in the MCM6 gene, and has \
                    been shown to regulate lactase levels. If you \
                    are lactose intolerant you should make sure that \
                    you are getting enough calcium from non-dairy or \
                    lactose-free sources. On the other hand, if you are \
                    not lactose intolerant, be aware that dairy products \
                    can be high in calories, fat, or both.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Sweet tooth"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Craving sweet foods is sometimes described as having a 'sweet tooth.' If your genotype \
shows an increased likelihood to eat lots of sweets, try choosing fruit as a healthy \
sweet alternative to sugary foods or soda. Be sure to follow your diet as some \
diet plans, such as the low carbohydrate diets, significantly limit the amount \
of sugar you can eat. Sweet foods can include healthy foods, such as fruits, or \
unhealthy foods like candy and sweetened beverages.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch))

        trait = "Caffeine"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Caffeine is one of the most widely consumed \
stimulants in the world, and it is found in the leaves \
and seeds of many plants. It is also produced \
artificially and added to some foods. Caffeine is \
found in tea, coffee, chocolate, many soft drinks and \
energy drinks, as well as in some pain relievers \
and other over-the-counter medications. Caffeine is \
metabolized by a liver enzyme, which is encoded \
by the CYP1A2 gene. Variation at a marker in the \
CYP1A2 gene results in different levels of enzyme \
activity, and thus, different metabolism rates for \
caffeine. If you are a slow metabolizer, \
then caffeine may have longer lasting stimulant \
effects for you.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Bitter taste"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("People taste things differently. Variations in the \
TAS2R38 gene are associated with different levels \
of sensitivity to a chemical called PTC \
which produces a strong bitter taste. A person described as a 'taster' \
may be more sensitive to bitter flavors found in \
foods, such as grapefruit, coffee, dark chocolate and \
cruciferous vegetables, such as Brussels sprouts, \
cabbage and kale. If you are a 'taster', you should make \
an extra effort to incorporate green leafy vegetables into your diet, \
as you may be initially inclined to avoid them.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Athletic performance - Endurance"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Endurance training is generally used to describe exercise that is done for a longer \
duration with moderate intensity. Most people can benefit from a combination of \
endurance, high intensity and resistance exercises. Some people have genetic \
markers that are associated with increased endurance performance.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Athletic performance - Strength"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("Strength training can be described as exercises that incorporate the use of \
opposing forces to build muscle. Certain variants have been associated with increased muscular strength.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch))

        trait = "Response to exercise"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("High blood pressure, also known as hypertension, is a common health issue. It \
has been estimated that a majority of people will have hypertension at some time \
in their lives. A genetic variant in the EDN1 gene has been shown to increase the \
likelihood of hypertension in people who were low in cardiorespiratory fitness, \
which refers to the ability of the heart and lungs to provide muscles with oxygen \
for physical activity. This genetic variant did not show an effect in people who \
were high in cardiorespiratory fitness.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Exercise injury"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("The Achilles tendon connects your calf muscles to \
your heel bone. Tendinopathy describes either the \
inflammation or tiny tears to the tendon. People \
who play sports and runners who place stress on \
the Achilles tendon have the greatest likelihood \
of tendinopathy. Certain genotypes \
may be more injury-prone, while other genotypes \
have a typical likelihood of developing Achilles \
tendinopathy.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        story.append(Spacer(1, 0.25*inch))

        trait = "Longevity"
        story.append(Paragraph(trait, h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))
        story.append(Paragraph("While it is the subject of much research, scientists have \
        not identified the gene 'for' longevity. It is much more likely that longevity is associated \
        with many genes and associated variants, each of which contributes a small probability. However, a few \
        genes have been associated with particularly long-lived individuals. Having these variants does not \
        guarantee a long life any more than not having them guarantees a short one.", h2))
        story.append(Spacer(1,5))
        self.ProcessTrait(story, trait)

        # Begin page 4
        #story.append(PageBreak())
        #story.append(Paragraph('Last heading', h1))

        """