from os import path, pardir

def parent_dir(directory: str):
    return path.abspath(path.join(directory, pardir))

script_path = path.abspath(__file__)
root_dir = parent_dir(parent_dir(script_path))
data_dir = path.join(root_dir, "data")
