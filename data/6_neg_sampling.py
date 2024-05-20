import sys
sys.path.append('./')
import json
from tqdm import tqdm
import re
import pandas as pd
import csv
from lib.utils import read_jsonl
from collections import defaultdict
import random

"""
Warning:
Initially when I ran the model, I did not set a random seed in this code (for negative sampling + shuffling).
Thus, running this code will result in a "different" file, and hence, different model input.
"""

N_NEG = 4

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print("Pass domain name: books, music")
        sys.exit(1)  

    DOMAIN = sys.argv[1]
    print(f"Domain: {DOMAIN}")
    
    submissions = read_jsonl(f'data/processed/{DOMAIN}/submissions.jsonl')
    recs = json.load(open(f'data/processed/{DOMAIN}/recs.json', 'r'))    
    all_items = set(pd.read_csv(f'data/processed/{DOMAIN}/items.csv')['title'].to_list())

    with open(f'data/processed/{DOMAIN}/submissions_ns.jsonl', 'w', encoding='utf-8') as outfile:
        for d in submissions:

            subid = d['submission_id'] 
            if subid not in recs:
                continue

            item2score = recs[subid]
            best_item = max(item2score, key=lambda k: item2score[k])

            candidates = all_items - item2score.keys()
            
            negs = random.sample(list(candidates), N_NEG)

            choices = [best_item] + negs
            random.shuffle(choices)

            true_index = choices.index(best_item)

            d['choices'] = choices
            d['true_index'] = true_index
        
            json_line = json.dumps(d) + '\n'
            outfile.write(json_line)