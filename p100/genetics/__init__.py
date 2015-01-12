import sys, gzip
import numpy as np
from scipy import stats
import pandas, pandas.io

from p100.errors import MyError
from p100.genotypes import Genotypes

class Genetics(object):

    def __init__(self, database):
        self.database = database

    def _get_trait_by_name(self, trait_name, pvalue=1, suppress_errors=True):

        # Get all the participant IDs
        cursor = self.database.GetCursor()
        cursor.execute("SELECT o.username "
                       "FROM prt_participant as o "
                       "ORDER BY o.username")

        # Loop over each username
        results = []
        for (username,) in cursor.fetchall():

            # Create the client object
            gt = Genotypes(username, self.database)

            # Process the trait
            result = gt.LoadTrait(trait_name, pvalue, suppress_errors)

            # Store the results
            if (not result is None):
                results.append((username, result.score))

        # Create the np array
        array = np.array(results, dtype=[('username', str, 8), (str(trait_name), float)])

        # Build pandas Series
        return pandas.DataFrame(array[str(trait_name)], index=array['username'], columns=[trait_name])
