"""
General purpose evaluator should take in a YAML file which specifies the parameters: type of model, evaluation dataset, type of scoring function, and supporting tools combination
Run the appropriate pipeline with these parameters.
Calculate the score.
Save results, score, predictions(inputs and outputs), other relevant information, in evaluation outputs.
"""
import pathlib
from pipelines.captured_relations_pipeline.captured_relations_pipeline import captured_relations_pipeline
import json
import os
from copy import deepcopy

DATASET_PATH = pathlib.Path("evaluation_datasets/multi_relation_dataset")
SETTINGS_PATH = pathlib.Path("./pipeline_settings.yaml")
DEBUG_PATH = pathlib.Path("evaluation_outputs/captured_relations_results/debug_outputs")
MULTIPAPER = True

def compare(prediction, ground_truth):
    score_dictionary = dict()
    if prediction["RelationshipClassification"].lower() == ground_truth["RelationshipClassification"].lower():
        score_dictionary["RelationshipClassificationScore"] = 1
        print("RelationshipClassification Score ==> success;", ground_truth["RelationshipClassification"])
    else:
        score_dictionary["RelationshipClassificationScore"] = 0
        print("RelationshipClassification Score ==> actual:", ground_truth["RelationshipClassification"], "; predicted:", prediction["RelationshipClassification"])
    
    # if prediction["IsCausal"].lower() == ground_truth["IsCausal"].lower():
    #     score_dictionary["IsCausalScore"] = 1
    #     print("Causal Score ==> success; ", ground_truth["IsCausal"])
    # else:
    #     score_dictionary["IsCausalScore"] = 0
    #     print("Causal Score ==> actual:", ground_truth["IsCausal"], "; predicted:", prediction["IsCausal"])
    return score_dictionary

def evaluate_one_paper(input_file_path, settings_path, strict_length=True, verbose=False, debug_path=None):
    # Read evaluation dataset
    with open(input_file_path) as f:
        ground_truth = json.load(f)
        print("datatype of ground truth", type(ground_truth))    

    # extract_relationships based on settings (which is text and nothing else)
    if True:
        predictions = captured_relations_pipeline(input_file_path, settings_path=settings_path, debug_path=debug_path)
    else:
        predictions = deepcopy(ground_truth)
        # Change predictions for testing
        predictions["PaperContents"] = ""
        predictions["Relations"][0]["RelationshipClassification"] = "inverse"
        print("datatype of prediction", type(predictions))

    # strip full text from ground truth to prevent accidental printing of full text
    ground_truth["PaperContents"] = ""

    # compare to obtain score
    if len(predictions["Relations"]) > len(ground_truth["Relations"]):
        index_max = len(ground_truth["Relations"])
        if strict_length:
            raise Exception("Prediction and Groundtruth lengths do not match")
    elif len(predictions["Relations"]) < len(ground_truth["Relations"]): 
        index_max = len(predictions["Relations"])
        if strict_length:
            raise Exception("Prediction and Groundtruth lengths do not match")
    else:
        index_max = len(predictions["Relations"])
        print("Number of relations in ground truth and predictions match.")

    results: list[dict] = list()
    for relation_index in range(index_max):
        relation = ground_truth["Relations"][relation_index]
        prediction = predictions["Relations"][relation_index]
        results.append(compare(prediction, relation))

    aggregate_results = dict()
    aggregate_results["RelationshipClassificationScore"] = 0
    # aggregate_results["CausalIdentificationScore"] = 0
    for x, result in enumerate(results):
        aggregate_results["RelationshipClassificationScore"] += result["RelationshipClassificationScore"]
        # aggregate_results["CausalIdentificationScore"] += result["IsCausalScore"]
    aggregate_results["RelationshipClassificationScore"] /= len(results)
    # aggregate_results["CausalIdentificationScore"] /= len(results)
    print(aggregate_results)

    with open("./pipelines/captured_relations_pipeline/eval_results/results.txt", "a+") as f:
        f.write(f"\nResults for {input_file_path.name}\n")
        f.write(json.dumps(aggregate_results, indent=2))
        f.write("\n")
        f.write("Predictions\n")
        f.write(json.dumps(predictions, indent=2))
        f.write("\n")
        f.write("Ground Truth\n")
        f.write(json.dumps(ground_truth, indent=2))
        f.write("\n")
    aggregate_results["file"] = input_file_path.name
    return aggregate_results

if MULTIPAPER:
    with open("evaluation_outputs/captured_relations_results/results.txt", "w") as f:
        f.write(f"New multi file evaluation source from path: {DATASET_PATH}")
    dir, _, files = next(os.walk(DATASET_PATH))
    full_evaluator_aggregate_results = []
    for file in files: 
        print("\n\nEvaluating: ", file)
        result = evaluate_one_paper(pathlib.Path(dir)/pathlib.Path(file), settings_path=SETTINGS_PATH, verbose=True, debug_path=DEBUG_PATH)
        full_evaluator_aggregate_results.append(result)
    with open("evaluation_outputs/captured_relations_results/results.txt", "a+") as f:
        f.write("\n\nAggregated_Results:\n")
        for i in full_evaluator_aggregate_results:
            f.write(f"{i['file']}\n")
            f.write(f"{i}\n")
else:
    with open("evaluation_outputs/captured_relations_results/results.txt", "w") as f:
        f.write(f"New single file evaluation")
    INPUT_FILE_PATH = pathlib.Path("evaluation_datasets/multi_relation_dataset/test_paper_2.json")
    result = evaluate_one_paper(INPUT_FILE_PATH, settings_path=SETTINGS_PATH, verbose=True, debug_path=DEBUG_PATH)