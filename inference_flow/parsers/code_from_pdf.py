import os
import re
import json
from PyPDF2 import PdfReader

def extract_sticky_notes(pdf_path):
    sticky_notes = []
    with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            if '/Annots' in page:
                annotations = page['/Annots']
                for annot in annotations:
                    annotation_object = annot.get_object()
                    if '/Contents' in annotation_object:
                        contents = annotation_object['/Contents']
                        variable_one_name = re.search(r'variable 1: (.+?)\n', contents, re.IGNORECASE)
                        variable_two_name = re.search(r'variable 2: (.+?)\n', contents, re.IGNORECASE)
                        relationship_classification = re.search(r'relationship: (.+?)(?:\n|$)', contents, re.IGNORECASE)
                        is_causal = re.search(r'is causal: (.+?)\n', contents, re.IGNORECASE)
                        attributes = re.search(r'attributes: (.+?)(?:\n|$)', contents, re.IGNORECASE)
                        supporting_text = re.search(r'text: (.+?)(?:\n|$)', contents, re.IGNORECASE)
                        sticky_notes.append({
                            'VariableOneName': variable_one_name.group(1) if variable_one_name else "",
                            'VariableTwoName': variable_two_name.group(1) if variable_two_name else "",
                            'RelationshipClassification': relationship_classification.group(1) if relationship_classification else "",
                            'IsCausal': is_causal.group(1) if is_causal else "",
                            'Attributes': attributes.group(1) if attributes else "",
                            'SupportingText': supporting_text,
                        })
    return sticky_notes


def extract_pdf_metadata(pdf_path):
   with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        metadata = pdf_reader.metadata
        page0 = pdf_reader.pages[0]
        text = page0.extract_text()
        doi_match = re.search(r'doi: (\S+)', text, re.IGNORECASE)
        if doi_match:
            doi = doi_match.group(1)
        else:
            print("DOI not found in the text.")
   return {
        'Title': metadata.title if metadata.title else '',
        'DOI': doi if doi else '',
    }


def extract_pdf_text(pdf_path):
    text_contents = []
    with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text_contents.append(page.extract_text())
    return text_contents

def sanitize_text(text):
    return text.replace("\n", "").replace("\r", "").replace("\t", "")
    #return re.sub("[^a-zA-Z0-9\n .,()\[\]{}]", "_", text)

def main(pdf_path):
    sticky_notes = extract_sticky_notes(pdf_path)
    text_contents = extract_pdf_text(pdf_path)
    metadata = extract_pdf_metadata(pdf_path)
    file_contents = "".join(text_contents)
    file_contents = sanitize_text(file_contents)
    input_data = {
        "PaperDOI": metadata['DOI'],
        "PaperTitle": metadata['Title'],
        "PaperContents": file_contents,
        "Relations": sticky_notes,
    }
    serialized_input_data = json.dumps(input_data, indent=4)
    metadata['Title'] = sanitize_text(metadata['Title'])
    file_name = f"{metadata['Title']}_{re.sub('[^a-zA-Z0-9]', '_', metadata['DOI'])}.json".replace(" ", "_")
    # try:
    #     with open(f"./evaluations/auto_generated_inputs/{file_name}", "w") as outfile:
    #         outfile.write(serialized_input_data)
    # except IOError:
    file_name = file_name[:50] + ".json"
    with open(f"./evaluations/auto_generated_inputs/{file_name}", "w") as outfile:
        outfile.write(serialized_input_data)


def parse_arguments(args):
    arg_dict = {}
    for arg in args[1:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            arg_dict[key] = value
    return arg_dict

if __name__ == "__main__":
    # # Parse command line arguments
    # arg_dict = parse_arguments(sys.argv)

    # # Check for required flags
    # if not all(flag in arg_dict for flag in ['-pdf']):
    #     print("Invalid or missing arguments")
    #     sys.exit("Usage: python pdf_script.py -pdf=PDF_PATH")

    # # Extract values from the dictionary
    # pdf_path = arg_dict['-pdf']
    

    # pdf_flag = sys.argv[1]
    # # Validate PDF flag
    # if not pdf_flag.startswith("-pdf=") or not pdf_flag.endswith('.pdf'):
    #     sys.exit("Invalid PDF flag")

    # # Extract PDF path
    # pdf_path = pdf_flag.split("=")[1]

    # # Perform main processing
    cwd = "./papers"
    for file in os.listdir(cwd):
        try:
            main(os.path.join(cwd, file))
        except:
            print("failed on", os.path.join(cwd, file))




