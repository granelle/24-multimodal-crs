import sys
sys.path.append('./')
import json
from tqdm import tqdm
import re
import pandas as pd
from pathlib import Path
from lib.utils import read_jsonl
from collections import defaultdict


def del_enumerate(text):
    pattern = r'^\d+[.)]\s*'
    return re.sub(pattern, "", text)


def del_quotes(text):
    pattern = r'"(.*?)"'
    return re.sub(pattern, r'\1', text)


def del_prefixes(text):
    text = text.replace("artist: ", "").replace("title: ", "")
    return text


def title_str_to_list(rec_str):
    recs = []
    for r in rec_str.split('\n'):
        r = r.lower().strip()
        r = del_prefixes(del_quotes(del_enumerate(r)))
        if len(r) > 100: # too long; probably not an item
            continue
        if len(r) < 4: # too short; probably not an item
            continue
        if ' - ' not in r:  # wrong format; probably not an item
            continue
        recs.append(r)
    return recs


def choice_str_to_index(rec_str):
    mapping = {
        'A': 0,
        'B': 1,
        'C': 2,
        'D': 3,
        'E': 4,
    }

    index = mapping.get(rec_str[0], None)

    if not index:
        for k, v in mapping.items():
            if k + '.' in rec_str:
                return v
        return rec_str
    return index



def extract_rec_title(io_paths):

    # Output files:
        # items.csv - all recs
        # rec.json - recs per submission 
        # rec_match.json - match results
    
    domain_to_all_recs = {
        'books': set(),
        'music': set()
    }
    
    for (in_path, out_dir) in io_paths:

        print(in_path)

        sid2titles = {}
        all_recs = set()

        for d in tqdm(read_jsonl(in_path)):

            rec_str = d["rec_title"]
            recs = title_str_to_list(rec_str)
            sid = d['submission_id']

            domain = 'books' if d["subreddit"] == "BooksThatFeelLikeThis" else 'music'

            sid2titles[sid] = recs
            all_recs.update(recs)
            domain_to_all_recs[domain].update(recs)

        with open(out_dir / 'subid_to_titles.json', 'w') as f:
            json.dump(sid2titles, f, indent=4)

        df = pd.DataFrame(list(all_recs))
        if not df.empty:
            df.to_csv(out_dir / f'titles.csv', index=False, header=['title'])
        else:
            print(f"No titles extracted from {in_path}")

    for domain in domain_to_all_recs:
        df = pd.DataFrame(list(domain_to_all_recs[domain]))
        df.to_csv(out_root / f'titles-{domain}.csv', index=False, header=['title'])


def extract_rec_choice(io_paths):

    for (in_path, out_dir) in io_paths:
        print(in_path)

        data = read_jsonl(in_path)

        sid2choice = {}

        for d in tqdm(read_jsonl(in_path)):

            rec_str = d["rec_choice"]
            choice_idx = choice_str_to_index(rec_str)
            sid = d['submission_id']

            domain = 'books' if d["subreddit"] == "BooksThatFeelLikeThis" else 'music'

            sid2choice[sid] = choice_idx

        with open(out_dir / 'subid_to_choice.json', 'w') as f:
            json.dump(sid2choice, f, indent=4)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("Pass task name: rec_title, rec_choice")
        sys.exit(1)  

    TASK = sys.argv[1]
    print(f"Task: {TASK}")

    in_root = Path(f'intermediate')
    out_root = Path(f'extracted')

    io_paths  = []
    for in_path in in_root.rglob(f'{TASK}.jsonl'):
        
        out_dir = out_root /  Path(*in_path.parts[1:-1])
        out_dir.mkdir(parents=True, exist_ok=True)
        io_paths.append((in_path, out_dir))

    
    if TASK == 'rec_title':
        extract_rec_title(io_paths)
    
    elif TASK == 'rec_choice':
        extract_rec_choice(io_paths)
    
    else:
        raise ValueError
