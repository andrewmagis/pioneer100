import statsmodels.sandbox.stats.multicomp
from scipy import stats
import pandas


class CompareDataFrames:
    """
    Given 2 dataframes with intersecting indices, perform pairwise correlative
    analysis.
    """
    def __init__(self, dataframe1, dataframe2):
        self._df1 = dataframe1
        self._df2 = dataframe2
        self._corr = None

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
                            'spearman_pval': sppv,
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
