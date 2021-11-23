# from pygel3d import jupyter_display as jd
import functools
from pathlib import Path
from IPython.display import display, clear_output
from ipywidgets import Button, Dropdown, HTML, HBox, IntSlider, FloatSlider, Textarea, Output, Text
import pandas as pd
import os
import csv
import re
import sys

OS_TYPE = None

THIS_ANNOTATION = []
ALL_ANNOTATION = []

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
                columns = row[1]
                annotated_data.append(columns)
    
    if OS_TYPE == "Windows":
        start = "..\\Assemblies_to_be_filtered\\"
    else:
        start = "../Assemblies_to_be_filtered/"
    end = ".png"
    
    for example in examples:
        
        example = str(example)
        image_name = example[example.find(start)+len(start):example.rfind(end)]
        
        if image_name not in annotated_data:
            files_to_annotate.append(example)
               
    return files_to_annotate
    

def save_annotation(annotation):
    
    annotations_df = pd.DataFrame(annotation, columns=['Assembly_Name', 'Filter_Result'])
    
    annotations_df.to_csv(LABELS_FINAL_OUT_DIR, mode='a', header=False)


def filter_assemblies(examples,
             operating_sys,
             label_info,
             display_fn=display):

    examples = list(examples)
    
    all_annotations = []
    this_annotation = []
    
    current_index = -1

    def set_label_text():
        nonlocal count_label
        count_label.value = '{} assemblies filtered, {} assemblies left'.format(
            len(all_annotations), len(examples) - current_index
        )

    def show_next():
        nonlocal current_index
        global ALL_ANNOTATION
        global THIS_ANNOTATION
        
        # Reset annotation slots
        ALL_ANNOTATION = []
        THIS_ANNOTATION = []
        
        current_index += 1
        set_label_text()
        
        if current_index >= len(examples):
            clear_output(wait=True)
            print('Assembly Filtering Completed.')
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
        
        THIS_ANNOTATION = [] # Reset
        THIS_ANNOTATION.append(name)
        THIS_ANNOTATION.append(annotation_tier1)
        
        save_annotation([THIS_ANNOTATION])
        
        show_next()
        
    def draw_tier1():
        
        options_1 = ["Accept", "Reject", "(Not Sure)"]
        
        buttons_tier1 = []
        standard_buttons = []
        custom_buttons = []
        tier1_additional_buttons = []
        
        print(f"[Filtering Assemblies - Progress: {current_index+1}/{len(examples)}]")
        print("--------------------------")
          
        # Tier 1 Label Options

        print("Do you accept this assembly as relevant?")
        for label in options_1:

            btn = Button(description=label)
            
            if label == "Accept":
                btn.style.button_color = 'lightgreen'
            if label == "Reject":
                btn.style.button_color = 'pink'

            def on_click(label, btn):
                add_annotation_tier1(label)     

            btn.on_click(functools.partial(on_click, label))
            buttons_tier1.append(btn)
        
        box = HBox(buttons_tier1)
        display(box)
        
        display_fn(examples[current_index])
        
        return
    
    set_os_type(operating_sys)
    
    set_label_output(label_info)
    
    count_label = HTML()
    
    display(count_label)

    # Skip all files that have already been annotated

    examples = retrieve_last_annotation(examples) 

    if len(examples) == 0:
        print("All Assemblies Are Filtered / No Assemblies to be Filtered")
        return
    
    set_label_text()
    draw_tier1()

    out = Output()
    display(out)

    show_next()

    return all_annotations
