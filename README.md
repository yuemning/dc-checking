# STNU Dynamic Controllability Checking

Algorithms for checking STNU dynamic controllability.

Current checkers include:
* Bucket elimination checker
* MILP checker

## Installation

With python version 3.7, use `pip install -r requirements.txt` to install dependencies.
Additionally, MILP checker needs Gurobi. Gurobi can be most conveniently installed through gurobipy package in Anaconda. The Gurobi version used is 9.0.2. You also need a license for Gurobi, and you may use a free academic license if you are a student.

## Basic Usage

See `example.py`.

## Create a Network

A basic example to specify a temporal network is shown below:
```
network = TemporalNetwork()
c1 = SimpleTemporalConstraint('e1', 'e2', 2, 5, 'c1')
c2 = SimpleContingentTemporalConstraint('e3', 'e2', 4, 7, 'c2')
c3 = SimpleTemporalConstraint('e3', 'e1', 0, None, 'c3')
network.add_constraints([c1, c2, c3])
```

## Bucket Elimination Checker

```
checker = DCCheckerBE(network)
controllable, conflict = checker.is_controllable(visualize=False, visualize_conflict=False)
```

### Conflict Extraction

When the network is uncontrollable, a conflict is also returned. For example, in this case:
```
[[[c1, 'UB+'], [c1, 'LB-'], [c2, 'UB-', 'LB+']],
 [[c1, 'LB-']]]
```
The first sublist is the negative cycle. The rest of the sublists are supporting conditions for the negative cycle.
The reason why there are supporting conditions is that when there are lowercase labeled edges in the negative cycle, they can only be reduced away if it has a extension path that sums to < 0.

The conflict holds if each sublist in the conflict sums to < 0. That is, the conflict is `(UB(c1) - LB(c1) - UB(c2) + LB(c2) < 0) AND (- LB(c1) < 0)`. In order to resolve the conflict, making any of the sublist sum to >= 0 is sufficient. That is, resolving conflict requires satisfying the constraint `(UB(c1) - LB(c1) - UB(c2) + LB(c2) >= 0) OR (- LB(c1) >= 0)`.

### Visualization

Setting `visualize=True` will visualize each step of bucket elimination. 
Setting `visualize_conflict=True` will visualize the final negative semi-reducible cycle, if one is found.

At every iteration, the node being eliminated is marked red.

First, the algorithm checks feasibility:
* Blue cycle means the cycle is consistent, i.e. not a negative semi-reducible cycle.
* Red bold cycle means a conflict is found, i.e. it is a negative semi-reducible cycle.

Then, the algorithm triangulates parent edges:
* Red solid edges means the parent edges.
* Red dashed edge means the new triangulated edge.
* Yellow edge means an edge that is tighter than the new triangulated edge, hence the new triangulated edge will not be added to the graph.
* Grey edges means the edges that are dominated by the new triangulated edge (the new edge is tighter than them), which will be removed from the graph.

## MILP checker

```
checker = DCCheckerMILP(network)
controllable, _ = checker.is_controllable(outputIIS=False)
```

MILP checker does not return a conflict. However, the infeasible set of constraints can be seen from the output file `infeasible.ilp` by setting `outputIIS=True`.

This implementation uses the MILP formulation from the following paper:

Cui, Jing, et al. "Optimising bounds in simple temporal networks with uncertainty under dynamic controllability constraints." Twenty-Fifth International Conference on Automated Planning and Scheduling. 2015.


## File Directory

* example.py: Basic examples.
* test.py: Test cases for checking correctness.
* evaluation.py: Evaluate performance using randomly generated examples.
* dc_checking/
	* temporal_network.py: Defines temporal network class.
	* dc_checker_abstract.py: Defines the DC checker abstract class.
	* dc_be: Implements the Bucket Elimination checker.
	* dc_milp: Implements the MILP checker.
	* ldgplot.py: Functions to plot the labeled distance graph.

