class User:
    def __init__(self, name, id_, username=None, exists=False):
        self.name = name
        self.id = id_
        self.exists = exists
        self.username = username
        self.defined = True

    def __repr__(self):
        return self.name
