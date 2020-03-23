# Bucket Elimination Algorithm For STNU Dynamic Controllability Checking

Bucket elimination algorithm for checking STNU dynamic controllability.

## Document
A basic example to specify a temporal network and checking its dynamic controllability is shown below:
```
network = TemporalNetwork()
c1 = SimpleTemporalConstraint('e1', 'e2', 2, 5, 'c1')
c2 = SimpleContingentTemporalConstraint('e3', 'e2', 4, 7, 'c2')
network.add_constraints([c1, c2])
feasible, conflict = network.is_controllable()
```

When the network is uncontrollable, a conflict is also returned. For example, in this case:
```
[[[c1, 'UB+'], [c1, 'LB-'], [c2, 'UB-', 'LB+']],
 [[c1, 'LB-']]]
```
The first sublist is the negative cycle. The rest of the sublists are supporting conditions for the negative cycle.
The conflict holds if each sublist in the conflict sums to < 0. In order to resolve the conflict, making any of the sublist sum to >= 0 is sufficient. 
To interpret each element in the sublist, `[c2, 'UB-', 'LB+']` means both upper bound and lower bound of constraint c2 are involved in the sublist, and the upper bound should be minused from the sum, whereas the lower bound should be added to the sum.
The reason why there are supporting conditions is that when there are lowercase labeled edges in the negative cycle, they can only be reduced away if it has a extension path that sums to < 0.

## File Directory
* temporal_network.py: Defines temporal network class and method for checking if it is controllable.
* check_dc.py: Main bucket elimination algorithm operating on labeled distance graph.
* test.py: Test cases for checking correctness.

## Dependencies
Use `pip3 install -r requirements.txt` to install dependencies