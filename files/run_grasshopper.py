# Pip install required packages
import os
import json
import compute_rhino3d.Grasshopper as gh
import compute_rhino3d.Util
import rhino3dm

# Set the compute_rhino3d.Util.url, default URL is http://localhost:6500/
compute_rhino3d.Util.url = 'http://localhost:6500/'

# Define path to local working directory
workdir = os.getcwd() + '\\'

# Read input parameters from JSON file
with open(workdir + 'input.json') as f:
    input_params = json.load(f)

# Create the input DataTree
input_trees = []
for key, value in input_params.items():
    tree = gh.DataTree(key)
    tree.Append([{0}], [str(value)])
    input_trees.append(tree)

# Evaluate the Grasshopper definition
output = gh.EvaluateDefinition(
    workdir + 'script.gh',
    input_trees
)


def get_value_from_tree(datatree: dict, param_name: str):
    """Get first value in datatree that matches given param_name"""
    for val in datatree['values']:
        if val["ParamName"] == param_name:
            return val['InnerTree']['{0}'][0]['data']


# Create a new rhino3dm file and save resulting geometry to file
file = rhino3dm.File3dm()
output_geometry = get_value_from_tree(output, "Geometry")
obj = rhino3dm.CommonObject.Decode(json.loads(output_geometry))
file.Objects.AddMesh(obj)

# Save Rhino file to working directory
file.Write(workdir + 'geometry.3dm', 7)

# Parse output data
output_values = {}
for key in ["floor_area", "gross_area", "facade_area", "avg_sun_hours_context", "avg_sun_hours_tower"]:
    val = get_value_from_tree(output, key)
    val = val.replace("\"", "")
    output_values[key] = val

# Save json file with output data to working directory
with open(workdir + 'output.json', 'w') as f:
    json.dump(output_values, f)
