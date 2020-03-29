import networkx as nx
from ldgplot import LDGPlot

def check_dc_bucket_elimination(graph, full_conflict=True, visualize=False):
    '''
    Given a labeled distance graph, check its dynamic controllability.
    If full_conflict is True, extract the full conflict. Otherwise,
    directly return the negative cycle as it is discovered.
    Return:
    + Boolean: FEASIBLE
    + Conflict: CONFLICT
    + Elimination order: ORDER
    Side Effect: 
    GRAPH is modified
    '''

    order = []
    curr_graph = graph
    eliminated_dict = {}

    #===================
    # Visualization
    #-------------------
    plot = None
    if visualize:
        plot = LDGPlot(curr_graph)
    #===================


    # Main elimination loop
    v, nc = next_node(curr_graph)
    while v is not None:
        # print("Eliminating node: ", v)
        #===================
        # Visualization
        #-------------------
        if visualize:
            plot.plot()
        #===================
        feasible, nc, eliminated_edges = eliminate(curr_graph, v, plot=plot)
        if not feasible:
            if full_conflict:
                return False, extract_conflict(nc), order
            else:
                return False, nc, order
        order.append(v)
        eliminated_dict[v] = eliminated_edges
        v, nc = next_node(curr_graph)

    if nc is not None:
        if full_conflict:
            return False, extract_conflict(nc), order
        else:
            return False, nc, order

    # Reverse pass: compile into dispatchable network
    order_cp = order.copy()
    while order_cp:
        v = order_cp.pop()
        # Add the eliminated edges back
        eliminated_edges = eliminated_dict[v]
        curr_graph.add_node(v)
        curr_graph.add_edges_from(eliminated_edges)

        #===================
        # Visualization
        #-------------------
        if visualize:
            curr_graph.nodes[v]['color'] = 'r'
            plot.plot()
            del curr_graph.nodes[v]['color']
        #===================

        # in edges must all be >= 0
        in_edges = curr_graph.in_edges(v, data=True, keys=True)
        # Any out edges >= 0 must find all extensions until < 0
        out_edges = curr_graph.out_edges(v, data=True, keys=True)
        out_pos_edges = []
        for e in out_edges:
            _, _, _, data = e
            if data['weight'] >= 0:
                out_pos_edges.append(e)

        while out_pos_edges:
            e1 = out_pos_edges.pop()
            _, t1, k1, data1 = e1

            #===================
            # Visualization
            #-------------------
            if visualize:
                curr_graph.nodes[v]['color'] = 'r'
                curr_graph.edges[v, t1, k1]['color'] = 'r'
                plot.plot()
                del curr_graph.nodes[v]['color']
                del curr_graph.edges[v, t1, k1]['color']
            #===================

            t_out_edges = curr_graph.out_edges(t1, data=True, keys=True)
            for e2 in t_out_edges:
                _, t2, k2, data2 = e2
                if data2['weight'] < 0:
                    new_edge = triangulate(e1, e2)
                    # print("Adding edge: ", new_edge)

                    if visualize:
                        #===================
                        # Visualization
                        #-------------------
                        old_edges = curr_graph.get_edge_data(v, t2)
                        if old_edges is None:
                            old_keys = set()
                        else:
                            old_keys = set(old_edges.keys())
                        curr_graph.add_edges_from([new_edge])
                        updated_keys = set(curr_graph.get_edge_data(v, t2).keys())
                        new_key = list(updated_keys.difference(old_keys))[0]

                        curr_graph.nodes[v]['color'] = 'r'
                        curr_graph.edges[v, t1, k1]['color'] = 'r'
                        curr_graph.edges[t1, t2, k2]['color'] = 'r'
                        curr_graph.edges[v, t2, new_key]['color'] = 'r'
                        curr_graph.edges[v, t2, new_key]['linestyle'] = '--'
                        plot.plot()
                        del curr_graph.nodes[v]['color']
                        del curr_graph.edges[v, t1, k1]['color']
                        del curr_graph.edges[t1, t2, k2]['color']
                        del curr_graph.edges[v, t2, new_key]['color']
                        del curr_graph.edges[v, t2, new_key]['linestyle']
                        #=====================
                    else:
                        curr_graph.add_edges_from([new_edge])

                    _, _, data = new_edge
                    if data['weight'] >= 0:
                        out_pos_edges.append((v, t2, 'dummy', data))

    #===================
    # Visualization
    #-------------------
    if visualize:
        plot.plot()

    return True, None, order

def next_node(curr_graph):
    '''
    Given the current graph, return the next node to eliminate.
    Return:
    + Node: V
    + Negative cycle: NC
    '''
    nodes = list(curr_graph.nodes())
    if nodes:
        return track_ready_node(curr_graph, nodes[0], [], [])
    else:
        return None, None

def track_ready_node(curr_graph, v, history, history_edges):
    '''
    Helper function to track ready node, unless a negative cycle is found.
    '''
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
    '''
    Given a negatice cycle NC, backtrack any triangulated edges
    into original edges in LDG, and compile the conflict.
    '''
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
    raise ValueError

def eliminate(curr_graph, v, plot=None):
    '''
    Given the current graph, eliminate v.
    Return:
    + Boolean: FEASIBLE
    + Negative cycle: NC
    Side Effect:
    v is eliminated from curr_graph is feasible.
    '''

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

                #===================
                # Visualization
                #-------------------
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
                #====================

                if not feasible:
                    return False, [e_in, e_out], None



    # Triangulate
    for e_out in curr_graph.out_edges(v, data=True, keys=True):
        for e_in in curr_graph.in_edges(v, data=True, keys=True):
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

                #===================
                # Visualization
                #-------------------
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
                #===================

    # Get edges that will be eliminated
    eliminated_edges = list(curr_graph.out_edges(v, data=True)) + list(curr_graph.in_edges(v, data=True))
    # Remove eliminated node and edges
    curr_graph.remove_node(v)

    return True, None, eliminated_edges

def filter_tightest_edges(existing_edges, e):
    '''
    Given a set of existing edges, check if e is tightest.
    e is tightest is no other edge is tighter than e.
    At the same time, find existing edges that can be removed
    (but not necessarily all of them).
    '''
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
    '''
    Check if the cycle is negative, or has the same label.
    '''
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
    '''
    Given in edge and out edge, triangulate a child edge.
    '''
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
        raise ValueError

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


