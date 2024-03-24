import langchain as lc
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel, Field, validator
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import openai
import pathlib
import os
import json
from pprint import pprint
import yaml

# Configure OpenAI API key
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("OPENAI_API_KEY")
openai.api_key = key

# Filepath Debug
mypath = os.path.abspath("")

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


def extract_relationships(data, set_prompt=None, verbose = False, model = None, verbatim=False, debug_path=None):
    """
    12/19/2023 (Function Last Updated)
    Data should be a python dictionary cleaned of all ground truth data. 
    Verbose triggers storage of information into debug files, this may break depending on where you run this script from as it depends on relative paths.
    Model specifies LLM to be used. (This file was only tested with OpenAI LLMs)
    Verbatim feeds the exact formatting of the dictionary found in the ground truth encoding into the prompt. (Minus the ground truth data)
    Verbatim will make it hard for the model to decide whether or not to include fields that were not in ground truth if you modify the SingleRelation class.
    debug_path, path to the file where verbose will dump debug information
    """
    # Add map reduce or some other type of summarization function here.
    """Possible to use the Kagi Summarizer, especially for long texts, limit is .3 dollars. https://kagi.com/summarizer/api.html"""
    processed_text = data["PaperContents"]
    if verbatim:
        relationships = {"Relations": data["Relations"]}
    else:
        relationships = extract_all_ordered_pairs(data)

    # Create Parser
    parser = PydanticOutputParser(pydantic_object=ListOfRelations) #Refers to a class called SingleRelation

    # Create the plain text prompt. Used some of langchain's functions to automatically create formated prompts. 
    prompt = PromptTemplate(
        template=set_prompt,
        input_variables=["text", "relationships"],
        partial_variables={"format_instructions":parser.get_format_instructions}
    )
    input_text = prompt.format_prompt(text=processed_text, relationships=relationships).to_string()
    if verbose:
        with open(debug_path / "MultiVariablePipelineInput.txt", "a") as f:
            f.write("="*70+f"\nPaper Analyzed: {data['PaperTitle']}"+"\nLLM Prompt:\n")
            f.write(input_text)
            f.write("\n\n\n")
    human_message_prompt = HumanMessagePromptTemplate(prompt=prompt)
    chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
    completion_prompt = chat_prompt.format_prompt(text=processed_text, relationships=relationships).to_messages()

    # Create LLM
    model = ChatOpenAI(temperature=.0, openai_api_key=key, model_name=model)

    # Obtain completion from LLM
    output = model(completion_prompt)
    if verbose:
        with open(debug_path / "MultiVariablePipelineOutput.txt", "a") as f:
            f.write("="*70+f"\nPaper Analyzed: {data['PaperTitle']}"+"\nLLM Pipeline Output:\n")
            f.write(str(output.content))
            f.write("\n")
    parsed_output = parser.parse(output.content) # Ensure content is in valid json format.
    if verbose:
        print(f"\n=========\nSuccessful pipeline completion for {data['PaperTitle'][:50]}, debug information and results saved at {debug_path}")
    return parsed_output.dict()  # Returns in dict format


def clean_data(data_path, verbose=False) -> dict:
    """Reads Json and removes list of user predictions"""
    with open(data_path, "r") as f:
        data = json.load(f)
    for relation in data['Relations']:
        relation["RelationshipClassification"] = ""
        relation["IsCausal"] = ""
        relation["SupportingText"] = ""
        relation["Attributes"] = ""
    if verbose:
        pprint(data)
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

def make_unique_names(relations):
    """Takes a list of relations, and combines var one and var two names into the field UniqueName"""
    for relationship in relations:
        relationship["UniqueName"] = make_unique_name(relationship)

def make_unique_name(relationship):
    variable_one = relationship.get("VariableOneName", "")
    variable_two = relationship.get("VariableTwoName", "")
    return variable_one + " -> " + variable_two

def captured_relations_pipeline(data_path, settings_path, debug_path: pathlib.Path):
    with open(settings_path, "r") as f:
        pipeline_settings = yaml.safe_load(f)
        verbose = pipeline_settings["verbose"]
        prompt = pipeline_settings["prompt"]
        model = pipeline_settings["model"]
    cleaned_data = clean_data(data_path, verbose=verbose)
    output = extract_relationships(cleaned_data, set_prompt=prompt, verbose=verbose, model=model, debug_path=debug_path)
    return output

if __name__ == "__main__":
    """This section configs the run's default debug settings for running the file without the evaluator"""
    captured_relations_pipeline(data_path="../evaluation_datasets/multi_relation_dataset/test_paper.json",
                                settings_path="../pipeline_settings.yaml",
                                debug_path=pathlib.Path("./debug_outputs"))
    pass
