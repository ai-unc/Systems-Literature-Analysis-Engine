from transformers import pipeline
from huggingface_hub import login
from dotenv import load_dotenv
from transformers import Conversation
import torch
import os
import gc
import json
import sys
from transformers.utils import logging


load_dotenv()
huggingface_key = os.getenv("HF_TOKEN")
login(token=huggingface_key)
logging.set_verbosity_error()

# translation test
if False:
    translator = pipeline(task="translation", model="Helsinki-NLP/opus-mt-zh-en") # Helsinki-NLP/opus-mt-zh-en
    text_input = "沙是蜂，人是善。"
    text_translated = translator(text_input)
    print(text_translated)
    del translator
    gc.collect()

# summarizer
if False:
    summarizer = pipeline(task="summarization", model="google/long-t5-tglobal-base", torch_dtype=torch.bfloat16)
    with open("inference_flow/papers_for_inference/Brain_activation_patterns_in_major_depressive_diso.json") as f:
        text = json.loads(f.read())
        text = text["PaperContents"][1500:5000]
    print("original text", text)
    print(summarizer(text))

# Cosine similariy with sentence transformers
if True:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    sentences1 = ["Good milk is better than bad milk",
                  "Apples are orange",
                  "Sand is yellow"]
    sentences2 = ["Bad milk is better than good milk",
                  "Apples are Red",
                  "Yellow is sand"]
    embeddings1 = model.encode(sentences1)
    embeddings2 = model.encode(sentences2)
    from sentence_transformers import util
    cosine_scores = util.cos_sim(embeddings1, embeddings2)
    print(cosine_scores.diagonal())
# converation test
if False:
    pipe = pipeline("conversational", model="facebook/blenderbot-400M-distill")
    conversation = Conversation()
    while True:
        user_input = input("Next message, enter 'exit' to stop: ")
        if user_input == "exit":
            break
        else:
            conversation.add_message({"role": "user",
        "content": user_input
        })
            conversation = pipe(conversation)
            print(conversation)