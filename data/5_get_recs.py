import sys
sys.path.append('./')
import json
from tqdm import tqdm
import re
import pandas as pd
import csv
from lib.utils import read_jsonl
from collections import defaultdict


NULL_CASES = ["None", "None.", "- None", "", "none", "NONE"]


def del_itemize(text):
    pattern = r'^-\s'
    return re.sub(pattern, "", text)

def del_enumerate(text):
    pattern = r'^\d+[.)]\s*'
    return re.sub(pattern, "", text)


def del_trailing_none(text):
    if '- none' in text:
        text = text[:-len(' - none')]
    return text


def del_quotes(text):
    pattern = r'^"|"$'
    return re.sub(pattern, "", text)


def rec_str_to_list(rec_str):
    recs = []
    if rec_str in NULL_CASES:
        pass
    else:
        for r in rec_str.split('\n'):
            r = r.lower().strip()
            r = del_quotes(del_trailing_none(del_enumerate(del_itemize(r))))
            if r in NULL_CASES:
                continue
            if len(r) > 100: # too long; probably not an item
                continue
            if len(r) < 4: # too short; probably not an item
                continue
            recs.append(r)
    return recs

def defaultdict_to_dict(d):
    
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_dict(v) for k, v in d.items()}

    return d


if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print("Pass domain name: books, music")
        sys.exit(1)  

    DOMAIN = sys.argv[1]
    print(f"Domain: {DOMAIN}")

    input_path = f'data/processed/{DOMAIN}/comments/comments_processed.jsonl'
    recs_path = f'data/processed/{DOMAIN}/recs.json'
    items_path = f'data/processed/{DOMAIN}/items.csv'

    data = read_jsonl(input_path)

    sid2recs = defaultdict(lambda: defaultdict(int))
    all_recs = set()

    for d in tqdm(read_jsonl(input_path)):

        rec_str = d["processed"]
        recs = rec_str_to_list(rec_str)

        sid = d['submission_id']
        upvotes = d['upvotes']

        if upvotes < 0:  # downvote
            continue

        for r in recs:
            sid2recs[sid][r] += upvotes
            all_recs.add(r)

    sid2recs = defaultdict_to_dict(sid2recs)
    with open(recs_path, 'w') as f:
        json.dump(sid2recs, f, indent=4)

    df = pd.DataFrame(list(all_recs))
    df.to_csv(items_path, index=False, header=['title'])
    