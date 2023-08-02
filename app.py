from io import BytesIO
import json

from viktor import ViktorController, File
from viktor.parametrization import ViktorParametrization, IntegerField, DateField
from viktor.parametrization import NumberField
from viktor.parametrization import Text
from viktor.external.generic import GenericAnalysis
from viktor.views import GeometryAndDataView, GeometryAndDataResult, DataGroup, DataItem


class Parametrization(ViktorParametrization):
    intro = Text(
        "## Grasshopper Analysis app \n This app parametrically generates and analyses a "
        "3D model of a tower using a Grasshopper script. "
        "The sunhour analysis is carried out using the Ladybug plugin for Grasshopper. "
        "Geometry and resulting values are sent back and forth to the Grasshopper script in real-time."
        "\n\n Please fill in the following parameters:"
    )

    # Input fields
    floorplan_width = NumberField("Floorplan width", default=15, min=10, max=18, suffix="m", flex=100, variant='slider', step=1)
    twist_top = NumberField("Twist top", default=0.65, min=0.20, max=1.00, variant='slider', flex=100, step=0.01)
    floor_height = NumberField("Floor height", default=3.5, min=2.5, max=5.0, suffix="m", variant='slider', flex=100, step=0.1)
    tower_height = NumberField("Tower height", default=75, min=20, max=100, suffix="m", flex=100, variant='slider', step=1)
    rotation = NumberField("Rotation", default=60, min=0, max=90, suffix="°", flex=100, variant='slider', step=1)
    month = IntegerField("Month of the year", default=3, min=1, max=12, flex=100)
    date = DateField('Pick a date', flex=100)


class Controller(ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization(width=30)

    @GeometryAndDataView("Geometry", duration_guess=0, update_label='Run Grasshopper')
    def run_grasshopper(self, params, **kwargs):

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
        output_values: File = generic_analysis.get_output_file("output.json", as_file=True)
        output_dict = json.loads(output_values.getvalue())
        data_group = DataGroup(
            *[DataItem(key.replace("_", " "), val) for key, val in output_dict.items()]
        )

        return GeometryAndDataResult(geometry=rhino_3dm_file, geometry_type="3dm", data=data_group)
