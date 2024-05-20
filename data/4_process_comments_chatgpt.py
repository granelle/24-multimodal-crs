"""
To run ths code,
1. Install OpenAPI
    - pip install openapi
2. Setup environment variables
    - export OPENAI_API_KEY=
    - export OPENAI_ORG=
3. Run this script
"""
import os
from openai import OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization=os.environ.get("OPENAI_ORG")
)

import sys
sys.path.append('./')
from pathlib import Path
from datetime import datetime
import json
import time
import argparse
from tqdm import tqdm
from lib.utils import read_jsonl

def call_text_api(prompt):

    request_timeout = 20
    for attempt in range(5):  # 5 attempts   
        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }],
                model="gpt-3.5-turbo-0125",
                max_tokens=200,
                temperature=0,
            ) 
            return response.choices[0].message.content

        except Exception as e:
            if attempt >= 4:  
                return None
            else:
                print(f"{str(e)}, retrying...")
                time.sleep(min(1 * 2**attempt, 60))  # exponential backoff with max delay of 60 seconds
                request_timeout = min(300, request_timeout * 2)  # increase timeout for next request


if __name__=="__main__":

    if len(sys.argv) != 2:
        print("Pass domain name: books, music")
        sys.exit(1)  

    DOMAIN = sys.argv[1]
    print(f"Domain: {DOMAIN}")

    

    now = datetime.now()
    formatted_now = now.strftime("%m%d_%H:%M:%S")

    input_path = f'data/processed/{DOMAIN}/comments/comments.jsonl'
    output_path = f'data/processed/{DOMAIN}/comments/comments_processed_{formatted_now}.jsonl'

    
    if DOMAIN == "music":
        instr = "In the following text, extract all music tracks.\
            \nEach track should be in the Artist - Title format and separated by a newline.\
            \nIf an artist is mentioned without the title, output the artist only.\
            \nIf there are no mentions, output None."
        
    if DOMAIN == "books":
        instr = "In the following text, extract all books.\
            \nEach book should be in the Author - Title format and separated by a newline.\
            \nIf an author is mentioned without the title, output the author only.\
            \nIf there are no mentions, output None."

    i = 0
    with open(output_path, 'w', encoding='utf-8') as outfile:
        
        for d in tqdm(read_jsonl(input_path)): 

            prompt = f"{instr}\n{d['raw']}"

            response = call_text_api(prompt)

            if not response:
                sys.exit(f"Exiting program due to no response.\nStopped at index: {i}")  

            # print(f"\n### Prompt ###\n{prompt}")
            # print(f"\n### Response ###\n{response}")

            d['processed'] = response
            json_line = json.dumps(d) + '\n'
            outfile.write(json_line)
            i += 1

    print("Done")