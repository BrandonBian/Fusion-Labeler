import functools
from pathlib import Path
from IPython.display import display, clear_output
from ipywidgets import Button, Dropdown, HTML, HBox, IntSlider, FloatSlider, Textarea, Output, Text
import pandas as pd
import os
import csv
import re
import sys
import numpy as np

# New libraries needed for visualizing 3D mesh
import meshplot as mp
from utils.assembly_graph import AssemblyGraph
import igl

################################ Code Starts Here

OS_TYPE = None

THIS_ANNOTATION = []
ALL_ANNOTATION = []

LABELS_FINAL_OUT_DIR = "../labels/test_labels.csv"

def set_os_type(os_type):
    global OS_TYPE
    
    OS_TYPE = os_type

def get_all_files(directory, pattern):
    return [f for f in Path(directory).glob(pattern)]

def set_label_output(label_info):
    global LABELS_FINAL_OUT_DIR
    
    LABELS_FINAL_OUT_DIR = label_info

def retrieve_last_annotation(examples): # Return list of annotation files without already annotated ones
    
    annotated_data = []
    files_to_annotate = []
    
    df = pd.read_csv(LABELS_FINAL_OUT_DIR)
    if df.empty:
        return examples
        
    with open(LABELS_FINAL_OUT_DIR, "r", encoding="utf-8", errors="ignore") as labels:
        reader = csv.reader(labels, delimiter=',')
        for row in reader:
            if row:  # avoid blank lines
                columns = row[1] + row[2]
                annotated_data.append(columns)
    
    if OS_TYPE == "Windows":
        start = "..\\Bodies_to_be_labeled\\"
    else:
        start = "../Bodies_to_be_labeled/"
    end = ".jpg"
    
    for example in examples:
        
        example = str(example)
        image_name = example[example.find(start)+len(start):example.rfind(end)]
        
        if OS_TYPE == "Windows":
            correct_name = image_name.split("\\")[1]
        else:
            correct_name = image_name.split("/")[1]
        
        assembly_name = correct_name.split("_sep_")[0]
        body_name = correct_name.split("_sep_")[1]
        
        name = assembly_name+body_name

        if name not in annotated_data:
            files_to_annotate.append(example)
               
    return files_to_annotate
    

def save_annotation(annotation):
    
    annotations_df = pd.DataFrame(annotation, columns=['Assembly_Name', 'Body_Name', 'Label_Tier1', 
                                                       'Label_Tier2', 'Label_Tier3'])

    annotations_df.to_csv(LABELS_FINAL_OUT_DIR, mode='a', header=False)


def annotate_functional_basis(examples,
             operating_sys,
             label_info,
             options_1=None,
             display_fn=display):
    """
    Build an interactive widget for annotating a list of input examples.

    Parameters
    ----------
    examples: list(any), list of items to annotate
    options: list(any) or tuple(start, end, [step]) or None
             if list: list of labels for binary classification task (Dropdown or Buttons)
             if tuple: range for regression task (IntSlider or FloatSlider)
             if None: arbitrary text input (TextArea)
    display_fn: func, function for displaying an example to the user

    Returns
    -------
    annotations : list of tuples, list of annotated examples (example, label)
    """

    examples = list(examples)
    
    all_annotations = []
    this_annotation = []
    
    current_index = -1


    def set_label_text():
        nonlocal count_label
        count_label.value = '{} examples annotated, {} examples left'.format(
            len(all_annotations), len(examples) - current_index
        )

    def show_next():
        nonlocal current_index
        global ALL_ANNOTATION
        global THIS_ANNOTATION
        
        # Reset annotation slots
        ALL_ANNOTATION = []
        THIS_ANNOTATION = []
        
#         # TODO - delete the image that has already been annotated
#         os.remove(examples[current_index])
        
        current_index += 1
        set_label_text()
        
        if current_index >= len(examples):
            clear_output(wait=True)
            print('Annotation Completed.')
            return

        clear_output(wait=True)
        draw_tier1()


    def add_annotation_tier1(annotation_tier1):
        global THIS_ANNOTATION
        
        current_name = str(examples[current_index])
        if OS_TYPE == "Windows":
            name = current_name.split("\\")[-1].split(".")[0]
        else:
            name = current_name.split("/")[-1].split(".")[0]
        assembly_name = name.split("_sep_")[0]
        body_name = name.split("_sep_")[1]
        
        THIS_ANNOTATION = [] # Reset
        THIS_ANNOTATION.append(assembly_name)
        THIS_ANNOTATION.append(body_name)
        THIS_ANNOTATION.append(annotation_tier1)
        
        draw_tier2(annotation_tier1)

    def add_annotation_tier1_additional(annotation_tier1_additional):
        global THIS_ANNOTATION
        global ALL_ANNOTATION
        
        current_name = str(examples[current_index])
        if OS_TYPE == "Windows":
            name = current_name.split("\\")[-1].split(".")[0]
        else:
            name = current_name.split("/")[-1].split(".")[0]
        assembly_name = name.split("_sep_")[0]
        body_name = name.split("_sep_")[1]
        
        THIS_ANNOTATION = [] # Reset
        THIS_ANNOTATION.append(assembly_name)
        THIS_ANNOTATION.append(body_name)
        
        # If "Unknown / Can't Tell"
        if annotation_tier1_additional == "[Unknown / Can't Tell]":
        
            THIS_ANNOTATION.append("[Unknown]")
            THIS_ANNOTATION.append("[Skipped]")
            THIS_ANNOTATION.append("[Skipped]")
        
        else:
            
            THIS_ANNOTATION.append("[Skipped]")
            THIS_ANNOTATION.append("[Skipped]")
            THIS_ANNOTATION.append("[Skipped]")
        
        ALL_ANNOTATION.append(THIS_ANNOTATION)
        
        save_annotation(ALL_ANNOTATION)
        
        show_next()
        
        
    def add_annotation_tier2(annotation_tier2):
        
        global THIS_ANNOTATION
        THIS_ANNOTATION.append(annotation_tier2)
        
        draw_tier3(annotation_tier2)

    def add_annotation_tier2_additional(annotation_tier2_additional):
        global THIS_ANNOTATION
        global ALL_ANNOTATION
        
        # If "Unknown / Can't Tell"
        if annotation_tier2_additional == "[Unknown / Can't Tell]":
        
            THIS_ANNOTATION.append("[Unknown]")
            THIS_ANNOTATION.append("[Skipped]")
        
            ALL_ANNOTATION.append(THIS_ANNOTATION)
        
            save_annotation(ALL_ANNOTATION)
        
            show_next()    
        
        else: # Reset the body
            
            clear_output(wait=True)
            draw_tier1()
   
        
    def add_annotation_tier3(annotation_tier3):
             
        global THIS_ANNOTATION
        global ALL_ANNOTATION
        THIS_ANNOTATION.append(annotation_tier3)
        
        ALL_ANNOTATION.append(THIS_ANNOTATION)
        
        save_annotation(ALL_ANNOTATION)
        
        show_next()
        
    def add_annotation_tier3_additional(annotation_tier3_additional):
        global THIS_ANNOTATION
        global ALL_ANNOTATION
        
        # If "Unknown / Can't Tell"
        if annotation_tier3_additional == "[Unknown / Can't Tell]":
        
            THIS_ANNOTATION.append("[Unknown]")
        
            ALL_ANNOTATION.append(THIS_ANNOTATION)
        
            save_annotation(ALL_ANNOTATION)
        
            show_next()    
        
        else: # Reset the body
            
            clear_output(wait=True)
            draw_tier1()        

    def display_3d_object():

        clear_output(wait=True)
        
        ############################### Draw highlighted 3D object section ###############################
        
        vertices_list = []
        faces_list = []
        face_offset = 0
               

        if OS_TYPE == "Windows":
            assembly_id = str(examples[current_index]).split("\\")[3].split(".jpg")[0].split("_sep_")[0]
            body_id = str(examples[current_index]).split("\\")[3].split(".jpg")[0].split("_sep_")[1]
        else:
            assembly_id = str(examples[current_index]).split("/")[3].split(".jpg")[0].split("_sep_")[0]
            body_id = str(examples[current_index]).split("/")[3].split(".jpg")[0].split("_sep_")[1]            
        
        assembly_dir = Path("Bodies_to_be_labeled")
        assembly_file = ".." / assembly_dir / assembly_id / "assembly.json"

        ag = AssemblyGraph(assembly_file)
        graph = ag.get_graph_networkx()
        
        body_to_highlight = body_id
        highlight_v = None
        highlight_f = None
        
        for index, (node_key, node_data) in enumerate(graph.nodes.data()):
    
            node_obj_file = assembly_file.parent / f"{node_data['body_file']}.obj"

            v, f = igl.read_triangle_mesh(str(node_obj_file))
            faces_list.append(f + face_offset)
            v = np.pad(v.T, ((0, 1), (0, 0)), mode="constant", constant_values=1)

            # Not all bodies have transform

            try:
                transform = np.array(node_data["transform"])

            except:
                print("Error: No Transform!")
                transform = np.identity(4)

            v = transform @ v

            if body_to_highlight in node_key:
                highlight_v = v.T
                highlight_f = f+face_offset

            vertices_list.append(v.T)
            face_offset += v.shape[1]
        
        # Obtain all vertices and faces
        vertices = np.concatenate(vertices_list)
        faces = np.concatenate(faces_list)

        # Show the combined mesh
        p = mp.plot(vertices[:,0:3], faces)

        # Corners of the bounding box
        m = np.min(highlight_v, axis=0)
        ma = np.max(highlight_v, axis=0)

        v_box = np.array([[m[0], m[1], m[2]], [ma[0], m[1], m[2]], [ma[0], ma[1], m[2]], [m[0], ma[1], m[2]],
                          [m[0], m[1], ma[2]], [ma[0], m[1], ma[2]], [ma[0], ma[1], ma[2]], [m[0], ma[1], ma[2]]])

        # Edges of the bounding box
        f_box = np.array([[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], 
                          [7, 4], [0, 4], [1, 5], [2, 6], [7, 3]], dtype=np.int)

        # Draw bounding box
        p.add_edges(v_box, f_box, shading={"line_color": "blue"});


        a = vertices[:,0:3][highlight_f[:,0]]
        b = vertices[:,0:3][highlight_f[:,1]]

        p.add_lines(a, b,  shading={"line_color": "red"});

        ##################################################################################################
        
        draw_tier1()            
        
    def draw_tier1():
        
        additional_tier1 = ["[Unknown / Can't Tell]", "[Skip Entire Body]"]
        display_3d = ["[Display 3D Object]"]
        
        buttons_tier1 = []
        standard_buttons = []
        custom_buttons = []
        tier1_additional_buttons = []
        
        print(f"[Labeling Functional Basis - Progress: {current_index+1}/{len(examples)}]")
        print("--------------------------")
          
        # Tier 1 Label Options

        print("Functional Basis (Tier 1):")
        for label in options_1:

            btn = Button(description=label)

            def on_click(label, btn):
                add_annotation_tier1(label)     

            btn.on_click(functools.partial(on_click, label))
            buttons_tier1.append(btn)
        
        box = HBox(buttons_tier1)
        display(box)
        
        print("--------------------------")
        print("Additional Options (Tier 1):")

        for label in additional_tier1:
            
            def on_click(label, btn):
                add_annotation_tier1_additional(label) 
        
            btn = Button(description=label)
            
            btn.style.button_color = 'pink'

            btn.on_click(functools.partial(on_click, label))
            tier1_additional_buttons.append(btn)
        
        for label in display_3d:
            
            def on_click(label, btn):
                display_3d_object() 
        
            btn = Button(description=label)
            
            btn.style.button_color = 'lightblue'

            btn.on_click(functools.partial(on_click, label))
            tier1_additional_buttons.append(btn)
        
        box_additional = HBox(tier1_additional_buttons)
        display(box_additional)        
        
        display_fn(examples[current_index])
        
        return

    def draw_tier2(tier1_choice):
         
        
        additional_tier2 = ["[Unknown / Can't Tell]", "[Reset Body]"]
        tier2_additional_buttons = []
        
        # Tier 2 Label Options
        
        buttons_tier2 = []
        
        if tier1_choice == "branch":
            options_2 = ["separate", "distribute"]
        
        elif tier1_choice == "channel":
            options_2 = ["import", "export", "guide", "transfer"]

        elif tier1_choice == "connect":
            options_2 = ["couple", "mix"]

        elif tier1_choice == "control magnitude":
            options_2 = ["actuate", "regulate", "change", "stop"]

        elif tier1_choice == "convert":
            options_2 = ["convert"]
            
        elif tier1_choice == "provision":
            options_2 = ["store", "supply"]   
            
        elif tier1_choice == "signal":
            options_2 = ["sense", "indicate", "process"]
            
        elif tier1_choice == "support":
            options_2 = ["stabilize", "secure", "position"]
            
        else: # No tier 2 function - should never run here (since every option has at least 2 tiers)
            add_annotation_tier2("NONE")
        
        clear_output(wait=True)
        
        
        print(f"[Progress: {current_index+1}/{len(examples)}]")
        print("--------------------------")
        
        print("Functional Basis (Tier 2):")
        
        for label in options_2:
        
            btn = Button(description=label)

            def on_click(label, btn):
                add_annotation_tier2(label)

            btn.on_click(functools.partial(on_click, label))
            buttons_tier2.append(btn)
        
        box = HBox(buttons_tier2)
        
        display(box)       

        
        print("--------------------------")
        print("Additional Options (Tier 2):")

        for label in additional_tier2:
        
            btn = Button(description=label)
            btn.style.button_color = 'pink'

            def on_click(label, btn):
                add_annotation_tier2_additional(label)     

            btn.on_click(functools.partial(on_click, label))
            tier2_additional_buttons.append(btn)
        
        box_additional = HBox(tier2_additional_buttons)
        display(box_additional)
        
        display_fn(examples[current_index])
    
    def draw_tier3(tier2_choice):

        # Tier 2 Label Options
        
        buttons_tier3 = []
        additional_tier3 = ["[Unknown / Can't Tell]", "[Reset Body]"]
        tier3_additional_buttons = []
        
        if tier2_choice == "separate":
            tier3_options = ["divide", "extract", "remove"]

        elif tier2_choice == "transfer":
            tier3_options = ["transport", "transmit"]

        elif tier2_choice == "guide":
            tier3_options = ["translate", "rotate", "allow dof"]

        elif tier2_choice == "couple":
            tier3_options = ["join", "link"]

        elif tier2_choice == "regulate":
            tier3_options = ["increase", "decrease"]

        elif tier2_choice == "change":
            tier3_options = ["increment", "decrement", "shape", "condition"]

        elif tier2_choice == "stop":
            tier3_options = ["prevent", "inhibit"]

        elif tier2_choice == "store":
            tier3_options = ["contain", "collect"]   

        elif tier2_choice == "sense":
            tier3_options = ["detect", "measure"]      
            
        elif tier2_choice == "indicate":
            tier3_options = ["track", "display"]   
            
        else: # No tier 3 function
            add_annotation_tier3("NONE")
            return
        
        clear_output(wait=True)

        print(f"[Progress: {current_index+1}/{len(examples)}]")
        print("--------------------------")
                          
        print("Functional Basis (Tier 3):")
        
        for label in tier3_options:
        
            btn = Button(description=label)

            def on_click(label, btn):
                add_annotation_tier3(label)

            btn.on_click(functools.partial(on_click, label))
            buttons_tier3.append(btn)
        
        box = HBox(buttons_tier3)
        display(box)         
        
        print("--------------------------")
        print("Additional Options (Tier 3):")

        for label in additional_tier3:
        
            btn = Button(description=label)
            btn.style.button_color = 'pink'

            def on_click(label, btn):
                add_annotation_tier3_additional(label)     

            btn.on_click(functools.partial(on_click, label))
            tier3_additional_buttons.append(btn)
        
        box_additional = HBox(tier3_additional_buttons)
        display(box_additional)
        
        display_fn(examples[current_index])
    
    set_os_type(operating_sys)
    
    set_label_output(label_info)
    
    count_label = HTML()
    
    display(count_label)

    # Skip all files that have already been annotated

    examples = retrieve_last_annotation(examples) 
    
    if len(examples) == 0:
        print("All Files Are Annotated / No Files to be Annotated")
        return
    
    set_label_text()
    draw_tier1()

    out = Output()
    display(out)

    show_next()

    return all_annotations
