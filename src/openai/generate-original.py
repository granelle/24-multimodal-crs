"""
To run ths code,
1. Install OpenAPI
    - pip install openapi
2. Setup environment variables
    - export OPENAI_API_KEY=
    - export OPENAI_ORG=
3. Run this script

References:
- https://platform.openai.com/docs/guides/text-generation/chat-completions-api
- https://platform.openai.com/docs/api-reference/chat
- https://platform.openai.com/docs/guides/vision
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
import json
import time
import argparse
from tqdm import tqdm
from lib.utils import read_jsonl, concatenate_image_descriptions, make_choices_str
from lib.file_io import IntermediateFileIO
from lib.instructions import select_instruction

import base64
import requests


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


def call_vision_api(prompt, image_paths, args):

    model_name = args.model_name  
    if model_name == 'gpt-4-vision-CoI':
        model_name = "gpt-4-vision-preview"

    content = []
    content.append({
        'type': 'text',
        'text': prompt
    })
    for img_path in image_paths:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{encode_image(img_path)}",
            },
        })

    messages = [{
        "role": "user",
        "content": content
        }
    ]

    request_timeout = 20
    for attempt in range(5):  # 5 attempts   
        try:
            response = client.chat.completions.create(
                    messages=messages,
                    model=model_name,
                    max_tokens=500,
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


def call_text_api(prompt, args):

    model_name = args.model_name    

    request_timeout = 20
    for attempt in range(5):  # 5 attempts   
        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }],
                model=model_name,
                max_tokens=500,
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

    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="gpt-4-vision-preview", choices=["gpt-3.5-turbo-0125", "gpt-4-0125-preview", "gpt-4-vision-preview", "gpt-4-vision-CoI"])  # gpt-4-vision-preview points to "1106"
    parser.add_argument("--task", type=str, default="description", choices=['description', 'rec_title', 'rec_choice'])   # TODO: maybe add descriptions task for gpt4v
    parser.add_argument("--domain", type=str, default="music", choices=['books', 'music'])
    parser.add_argument("--input_modality", type=str, default="image", choices=['image', 'OFA-huge', 'llava-v1.5-13b', 'gpt-4-vision-preview'])
    args = parser.parse_args()

    args.model_name = args.model_path

    # description task -> input modality should be image
    if 'description' in args.task:
        assert(args.input_modality == 'image')

    # input modality is image -> use vision model
    if args.input_modality == 'image':
        assert('vision' in args.model_name)

    file_io = IntermediateFileIO(args)

    instr = select_instruction(args)

    i = 0
    with open(file_io.output_fpath, 'w', encoding='utf-8') as outfile:
        
        for d in tqdm(read_jsonl(file_io.input_fpath)): 

            if args.input_modality == 'image':  
                if args.task == "description":

                    prompt = f"{instr}"
                    response = []
                    image_paths = [f"data/processed/_images/{args.domain}/{image}" for image in d['images']]

                    for image in image_paths[:4]:
                        response.append(call_vision_api(prompt, [image], args))
                
                else:  # rec
                    prompt = f"{instr}\nRequest:\n{d['title']}\n{d['selftext']}\n"
                    
                    if args.task == 'rec_choice':
                        prompt += f"Choices:\n{make_choices_str(d['choices'])}\n"

                    image_paths = [f"data/processed/_images/{args.domain}/{image}" for image in d['images']]
                    response = call_vision_api(prompt, image_paths, args)

            else:
                image_description = concatenate_image_descriptions(d['description'], max_num=4)
                prompt = f"{instr}\nRequest:\n{d['title']}\n{d['selftext']}\n\nImage descriptions:\n{image_description}\n"  
                
                if args.task == 'rec_choice':
                    prompt += f"Choices:\n{make_choices_str(d['choices'])}\n"
                    
                response = call_text_api(prompt, args)

            if not response:
                sys.exit(f"Exiting program due to no response.\nStopped at index: {i}")  

            # print(f"\n### Prompt ###\n{prompt}")
            # print(f"\n### Response ###\n{response}")

            d[args.task] = response
            json_line = json.dumps(d) + '\n'
            outfile.write(json_line)
            i += 1

    print("Done")