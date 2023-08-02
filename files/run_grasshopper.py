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
    return next(
        val['InnerTree']['{0}'][0]['data']
        for val in datatree['values']
        if val["ParamName"] == param_name
    )


# Create a new rhino3dm file and add resulting geometry to file
file = rhino3dm.File3dm()
# output_geometry = output['values'][0]['InnerTree']['{0}'][0]['data']
output_geometry = get_value_from_tree(output, "Geometry")
floor_area = get_value_from_tree(output, "floor_area")
gross_area = get_value_from_tree(output, "gross_area")
floor_area = int(floor_area.replace("\"", ""))
gross_area = int(gross_area.replace("\"", ""))
obj = rhino3dm.CommonObject.Decode(json.loads(output_geometry))
file.Objects.AddMesh(obj)

# Save the rhino3dm file to your working directory
file.Write(workdir + 'geometry.3dm', 7)

# Save the output values to your working directory
with open(workdir + 'output.json', 'w') as f:
    json.dump({"floor_area": floor_area, "gross_area": gross_area}, f)
