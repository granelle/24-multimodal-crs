# Codebase for Multimodal CRS

## Data 

Everything related to the data is stored in `data/`:
- `data/processed/` contains the ready-to-use datasets.
- You can scrpe and process the data yourself by using the python scripts from `{1-6}_*.py`.

### Ready-to-use datasets

- `data/processed/{books, music}`
    - `items.csv`: List of all the items recommended
    - `recs.json`: Submission IDs to recommended items, along with (net) upvote count per item.
    - `submissions_ns.jsonl`: Submissions information after negative sampling (for multiple-choice selection). Contains 
    - `submissions.jsonl`: Submissions information before negative sampling.
    - `comments/`
        - `comments_processed.jsonl`: Comments information after processing (item title extraction) with ChatGPT.
        - `comments.jsonl`: Comments information before processing.
- `data/metadata/{subreddit_name}`
    - `comments.jsonl`: Metadata of comments.
    - `submissions.jsonl`: Metadata of submissions.


### Scraping your own data

- You will need to install PRAW first. Check out the documentation (https://praw.readthedocs.io/en/stable/).

- Run `data/run.sh` to scrape the data and perform basic postprocessing. This runs the first three python scripts:
    - `1_get_urls.py` gets the urls to the submissions we are looking for (recommendation requests containing images). The urls will be stored in `data/urls/{subreddit_name}`.
    - `2_scrape_pages.py` scrapes the submission per url, and downloads all the relevant information, including images (`data/images`) and metadata (`data/metadata`).
    - `3_process.py` processes the submission:
        - Combine subreddits into single domain (books, music)
        - Filter irrelevant submissions (stored in `data/irrelevant_submissions.csv`, which is identified manually – however, we find that irrelevant submissions take a very small proportion of the entire data, so it could be okay not to consider it.)
        - Combine first four images and remove invalid ones
    - You will obtain `submissions.jsonl` and `comments.jsonl`.

- Next, run `4_process_comments_chatgpt.py` ChatGPT to extract items from comments. It will store the results to `data/processed/{DOMAIN}/comments/comments_processed_{current_time}.jsonl` real-time. It's designed to work this way because ChatGPT may stop running due to error like insufficient funds, and we want to save the intermediate results. If every data point is processed successfully , manually change the file name to `comments_processd.jonl`.

- ChatGPT responses (strings) need to be further processed (lists of items). `5_get_recs.py` does this by taking `comments_processed.jsonl` and generating `recs.json` and `items.csv`.

- Run `6_neg_sampling.py` to sample negative items for multiple-choice selection. It will use `submissions.jsonl` to produce `submissions_ns.jsonl`, which basically has additional fields.

## Getting model outputs

All the scripts needed in this step are stored in `src/`. 

### Running the models

The file names for getting their responses are `src/{model_type}/generated.py`. In the beginning of these files, there will be an explanation of how to prepare the environment for running the file (e.g., downloading the model). Here is the list of model types:
- `huggingface`: Models available through huggingface (LLaMA, Vicuna).
- `llava`: LLaVA.
- `ofa`: OFA.
- `openai`: OpenAI models.

Things to note:
- The options (model, dataset, task, etc.) can be set through argparse. For example, you can run 
    ```
    src/huggingface/generate.py --model_path meta-llama/Llama-2-13b-chat-hf --task rec_choice --domain music --input_modality gpt-4-vision-preview
    ```
    for running LLaMA for multiple-choice music selection, using GPT-4 descriptions.
- To run text-only models, you must first run the description generation tasks with either OFA, LLaVA, or GPT-4V.
- The responses will be stored real-time in `intermediate/` with the `_{current_time}.jsonl` suffix. Once you've got the results, manually remove the current time. (See the responses that are already stored.)

### Post-processing model responses

- `src/extract_recs.py` extracts items recommended by the models. It identifies all the `responses.jonl` file stored in `intermediate/` and stores the results in `extracted/`.
- `src/match_titles.py` uses the outputs of `extract_recs.py` to compare the extracted items with the ground-truth recommendations. Results are stored in `extracted/`.

## Evaluation

Use the notebook `evaluation.ipynb` to evaluate the models and and visualize the results. The results will be stored in `results/`.


## Appendix

`appendix.pdf` is the appendix of the main paper.