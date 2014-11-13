"""
    __init__.py "

    Andrew Magis
    Date:    2014-7-29

"""

from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
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

PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
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
      
class TransitionsReport(object):

    def __init__(self, participant):

        # Save the participant object
        self.participant = participant;

        self.theme = MyTheme;
        self.title = "Transitions Report"
        self.author = "Do not distribute";

        # Set this value if you don't want to build the report
        self.buildme = True
        
    def myFirstPage(self, canvas, doc):
       
        canvas.saveState()
        
        canvas.setFont('Helvetica',14)
        canvas.drawString(4.0*inch, 11.4*inch, "%s"%(self.participant.username));
        #canvas.drawString(0.5*inch, 11.2*inch, "Gender: %s"%(self.gender));
        #canvas.drawString(0.5*inch, 11.0*inch, "DOB: %s"%(self.dob));
                
        #canvas.drawString(6.5*inch, 11.4*inch, self.title)
        #canvas.drawString(6.5*inch, 11.2*inch, self.author)

        canvas.setFont('Helvetica',8)
        #canvas.drawString(0.25*inch, 0.25*inch, "Page %d"%(doc.page))
        canvas.drawString(2.5*inch, 0.20*inch, u"\u00A9 2014 Institute for Systems Biology. All Rights Reserved.")
        
        canvas.restoreState()
        
    def myLaterPages(self, canvas, doc):
    
        canvas.saveState()
        
        canvas.setFont('Helvetica',14)
        canvas.drawString(4.0*inch, 11.4*inch, "%s"%(self.participant.username));
        #canvas.drawString(0.5*inch, 11.2*inch, "Gender: %s"%(self.gender));
        #canvas.drawString(0.5*inch, 11.0*inch, "DOB: %s"%(self.dob));
        
        #canvas.drawString(6.5*inch, 11.4*inch, self.title)
        #canvas.drawString(6.5*inch, 11.2*inch, self.author)

        canvas.setFont('Helvetica',8)
        canvas.drawString(7.75*inch, 0.25*inch, "%d"%(doc.page))
        canvas.drawString(2.5*inch, 0.25*inch, u"\u00A9 2014 Institute for Systems Biology. All Rights Reserved.")
        
        canvas.restoreState();

    def GetBounds(self, data, ranges):
        min = float("inf");
        max = float("-inf");
        
        for dataset in data:
            for value in dataset:
                if (value > max):
                    max = value;
                if (value < min):
                    min = value;
        
        # Get distance from 
        
        return (min, max);
        
    def LineGraph(self, story, dates, values, range):
    
        drawing = Drawing(400, 200)
        chart = HorizontalLineChart()
    
        chart.x = 30
        chart.y = 50
        chart.height = 125
        chart.width = 350
        chart.data = data
        catNames = catnames
        chart.categoryAxis.categoryNames = catNames
        chart.categoryAxis.labels.boxAnchor = 'n'
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = 200
        chart.valueAxis.valueStep = 25
        chart.lines[0].strokeWidth = 2
        chart.lines[0].symbol = makeMarker('FilledCircle') # added to make filled circles.
        chart.lines[1].strokeWidth = 1.5
        drawing.add(chart)
        
        # Drop the Drawing onto the page.
        story.append(drawing)
            
    def AddGraph(self, header, title, width=100):
    
        (dates, values, range) = self.participant.GetMeasurement(header);

        drawing = Drawing(150, 150)
        drawing.add(String(400, 500, title), name="title")
        chart = VerticalBarChart()

        # If there are not two values for each, then do not build
        if (values.size < 3):
            self.buildme = False;
            return None;

        if (np.isnan(values[0])) and (np.isnan(values[1]) and np.isnan(values[2])):
            print "%s is missing three rounds %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            return None

        """
        # Sanity check on the data
        if (values[0] == None):
            print "%s is missing first round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            return None
        if (np.isnan(values[0])):
            print "%s is missing first round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            return None
        if (values[1] == None):
            print "%s is missing second round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            self.buildme = False;
            return None
        if (np.isnan(values[1])):
            print "%s is missing second round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            self.buildme = False;
            return None
        if (values[2] == None):
            print "%s is missing third round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            self.buildme = False;
            return None
        if (np.isnan(values[2])):
            print "%s is missing third round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            self.buildme = False;
            return None
        """

        CHART_WIDTH=width;
        CHART_HEIGHT=100 
        
        min_value = range[0];
        mid_value = None;
        max_value = range[1];
        if (len(range)>2):
            mid_value = max_value;
            max_value = range[2];

        if (max_value == float("inf")):
            max_value = max(values) + max(values)*0.5;
        
        chart.height = CHART_HEIGHT;
        chart.width = CHART_WIDTH;
        chart.data = [values];
        chart.strokeColor = colors.black;
        chart.valueAxis.valueMin = 0;
        chart.valueAxis.valueMax = max(max_value, max(values)) + 0.75*(max_value-min_value);
        #chart.valueAxis.valueStep = round((range[1]-range[0]) / 5);
        chart.valueAxis.valueSteps = [round(x, 1) for x in range];
        chart.valueAxis.tickRight = CHART_WIDTH;
        chart.valueAxis.strokeWidth = 0.1;
        
        drawing.title.x = 20 + chart.width/2;
        drawing.title.y = 10 + chart.height + 5;
        drawing.title.textAnchor ='middle'
        drawing.title.fontSize = 10
        
        index = 0;
        for value in values:
            if (value < min_value):
                chart.bars[(0,index)].fillColor = colors.red;
            elif (not mid_value is None) and (value > mid_value) and (value <= max_value):
                chart.bars[(0,index)].fillColor = colors.yellow;
            elif (value > max_value):
                chart.bars[(0,index)].fillColor = colors.red;
            else:
                chart.bars[(0,index)].fillColor = colors.green;
            index += 1;
        
        chart.categoryAxis.labels.boxAnchor = 'ne'
        chart.categoryAxis.labels.fontSize = 8;
        chart.categoryAxis.labels.dx = 12;
        chart.categoryAxis.labels.dy = -2;
        chart.categoryAxis.labels.angle = 0;
        chart.categoryAxis.categoryNames = ["Draw"+str(x) for x in dates];

        chart.bars.strokeWidth = 1.0;
        
        chart.barLabels.fontName = "Helvetica"
        chart.barLabels.fontSize = 10
        chart.barLabels.fillColor = colors.black;
        chart.barLabelFormat = '%.1f'
        chart.barLabels.nudge = 7
        
        drawing.add(chart);
        return drawing;

    def AddPattern(self, header, title):

        CHART_WIDTH = 75;
        CHART_HEIGHT = 100;

        (dates, values, range) = self.participant.GetMeasurement(header);

        drawing = Drawing(150, 150)

        # If there are not two values for each, then do not build
        if (values.size < 2):
            self.buildme = False;
            return None;

        # Sanity check on the data
        if (values[0] == None):
            print "%s is missing first round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            return None
        if (values[1] == None):
            print "%s is missing second round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            self.buildme = False;
            return None

        drawing.add(String(400, 500, title), name="title")
        drawing.title.x = 20 + CHART_WIDTH/2;
        drawing.title.y = 10 + CHART_HEIGHT + 5;
        drawing.title.textAnchor = 'middle';
        drawing.title.fontSize = 10;

        if (values[0] == 0):
            pattern0 = 'A'
        else:
            pattern0 = 'B'

        drawing.add(String(400, 500, pattern0), name="pattern1")
        drawing.pattern1.x = 20+CHART_WIDTH*0.15;
        drawing.pattern1.y = 10+CHART_HEIGHT*0.75;
        drawing.pattern1.textAnchor = 'middle';
        drawing.pattern1.fontSize = 32;

        if (values[0] == range[0]):
            drawing.pattern1.fillColor = colors.green;
        else:
            drawing.pattern1.fillColor = colors.red;

        drawing.add(String(400, 500, "Draw"+str(dates[0])), name="range1")
        drawing.range1.x = 20+CHART_WIDTH*0.15;
        drawing.range1.y = 10+CHART_HEIGHT*0.6;
        drawing.range1.textAnchor = 'middle';
        drawing.range1.fontSize = 8;

        if (values[1] == 0):
            pattern1 = 'A'
        else:
            pattern1 = 'B'

        drawing.add(String(400, 500, pattern1), name="pattern2")
        drawing.pattern2.x = 20+CHART_WIDTH*0.80;
        drawing.pattern2.y = 10+CHART_HEIGHT*0.75;
        drawing.pattern2.textAnchor = 'middle';
        drawing.pattern2.fontSize = 32;

        if (values[1] == range[1]):
            drawing.pattern2.fillColor = colors.green;
        else:
            drawing.pattern2.fillColor = colors.red;

        drawing.add(String(400, 500, "Draw"+str(dates[1])), name="range2")
        drawing.range2.x = 20+CHART_WIDTH*0.80;
        drawing.range2.y = 10+CHART_HEIGHT*0.6;
        drawing.range2.textAnchor = 'middle';
        drawing.range2.fontSize = 8;

        # Drop the Drawing onto the page.
        return drawing;

    """
    def AddPattern(self, header, title):
    
        CHART_WIDTH = 75;
        CHART_HEIGHT = 100;
    
        (dates, values, range) = self.participant.GetMeasurement(header);

        drawing = Drawing(150, 150)

        # If there are not two values for each, then do not build
        if (values.size < 2):
            self.buildme = False;
            return None;

        # Sanity check on the data
        if (values[0] == None):
            print "%s is missing first round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            return None
        if (values[1] == None):
            print "%s is missing second round %s: %s"%(self.participant.username, header, ','.join([str(x) for x in values]))
            self.buildme = False;
            return None

        drawing.add(String(400, 500, title), name="title")
        drawing.title.x = 20 + CHART_WIDTH/2;
        drawing.title.y = 10 + CHART_HEIGHT + 5;
        drawing.title.textAnchor = 'middle';
        drawing.title.fontSize = 10;

        if (values[0] != 0):
            drawing.add(String(400, 500, values[0]), name="pattern1")
            drawing.pattern1.x = 20+CHART_WIDTH*0.15;
            drawing.pattern1.y = 10+CHART_HEIGHT*0.75;
            drawing.pattern1.textAnchor = 'middle';
            drawing.pattern1.fontSize = 32;

            if (values[0] == range[0]):
                drawing.pattern1.fillColor = colors.green;
            else:
                drawing.pattern1.fillColor = colors.red;

            drawing.add(String(400, 500, "Draw"+str(dates[0])), name="range1")
            drawing.range1.x = 20+CHART_WIDTH*0.15;
            drawing.range1.y = 10+CHART_HEIGHT*0.6;
            drawing.range1.textAnchor = 'middle';
            drawing.range1.fontSize = 8;

        if (values[1] != 0):

            drawing.add(String(400, 500, values[1]), name="pattern2")
            drawing.pattern2.x = 20+CHART_WIDTH*0.80;
            drawing.pattern2.y = 10+CHART_HEIGHT*0.75;
            drawing.pattern2.textAnchor = 'middle';
            drawing.pattern2.fontSize = 32;

            if (values[1] == range[1]):
                drawing.pattern2.fillColor = colors.green;
            else:
                drawing.pattern2.fillColor = colors.red;

            drawing.add(String(400, 500, "Draw"+str(dates[1])), name="range2")
            drawing.range2.x = 20+CHART_WIDTH*0.80;
            drawing.range2.y = 10+CHART_HEIGHT*0.6;
            drawing.range2.textAnchor = 'middle';
            drawing.range2.fontSize = 8;
    
        # Drop the Drawing onto the page.
        return drawing;
    """
        
    def LogoHeader(self, story, src, blurb, subblurb=""):
    
        # Add logo
        #img = Image2(src, 75, 75)
        #img.hAlign = "CENTER";
        
        count = 0;
        variant_table = [];
        variant_style = [];
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'TOP'));
        variant_style.append(('ALIGN',(0,0),(-1,-1),'CENTER'));
 
        variant_table.append([Paragraph("", h1), Paragraph(blurb, h0)]);
        variant_table.append([Paragraph("", h2), Paragraph("", h2)]);  
        variant_table.append([Paragraph("", h2), Paragraph("", h2)]);     
        variant_table.append([Paragraph("", h2), Paragraph(subblurb, h2)]);
            
        variant_style.append(('VALIGN', (0,count), (-1,count), 'MIDDLE'));
        variant_style.append(('ALIGN',(0,count),(-1,count),'CENTER'));

        table = Table(variant_table, [0, 450], hAlign='LEFT', style=variant_style)
        story.append(table)   
        
    def DrawingBlurb(self, story, drawing, blurb):
            
        count = 0;
        variant_table = [];
        variant_style = [];
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'TOP'));
        variant_style.append(('ALIGN',(0,0),(-1,-1),'CENTER'));
        
        data = [Paragraph("", h2), Paragraph(blurb, h2), Paragraph("", h2)];
        ranges = [50, 290, 40];
        for d in drawing:
            data.append(d);
            ranges.append(250/len(drawing));
 
        variant_table.append(data)
            
        variant_style.append(('VALIGN', (0,count), (-1,count), 'MIDDLE'));
        variant_style.append(('ALIGN',(0,count),(-1,count),'CENTER'));

        table = Table(variant_table, ranges, hAlign='CENTER', style=variant_style)
        story.append(table)        

    def go(self, force=False):
     
        story = [];

        # Add logo
        src = './images/transition_cover1.png' 
        img = Image2(src, 625, 795)
        img.hAlign = "CENTER";
        story.append(img)
                
        story.append(PageBreak())
  
        story.append(Spacer(1,0.5*inch))
        self.LogoHeader(story, './images/cardiovascular.png', "<font color='#002060'><strong>CARDIOVASCULAR HEALTH</strong></font>", "The following selected measurements are related to your cardiovascular health.");
        #story.append(MCLine(6.0*inch));
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>TOTAL CHOLESTEROL</strong></font> is a sum of your blood's cholesterol content. Cholesterol \
        is an essential molecule needed for the integrity of all our cells. High concentrations \
        of cholesterol found in the blood have been associated with increased risk of heart disease \
        because these molecules stick to the arteries and cause buildups (plaques). If your total \
        cholesterol levels are high it is important to know your LDL cholesterol and HDL cholesterol \
        levels before deciding on your action.";
        
        drawing = self.AddGraph('TOTAL_CHOLESTEROL', 'Total Cholesterol');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>TOTAL LOW-DENSITY LIPOPROTEIN (LDL)</strong></font> cholesterol is often called the 'bad' \
        cholesterol as it can carry fat molecules into artery walls leading to fat build up and \
        inflammation. Accumulation of fatty deposits in your arteries (atherosclerosis) increases \
        your risk for cardiovascular disease.";
        
        drawing = self.AddGraph('LDL_CHOLESTEROL', 'LDL-Cholesterol');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>TRIGLYCERIDES</strong></font> are a type of fat in the blood that your body uses for energy. \
        Triglycerides are the main constituents of vegetable oil and animal fat. High triglyceride \
        levels may contribute to hardening of the arteries or thickening of the artery walls - \
        increasing your risk for heart disease and metabolic syndrome.";
        
        drawing = self.AddGraph('TRIGLYCERIDES', 'Triglycerides');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "The <font color='#db881e'><strong>LDL PATTERN</strong></font> reflects the size and density of your LDL particles which has been shown \
        to be much more indicative of your heart health than total cholesterol or LDL numbers.<br/><br/>\
        - <font color='#db881e'><strong>LDL Pattern 'A'</strong></font> means your particles are big and fluffy, which helps protect against heart disease. <br/><br/>\
        - <font color='#db881e'><strong>LDL Pattern 'B'</strong></font> refers to a small and dense particle pattern.  These small, dense particles \
        can easily lodge into your arteries and create plaques and are also more likely to cause inflammation.";
        
        story.append(Spacer(1,0.4*inch));
        drawing = self.AddPattern('LDL_PATTERN_QUEST', 'LDL Pattern');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        story.append(PageBreak())
        
        story.append(Spacer(1,0.5*inch));  
        self.LogoHeader(story, './images/nutrients.png', "<font color='#002060'><strong>NUTRITIONAL STATUS</strong></font>", "The following selected measurements are related to your nutritional health.");
        #story.append(MCLine(6.0*inch));
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>FERRITIN</strong></font> is a protein that stores iron, so measuring blood ferritin is an indirect \
        test of total body iron stores. Low values can indicate anemia, while high values can reflect \
        too much iron in the body, which can lead to a multitude of medical issues due to build-up of \
        iron in the organs.";
        
        drawing = self.AddGraph('FERRITIN_QUEST', 'Ferritin');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>VITAMIN D</strong></font> is a crucial nutrient for multiple body systems. Keeping vitamin D \
        in the normal range is important for maintaining bone health. Low levels of vitamin D \
        have been directly implicated to immune health, metabolic health, cognitive abilities, and many \
        other conditions. Vitamin D is produced by the body in response to sunlight exposure, however \
        few people in developed countries get enough sun to produce adequate amounts. There are few \
        foods that naturally contain vitamin D - these include oily fish, fish liver oil and egg yolks.";
        
        drawing = self.AddGraph('VITAMIN_D', 'Vitamin D');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>ZINC</strong></font> is a mineral that is an important nutritional cofactor in many body systems. \
        Maintaining optimal levels of zinc is crucial for immune health, skin health, male reproductive \
        health, DNA synthesis, wound healing and sense of taste and smell. Foods that are rich in zinc \
        include red meat, poultry, shellfish, spinach, mushrooms, and tofu.";
        
        drawing = self.AddGraph('GLUTATHIONE', 'Glutathione');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>BODY MASS INDEX (BMI)</strong></font> is a number calculated from a person's weight and height. \
        Although an indirect measure, for most people BMI provides a reliable indicator of health risks \
        related to excess body fat.  A BMI over 25 is considered overweight and a BMI over 30 is considered \
        obese. Health risks (e.g. heart disease, Type 2 diabetes, gall bladder disease, some cancers) tend \
        to increase linearly with increasing BMI.";
        
        drawing = self.AddGraph('BODY_MASS_INDEX', 'Body Mass Index');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        story.append(PageBreak())
        
        story.append(Spacer(1,0.5*inch));  
        self.LogoHeader(story, './images/inflammation.png', "<font color='#002060'><strong>INFLAMMATION</strong></font>", "Inflammation is the common theme of most chronic age-related diseases. Uncontrolled systemic inflammation places you at risk for many degenerative diseases like heart disease, stroke, Type 2 diabetes and dementia. The following measurements are markers for chronic inflammation in your body.");
        #story.append(MCLine(6.0*inch));
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>Hs-CRP</strong></font> is a protein produced in the liver that increases in abundance in response \
        to inflammation with in the body. Its biological role is to bind and remove dead and dying cells. \
        In large epidemiologic studies, elevated levels of hs-CRP have been shown to be a strong indicator \
        of cardiovascular disease and have been implicated in chronic diseases, cancer and immune dysfunction.";
        
        drawing = self.AddGraph('HS_CRP', 'hs-CRP');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>IL-6, IL-8, AND TNF-ALPHA</strong></font> are all small proteins known as cytokines that act as signaling \
        molecules to send messages through the body. All three act to stimulate the immune system to create \
        an inflammatory response.<br/><br/> At healthy levels theses proteins help the body fight viral infections, \
        bacterial invasions, and cancerous cells. Extended signaling from these small proteins lead to \
        chronic and harmful inflammation within the body.";
        
        drawing1 = self.AddGraph('INTERLEUKIN_IL_6', 'IL-6', 50);
        drawing2 = self.AddGraph('INTERLEUKIN_IL_8', 'IL-8', 50);
        drawing3 = self.AddGraph('TNFALPHA', 'TNF-'+u'\u03B1', 50);

        final = [];
        if (not drawing1 is None):
            final.append(drawing1)
        if (not drawing2 is None):
            final.append(drawing2)
        if (not drawing3 is None):
            final.append(drawing3)

        if (len(final)>0):
            self.DrawingBlurb(story, final, blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>PAI-1</strong></font> is a protein associated with fibrosis - a condition that causes the excessive \
        formation of connective tissue in organs. Fibrosis typically occurs as a result of inflammation \
        in the body.  Elevated levels of PAI-1 are found in cardiovascular disease, Type 2 diabetes and \
        metabolic syndrome.";
        
        drawing = self.AddGraph('PAI_1', 'PAI-1');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "Combined we can calculate your <font color='#db881e'><strong>AVERAGE INFLAMMATION SCORE</strong></font> based on the significance of \
        each measurement.";
        
        drawing = self.AddGraph('AVERAGE_INFLAMMATION_SCORE', 'Average Inflammation');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        story.append(PageBreak())
        
        story.append(Spacer(1,0.5*inch));  
        self.LogoHeader(story, './images/prediabetes.png', "<font color='#002060'><strong>DIABETES RISK</strong></font>", "The following selected measurements reflect your risk for developing \
Type 2 diabetes. If you already have diabetes, these measurements \
can reflect your risk of developing diabetes complications. If you have \
pre-diabetes (higher than normal blood sugar, but not high enough to \
diagnose diabetes), your chances of developing diabetes in <10 years are \
high and the long-term damage of diabetes - especially to your heart and \
circulatory system - may already be starting.");
        #story.append(MCLine(6.0*inch));
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>GLUCOSE</strong></font> is the main source of energy used by the body. Glucose comes from \
        most dietary carbohydrates and is absorbed directly into the blood stream after digestion. \
        Glucose in the blood stream after at least 8 hours of fasting indicates the amount of glucose \
        not taken up by cells for an energy source. Elevated levels of fasting glucose are indicative \
        of possible pre-diabetes or diabetes.";
        
        drawing = self.AddGraph('GLUCOSE', 'Glucose');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>INSULIN</strong></font> is a hormone that helps your body's cells use glucose by promoting its \
        absorption from the blood stream to the skeletal muscles for energy or fat tissue for storage. \
        Insulin prevents the accumulation of glucose in the blood stream, which can have toxic effects. \
        Elevated insulin is often associated with excess body weight and typically indicates insulin \
        resistance by the cells.";
        
        drawing = self.AddGraph('INSULIN', 'Insulin');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>HbA1c</strong></font> reflects your average blood glucose (sugar) level for the past two to three \
        months. It measures the percentage of blood sugar attached to hemoglobin, the oxygen-carrying \
        protein in red blood cells. The higher your blood sugar levels, the more hemoglobin you'll have \
        with sugar attached and the higher your HbA1c.";
        
        drawing = self.AddGraph('HEMOGLOBIN_A1C', 'HbA1c');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);
        
        # Get the values from the participant for a particular metabolite
        blurb = "<font color='#db881e'><strong>HOMA</strong></font> score is a calculation of your insulin resistance. Insulin resistance \
        is a condition in which the body produces insulin but does not use it effectively. \
        When people have insulin resistance, glucose can build up in the blood stream instead \
        of being absorbed by the cells, leading to type 2 diabetes or prediabetes.";
        
        drawing = self.AddGraph('HOMA_IR', 'HOMA');
        if (not drawing is None):
            self.DrawingBlurb(story, [drawing], blurb);

        output_dir = './results';
        output_filename = output_dir + '/' + self.participant.username + '.comparisons.2.pdf';

        # Only build the report if I haven't found any issues with the data
        if (self.buildme or force):
            doc_template_args = self.theme.doc_template_args()
            doc = SimpleDocTemplate(output_filename, title=self.title, author=self.author, **doc_template_args)
            doc.build(story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)
        else:
            print "Skipping report for %s"%(self.participant.username);
        
class GeneticsReport(object):

    def __init__(self, participant):

        self.participant = participant;

        self.theme = MyTheme;
        self.title = "Beta Genetics Report"
        self.author = "Do not distribute";
        
        # Colors
        self.header = colors.Color(0.5, 0.5, 0.5, alpha=0.5);
        self.no_effect = colors.Color(0.7, 0.7, 0.7, alpha=0.1);
        
        self.strong_effect_protective = colors.Color(0.0, 1.0, 0.0, alpha=0.8);
        self.weak_effect_protective = colors.Color(0.0, 1.0, 0.0, alpha=0.4);
        
        self.strong_effect_risk = colors.Color(1.0, 0.0, 0.0, alpha=0.5);
        self.weak_effect_risk = colors.Color(1.0, 1.0, 0.0, alpha=0.5);
        
        self.bad_variant = colors.Color(0.0, 0.0, 0.0, alpha=1.0);

    def myFirstPage(self, canvas, doc):
       
        canvas.saveState()
        
        canvas.setFont('Helvetica',10)
        canvas.drawString(0.5*inch, 11.4*inch, "Name: %s"%(self.participant.username));
        #canvas.drawString(0.5*inch, 11.2*inch, "Gender: %s"%(self.gender));
        #canvas.drawString(0.5*inch, 11.0*inch, "DOB: %s"%(self.dob));
        
        canvas.drawString(6.5*inch, 11.4*inch, self.title)
        canvas.drawString(6.5*inch, 11.2*inch, self.author)

        canvas.setFont('Helvetica',10)
        canvas.drawString(0.25*inch, 0.25*inch, "Page %d"%(doc.page))
        
        canvas.restoreState()
        
    def myLaterPages(self, canvas, doc):
    
        canvas.saveState()
        
        canvas.setFont('Helvetica',10)
        canvas.drawString(0.5*inch, 11.4*inch, "Name: %s"%(self.participant.username));
        #canvas.drawString(0.5*inch, 11.2*inch, "Gender: %s"%(self.gender));
        #canvas.drawString(0.5*inch, 11.0*inch, "DOB: %s"%(self.dob));
        
        canvas.drawString(6.5*inch, 11.4*inch, self.title)
        canvas.drawString(6.5*inch, 11.2*inch, self.author)

        canvas.setFont('Helvetica',10)
        canvas.drawString(0.25*inch, 0.25*inch, "Page %d"%(doc.page))
        
        canvas.restoreState()
        
    def Legend(self, story):
    
        variant_table = [];
        variant_style = [];
        
        variant_table.append(["Legend for color codes"]);
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'MIDDLE'));
        variant_style.append(('ALIGN',(0,0),(-1,-1),'CENTER'));
        variant_style.append(('LINEABOVE',(0,0),(-1,0),0.5,colors.black));
        variant_style.append(('LINEBELOW',(0,0),(-1,0),1.0,colors.black));
        variant_style.append(('LINEBEFORE',(0,0),(-1,0),0.5,colors.black));
        variant_style.append(('LINEAFTER',(0,0),(-1,0),0.5,colors.black));
        variant_style.append(('BACKGROUND', (0, 0), (-1, 0), self.header))
        
        variant_table.append(['You do not have a form of this variant that exerts a positive or negative effect'])
        variant_style.append(('BACKGROUND', (0, 1), (-1, 1), self.no_effect));
        variant_table.append(['Your genotype for this variant is associated with a protective effect'])
        variant_style.append(('BACKGROUND', (0, 2), (-1, 2), self.strong_effect_protective));
        variant_table.append(['Your genotype for this variant is associated with a weak protective effect'])
        variant_style.append(('BACKGROUND', (0, 3), (-1, 3), self.weak_effect_protective));
        variant_table.append(['Your genotype for this variant is associated with a weak risk'])
        variant_style.append(('BACKGROUND', (0, 4), (-1, 4), self.weak_effect_risk));
        variant_table.append(['Your genotype for this variant is associated with a risk'])
        variant_style.append(('BACKGROUND', (0, 5), (-1, 5), self.strong_effect_risk));
        
        table = Table(variant_table, [500], hAlign='CENTER', style=variant_style)
        story.append(table);
        
    def ProcessTrait(self, story, trait):
    
        trait = self.participant.ProcessActionable(trait);

        variant_table = [['Gene', 'Identifier', 'Allele', 'You', 'Description']] # this is the header row
        variant_style = [];
        variant_style.append(('VALIGN', (0,0), (-1,-1), 'MIDDLE'));
        variant_style.append(('ALIGN',(0,0),(-1,-1),'CENTER'));
        variant_style.append(('LINEABOVE',(0,0),(-1,0),0.5,colors.black));
        variant_style.append(('LINEBELOW',(0,0),(-1,0),1.0,colors.black));
        variant_style.append(('LINEBEFORE',(0,0),(-1,0),0.5,colors.black));
        variant_style.append(('LINEAFTER',(0,0),(-1,0),0.5,colors.black));
        variant_style.append(('BACKGROUND', (0, 0), (-1, 0), self.header))
     
        count = 1;
        for key in trait.variants.keys():
            variant = trait.variants[key];
            variant_table.append([Paragraph(variant.reported_genes, h2), variant.dbsnp, variant.risk_allele, variant.genotype, Paragraph(variant.notes, h2)])
            
            variant_style.append(('VALIGN', (0,count), (-1,count), 'MIDDLE'));
            variant_style.append(('ALIGN',(0,count),(-1,count),'CENTER'));
            variant_style.append(('LINEABOVE',(0,count),(-1,count),0.5,colors.black));
            variant_style.append(('LINEBELOW',(0,count),(-1,count),0.5,colors.black));
            variant_style.append(('LINEBEFORE',(0,count),(-1,count),0.5,colors.black));
            variant_style.append(('LINEAFTER',(0,count),(-1,count),0.5,colors.black));
                   
            # Based on the effect value, set the colors
            if (variant.effect == 2):
            
                # If the variant is protective
                if (variant.risk_type == "protective"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.strong_effect_protective));
                elif (variant.risk_type == "risk"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.strong_effect_risk));
                else:
                    print "Warning, unknown risk value: %s"%(variant.risk_type);
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.bad_variant));

            elif (variant.effect == 1):
            
                # If the variant is protective
                if (variant.risk_type == "protective"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.weak_effect_protective));
                elif (variant.risk_type == "risk"):
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.weak_effect_risk));
                else:
                    print "Warning, unknown risk value: %s"%(variant.risk_type);
                    variant_style.append(('BACKGROUND', (0, count), (-1, count), self.bad_variant));            
            
            else:
                variant_style.append(('BACKGROUND', (0, count), (-1, count), self.no_effect));
            count += 1;

        table = Table(variant_table, [75, 60, 30, 25, 350], hAlign='CENTER', style=variant_style)
        story.append(table) 

    def go(self):
     
        #if (not self.generate):
        #    print "*** Skipping %s ***"%(self.id);
        #    return;

        story = [];
        
        story.append(Spacer(1,0.5*inch));
        
        story.append(Paragraph("This is your personalized metabolism, diet, nutrition \
and exercise report based on your analyzed whole genome sequence. If you are thinking about starting a weight loss program or just \
maintaining a healthy diet, the goal of this report is to give you information about yourself that may \
help you modify your behavior. While this report is based on the most current \
scientific research, information about how genetics interact with diet and exercise is \
constantly evolving. We recommend you discuss with your doctor any changes to lifestyle or diet. Note that \
this report is still in beta testing and has not been reviewed by a medical geneticist.", h2))

        story.append(Spacer(1,0.25*inch));
        
        self.Legend(story);
        
        # Add logo
        #src = './images/pioneerLogo_ISBLogo.png' 
        #img = Image(src, 450, 75)
        #img.hAlign = "CENTER";
        #story.append(img)
        
        story.append(Spacer(1,0.25*inch));
        
        trait = "Obesity/Overweight";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Obesity is a complex disorder involving an excessive amount of body fat. \
        Obesity isn't just a cosmetic concern. It increases your risk of diseases and health problems such as heart disease, \
        diabetes and high blood pressure. Studies have identified many genes that influence obesity risk. We have chosen \
        some of the most significant genes for this report, involved in fat absorption and metabolism.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1,0.25*inch));
        
        trait = "Insulin Resistance/Type 2 Diabetes";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Type 2 diabetes, once known as adult-onset or noninsulin-dependent diabetes, \
        is a chronic condition that affects the way your body metabolizes sugar (glucose), your body's important \
        source of fuel. With type 2 diabetes, your body either resists the effects of insulin - a hormone that \
        regulates the movement of sugar into your cells - or doesn't produce enough insulin to maintain a normal glucose level.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(PageBreak())
        story.append(Spacer(1,0.5*inch));
        
        trait = "Snacking";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Snacking can be a healthy or unhealthy behavior. Snacking on balanced foods, \
containing healthy fats, lean protein, fiber and low glycemic index carbohydrates, \
in small portions, throughout the day can help control hunger cravings and reduce \
total caloric intake, while snacking on junk food can have negative health effects. \
If you have a predisposition for snacking, you may want to curtail the negative effects by choosing healthy \
snacks, eating slowly and reducing the size or calories of snacks.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1,0.25*inch));
        
        trait = "Satiety/Feeling Full";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Satiety can be described as the feeling of fullness after you eat. The FTO (fat mass \
and obesity-associated) gene is known to be an important factor that predisposes \
a person to a healthy or unhealthy level of body weight. People who \
experience difficulty in feeling full tend to eat more without feeling satisfied. \
To help manage this outcome, you could increase the amount of fiber in your diet \
and balance meals and snacks throughout the day. Examples of foods high in \
fiber include whole wheat bread, oatmeal, barley, lentils, black beans, artichokes, \
raspberries, and peas.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1,0.25*inch));
        
        trait = "Cholesterol";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Low-density lipoprotein (LDL) is the type of cholesterol that can become dangerous \
if you have too much of it. Like gunk clogging up your kitchen drain, LDL \
cholesterol can form plaque and build up in the walls of your arteries. This can \
make your arteries narrower and less flexible, putting you at risk for conditions like \
a heart attack or stroke. High-density lipoprotein (HDL) cholesterol is known as good cholesterol, because \
high levels of HDL cholesterol seem to protect against heart attack, while low \
levels of HDL cholesterol (less than 40 mg/dL) increase the risk of heart disease. \
While multiple mechanisms are known to account for this, the major one is thought \
to be the role of HDL in transporting excess cholesterol away from the arteries and \
back to the liver, where it is passed from the body", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
 
        story.append(PageBreak()) 
        story.append(Spacer(1,0.5*inch));
        
        trait = "Oxidative Stress";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Your body constantly reacts with oxygen as you breathe and your cells produce energy. \
        As a consequence of this activity, highly reactive molecules are produced within our cells known as free radicals \
and oxidative stress occurs. When our protein-controlled anti-oxident response doesn't keep up, oxidative stress causes damage \
that has been implicated in the cause of many diseases, as well as impacting the body's aging process.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1,0.25*inch));
        
        trait = "Vitamin D";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Vitamin D is important for the absorption and utilization of calcium, which is \
beneficial for maintaining good bone health. Exposure to sunlight is an important \
determinant of a person's vitamin D level, since there are few natural dietary \
sources of vitamin D. While sunscreen use blocks skin production of vitamin D, \
excessive sun exposure is a risk factor for skin cancer and related conditions, and \
is not recommended. Dietary sources of vitamin D include some fatty fish, fish \
liver oils, and milk or cereals fortified with vitamin D. The recommended intake of \
vitamin D for most adults is 600 IUs per day. About 115 IUs of vitamin D is found in \
one cup of vitamin D-fortified, non-fat, fluid milk.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));
        
        trait = "Vitamin B6";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Vitamin B6, also called pyridoxine, helps your body's neurological system \
to function properly, promotes red blood cell health, and is involved in sugar \
metabolism. Vitamin B6 is found naturally in many foods, including beans, whole grains, meat, eggs and fish. Most \
people receive sufficient amounts of vitamin B6 from a healthy diet, and B6 \
deficiency is rare in the United States.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch));
        
        trait = "Vitamin B12";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Vitamin B12 plays an important role in how your brain and nervous system \
function. It helps to keep red blood cells healthy and is a critical component for \
synthesis and regulation of your DNA. Vitamin B12 is found naturally in foods \
of animal origin including meat, fish, poultry, eggs and milk products. A healthy \
diet will typically provide sufficient B12, although vegetarians, vegans, older \
people, and those with problems absorbing B12 due to digestive system disorders \
may be deficient. Symptoms of vitamin B12 deficiency can vary, but may include \
fatigue, weakness, bloating, or numbness and tingling in the hands and feet. The \
recommended intake for adults is 2.4 micrograms per day.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));
        
        trait = "Vitamin C";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Vitamin C, or L-ascorbic acid, must be acquired from dietary sources, as humans \
are unable to synthesize it. Some dietary sources of vitamin C include lemons, \
oranges, red peppers, watermelons, strawberries and citrus juices or juices \
fortified with vitamin C. While a severe deficiency of vitamin C ultimately leads \
to scurvy, variations in vitamin C levels have also been associated with a wide \
range of chronic complex diseases, such as atherosclerosis, type 2 diabetes and \
cancer. These associations are thought to result from a contribution of vitamin \
C as an antioxidant, as well as its role in the synthesis of collagen and various \
hormones. After ingestion, the vitamin C in one's diet gets transported across the \
cell membrane via transport proteins, one of which is SLC23A1", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));
        
        trait = "Folate";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
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
day.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch));
        
        trait = "Vitamin E";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Vitamin E is a group of eight antioxidant molecules, of which alpha-tocopherol is \
the most abundant in the body. Vitamin E functions to promote a strong immune \
system and regulates other metabolic processes. The recommended intake \
of vitamin E for most adults is 15 milligrams per day. Note that synthetic varieties \
of vitamin E found in some fortified foods and supplements are less biologically \
active. Sources of naturally-occurring vitamin E in foods are vegetable oils, green \
leafy vegetables, eggs and nuts. Most adults normally do not \
take in adequate amounts of vitamin E on a daily basis, so keeping an eye on \
your vitamin E intake is good advice for anyone.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));

        trait = "Iron";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Hereditary hemochromatosis causes your body to absorb too much iron from \
        the food you eat. The excess iron is stored in your organs, especially your liver, heart and pancreas. The excess \
        iron can poison these organs, leading to life-threatening conditions such as cancer, heart \
        arrhythmias and cirrhosis. Many people inherit the faulty genes that cause hemochromatosis - it is the most \
        common genetic disease in Caucasians. But only a minority of those with the genes develop serious \
        problems. Hemochromatosis is more likely to be serious in men. Signs and symptoms of hereditary hemochromatosis \
        usually appear in midlife. Iron can be dropped to safe levels by regularly removing blood from your body.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));

        trait = "Lactose";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
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
                    can be high in calories, fat, or both.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));

        trait = "Sweet tooth";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Craving sweet foods is sometimes described as having a 'sweet tooth.' If your genotype \
shows an increased likelihood to eat lots of sweets, try choosing fruit as a healthy \
sweet alternative to sugary foods or soda. Be sure to follow your diet as some \
diet plans, such as the low carbohydrate diets, significantly limit the amount \
of sugar you can eat. Sweet foods can include healthy foods, such as fruits, or \
unhealthy foods like candy and sweetened beverages.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch));

        trait = "Caffeine";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
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
effects for you.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));
        
        trait = "Bitter taste";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("People taste things differently. Variations in the \
TAS2R38 gene are associated with different levels \
of sensitivity to a chemical called PTC \
which produces a strong bitter taste. A person described as a 'taster' \
may be more sensitive to bitter flavors found in \
foods, such as grapefruit, coffee, dark chocolate and \
cruciferous vegetables, such as Brussels sprouts, \
cabbage and kale. If you are a 'taster', you should make \
an extra effort to incorporate green leafy vegetables into your diet, \
as you may be initially inclined to avoid them.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));
        
        trait = "Athletic performance - Endurance";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Endurance training is generally used to describe exercise that is done for a longer \
duration with moderate intensity. Most people can benefit from a combination of \
endurance, high intensity and resistance exercises. Some people have genetic \
markers that are associated with increased endurance performance.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));

        trait = "Athletic performance - Strength";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("Strength training can be described as exercises that incorporate the use of \
opposing forces to build muscle. Certain variants have been associated with increased muscular strength.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
    
        story.append(Spacer(1, 0.25*inch));
        
        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch));
    
        trait = "Response to exercise";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("High blood pressure, also known as hypertension, is a common health issue. It \
has been estimated that a majority of people will have hypertension at some time \
in their lives. A genetic variant in the EDN1 gene has been shown to increase the \
likelihood of hypertension in people who were low in cardiorespiratory fitness, \
which refers to the ability of the heart and lungs to provide muscles with oxygen \
for physical activity. This genetic variant did not show an effect in people who \
were high in cardiorespiratory fitness.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));
    
        trait = "Exercise injury";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("The Achilles tendon connects your calf muscles to \
your heel bone. Tendinopathy describes either the \
inflammation or tiny tears to the tendon. People \
who play sports and runners who place stress on \
the Achilles tendon have the greatest likelihood \
of tendinopathy. Certain genotypes \
may be more injury-prone, while other genotypes \
have a typical likelihood of developing Achilles \
tendinopathy.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        story.append(Spacer(1, 0.25*inch));
    
        trait = "Longevity";
        story.append(Paragraph(trait, h1));
        story.append(Spacer(1,5));
        story.append(MCLine(7.3*inch));
        story.append(Spacer(1,5));
        story.append(Paragraph("While it is the subject of much research, scientists have \
        not identified the gene 'for' longevity. It is much more likely that longevity is associated \
        with many genes and associated variants, each of which contributes a small probability. However, a few \
        genes have been associated with particularly long-lived individuals. Having these variants does not \
        guarantee a long life any more than not having them guarantees a short one.", h2));
        story.append(Spacer(1,5));
        self.ProcessTrait(story, trait);
        
        # Begin page 4;
        #story.append(PageBreak())
        #story.append(Paragraph('Last heading', h1))
        
        output_dir = './results';
        output_filename = output_dir + '/' + self.participant.username + '.report.pdf';
        
        doc_template_args = self.theme.doc_template_args()
        doc = SimpleDocTemplate(output_filename, title=self.title, author=self.author, **doc_template_args)
        doc.build(story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)

