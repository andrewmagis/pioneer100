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

class DiseaseReport(object):

    def __init__(self, participant):

        self.participant = participant

        self.theme = MyTheme
        self.title = "Beta Genetics Report"
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
        canvas.drawString(4.0*inch, 11.4*inch, "%s"%(self.participant.username))
        #canvas.drawString(0.5*inch, 11.2*inch, "Gender: %s"%(self.gender))
        #canvas.drawString(0.5*inch, 11.0*inch, "DOB: %s"%(self.dob))

        #canvas.drawString(6.5*inch, 11.4*inch, self.title)
        #canvas.drawString(6.5*inch, 11.2*inch, self.author)

        canvas.setFont('Helvetica',8)
        #canvas.drawString(0.25*inch, 0.25*inch, "Page %d"%(doc.page))
        canvas.drawString(2.5*inch, 0.20*inch, u"\u00A9 2014 Institute for Systems Biology. All Rights Reserved.")

        canvas.restoreState()

    def myLaterPages(self, canvas, doc):

        canvas.saveState()

        canvas.setFont('Helvetica',14)
        canvas.drawString(4.0*inch, 11.4*inch, "%s"%(self.participant.username))
        #canvas.drawString(0.5*inch, 11.2*inch, "Gender: %s"%(self.gender))
        #canvas.drawString(0.5*inch, 11.0*inch, "DOB: %s"%(self.dob))

        #canvas.drawString(6.5*inch, 11.4*inch, self.title)
        #canvas.drawString(6.5*inch, 11.2*inch, self.author)

        canvas.setFont('Helvetica',8)
        canvas.drawString(7.75*inch, 0.25*inch, "%d"%(doc.page))
        canvas.drawString(2.5*inch, 0.25*inch, u"\u00A9 2014 Institute for Systems Biology. All Rights Reserved.")

        canvas.restoreState()

    def BuildAlzheimersReport(self, force=False):

        #if (not self.generate):
        #    print "*** Skipping %s ***"%(self.id)
        #    return

        story = []

        story.append(Spacer(1,0.25*inch))

        # Get my APOE haplotype
        title = "APOE Status for Alzheimers"
        self.participant.LoadTrait("APOE Status for Alzheimers", 1, True)
        if (not title in self.participant.traits):
            return
        trait = self.participant.traits[title]

        genotype = None

        # We can just do the calculation here for now. Later we will have
        # some analysis code to do this in a general way
        if (trait.variants['rs7412'].effect == 0):

            if (trait.variants['rs429358'].effect == 0):

                # rs7412(T) and rs429358(T) <- E2
                # rs7412(T) and rs429358(T) <- E2
                genotype = "ApoE2/ApoE2"

            elif (trait.variants['rs429358'].effect == 1):

                # rs7412(T) and rs429358(C) <- unobserved haplotype
                # rs7412(T) and rs429358(T) <- E2
                raise MyError('This is a previously unobserved haplotype')

            elif (trait.variants['rs429358'].effect == 2):

                # rs7412(T) and rs429358(C) <- unobserved haplotype
                # rs7412(T) and rs429358(C) <- unobserved haplotype
                raise MyError('This is a previously unobserved haplotype')

            else:
                raise MyError("Unknown haplotype for APOE")

        elif (trait.variants['rs7412'].effect == 1):
            if (trait.variants['rs429358'].effect == 0):

                # rs7412(C) and rs429358(T) <- E3
                # rs7412(T) and rs429358(T) <- E2
                genotype = "ApoE2/ApoE3"

            elif (trait.variants['rs429358'].effect == 1):

                # Remember that
                # rs7412(T) and rs429358(C) is not observed, so the
                # rs7412(T) and rs429358(C)
                # rs7412(C) and rs429358(T) arrangement is not possible

                # rs7412(C) and rs429358(C) <- E4
                # rs7412(T) and rs429358(T) <- E2
                genotype = "ApoE2/ApoE4"

            elif (trait.variants['rs429358'].effect == 2):

                # rs7412(C) and rs429358(C) <- E4
                # rs7412(T) and rs429358(C) <- unobserved haplotype
                raise MyError('This is a previously unobserved haplotype')

            else:
                raise MyError("Unknown haplotype for APOE")

        elif (trait.variants['rs7412'].effect == 2):
            if (trait.variants['rs429358'].effect == 0):

                # rs7412(C) and rs429358(T) <- E3
                # rs7412(C) and rs429358(T) <- E3
                genotype = "ApoE3/ApoE3"

            elif (trait.variants['rs429358'].effect == 1):

                # rs7412(C) and rs429358(C) <- E4
                # rs7412(C) and rs429358(T) <- E3
                genotype = "ApoE3/ApoE4"

            elif (trait.variants['rs429358'].effect == 2):

                # rs7412(C) and rs429358(C) <- E4
                # rs7412(C) and rs429358(C) <- E4
                genotype = "ApoE4/ApoE4"

            else:
                raise MyError("Unknown haplotype for APOE")

        print "******************* APOE Status", genotype

        story.append(Paragraph("ALZHEIMER'S/CARDIOVASCULAR GENETIC RISK REPORT", h1))
        story.append(Spacer(1, 5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        story.append(Paragraph("<strong>Your genotype: %s</strong>"%(genotype), h2))

        story.append(Spacer(1,0.25*inch))

        story.append(Paragraph("There are a number of genes that have been associated with Alzheimer's disease risk but the most common one is called apolipoprotein E (APOE). This gene codes for a protein that carries cholesterol in the bloodstream and is also associated with increased risk for heart attack and stroke.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("The APOE gene has three forms, or alleles:", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("ApoE3 - the most common - neutral effect on the risk of Alzheimer's/cardiovascular disease.", h2, bulletText='-'))
        story.append(Paragraph("ApoE2 - the least common - reduced risk of Alzheimer's/cardiovascular disease compared to ApoE3.", h2, bulletText='-'))
        story.append(Paragraph("ApoE4 - a little more common - increased risk of Alzheimer's/cardiovascular disease compared to ApoE3.", h2, bulletText='-'))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("You inherit one copy of the APOE gene from your mother and another from your father, so you have two copies, which can either be the same or different. Having at least one ApoE4 allele increases your risk of developing Alzheimer's disease. If you have two ApoE4 alleles, your risk is even higher.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Not everyone who has the ApoE4 allele develops Alzheimer's disease, and the disease occurs in many people who don't have the ApoE4 allele. Thus, ApoE4 affects risk but is not a cause. Most experts agree that multiple genetic and environmental factors interact to cause Alzheimer's disease.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Lifestyle Approaches to Reduce Risk for Alzheimer's", h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))

        story.append(Paragraph("Although there is no proven way to prevent Alzheimer's, many studies suggest that the same behaviors that reduce risk of atherosclerosis and heart disease may also reduce Alzheimer's risk. For example:", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Being more physically active", h2, bulletText='-'))
        story.append(Paragraph("Eating more fruits and vegetables, decreasing meat and dairy intake and glycemic index", h2, bulletText='-'))
        story.append(Paragraph("Quitting smoking", h2, bulletText='-'))
        story.append(Paragraph("Losing excess weight", h2, bulletText='-'))
        story.append(Paragraph("Reducing blood cholesterol and high blood pressure", h2, bulletText='-'))
        story.append(Paragraph("Managing diabetes", h2, bulletText='-'))
        story.append(Paragraph("Managing depression", h2, bulletText='-'))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Studies have also found an association between lifelong involvement in mentally and socially stimulating activities and reduced risk of Alzheimer's disease.  Some ideas include: learning a musical instrument or a new language, story-telling, travel, taking classes in topics of interest, games and puzzles.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Alzheimer's disease is more common in people who have low blood levels of vitamin D and omega-3 fatty acids.  Although it is unknown whether taking supplements of vitamin D or omega-3 fatty acids can actually prevent or delay the development of Alzheimer's, there are few risks and many other benefits to maintaining optimal blood levels of these nutrients. Supplements could be considered in those with genetic risk for Alzheimer's disease who have low blood levels of vitamin D or omega-3 fatty acids.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Lastly, research suggests a connection between exposure to certain environmental toxins and pesticides and development of Alzheimer's disease.  While we don't know if avoiding pesticide exposure reduces risk, it seems prudent for people at increased genetic risk to focus on minimizing exposure through consuming organically grown foods and avoiding home and occupational exposure to toxins.", h2))

        output_dir = './results'
        output_filename = output_dir + '/' + self.participant.username + '.alzheimers.pdf'

        # Only build the report if I haven't found any issues with the data
        if (self.buildme or force):
            doc_template_args = self.theme.doc_template_args()
            doc = SimpleDocTemplate(output_filename, title=self.title, author=self.author, **doc_template_args)
            doc.build(story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)
        else:
            print "Skipping report for %s"%(self.participant.username)

    def BuildParkinsonsReport(self, force=False):

        #if (not self.generate):
        #    print "*** Skipping %s ***"%(self.id)
        #    return

        story = []

        story.append(Spacer(1,0.25*inch))

        story.append(Paragraph("PARKINSON'S GENETIC RISK REPORT", h1))
        story.append(Spacer(1, 5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,0.25*inch))

        trait = self.participant.ProcessPharmacogeneticsTrait("Parkinson's Status")
        #for key in trait.variants.keys():
        #    trait.variants[key].Print();

        variant_table = [['Gene', 'Identifier', 'Effect', 'You', 'Description']] # this is the header row
        variant_style = []
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'MIDDLE'))
        variant_style.append(('ALIGN',(0,0),(-1,-1),'CENTER'))
        variant_style.append(('LINEABOVE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEBELOW',(0,0),(-1,0),1.0,colors.black))
        variant_style.append(('LINEBEFORE',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('LINEAFTER',(0,0),(-1,0),0.5,colors.black))
        variant_style.append(('BACKGROUND', (0, 0), (-1, 0), self.header))

        count = 1
        for key in trait.variants.keys():
            variant = trait.variants[key]

            notes = "Nothing"
            if (variant.effect == 0):
                notes = "You do not have any copies of the A allele. You are at normal risk for Parkinson's disease"
            elif (variant.effect == 1):
                notes = "You have a single copy of the A allele. You are at increased risk for Parkinson's disease"
                print notes
            elif (variant.effect == 2):
                notes = "You have two copies of the A allele. You are at increased risk for Parkinson's disease"
            else:
                raise MyError('Invalid effect')

            variant_table.append([Paragraph(variant.reported_genes, h2), variant.dbsnp, variant.risk_allele, variant.genotype, Paragraph(notes, h2)])

        table = Table(variant_table, [75, 60, 30, 25, 350], hAlign='CENTER', style=variant_style)
        story.append(table)

        story.append(Spacer(1,0.25*inch))

        story.append(Paragraph("Parkinson's disease (PD) is a progressive disorder of the nervous system. PD affects several regions of the brain, especially areas that control balance and movement.  The disease can also affect emotions and thinking ability.  Despite decades of intensive study, the causes of PD remain unknown. Although genes play a role, only 15-25% of people with Parkinson's report having a relative with the disease.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("There are a number of different gene variants that have been associated with increased risk of PD - some of these variants appear to impact overall risk, others impact age of onset.  None of these genes is thought to cause the disease independent of lifestyle and environment - most experts agree that multiple genetic and environmental factors interact to cause Parkinson's disease.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Approaches to Reducing Risk for Parkinson's Disease", h1))
        story.append(Spacer(1,5))
        story.append(MCLine(7.3*inch))
        story.append(Spacer(1,5))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("There is no known way to prevent Parkinson's disease; however, research has shown that some lifestyle approaches may be helpful in reducing risk.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("<strong>Nutrition:</strong>  In general, nutrients that protect against oxidative damage and reduce inflammation are among the leading contenders to reduce PD risk:", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Mediterranean Diet - People who eat a Mediterranean type diet pattern (more fruits and vegetables, high-fiber foods, fish, and omega-3 rich oils and less red meat and dairy) have lower rates of PD than people who eat a typical Western diet.", h2, bulletText='-'))
        story.append(Paragraph("Some specific foods, including peppers, tomatoes, oranges, apples and berries, have been associated with lower risk of developing PD. Higher intake of coffee and green tea have also been found to reduce Parkinson's risk.", h2, bulletText='-'))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Several other nutrients may also be important in moderating PD risk:", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("Vitamin B6: Several studies suggest that increasing intake of vitamin B6 lowers risk.", h2, bulletText='-'))
        story.append(Paragraph("CoQ10: CoQ10 levels are low in plasma from patients with PD are also low in vital regions of the brain in PD sufferers. It is unclear if supplementation reduces risk.", h2, bulletText='-'))
        story.append(Paragraph("Omega-3 fats:  People consuming diets high in omega-3 fats have a lower risk of PD.", h2, bulletText='-'))
        story.append(Paragraph("Vitamin D - vitamin D plays a crucial role in brain development, brain function regulation and neuroprotection. Vitamin D deficiency is common in patients with PD and 1 study in patients with PD showed beneficial effects of vitamin D supplements.", h2, bulletText='-'))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("<strong>Exercise:</strong> Several large prospective studies have shown a correlation between aerobic exercise earlier in life and a reduced chance of developing Parkinson's. Exercising in your 30s and 40s - decades before Parkinson's typically occurs - may reduce the risk of getting Parkinson's disease by about 30%.  Vigorous exercise may be needed to get this effect. (NOTE: Talk to your physician before starting a new exercise program or significantly increasing exercise intensity).", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("<strong>Environmental Toxins:</strong> Epidemiological research has identified rural living, well water, manganese and pesticides as increasing risk for PD.  The effect of pesticides on PD risk is thought to explain the higher rates in people who live in rural (farming) areas and who drink rural well water that may be contaminated with pesticides.  Prudence suggests limiting all exposure to reduce risk.", h2))

        story.append(Spacer(1,0.1*inch))

        story.append(Paragraph("<strong>Drugs:</strong> Once Parkinson's has been diagnosed, conventional medical therapy using a variety of pharmaceutical approaches is advised.  A physician who specializes in treating Parkinson's disease should advise on the best course of treatment for each individual.", h2))

        output_dir = './results'
        output_filename = output_dir + '/' + self.participant.username + '.parkinsons.pdf'

        # Only build the report if I haven't found any issues with the data
        if (self.buildme or force):
            doc_template_args = self.theme.doc_template_args()
            doc = SimpleDocTemplate(output_filename, title=self.title, author=self.author, **doc_template_args)
            doc.build(story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)
        else:
            print "Skipping report for %s"%(self.participant.username)