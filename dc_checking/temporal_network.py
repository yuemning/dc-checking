from uuid import uuid4
from collections import defaultdict

def print_tc(name, s, e, lb, ub, contingent=False):
    if contingent:
        tc_type = 'SCTC'
    else:
        tc_type = 'STC'
    return "<{} {}: {}, {}, {}, {}>".format(tc_type, name, s, e, lb, ub)


class TemporalConstraint:
    """Temporal Constraint base class."""

    def __init__(self, s, e, lb=None, ub=None, name=None):
        """Initialize a temporal constraint.

        Args:
            s: From event
            e: End event
            lb: Lower bound
            ub: Upper bound
        """

        self.s = s
        self.e = e
        self.lb = lb
        self.ub = ub
        if name == None:
            name = str(uuid4())
        self.name = name
        self.annotation = {}

    def to_json(self):
        return {'type': 'TemporalConstraint',
                'start': self.s,
                'end': self.e,
                'lb': self.lb,
                'ub': self.ub,
                'name': self.name}

    @classmethod
    def from_json(cls, data):
        assert(data['type'] == 'TemporalConstraint')
        s = data['start']
        e = data['end']
        lb = data['lb']
        ub = data['ub']
        name = data['name']
        return cls(s, e, lb, ub, name)


class SimpleTemporalConstraint(TemporalConstraint):
    """Simple Tempora Constraint class."""

    def __repr__(self):
        return print_tc(self.name, self.s, self.e, self.lb, self.ub)

    def __str__(self):
        return print_tc(self.name, self.s, self.e, self.lb, self.ub)

    def to_json(self):
        data = super().to_json()
        data['type'] = 'SimpleTemporalConstraint'
        return data

    @classmethod
    def from_json(cls, data):
        assert(data['type'] == 'SimpleTemporalConstraint')
        s = data['start']
        e = data['end']
        lb = data['lb']
        ub = data['ub']
        name = data['name']
        return cls(s, e, lb, ub, name)


class SimpleContingentTemporalConstraint(TemporalConstraint):
    """Simple Contingent Temporal Constraint class.

    Represents contingent constraint, that is, end event can only be observed
    and not controlled.
    """

    def __init__(self, s, e, lb=None, ub=None, name=None):
        super().__init__(s, e, lb, ub, name)
        assert(lb is not None)
        assert(ub is not None)
        assert(lb >= 0)
        # We allow the case where lv == ub.
        #  assert(not lb == ub)

    def __repr__(self):
        return print_tc(self.name, self.s, self.e, self.lb, self.ub, contingent=True)

    def __str__(self):
        return print_tc(self.name, self.s, self.e, self.lb, self.ub, contingent=True)

    def to_json(self):
        data = super().to_json()
        data['type'] = 'SimpleContingentTemporalConstraint'
        return data

    @classmethod
    def from_json(cls, data):
        assert(data['type'] == 'SimpleContingentTemporalConstraint')
        s = data['start']
        e = data['end']
        lb = data['lb']
        ub = data['ub']
        name = data['name']
        return cls(s, e, lb, ub, name)


class TemporalNetwork:
    """Temporal Network class.

    Each uncontrollable event is associated with a contingent constraint.
    """

    def __init__(self, constraints=None, name=None):
        if name is None:
            name = str(uuid4())
        self.name = name
        if constraints is None:
            constraints = []
        self.id2constraint = {}
        self.event2constraints = defaultdict(list)
        self.add_constraints(constraints)

    def __repr__(self):
        return "<TN: {} constraints>".format(len(self.id2constraint))

    def __str__(self):
        return "<TN: {} constraints>".format(len(self.id2constraint))

    def add_constraint(self, c):
        name = c.name
        if name in self.id2constraint:
            print("ERROR: constraint {} already exists network.".format(c))
            raise Exception
        else:
            self.id2constraint[name] = c
            self.event2constraints[c.s].append(c)
            self.event2constraints[c.e].append(c)

    def add_constraints(self, c_list):
        for c in c_list:
            self.add_constraint(c)

    def add_event(self, e):
        if e not in self.event2constraints:
            self.event2constraints[e] = []

    def add_events(self, e_list):
        for e in e_list:
            self.add_event(e)

    def get_events(self):
        return list(self.event2constraints.keys())

    def get_constraint(self, name_or_constraint):
        name = name_or_constraint
        if isinstance(name_or_constraint, TemporalConstraint):
            name = name_or_constraint.name
        if name in self.id2constraint:
            return self.id2constraint[name]
        else:
            return None

    def get_constraints(self):
        return list(self.id2constraint.values())

    def remove_event(self, e, remove_constraints=True, remove_unconnected_events=True):
        """Remove an event from network.

        Args:
            e: Event to be removed.
            remove_constraints: Optional; If remove_constraints is True, the constraints
                connected to e will also be removed.
            remove_unconnected_events: Optional; If remove_unconnected_events is True,
                remove any event with no constraints connected to it.
        """

        if e in self.event2constraints:
            constraints = self.event2constraints[e]
            if constraints:
                if remove_constraints:
                    self.remove_constraints(constraints, remove_unconnected_events)
                else:
                    print("ERROR: Removing event {} while still connected to constraints.".format(e))
                    raise Exception

            # Check again if exists, since might have been removed during remove_constraints
            if e in self.event2constraints:
                del self.event2constraints[e]
        else:
            print("ERROR: Cannot remove event {}, as it does not exist in network.".format(e))
            raise Exception

    def remove_events(self, e_list, remove_constraints=True, remove_unconnected_events=True):
        for e in e_list.copy():
            self.remove_event(e, remove_constraints, remove_unconnected_events)

    def remove_constraint(self, c, remove_events=True):
        """Remove a constraint from network.

        Args:
            c: Constraint to be removed.
            remove_events: Optional; If remove_events is True, remove the events if no
                constraints are still connected to it.
        """

        if isinstance(c, TemporalConstraint):
            c = c.name
        if c in self.id2constraint:
            constraint = self.id2constraint[c]
            s = constraint.s
            self.event2constraints[s].remove(constraint)
            e = constraint.e
            self.event2constraints[e].remove(constraint)
            if remove_events:
                if not self.event2constraints[s]:
                    self.remove_event(s, remove_constraints=False)
                if not self.event2constraints[e]:
                    self.remove_event(e, remove_constraints=False)
            del self.id2constraint[c]
        else:
            print("ERROR: Cannot remove constraint {}, as it does not exist in network.".format(c))
            raise Exception

    def remove_constraints(self, c_list, remove_events=True):
        for c in c_list.copy():
            self.remove_constraint(c, remove_events)

    def to_json(self):
        return {
                'type': 'TemporalNetwork',
                'name': self.name,
                'constraints': [c.to_json() for c in self.get_constraints()]
                }

    @classmethod
    def from_json(cls, data):
        assert(data['type'] == 'TemporalNetwork')
        name = data['name']
        constraints_json = data['constraints']
        constraints = []
        for c_json in constraints_json:
            c_cls = globals().get(c_json['type'])
            constraints.append(c_cls.from_json(c_json))
        return cls(constraints, name)
