import sys
sys.path.append('./')
import praw
import requests
from pathlib import Path
import json
import pandas as pd

from private.reddit_auth import reddit 
"""
reddit = praw.Reddit(
    client_id="client_id",
    client_secret="client_secret",
    user_agent="user_agent",
    username="username",
    password="password",
)
""" 


def parse(post_url, image_save_dir):

    sub = reddit.submission(url=post_url)

    if not sub.author: # deleted author
        author_name = '[deleted]'
    else:
        author_name = sub.author.name

    submission_dict = {
        'submission_id': sub.id,
        'title': sub.title,
        'selftext': sub.selftext,
        'author': author_name,
        'created_utc': sub.created_utc,
        'over_18': sub.over_18,
        'permalink': sub.permalink,
        'subreddit': sub.subreddit.display_name,
        'comment_ids': [],
        'images': [],
        'image_urls': []
    }

    # Download image if it exists
    if hasattr(sub, 'is_gallery') and sub.is_gallery:

        # Iterate through the gallery items
        for i, item in enumerate(sub.gallery_data['items']):
            media_id = item['media_id']
            if media_id in sub.media_metadata:
                try:
                    image_url = sub.media_metadata[media_id]['s']['u'].replace('&amp;', '&')
                except:
                    print(sub.id)
                    print(sub.permalink)
                    print(sub.media_metadata[media_id])
                    return

                image_name = f'{sub.subreddit.display_name}_{sub.id}_{i+1}.{image_url.split("/")[-1].split("?")[0].split(".")[-1]}'
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(image_save_dir / image_name, "wb") as f:
                        f.write(response.content)
                        submission_dict['images'].append(image_name)
                        submission_dict['image_urls'].append(image_url)
    else:
        image_url = sub.url
        if image_url.endswith((".jpg", ".jpeg", ".png", ".webp")):
            image_name = f'{sub.subreddit.display_name}_{sub.id}.{image_url.split(".")[-1]}'
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(image_save_dir / image_name, "wb") as f:
                    f.write(response.content)
                    submission_dict['images'].append(image_name)
                    submission_dict['image_urls'].append(image_url)
    
    if not submission_dict['images']:
        return  # no image; skip

    # Process top-level comments
    comment_dicts = []
    for comment in sub.comments:
        if isinstance(comment, praw.models.MoreComments):
            continue

        comment_dicts.append({
            'comment_id': comment.id,
            'submission_id': sub.id,
            'subreddit': sub.subreddit.display_name,
            'raw': comment.body,
            'created_utc': comment.created_utc,
            'upvotes': comment.ups
        })

        submission_dict['comment_ids'].append(comment.id)

    if len(submission_dict['comment_ids']) == 0:
        return  # no comment; skip

    return submission_dict, comment_dicts


def to_jsonl(data, fpath):
    with open(fpath, 'w') as outfile:
        for entry in data:
            json.dump(entry, outfile)
            outfile.write('\n') 



if __name__=="__main__":

    ROOT_DIR = 'data'

    if len(sys.argv) != 2:
        print("Pass subreddit name (lowercase)")
        sys.exit(1)  

    SUBREDDIT = sys.argv[1]
    print(f"Subreddit: {SUBREDDIT}")

    urls = pd.read_csv(f'{ROOT_DIR}/urls/{SUBREDDIT}/{SUBREDDIT}_urls_raw.csv')['url'].to_list()

    img_save_dir = Path(f'{ROOT_DIR}/images') / SUBREDDIT
    data_save_dir = Path(f'{ROOT_DIR}/metadata') / SUBREDDIT

    img_save_dir.mkdir(exist_ok=True, parents=True)
    data_save_dir.mkdir(exist_ok=True, parents=True)

    submissions_data = []
    comments_data = []

    # Loop through urls
    for i, post_url in enumerate(urls):
        try:
            output = parse(post_url, img_save_dir)
        except:
            print("Error: ", i, post_url)
            continue
        
        if output:
            submission_dict, comment_dicts = output
            submissions_data.append(submission_dict)
            comments_data += comment_dicts

    to_jsonl(submissions_data, data_save_dir / 'submissions.jsonl')
    to_jsonl(comments_data, data_save_dir / 'comments.jsonl')

    print("Done!")


