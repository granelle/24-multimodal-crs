import json
from pathlib import Path
from datetime import datetime


class IntermediateFileIO:
    def __init__(self, args):

        self.model_name = args.model_name
        self.domain = args.domain
        self.task = args.task
        self.input_modality = args.input_modality

        self.input_fpath = self._set_input_fpath()
        self.output_fpath = self._set_output_fpath()

        print(f"Load from: {self.input_fpath}\n")
        print(f"Save to: {self.output_fpath}\n")


    def _set_input_fpath(self):

        if self.task == "description":
            fpath = Path(f"data/processed/{self.domain}/submissions_ns.jsonl")
        
        elif 'rec_' in self.task:  
            
            if self.input_modality == "image":
                fpath = Path(f"data/processed/{self.domain}/submissions_ns.jsonl")
            else:
                fpath = Path(f"intermediate/{self.input_modality}/{self.domain}/image/description.jsonl")
        
        else: 
            raise ValueError(f"Unknown task: {self.task}")

        return fpath

    def _set_output_fpath(self):
        save_dir = Path(f"intermediate/{self.model_name}/{self.domain}/{self.input_modality}")
        save_dir.mkdir(exist_ok=True, parents=True)

        now = datetime.now()
        formatted_now = now.strftime("%m%d_%H:%M:%S")

        return save_dir / f"{self.task}_{formatted_now}.jsonl"
