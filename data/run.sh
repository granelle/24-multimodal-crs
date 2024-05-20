#!/bin/bash
# Entire pipeline for data collection

ROOT_DIR='data'

subreddits=('musicsuggestions' 'ifyoulikeblank' 'picturethesound' 'booksthatfeellikethis')

for sub in "${subreddits[@]}"; do
    python ${ROOT_DIR}/1_get_urls.py $sub
    python ${ROOT_DIR}/2_scrape_pages.py $sub
done

python ${ROOT_DIR}/3_process.py books
python ${ROOT_DIR}/3_process.py music
