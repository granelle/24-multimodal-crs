import sys
sys.path.append('./')
import praw
import pandas as pd
from pathlib import Path
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

if len(sys.argv) != 2:
    print("Pass subreddit name (lowercase)")
    sys.exit(1)  

SUBREDDIT = sys.argv[1]
print(f"Subreddit: {SUBREDDIT}")

QUERIES = []
for artname in ['image', 'picture', 'photo', 'drawing']:
    for verb in ['', 'sound like', 'fit', 'feel like',]:
         QUERIES.append(f'{verb} this {artname}')

save_dir = 'data/urls'  / Path(SUBREDDIT) 
save_dir.mkdir(exist_ok=True, parents=True)

subreddit = reddit.subreddit(SUBREDDIT)

urls = []

if SUBREDDIT in ['picturethesound', 'booksthatfeellikethis']:
    for submission in subreddit.new(limit=100000):
    
        urls.append({
            'title': submission.title,
            'url': f"https://www.reddit.com{submission.permalink}",
        })

    for submission in subreddit.top(limit=100000):
        
        urls.append({
            'title': submission.title,
            'url': f"https://www.reddit.com{submission.permalink}",
        })
    
    for submission in subreddit.hot(limit=100000):
        
        urls.append({
            'title': submission.title,
            'url': f"https://www.reddit.com{submission.permalink}",
        })

else:
    for query in QUERIES:
        for order in ['relevance', 'new']:
            print(query, order)
            for submission in subreddit.search(query, sort=order, limit=1000):

                title = submission.title

                if 'playlist' in title:
                    continue  # likely asking to expand their playlist

                if SUBREDDIT in ['ifyoulikeblank']:
                    if 'image' not in title and 'photo' not in title and 'picture' not in title and 'drawing' not in title:
                        continue  # stricter filtering needed for this sub

                urls.append({
                    'title': submission.title,
                    'url': f"https://www.reddit.com{submission.permalink}",
                })

df = pd.DataFrame(urls)

deduplicated_df = df.drop_duplicates(subset=['title', 'url'], keep='first') #.sort_values(by='title')

fname = f'{SUBREDDIT}_urls_raw.csv'

deduplicated_df.to_csv(save_dir / fname, index=False)
