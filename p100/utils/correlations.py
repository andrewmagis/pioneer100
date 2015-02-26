import statsmodels.sandbox.stats.multicomp
from scipy import stats
import pandas
import json


import logging
l_logger = logging.getLogger("p100.utils.correlations")

class CompareDataFrames:
    """
    Given 2 dataframes with intersecting indices, perform pairwise correlative
    analysis.
    """
    def __init__(self, dataframe1, dataframe2):
        self._df1 = dataframe1
        self._df2 = dataframe2
        self._corr = None
        self._mh_method = None

    def spearman_pearson(self,min_obs=10 ):
        """
        Returns a dataframe containing the pearson and spearman correlation with
        other useful statistics between the 2 given dataframes.

        min_obs - minimum number of valid values to observe for calculating
        
        """
        if self._corr is None:
            results = []
            for col1  in self._df1.columns:
                for col2 in self._df2.columns:
                    df1, df2 = self.select( col1, col2 )
                    if len(df1) > min_obs:
                        p, pv = stats.pearsonr(df1,df2)
                        sp, sppv = stats.spearmanr(df1,df2)
                        results.append({
                            'var_1': col1,
                            'var_2': col2,
                            'spearman_coeff': sp,
                            'spearman_pval':sppv,
                            'pearson_coeff': p,
                            'pearson_pval': pv })
            self._corr = pandas.DataFrame(results)
        return self._corr

    def select( self, var1, var2 ):
        """
        Given 2 column names, return 2 intersected series
        """
        df1_temp = self._df1[var1].dropna()
        df2_temp = self._df2[var2].dropna()
        df1 = df1_temp[df2_temp.index].dropna()
        df2 = df2_temp[df1.index]
        return (df1, df2)

    def filter(self, rejected='both', mh_method='fdr_bh', cutoff=.05):
        """
        mh_method - method used for multiple hypothesis testing
                    see: http://statsmodels.sourceforge.net/0.5.0/generated/statsmodels.sandbox.stats.multicomp.multipletests.html
        cutoff - rejection level for the corrected p-values
        rejected - return only relationships that have corrected p-values less than
                the threshold for {'both', 'spearman', 'pearson', 'either', None},
                with None meaning return all correlations
        """
        if self._corr is None:
            self.spearman_pearson()
        t = self._corr.copy() 
        t = self._add_rejected(t, mh_method, cutoff)
        self._mh_method = mh_method#save for addendum
        if t is not None:
            front = ['var_1', 'var_2','spearman_corrected', 'pearson_corrected']
            back = sorted([c for c in t.columns if c not in front])
            t = t[front + back]
        if rejected == 'both':
            return t[t.spearman_rejected & t.pearson_rejected]
        elif rejected == 'spearman':
            return t[t.spearman_rejected]
        elif rejected == 'pearson':
            return t[t.pearson_rejected]
        elif rejected == 'either':
            return t[t.spearman_rejected | t.pearson_rejected]
        else:
            return t
    
    def _add_rejected(self, corr_df, method, cutoff):
        """
        Adds the corrected pvalues and whether one can reject the null
        hypothesis
        """
        mt = statsmodels.sandbox.stats.multicomp.multipletests
        (accepted, corrected, unused1, unused2) = mt(corr_df['spearman_pval'].fillna(1), method=method, alpha=cutoff)
        corr_df['spearman_corrected'] = corrected
        corr_df['spearman_rejected'] = accepted
        (accepted, corrected, unused1, unused2) =mt(corr_df['pearson_pval'].fillna(1), method=method, alpha=cutoff)
        corr_df['pearson_corrected'] = corrected
        corr_df['pearson_rejected'] = accepted
        return corr_df

    def save(self, database, table_1, column1, table_2, column2, corr, addendum={}):

        q_string = """
            INSERT into correlations( dt1_table, dt1_column, dt2_table, dt2_column, addendum,
            dt1_id, dt2_id, p_coeff, p_pval, p_pval_adj, s_coeff, s_pval, s_pval_adj) 
            VALUES (""" 
        q_string += ', '.join(['%s']*13) + ')'
        if 'mh_method' not in addendum:
            addendum['mh_method'] = self._mh_method

        addendum = json.dumps( addendum )
        base = [table_1, column1, table_2, column2, addendum]
        inserts = []
        for idx,row in corr.iterrows():
            local = [row['var_1' ], row['var_2'],
            row['pearson_coeff'], row['pearson_pval'], row['pearson_corrected'],
            row['spearman_coeff'], row['spearman_pval'], row['spearman_corrected']]
            inserts.append( tuple( base + local ) )
        cursor =  database.GetCursor()
        l_logger.debug(q_string)
        l_logger.debug(inserts)
        cursor.executemany( q_string, inserts)
        database.Commit()

    def GetData( self, database ):
        return database.GetDataFrame( "SELECT * from correlations" )




