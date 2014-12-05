
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

    def GetData(self, username=None, round=None):
        """
        Returns a dataframe with the metabolomic data for
        a given user and round(if provided).
        """
        logger.debug("GetData( %s, %s )" %(username, round))
        q_string = """
        SELECT mo.username, mo.round, imputed as value, biochemical as metabolite_name,
                super_pathway, sub_pathway, hmdb
        FROM meta_values mv, meta_observation mo, meta_metabolite mm
        WHERE mm.metabolite_id = mv.metabolite_id
        and mo.observation_id = mv.observation_id"""
        if username is None:
            var_tup = []
        else:
            q_string += " and mo.username = %s "
            var_tup = [username]

        if round is not None:
            q_string += " and mo.round = %s"
            var_tup += [round]
        return self.database.GetDataFrame( q_string, tuple(var_tup) )

    def get_ids(self, tax ):
        """
        Given a list/tuple of taxonomy labels in the order
        kingdom, phylum, class ...
        returns their associated label ids in order
        """
        select_stmt = ['`kd`.`tax_label_id` AS `kingdom_id`',
                '`ph`.`tax_label_id` AS `phylum_id`',
                '`cl`.`tax_label_id` AS `class_id`',
                '`ord`.`tax_label_id` AS `order_id`',
                '`fam`.`tax_label_id` AS `family_id`',
                '`gen`.`tax_label_id` AS `genus_id`',
                '`spc`.`tax_label_id` AS `species_id`']
        from_stmt = ['`mb_taxonomy_labels` `kd`',
                '`mb_taxonomy_labels` `ph`',
                '`mb_taxonomy_labels` `cl`',
                '`mb_taxonomy_labels` `ord`',
                '`mb_taxonomy_labels` `fam`',
                '`mb_taxonomy_labels` `gen`',
                '`mb_taxonomy_labels` `spc`']
        where_stmt = ['`kd`.`tax_level` = "kingdom" and `kd`.`tax_label` = %s',
                 '`ph`.`tax_level` = "phylum"  and `ph`.`tax_label` = %s',
                  '`cl`.`tax_level` = "class" and `cl`.`tax_label` = %s',
                 '`ord`.`tax_level` = "order" and `ord`.`tax_label` = %s',
                 '`fam`.`tax_level` = "family" and `fam`.`tax_label` = %s',
                 '`gen`.`tax_level` = "genus" and `gen`.`tax_label` = %s',
                 '`spc`.`tax_level` = "species" and `spc`.`tax_label` = %s']
        ss = ','.join(select_stmt[:len(tax)])
        fs = ','.join(from_stmt[:len(tax)])
        ws = ' and '.join(where_stmt[:len(tax)])
        query_str = "SELECT %s FROM %s WHERE %s" % (ss,fs,ws)
        result = None
        logging.debug("Query string [%s]" % query_str )
        logging.debug("Query values [%r]" % (tax,) )
        retry = True
        ctr = 0
        while retry:
            try:
                #with closing( mdb.connect('mysql', 'ipython', 'docker-db', '100i')) as conn: #ensure that the connection is closed
                conn = get_db_conn()
                with conn as cursor: 
                    cursor.execute(query_str, tuple(tax))
                    result = cursor.fetchone()
                    retry = False
                conn.close()
            except MySQLdb.OperationalError as err:
                logging.warning("Operational Error %r" % (err,))
                if ctr<5:
                    conn.close()
                    #connection error, lets retry
                    logging.warning("Retrying connection")
                    time.sleep(ctr*2 + 1)#linear backoff
                    conn = get_db_conn(True)
                    ctr+=1
                    retry = True
                else:
                    # This is not the error you're looking for
                    raise
        return result

        
    def get_labels(self, tax_id ):
        """
        Given a list/tuple of taxonomy ids in the order
        kingdom, phylum, class ...
        returns their associated label ids in same order
        """
        select_stmt = ['`kd`.`tax_label` AS `kingdom`',
                '`ph`.`tax_label` AS `phylum`',
                '`cl`.`tax_label` AS `class`',
                '`ord`.`tax_label` AS `ordr`',
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
        where_stmt = [

    '`kd`.`tax_level` = "kingdom" and `kd`.`tax_label_id` = %s',
                 '`ph`.`tax_level` = "phylum"  and `ph`.`tax_label_id` = %s',
                  '`cl`.`tax_level` = "class" and `cl`.`tax_label_id` = %s',
                 '`ord`.`tax_level` = "order" and `ord`.`tax_label_id` = %s',
                 '`fam`.`tax_level` = "family" and `fam`.`tax_label_id` = %s',
                 '`gen`.`tax_level` = "genus" and `gen`.`tax_label_id` = %s',
                 '`spc`.`tax_level` = "species" and `spc`.`tax_label_id` = %s']


        ss = ','.join(select_stmt[:len(tax_id)])
        fs = ','.join(from_stmt[:len(tax_id)])
        ws = ' and '.join(where_stmt[:len(tax_id)])
        query_str = "SELECT %s FROM %s WHERE %s" % (ss,fs,ws)
        
        result = None
        logging.debug("Query string [%s]" % query_str )
        logging.debug("Query values [%r]" % (tax_id,) )
        retry = True
        ctr = 0
        while retry:
            try:
                conn = get_db_conn()
                with conn as cursor: 
                    cursor.execute(query_str, tuple(tax_id))
                    result = cursor.fetchone()
                    retry = False
                conn.close()
            except MySQLdb.OperationalError as err:
                logging.warning("Operational Error %r" % (err,))
                if ctr<5:
                    #connection error, lets retry
                    time.sleep(ctr*2 + 1)#linear backoff
                    retry = True
                    ctr += 1
                    conn.close()
                    conn = get_db_conn(True)
                    logging.warning("Retrying connection")
                else:
                    # This is not the error you're looking for
                    raise
        return result

    def get_mb(self, username, perc=True, rnd=1, agg_to='species'):
        cut = self.tax.index(agg_to) + 1
        select_stmt = ['`kd`.`tax_label` AS `kingdom`',
                '`ph`.`tax_label` AS `phylum`',
                '`cl`.`tax_label` AS `class`',
                '`ord`.`tax_label` AS `ordr`',
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

        s = ['tx.%s as %s_id' % (t,t) for t in self.tax[:cut]]
        s_stmt = ','.join(s) 

        if perc:
            s_stmt += ", SUM(lvl.percentage)"
        else:
            s_stmt += ", SUM(lvl.read_counts)"
        q_string = "SELECT obs.observation_id, obs.username, " + s_stmt + ',' + ss + """
        FROM mb_observation obs, mb_taxonomy tx, mb_levels lvl, """ + fs + """ 

        WHERE obs.round = %s and 
            obs.observation_id = lvl.observation_id and 
            tx.taxonomy_id = lvl.taxonomy_id and
            lvl.read_counts > 0 and """ + ws
        if username is not None:
            q_string += " and obs.username = %s"
        q_string += " GROUP BY obs.observation_id, " + ','.join(['tx.%s' % t for t in self.tax[:cut]])

        retry = True
        ctr = 0
        if username:
            var_tup = (rnd, username)
        else:
            var_tup = (rnd, )
        res = self.database.GetDataFrame(q_string, var_tup)
        return res

