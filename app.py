import datetime
import json
from io import BytesIO

import viktor as vkt
from viktor.external.generic import GenericAnalysis


class Parametrization(vkt.ViktorParametrization):
    intro = vkt.Text(
        "## Grasshopper Analysis app \n This app parametrically generates and analyses a "
        "3D model of a tower using a Grasshopper script. "
        "The sun hour analysis is carried out using the Ladybug plugin for Grasshopper. "
        "Geometry and resulting values are sent back and forth to the Grasshopper script in real-time."
        "\n\n Please fill in the following parameters:"
    )

    # Input fields
    floorplan_width = vkt.NumberField(
        "Floorplan width", default=15, min=10, max=18, suffix="m", flex=100, variant='slider', step=1
    )
    twist_top = vkt.NumberField(
        "Twist top", default=0.65, min=0.20, max=1.00, variant='slider', flex=100, step=0.01
    )
    floor_height = vkt.NumberField(
        "Floor height", default=3.5, min=2.5, max=5.0, suffix="m", variant='slider', flex=100, step=0.1
    )
    tower_height = vkt.NumberField(
        "Tower height", default=75, min=20, max=100, suffix="m", flex=100, variant='slider', step=1
    )
    rotation = vkt.NumberField(
        "Rotation", default=60, min=0, max=90, suffix="°", flex=100, variant='slider', step=1
    )
    date = vkt.DateField(
        'Date for the sun hour analysis', default=datetime.date.today(),  flex=100
    )


class Controller(vkt.ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization(width=30)

    @vkt.GeometryAndDataView("Geometry", duration_guess=0, update_label='Run Grasshopper', x_axis_to_right=True)
    def run_grasshopper(self, params, **kwargs):

        # Replace datetime object with month and day
        date: datetime.date = params["date"]
        params["month"] = date.month
        params["day"] = date.day
        params.pop("date")

        # Create a JSON file from the input parameters
        input_json = json.dumps(params)

        # Generate the input files
        files = [('input.json', BytesIO(bytes(input_json, 'utf8')))]

        # Run the Grasshopper analysis and obtain the output files
        generic_analysis = GenericAnalysis(files=files, executable_key="run_grasshopper", output_filenames=[
            "geometry.3dm", "output.json"
        ])
        generic_analysis.execute(timeout=60)
        rhino_3dm_file = generic_analysis.get_output_file("geometry.3dm", as_file=True)
        output_values: vkt.File = generic_analysis.get_output_file("output.json", as_file=True)

        # Create a DataGroup object to display output data
        output_dict = json.loads(output_values.getvalue())
        data_group = vkt.DataGroup(
            *[vkt.DataItem(key.replace("_", " "), val) for key, val in output_dict.items()]
        )

        return vkt.GeometryAndDataResult(geometry=rhino_3dm_file, geometry_type="3dm", data=data_group)
