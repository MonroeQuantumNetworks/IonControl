__author__ = 'pmaunz'


def make_tuple(arg):
    if not isinstance(arg, tuple):
        arg = (arg, )
    return arg

if __name__=="__main__":

    def a():
        return 1

    def b():
        return 1,2

    print make_tuple(a())
    print make_tuple(b())