"""
To run this code,
1. Make a Hugging Face account and request access to models 
    - https://huggingface.co/meta-llama
2. Log into your HF account
    - pip install transformers
    - huggingface-cli login
3. Run this script

References:
- https://huggingface.co/blog/llama2
"""
from transformers import AutoTokenizer
import transformers
import torch


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


if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="lmsys/vicuna-13b-v1.5", choices=["meta-llama/Llama-2-13b-chat-hf", "lmsys/vicuna-13b-v1.5"])
    parser.add_argument("--task", type=str, default="rec_title", choices=['rec_title', 'rec_choice'])
    parser.add_argument("--domain", type=str, default="books", choices=['books', 'music'])
    parser.add_argument("--input_modality", type=str, default="gpt-4-vision-preview", choices=['OFA-huge', 'llava-v1.5-13b', 'gpt-4-vision-preview'])
    args = parser.parse_args()

    args.model_name = args.model_path.split('/')[-1]

    file_io = IntermediateFileIO(args)

    instr = select_instruction(args)

    # Huggingface
    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    pipe = transformers.pipeline(
        "text-generation",
        model=args.model_path,
        torch_dtype=torch.float16,  # float32 will be slower
        device_map="auto" 
    )

    with open(file_io.output_fpath, 'w', encoding='utf-8') as outfile:
        
        for d in tqdm(read_jsonl(file_io.input_fpath)):

            image_description = concatenate_image_descriptions(d['description'], max_num=4)

            if args.task == 'rec_choice':
                prompt = f"[INST]{instr}\nRequest:\n{d['title']}\n{d['selftext']}\n\nImage descriptions:\n{image_description}\nChoices:\n{make_choices_str(d['choices'])}\n[\INST]\n"
            
            else:
                prompt = f"[INST]{instr}\nRequest:\n{d['title']}\n{d['selftext']}\n\nImage descriptions:\n{image_description}\n[\INST]"  
 
            # [INST] is redundant but helpful
            
            output = pipe(
                prompt, 
                do_sample=True,
                top_k=10,
                num_return_sequences=1,
                eos_token_id=tokenizer.eos_token_id,
                max_length=2048,
                return_full_text=False,  # prevent repeating the prompt
                truncation=True,
                temperature=0.001  # 0 is not allowed
            )
            response = output[0]['generated_text']

            # print(f"\n### Prompt ###\n{prompt}")
            print(f"\n### Response ###\n{response}")

            d[args.task] = response
            json_line = json.dumps(d) + '\n'
            outfile.write(json_line)

    print("Done")