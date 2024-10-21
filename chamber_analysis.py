import os
import subprocess
import glob
import sys
import networkx as nx
import json

def top_n_keys(input_dict, top_entries):
    """
    Function to remove all the keys except for those with the top N values
    Parameters
    input_dict: input dictionary
    top_entries: number of top entries to keep
    """
    # sort the dictionary
    sorted_items = sorted(input_dict.items(), key=lambda item: item[1], reverse=True)

    # take the top N items
    top_n_items = sorted_items[:top_entries]

    # create the new dictionary
    top_n_dict = dict(top_n_items)

    return top_n_dict

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

def get_topusers_community(modules,node_inflow,number_top_users):
    """
    Function to transform the dictionary of nodes and communities to a dictionary with communities and their size
    :param modules:
    :param module_size
    :param top_users

    :return
    Returns
    community_counts: dictionary with communities as keys as size as values

    """
    user_dict={}
    community_dict={}
    module_size=get_community_size(modules)
    module_size=top_n_keys(module_size,100)
    for user in modules:
        if node_inflow.get(user,"error")!="error":
            if module_size.get(modules[user],"error")!="error":
                community_dict[modules[user]]=community_dict.setdefault(modules[user],{})
                community_dict[modules[user]][user]=node_inflow[user]
    for community in community_dict:
        community_dict[community]=top_n_keys(community_dict[community], number_top_users)
        for user in community_dict[community]:
            if node_inflow[user]>0:
                user_dict[user]=node_inflow[user]
    return user_dict

def get_reversed_graph(graph):
    """
    Function to calculate the reversed graph
    Parameters
    graph: original networkx graph opject

    Returns
    graph_reversed: reversed graph where source are now targets and viceversa
    """
    # new reversed graph object
    graph_reversed = nx.DiGraph()

    # reverse the edges and add them to the new graph
    for u, v, data in graph.edges(data=True):
        weight = data['weight']
        graph_reversed.add_edge(v, u, **data)
    return graph_reversed
def get_inflow(graph):
    """Function to calculate the total inflow and outdegree of users
    Parameters
    graph: networkx graph object

    Returns
    total_inflow: dictionary with nodes as keys and inflow as value
    indegree_dict: dictionary with nodes as keys and indegree as value
    """
    # calculate total inflow for each node
    total_inflow = {}
    for node in graph.nodes():
        inflow = sum(data['weight'] for _, _, data in graph.in_edges(node, data=True))
        total_inflow[node] = inflow
    # Calculate the indegree of the nodes
    indegree_dict = {}
    for node in graph.nodes():
        indegree = graph.in_degree(node)
        indegree_dict[node] = indegree
    return indegree_dict,total_inflow

def dictionary_overlap(dict1, dict2):
    """
    Function to calculate the overlapping keys between two dictionaries.
    This function is symmetric
    Parameters
    dict1: dictionary 1
    dict2: dictionary 2

    Returns
    overlap: dictionary with the overlapping keys
    """
    set1= set(dict1.keys())
    set2=set(dict2.keys())
    common_keys = set1 & set2
    total_keys =set1.union(set2)

    return float(len(common_keys))/float(len(total_keys))

def get_outflow(graph):
    """Function to calculate the total outflow and out degree of users
    Parameters
    graph: networkx graph object

    Returns
    total_outflow: dictionary with nodes as keys and outflow as value
    outdegree_dict: dictionary with nodes as keys and outdegree as value
    """
    # calculate total inflow for each node
    total_outflow = {}
    for node in graph.nodes():
        outflow = sum(data['weight'] for _, _, data in graph.out_edges(node, data=True))
        total_outflow[node] = outflow
    # Calculate the indegree of the nodes
    outdegree_dict = {}
    for node in graph.nodes():
        outdegree = graph.out_degree(node)
        outdegree_dict[node] = outdegree

    return outdegree_dict,total_outflow

def get_chamber_overlap(input_user_chamber):
    """
    Function to calculate the chamber overlap between users
    Parameters
    input_user_chamber: dictionary with the user as keys and the chamber dictionary as value
    user_dict: dictionary of users to consider

    Returns
    chamber_overlap_dict: dictionary with the chamber overlap between users
    """
    chamber_overlap_dict={}
    for i1,user in enumerate(sorted(input_user_chamber)):
        chamber_overlap_dict[user]={}
        for i2,user1 in enumerate(sorted(input_user_chamber)):
            if user!=user1 and i1<i2:
                overlap_value=dictionary_overlap(input_user_chamber[user],input_user_chamber[user1])
                chamber_overlap_dict[user][user1]=overlap_value

    return chamber_overlap_dict

def get_audience(graph,user_dict):
    """
    Function to calculate the audience of each user

    Parameters
    graph: networkx graph object

    Return
    user_audience: dictionary with users as keys and the dictionary of audience as values
    """
    graph_reversed=get_reversed_graph(graph)
    user_audience={}
    for user in graph.nodes():
        if user_dict.get(user,"error")!="error":
            user_audience[user]=list(graph_reversed[user].keys())
    return user_audience

def get_chamber(graph,audience):
    """
    Function to calculate the chamber of each user

    Parameters
    graph: networkx graph object
    audience: dictionary with users as keys and the audience as a value dictionary

    Return
    user_chamber: dictionary with users as keys and the dictionary of chamber as values
    """

    user_chamber={}
    for user in audience:
        for member in audience[user]:
            for target in graph[member]:
                user_chamber[user]=user_chamber.setdefault(user,{})
                user_chamber[user][target]=1
    return user_chamber


def main(input_file):

    # Read configuration file
    config_file = f"{input_file}"
    # Open the JSON file
    with open(config_file, 'r') as f:
        # Read the JSON data
        config = json.load(f)



    FILE_PATH = config["path"]
    network_file = config["network_file"]
    community_file = config["community_file"]
    ## Define the main opposed communities
    relevant_communities = config["relevant_communities"]
    G = nx.read_gml(f"{FILE_PATH}{network_file}")


    # Open the JSON file
    with open(f"{FILE_PATH}{community_file}", 'r') as f:
        # Read the JSON data
        modules = json.load(f)

    # Calculate node degree and flow
    node_indegree,node_inflow = get_inflow(G)
    node_outdegree,node_outflow = get_outflow(G)
    # Dictionary with top users per community
    number_of_top_users = config["number_of_top_users"]
    # Top communities to consider

    top_user_dict = get_topusers_community(modules,node_inflow,number_of_top_users)

    # Filter the node inflow according to the top users
    filtered_top_user_dict = {node: inflow for node, inflow in top_user_dict.items() if modules.get(node) in relevant_communities}

    # Calculate user audience
    user_audience = get_audience(G,filtered_top_user_dict)
    print ("passed_audience")
    # Calculate user chamber
    user_chamber = get_chamber(G,user_audience)
    print ("passed user chamber")
    # Calculate chamber overlap
    chamber_overlap = get_chamber_overlap(user_chamber)

if __name__ == '__main__':

    main(sys.argv[1])
