import json
import ast

def kumu_to_pipeline(file):
    curFile = json.load(open("./evaluations/kumu_to_pipeline/inputs/" + file))
    output = {
        "Relations": []
    }
    
    for connection in curFile['connections']:
        consolidate = {
            "relationshipc": [],
            "IsCausal": [],
            "supportingtext": [],
        }
        attrs = connection["attributes"]['description'].split("\n=====\n")
        for attr in attrs:
            temp = ast.literal_eval(attr)
            consolidate['relationshipc'].append(temp['relationType'])
            consolidate['IsCausal'].append(temp['isCausal'])
            consolidate['supportingtext'].append(temp['SupportingText'])

        entry = {
            "VariableOneName": connection['from'],
            "VariableTwoName": connection['to'],
            "RelationshipClassification": consolidate['relationshipc'],
            "IsCausal" : consolidate['IsCausal'],
            "SupportingText": consolidate['supportingtext']
        }
        output['Relations'].append(entry)
    with open("./outputs/" + file[:-5] + "_output.json", "w") as f:
        f.write(json.dumps(output, indent=4))

def kumu_to_pipeline_no_io(dictionary):
    curFile = dictionary
    output = {
        "Relations": []
    }

    vars = {}
    
    for elm in curFile['elements']:
        vars[elm["_id"]] = elm['attributes']['label']

    for connection in curFile['connections']:
        relationship_status = ""
        if "connection type" in connection["attributes"]:
            relationship_status = connection["attributes"]["connection type"]

        if relationship_status.lower() == "opposite" or relationship_status.lower() == "o":
            relationship_status = "+"
        elif relationship_status.lower() == "direct" or relationship_status.lower() == "same":
            relationship_status = "+"

        entry = {
            "VariableOneName": vars[connection['from']],
            "VariableTwoName": vars[connection['to']],
            "RelationshipClassification": relationship_status,
        }
        output['Relations'].append(entry)
    
    return output


def user_input_to_list_of_relations(dictionary):
    curFile = dictionary
    output = {
        "Relations": []
    }

    vars = {}
    
    for elm in curFile['elements']:
        vars[elm["_id"]] = elm['attributes']['label']

    for connection in curFile['connections']:
        relationship_status = ""
        if "connection type" in connection["attributes"]:
            relationship_status = connection["attributes"]["connection type"]

        if relationship_status.lower() in ["opposite", "-", "o"]:
            relationship_status = "inverse"
        elif relationship_status.lower() in ["direct", "+", "same"]:
            relationship_status = "direct"
        else:
            relationship_status = "uncorrelated"
        print(relationship_status)
        entry = {
            "VariableOneName": vars[connection['from']],
            "VariableTwoName": vars[connection['to']],
            "RelationshipClassification": relationship_status,
        }
        output['Relations'].append(entry)
    
    return output



#DEBUG
# if __name__ == "__main__":
#     with open("./evaluations/inference_io/ideals/user_input_expected_form.json", "r") as g:
#         input = json.load(g)
#     with open('./evaluations/test_outputs/kumu_to_pipeline_text.json', 'w') as f:
#         f.write(str(kumu_to_pipeline_no_io(input)))