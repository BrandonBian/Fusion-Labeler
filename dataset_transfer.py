"""
Transfer the images (PNG files) from original (a02) dataset to the current ones
"""
import os
import shutil
import glob
from tqdm import tqdm


def dataset_transfer(original, current):
    current_assemblies = os.listdir(current)
    original_assemblies = os.listdir(original)

    for current_assembly in tqdm(current_assemblies, desc="Transferring the assembly files..."):
        for original_assembly in original_assemblies:
            if original_assembly == current_assembly:
                for pngfile in glob.iglob(os.path.join(original_dataset_path+'\\'+original_assembly, "*.png")):
                    shutil.copy(pngfile, current_dataset_path+'\\'+current_assembly)

                for objfile in glob.iglob(os.path.join(original_dataset_path+'\\'+original_assembly, "*.obj")):
                    shutil.copy(objfile, current_dataset_path+'\\'+current_assembly)

if __name__ == "__main__":
    original_dataset_path = "E:\\a2\\a2\\a2\\a02_dedup"
    current_dataset_path = "data"

    dataset_transfer(original_dataset_path, current_dataset_path)
