import os
import subprocess
import glob
import sys
import json
import networkx as nx
from scipy.stats import entropy
import math

def add_or_update_edge(graph, source, target, weight):
    if graph.has_edge(source, target):
        # Edge already exists, update the weight
        current_weight = graph[source][target]['weight']
        new_weight = current_weight + weight
        graph[source][target]['weight'] = new_weight
    else:
        # Edge doesn't exist, add it with the given weight
        graph.add_edge(source, target, weight=weight)

def get_community_size(community_info):
    """
    Function to transform the dictionary of nodes and communities to a dictionary with communities and their size
    Parameters
    community_info: dictionary with nodes as keys and communities as values

    Returns
    community_counts: dictionary with communities as keys as size as values

    """
    community_counts = {}
    for community in community_info.values():
        if community_counts.get(community,"error")!="error":
            community_counts[community] += 1
        else:
            community_counts[community] = 1

    return community_counts

def get_community_network(G,community_info,loop_links=True):
    """This function reads the a network and returns the network between the communities given a community partition
    Parameters
    G: network between nodes
    community_info: dictionary with nodes as keys and communities as values
    community_counts: dictionary with communities as keys as size as values
    loop_links:boolean to set if loops are considered

    Returns
    G_community: network between communities
    """
    G_community=nx.DiGraph()
    community_counts=get_community_size(community_info)

    weights=[]
    if loop_links==False:
        for edge in G.edges(data=True):
            if community_info.get(edge[0],"error")!="error" and community_info.get(edge[1],"error")!="error":

                if community_counts.get(community_info[edge[0]],"error")!="error" and community_counts.get(community_info[edge[1]],"error")!="error":
                    if community_info[edge[0]]!=community_info[edge[1]]:
                        add_or_update_edge(G_community, community_info[edge[0]],community_info[edge[1]],weight=edge[2]["weight"])
    else:
        for edge in G.edges(data=True):
            if community_info.get(edge[0],"error")!="error" and community_info.get(edge[1],"error")!="error":

                if community_counts.get(community_info[edge[0]],"error")!="error" and community_counts.get(community_info[edge[1]],"error")!="error":

                        add_or_update_edge(G_community, community_info[edge[0]],community_info[edge[1]],weight=edge[2]["weight"])
    return G_community

def get_community_polarization(community_graph):
    """
    Function to calculate the polarization of the communities given by the ratio
    of loop links divided by the total amount of links
    """
    polarization_dict={}
    for community in community_graph.nodes():
        total=0
        il=0
        el=0
        for target in community_graph[community]:
            total+=community_graph[community][target]["weight"]
            if community==target:
                il+=community_graph[community][target]["weight"]
            else:
                el+=community_graph[community][target]["weight"]
        if total>0:
            polarization_dict[community]=(el-il)/(total)
    return polarization_dict

def get_community_interaction(community_graph,community_dict):
    """
    Function to calculate the polarization of the communities given by the ratio
    of loop links divided by the total amount of links
    """
    community_size=get_community_size(community_dict)
    network_size=sum(community_dict.values())
    outflow={}
    interaction={}
    for community in community_graph.nodes():
        outflow[community]=0
        for community1 in community_graph[community]:
            outflow[community]+=community_graph[community][community1]["weight"]

        interaction[community]=(outflow[community]*community_size[community])/(network_size)
    return interaction

def get_community_entropy(community_graph):
    """
    Function to calculate the entropy of the communities as
    the diversity of communities
    """
    entropy_dict={}
    for community in community_graph.nodes():

        entropy_array=[]
        normalization=0
        for community1 in community_graph[community]:
            normalization+=community_graph[community][community1]["weight"]
        if normalization!=0:
            for community1 in community_graph.nodes():

                if community_graph[community].get(community1,"error")!="error":

                    entropy_array.append(community_graph[community][community1]["weight"]/normalization)
                else:
                    entropy_array.append(0)
            if len(entropy_array)>0:
                entropy_dict[community]=entropy(entropy_array)/math.log(len(entropy_array))
    return entropy_dict


def main(infile):
    # Read configuration file
    config_file = f"{infile}"
    # Open the JSON file
    with open(config_file, 'r') as f:
        # Read the JSON data
        config = json.load(f)

    FILE_PATH = config["path"]
    network_file = config["network_file"]
    community_file = config["community_file"]
    ## Define the main opposed communities
    relevant_communities = [0, 1]
    G = nx.read_gml(f"{FILE_PATH}{network_file}")

    # Open the JSON file
    with open(f"{FILE_PATH}{community_file}", 'r') as f:
        # Read the JSON data
        modules = json.load(f)


    # Calculate community network
    G_com = get_community_network(G,modules)

    # Get regular polarization, entropy and interaction
    community_polarization = get_community_polarization(G_com)
    community_entropy = get_community_entropy(G_com)
    community_interaction = get_community_interaction(G_com,modules)

if __name__ == '__main__':
    main(sys.argv[1])
