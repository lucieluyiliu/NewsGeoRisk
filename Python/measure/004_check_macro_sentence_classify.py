# Repo copy of Henry_updated pipeline. Data stays in Henry_updated/data; paths
# below are relative, so switch the working directory there (see config.py).
import os as _os; from config import HENRY_ROOT as _HR; _os.chdir(_HR)

# This code executes 2 prompts to GPT for the matched and cleaned dataframe
# 1. Whether or not GPT thinks the news a macro level news
# 2. Classify the sentences on judegemental language to Country A(East/West bloc) talks about Country B(East/West bloc) in a [tone] way


import pandas as pd
from openai import OpenAI
import time
from datetime import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import openai
import os
import textwrap
import json, re, pandas as pd

prompt_string_verify_macronews = ("""
I will provide you with a news article. Based on the article:


Task:
- Determine if the article is a "macro_level international news" article. Return True or False.
- Provide a short justification on how you made the decision that the article was a "macro_level international news" article, less than 100 words.

For determining if the article is a "macro_level international news article" output a JSON object with the following field:
1. "macro_level international news": True of False.
Return True if the article’s main focus is an international or cross-border issue involving multiple countries or international organizations (UN, NATO, IMF, etc.), such as:
diplomacy, sanctions, treaties, conflicts, global health, trade or energy policy with cross-border effects.

Return False if it mainly covers:
domestic economic indicators, routine market or corporate news (stocks, bonds, earnings, products), or purely national events without explicit international impact.

Borderline rule:
If domestic policy is covered, return True only when the article links it to foreign reactions or international consequences.

Heuristic cues:
Return True if at least two of these appear:
 -Mentions ≥2 countries or an international body.
 -Describes interstate action (e.g., sanctions, summit, treaty).
 -States cross-border effects or coordination.

2. "Justification": string
Provide a short justification on how you made the decision that the article was a "macro_level international news" article, less than 100 words.


        Output Format:  
        Return a JSON array with one object per article, structured as follows:

        [
          { 
            "macro_level international news" : "...",
            "Justification" : "..."
          }
        ]


        "Format the output as valid JSON with all keys and values enclosed in double-quotes, and ensure every string ends with a double-quote."
                         "Ensure there is a comma separating all the JSON key-value pairs."
                         "Ensure there is no line break after the last element of a JSON object."
                         "Ensure there is no line break or comma immediately before the closing curly brace of the JSON object."
                         "There should be no unescaped special characters at all, including newline characters, tabs, unicode characters, or any other control characters, within the JSON output."
                         "All values should be in double-quotes."

         "The article is as followed: "  """)


prompt_string = ("""
I will provide you with a news article. Based on the article:


Task:
- Extract all sentences that explicitly or implicitly convey an *attitude, stance, or tone* toward a country entity from the West or East bloc.
(An "Implicit tone" is when evaluative tone is conveyed through: choice of verbs/adjectives "blamed"/"hailed"/"accused"/"praised"; reported speech
with evaluative verbs “criticized,” “commended”; or Causal framing implying judgement "...leading to instability,"/"...helped stabilize the region",
An "Explicit tone" is when evaluative tone is straightforward)
- Do not paraphrase — always use the verbatim text from the article.


For each extracted sentence, output a JSON object with the following fields:
1. "sentence": the exact sentence text.  
2. "framer_country": the country making or implied to be making the judgment, claim, or stance.  If multiple countries are the framer_country return all of them.
3. "framer_bloc": East or West (based on provided definitions).  
4. "target_country": the country being described, judged, praised, criticized, defended, or affected.  If multiple countries are the target_country, return all of them.
5. "target_bloc": East or West.  
6. "tone": framer_country's tone* toward target_country  from the West or East bloc. Choose from one of the following categories:
   - "Positive" → praise, support, beneficial framing.  
   - "Negative" → criticism, blame, hostile framing.  
   - "Neutral" → factual mention with some stance but not clearly positive or negative.  
   - "Mixed" → both positive and negative aspects in the same sentence.  
   - "Objective" → plain reporting of an action or statement without evaluative tone.  
7. "explanation": a short reasoning why the sentence was classified this way.
8. "confidence": The model's internal certainty of its classfication of the tone, should be between 0 and 1.

Rules:
For choice of "sentence":
- If no tone is conveyed, ignore the sentence.  
For "framer_country", "target_country":
- If the framer_country is not explicitly mentioned but clearly implied through city/department or government officials(e.g. “Beijing said...”), infer the corresponding country name (→ “People’s Republic of China”)
- If the sentence is reported speech (“US officials said that China…”), treat the speaker as the framer (United States)
- If journalistic narration conveys tone without attribution (“The move was widely seen as aggressive”), treat the publisher’s bloc (e.g. Reuters = West or Xinhua News = East) as the framer_country/bloc
- If the **framer_country = target_country**, classify as self-framing. (Example: "China defended its trade policies and benefits" → framer=China, target=China, tone=Positive.
- If a sentence involves multiple framer_country and target_country, and the framer_country and target_country are not from the same bloc, return them as seperate records based on the bloc.
"framer_bloc", "target_bloc":
- Always use the provided West/East bloc definitions to identify bloc membership.  
- If a bloc country is mentioned without attitude/tone, ignore it.  
For "tone":
- If evaluative words exist, classify as "Positive", "Negative", or "Mixed".
- If sentence implies stance but avoids evaluation return "Neutral".
- If purely factual with no stance return "Objective".
- If uncertain, default to "Objective" rather than inferring tone. 

Special Rules:
To maintain consistency across linguistic domains, if the text seems to be translated or contains ambiguous expressions, infer tone based on the English semantics — do not speculate about the phrasing in its original language.


Definition of west bloc countries: [
"Australia", "Austria", "Belgium", "Bulgaria", "Canada", "Switzerland", "Cyprus",
"Czech Republic", "Germany", "Denmark", "Spain", "Estonia", "Finland", "France",
"United Kingdom", "Greece", "Croatia", "Hungary", "Ireland", "Italy", "Japan",
"Republic of Korea", "Lithuania", "Luxembourg", "Latvia", "Malta", "Netherlands",
"Norway", "Poland", "Portugal", "Romania", "Slovak Republic", "Slovenia", "Sweden",
"Türkiye", "Taiwan", "United States", "Colombia", "Paraguay", "Peru"]

Definition of east bloc countries: [
"Brazil", "People’s Republic of China", "Indonesia", "India", "Mexico", "Russia",
"Bangladesh", "Malaysia", "Philippines", "Thailand", "Viet Nam", "Kazakhstan",
"Mongolia", "Sri Lanka", "Pakistan", "Fiji", "Laos", "Brunei Darussalam", "Bhutan",
"Kyrgyz Republic", "Cambodia", "Maldives", "Nepal", "Singapore", "Hong Kong",
"Argentina", "Bolivia", "Chile", "Ecuador", "Uruguay", "Venezuela", "Rest of Latin America"]


        Output Format:  
        Return a JSON array with one object per article, structured as follows:

        [
          {
            "extracted_sentences": [
              {
                "sentence": "...",
                "framer_country": "...",
                "framer_bloc": "...",
                "target_country": "...",
                "target_bloc": "...",
                "tone": "...",
                "explanation": "...",
                "confidence": "..."
              }
            ]
          }
        ]


        "Format the output as valid JSON with all keys and values enclosed in double-quotes, and ensure every string ends with a double-quote."
                         "Ensure there is a comma separating all the JSON key-value pairs."
                         "Ensure there is no line break after the last element of a JSON object."
                         "Ensure there is no line break or comma immediately before the closing curly brace of the JSON object."
                         "There should be no unescaped special characters at all, including newline characters, tabs, unicode characters, or any other control characters, within the JSON output."
                         "All values should be in double-quotes."

         "The article is as followed: "  """)




GET_HENRY_KEY = os.getenv("GPT_HENRY_KEY")
client = OpenAI(api_key=GET_HENRY_KEY)


GET_LUCY_KEY = os.getenv("GPT_LUCY_KEY")
client = OpenAI(api_key=GET_LUCY_KEY)


def write_command_for_gpt(list_of_string, index_start,input_route = 'data/gpt_results/translation/input/consolidated_pooled_part_two/',
                                    file_name='gpt_cn_headline_translate', batch_count=1,prompt_string=prompt_string):
    file_name = file_name + f'_{batch_count}.jsonl'
    command_file_path = input_route + file_name
    # Open the file in write mode
    with open(command_file_path, 'w') as file:
        for i, (string1) in enumerate(list_of_string, start=index_start):
            # Create a dictionary for each record
            record = {
                "custom_id": f"request{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "user",
                         "content": prompt_string + string1
                         }
                    ],
                    "temperature": 0
                    # "max_tokens": 4096,
                    # "logprobs": True,
                    # "top_logprobs": 3
                }
            }
            # Write the JSON record to the file, followed by a newline character
            json.dump(record, file)
            file.write('\n')
    return command_file_path




def write_execute_batch_commands(df_to_prompt, INSERT_API, column_to_query, PROMPT_STARTER, batch_size=50,
                                 file_base='gpt_cn_headline_translate',
                                 input_route = 'data/gpt_results/translation/input/consolidated_pooled_part_two/',
                                 output_route='data/gpt_results/translation/output/consolidated_pooled_part_two/',
                                 work_create_time_sleep=5):
    # start executing commands
    client = OpenAI(api_key=INSERT_API)
    # file paths
    output_path = output_route
    input_path = input_route
    # unify and clean the df to translate
    df_to_prompt = df_to_prompt.reset_index(drop=True)
    # get list of content to query
    list_of_headline = df_to_prompt[column_to_query].to_list()

    # split the translation lists into batches
    number_batches = len(list_of_headline) // batch_size + 1

    list_for_batch_command_ids = []
    for i in range(1, number_batches + 1):
        # index base on batch number
        if i != number_batches:
            start_index = (i - 1) * batch_size
            end_index = i * batch_size

        if i == number_batches:
            start_index = (i - 1) * batch_size
            end_index = len(list_of_headline) + 1
        slice_of_headline = list_of_headline[start_index:end_index]

        if len(slice_of_headline) == 0:
            break

        # start writing commands for gpt ( can replace with other command functions)
        temp_command_file = write_command_for_gpt(list_of_string=slice_of_headline,input_route=input_path, index_start=start_index,
                                                            file_name=file_base, batch_count=i,prompt_string=PROMPT_STARTER)
        print(temp_command_file)


        # Uploading Your Batch Input File
        batch_input_file = client.files.create(
            file=open(temp_command_file, "rb"),
            purpose="batch"
        )

        # Get the updated Batch id and store in the list for further operations
        batch_input_file_id = batch_input_file.id
        list_for_batch_command_ids.append(batch_input_file_id)
    print(list_for_batch_command_ids)

    list_for_work_id = []
    # create batch works at 1 min interval for avoiding any rate limits, record work ids to list
    for k in range(0, len(list_for_batch_command_ids)):
        temp_batch_id = list_for_batch_command_ids[k]
        for try_create_work in range(0, 40):
            create_batch = client.batches.create(
                input_file_id=temp_batch_id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            time.sleep(10)
            work_id = create_batch.id
            temp_work_status = client.batches.retrieve(work_id).status
            for loop_controlling_validation in range(0, 100):
                temp_work_status = client.batches.retrieve(work_id).status
                if temp_work_status == 'validating':
                    time.sleep(10)
                if temp_work_status in (['in_progress', 'finalizing', 'completed']):
                    list_for_work_id.append(create_batch.id)
                    print(f'completed creation of the number {k + 1} batch work')
                    print(f'{(k + 1) / len(list_for_batch_command_ids)} progress')
                    print(f'Start pause for {work_create_time_sleep} seconds......')
                    time.sleep(work_create_time_sleep)
                    break
                if temp_work_status == 'failed':
                    print('current state for creating work is failed, retry after 3 minutes')
                    time.sleep(180)
            break

    # sleep for 10 minutes before checking status
    print('sleeping for 10s before pulling batch status')
    time.sleep(10)
    # Initial setup, check status of batch work, record filepath of results to download
    start_time = datetime.now()
    time_limit = timedelta(hours=6)
    batch_result_id = [None] * len(list_for_work_id)
    counter_for_completions = 0

    while counter_for_completions < len(list_for_work_id):
        for j in range(0, len(list_for_work_id)):
            # get status of batch record end results to a list
            retrive_batch_status = client.batches.retrieve(list_for_work_id[j])

            if retrive_batch_status.status == 'in_progress':
                print(f'batch {j} with batch id {list_for_work_id[j]} still in progress...')
            if retrive_batch_status.status != 'in_progress':
                if retrive_batch_status.status == "completed":
                    print(f'batch {j} with batch id {list_for_work_id[j]} completed...')
                    # append output file ids to a list
                    batch_result_id[j] = retrive_batch_status.output_file_id
                if retrive_batch_status.status != "completed":
                    print(
                        f'batch {j} with batch id {list_for_work_id[j]} has problems, current status is {retrive_batch_status.status}')
        # update status for total completions
        counter_for_completions = len([item for item in batch_result_id if item is not None])

        # Check time elapsed
        current_time = datetime.now()
        if current_time - start_time > time_limit:
            print(f"6 hours have passed, stopping the process...")
            break
        # print sleep time
        print('sleep for 30 seconds')
        time.sleep(30)

    # write outputs to local files
    for z in range(0, len(batch_result_id)):
        # get content of response
        temp_file_response = client.files.content(batch_result_id[z])
        # decode the content
        temp_file_response_string = temp_file_response.content.decode("utf-8")
        output_file_path = output_path + file_base + f'_outputs_{z + 1}.jsonl'

        # Open the file in write mode and write the decoded content
        with open(output_file_path, 'w') as file:
            file.write(temp_file_response_string)

        print(f"Data has been successfully saved to {output_file_path}.")
    return list_for_work_id, batch_result_id





# load data

df_cn_matched_filtered_translated=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated_cleaned.csv.gz')
df_cn_traditional_matched_filtered_translated=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_matched_filtered_translated_cleaned.csv.gz')
df_cn_matched_filtered_part2_translated=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated_cleaned_part2.csv.gz')
df_cn_traditional_matched_filtered_part2_translated=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_matched_filtered_translated_cleaned_part2.csv.gz')










# First run on simple chinese before expanding to traditional chinese+
# do for part 1 simple chinese
list_for_work_id_4o_en, batch_result_id_4o_en = write_execute_batch_commands(df_to_prompt=df_cn_matched_filtered_translated,
                                                                             INSERT_API=GET_LUCY_KEY,
                                                                             column_to_query='body',
                                                                             PROMPT_STARTER=prompt_string,
                                                                             batch_size=2000,
                                                                             file_base='gpt_en_sentence_verify',
                                                                             input_route = 'data/gpt_results/measure_query/input/part1/cn_simple/',
                                                                             output_route='data/gpt_results/measure_query/output/part1/cn_simple/',
                                                                             work_create_time_sleep=5)

list_for_work_id_4o_cn, batch_result_id_4o_cn = write_execute_batch_commands(df_to_prompt=df_cn_matched_filtered_translated,
                                                                             INSERT_API=GET_LUCY_KEY,
                                                                             column_to_query='cn_body_translated',
                                                                             PROMPT_STARTER=prompt_string,
                                                                             batch_size=2000,
                                                                             file_base='gpt_cn_sentence_verify',
                                                                             input_route='data/gpt_results/measure_query/input/part1/cn_simple/',
                                                                             output_route='data/gpt_results/measure_query/output/part1/cn_simple/',
                                                                             work_create_time_sleep=5)


list_for_work_id_4o_en_macro, batch_result_id_4o_en_macro = write_execute_batch_commands(df_to_prompt=df_cn_matched_filtered_translated,
                                                                                         INSERT_API=GET_LUCY_KEY,
                                                                                         column_to_query='body',
                                                                                         PROMPT_STARTER=prompt_string_verify_macronews,
                                                                                         batch_size=2000,
                                                                                         file_base='gpt_en_macro_verify',
                                                                                         input_route = 'data/gpt_results/measure_query/input/part1/cn_simple/',
                                                                                         output_route='data/gpt_results/measure_query/output/part1/cn_simple/',
                                                                                         work_create_time_sleep=5)

list_for_work_id_4o_cn_macro, batch_result_id_4o_cn_macro = write_execute_batch_commands(df_to_prompt=df_cn_matched_filtered_translated,
                                                                                         INSERT_API=GET_LUCY_KEY,
                                                                                         column_to_query='cn_body_translated',
                                                                                         PROMPT_STARTER=prompt_string_verify_macronews,
                                                                                         batch_size=2000,
                                                                                         file_base='gpt_cn_macro_verify',
                                                                                         input_route='data/gpt_results/measure_query/input/part1/cn_simple/',
                                                                                         output_route='data/gpt_results/measure_query/output/part1/cn_simple/',
                                                                                         work_create_time_sleep=5)





# do for part 2 simple chinese

list_for_work_id_4o_en, batch_result_id_4o_en = write_execute_batch_commands(df_to_prompt=df_cn_matched_filtered_part2_translated,
                                                                             INSERT_API=GET_HENRY_KEY,
                                                                             column_to_query='body',
                                                                             PROMPT_STARTER=prompt_string,
                                                                             batch_size=300,
                                                                             file_base='gpt_en_sentence_verify',
                                                                             input_route = 'data/gpt_results/measure_query/input/part2/cn_simple/',
                                                                             output_route='data/gpt_results/measure_query/output/part2/cn_simple/',
                                                                             work_create_time_sleep=5)

list_for_work_id_4o_cn, batch_result_id_4o_cn = write_execute_batch_commands(df_to_prompt=df_cn_matched_filtered_part2_translated,
                                                                             INSERT_API=GET_HENRY_KEY,
                                                                             column_to_query='cn_body_translated',
                                                                             PROMPT_STARTER=prompt_string,
                                                                             batch_size=300,
                                                                             file_base='gpt_cn_sentence_verify',
                                                                             input_route='data/gpt_results/measure_query/input/part2/cn_simple/',
                                                                             output_route='data/gpt_results/measure_query/output/part2/cn_simple/',
                                                                             work_create_time_sleep=5)


list_for_work_id_4o_en_macro, batch_result_id_4o_en_macro = write_execute_batch_commands(df_to_prompt=df_cn_matched_filtered_part2_translated,
                                                                                         INSERT_API=GET_HENRY_KEY,
                                                                                         column_to_query='body',
                                                                                         PROMPT_STARTER=prompt_string_verify_macronews,
                                                                                         batch_size=300,
                                                                                         file_base='gpt_en_macro_verify',
                                                                                         input_route = 'data/gpt_results/measure_query/input/part2/cn_simple/',
                                                                                         output_route='data/gpt_results/measure_query/output/part2/cn_simple/',
                                                                                         work_create_time_sleep=5)

list_for_work_id_4o_cn_macro, batch_result_id_4o_cn_macro = write_execute_batch_commands(df_to_prompt=df_cn_matched_filtered_part2_translated,
                                                                                         INSERT_API=GET_HENRY_KEY,
                                                                                         column_to_query='cn_body_translated',
                                                                                         PROMPT_STARTER=prompt_string_verify_macronews,
                                                                                         batch_size=300,
                                                                                         file_base='gpt_cn_macro_verify',
                                                                                         input_route='data/gpt_results/measure_query/input/part2/cn_simple/',
                                                                                         output_route='data/gpt_results/measure_query/output/part2/cn_simple/',
                                                                                         work_create_time_sleep=5)








import glob
def consolidate_batch_results(df_to_merge_back, result_column_name,output_path='data/gpt_results/translation/output/consolidated_pooled_part_two/',
                              batch_base_name='gpt_cn_headline_translate_outputs*.jsonl'):
    # Initialize result column if not already there
    if result_column_name not in df_to_merge_back.columns:
        df_to_merge_back[result_column_name] = None

    # Force to object dtype
    df_to_merge_back[result_column_name] = df_to_merge_back[result_column_name].astype("object")
    # record results from each line to df
    file_path_raw_outputs_pattern = output_path + batch_base_name
    file_path_raw_outputs = glob.glob(file_path_raw_outputs_pattern)

    # Temporary dictionary for batch updates
    update_dict = {}

    for file_path in file_path_raw_outputs:
        with open(file_path, 'r') as file:
            for line in file:
                data = json.loads(line)
                index_str = data['custom_id']
                index = pd.to_numeric(index_str.strip('request'), errors='coerce')
                content = data['response']['body']['choices'][0]['message']['content']
                update_dict[index] = content

    # Apply updates efficiently
    for index, content in update_dict.items():
        if index in df_to_merge_back.index:
            df_to_merge_back.at[index, result_column_name] = content

    return df_to_merge_back








df_cn_matched_filtered_part2_translated = consolidate_batch_results(df_cn_matched_filtered_part2_translated,'en_bloc_result',
                                                                    output_path='data/gpt_results/measure_query/output/part2/cn_simple/',
                              batch_base_name='gpt_en_sentence_verify*.jsonl')
df_cn_matched_filtered_part2_translated = consolidate_batch_results(df_cn_matched_filtered_part2_translated,'cn_bloc_result',
                                                                    output_path='data/gpt_results/measure_query/output/part2/cn_simple/',
                              batch_base_name='gpt_cn_sentence_verify*.jsonl')
df_cn_matched_filtered_part2_translated = consolidate_batch_results(df_cn_matched_filtered_part2_translated,'en_macro_verify',
                                                                    output_path='data/gpt_results/measure_query/output/part2/cn_simple/',
                              batch_base_name='gpt_en_macro_verify*.jsonl')
df_cn_matched_filtered_part2_translated = consolidate_batch_results(df_cn_matched_filtered_part2_translated,'cn_macro_verify',
                                                                    output_path='data/gpt_results/measure_query/output/part2/cn_simple/',
                              batch_base_name='gpt_cn_macro_verify*.jsonl')


# clean json columns

df_cn_matched_filtered_part2_translated.to_csv('data/sentence_classification/cn_matched_part2.csv',index=False)












#
#
#
# create_batch = client.batches.create(
#     input_file_id="file-HED8Ftrp98KnRr2pPQAF56",
#     endpoint="/v1/chat/completions",
#     completion_window="24h",
# )
#
# print(create_batch.id)
# print(create_batch.status)
#
#
#
# batches = client.batches.list(limit=20)
#
# for batch in batches.data:
#     print(batch.id, batch.status, batch.created_at)
#
#
#
#
# batch_id = "batch_6a291cd0a2a881909f760bc16da87645"
#
# batch = client.batches.retrieve(batch_id)
#
# print("batch_id:", batch.id)
# print("status:", batch.status)
# print("input_file_id:", batch.input_file_id)
# print("output_file_id:", batch.output_file_id)
# print("error_file_id:", batch.error_file_id)
# print("errors:", batch.errors)
# print("created_at:", batch.created_at)
# print("failed_at:", batch.failed_at)
# print("request_counts:", batch.request_counts)
#
#
#
# active_statuses = ["validating", "in_progress", "finalizing"]
#
# batches = client.batches.list(limit=100)
#
# for batch in batches.data:
#     if batch.status in active_statuses:
#         print("batch_id:", batch.id)
#         print("status:", batch.status)
#         print("input_file_id:", batch.input_file_id)
#         print("created_at:", batch.created_at)
#         print("-" * 60)
#
#
#
#
# active_statuses = ["validating", "in_progress", "finalizing"]
#
# batches = client.batches.list(limit=100)
#
# for batch in batches.data:
#     if batch.status in active_statuses:
#         print("batch_id:", batch.id)
#         print("status:", batch.status)
#         print("input_file_id:", batch.input_file_id)
#         print("created_at:", batch.created_at)
#         print("-" * 60)