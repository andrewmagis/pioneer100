
class Range(object):

    def __init__(self, ranges):

        self.ranges = ranges

    def state(self, value, gender):

        my_type = None
        my_level = None

        # Go through each range
        for (min_value, max_value, range_type, range_level, range_gender) in self.ranges:

            # Make sure genders match up
            if (gender == 0):
                gender = 'F'
            elif (gender == 1):
                gender = 'M'

            # No inf value in the database
            if (max_value is None):
                max_value = float("inf")

            if (gender == range_gender):

                if (value >= min_value) and (value <= max_value):

                    if (not my_type is None):
                        print "Warning, multiple states match in range"
                    else:
                        my_type = range_type
                        my_level = range_level

        return (my_type, my_level)

