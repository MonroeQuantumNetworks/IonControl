
class HashableList(list):
    def __hash__(self):
        return hash(tuple(self))