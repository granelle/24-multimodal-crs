"""
To run this code,
1. prepare OFA (example: OFA-huge)
- git clone --single-branch --branch feature/add_transformers https://github.com/OFA-Sys/OFA.git
- pip install OFA/transformers/
- git clone https://huggingface.co/OFA-Sys/OFA-huge
2. Set args.model_path (equivalent to ckpt_dir in the original reference code) as the directory of OFA-huge
3. Run! (Each instance takes 2-3 minutes)

References:
- https://github.com/OFA-Sys/OFA/tree/main
- https://github.com/OFA-Sys/OFA/blob/main/transformers.md
"""
from PIL import Image
import torch
from torchvision import transforms
from transformers import OFATokenizer, OFAModel
from transformers.models.ofa.generate import sequence_generator

import sys
sys.path.append('./')
from pathlib import Path
import json
import time
import argparse
from tqdm import tqdm
from lib.utils import read_jsonl, concatenate_image_descriptions
from lib.file_io import IntermediateFileIO
from lib.instructions import select_instruction

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_response(prompt, image_file):
    inputs = tokenizer([prompt], return_tensors="pt").input_ids.to(device)
    img = Image.open(image_file)
    patch_img = patch_resize_transform(img).unsqueeze(0).to(device)

    data = {}
    data["net_input"] = {"input_ids": inputs, 'patch_images': patch_img, 'patch_masks':torch.tensor([True])}

    gen_output = generator.generate([model], data)
    gen = [gen_output[i][0]["tokens"] for i in range(len(gen_output))]

    response = tokenizer.batch_decode(gen, skip_special_tokens=True)[0].strip()
    return response


if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="../OFA-huge", choices=["../OFA-huge"])
    parser.add_argument("--domain", type=str, default="books", choices=['books', 'music'])
    args = parser.parse_args()

    args.task = 'description'
    args.input_modality = 'image'
    args.model_name = args.model_path.split('/')[-1]

    file_io = IntermediateFileIO(args)

    # instr = select_instruction(args)

    # OFA-huggingface
    mean, std = [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]
    resolution = 256
    patch_resize_transform = transforms.Compose([
        lambda image: image.convert("RGB"),
        transforms.Resize((resolution, resolution), interpolation=Image.BICUBIC),
        transforms.ToTensor(), 
        transforms.Normalize(mean=mean, std=std)
    ])
    tokenizer = OFATokenizer.from_pretrained(args.model_path)
    model = OFAModel.from_pretrained(args.model_path, use_cache=True).to(device)
    generator = sequence_generator.SequenceGenerator(
        tokenizer=tokenizer,
        beam_size=5,
        max_len_b=16,
        min_len=0,
        no_repeat_ngram_size=3,
        )

    with open(file_io.output_fpath, 'w', encoding='utf-8') as outfile:
        
        for d in tqdm(read_jsonl(file_io.input_fpath)):

            # prompt = f"{instr}"
            prompt = " what does the image describe?"  # tried custom prompt, always returns "no" as answer
            response = []
            for image in d['images']:
                response.append(get_response(prompt=prompt, image_file=f"data/processed/_images/{args.domain}/{image}"))
            # print(response)

            d[args.task] = response
            json_line = json.dumps(d) + '\n'
            outfile.write(json_line)

    print("Done")