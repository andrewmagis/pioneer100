

# System imports
from datetime import date, datetime, timedelta as td
import logging

import numpy as np
import scipy
import math, re
import pandas, pandas.io

# Codebase imports
from p100.errors import MyError
import time

l_logger = logging.getLogger("p100.drugs.rxtools")

import requests
from bs4 import BeautifulSoup
import json

def get_rxNormID( drug_name ):
    """
    Returns the rxNormID from the nih database
    
    """

    r = requests.get( 'http://rxnav.nlm.nih.gov/REST/rxcui',
            params={'name':drug_name} )
    l_logger.debug( "request for rxnormid to [%s], with response status[%i:'%s']" % (
        r.url, r.status_code, r.reason) )
    if r.status_code == 200:
        bs = BeautifulSoup(r.text, "xml")
        try:
            return int( bs.rxnormId.text ) 
        except:
            l_logger.error("Request to [%s] given as [%s]" % (r.url,
                r.text) )
            l_logger.exception( "Error attempting to in response fromNIH")
    return None#no valid response

def get_rxClass( rxNormID, classtype=None, raw=False ):
    """
       Valid classtypes: 
            "classTypeList": {
                "classType": [
                    "ATC1-4",
                    "CHEM",
                    "DISEASE",
                    "EPC",
                    "MESHPA",
                    "MOA",
                    "PE",
                    "PK"
                ]
            }
    see:http://rxnav.nlm.nih.gov/RxClassAPIREST.html#uLink=RxClass_REST_getClassTypes
    """
    def massage( result ):
        """
        Massages the result into a useful dict
        """
        x = result
        return {
                    k:v for k,v in 
                    list(x['rxclassMinConceptItem'].iteritems()) +
                    [('relaSource', x['relaSource']),
                        ('rela', x['rela'])]
               }

    r = requests.get('http://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json', 
            params={ 'rxcui' : rxNormID })
    l_logger.debug( "request for rxnormid to [%s], with response status[%i:'%s']" % (
        r.url, r.status_code, r.reason) )

    if r.status_code == 200:
        #bs = BeautifulSoup(r.text, "xml")
        try:
            result = r.json()
            if raw:
                return result
            if classtype:
                return [massage(x) for x in
                        result["rxclassDrugInfoList"]["rxclassDrugInfo"]
                        if x['rxclassMinConceptItem']['classType'] ==
                        classtype]
            else:
                return [massage(x) for x in
                        result["rxclassDrugInfoList"]["rxclassDrugInfo"]]
        except:
            l_logger.error("Request to [%s] given as [%s]" % (r.url,
                r.text) )
            l_logger.exception( "Error attempting to in response fromNIH")
    return None#no valid response


def get_rxClassMembers( classId, relaSource, rela, raw=False ):
    """
    Returns the rxnormIds of drugs in this class

    see:
    http://rxnav.nlm.nih.gov/RxClassAPIREST.html#uLink=RxClass_REST_getClassMembers

    for information about the identifiers
    """
    r = requests.get('http://rxnav.nlm.nih.gov/REST/rxclass/classMembers.json',
            params={'classId':classId, 'relaSource': relaSource,
                'rela':rela} )

    if r.status_code == 200:
        #bs = BeautifulSoup(r.text, "xml")
        try:
            result = r.json()
            if raw:
                return result
            else:
                return [x['minConcept']['rxcui'] for x in
                        result['drugMemberGroup']['drugMember']]
        except:
            l_logger.error("Request to [%s] given as [%s]" % (r.url,
                r.text) )
            l_logger.exception( "Error attempting to in response fromNIH")
    return None#no valid response


