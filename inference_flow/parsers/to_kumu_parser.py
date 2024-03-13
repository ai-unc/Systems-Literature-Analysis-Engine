import json, sys

def compute_direction(verdicts, connection):
    types = {"direct":0, "inverse":0, "uncorrelated":0}
    verdicts_for_this_connection = verdicts[(connection[0], connection[1])]
    for verdict in verdicts_for_this_connection:
        verdict = verdict["relationType"]
        if verdict.lower().strip() == "not applicable":
            continue
        types[verdict.lower().strip()] += 1
    best = ""
    best_value = 0
    for type in types:
        if types[type] >= best_value:
            best = type
            best_value = types[type]
    #print(best, types)
    mapping = {"direct":"+", "inverse":"-", "uncorrelated":""}
    return mapping[best]


def create_description_text(connection, verdicts):
    description_bottom = ""
    for index, verdict in enumerate(verdicts[(connection[0], connection[1])]):
        description_bottom += f"Paper number {index}\n"
        description_bottom += "Opinion from: " + verdict["title"] + "\n"
        description_bottom += "Paper DOI <link>: " + verdict["doi"] + "\n"
        description_bottom += "Opinion extracted: " + verdict["relationType"] + "\n"
        description_bottom += "Original user opinion: " + verdict["UserPrediction"] + "\n"
        description_bottom += "Supporting text used in extraction: " + verdict["SupportingText"] + "\n"
        # description_bottom += "Reasoning used in extraction: " + verdict["Reasoning"] + "\n"
        description_bottom += "\n"

    description_top = f"Below are a summary of {len(verdicts[(connection[0], connection[1])])} \
relevant papers and what they implied about this relationship.\n\n"
    return description_top + description_bottom
    

def compute_single_correctness(UserPrediction, relationType):
    if relationType.lower().strip() == "not applicable":
        return 0.5
    return UserPrediction.lower().strip() == relationType.lower().strip()


def pipeline_to_kumu(dic, outputPath):

    vars = []
    connections = []
    elementList = []
    connectionList = []
    verdicts = {}
    # Process each JSON object in the list

    for paper in dic["Papers"]:
        title = paper['PaperTitle']
        doi = paper['PaperDOI']

        # Extract the variables and connections from each relation in the JSON object
        for relation in paper['Relations']:
            variable_one = relation['VariableOneName']
            variable_two = relation['VariableTwoName']
            relationType = relation['RelationshipClassification']
            SupportingText = relation['SupportingText']
            UserPrediction = relation['UserOriginalRelationshipClassification']

            # if relationType.lower().strip() == "not applicable":
            #     connections.append([variable_one, variable_two])
            #     continue

            correctness = compute_single_correctness(UserPrediction, relationType)
            if "isCausal" in relation:
                if relation['isCausal'] == "True":
                    isCausal = "causal"
                elif relation['isCausal'] == "False":
                    isCausal = "non-causal"
            else:
                isCausal = ""
            # Add the variables to the list if they are not already present
            if(variable_one not in vars):
                vars.append(variable_one)
            if(variable_two not in vars):
                vars.append(variable_two)
            
            if (variable_one, variable_two) not in verdicts:
                verdicts[(variable_one,variable_two)] = []
                verdicts[(variable_one,variable_two)].append( {"title": title, "doi": doi, "relationType": relationType, "UserPrediction": UserPrediction, "isCausal": isCausal, "SupportingText": SupportingText, "correctness": correctness})
            else:
                verdicts[(variable_one,variable_two)].append({"title": title, "doi": doi, "relationType": relationType, "UserPrediction": UserPrediction, "isCausal": isCausal, "SupportingText": SupportingText, "correctness": correctness})

            connections.append([variable_one, variable_two])

    #print(verdicts)
    # Create the element list for the output JSON
    for var in vars:
        entry = {
            "label": var,
            "type": "variable",
        }
        elementList.append(entry)
        
    # Create the connection list for the output JSON

    for connection in verdicts:
        # if connection[2] == "direct" or connection[2] == "Direct":
        #     connection[2] = "directed"
        # else:
        #     connection[2] = "mutual"
        print(connection)
        entry = {
            "from": connection[0],
            "to": connection[1],
            #"direction": connection[2],
            #"type": connection[4],
            "attributes":{
                "connection type": compute_direction(verdicts, connection),
                "description": create_description_text(connection, verdicts),
                "correctness": sum([i["correctness"] for i in verdicts[(connection[0], connection[1])]]) / len(verdicts[(connection[0], connection[1])]),
                "papers Examined": len(verdicts[(connection[0], connection[1])])
            }
            
        }
        connectionList.append(entry)

    # Write the output JSON to ParsedMultiVariablePipelineOutput.json file
    with open(outputPath, 'w') as g:
        output_dict = {"elements": elementList, "connections": connectionList}
        json_str = json.dumps(output_dict, indent=4)
        g.write(json_str)
    g.close()

# if __name__ == "__main__":
#     outputPath = sys.path[0][:-15] + "outputs\\"
#     f = open(outputPath + "MultiVariablePipelineOutput.txt")
#     pipeline_to_kumu(f, outputPath)
        