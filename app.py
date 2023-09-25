import datetime
import json
import os
import tempfile
from pathlib import Path
import compute_rhino3d.Grasshopper as gh
import compute_rhino3d.Util
import rhino3dm

from viktor import ViktorController, File
from viktor.parametrization import ViktorParametrization, DateField, NumberField, ToggleButton, Text, Lookup
from viktor.utils import memoize
from viktor.views import GeometryAndDataView, GeometryAndDataResult, DataGroup, DataItem


class Parametrization(ViktorParametrization):
    intro = Text(
        "# Sunlight Hours Analysis with Grasshopper & Ladybug 🐞 🦗 🦏 \n This app parametrically generates and analyses a "
        "3D model of a tower using a Grasshopper script. "
        "The sun hours analysis is carried out using the Ladybug plugin for Grasshopper. \n "
        "\n Please fill in the following parameters:"
    )

    # Input fields
    floorplan_width = NumberField("Floorplan width", default=15, min=10, max=18, suffix="m", flex=100, variant='slider', step=1)
    twist_top = NumberField("Twist top", default=0.65, min=0.20, max=1.00, variant='slider', flex=100, step=0.01)
    floor_height = NumberField("Floor height", default=3.5, min=2.5, max=5.0, suffix="m", variant='slider', flex=100, step=0.1)
    tower_height = NumberField("Tower height", default=75, min=20, max=100, suffix="m", flex=100, variant='slider', step=1)
    rotation = NumberField("Rotation", default=60, min=0, max=90, suffix="°", flex=100, variant='slider', step=1)
    run_solar_analysis = ToggleButton("Sun Hours Analysis")
    date = DateField("Date for the sun hour analysis", default=datetime.date.today(),  flex=100, visible=Lookup('run_solar_analysis'))

    outro = Text(" ## Start building Grasshopper cloud apps [here](https://community.viktor.ai/t/sunlight-hours-analysis-with-grasshopper-and-ladybug/1250?u=mostafa) 🚀 ")
    ps = Text("PS: If the app starts after an hour of inactivity, it takes an extra 30 seconds to get the Rhino Compute server up and running.")


class Controller(ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization(width=30)

    @GeometryAndDataView("Output", duration_guess=0, update_label='Run Grasshopper')
    def run_grasshopper(self, params, **kwargs):
        # Credentials for Rhino Compute api
        compute_rhino3d.Util.url = os.getenv("RHINO_COMPUTE_URL")
        compute_rhino3d.Util.apiKey = os.getenv("RHINO_COMPUTE_API_KEY")

        # Replace datetime object with month and day
        date: datetime.date = params["date"]
        params["month"] = date.month
        params["day"] = date.day
        params.pop("date")

        # Run Grasshopper file with input parameters
        output = self.evaluate_grasshopper(str(Path(__file__).parent / 'files' / 'script.gh'), params)

        # Create a new rhino3dm file and save resulting geometry to file
        file = rhino3dm.File3dm()
        output_geometry = self.get_value_from_tree(output, "Geometry", index=0)
        output_geometry2 = self.get_value_from_tree(output, "Geometry2")

        obj = rhino3dm.CommonObject.Decode(json.loads(output_geometry))
        file.Objects.AddMesh(obj)

        for data in output_geometry2:
            obj2 = rhino3dm.CommonObject.Decode(json.loads(data))
            file.Objects.Add(obj2)

        # Add solar analysis legend values
        point_x = self.get_value_from_tree(output, "pointsx")
        point_y = self.get_value_from_tree(output, "pointsy")
        solar_vals = self.get_value_from_tree(output, "solar_values")
        for i in range(len(point_y)):
            pointyvalue = float(point_y[i].replace('"', ""))
            pointxvalue = float(point_x[i].replace('"', ""))
            solarv = str(solar_vals[i])
            file.Objects.AddTextDot(text=solarv, location=rhino3dm._rhino3dm.Point3d(pointxvalue, pointyvalue, 0))

        # Add compass orientation
        compass__x = self.get_value_from_tree(output, "compass_x")
        compass__y = self.get_value_from_tree(output, "compass_y")
        comapass__text = self.get_value_from_tree(output, "compass_text")
        for i in range(len(compass__x)):
            compass_xpoint = float(compass__x[i].replace('"', ""))
            compass_ypoint = float(compass__y[i].replace('"', ""))
            compassv= str(comapass__text[i])
            file.Objects.AddTextDot(text=compassv, location=rhino3dm._rhino3dm.Point3d(compass_xpoint,compass_ypoint, 0))

        # Save Rhino file to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".3dm", delete=False, mode="wb")
        temp_file.close()
        file.Write(temp_file.name, 7)
        rhino_3dm_file = File.from_path(Path(temp_file.name))

        # Parse output data
        output_params = ["floor_area", "gross_area", "facade_area"]
        if params.run_solar_analysis:
            output_params.extend(["avg_sun_hours_context", "avg_sun_hours_tower"])

        output_values = {}
        for key in output_params:
            val = self.get_value_from_tree(output, key, index=0)
            output_values[key] = float(val.replace("\"", ""))

        data_items = [
            DataItem('Floor area', output_values["floor_area"], suffix='m²', number_of_decimals=0),
            DataItem('Gross area', output_values["gross_area"], suffix='m²', number_of_decimals=0),
            DataItem('Facade area', output_values["facade_area"], suffix='m²', number_of_decimals=0),
        ]

        if params.run_solar_analysis:
            data_items.extend([
                DataItem('Avg sun hours context', output_values["avg_sun_hours_context"], suffix='h', number_of_decimals=2),
                DataItem('Avg sun hours tower', output_values["avg_sun_hours_tower"], suffix='h', number_of_decimals=2),
            ])

        return GeometryAndDataResult(geometry=rhino_3dm_file, geometry_type="3dm", data=DataGroup(*data_items))

    @staticmethod
    @memoize
    def evaluate_grasshopper(file_path, params):
        # Create the input DataTree
        input_trees = []
        for key, value in params.items():
            tree = gh.DataTree(key)
            tree.Append([{0}], [str(value).lower()])
            input_trees.append(tree)

        return gh.EvaluateDefinition(file_path, input_trees)

    @staticmethod
    def get_value_from_tree(datatree: dict, param_name: str, index=None):
        """Get first value in datatree that matches given param_name"""
        for val in datatree['values']:
            if val["ParamName"] == param_name:
                try:
                    if index is not None:
                        return val['InnerTree']['{0}'][index]['data']
                    return [v['data'] for v in val['InnerTree']['{0}']]
                except:
                    if index is not None:
                        return val['InnerTree']['{0}'][index]['data']
                    return [v['data'] for v in val['InnerTree']['{0;0}']]
