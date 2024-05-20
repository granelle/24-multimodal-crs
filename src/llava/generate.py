"""
To run this code,
1. Install LLaVA: https://github.com/haotian-liu/LLaVA
2. Modify llava/eval/run_llava/eval_model.py: print(output) -> return output
3. Activate conda environment: conda activate llava
4. Run this script

Note:
Seems to require ~53GB of GPU memory.
We use NVIDIA RTX A6000. Need to manually allocate 2 GPUs (export CUDA_VISIBLE_DEVICES).
"""
from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path
from llava.eval.run_llava import eval_model

import sys
sys.path.append('./')
from pathlib import Path
import json
import time
import argparse
from tqdm import tqdm
from lib.utils import read_jsonl, make_choices_str
from lib.file_io import IntermediateFileIO
from lib.instructions import select_instruction


if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default='llava-v1.5-13b', choices=['llava-v1.5-13b', 'llava-v1.5-CoI'])
    parser.add_argument("--task", type=str, default="rec_choice", choices=['description', 'rec_title', 'rec_choice'])
    parser.add_argument("--domain", type=str, default="music", choices=['books', 'music'])
    args = parser.parse_args()

    args.model_path = "liuhaotian/llava-v1.5-13b"
    args.input_modality = "image"

    file_io = IntermediateFileIO(args)

    instr = select_instruction(args)

    # LLaVA
    tokenizer, model, image_processor, context_len = load_pretrained_model(
        model_path=args.model_path,
        model_base=None,
        model_name=get_model_name_from_path(args.model_path)
    )

    def get_response(prompt, image_file):
        model_args = type('Args', (), {
                        "model_path": args.model_path,
                        "model_base": None,
                        "model_name": get_model_name_from_path(args.model_path),
                        "query": prompt,
                        "conv_mode": None,
                        "image_file": image_file,  # does not accept None
                        "sep": ",",
                        "temperature": 0,
                        "top_p": None,
                        "num_beams": 1,
                        "max_new_tokens": 512
                    })()
        return eval_model(model_args)

    with open(file_io.output_fpath, 'w', encoding='utf-8') as outfile:

        for d in tqdm(read_jsonl(file_io.input_fpath)):

            if args.task == "description":
                prompt = f"{instr}"
                response = []
                for image in d['images']:
                    response.append(get_response(prompt=prompt, image_file=f"data/processed/_images/{args.domain}/{image}"))
            
            elif "rec" in args.task:
                prompt = f"{instr}\nRequest:\n{d['title']}\n{d['selftext']}\n" 
                if args.task == "rec_choice":
                    prompt += f"Choices:\n{make_choices_str(d['choices'])}\n"
                
                response = get_response(prompt, image_file=f"data/processed/_images/{args.domain}/{d['combined_image']}")            
            
            else:
                raise NotImplementedError
            
            # print(f"\n### Prompt ###\n{prompt}")
            # print(f"\n### Response ###\n{response}")

            d[args.task] = response
            json_line = json.dumps(d) + '\n'
            outfile.write(json_line)

    print("Done")
