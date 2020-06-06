import matplotlib.pyplot as plt
import networkx as nx
import math

def distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

class LDGPlot():
    '''
    Given a reference to labeled distance graph LDG,
    plot the graph.
    Assumes LDG is unmodified during initialization.
    '''
    def __init__(self, g):
        self.ldg = g

        # Find uncontrollable nodes
        self.u_nodes = set()
        for e in self.ldg.edges(data=True):
            _, _, data = e
            if data['labelType'] is not None:
                self.u_nodes.add(data['label'])
        self.c_nodes = set(self.ldg.nodes()).difference(self.u_nodes)

        # Compute layout
        # self.pos = nx.layout.spring_layout(self.ldg)
        # self.pos = nx.random_layout(self.ldg)
        self.pos = nx.planar_layout(self.ldg)
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None

        # Parameters
        self.curve_ratio = 0.2


    def plot(self):
        '''
        Plot the current LDG.
        Notice that a node can have attributes 'color'.
        And an edge can have attributes 'color', 'linewidth' and 'linestyle'.
        '''
        pos = self.pos

        curr_nodes = set(self.ldg.nodes())
        c_nodes = list(curr_nodes.intersection(self.c_nodes))
        u_nodes = list(curr_nodes.intersection(self.u_nodes))

        labels = {}
        node2data = {}
        for v, data in self.ldg.nodes(data=True):
            labels[v] = v
            node2data[v] = data

        node_color = [node2data[v]['color'] if 'color' in node2data[v] else 'w' for v in c_nodes]
        nx.draw_networkx_nodes(self.ldg, pos, nodelist=c_nodes, node_shape = 'o', node_color = node_color, node_size = 250, alpha = 1, linewidths=1, edgecolors= 'black')
        node_color = [node2data[v]['color'] if 'color' in node2data[v] else 'w' for v in u_nodes]
        nx.draw_networkx_nodes(self.ldg, pos, nodelist=u_nodes, node_shape = 's', node_color = node_color, node_size = 250, alpha = 1, linewidths=1, edgecolors= 'black')
        nx.draw_networkx_labels(self.ldg, pos, labels, font_size=10)

        ax = plt.gca()

        for e in self.ldg.edges(data=True, keys=True):
            s, t, key, data = e
            linestyle = '-'
            if 'linestyle' in data:
                linestyle = data['linestyle']
            color = 'black'
            if 'color' in data:
                color = data['color']
            linewidth = 1
            if 'linewidth' in data:
                linewidth = data['linewidth']
            ax.annotate("",
                        xy=pos[t], xycoords='data',
                        xytext=pos[s], textcoords='data',
                        arrowprops=dict(arrowstyle="->", color=color,
                                        linestyle=linestyle,
                                        linewidth=linewidth,
                                        shrinkA=8, shrinkB=8,
                                        patchA=None, patchB=None,
                                        connectionstyle="arc3,rad=rrr".replace('rrr',str(self.curve_ratio*key + self.curve_ratio)
                                        ),
                                        ),
                        )
            weight = data['weight']
            label = ""
            if data['labelType'] == 'lower':
                label = "L:" + data['label'] + ":"
            elif data['labelType'] == 'upper':
                label = "U:" + data['label'] + ":"
            pos_distance = distance(pos[s], pos[t])
            pos_delta = pos[t] - pos[s]
            pos_label = (pos[s] + pos[t]) /2
            sine = pos_delta[1] / pos_distance
            cosine = pos_delta[0] / pos_distance
            half_distance = (self.curve_ratio * key + self.curve_ratio)/2
            pos_offset = [sine * half_distance * pos_distance, -cosine * half_distance * pos_distance]
            ax.annotate("{}{}".format(label, weight),
                        xy=pos_label + pos_offset, xycoords='data')


        if self.xmin is not None:
            plt.axis('equal')
            ax.set(xlim=(self.xmin, self.xmax), ylim=(self.ymin, self.ymax))
        else:
            self.xmin, self.xmax, self.ymin, self.ymax = plt.axis('equal')
        plt.show()



if __name__ == '__main__':
    from dc_be import eliminate
    G = nx.MultiDiGraph()
    G.add_nodes_from(['e1', 'e2', 'e3'])
    G.add_edges_from([('e1', 'e2', {'label': None, 'labelType': None, 'weight': 5}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': 'lower', 'weight': 0}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': None, 'weight': 10}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': None, 'weight': 11}),
                      ('e1', 'e3', {'label': 'e3', 'labelType': None, 'weight': 12}),
                      ('e3', 'e1', {'label': 'e3', 'labelType': 'upper', 'weight': -5}),
                      ('e3', 'e1', {'label': 'e3', 'labelType': None, 'weight': 14})])

    p = LDGPlot(G)
    p.plot()

    eliminate(G, 'e3')

    p.plot()

