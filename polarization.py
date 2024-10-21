import os
import sys
import networkx as nx
import metis
import json
import pandas as pd
import numpy as np
import pickle
import glob
import matplotlib.pyplot as plt
def krackhardt_ratio_pol(G, ms):
    """Computes EI-Index Polarization"""
    EL = 0
    IL = 0

    for e in G.edges(data=True):
        s, t, w = e

        if ms[s] != ms[t]:
            EL += w["weight"]
        else:
            IL += w["weight"]


    return (EL-IL)/(EL+IL)

def extended_krackhardt_ratio_pol(G, ms):
    """Computes Extended EI-Index Polarization"""

    block_a = [k for k in ms if ms[k] == 0]
    block_b = [k for k in ms if ms[k] == 1]

    n_a = len(block_a)
    n_b = len(block_b)


    c_ab = 0
    c_ba = 0
    c_bb=0
    c_aa=0

    for e in G.edges(data=True):
        s, t, w = e
        if ms[s] != ms[t]:
            if ms[s]==0:
                c_ab += w["weight"]
            else:
                c_ba += w["weight"]

        else:
            if ms[s]==0:
                c_aa += w["weight"]

            if ms[s]==1:
                c_bb += w["weight"]


    B_aa = (c_aa)/(n_a*(n_a-1)*0.5)
    B_bb = (c_bb)/(n_b*(n_b-1)*0.5)
    B_ab = (c_ab)/(n_a*n_b)
    B_ba = (c_ba)/(n_a*n_b)

    return -(B_aa+B_bb-B_ab-B_ba)/(B_aa+B_bb+B_ab+B_ba)


def two_communities_partition(G):
    """Function to calculate the split of the network in two graphs
    Parameters:
    G: networkx graph object

    Return:
    metis_community: dictionary with nodes as keys and the community as value
    partition_array: array with the partition of nodes as demanded by the calculation
    of modularity and conductance
    """

    G_temporal=G.copy()
    G_temporal.graph['edge_weight_attr'] = 'weight'
    metis_graph=metis.networkx_to_metis(G_temporal)
    partition=metis.part_graph(metis_graph)
    H = nx.convert_node_labels_to_integers(G_temporal,label_attribute='old_label')
    community_correspondance={}
    metis_community={}
    metis_nodes={}
    for node in H.nodes():
            label_node=H.nodes[node]["old_label"]
            metis_community[label_node]=partition[1][node]
            metis_nodes[partition[1][node]]=metis_nodes.setdefault(partition[1][node],{})
            metis_nodes[partition[1][node]][label_node]=1

    partition_array=[]
    for community in metis_nodes:
        list1=[]
        for node in metis_nodes[community]:
            list1.append(node)
        partition_array.append(set(list1))

    return metis_community,partition_array


def calculate_polarization_metrics(G,partition_array,community_dict):
    """Fuction to calculate the polarization metrics
    params
    G: networkx graph object of the graph
    partition_array: array of node partition as required by modularity and conductance
    community_dict: dictionary with nodes as keys and the community as value

    returns
    pol_metrics: dictionary with the main polarization metrics
    """

    modularity = nx.community.modularity(G, partition_array,weight=None)
    conductance = 1 - nx.conductance(G, partition_array[0], partition_array[1],weight=None)
    ei_index=krackhardt_ratio_pol(G,community_dict)
    ei_index_extended=extended_krackhardt_ratio_pol(G,community_dict)

    dict_metrics={"modularity":modularity
                  ,"conductance":conductance
                  ,"ei_index":ei_index
                  ,"ei_index_extended":ei_index_extended}
    return dict_metrics

def generate_configuration_graph(degree_sequence,original_sequence):
    """Function to generate a configuration graph keeping
    the in and out degree sequence and the strength distribution
    Params
    G: networkx object of the original graph

    returns
    G_rand: networkx object with the random graph
    """

    # Configuration model graph
    G_config = nx.configuration_model(degree_sequence)
    new_sequence = [node for node in G_config.nodes()]
    # Sequence of nodes in the configuration graph
    # Dictionary with the sequence of nodes
    node_sequences=my_dict = dict(zip(new_sequence, original_sequence))
    # THis is a way to have the random graph named as the observed one
    G_config=nx.relabel_nodes(G_config,node_sequences)

    # Keep the largest weakly connected component
    ccs = nx.connected_components(G_config)
    gcc = max(ccs, key=len)
    G_config = G_config.subgraph(gcc)
    return G_config

def process_graph(G):

    G=G.to_undirected()

    ### Set all weights equal to 1
    nx.set_edge_attributes(G, 1, 'weight')


    ccs = nx.connected_components(G)
    gcc = max(ccs, key=len)
    G = G.subgraph(gcc).copy()

    del ccs,gcc

    return G
# Define paths

def main(network_file):


    ## Read graph
    G = nx.read_gml(f"{network_file}")
    G=process_graph(G)

    degree_sequence = [val[1] for val in G.degree]
    original_sequence = [node for node in G.nodes()]

    ### Create metis graph
    metis_graph=metis.networkx_to_metis(G)
    ### Get metis partition
    partition_array=metis.part_graph(metis_graph)

    ## Calculate integer graph that corresponds to the metis graph
    H = nx.convert_node_labels_to_integers(G,label_attribute='old_label')

    ### Get module dictionary using the old labels
    modules={}
    for node in H.nodes():
        label_node = H.nodes[node]["old_label"]
        modules[label_node]=partition_array[1][node]

    ### Calculate partition array need for some metrics
    partition_array=[[],[]]
    for node in sorted(modules):
        partition_array[modules[node]].append(node)

    ## Calculate polarization metrics
    polarization_measures=calculate_polarization_metrics(G,partition_array,modules)

    summary_polarization={}
    summary_polarization["real"]={}
    for key in polarization_measures:
        summary_polarization["real"][key] = polarization_measures[key]

    del G

    summary_polarization["random"]={}

    for i in range(0,100):
        ## Create random graph with degree sequence
        G_temporal = generate_configuration_graph(degree_sequence,original_sequence)

        # Set all weights to 0
        for (u, v, d) in G_temporal.edges(data=True):
            d['weight'] = 1
        ## Create metis graphs
        metis_graph = metis.networkx_to_metis(G_temporal)
        ## Get metis partition
        partition = metis.part_graph(metis_graph)
        H = nx.convert_node_labels_to_integers(G_temporal,label_attribute='old_label')


        # Calculate partitions
        community_metis, partition_array = two_communities_partition(G_temporal)

        ### Calculate randomized metrics
        polarization_measures=calculate_polarization_metrics(G_temporal,partition_array,community_metis)
        for metric in polarization_measures:
            summary_polarization["random"][metric]=summary_polarization["random"].setdefault(metric,[])
            summary_polarization["random"][metric].append(polarization_measures[metric])


if __name__ == '__main__':
    main(sys.argv[1])
