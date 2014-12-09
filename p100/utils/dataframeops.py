
class DataFrameOps(object):

    def __init__(self):
        pass

    def _get_diff_by_id(self, roundA, roundB, field_id):

        # Get these two rounds
        dataA = self._get_field_by_id(roundA, field_id)
        dataB = self._get_field_by_id(roundB, field_id)

        # Now take the difference of the rounds and drop any that have data missing
        return (dataB - dataA).dropna()

    def _get_diff_by_name(self, roundA, roundB, field_name):

        # Get these two rounds
        dataA = self._get_field_by_name(roundA, field_name)
        dataB = self._get_field_by_name(roundB, field_name)

        # Now take the difference of the rounds and drop any that have data missing
        return (dataB - dataA).dropna()

    def _get_all_diff(self, roundA, roundB):

        # Get these two rounds
        dataA = self._get_all_fields(roundA)
        dataB = self._get_all_fields(roundB)

        # Now take the difference of the rounds and drop any that have data missing
        return (dataB - dataA)

