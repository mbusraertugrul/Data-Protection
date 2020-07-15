# -*- coding: utf-8 -*-

import networkx as nx
import matplotlib.pyplot as plt
from random import choice
import numpy as np


def draw_graph(g, perturbation, layout):
    nx.draw_networkx(g, with_labels=True, pos=layout, node_size=5, font_size=10, font_color='r', arrowsize=3)
    plt.title(perturbation)
    plt.draw()
    plt.show()
    plt.close()


def naive_anonymization(g):
    """
    It anonymises the nodes in the graph.
    Bob, Alice becomes 1,2
    Parameters
    ----------
    g : Graph
    """
    mapping = {}
    anonymized_number = 0;

    for n in g:
        mapping[n] = anonymized_number
        anonymized_number += 1;

    return nx.relabel_nodes(g, mapping)


def perturbation(graph, percentage):
    """
    It makes perturbation and create new graph from the original one.
    Parameters
    ----------
    graph : Graph
    percentage : percentage of perturbation
    """
    g = graph.copy()
    edge_number_deletion = int(len(g.edges()) * percentage)

    deleted_edges = []

    for i in range(edge_number_deletion):
        random_edge = choice(list(g.edges()))
        g.remove_edges_from([random_edge])
        deleted_edges.append(random_edge)

    while (edge_number_deletion > 0):

        first_node = choice(list(g.nodes()))
        second_node = choice(list(g.nodes()))

        if (second_node == first_node) or (g.has_edge(first_node, second_node) in deleted_edges):
            continue
        else:
            g.add_edge(first_node, second_node)
            edge_number_deletion -= 1
    return g


def calculate_measures(g):
    """
    It calculates the main measures of graph such as Density, Average closeness and betweenness centrality,
    Clustering coefficient.
    Parameters
    ----------
    g : Graph
    """

    N = g.number_of_nodes()
    L = g.number_of_edges()
    # Density for directed graph L / (N * (N-1))
    D = float(L) / float((N * (N - 1)))
    closeness = nx.closeness_centrality(g)
    betweenness = nx.betweenness_centrality(g)
    # Computes graph transitivity, the fraction of all possible triangles present in G.
    GC = nx.transitivity(g)
    print("Density  : ", D)
    print("closeness :", np.mean(np.array(list(closeness.values()))))
    print("betweenness :", np.mean(np.array(list(betweenness.values()))))
    print("clustering coefficient: " + str(GC))


def create_neighbor_list(g, root_node, iteration_number):
    """
    It finds neighbors of a node (if we are calculating h2 or more it also finds neighbors of neighbors etc)
    Parameters
    ----------
    g : Graph
    root_node : The root node we are searching for its neighbours.
    iteration_number: Level of H - 1
    """
    neighbors = set([root_node])

    for i in range(iteration_number):
        neighbors = set((neigh for neighbor in neighbors for neigh in g[neighbor]))

    return neighbors


def create_degree_list(g, i):
    """
    It creates the degree list for neighbors or itself according to H type
    Returns
    ----------
    H 0: The weakest knowledge query which simply returns the label of the node. (0:[1]), (1:[1])
    H1(x) returns the degree of x. (0:[73]), (1:[52])
    H2(x) returns the list of each neighbors’ degree. (0:[15,23,31,32,36....] , 1:[52,12...])
    Parameters
    ----------
    g : Graph
    i : Level of H (Vertex Refinement)
    """
    neighbors = {n: create_neighbor_list(g, n, i - 1) for n in g.nodes()}

    neighbor_degree_list = {}

    for k, v in neighbors.items():
        if i == 0:
            neighbor_degree_list[k] = [1]
        else:
            neighbor_degree_list[k] = sorted([g.degree(n) for n in v])

    return neighbor_degree_list


def create_buckets(equivalence_calc_list, iteration_number, total_node_number, query_type):
    """
    It creates the buckets according to pre defined equivalance calculation list.
    Returns
    ----------
    {"1": [A,B,C,D], "2-4": [[A,B],[A,B,C]...], "5-10": [], "11-20": [], "21-inf": []}
    Parameters
    ----------
    equivalence_calc_list : Pre defined equivalance calculation list
                            if vertex_refinement ? 'Degree List' : 'Isomorphically equal subgraph lists'
    iteration_number : Level of H or Total number of edge facts)
    total_node_number: Total node number of graph
    query_type : Type of query (Vertex Refinement or subgraph )
    """
    eq_classes = create_equivalence_class(equivalence_calc_list)

    can_set_size = {"1": [], "2-4": [], "5-10": [], "11-20": [], "21-inf": []}

    for k, v in eq_classes.items():

        candi_set_size = len(v)

        if candi_set_size == 1:
            can_set_size["1"].append(candi_set_size)
        elif 2 <= candi_set_size and candi_set_size <= 4:
            can_set_size["2-4"].append(candi_set_size)
        elif 5 <= candi_set_size and candi_set_size <= 10:
            can_set_size["5-10"].append(candi_set_size)
        elif 11 <= candi_set_size and candi_set_size <= 20:
            can_set_size["11-20"].append(candi_set_size)
        else:
            can_set_size["21-inf"].append(candi_set_size)

    for k, v in can_set_size.items():

        if query_type == "vertex_refinement":
            print("h" + str(iteration_number) + " bucket " + k + ": " + str(float(sum(v)) / float(total_node_number)))
        elif query_type == "subgraph":
            print(str(iteration_number) + " edge fact for bucket " + k + ": " + str(float(sum(v)) / float(total_node_number)))


def create_equivalence_class(equivalence_calc_list):
    """
    It creates equivalance class.
    For vertex it keeps degrees, for subgraph it keeps nodes which have isomorphic subgraphs
    Returns
    ----------
    0: [0,1,2], 1: [1,0,2,3,4], 2: [1,2,0] -> [0,1,2], [0,1,2,3,4] # Duplicates are eliminated.
    Parameters
    ----------
    equivalence_calc_list : Pre defined equivalance calculation list
    """
    equivalence_class = {}

    for key, v in equivalence_calc_list.items():
        k = tuple(v)

        if k not in equivalence_class:
            equivalence_class[k] = []

        equivalence_class[k].append(key)

    return equivalence_class


def subgraph_queries(size, edge_list):
    """
    Result of this func. keeps nodes as a key and keeps structurally same subgraph's root nodes ,
    {0: [0, 11], 1: [1, 17], 2: [2], 3: [3], 4: [4, 5]........
    Parameters
    ----------
    size : Size of edges to create in subgraph
    edge_list: Produced edges in a breadth-first-search
    """
    subgraph_list = {}

    # k: root node, v: is edges for bfs when we start with root note.
    for k, v in edge_list.items():
        subgraph_list[k] = create_subgraph(v, size, k)

    iso_equal_list = {}

    for k, v in subgraph_list.items():
        i = 1
        iso_equal_list[k] = []

        for l, m in subgraph_list.items():
            if nx.is_isomorphic(v, m):
                iso_equal_list[k].append(l)
                i += 1

    return iso_equal_list


def create_subgraph(sub_edge_list, size, root_node):
    gk = nx.Graph()
    counter = 0

    for u, v in sub_edge_list:

        if counter == size:
            break

        gk.add_edge(u, v)
        counter += 1

    return gk


def main():
    g = nx.read_edgelist('email-Eu-core.txt', '%', nodetype=int, delimiter=" ",
                         create_using=nx.DiGraph())  # nx.karate_club_graph()

    karate_graph = nx.karate_club_graph()

    g = naive_anonymization(g)
    karate_graph = naive_anonymization(karate_graph)

    # Returns a dictionary of positions keyed by node which will help to draw the graph.
    # Node 0: [-0.12168, 0.00195548]
    layout = nx.spring_layout(g)
    layout_karate = nx.spring_layout(karate_graph)

    # draw_graph(g, 0, layout)
    draw_graph(karate_graph, 0, layout_karate)

    pert_graph = perturbation(g, .10)
    pert_graph_karate = perturbation(karate_graph, .20)

    print("Measures for email graph before perturbation")
    calculate_measures(g)
    print("Measures for email graph after %10 perturbation ")
    calculate_measures(pert_graph)

    print("Measures for karate graph before perturbation")
    calculate_measures(karate_graph)
    print("Measures for karate graph after %20 perturbation ")
    calculate_measures(pert_graph_karate)

    layout_pert = nx.spring_layout(pert_graph)
    layout_karate_pert_karate = nx.spring_layout(pert_graph_karate)

    # draw_graph(pert_graph, .10, layout)
    draw_graph(pert_graph_karate, .20, layout_karate_pert_karate)

    # Vertex Refinement
    for i in range(0, 4):
        degree_list = create_degree_list(pert_graph, i)
        create_buckets(degree_list, i, pert_graph.number_of_nodes(), "vertex_refinement")

    # Produce edges in a breadth-first-search starting at source.
    # nx.bfs_edges([0,1,2],0) -> [(0, 1), (1, 2)]
    edge_list = {}
    for n in pert_graph_karate.nodes():
        edge_list[n] = list(nx.bfs_edges(pert_graph_karate, n))

    subgrap_equal_list = subgraph_queries(10, edge_list)
    create_buckets(subgrap_equal_list, 10, pert_graph_karate.number_of_nodes(), "subgraph")

    subgrap_equal_list = subgraph_queries(20, edge_list)
    create_buckets(subgrap_equal_list, 20, pert_graph_karate.number_of_nodes(), "subgraph")

    # subgrap_equal_list = subgraph_queries(30, edge_list)
    # create_buckets(subgrap_equal_list, 30, pert_graph_karate.number_of_nodes(), "subgraph")

if __name__ == '__main__':
    main()