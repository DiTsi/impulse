class Unit:
    def __init__(self, name, actions):
        self.name = name
        if actions is not None:
            self.actions = actions

    def __repr__(self):
        return self.name


class UnitGroup(Unit):
    def __init__(self, name, units):
        super().__init__(name, None)
        self.units = units
