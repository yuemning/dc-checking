import networkx as nx
from .ldgplot import LDGPlot
from .temporal_network import TemporalNetwork, SimpleContingentTemporalConstraint, SimpleTemporalConstraint
from .dc_checker_abstract import DCChecker

class DCCheckerBE(DCChecker):
    """DC Checker class using Bucket Elimination approach.

    This implementation extends STN consistency checking algorithm using
    bucket elimination to STNU DC checking. This algorithm can be visualized.
    """

    def __init__(self, tn):
        self.tn = tn

    def is_controllable(self, visualize=False, visualize_conflict=False):
        """Check the dynamic controllability of network.

        Args:
            visualize: Optional; Whether the process of bucket elimination is
                visualized step by step.
            visualize_conflict: Optional; Whether the final conflict, if any,
                is visualized.

        Returns:
            controllable: controllable or not
            conflict: conflict when network is uncontrollable
        """

        ldg = self.to_ldg()
        feasible, conflict, order = check_dc_bucket_elimination(ldg, visualize=visualize)
        if conflict is not None:

            # Visualization of conflict
            if visualize_conflict:
                ldg_copy = self.to_ldg()
                plot = LDGPlot(ldg_copy)
                for c in conflict[0]:
                    source, target, key, _ = c
                    ldg_copy.edges[source, target, key]['color'] = 'r'
                    ldg_copy.edges[source, target, key]['linewidth'] = 2
                plot.plot()

            tn_conflict = []
            for c in conflict:
                tn_c = [data['constraint'] for (source, target, key, data) in c if 'constraint' in data]
                tn_conflict.append(tn_c)
            return feasible, tn_conflict
        else:
            return feasible, conflict

    def to_ldg(self):
        """Convert the temporal network into a normalized labeled distance graph.

        Returns:
            labeled distance graph
        """

        g = nx.MultiDiGraph()

        for c_id in self.tn.id2constraint:
            c = self.tn.id2constraint[c_id]
            if isinstance(c, SimpleTemporalConstraint):
                if c.ub is not None:
                    g.add_edges_from([(c.s, c.e, {'label': None, 'labelType': None, 'weight': c.ub, 'constraint': [c, 'UB+']})])
                if c.lb is not None:
                    g.add_edges_from([(c.e, c.s, {'label': None, 'labelType': None, 'weight': -c.lb, 'constraint': [c, 'LB-']})])
            elif isinstance(c, SimpleContingentTemporalConstraint):
                # In commonly accepted definition of STNU, for a contingent link, c.ub > c.lb.
                if c.lb == c.ub:
                    g.add_edges_from([(c.s, c.e, {'label': None, 'labelType': None, 'weight': c.ub, 'constraint': [c, 'UB+']}),
                                      (c.e, c.s, {'label': None, 'labelType': None, 'weight': -c.lb, 'constraint': [c, 'LB-']})])
                else:
                    if c.lb > 0:
                        g.add_edges_from([(c.s, c.e + "'", {'label': None, 'labelType': None, 'weight': c.lb, 'constraint': [c, 'LB+']}),
                                          (c.e + "'", c.s, {'label': None, 'labelType': None, 'weight': -c.lb, 'constraint': [c, 'LB-']}),
                                          (c.e + "'", c.e, {'label': c.e, 'labelType': 'lower', 'weight': 0}),
                                          (c.e, c.e + "'", {'label': c.e, 'labelType': 'upper', 'weight': -(c.ub - c.lb), 'constraint': [c, 'UB-', 'LB+']})])
                    elif c.lb == 0:
                        g.add_edges_from([(c.s, c.e, {'label': c.e, 'labelType': 'lower', 'weight': c.lb, 'constraint': [c, 'LB+']}),
                                          (c.e, c.s, {'label': c.e, 'labelType': 'upper', 'weight': -c.ub, 'constraint': [c, 'UB-']})])
                    else:
                        raise Exception

        return g

    def compile_out_nodes(self, nodes, visualize=False):
        """Compile the nodes out of network using bucket elimination.

        Assumes the network does not contain contingent constraints.

        Args:
            nodes: A set of nodes to be eliminated.

        Returns:
            bool: Successful compiltion or not.
            stn: network after compilation
        """

        # The network must not contain any contingent links
        for tc in self.tn.get_constraints():
            if isinstance(tc, SimpleContingentTemporalConstraint):
                raise Exception
        events = self.tn.get_events()
        # The eliminated nodes must be network's events
        for node in nodes:
            if node not in events:
                raise Exception

        ldg = self.to_ldg()
        self.ldg = ldg
        feasible, conflict, order = check_dc_bucket_elimination(ldg, visualize=visualize, eliminate_nodes=nodes)
        compiled_stn = None
        if feasible:
            compiled_stn = dg_to_stn(ldg)
        return feasible, compiled_stn

def dg_to_stn(dg):
    """Compile a distance graph into STN."""

    stcs = []
    edges = dg.edges(data=True)
    for e in edges:
        source, target, data = e
        if 'label' in data and data['label'] is not None:
            raise Exception
        if 'labelType' in data and data['labelType'] is not None:
            raise Exception
        weight = data['weight']
        stc = SimpleTemporalConstraint(source, target, ub=weight)
        stcs.append(stc)

    tn = TemporalNetwork(constraints=stcs)
    return tn

#######################################################################################
## Implementation of bucket elimination algorithm given labeled distance graph (LDG) ##
#######################################################################################

def check_dc_bucket_elimination(graph, full_conflict=True, visualize=False, eliminate_nodes=None):
    """Given a labeled distance graph, check its dynamic controllability.

    Args:
        graph: labeled distance graph converted from a temporal network
        full_conflict: Optional; If full_conflict is True, extract the hybrid
            conflict. Otherwise, directly return the negative cycle as it is
            discovered.
        visualize: Optional; Visualization elimination step by step.
        eliminate_nodes: Optional; A set of nodes to be eliminated.

    Returns:
        feasible: A boolean representing if controllable
        conflict: Conflict returned if uncontrollable
        order: order of elimination of nodes

    Side Effect:
        graph is modified
    """

    order = []
    curr_graph = graph

    plot = None
    if visualize:
        plot = LDGPlot(curr_graph)

    # Main elimination loop
    if eliminate_nodes is None:
        v, nc = next_node(curr_graph)
    else:
        to_eliminate = eliminate_nodes.copy()
        v = None
        nc = None
        if to_eliminate:
            v = to_eliminate.pop(0)

    while v is not None:
        # print("Eliminating node: ", v)
        if visualize:
            plot.plot()
        feasible, nc = eliminate(curr_graph, v, plot=plot)
        if not feasible:
            if full_conflict:
                return False, extract_conflict(nc), order
            else:
                return False, nc, order
        order.append(v)
        if eliminate_nodes is None:
            v, nc = next_node(curr_graph)
        else:
            v = None
            if to_eliminate:
                v = to_eliminate.pop(0)

    if nc is not None:
        if full_conflict:
            return False, extract_conflict(nc), order
        else:
            return False, nc, order

    return True, None, order

def next_node(curr_graph):
    """Given the current graph, return the next node to eliminate.

    Returns:
        v: Node to eliminate
        nc: Negative cycle if any
    """

    nodes = list(curr_graph.nodes())
    if nodes:
        return track_ready_node(curr_graph, nodes[0], [], [])
    else:
        return None, None

def track_ready_node(curr_graph, v, history, history_edges):
    """Helper function to track ready node, unless a negative cycle is found."""

    if v in history:
        idx = history.index(v)
        return None, history_edges[idx:]
    in_edges = curr_graph.in_edges(v, data=True, keys=True)
    for e in in_edges:
        source, _, key, data = e
        if data['weight'] < 0:
            history.append(v)
            history_edges.append(e)
            return track_ready_node(curr_graph, source, history, history_edges)
    return v, None

def extract_conflict(nc):
    """Extract conflict from negative cycle.

    Given a negatice cycle, backtrack any triangulated edges into original
    edges in the graph, and compile the conflict.
    """

    # It is essential that expanded_nc expands the nc in place, i.e.
    # e1 -> e2, e2 -> e3 becomes e1 -> e4, e4 -> e2, e2 -> e3, and not
    # e1 -> e4, e2 -> e3, e4 -> e2.
    expanded_nc = expand_nc(nc)
    conflict = [expanded_nc]
    for e in expanded_nc:
        _, _, _, data = e
        if data['labelType'] == 'lower':
            conflict.append(expand_extension_path(expanded_nc, e))
    return conflict

def expand_nc(nc):
    expanded_nc = []
    for e in nc:
        _, _, _, data = e
        if 'parents' in data:
            expanded_nc = expanded_nc + expand_nc(data['parents'])
        else:
            expanded_nc.append(e)
    return expanded_nc

def expand_extension_path(nc, e):
    _, _, _, data = e
    assert(data['labelType'] == 'lower')
    weight = data['weight']
    curr_weight = weight
    idx = nc.index(e)
    path = [e]
    for i in range(len(nc)):
        curr_idx = (i+idx+1) % len(nc)
        _, _, _, d = nc[curr_idx]
        w = d['weight']
        curr_weight += w
        path.append(nc[curr_idx])
        if curr_weight < 0:
            return path
    raise Exception

def eliminate(curr_graph, v, plot=None):
    """Given the current graph, eliminate v.

    Returns:
        feasible: A boolean
        nc: Any negative cycle found

    Side Effect:
        v is eliminated from curr_graph is feasible.
    """

    ## Join Project

    # Check consistency
    for e_out in curr_graph.out_edges(v, data=True, keys=True):
        for e_in in curr_graph.in_edges(v, data=True, keys=True):
            source, _, key_in, _ = e_in
            _, target, key_out, _ = e_out
            # Check consistency if forms a loop
            if source == target:
                feasible = check_nc(e_in, e_out)
                # print('check feasible: ', feasible)

                # Visualization
                if plot is not None:
                    curr_graph.nodes[v]['color'] = 'r'
                    curr_graph.edges[source, v, key_in]['color'] = 'b' if feasible else 'r'
                    curr_graph.edges[source, v, key_in]['linewidth'] = 1 if feasible else 2
                    curr_graph.edges[v, target, key_out]['color'] = 'b' if feasible else 'r'
                    curr_graph.edges[v, target, key_out]['linewidth'] = 1 if feasible else 2
                    plot.plot()
                    del curr_graph.nodes[v]['color']
                    del curr_graph.edges[source, v, key_in]['color']
                    del curr_graph.edges[source, v, key_in]['linewidth']
                    del curr_graph.edges[v, target, key_out]['color']
                    del curr_graph.edges[v, target, key_out]['linewidth']

                if not feasible:
                    return False, [e_in, e_out]

    # Triangulate
    out_edges = list(curr_graph.out_edges(v, data=True, keys=True)).copy()
    in_edges = list(curr_graph.in_edges(v, data=True, keys=True)).copy()
    for e_out in out_edges:
        for e_in in in_edges:
            source, _, key_in, data_in = e_in
            _, target, key_out, data_out = e_out
            # Triangulate edges
            if not source == target:
                new_edge = triangulate(e_in, e_out)
                # Filter tightest edges
                source, target, data = new_edge
                existing_edges = curr_graph.get_edge_data(source, target)
                if existing_edges == None:
                    existing_edges = {}
                tightest, remove_edges, tighter_edge_idx = filter_tightest_edges(existing_edges, new_edge)

                if plot is None:
                    # Add to ldg if tightest
                    if tightest:
                        # print("adding edge:", e)
                        curr_graph.add_edges_from([new_edge])
                    # Remove any dominated edges
                    # print("removing dominated edges:", remove_edges)
                    curr_graph.remove_edges_from(remove_edges)

                # Visualization
                else:
                    # Add to ldg, if not tightest, will remove next (this is easier for plotting)
                    old_keys = set(existing_edges.keys())
                    curr_graph.add_edges_from([new_edge])
                    updated_keys = set(curr_graph.get_edge_data(source, target).keys())
                    new_key = list(updated_keys.difference(old_keys))[0]

                    curr_graph.nodes[v]['color'] = 'r'
                    curr_graph.edges[source, target, new_key]['linestyle'] = '--'
                    curr_graph.edges[source, target, new_key]['color'] = 'r'
                    curr_graph.edges[source, v, key_in]['color'] = 'r'
                    curr_graph.edges[v, target, key_out]['color'] = 'r'
                    if tighter_edge_idx is not None:
                        curr_graph.edges[source, target, tighter_edge_idx]['color'] = 'y'
                    for e in remove_edges:
                        s, t, k = e
                        curr_graph.edges[s, t, k]['color'] = 'grey'
                    plot.plot()
                    del curr_graph.nodes[v]['color']
                    del curr_graph.edges[source, target, new_key]['linestyle']
                    del curr_graph.edges[source, target, new_key]['color']
                    del curr_graph.edges[source, v, key_in]['color']
                    del curr_graph.edges[v, target, key_out]['color']
                    if tighter_edge_idx is not None:
                        del curr_graph.edges[source, target, tighter_edge_idx]['color']
                    for e in remove_edges:
                        s, t, k = e
                        del curr_graph.edges[s, t, k]['color']

                    # Remove any dominated edges
                    # print("removing dominated edges:", remove_edges)
                    curr_graph.remove_edges_from(remove_edges)
                    if not tightest:
                        curr_graph.remove_edges_from([(source, target, new_key)])

    # Remove eliminated node and edges
    curr_graph.remove_node(v)
    return True, None

def filter_tightest_edges(existing_edges, e):
    """Given a set of existing edges, check if e is tightest.

    e is tightest is no other edge is tighter than e. At the same time, find
    existing edges that can be removed (but not necessarily all of them).
    """

    source, target, data = e
    remove_edges = []
    for k in existing_edges:
        e_data = existing_edges[k]
        if tighter(e_data, data):
            return False, remove_edges, k
        if tighter(data, e_data):
            remove_edges.append((source, target, k))
    return True, remove_edges, None

def tighter(e1, e2):
    if e1['weight'] <= e2['weight']:
        if e1['labelType'] is None:
            return True
        elif e1['labelType'] == e2['labelType'] and e1['label'] == e2['label']:
            return True
    return False

def check_nc(e_in, e_out):
    """Check that e_in, e_out do not form a semi-reducible negative cycle."""

    _, _, _, e_in = e_in
    _, _, _, e_out = e_out
    w_in = e_in['weight']
    w_out = e_out['weight']
    if w_in + w_out >= 0:
        return True
    label_type_in = e_in['labelType']
    label_type_out = e_out['labelType']
    label_in = e_in['label']
    label_out = e_out['label']
    if label_type_in == 'lower' and label_type_out == 'upper' and label_in == label_out:
        return True
    return False

def triangulate(e_in, e_out):
    """Given in edge and out edge, triangulate a child edge."""

    source, _, _, e_in_data = e_in
    _, target, _, e_out_data = e_out
    label_type_in = e_in_data['labelType']
    label_type_out = e_out_data['labelType']
    label_in = e_in_data['label']
    label_out = e_out_data['label']
    w_in = e_in_data['weight']
    w_out = e_out_data['weight']
    new_edge = None
    if label_type_in == 'lower':
        if label_type_out == 'upper':
            if not label_in == label_out:
                if w_in + w_out >= 0:
                    new_edge = {'labelType': 'lower', 'label': label_in, 'weight': w_in + w_out}
                else:
                    new_edge = {'labelType': 'upper', 'label': label_out, 'weight': w_in + w_out}
        elif label_type_out == 'lower':
            new_edge = {'labelType': 'lower', 'label': label_in, 'weight': w_in + w_out}
        else:
            new_edge = {'labelType': 'lower', 'label': label_in, 'weight': w_in + w_out}
    elif label_type_in == None:
        if label_type_out == 'upper':
            new_edge = {'labelType': 'upper', 'label': label_out, 'weight': w_in + w_out}
        elif label_type_out == 'lower':
            new_edge = {'labelType': None, 'label': None, 'weight': w_in + w_out}
        else:
            new_edge = {'labelType': None, 'label': None, 'weight': w_in + w_out}
    else:
        print("ERROR: A negative incoming uppercase edge should not be in triangulation step.")
        raise Exception

    if new_edge is not None:
        if new_edge['labelType'] == 'lower' and new_edge['weight'] < 0:
            new_edge['labelType'] = None
            new_edge['label'] = None
        if new_edge['labelType'] == 'upper' and new_edge['weight'] >= 0:
            new_edge['labelType'] = None
            new_edge['label'] = None
        new_edge['parents'] = [e_in, e_out]
        return (source, target, new_edge)
    else:
        return None
