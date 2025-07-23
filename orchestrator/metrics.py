# orchestrator/metrics.py

import math
import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast
#from blanc import BlancHelp

# Load GPT-2 model + tokenizer once (for perplexity)
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()

# Compute Perplexity
def compute_perplexity(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
    input_ids = inputs.input_ids
    with torch.no_grad():
        outputs = model(input_ids, labels=input_ids)
        loss = outputs.loss
    return math.exp(loss.item())

# BLANC-help model
#blanc = BlancHelp("roberta-base", device="cuda" if torch.cuda.is_available() else "cpu")

# Compute BLANC-help score (document vs. generated summary)
#def compute_blanc_help(document, summary):
    #return blanc.score_from_pairs([document], [summary])["scores"][0]
