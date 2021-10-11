#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### Information ###
# This sample code is designed to create a knowledge graph from data supplied from the OSDR
# The data collected includes: Component, System, Functon, Flow, and Material Data
# The edges are denoted by Flow in, Flow out, and Familial Assembly.
# This is a rough code, not following best practices


import networkx as nx
import csv
import numpy as np


def load_data(path="autodesk_colab_fullv6_2021_debugged.csv"):
    with open(path, 'rt') as f:
        reader = csv.reader(f)
        data = list(reader)

    # Sets of unique items

    component_basis_set = set()  # column [5] in CSV
    material_set = set()  # column [15] in CSV
    input_flow_basis_set = set()  # column [17] in CSV
    output_flow_basis_set = set()  # column [21] in CSV
    subfunction_basis_set = set()  # column [9] in CSV
    manufac_type_set = set()  # column [32] in CSV

    ## list of Systems within the dataset
    systems = [item[6] for item in data]
    unique_systems = np.sort(list(set(systems)))

    ## Droping "systems" label from CSV as a unique value ##
    unique_systems = unique_systems[0:len(unique_systems) - 1]

    ####################### LABEL GRAPH for visualization ##############################
    ## Adding Nodes from CSV all component-function combonations based on Common name component Labels ##

    ## List of NetworkX Graphs##
    graph_list = []

    for h in range(len(unique_systems)):

        ## Creating System_level Sub Dataset   ##
        system_data = []
        for q in range(len(data)):
            if unique_systems[h] == data[q][6]:
                system_data.append(data[q])

        ## Intializing Graph ##
        G = nx.DiGraph()

        #################### NODE CREATION ###################################
        ## Adding node and attributes for all data ##
        for i in range(len(system_data)):

            # Generate Node
            G.add_node((system_data[i][0], system_data[i][2]))

            ## Adding Attributes to each node

            ## Component ID ##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][1]] = system_data[i][1]

            ## Name ##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][2]] = system_data[i][2]

            ## Component Basis Name ##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][5]] = system_data[i][5]

            ## Product Name ##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][11]] = system_data[i][11]

            ## Product Basis Name##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][13]] = system_data[i][13]

            ## Material ##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][15]] = system_data[i][15]

            ## Function ##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][9]] = system_data[i][9]

            ## Input Flow ##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][17]] = system_data[i][17]

            ## Output Flow ##
            G.nodes[(system_data[i][0], system_data[i][2])][data[0][21]] = system_data[i][21]

            try:
                G.nodes[(system_data[i][0], system_data[i][2])][data[0][32]] = system_data[i][32]
            except:
                continue

            #####  Hierarchical Functions ###############

            ## Component Function is natively tier 1 ####
            if system_data[i][24] == str(1):

                ## Function Tier 1##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_1_function'] = system_data[i][9]

                ## Function Tier 2##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_2_function'] = ''

                ## Function Tier 3##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_3_function'] = ''

            ## Component Function is natively tier 2 ####
            elif system_data[i][24] == str(2):

                ## Function Tier 1##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_1_function'] = system_data[i][27]

                ## Function Tier 2##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_2_function'] = system_data[i][9]

                ## Function Tier 3##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_3_function'] = ''

            ## Component Function is natively tier 3 ####
            elif system_data[i][24] == str(3):

                ## Function Tier 1##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_1_function'] = system_data[i][30]

                ## Function Tier 2##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_2_function'] = system_data[i][27]

                ## Function Tier 3##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_3_function'] = system_data[i][9]


            ## Component Function does not exist ####
            else:

                ## Function Tier 1##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_1_function'] = ''

                ## Function Tier 2##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_2_function'] = ''

                ## Function Tier 3##
                G.nodes[(system_data[i][0], system_data[i][2])]['tier_3_function'] = ''

        #################### EDGE CREATION ###################################

        ## Adding Edges first by Assembly Data ##

        # for the length of data
        # point 1 take id
        # Pull G node index
        # take child off
        # search data for child of id == id
        # Create G node Index
        # Create edge from gnode index 1 to 2

        node_index = list(G.nodes)
        for k in range(len(G.nodes.data())):
            data_point_1 = node_index[k][0]
            child_of = data[int(data_point_1)][3]

            for j in range(len(G.nodes.data())):
                if child_of == data[int(node_index[j][0])][1]:
                    G.add_edge(node_index[k], node_index[j])
                    G.add_edge(node_index[j], node_index[k])

        # Adding Edges by Flow Data ##

        # ## Input Flow ##
        for l in range(len(G.nodes.data())):
            data_point_1 = node_index[l][0]
            input_flow_from = data[int(data_point_1)][19]

            for m in range(len(G.nodes.data())):
                if input_flow_from == data[int(node_index[m][0])][1]:
                    G.add_edge(node_index[m], node_index[l])
                    G.edges[node_index[m], node_index[l]][data[0][16]] = data[int(data_point_1)][17]

        # ## Output Flow ##
        for n in range(len(G.nodes.data())):
            data_point_1 = node_index[n][0]
            output_flow_from = data[int(data_point_1)][23]

            for p in range(len(G.nodes.data())):
                if output_flow_from == data[int(node_index[p][0])][1]:
                    G.add_edge(node_index[n], node_index[p])
                    G.edges[node_index[n], node_index[p]][data[0][20]] = data[int(data_point_1)][21]

        ## Adding System Knowledge Graph to Graph List #########
        graph_list.append(G)

    # nx.draw(graph_list[0],with_labels = True)
    # print(len(unique_systems))

    return graph_list


def process_data():
    graphs = load_data()

    subfunc_counts, tier1_counts, tier2_counts, tier3_counts, material_counts = [], [], [], [], []
    sys_name_counts = []

    vocab = {
        'component_basis': set(),  # Relevant
        'sys_name': set(),
        'sys_type_name': set(),
        'material_name': set(),  # Relevant
        'subfunction_basis': set(),  # Relevant
        'tier_1_function': set(),
        'tier_2_function': set(),
        'tier_3_function': set(),
        'flow': set(),  # Relevant
        'manufac_type': set(),  # Relevant
    }
    for g in graphs:
        for __, attr in g.nodes(data=True):
            vocab['component_basis'].add(attr['component_basis'])
            vocab['sys_name'].add(attr['sys_name'])
            vocab['sys_type_name'].add(attr['sys_type_name'])
            vocab['material_name'].add(attr['material_name'])
            vocab['subfunction_basis'].add(attr['subfunction_basis'])
            vocab['tier_1_function'].add(attr['tier_1_function'])
            vocab['tier_2_function'].add(attr['tier_2_function'])
            vocab['tier_3_function'].add(attr['tier_3_function'])

            vocab['manufac_type'].add(attr['manufac_type'])

            subfunc_counts.append(attr['subfunction_basis'])
            tier1_counts.append(attr['tier_1_function'])
            tier2_counts.append(attr['tier_2_function'])
            tier3_counts.append(attr['tier_3_function'])

            # sys_name_counts.append(attr['sys_name'])

            # TODO: update material_counts - done
            material_counts.append(attr['material_name'])

        for attr in g.edges(data=True):
            if 'input_flow' in attr[-1]:
                vocab['flow'].add(attr[-1]['input_flow'])
            if 'output_flow' in attr[-1]:
                vocab['flow'].add(attr[-1]['output_flow'])

    # for k, v in vocab.items():
    #     vocab[k] = {s: idx for idx, s in enumerate(sorted(v))}

    for component_basis in vocab['component_basis']:
        for g in graphs:
            for __, attr in g.nodes(data=True):
                if attr['component_basis'] == component_basis:
                    with open(f'OSDR_stats/component_basis-{component_basis}.txt', 'a') as f:
                        f.write(str(attr['name']))
                        f.write("\n")


    for material in vocab['material_name']:
        for g in graphs:
            for __, attr in g.nodes(data=True):
                if attr['material_name'] == material:
                    with open(f'OSDR_stats/material-{material}.txt', 'a') as f:
                        f.write(str(attr['name']))
                        f.write("\n")

    for sub_func in vocab['subfunction_basis']:
        for g in graphs:
            for __, attr in g.nodes(data=True):
                if attr['subfunction_basis'] == sub_func:
                    with open(f'OSDR_stats/subfunction_basis-{sub_func}.txt', 'a') as f:
                        f.write(str(attr['name']))
                        f.write("\n")

    for manufac_type in vocab['manufac_type']:
        for g in graphs:
            for __, attr in g.nodes(data=True):
                if attr['manufac_type'] == manufac_type:
                    with open(f'OSDR_stats/manufac_type-{manufac_type}.txt', 'a') as f:
                        f.write(str(attr['name']))
                        f.write("\n")

    for flow in vocab['flow']:
        for g in graphs:
            for __, attr in g.nodes(data=True):
                if attr['input_flow_basis'] == flow or attr['output_flow_basis'] == flow:
                    with open(f'OSDR_stats/flow-{flow}.txt', 'a') as f:
                        f.write(str(attr['name']))
                        f.write("\n")

if __name__ == '__main__':
    graphs = process_data()
