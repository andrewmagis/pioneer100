
# System imports
from datetime import date, datetime, timedelta as td
import logging

import fitbit
from p100.errors import MyError

import numpy as np
import scipy
import math, re
import pandas, pandas.io

# Codebase imports
from p100.errors import MyError

logger = logging.getLogger("p100.microbiome")

class Microbiome(object):
    tax = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
    def __init__(self, database):
        logger.debug("Creating a Microbiome object")
        self.database = database

    def GetData(self, username=None, rnd=None, agg_to='species',
            perc=True):
        """
        Returns a dataframe with the microbiomic data for
        a given user and round(if provided) aggregated to the agg_to
        level.  If perv is true, the it returns the aggregated
        percentages, otherwise the counts.
        """
        logger.debug("GetData( %s, %s, %s, %s  )" %( username,
            rnd,  agg_to, perc))
        #this part puts together the bits needed to get the taxonomic
        #labels
        cut = self.tax.index(agg_to) + 1
        select_stmt = ['`kd`.`tax_label` AS `kingdom`',
                '`ph`.`tax_label` AS `phylum`',
                '`cl`.`tax_label` AS `class`',
                '`ord`.`tax_label` AS `order`',
                '`fam`.`tax_label` AS `family`',
                '`gen`.`tax_label` AS `genus`',
                '`spc`.`tax_label` AS `species`']
        from_stmt = ['`mb_taxonomy_labels` `kd`',
                '`mb_taxonomy_labels` `ph`',
                '`mb_taxonomy_labels` `cl`',
                '`mb_taxonomy_labels` `ord`',
                '`mb_taxonomy_labels` `fam`',
                '`mb_taxonomy_labels` `gen`',
                '`mb_taxonomy_labels` `spc`']
        where_stmt = ['`kd`.`tax_level` = "kingdom" and `kd`.`tax_label_id` = tx.kingdom',
                 '`ph`.`tax_level` = "phylum"  and `ph`.`tax_label_id` = tx.phylum',
                 '`cl`.`tax_level` = "class" and `cl`.`tax_label_id` = tx.class',
                 '`ord`.`tax_level` = "order" and `ord`.`tax_label_id` =tx.order',
                 '`fam`.`tax_level` = "family" and `fam`.`tax_label_id` = tx.family',
                 '`gen`.`tax_level` = "genus" and `gen`.`tax_label_id` = tx.genus',
                 '`spc`.`tax_level` = "species" and `spc`.`tax_label_id` = tx.species']

        tax_id = self.tax[:cut]
        ss = ','.join(select_stmt[:len(tax_id)])
        fs = ','.join(from_stmt[:len(tax_id)])
        ws = ' and '.join(where_stmt[:len(tax_id)])
        #this works with the taxonomic ids
        s = ['tx.%s as %s_id' % (t,t) for t in self.tax[:cut]]
        s_stmt = ','.join(s) 

        if perc:
            s_stmt += ", SUM(lvl.percentage) as value"
        else:
            s_stmt += ", SUM(lvl.read_counts) as value"
        q_string = "SELECT obs.observation_id, obs.username, obs.round, " 
        q_string += s_stmt + ',' 
        q_string +=  ss 
        q_string += " FROM mb_observation obs, mb_taxonomy tx, mb_levels lvl, "
        q_string += fs 
        q_string += """
            WHERE obs.observation_id = lvl.observation_id and 
            tx.taxonomy_id = lvl.taxonomy_id and
            lvl.read_counts > 0 and """ + ws
        if username and rnd:
            q_string += " and obs.round = %s and obs.username = %s "
            var_tup = (rnd, username)
        elif username:
            q_string += " and obs.username = %s "
            var_tup = (username,)
        elif rnd:
            q_string += " and obs.round = %s "
            var_tup = (rnd, )
        else:
            var_tup = None
        q_string += " GROUP BY obs.observation_id, " + ','.join(['%s_id' % t for t in self.tax[:cut]])
        res = self.database.GetDataFrame(q_string, var_tup)
        #reorder the columns, they get messy
        column_order = ['observation_id', 'username', 'round']
        column_order += self.tax[:cut]
        column_order += ["%s_id" % x for x in self.tax[:cut]]
        column_order += ['value']
        column_order += [x for x in res.columns if x not in column_order]
        return res[column_order]

