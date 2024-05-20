import pandas as pd
from pathlib import Path
import json
import sys
from tqdm import tqdm
sys.path.append('./')
from lib.utils import read_jsonl

from PIL import Image


def remove_enum(image_name):  # e.g., musicsuggestions_1ajlvkm_5.jpg -> musicsuggestions_1ajlvkm.jpg
    parts = image_name.split('_')
    removed = '_'.join([parts[0], parts[1].split('.')[0]])
    ext = image_name.split('.')[-1]
    return f"{removed}.{ext}"
    

def save_combined_image(load_image_paths, save_dir, combined_name):
    valid_image_names = []  
    valid_images = []  
    
    for img_path in load_image_paths:
        try:
            with Image.open(img_path) as img:
                img.load()  
                image_name = Path(img_path).name
                img.save(save_dir / image_name)
                
                valid_image_names.append(image_name)  
                valid_images.append(Image.open(img_path))  
        except Exception as e:
            continue  
    
    if len(valid_images) == 0:
        return None
    
    total_width = sum(i.width for i in valid_images)
    max_height = max(i.height for i in valid_images)
    new_im = Image.new('RGB', (total_width, max_height))
    
    x_offset = 0
    for img in valid_images:
        new_im.paste(img, (x_offset, 0))
        x_offset += img.width
    
    combined_path = save_dir / combined_name
    new_im.save(combined_path)
    
    return valid_image_names


if __name__=="__main__":

    ROOT_DIR = 'data'

    if len(sys.argv) != 2:
        print("Pass domain name: books, music")
        sys.exit(1)  

    DOMAIN = sys.argv[1]
    print(f"Domain: {DOMAIN}")

    load_dir = Path(f'{ROOT_DIR}/metadata')

    submissions_dir = Path(f'{ROOT_DIR}/processed/{DOMAIN}')
    submissions_dir.mkdir(exist_ok=True, parents=True)

    comments_dir = submissions_dir / 'comments'
    comments_dir.mkdir(exist_ok=True, parents=True)

    image_dir = Path(f'{ROOT_DIR}/processed/_images/{DOMAIN}')
    image_dir.mkdir(exist_ok=True, parents=True)

    irrelevant_submission_ids = pd.read_csv('data/irrelevant_submissions.csv')['submission_id'].to_list()

    # 1. Combine subreddits into single domain (books, music)
    if DOMAIN == "books":
        subreddits = ['booksthatfeellikethis']
    if DOMAIN == "music":
        subreddits = ['ifyoulikeblank', 'musicsuggestions', 'picturethesound']

    valid_submission_ids = []
    for fname, out_dir in [('submissions.jsonl', submissions_dir), ('comments.jsonl', comments_dir)]:

        with open(out_dir / fname, 'w', encoding='utf-8') as outfile:
            for sub in subreddits:
                print(sub)
                for d in tqdm(read_jsonl(load_dir / sub / fname)):
                    
                    # 2. Filter irrelevant submissions
                    if d['submission_id'] in irrelevant_submission_ids:
                        continue
                    
                    # 3. Combine first four images and remove invalid ones
                    if fname == 'submissions.jsonl':
                        image_paths = []
                        for img_name in d['images']:
                            image_paths.append(f"data/images/{sub}/{img_name}")

                            if len(image_paths) == 4:  # up to first four
                                break
                        
                        combined_img_name = remove_enum(img_name)
                        valid_image_names = save_combined_image(image_paths, image_dir, combined_img_name)
                        if valid_image_names:
                            d['images'] = valid_image_names
                            d['combined_image'] = combined_img_name
                        else:
                            print("Corrupt image:", d['submission_id'])
                            continue
                    
                    json_line = json.dumps(d) + '\n'
                    outfile.write(json_line)

        
