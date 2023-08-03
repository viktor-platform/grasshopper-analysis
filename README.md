# sample-grasshopper-analysis
A VIKTOR sample app which runs a Grasshopper script with Ladybug sunhours analysis. 🦗🐞

This app demonstrates how to connect VIKTOR applications to Grasshopper scripts. The app is connected to a Rhino Grasshopper instance running on a server, and allows the user to run a Grasshopper script with a sunhours analysis. A twisting tower is configured through the app parameters, and each time the user updates a parameter, a Grasshopper script runs on the server that performs a sunhours analysis using the popular Ladybug plugin.

The app allows the user to adjust the tower parameters and visualize the resulting geometry and sunhour performance in real-time:

![Screenshot 2023-08-02 163720](https://github.com/viktor-platform/sample-grasshopper-analysis/assets/93203883/9cf0c837-af95-4dd5-90a2-8989bfa7c69c)

The Grasshopper script and worker configuration used for this app can be found in this repo under `files`.

![Screenshot 2023-08-02 155545](https://github.com/viktor-platform/sample-grasshopper-analysis/assets/93203883/dea427a6-93ba-4256-a302-e9ba0087d9ba)
