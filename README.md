# Systems Literature Analysis Engine

## Usage

Ensure that the only map in your project is the map you want to verify using SLAE. 
You can export a single map with this utility: https://to-kumu-map-blueprint.netlify.app/.
Rename the file "user_input.json".
Run the "flow_control.py" script!
Start a new kumu project and make an empty Causal Loop Diagram map.
Import the file "final_to_kumu_output.json" into the project.
Open the right hand side settings bar and switch to Advanced Settings Mode.
Replace existing code with the following:

@settings {
  template: causal-loop;
  layout: force;
  layout-preset: dense;
  connection-size: 6;
  connection-curvature: 0.28;
}

/* Correctness */
connection {
  color: scale("correctness", #FF2D00, #b9e5a0);
}

/* Papers Examined */
connection {
  scale: scale("papers examined", 1, 2);
}
