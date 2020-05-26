from uuid import uuid4
from collections import defaultdict

def print_tc(name, s, e, lb, ub, contingent=False):
    if contingent:
        tc_type = 'SCTC'
    else:
        tc_type = 'STC'
    return "<{} {}: {}, {}, {}, {}>".format(tc_type, name, s, e, lb, ub)


class TemporalConstraint:
    '''
    s: from event
    e: end event
    lb: lower bound
    ub: upper bound
    '''
    def __init__(self, s, e, lb=None, ub=None, name=None):
        self.s = s
        self.e = e
        self.lb = lb
        self.ub = ub
        if name == None:
            name = str(uuid4())
        self.name = name


class SimpleTemporalConstraint(TemporalConstraint):
    def __repr__(self):
        return print_tc(self.name, self.s, self.e, self.lb, self.ub)

    def __str__(self):
        return print_tc(self.name, self.s, self.e, self.lb, self.ub)


class SimpleContingentTemporalConstraint(TemporalConstraint):

    def __init__(self, s, e, lb=None, ub=None, name=None):
        super().__init__(s, e, lb, ub, name)
        assert(lb is not None)
        assert(ub is not None)
        assert(lb >= 0)

    def __repr__(self):
        return print_tc(self.name, self.s, self.e, self.lb, self.ub, contingent=True)
        
    def __str__(self):
        return print_tc(self.name, self.s, self.e, self.lb, self.ub, contingent=True)


class TemporalNetwork:
    def __init__(self, constraints=[]):
        '''
        Assume one contingent constraint for one uncontrollable event
        '''
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
            raise ValueError
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

    def get_constraints(self):
        return list(self.id2constraint.values())

    def remove_event(self, e, remove_constraints=True, remove_unconnected_events=True):
        '''
        If remove_constraints is True, the constraints
        connected to e will also be removed.
        If remove_single_events is True, remove the events 
        if no constraints are still connected to it.
        '''
        if e in self.event2constraints:
            constraints = self.event2constraints[e]
            if constraints:
                if remove_constraints:
                    self.remove_constraints(constraints, remove_unconnected_events)
                else:
                    print("ERROR: Removing event {} while still connected to constraints.".format(e))
                    raise ValueError
            # Check again if exists, since might be removed during remove_constraints
            if e in self.event2constraints:
                del self.event2constraints[e]
        else:
            print("ERROR: Cannot remove event {}, as it does not exist in network.".format(e))
            raise ValueError

    def remove_events(self, e_list, remove_constraints=True, remove_unconnected_events=True):
        for e in e_list.copy():
            self.remove_event(e, remove_constraints, remove_unconnected_events)


    def remove_constraint(self, c, remove_events=True):
        '''
        If remove_events is True, remove the events if no 
        constraints are still connected to it.
        '''
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
            raise ValueError

    def remove_constraints(self, c_list, remove_events=True):
        for c in c_list.copy():
            self.remove_constraint(c, remove_events)

