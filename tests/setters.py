__author__ = 'pmaunz'


class mysetter(object):
    def __init__(self, v=None):
        self._value = v
        self._origin = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        if isinstance(v, tuple):
            self._value, self._origin = v
        else:
            self._value = v

    def __repr__(self):
        return "{0} {1}".format(self._value, self._origin)

if __name__=="__main__":
    m = mysetter(23)
    print m.value
    print m
    m.value = 43
    print m
    m.value = 42, "Peter"
    print m