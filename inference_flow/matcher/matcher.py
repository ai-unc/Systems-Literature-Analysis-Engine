import os
import json
from pprint import pprint
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Initialize the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

def compute_similarity(embedding1, embedding2):
    # Cosine similarity
    return np.dot(embedding1, embedding2.T) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

def passage_rank(relation, papers, threshold=0.25):
    # Tokenize and encode the relation
    inputs = tokenizer(relation, return_tensors="pt", padding=True, truncation=True, max_length=512)
    relation_embedding = model(**inputs).last_hidden_state.mean(dim=1).detach().numpy()
    
    relevant_papers = []
    for paper in papers:
        # Tokenize and encode each paper
        paper_inputs = tokenizer(paper["PaperContents"], return_tensors="pt", padding=True, truncation=True, max_length=512)
        # paper inputs are a dictionary consisting of the embeddings, type, and attention mask.
        paper_embedding = model(**paper_inputs).last_hidden_state.mean(dim=1).detach().numpy()
        
        # Compute similarity
        similarity = compute_similarity(relation_embedding, paper_embedding)
        print(paper["PaperTitle"][:50], relation, similarity)
        if similarity > threshold:
            relevant_papers.append(paper)
    return relevant_papers


def match_relations_to_papers(papers_directory = "../evaluations/auto_generated_inputs", input_relations_directory = "../evaluations/test_inputs/test_input.json", debug = False):
    papers = []

    for file in os.listdir(papers_directory):
        input_path = os.path.join(papers_directory, file)
        with open(input_path, "r") as f:
            data = json.load(f)
            papers.append(data)
            # print(input_path)


    input_path = input_relations_directory
    with open(input_path, "r") as f:
        data = json.load(f)
    relationships = data["Relations"]

    variable_pairs = []
    # Iterate through each relationship and extract variables
    for relationship in relationships:
        variable_one = relationship.get("VariableOneName", "")
        variable_two = relationship.get("VariableTwoName", "")
        variable_pairs.append(variable_one + " -> " + variable_two)

    print(variable_pairs)

    relations_and_ranked_papers: dict = dict()
    for i in range(len(variable_pairs)):
        relation = variable_pairs[i]
        relevant_papers = passage_rank(relation, papers) # relevant papers is a list of relevant paper dictionaries with relevant metadata
        relations_and_ranked_papers[i] = {j["PaperDOI"] for j in relevant_papers}

    print(relations_and_ranked_papers)

    # Goal: something in the form of list of paper objects with relations
    for i in range(len(papers)):   
        papers[i]["Relations"] = []
        for key in relations_and_ranked_papers:
            value = relations_and_ranked_papers[key]
            if papers[i]["PaperDOI"] in value:
                # print(relationships[key])
                papers[i]["Relations"].append(relationships[key])

        print("Paper titled", papers[i]["PaperTitle"][:50], "Matched with", len(papers[i]["Relations"]), "relations.")


    if debug:
        with open("../evaluations/test_inputs/output.json", "w") as f:
            data_out = json.dumps({"papers":papers})
            f.write(data_out)
            pprint({"papers":papers})

    return papers