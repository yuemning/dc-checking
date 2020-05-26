import networkx as nx
from dc_be import check_dc_bucket_elimination, eliminate, DCCheckerBE
from dc_milp import DCCheckerMILP
from temporal_network import SimpleTemporalConstraint, SimpleContingentTemporalConstraint, TemporalNetwork

def test_simple_bucket_elim():
    g = nx.MultiDiGraph()
    g.add_nodes_from(['e1', 'e2', 'e3'])
    g.add_edges_from([('e1', 'e2', {'label': None, 'labelType': None, 'weight': 5}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': 'lower', 'weight': 0}),
                      ('e3', 'e1', {'label': 'e3', 'labelType': 'upper', 'weight': -5})])

    feasible, conflict, order = check_dc_bucket_elimination(g)
    assert(feasible)
    assert(conflict == None)
    assert(order.index('e3') < order.index('e1'))

def test_temporal_network():
    c1 = SimpleTemporalConstraint('e1', 'e2', 1, 3, 'c1')
    c2 = SimpleContingentTemporalConstraint('e2', 'e3', 2, 3)
    network = TemporalNetwork([c1, c2])
    # print(network)
    # print(network.get_constraints())
    # print(network.get_events())
    network.remove_event('e2')
    assert(len(network.get_constraints()) == 0)
    assert(len(network.get_events()) == 0)

    network.add_constraints([c1, c2])
    network.remove_event('e2', remove_constraints=True, remove_unconnected_events=False)
    assert(len(network.get_constraints()) == 0)
    assert(len(network.get_events()) == 2)

    network.add_constraints([c1, c2])
    network.remove_constraint('c1')
    assert(len(network.get_constraints()) == 1)
    network.remove_constraint(c2)
    assert(len(network.get_constraints()) == 0)
    assert(len(network.get_events()) == 0)

    network.add_constraint(c1)
    network.remove_constraint(c1, remove_events=False)
    assert(len(network.get_events()) == 2)
    network.remove_event('e1', remove_constraints=False)
    assert(len(network.get_events()) == 1)

    network = TemporalNetwork([c1, c2])
    checker = DCCheckerBE(network)
    ldg = checker.to_ldg()
    # print(ldg.nodes())
    # print(ldg.edges(data=True))
    assert(len(ldg.nodes()) == 4)
    assert(len(ldg.edges(data=True)) == 6)

    feasible, conflict = checker.is_controllable()
    assert(feasible)

def test_tightest():
    c1 = SimpleTemporalConstraint('e1', 'e2', 3, 5, 'c1')
    c2 = SimpleTemporalConstraint('e3', 'e2', 4, 7, 'c2')
    c3 = SimpleTemporalConstraint('e1', 'e3', None, 3, 'c3')
    c4 = SimpleTemporalConstraint('e1', 'e3', None, 7, 'c4')
    network = TemporalNetwork([c1, c2, c3, c4])
    checker = DCCheckerBE(network)
    ldg = checker.to_ldg()
    assert(len(ldg.edges()) == 6)
    feasible, nc = eliminate(ldg, 'e2')
    assert(len(ldg.edges()) == 2)

def test_next_node():
    g = nx.MultiDiGraph()
    g.add_nodes_from(['e1', 'e2', 'e3'])
    g.add_edges_from([('e1', 'e2', {'label': None, 'labelType': None, 'weight': 5}),
                      ('e2', 'e3', {'label': None, 'labelType': None, 'weight': 3}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': 'lower', 'weight': 0}),
                      ('e3', 'e1', {'label': 'e3', 'labelType': 'upper', 'weight': -5})])

    feasible, conflict, order = check_dc_bucket_elimination(g)
    assert(feasible)
    assert(conflict == None)
    assert(order == ['e3', 'e2', 'e1'])

def test_next_node_nc():
    g = nx.MultiDiGraph()
    g.add_nodes_from(['e1', 'e2', 'e3', 'e4'])
    g.add_edges_from([('e1', 'e2', {'label': None, 'labelType': None, 'weight': -1}),
                      ('e1', 'e4', {'label': None, 'labelType': None, 'weight': -2}),
                      ('e2', 'e3', {'label': None, 'labelType': None, 'weight': 0}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': 'lower', 'weight': 0}),
                      ('e3', 'e1', {'label': 'e3', 'labelType': 'upper', 'weight': -5})])

    feasible, conflict, order = check_dc_bucket_elimination(g, full_conflict=False)
    assert(not feasible)
    assert(len(conflict) == 2)
    assert(order == ['e3'])

    g = nx.MultiDiGraph()
    g.add_nodes_from(['e4', 'e3', 'e2', 'e1'])
    g.add_edges_from([('e1', 'e2', {'label': None, 'labelType': None, 'weight': -1}),
                      ('e1', 'e4', {'label': None, 'labelType': None, 'weight': -2}),
                      ('e2', 'e3', {'label': None, 'labelType': None, 'weight': -1}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': 'lower', 'weight': 0}),
                      ('e3', 'e1', {'label': 'e3', 'labelType': 'upper', 'weight': -5})])

    feasible, conflict, order = check_dc_bucket_elimination(g, full_conflict=False)
    assert(not feasible)
    assert(len(conflict) == 3)
    assert(order == [])


def test_conflict():
    g = nx.MultiDiGraph()
    g.add_nodes_from(['e1', 'e2', 'e3', 'e4', 'e5', 'e6'])
    g.add_edges_from([('e1', 'e5', {'label': None, 'labelType': None, 'weight': 6}),
                      ('e5', 'e6', {'label': None, 'labelType': None, 'weight': -4}),
                      ('e6', 'e2', {'label': None, 'labelType': None, 'weight': -3}),
                      ('e1', 'e4', {'label': None, 'labelType': None, 'weight': -2}),
                      ('e2', 'e3', {'label': None, 'labelType': None, 'weight': 0}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': 'lower', 'weight': 0}),
                      ('e3', 'e1', {'label': 'e3', 'labelType': 'upper', 'weight': -5})])

    feasible, conflict, order = check_dc_bucket_elimination(g, full_conflict=True)
    assert(not feasible)
    assert(len(conflict) == 1)
    assert(len(conflict[0]) == 5)
    assert('e3' in order)
    assert(order.index('e5') < order.index('e6'))

    g = nx.MultiDiGraph()
    g.add_nodes_from(['e1', 'e2', 'e3', 'e4', 'e5', 'e6'])
    g.add_edges_from([('e1', 'e5', {'label': 'e5', 'labelType': 'lower', 'weight': 6}),
                      ('e5', 'e6', {'label': None, 'labelType': None, 'weight': -4}),
                      ('e6', 'e2', {'label': None, 'labelType': None, 'weight': -3}),
                      ('e1', 'e4', {'label': None, 'labelType': None, 'weight': -2}),
                      ('e2', 'e3', {'label': None, 'labelType': None, 'weight': 0}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': 'lower', 'weight': 0}),
                      ('e3', 'e1', {'label': 'e3', 'labelType': 'upper', 'weight': -5})])

    feasible, conflict, order = check_dc_bucket_elimination(g, full_conflict=True)
    assert(not feasible)
    assert(len(conflict) == 2)
    assert(len(conflict[0]) == 5)
    assert(len(conflict[1]) == 3)
    assert('e3' in order)
    assert(order.index('e5') < order.index('e6'))


def test_dc_0():
    c1 = SimpleTemporalConstraint('e1', 'e2', 2, 5, 'c1')
    c2 = SimpleContingentTemporalConstraint('e3', 'e2', 4, 7, 'c2')
    network = TemporalNetwork([c1, c2])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(feasible)

    c1 = SimpleTemporalConstraint('e1', 'e2', 3, 5, 'c1')
    c2 = SimpleContingentTemporalConstraint('e3', 'e2', 4, 7, 'c2')
    network = TemporalNetwork([c1, c2])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)
    assert(len(conflict) == 2)
    assert(len(conflict[0]) == 3)
    assert(len(conflict[1]) == 1)
    assert([c1, 'UB+'] in conflict[0])
    assert([c1, 'LB-'] in conflict[0])
    assert([c2, 'UB-', 'LB+'] in conflict[0])
    assert([c1, 'LB-'] in conflict[1])

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)


def test_dc_1():
    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 20, 30, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 40, 45, 'c2')
    c3 = SimpleTemporalConstraint('e1', 'e3', 0, 50, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)
    assert(len(conflict) == 1)
    assert(len(conflict[0]) == 4)
    assert([c3, 'UB+'] in conflict[0])
    assert([c2, 'LB-'] in conflict[0])
    assert([c1, 'UB-', 'LB+'] in conflict[0])
    assert([c1, 'LB-'] in conflict[0])

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 5, 30, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 40, 45, 'c2')
    c3 = SimpleTemporalConstraint('e1', 'e3', 0, 50, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)
    assert(len(conflict) == 1)
    assert(len(conflict[0]) == 4)
    assert([c3, 'UB+'] in conflict[0])
    assert([c2, 'LB-'] in conflict[0])
    assert([c1, 'UB-', 'LB+'] in conflict[0])
    assert([c1, 'LB-'] in conflict[0])

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 5, 10, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 40, 45, 'c2')
    c3 = SimpleTemporalConstraint('e1', 'e3', 0, 50, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

    checker = DCCheckerMILP(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

def test_dc_2():
    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 5, 30, 'c1')
    c2 = SimpleTemporalConstraint('e3', 'e2', 1, 1, 'c2')
    network = TemporalNetwork([c1, c2])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

def test_dc_3():
    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 3, 100000, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', -1, 100000, 'c2')
    c3 = SimpleContingentTemporalConstraint('e3', 'e4', 1, 5.5, 'c3')
    c4 = SimpleTemporalConstraint('e4', 'e5', 0, None, 'c4')
    c5 = SimpleContingentTemporalConstraint('e5', 'e6', 10, 14.5, 'c5')
    c6 = SimpleTemporalConstraint('e6', 'e7', 0, 100000, 'c6')
    c7 = SimpleTemporalConstraint('e2', 'e7', 5, 18, 'c7')
    network = TemporalNetwork([c1, c2, c3, c4, c5, c6, c7])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

def test_dc_4():
    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 1, 10, 'c1')
    c2 = SimpleTemporalConstraint('e3', 'e2', 1, 2, 'c2')
    c3 = SimpleContingentTemporalConstraint('e1', 'e3', 1, 8, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

    
    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 0, 10, 'c1')
    c2 = SimpleTemporalConstraint('e3', 'e2', 0, 2, 'c2')
    c3 = SimpleContingentTemporalConstraint('e1c', 'e3', 0, 8, 'c3')
    c4 = SimpleTemporalConstraint('e1', 'e1c', 0, 0, 'c4')
    network = TemporalNetwork([c1, c2, c3, c4])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 0, 10, 'c1')
    c2 = SimpleTemporalConstraint('e3', 'e2', 0, 2, 'c2')
    c3 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 8, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 1, 10, 'c1')
    c2 = SimpleTemporalConstraint('e3', 'e2', 1, 2, 'c2')
    c3 = SimpleTemporalConstraint('e1', 'e3', 1, 8, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

def test_dc_5():
    c1 = SimpleTemporalConstraint('e1', 'e2', 1, 8, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 1, 2, 'c2')
    c3 = SimpleContingentTemporalConstraint('e1', 'e3', 1, 10, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

def test_dc_6():
    c1 = SimpleContingentTemporalConstraint('e1', 'e5', 0.6294, 18.8554, 'c1')
    c2 = SimpleTemporalConstraint('e1', 'e2', 1, 100, 'c2')
    c3 = SimpleTemporalConstraint('e2', 'e5', 0, 100, 'c3')
    c4 = SimpleTemporalConstraint('e2', 'e3', 1, 100, 'c4')
    c5 = SimpleTemporalConstraint('e3', 'e4', 1.5, 100, 'c5')
    c6 = SimpleTemporalConstraint('e1', 'e4', 1, 3.5, 'c6')
    network = TemporalNetwork([c1, c2, c3, c4, c5, c6])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

def test_dc_7():
    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 3, 3.5, 'c1')
    c2 = SimpleTemporalConstraint('e1', 'e2', 4, 6, 'c2')
    c3 = SimpleTemporalConstraint('e1', 'e2', 2, 3.5, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

def test_dc_8():
    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 0, 2, 'c1')
    c2 = SimpleContingentTemporalConstraint('e3', 'e4', 0, 3, 'c2')
    c3 = SimpleTemporalConstraint('e4', 'e2', -1, 3, 'c3')
    c4 = SimpleTemporalConstraint('e5', 'e2', 2, 4, 'c4')
    network = TemporalNetwork([c1, c2, c3, c4])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

def test_dc_9():
    c1 = SimpleContingentTemporalConstraint('e1', 'e2', 0, 1, 'c1')
    c2 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 1, 'c2')
    c3 = SimpleTemporalConstraint('e2', 'e4', 0, 0, 'c3')
    c4 = SimpleTemporalConstraint('e3', 'e4', 0, 0, 'c4')
    network = TemporalNetwork([c1, c2, c3, c4])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

def test_dc_10():
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 4, 'c1')
    c2 = SimpleTemporalConstraint('e1', 'e2', 0, 2, 'c2')
    c3 = SimpleTemporalConstraint('e2', 'e3', 0, 2, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(feasible)

def test_dc_11():
    # A =======[0,10]=====> C
    #           B --[0,2]--/
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 10, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 0, 2, 'c2')
    network = TemporalNetwork([c1, c2])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(feasible)

    # A =======[0,10]=====> C
    #           B --[1,2]--/
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 10, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 1, 2, 'c2')
    network = TemporalNetwork([c1, c2])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

    # A =======[0,10]=====> C
    #  \--[8,*)->B--[0,2]--/
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 10, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 0, 2, 'c2')
    c3 = SimpleTemporalConstraint('e1', 'e2', 8, None, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

    # A =======[0,10]=====> C
    #  \--[0,8]->B--[0,2]--/
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 10, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 0, 2, 'c2')
    c3 = SimpleTemporalConstraint('e1', 'e2', 0, 8, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(feasible)

    # A =======[0,10]=====> C
    #  \==[0,8]=>B--[0,2]--/
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 10, 'c1')
    c2 = SimpleTemporalConstraint('e2', 'e3', 0, 2, 'c2')
    c3 = SimpleContingentTemporalConstraint('e1', 'e2', 0, 8, 'c3')
    network = TemporalNetwork([c1, c2, c3])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(not feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(not feasible)

    # A =======[0,10]=====> C ---[0,2]--> B
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 10, 'c1')
    c2 = SimpleTemporalConstraint('e3', 'e2', 0, 2, 'c2')
    network = TemporalNetwork([c1, c2])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(feasible)

    # A =======[0,10]=====> C ===[0,2]==> B
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 0, 10, 'c1')
    c2 = SimpleContingentTemporalConstraint('e3', 'e2', 0, 2, 'c2')
    network = TemporalNetwork([c1, c2])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(feasible)

    # A =======[2,10]=====> C ===[1,2]==> B
    c1 = SimpleContingentTemporalConstraint('e1', 'e3', 2, 10, 'c1')
    c2 = SimpleContingentTemporalConstraint('e3', 'e2', 1, 2, 'c2')
    network = TemporalNetwork([c1, c2])

    checker = DCCheckerBE(network)
    feasible, conflict = checker.is_controllable()
    assert(feasible)

    checker = DCCheckerMILP(network)
    feasible, _ = checker.is_controllable()
    assert(feasible)


test_simple_bucket_elim()
test_temporal_network()
test_tightest()
test_next_node()
test_next_node_nc()
test_conflict()
test_dc_0()
test_dc_1()
test_dc_2()
test_dc_3()
test_dc_4()
test_dc_5()
test_dc_6()
test_dc_7()
test_dc_8()
test_dc_9()
test_dc_10()
test_dc_11()
print("All tests passed.")
