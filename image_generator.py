"""
Generate the images to help the labeler during the labeling of the dataset
"""

from PIL import Image, ImageDraw, ImageFont
import sys
import json
import argparse
import time
from pathlib import Path
from collections import Counter
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sn
import pandas as pd
from tools.technet.utils import *
import re
import os
import shutil
from sklearn.decomposition import PCA
from tqdm import tqdm
import cv2

# from tools.technet.main import *

# Prediction selection: "material_id", "material_category_tier_1", "material_category_full"
PREDICTION = "material_id"
# PREDICTION = "material_category_tier_1"
# PREDICTION = "material_category_full"

# Whether to crop the data (e.g., remove JSONs with all default material and default appearance)
CROP_DATA = False

# Whether to group the rare materials into "Other" group (only preserving TOP 20 materials)
GROUP_RARE_MATERIAL = False

# Whether to change default material to non-default appearance (if applicable)
MATERIAL_TO_APPEARANCE = True

# Whether to use the original edge links (the one with edge duplicates)
ORIGINAL_EDGE_FEATURES = True

# Whether using TechNet embeddings (there needs to be TechNet embeddings in dataset)
TECHNET_EMBEDDING = True

# Whether using visual embeddings (there needs to be visual embeddings in dataset)
VISUAL_EMBEDDING = True

# TOP 20 dominant materials
DOMINANT_NUM = 20
DOMINANT_MATERIALS = []


class AssemblyGraph():
    """
    Construct a graph representing an assembly with connectivity
    between B-Rep bodies with joints and contact surfaces
    """

    def __init__(self, assembly_data):
        if isinstance(assembly_data, dict):  # Check if assembly_data is a dictionary
            self.assembly_data = assembly_data
        else:
            if isinstance(assembly_data, str):
                assembly_file = Path(assembly_data)
            else:
                assembly_file = assembly_data
            assert assembly_file.exists()
            with open(assembly_file, "r", encoding="utf-8") as f:
                self.assembly_data = json.load(f)
        self.graph_nodes = []
        self.graph_links = []
        self.graph_edges = []
        self.graph_node_ids = set()
        self.depth = 0

    def get_graph_data(self):
        """Get the graph data as a list of nodes and links"""

        self.graph_nodes = []
        self.graph_links = []
        self.graph_edges = []
        self.graph_node_ids = set()

        self.populate_graph_nodes()  # Populate "nodes" list
        # print(self.graph_nodes)
        self.populate_graph_links()  # Populate "links" list
        # print(self.graph_links)

        # further processing of the graph links (edges)
        self.populate_graph_edges()

        return self.graph_nodes, self.graph_links, self.graph_edges, self.depth

    def get_graph_networkx(self):
        """Get a networkx graph"""
        graph_data = {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": [],
            "links": [],
            "edges": [],
        }

        """Use graph edges (new implementation) or graph links (original)"""

        if not ORIGINAL_EDGE_FEATURES:
            graph_data["nodes"], _, graph_data["links"], _ = self.get_graph_data()  # processed edges as graph links
        else:
            graph_data["nodes"], graph_data["links"], _, _ = self.get_graph_data()  # original links as graph links
        from networkx.readwrite import json_graph
        return json_graph.node_link_graph(graph_data)

    def get_node_label_dict(self, attribute="occurrence_name"):
        """Get a dictionary mapping from node ids to a given attribute"""
        label_dict = {}
        if len(self.graph_nodes) == 0:
            return label_dict
        for node in self.graph_nodes:
            node_id = node["id"]
            if attribute in node:
                node_att = node[attribute]
            else:
                node_att = node["body_name"]
            label_dict[node_id] = node_att
        return label_dict

    def export_graph_json(self, json_file):
        """Export the graph as an networkx node-link format json file"""
        graph_data = {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": [],
            "links": [],
            "edges": [],
        }
        graph_data["nodes"], graph_data["links"], graph_data["edges"], _ = self.get_graph_data()
        with open(json_file, "w", encoding="utf8") as f:
            json.dump(graph_data, f, indent=4)
        return json_file.exists()

    def populate_graph_nodes(self):
        """
        Recursively traverse the assembly tree
        and generate a flat set of graph nodes from bodies
        """
        # First get the root and add it's bodies

        root_component_uuid = self.assembly_data["root"]["component"]  # root > component

        root_component = self.assembly_data["components"][root_component_uuid]  # components > component uuid

        if "bodies" in root_component:  # Add each body of the root component as a node
            for body_uuid in root_component["bodies"]:
                node_data = self.get_graph_node_data(body_uuid)  # Get the node features
                self.graph_nodes.append(node_data)  # Append to the "nodes" list

        # Recurse over the occurrences in the tree
        tree_root = self.assembly_data["tree"]["root"]  # tree > root
        # Start with an identity matrix
        root_transform = np.identity(4)
        self.walk_tree(tree_root, root_transform)
        # Check all our node ids are unique
        total_nodes = len(self.graph_nodes)
        self.graph_node_ids = set([f["id"] for f in self.graph_nodes])  # set of unique ids in self.graph_nodes
        assert total_nodes == len(self.graph_node_ids), "Duplicate node ids found"  # all nodes are unique in ids

    def populate_graph_links(self):
        """Create links in the graph between bodies with joints and contacts"""
        if "joints" in self.assembly_data:
            self.populate_graph_joint_links()
        if "as_built_joints" in self.assembly_data:
            self.populate_graph_as_built_joint_links()
        if "contacts" in self.assembly_data:
            self.populate_graph_contact_links()

    # TODO: function to process graph links to eliminate duplicates

    def populate_graph_edges(self):

        link_ids = set([f["id"] for f in self.graph_links])  # Remove duplicates

        for id in link_ids:

            edge_data = {}
            edge_data["id"] = id

            counter = 0
            for link in self.graph_links:
                if link["id"] == id:
                    counter += 1
                    edge_data["source"] = link["source"]
                    edge_data["target"] = link["target"]

                if "type" in link and "joint_type" in link:
                    edge_data["type"] = link["type"] + link["joint_type"]
                else:
                    if "joint_type" in link:
                        edge_data["type"] = link["joint_type"]
                    else:
                        edge_data["type"] = link["type"]

            edge_data["edge_weight"] = counter
            self.graph_edges.append(edge_data)

    def walk_tree(self, occ_tree, occ_transform):
        """Recursively walk the occurrence tree"""
        self.depth = 1

        for occ_uuid, occ_sub_tree in occ_tree.items():  # for each item from the tree root
            self.depth += 1
            occ = self.assembly_data["occurrences"][occ_uuid]  # occurrences > occurrence uuid
            if not occ["is_visible"]:  # not visible, ignore and move on
                continue

            # "@" means matrix multiplication
            occ_sub_transform = occ_transform @ self.transform_to_matrix(occ["transform"])

            # TODO: Consider filtering out bodies that are not visible

            if "bodies" in occ:  # Add each body in the occurrence as a graph node
                for occ_body_uuid, occ_body in occ["bodies"].items():
                    if not occ_body["is_visible"]:
                        continue
                    node_data = self.get_graph_node_data(
                        occ_body_uuid,
                        occ_uuid,
                        occ,
                        occ_sub_transform
                    )
                    self.graph_nodes.append(node_data)  # append node to "nodes" list
            self.walk_tree(occ_sub_tree, occ_sub_transform)  # recursion

    def get_graph_node_data(self, body_uuid, occ_uuid=None, occ=None, transform=None):
        """Add a body as a graph node"""

        body = self.assembly_data["bodies"][body_uuid]  # bodies > body uuid
        node_data = {}
        if occ_uuid is None:
            body_id = body_uuid
        else:
            body_id = f"{occ_uuid}_{body_uuid}"
        node_data["id"] = body_id
        node_data["body_name"] = body["name"]
        node_data["valid_body_name"] = str(body["valid_body_name"])
        node_data["body_type"] = body["type"]
        node_data["body_file"] = body_uuid
        node_data["body_png"] = body["png"]

        try:
            node_data["body_area"] = body["area"]
            node_data["body_volume"] = body["volume"]
        except:
            node_data["body_area"] = 0
            node_data["body_volume"] = 0

        try:
            node_data["material_category"] = body["material"]["category"]

            # Create hierarchy for material category:
            node_data["material_category_tier_1"] = node_data["material_category"].split('.')[0]

        except:
            pass

        node_data["material_name"] = body["material"]["name"]
        node_data["appearance_id"] = body["appearance"]["id"]

        if TECHNET_EMBEDDING:
            try:
                node_data["body_name_embedding"] = body["body_name_embedding"]
            except:
                print("Error: No TechNet embedding detected!")
                exit(1)

        if VISUAL_EMBEDDING:
            try:
                node_data["visual_embedding"] = body["visual_embedding"]
            except:
                print("Error: No visual embedding detected!")
                exit(1)

        # [Preprocessing] Modify appearance_id to correspond to the material_id pool

        try:
            node_data["appearance_id"] = node_data["appearance_id"].split('_')[0]
        except:
            node_data["appearance_id"] = node_data["appearance_id"]

        node_data["appearance_name"] = body["appearance"]["name"]
        node_data["obj"] = body["obj"]

        if PREDICTION == "material_id":  # We want to predict the physical material ID

            node_data["material"] = body["material"]["id"]
            # [Preprocessing] Change default material to non-default appearance

            if MATERIAL_TO_APPEARANCE:
                if node_data["material"] == "PrismMaterial-018":  # default material
                    # non-default appearance
                    if node_data["appearance_id"] != "PrismMaterial-018":
                        node_data["material"] = node_data["appearance_id"]

            if GROUP_RARE_MATERIAL:
                if node_data["material"] not in DOMINANT_MATERIALS:
                    node_data["material"] = "Other"
                    node_data["material_name"] = "Other"

        if PREDICTION == "material_category_tier_1":
            node_data["material"] = node_data["material_category_tier_1"]
            if node_data["material"] == "":
                node_data["material"] = "Unknown"

        if PREDICTION == "material_category_full":
            node_data["material"] = node_data["material_category"]
            if node_data["material"] == "":
                node_data["material"] = "Unknown"

        if occ:
            node_data["occurrence_name"] = occ["name"]
            node_data["valid_occ_name"] = str(occ["valid_occ_name"])
            node_data["occurrence_area"] = occ["physical_properties"]["area"]
            node_data["occurrence_volume"] = occ["physical_properties"]["volume"]


        else:  # TODO: what if body has no corresponding occurrence?
            node_data["occurrence_name"] = "Root"  # Body belongs to root occurrence
            node_data["valid_occ_name"] = "True"
            node_data["occurrence_area"] = 0
            node_data["occurrence_volume"] = 0

        return node_data

    def populate_graph_joint_links(self):
        """Populate directed links between bodies with joints"""
        for joint_uuid, joint in self.assembly_data["joints"].items():
            try:
                # TODO: Consider links between entity_two if it exists
                ent1 = joint["geometry_or_origin_one"]["entity_one"]
                ent2 = joint["geometry_or_origin_two"]["entity_one"]
                # Don't add links when the bodies aren't visible
                body1_visible = self.is_body_visible(ent1)
                body2_visible = self.is_body_visible(ent2)
                if not body1_visible or not body2_visible:
                    continue
                link_data = self.get_graph_link_data(ent1, ent2)
                link_data["type"] = "Joint"
                link_data["joint_type"] = joint["joint_motion"]["joint_type"]
                # TODO: Add more joint features
                self.graph_links.append(link_data)
            except:
                continue

    def populate_graph_as_built_joint_links(self):
        """Populate directed links between bodies with as built joints"""
        for joint_uuid, joint in self.assembly_data["as_built_joints"].items():
            geo_ent = None
            geo_ent_id = None
            # For non rigid joint types we will get geometry
            if "joint_geometry" in joint:
                if "entity_one" in joint["joint_geometry"]:
                    geo_ent = joint["joint_geometry"]["entity_one"]
                    geo_ent_id = self.get_link_entity_id(geo_ent)

            occ1 = joint["occurrence_one"]
            occ2 = joint["occurrence_two"]
            body1 = None
            body2 = None
            if geo_ent is not None and "occurrence" in geo_ent:
                if geo_ent["occurrence"] == occ1:
                    body1 = geo_ent["body"]
                elif geo_ent["occurrence"] == occ2:
                    body2 = geo_ent["body"]

            # We only add links if there is a single body
            # in both occurrences
            # TODO: Look deeper in the tree if there is a single body
            if body1 is None:
                body1 = self.get_occurrence_body_uuid(occ1)
                if body1 is None:
                    continue
            if body2 is None:
                body2 = self.get_occurrence_body_uuid(occ2)
                if body2 is None:
                    continue
            # Don't add links when the bodies aren't visible
            body1_visible = self.is_body_visible(body_uuid=body1, occurrence_uuid=occ1)
            body2_visible = self.is_body_visible(body_uuid=body2, occurrence_uuid=occ2)
            if not body1_visible or not body2_visible:
                continue
            ent1 = f"{occ1}_{body1}"
            ent2 = f"{occ2}_{body2}"
            link_id = f"{ent1}>{ent2}"
            link_data = {}
            link_data["id"] = link_id
            link_data["source"] = ent1
            assert link_data["source"] in self.graph_node_ids, "Link source id doesn't exist in nodes"
            link_data["target"] = ent2
            assert link_data["target"] in self.graph_node_ids, "Link target id doesn't exist in nodes"
            link_data["type"] = "AsBuiltJoint"
            link_data["joint_type"] = joint["joint_motion"]["joint_type"]
            # TODO: Add more joint features
            self.graph_links.append(link_data)

    def populate_graph_contact_links(self):
        """Populate undirected links between bodies in contact"""
        for contact in self.assembly_data["contacts"]:
            ent1 = contact["entity_one"]
            ent2 = contact["entity_two"]
            # Don't add links when the bodies aren't visible
            body1_visible = self.is_body_visible(ent1)
            body2_visible = self.is_body_visible(ent2)
            if not body1_visible or not body2_visible:
                continue
            link_data = self.get_graph_link_data(ent1, ent2)
            link_data["type"] = "Contact"
            self.graph_links.append(link_data)
            # Add a link in reverse so we have a undirected connection
            link_data = self.get_graph_link_data(ent2, ent1)
            link_data["type"] = "Contact"
            self.graph_links.append(link_data)

    def get_graph_link_data(self, entity_one, entity_two):
        """Get the common data for a graph link from a joint or contact"""
        link_data = {}
        link_data["id"] = self.get_link_id(entity_one, entity_two)
        link_data["source"] = self.get_link_entity_id(entity_one)
        assert link_data["source"] in self.graph_node_ids, "Link source id doesn't exist in nodes"
        link_data["target"] = self.get_link_entity_id(entity_two)
        assert link_data["target"] in self.graph_node_ids, "Link target id doesn't exist in nodes"
        return link_data

    def get_link_id(self, entity_one, entity_two):
        """Get a unique id for a link"""
        ent1_id = self.get_link_entity_id(entity_one)
        ent2_id = self.get_link_entity_id(entity_two)
        return f"{ent1_id}>{ent2_id}"

    def get_link_entity_id(self, entity):
        """Get a unique id for one side of a link"""
        if "occurrence" in entity:
            return f"{entity['occurrence']}_{entity['body']}"
        else:
            return entity["body"]

    def get_occurrence_body_uuid(self, occurrence_uuid):
        """Get the body uuid from an occurrence"""
        occ = self.assembly_data["occurrences"][occurrence_uuid]
        # We only return a body_uuid if there is one body
        if "bodies" not in occ:
            return None
        if len(occ["bodies"]) != 1:
            return None
        # Return the first key
        return next(iter(occ["bodies"]))

    def is_body_visible(self, entity=None, body_uuid=None, occurrence_uuid=None):
        """Check if a body is visible"""
        if body_uuid is None:
            body_uuid = entity["body"]
        if occurrence_uuid is None:
            # If we don't have an occurrence
            # we need to look in the root component
            if "occurrence" not in entity:
                body = self.assembly_data["root"]["bodies"][body_uuid]
                return body["is_visible"]
            # First check the occurrence is visible
            occurrence_uuid = entity["occurrence"]
        occ = self.assembly_data["occurrences"][occurrence_uuid]
        if not occ["is_visible"]:
            return False
        body = occ["bodies"][body_uuid]
        return body["is_visible"]

    def transform_to_matrix(self, transform=None):
        """
        Convert a transform dict into a
        4x4 affine transformation matrix
        """
        if transform is None:
            return np.identity(4)
        x_axis = self.transform_vector_to_np(transform["x_axis"])
        y_axis = self.transform_vector_to_np(transform["y_axis"])
        z_axis = self.transform_vector_to_np(transform["z_axis"])
        translation = self.transform_vector_to_np(transform["origin"])
        translation[3] = 1.0
        return np.transpose(np.stack([x_axis, y_axis, z_axis, translation]))

    def transform_vector_to_np(self, vector):
        x = vector["x"]
        y = vector["y"]
        z = vector["z"]
        h = 0.0
        return np.array([x, y, z, h])


def get_input_files(input="data"):
    input_path = Path(input)
    if not input_path.exists():
        sys.exit("Input folder/file does not exist")
    if input_path.is_dir():
        assembly_files = os.listdir(input)

        return assembly_files



def generate_image(assembly_id, body_id, assembly_png_path, body_png_path,
                   body_name, body_material):
    assembly_png = Image.open(assembly_png_path) # Width = 600, Height = 600
    body_png = Image.open(body_png_path)

    img = Image.new('RGB', (1600, 900), color='white')
    draw = ImageDraw.Draw(img)
    draw.line((800, 0, 800, 900), fill=0)
    draw.line((0, 180, 1600, 180), fill=0)

    # Paste the PNGs

    img.paste(assembly_png, (100, 250))
    img.paste(body_png, (900, 250))

    # Add Text Titles
    body_name = "Body: \"" + body_name + "\""
    body_material = "Body Material: \"" + body_material + "\""

    font_title = ImageFont.truetype("C:\Windows\Fonts\Calibri.ttf", 50)
    font_description = ImageFont.truetype("C:\Windows\Fonts\Calibri.ttf", 32)
    draw.text((250, 60), "Assembly", (0, 0, 0), font=font_title)
    draw.text((900, 60), body_name, (0, 0, 0), font=font_title)

    draw.text((900, 120), body_material, (0, 0, 0), font=font_description)


    output_dir = Path("generated_images")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    img_name = assembly_id + '_sep_' + body_id + ".jpg"
    img_path = "generated_images/" + img_name

    img.save(img_path)


if __name__ == "__main__":

    input_files = get_input_files()

    for input_file in tqdm(input_files, desc="Generating Images..."):

        input_file_path = Path("data/" + input_file)
        assembly_files_path = Path("data/" + input_file + '/assembly.json')
        assembly_png_path = Path("data/" + input_file + '/' + "assembly.png")

        # """Directly reading from the JSONs"""

        # with open(assembly_files_path, "r", encoding="utf-8") as f:
        #     assembly_data = json.load(f)
        #

        # f = Image.open(assembly_png_path).show()
        #
        # for body_uuid, body in assembly_data["bodies"].items():
        #
        #     """Body PNG File"""
        #     body_png = body["png"]
        #     body_png_path = Path("data/" + input_file + '/' + body_png)

        """From Assembly Graphs"""

        ag = AssemblyGraph(assembly_files_path)

        graph = ag.get_graph_networkx()  # Change to corresponding NetworkX graphs
        nodes, _, edges, depth = ag.get_graph_data()

        label_dict = ag.get_node_label_dict()

        # nx.draw_circular(graph, connectionstyle="arc3, rad = 0.1", labels=label_dict, with_labels=True)
        # plt.show()

        for node in nodes:
            body_png_path = Path("data/" + input_file + '/' + node["body_png"])

            image_assembly_id = input_file
            image_body_id = node["body_file"]

            body_name = node["body_name"]
            body_material = node["material_name"]

            # Generate the Image corresponding to this body

            generate_image(image_assembly_id, image_body_id, assembly_png_path, body_png_path,
                           body_name, body_material)
