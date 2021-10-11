"""
Provide suggestions for feature categories (based on the knowledge base of OSDR)
"""

import networkx as nx
import csv
import numpy as np
from collections import Counter
import difflib

TOP_K_MATCHES = 10
TOP_K_SUGGESTIONS = 3

def set_of_names():
    unique_names = set()

    path = "autodesk_colab_fullv6_2021_debugged.csv"
    with open(path, 'rt') as f:
        reader = csv.reader(f)
        data = list(reader)

    for i in range(len(data)):
        unique_names.add(data[i][2])

    return unique_names


def suggestion(name):
    path = "autodesk_colab_fullv6_2021_debugged.csv"
    with open(path, 'rt') as f:
        reader = csv.reader(f)
        data = list(reader)

    component_basis, input_flow, output_flow, subfunction_basis, manufac_type = [], [], [], [], []
    component_basis_, input_flow_, output_flow_, subfunction_basis_, manufac_type_ = [], [], [], [], []

    material = []
    material_ = []

    for i in range(len(data)):
        if data[i][2] == name:
            component_basis.append(data[i][5])
            subfunction_basis.append(data[i][9])
            manufac_type.append(data[i][32])
            input_flow.append(data[i][17])
            output_flow.append(data[i][21])
            material.append(data[i][15])

    c1 = Counter(component_basis)
    component_basis_ = [key for key, val in c1.most_common(TOP_K_MATCHES)]

    c2 = Counter(input_flow)
    input_flow_ = [key for key, val in c2.most_common(TOP_K_MATCHES)]

    c3 = Counter(output_flow)
    output_flow_ = [key for key, val in c3.most_common(TOP_K_MATCHES)]

    c4 = Counter(subfunction_basis)
    subfunction_basis_ = [key for key, val in c4.most_common(TOP_K_MATCHES)]

    c5 = Counter(manufac_type)
    manufac_type_ = [key for key, val in c5.most_common(TOP_K_MATCHES)]

    c6 = Counter(material)
    material_ = [key for key, val in c6.most_common(TOP_K_MATCHES)]

    print("Top suggestions for [Material]: ", material_)
    print("Top suggestions for [Component Basis]: ", component_basis_)
    print("Top suggestions for [Input Flow]: ", input_flow_)
    print("Top suggestions for [Output Flow]: ", output_flow_)
    print("Top suggestions for [Subfunction Basis]: ", subfunction_basis_)
    print("Top suggestions for [Manufacturing Type]: ", manufac_type_)


if __name__ == '__main__':

    unique_names = set_of_names()
    counter = 1

    while True:
        print(f"------[Round {counter}]------")

        input_name = input("Step 1 - Please enter the body name: ")
        closest_matches = difflib.get_close_matches(input_name, unique_names, n=TOP_K_MATCHES)

        print("Step 2 - Top matches: ", closest_matches)

        print("------")
        input_match = input("Step 3 - Select a match: ")
        if input_match not in closest_matches:
            print("Error: Input has no match!")
            exit(1)

        print("------")
        print("Step 4 - Suggested features: ")

        suggestion(input_match)
        counter += 1
