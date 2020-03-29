# Bucket Elimination Algorithm For STNU Dynamic Controllability Checking

Bucket elimination algorithm for checking STNU dynamic controllability.

## Document

A basic example to specify a temporal network and checking its dynamic controllability is shown below:
```
network = TemporalNetwork()
c1 = SimpleTemporalConstraint('e1', 'e2', 2, 5, 'c1')
c2 = SimpleContingentTemporalConstraint('e3', 'e2', 4, 7, 'c2')
network.add_constraints([c1, c2])
feasible, conflict = network.is_controllable(visualize=False, visualize_conflict=True)
```
Setting `visualize=True` will visualize each step of bucket elimination. The illustration is described below under [Visualization](#visualization). 
Setting `visualize_conflict=True` will visualize the final negative semi-reducible cycle, if one is found.

To try an example STNU, run:
```
python3 temporal_network.py
```

When the network is uncontrollable, a conflict is also returned. For example, in this case:
```
[[[c1, 'UB+'], [c1, 'LB-'], [c2, 'UB-', 'LB+']],
 [[c1, 'LB-']]]
```
The first sublist is the negative cycle. The rest of the sublists are supporting conditions for the negative cycle.
The reason why there are supporting conditions is that when there are lowercase labeled edges in the negative cycle, they can only be reduced away if it has a extension path that sums to < 0.

The conflict holds if each sublist in the conflict sums to < 0. That is, the conflict is `(UB(c1) - LB(c1) - UB(c2) + LB(c2) < 0) AND (- LB(c1) < 0)`. In order to resolve the conflict, making any of the sublist sum to >= 0 is sufficient. That is, resolving conflict requires satisfying the constraint `(UB(c1) - LB(c1) - UB(c2) + LB(c2) >= 0) OR (- LB(c1) >= 0)`.


## Visualization

At every iteration, the node being eliminated is marked red.

First, the algorithm checks feasibility:
* Blue cycle means the cycle is consistent, i.e. not a negative semi-reducible cycle.
* Red bold cycle means a conflict is found, i.e. it is a negative semi-reducible cycle.

Then, the algorithm triangulates parent edges:
* Red solid edges means the parent edges.
* Red dashed edge means the new triangulated edge.
* Yellow edge means an edge that is tighter than the new triangulated edge, hence the new triangulated edge will not be added to the graph.
* Grey edges means the edges that are dominated by the new triangulated edge (the new edge is tighter than them), which will be removed from the graph.


## File Directory

* temporal_network.py: Defines temporal network class and method for checking if it is controllable.
* check_dc.py: Main bucket elimination algorithm operating on labeled distance graph.
* ldgplot.py: Functions to plot the labeled distance graph.
* test.py: Test cases for checking correctness.


## Dependencies

Use `pip3 install -r requirements.txt` to install dependencies

## Reverse Compilation

We do a reverse pass to compile the network into a dispatchable one. This is a hypothesis. It has not been verified or tested yet. See changes in `check_dc.py`.