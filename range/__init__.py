
class Range(object):

    def __init__(self, measurement, unit, male_low, male_med, male_high, female_low, female_med, female_high, hmdb, internal_id):

        self.measurement = measurement
        self.unit = unit
        self.hmdb = hmdb
        self.internal_id = internal_id
        self.is_range = True
        self.sd = None
        self.mean = None
        self.changed = 0;
        self.avg_change = [];
        self.sum_change = 0;

        # Male high and low ranges (always present)
        try:
            self.male_low = float(male_low)
        except:
            self.male_low = male_low
            self.is_range = False
        try:
            self.male_high = float(male_high)
        except:
            self.male_high = male_high
            self.is_range = False

        # Female high and low ranges (always present)
        try:
            self.female_low = float(female_low)
        except:
            self.female_low = female_low
            self.is_range = False
        try:
            self.female_high = float(female_high)
        except:
            self.female_high = female_high
            self.is_range = False

        # Male and female mid ranges (sometimes present)
        try:
            self.male_med = float(male_med)
        except:
            self.male_med = male_med
        try:
            self.female_med = float(female_med)
        except:
            self.female_med = female_med

    def OutOfRange(self, value, gender):

        # Unknown values are always in-range
        if (value is None):
            return None

        if (gender == "M"):
            
            if (self.is_range):

                if (not self.male_med is None):

                    if (value <= self.male_low):
                        return -1
                    elif (value <= self.male_med):
                        return 0
                    elif (value <= self.male_high):
                        return 1
                    else:
                        return 2

                else:
                    if (value <= self.male_low):
                        return -1
                    elif (value <= self.male_high):
                        return 0
                    else:
                        return 2

            else:
                 if (value == self.male_low):
                    return 0
                 else:
                    return 1

            """
            if (self.is_range):
                if (value <= self.male_low):
                    return -1
                elif (not self.male_med is None) and (value <= self.male_med):
                    return 1
                elif (value > self.male_high):
                    return 2
                else:
                    return 0
            else:
                if (value == self.male_low):
                    return 0
                else:
                    return 1
            """

        elif (gender == "F"):

            if (self.is_range):

                if (not self.female_med is None):

                    if (value <= self.female_low):
                        return -1
                    elif (value <= self.female_med):
                        return 0
                    elif (value <= self.female_high):
                        return 1
                    else:
                        return 2

                else:
                    if (value <= self.female_low):
                        return -1
                    elif (value <= self.female_high):
                        return 0
                    else:
                        return 2

            else:
                 if (value == self.female_low):
                    return 0
                 else:
                    return 1

            """
            if (self.is_range):
                if (value <= self.female_low):
                    return -1
                elif (not self.female_med is None) and (value <= self.female_med):
                    return 1
                elif (value > self.female_high):
                    return 2
                else:
                    return 0
            else:
                if (value == self.female_low):
                    return 0
                else:
                    return 1
            """
        else:
            raise MyError("[Range] Unknown gender", str(gender))

    def Print(self):
        print self.measurement, self.unit, self.min_male, self.max_male, self.min_female, self.max_female, self.is_range

    def AddRangesToDatabase(self):

        command = ""
        command += "CREATE TABLE ranges (MEASUREMENT VARCHAR(128) PRIMARY KEY, UNIT VARCHAR(128) NOT NULL, MALE_LOW FLOAT, MALE_MED FLOAT, MALE_HIGH FLOAT, FEMALE_LOW FLOAT, FEMALE_MED FLOAT, FEMALE_HIGH FLOAT, HMDB VARCHAR(16))"
        self.database.Command(command)

        command = ""
        command += "INSERT INTO ranges VALUES ("

        for met in sorted(self.ranges.keys()):
            if (met == "Round"):
                continue
            else:
                command += met.upper().replace('-','_').replace('/','_').replace(' ', '_').replace('.','_')
            command += ',' + self.ranges[met].unit
            command += ',' + str(self.ranges[met].male_low)
            command += ',' + str(self.ranges[met].male_medium)
            command += ',' + str(self.ranges[met].male_high)
            command += ',' + str(self.ranges[met].female_low)
            command += ',' + str(self.ranges[met].female_medium)
            command += ',' + str(self.ranges[met].female_high)
            command += ',' + self.ranges[met].hmdb

        command += ")"
        print command