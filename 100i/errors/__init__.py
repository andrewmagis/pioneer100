class MyError(Exception):
    def __init__(self, expr):
        self.expr = expr

    def Print(self):
        print self.expr

    def __str__(self):
        print " [%s]"%(self.expr)