import sys
sys.path.append('./')
import json
from pathlib import Path
import editdistance
import numpy as np
from tqdm import tqdm


def nearest(item, candidates):

    candidates = list(set(candidates))
    dists = [editdistance.eval(item.lower(), i.lower()) for i in candidates]
    
    nearest_idx = np.argmin(dists)
    nearest_item = candidates[nearest_idx]
    
    return {
        'item': item,
        'nearest_item': nearest_item,
        'min_edit_distance': dists[nearest_idx],
    }


if __name__ == '__main__':

    # Ground truth recommendation
    domain_to_gt = {
        'books': json.load(open('data/processed/books/recs.json', 'r')),
        'music': json.load(open('data/processed/music/recs.json', 'r'))
    }

    # Generated titles
    io_paths  = []
    for in_path in Path(f'extracted').rglob('subid_to_titles.json'):
        out_path = in_path.parent / 'subid_to_titles_match.json'

        # if 'CoI' in str(in_path):  # TODO: temporary
        #     io_paths.append((in_path, out_path))

    for (in_path, out_path) in io_paths:
        print(in_path)

        domain = 'books' if '/books/' in in_path._str else 'music'

        with open(in_path, 'r') as file:
            subid_to_recs = json.load(file)

        recs_match = {k: [] for k in domain_to_gt[domain]}

        for subid in tqdm(recs_match):

            recs_pr = subid_to_recs[subid]
            recs_gt = domain_to_gt[domain][subid] 

            recs_gt = list(recs_gt.keys())  

            creators_gt = [r for r in recs_gt if ' - ' not in r]

            # note that if len(recs_pr) == 0, probably the model outputted gibberish 
            
            for r in recs_pr:

                m = None
                match_info = nearest(r, recs_gt)
                if match_info['min_edit_distance'] < 5:
                    m = match_info  # full match
                else:
                    for c in creators_gt:
                        if c in r.split('-')[0]:
                            m = {
                                'item': r,
                                'nearest_item': c
                            }  # creator match
                
                recs_match[subid].append(m)
                
            
        with open(out_path, 'w') as f:
            json.dump(recs_match, f, indent=4)
        