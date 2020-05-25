import gurobipy as gp
from gurobipy import GRB
from temporal_network import TemporalNetwork, SimpleContingentTemporalConstraint, SimpleTemporalConstraint

MAX_NUMERIC_BOUND = 100000

class DCCheckerMILP:
    '''
    This implementation uses the MILP formulation from the following paper:

    Optimising Bounds in Simple Temporal Networks with Uncertainty under
    Dynamic Controllability Constraints
    Jing Cui, Peng Yu, Cheng Fang, Patrik Haslum, Brian C. Williams 

    It is also summarized in Casanova's paper in ECAI 2016.
    '''

    def __init__(self, tn):
        self.tn = tn

    def solve_dc(self):

        # Create a new model
        m = gp.Model("DCchecking")

        # Create variables
        self.add_variables_to_model(m)

        # Set objectives
        # (feasibility problem, no objective)

        # Add constraints
        self.add_constraints_to_model(m)

        # Optimize model
        m.optimize()

        if m.status == GRB.Status.INFEASIBLE:
            print('No feasible solution. See infeasible.ilp for conflict.')
            m.computeIIS()
            m.write("infeasible.ilp")
        else:
            print('Solution found.')

    def add_variables_to_model(self, m):

        events = self.tn.get_events()
        constraints = self.tn.get_constraints()

        # (vi, vj) => variable, vi != vj
        self.u = {}

        for vi in events:
            for vj in events:
                if not vi == vj:
                    uij = m.addVar(lb=-MAX_NUMERIC_BOUND, ub=MAX_NUMERIC_BOUND, vtype=GRB.CONTINUOUS, name="u({}, {})".format(vi, vj))
                    self.u[(vi, vj)] = uij

        # (vi, vj, vk) => variable, where (vi, vk) is contingent, vj != vk, vj != vi
        self.w = {}

        # (vi, vj, vk) => boolean variable, for each wait var
        self.x = {}

        # (vi, vj, vk) => boolean variable, for precede or not
        self.b = {}

        for c in constraints:
            if isinstance(c, SimpleContingentTemporalConstraint):
                vi = c.s
                vk = c.e
                for vj in events:
                    if not vj == vi and not vj == vk:
                        wijk = m.addVar(lb=-MAX_NUMERIC_BOUND, ub=MAX_NUMERIC_BOUND, vtype=GRB.CONTINUOUS, name="w({}, {}, {})".format(vi, vj, vk))
                        self.w[(vi, vj, vk)] = wijk
                        xijk = m.addVar(vtype=GRB.BINARY, name="x({}, {}, {})".format(vi, vj, vk))
                        self.x[(vi, vj, vk)] = xijk
                        bijk = m.addVar(vtype=GRB.BINARY, name="b({}, {}, {})".format(vi, vj, vk))
                        self.b[(vi, vj, vk)] = bijk
                        

    def add_constraints_to_model(self, m):

        events = self.tn.get_events()
        constraints = self.tn.get_constraints()

        # Non-negative cycle constraint
        # uij + uji >= 0
        visited = {}
        for (vi, vj) in self.u:
            if not (vi, vj) in visited and not (vj, vi) in visited:
                visited[(vi, vj)] = True
                uij = self.u[(vi, vj)]
                uji = self.u[(vj, vi)]
                m.addConstr(uij + uji >= 0, 'non-neg-{}-{}'.format(vi, vj))

        # (1), (2) Bounds for requirement and contingent constraints
        for c in constraints:
            # uij <= Uij, lij >= Lij (uji <= -Lij)
            uij = self.u[(c.s, c.e)]
            uji = self.u[(c.e, c.s)]
            m.addConstr(uij <= c.ub, 'u({}, {}) <= U'.format(c.s, c.e))
            m.addConstr(uji <= - c.lb, 'u({}, {}) <= -L'.format(c.e, c.s))

            # if contingent, uij = Uij, lij = Lij
            if isinstance(c, SimpleContingentTemporalConstraint):
                m.addConstr(uij >= c.ub, 'u({}, {}) >= U'.format(c.s, c.e))
                m.addConstr(uji >= - c.lb, 'u({}, {}) >= -L'.format(c.e, c.s))

        # (3) Shortest path constraint
        # uik <= uij + ujk
        for vi in events:
            for vj in events:
                for vk in events:
                    if not vi == vj and not vi == vk and not vj == vk:
                        uij = self.u[(vi, vj)]
                        ujk = self.u[(vj, vk)]
                        uik = self.u[(vi, vk)]
                        m.addConstr(uik <= uij + ujk, 'shortestpath({},{},{})'.format(vi, vj, vk))

        # (4) Precede constraint 
        # ljk > 0 => uij <= lik - ljk (uij <= -uki + ukj) and lij >= uik - ujk (-uji >= uik - ujk)
        for (vi, vj, vk) in self.b:
            # When (vi, vk) is contingent and ljk > 0 means vj precedes vk for sure
            bijk = self.b[(vi, vj, vk)]
            uij = self.u[(vi, vj)]
            uji = self.u[(vj, vi)]
            uik = self.u[(vi, vk)]
            uki = self.u[(vk, vi)]
            ujk = self.u[(vj, vk)]
            ukj = self.u[(vk, vj)]
            # If b = 0, ljk <= 0 (ukj >= 0)
            m.addConstr(ukj + bijk * MAX_NUMERIC_BOUND >= 0, 'precede-b0({},{},{})'.format(vi, vj, vk))
            # If b = 1, the other two constraints
            m.addConstr(uij - (1-bijk) * MAX_NUMERIC_BOUND <= -uki + ukj, 'precede-b1({},{},{})-a'.format(vi, vj, vk))
            m.addConstr(-uji + (1-bijk) * MAX_NUMERIC_BOUND >= uik - ujk, 'precede-b1({},{},{})-b'.format(vi, vj, vk))

        # (5)(6) Wait constraint
        # uik - ujk <= wijk
        # min(lik, wijk) <= lij     
        # (6) TODO: Why only min with lik? In the extreme case, shouldn't both be satisfied?
        # (6) TODO: Why is the alpha beta formulation necessary in Cui's paper?
        for (vi, vj, vk) in self.w:
            # When (vi, vk) is contingent and vj, vk unordered
            uij = self.u[(vi, vj)]
            uji = self.u[(vj, vi)]
            uik = self.u[(vi, vk)]
            uki = self.u[(vk, vi)]
            ujk = self.u[(vj, vk)]
            wijk = self.w[(vi, vj, vk)]
            # uik - ujk <= wijk
            m.addConstr(uik - ujk <= wijk, 'wait({},{},{})'.format(vi, vj, vk))

            # wijk <= uij should hold according to Cui's
            # TODO: don't see why this is necessary to encode
            # m.addConstr(wijk <= uij, 'redundant({},{},{})'.format(vi, vj, vk))

            # min(lik, wijk) <= lij
            # (lij >= lik and wijk >= lik) or (lij >= wijk and wijk <= lik)
            # Should be fine without comparing wijk >=/<= lik, but (7) uses it in Peng's implementation
            xijk = self.x[(vi, vj, vk)]
            # If x = 0, lij >= lik (uji <= uki)
            m.addConstr(uji - xijk * MAX_NUMERIC_BOUND <= uki, 'waitcond0({}, {}, {})'.format(vi, vj, vk))
            m.addConstr(wijk + xijk * MAX_NUMERIC_BOUND >= -uki, 'waitcond0+({}, {}, {})'.format(vi, vj, vk))
            # If x = 1, lij >= wijk (-uji >= wijk)
            m.addConstr(-uji + (1-xijk) * MAX_NUMERIC_BOUND >= wijk, 'waitcond1({}, {}, {})'.format(vi, vj, vk))
            m.addConstr(wijk - (1-xijk) * MAX_NUMERIC_BOUND <= -uki, 'waitcond1+({}, {}, {})'.format(vi, vj, vk))

        # (8) wait regression
        # wijk − umj <= wimk
        for c in constraints:
            if isinstance(c, SimpleContingentTemporalConstraint):
                vi = c.s
                vk = c.e
                for vj in events:
                    for vm in events:
                        if not vj == vi and not vj == vk and not vm == vi and not vm == vk and not vm == vj:
                            wijk = self.w[(vi, vj, vk)]
                            wimk = self.w[(vi, vm, vk)]
                            umj = self.u[(vm, vj)]
                            m.addConstr(wijk - umj <= wimk, 'regression({}, {}, {}, {})'.format(vi, vj, vk, vm))

        # (7) wait regression for contingent constraint
        # (wijk <= 0) or (wijk − lmj <= wimk)
        # In Peng's implementation, (wijk >= lik) => (wijk − lmj <= wimk), we will try this
        # That is xijk = 0 => (wijk + ujm <= wimk)
        # TODO: unclear what this (wijk <= 0) condition really should be
        for c1 in constraints:
            if isinstance(c1, SimpleContingentTemporalConstraint):
                for c2 in constraints:
                    if isinstance(c2, SimpleContingentTemporalConstraint):
                        if not c1 == c2:
                            vi = c1.s
                            vk = c1.e
                            vm = c2.s
                            vj = c2.e
                            wijk = self.w[(vi, vj, vk)]
                            xijk = self.x[(vi, vj, vk)]
                            wimk = self.w[(vi, vm, vk)]
                            ujm = self.u[(vj, vm)]
                            m.addConstr(wijk + ujm - xijk * MAX_NUMERIC_BOUND <= wimk, 'regression-contingent({}, {}, {}, {})'.format(vi, vj, vk, vm))


if __name__ == '__main__':
    # Controllable
    c1 = SimpleContingentTemporalConstraint('e1', 'e5', 15, 18.8554, 'c1')
    # Uncontrollable
    # c1 = SimpleContingentTemporalConstraint('e1', 'e5', 0.6294, 18.8554, 'c1')
    c2 = SimpleTemporalConstraint('e1', 'e2', 1, 100, 'c2')
    c3 = SimpleTemporalConstraint('e2', 'e5', 0, 100, 'c3')
    c4 = SimpleTemporalConstraint('e2', 'e3', 1, 100, 'c4')
    c5 = SimpleTemporalConstraint('e3', 'e4', 1.5, 100, 'c5')
    c6 = SimpleTemporalConstraint('e1', 'e4', 1, 3.5, 'c6')
    network = TemporalNetwork([c1, c2, c3, c4, c5, c6])

    solver = DCCheckerMILP(network)
    solver.solve_dc()






# Gurobi example

# try:

#     # Create a new model
#     m = gp.Model("mip1")

#     # Create variables
#     x = m.addVar(vtype=GRB.BINARY, name="x")
#     y = m.addVar(vtype=GRB.BINARY, name="y")
#     z = m.addVar(vtype=GRB.BINARY, name="z")

#     # Set objective
#     m.setObjective(x + y + 2 * z, GRB.MAXIMIZE)

#     # Add constraint: x + 2 y + 3 z <= 4
#     m.addConstr(x + 2 * y + 3 * z <= 4, "c0")

#     # Add constraint: x + y >= 1
#     m.addConstr(x + y >= 1, "c1")

#     # Optimize model
#     m.optimize()

#     for v in m.getVars():
#         print('%s %g' % (v.varName, v.x))

#     print('Obj: %g' % m.objVal)

# except gp.GurobiError as e:
#     print('Error code ' + str(e.errno) + ': ' + str(e))

# except AttributeError:
#     print('Encountered an attribute error')