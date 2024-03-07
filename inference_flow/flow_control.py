#Debug
if False:
    import sys
    print(sys.path)
    exit()
import yaml
import pathlib
import json
from utils.matcher.matcher import match_relations_to_papers
from pipelines.captured_relations_pipeline.captured_relations_pipeline import extract_relationships
from utils.parsers.to_kumu_parser import pipeline_to_kumu
from utils.parsers.from_kumu_parser import user_input_to_list_of_relations
from pprint import pprint

"""
Ensure that the only map in your project is the map you want to verify using SLAE, empty the project trash.
You can export a single map with this utility: https://to-kumu-map-blueprint.netlify.app/.
Rename the file "user_input.json".
Run this script!
Start a new kumu project and make an empty Causal Loop Diagram map.
Import the file "final_to_kumu_output.json" into the project.
Click on one of the connections, right click into the correctness and papers examined attributes and ensure they are type numeric.
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
Then you are done.
You may have to reload the webapp to see the changes!
"""

# Obtain list of relations from Kumu or Vensim file
if True:
    with open(pathlib.Path("inference_flow/inference_io/user_input.json"), "r") as f:
        kumu_read = user_input_to_list_of_relations(json.load(f))
        for relation in kumu_read["Relations"]:
            relation["UserOriginalRelationshipClassification"] = relation["RelationshipClassification"]
    with open(pathlib.Path("inference_flow/inference_io/parsed_input.json"), "w") as f:
        json.dump(kumu_read, f)


# Use the matcher to separate the list of relations, resulting in a series of python dictionaries each with a single paper and a list of related relations.
if True:
    matched_papers = match_relations_to_papers(papers_directory="inference_flow/papers_for_inference", input_relations_directory="inference_flow/inference_io/parsed_input.json")
    # print(matched_papers)

if True:
    # Obtain settings by reading in the file
    with open("./pipelines/captured_relations_pipeline/pipeline_settings.yaml", "r") as f:
        pipeline_settings = yaml.safe_load(f)
        verbose = pipeline_settings["verbose"]
        prompt = pipeline_settings["prompt"]
        model = pipeline_settings["model"]

    # For each dictionary run the "extract_relationships" function and settings.
    outputs = list()
    for data in matched_papers:
        if len(data["Relations"]) == 0:
            print("\nPaper", data["PaperTitle"][:50], ": no matching relations")
            continue
        else:
            print("\nParsing", len(data["Relations"]), "relations from", data["PaperTitle"][:50])
        output = extract_relationships(data, set_prompt=prompt, verbose=verbose, model=model, debug_path=pathlib.Path("./pipelines/captured_relations_pipeline/debug_outputs"))
        output["PaperTitle"] = data["PaperTitle"]
        output["PaperDOI"] = data["PaperDOI"]
        for index, relation in enumerate(output["Relations"]):
            relation["UserOriginalRelationshipClassification"] = data["Relations"][index]["UserOriginalRelationshipClassification"]
        outputs.append(output)
    outputs_dict = {"Papers" : outputs}
    debug = True
    if debug:
        with open("inference_flow/inference_io/predicted_relations_output.json", "w") as f:
            f.write(json.dumps(outputs_dict))
with open("inference_flow/inference_io/predicted_relations_output.json", "r") as f:
    outputs_dict = json.load(f)

# Obtain the list of output jsons from the iterative running of extract_relationships and recombine the output jsons into the format required to output to Kumu
# Parse it into Kumu form and save the json in a file.
pipeline_to_kumu(outputs_dict, "inference_flow/inference_io/final_to_kumu_output.json")
