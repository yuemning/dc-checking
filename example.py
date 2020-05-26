from temporal_network import TemporalNetwork, SimpleContingentTemporalConstraint, SimpleTemporalConstraint
from dc_milp import DCCheckerMILP
from dc_be import DCCheckerBE

# Controllable
# c1 = SimpleContingentTemporalConstraint('e1', 'e5', 15, 18.8554, 'c1')
# Uncontrollable
c1 = SimpleContingentTemporalConstraint('e1', 'e5', 0.6294, 18.8554, 'c1')
c2 = SimpleTemporalConstraint('e1', 'e2', 1, 100, 'c2')
c3 = SimpleTemporalConstraint('e2', 'e5', 0, 100, 'c3')
c4 = SimpleTemporalConstraint('e2', 'e3', 1, 100, 'c4')
c5 = SimpleTemporalConstraint('e3', 'e4', 1.5, 100, 'c5')
c6 = SimpleTemporalConstraint('e1', 'e4', 1, 3.5, 'c6')
network = TemporalNetwork([c1, c2, c3, c4, c5, c6])

# DC Checker using Bucket Elimination
checker = DCCheckerBE(network)
controllable, conflict = checker.is_controllable(visualize=False, visualize_conflict=False)
print(controllable, conflict)

# DC checker using MILP
checker = DCCheckerMILP(network)
controllable, _ = checker.is_controllable()
print(controllable)