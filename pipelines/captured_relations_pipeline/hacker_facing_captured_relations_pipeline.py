import langchain as lc
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel, Field, validator
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
import openai
import pathlib
import os
import json
from pprint import pprint
import yaml
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory


class SingleRelation(BaseModel):
    VariableOneName: str
    VariableTwoName: str
    SupportingText: str
    Reasoning: str
    RelationshipClassification: str
    
    @validator("RelationshipClassification")
    def allowed_classifications(cls, field):
        if field.lower() in {"direct", "inverse", "not applicable", "uncorrelated"}:
            return field
        else:
            raise ValueError(f"Invalid Relationship Type {{{field}}}")


class ListOfRelations(BaseModel):
    Relations: list[SingleRelation]


def extract_relationships(data, set_prompt=None, verbose = False, model = None, debug_path=None, key=None):
    """
    12/19/2023 (Function Last Updated)
    Data should be a python dictionary cleaned of all ground truth data. 
    Verbose triggers storage of information into debug files, this may break depending on where you run this script from as it depends on relative paths.
    Model specifies LLM to be used. (This file was only tested with OpenAI LLMs)
    Verbatim feeds the exact formatting of the dictionary found in the ground truth encoding into the prompt. (Minus the ground truth data)
    Verbatim will make it hard for the model to decide whether or not to include fields that were not in ground truth if you modify the SingleRelation class.
    debug_path, path to the file where verbose will dump debug information
    """

    # Extracts the full text of a paper into "processed_text", extracts all relevant relationships into "relationships".
    processed_text = data["PaperContents"]
    relationships = extract_all_ordered_pairs(data)

    # Create Parser to ensure correct JSON formatting of LLM outputs.
    parser = PydanticOutputParser(pydantic_object=ListOfRelations) #Refers to a class called SingleRelation.

    # Create the plain text prompt. Used some of langchain's functions to automatically create formated prompts. 
    prompt = PromptTemplate(
        template=set_prompt,
        input_variables=["text", "relationships"],
        partial_variables={"format_instructions":parser.get_format_instructions}
    )
    input_text = prompt.format_prompt(text=processed_text, relationships=relationships).to_string()

    # Adds the prompt fed in to the LLM to a debug file so you can inspect it.
    if verbose:
        with open(debug_path / "MultiVariablePipelineInput.txt", "a") as f:  # Appends to the file.
            f.write("="*70+f"\nPaper Analyzed: {data['PaperTitle']}"+"\nLLM Prompt:\n")
            f.write(input_text)
            f.write("\n\n\n")

    # Create LLM.
    model = ChatGoogleGenerativeAI(temperature=.0, google_api_key=key, model=model, safety_settings={HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE})

    # Obtain response from LLM.
    output = model.invoke(input_text)

    # Writes response to a debug file for inspection.
    if verbose:
        with open(debug_path / "MultiVariablePipelineOutput.txt", "a") as f:
            f.write("="*70+f"\nPaper Analyzed: {data['PaperTitle']}"+"\nLLM Pipeline Output:\n")
            f.write(str(output.content))
            f.write("\n")

    # Ensure content is in valid json format with parser.
    parsed_output = parser.parse(output.content) 

    # Prints where debug information has been stored and other telemetry.
    if verbose:
        print(f"\n=========\nSuccessful pipeline completion for {data['PaperTitle'][:50]}, debug information and results saved at {debug_path}")

    # Returns json result in dict format.
    return parsed_output.dict()  


def clean_data(data_path, verbose=False) -> dict:
    """Reads Json and removes list of user predictions"""
    with open(data_path, "r") as f:
        data = json.load(f)
    for relation in data['Relations']:
        relation["RelationshipClassification"] = ""
        relation["IsCausal"] = ""
        relation["SupportingText"] = ""
        relation["Attributes"] = ""
    return data  


def extract_all_ordered_pairs(data):
    #Extract the relationships
    relationships = data.get("Relations", [])
    variable_pairs = [f"Below are {len(relationships)} relations:"]
    # Iterate through each relationship and extract variables
    for relationship in relationships:
        variable_one = relationship.get("VariableOneName", "")
        variable_two = relationship.get("VariableTwoName", "")
        variable_pairs.append(variable_one + " -> " + variable_two)
    relations_text = "\n".join(variable_pairs)
    return relations_text


def captured_relations_pipeline(data_path, settings_path, debug_path: pathlib.Path, key=None):
    with open(settings_path, "r") as f:
        pipeline_settings = yaml.safe_load(f)
        verbose = pipeline_settings["verbose"]
        prompt = pipeline_settings["prompt"]
        model = pipeline_settings["model"]
    cleaned_data = clean_data(data_path, verbose=verbose)
    output = extract_relationships(cleaned_data, set_prompt=prompt, verbose=verbose, model=model, debug_path=debug_path)
    return output


if __name__ == "__main__":
    """This section will not be run automatically if you import this file into another file."""
    # Configures API keys.
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("GOOGLE_API_KEY")
    openai.api_key = key

    # Configures file paths to use when running the pipeline from this file.
    captured_relations_pipeline(data_path="./pipeline_evaluator/standard_dataset/test_paper.json",
                                settings_path="./pipelines/captured_relations_pipeline/pipeline_settings.yaml",
                                debug_path=pathlib.Path("./pipelines/captured_relations_pipeline/debug_outputs"), 
                                key=key)
