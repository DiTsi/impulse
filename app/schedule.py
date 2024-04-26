
class Schedule:
    def __init__(self, datetime_, action, status):
        self.datetime = datetime_
        self.action = action
        self.status = status  # 'waiting' | 'done'

    def dump(self):
        return {
            'datetime': self.datetime,
            'action': self.action.dump(),
            'status': self.status
        }

    @classmethod
    def load(cls, dump):
        return cls(dump['datetime'], Action.load(dump['action']), dump['status'])


class Action:
    def __init__(self, id_, type_, to):
        self.id = id_
        self.type = type_
        self.to = to

    def dump(self):
        return {
            'id': self.id,
            'type': self.type,
            'to': self.to
        }

    @classmethod
    def load(cls, dump):
        return cls(dump['id'], dump['type'], dump['to'])

    def __repr__(self):
        return {
            'id': self.id,
            'type': self.type,
            'to': self.to
        }
