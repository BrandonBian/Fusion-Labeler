# Fusion-Labeler

## Tutorial:
Please check out the tutorial video [here](https://youtu.be/LszJEKjMAN8).

## Requirements (make sure to install them first):
1. Python ([from official website](https://www.python.org/downloads/release/python-3810/)): preferably **version 3.8.10**
2. Git ([from official website](https://git-scm.com/downloads))
3. Jupyter Notebook (command: "pip install notebook")
4. pandas (command: "pip install pandas")
5. matplotlib (command: "pip install matplotlib")
6. ipywidgets (command: "pip install ipywidgets")
7. Anaconda ([from official website](https://www.anaconda.com/products/individual))
8. meshplot (command should be run in Anaconda: "conda install -c conda-forge meshplot")
9. igl (command should be run in Anaconda: "conda install -c conda-forge igl")

## Cloning the repository:
Move to the directory on your local machine that you want to put the code and files in.
Then, run the following command to clone the remote repository to your local machine.
```
git clone https://github.com/BrandonBian/Fusion-Labeler.git
```

## General Steps:
0. Delete ALL the placeholders in "Bodies_to_be_labeled/" and "labels/" directories.
1. Put dataset assigned to you to the "Bodies_to_be_labeled/" directory.
2. Go to the "UI/" directory, and copy its path.
3. Open Anaconda prompt and move to the directory by running "cd \[paste the path here\]".
4. Open Jupyter Notebook by running "jupyter notebook".
5. Open "Annotate_Functional_Basis.ipynb" and follow instructions to perform labeling.
