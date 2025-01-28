import viktor as vkt
import datetime
import json
import rhino3dm
from pathlib import Path


class Parametrization(vkt.ViktorParametrization):
    intro = vkt.Text(
        "## Grasshopper Analysis app \n This app parametrically generates and analyses a "
        "3D model of a tower using a Grasshopper script. "
        "The sun hour analysis is carried out using the Ladybug plugin for Grasshopper. "
        "Geometry and resulting values are sent back and forth to the Grasshopper script in real-time."
        "\n\n Please fill in the following parameters:"
    )

    floorplan_width = vkt.NumberField("Floorplan width", default=15, min=10, max=18, suffix="m", flex=100, variant='slider', step=1)
    twist_top = vkt.NumberField("Twist top", default=0.65, min=0.20, max=1.00, variant='slider', flex=100, step=0.01)
    floor_height = vkt.NumberField("Floor height", default=3.5, min=2.5, max=5.0, suffix="m", variant='slider', flex=100, step=0.1)
    tower_height = vkt.NumberField("Tower height", default=75, min=20, max=100, suffix="m", flex=100, variant='slider', step=1)
    rotation = vkt.NumberField("Rotation", default=60, min=0, max=90, suffix="°", flex=100, variant='slider', step=1)
    date = vkt.DateField('Date for the sun hour analysis', default=datetime.date.today(), flex=100)


class Controller(vkt.ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization(width=30)

    @vkt.GeometryView("Geometry", duration_guess=5, update_label='Run Grasshopper', x_axis_to_right=True)
    def run_grasshopper(self, params, **kwargs):

        # Replace datetime object with month and day
        date: datetime.date = params["date"]
        params["month"] = date.month
        params["day"] = date.day
        params.pop("date")

        grasshopper_script_path = Path(__file__).parent / "sunlight_analysis.gh"
        script = vkt.File.from_path(grasshopper_script_path)
        input_parameters = dict(params)

        # Run the Grasshopper analysis and obtain the output data
        analysis = vkt.grasshopper.GrasshopperAnalysis(script=script, input_parameters=input_parameters)
        analysis.execute(timeout=30)
        output = analysis.get_output()

        # Convert output data to mesh
        file3dm = rhino3dm.File3dm()
        obj = rhino3dm.CommonObject.Decode(json.loads(output["values"][0]["InnerTree"]['{0}'][0]["data"]))
        file3dm.Objects.Add(obj)

        # Write to geometry_file
        geometry_file = vkt.File()
        file3dm.Write(geometry_file.source, version=7)
        return vkt.GeometryResult(geometry=geometry_file, geometry_type="3dm")
