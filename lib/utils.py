import json
import string


def read_jsonl(fpath):
    data = []
    with open(fpath, 'r') as file:
        for line in file:
            # Parse the JSON from each line and append to the list
            data.append(json.loads(line))
    return data


def yield_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            yield json.loads(line)


def concatenate_image_descriptions(descriptions, max_num=None):
    if max_num:
        descriptions = descriptions[:max_num]
    
    concatenated = '\n'.join([f"Image {i+1}: {desc}" for i, desc in enumerate(descriptions)])
    return concatenated


def remove_enum(image_name):  # e.g., musicsuggestions_1ajlvkm_5.jpg -> musicsuggestions_1ajlvkm.jpg
    parts = image_name.split('_')
    removed = '_'.join([parts[0], parts[1].split('.')[0]])
    ext = image_name.split('.')[-1]
    return f"{removed}.{ext}"


def make_choices_str(choices):
    enumerated_list = [f"{string.ascii_uppercase[i]}. {item}" for i, item in enumerate(choices)]
    # enumerated_list = [f"{i+1}. {item}" for i, item in enumerate(choices)]
    # enumerated_list = choices

    joined_string = '\n'.join(enumerated_list)
    
    return joined_string