# Repo copy of Henry_updated pipeline. Data stays in Henry_updated/data; paths
# below are relative, so switch the working directory there (see config.py).
import os as _os; from config import HENRY_ROOT as _HR; _os.chdir(_HR)

# This code 1. sets threshold for cos-sim for matches,
# 2. merges back article body to headlines
# 3. and translates the articles to chinese using gpt
# 4. cleans articles such that it does not include email addresses, authors or contact information


from datetime import timedelta

import pandas as pd

# merge back the articles of these matched headlines #################################################################################
# load matched dfs
df_cn_matched = pd.read_csv('data/pooled_cnen_news/matched_headline/cn_articles.csv.gz')
df_cn_traditional_matched= pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles.csv.gz')


df_cn_matched_part2 = pd.read_csv('data/pooled_cnen_news/matched_headline/cn_articles_part2.csv.gz')
df_cn_traditional_matched_part2= pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles_part2.csv.gz')



# Procedure for part 1 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
headline_cn_clean_again = pd.read_csv('data/pooled_cnen_news/matching_pool/cn_articles_part1.csv.gz')
headline_cn_traditional_clean_again = pd.read_csv('data/pooled_cnen_news/matching_pool/cn_traditional_articles_part1.csv.gz')
headline_en_clean_again = pd.read_csv('data/pooled_cnen_news/matching_pool/en_articles_part1.csv.gz')



df_cn_matched = df_cn_matched.merge(headline_cn_clean_again[['body']],left_index=True,right_index=True,how='left')
df_cn_matched = df_cn_matched.rename(columns = {'body':'cn_body'})
df_cn_traditional_matched = df_cn_traditional_matched.merge(headline_cn_traditional_clean_again[['body']],left_index=True,right_index=True,how='left')
df_cn_traditional_matched = df_cn_traditional_matched.rename(columns = {'body':'cn_body'})



headline_en_clean_again['matched_obs_id'] = headline_en_clean_again.index
df_cn_matched = df_cn_matched.merge(headline_en_clean_again[['matched_obs_id','body']],on=['matched_obs_id'],how='left')
df_cn_traditional_matched = df_cn_traditional_matched.merge(headline_en_clean_again[['matched_obs_id','body']],on=['matched_obs_id'],how='left')



# break off point for traditional is 0.67
# break off point for simple chinese is 0.65

def filter_matched(df,cutoff):
    df_filtered = df.copy()
    df_filtered = df_filtered[['timestamp_dt','headline','cleaned_headline_toembed','matched_cleaned_headline_toembed','matched_obs_id','matched_cos_sim','cn_body','body']]
    df_filtered = df_filtered[df_filtered['matched_cos_sim']>=cutoff]
    return df_filtered

df_cn_matched_filtered = filter_matched(df_cn_matched,cutoff=0.65)
df_cn_traditional_matched_filtered = filter_matched(df_cn_traditional_matched,cutoff=0.67)


df_cn_matched_filtered.to_csv('data/pooled_cnen_news/matched_headline/cn_articles_matched_filtered.csv.gz',index=False)
df_cn_traditional_matched_filtered.to_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles_matched_filtered.csv.gz',index=False)






# Procedure for part 2 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
headline_cn_clean_again_part2 = pd.read_csv('data/pooled_cnen_news/matching_pool/cn_articles_part2.csv.gz')
headline_cn_traditional_clean_again_part2 = pd.read_csv('data/pooled_cnen_news/matching_pool/cn_traditional_articles_part2.csv.gz')
headline_en_clean_again_part2 = pd.read_csv('data/pooled_cnen_news/matching_pool/en_articles_part2.csv.gz')




df_cn_matched_part2 = df_cn_matched_part2.merge(headline_cn_clean_again_part2[['body']],left_index=True,right_index=True,how='left')
df_cn_matched_part2 = df_cn_matched_part2.rename(columns = {'body':'cn_body'})
df_cn_traditional_matched_part2 = df_cn_traditional_matched_part2.merge(headline_cn_traditional_clean_again_part2[['body']],left_index=True,right_index=True,how='left')
df_cn_traditional_matched_part2 = df_cn_traditional_matched_part2.rename(columns = {'body':'cn_body'})



headline_en_clean_again_part2['matched_obs_id'] = headline_en_clean_again_part2.index
df_cn_matched_part2 = df_cn_matched_part2.merge(headline_en_clean_again_part2[['matched_obs_id','body']],on=['matched_obs_id'],how='left')
df_cn_traditional_matched_part2 = df_cn_traditional_matched_part2.merge(headline_en_clean_again_part2[['matched_obs_id','body']],on=['matched_obs_id'],how='left')



# break off point for traditional is 0.67
# break off point for simple chinese is 0.65

def filter_matched(df,cutoff):
    df_filtered = df.copy()
    df_filtered = df_filtered[['timestamp_dt','headline','cleaned_headline_toembed','matched_cleaned_headline_toembed','matched_obs_id','matched_cos_sim','cn_body','body']]
    df_filtered = df_filtered[df_filtered['matched_cos_sim']>=cutoff]
    return df_filtered

df_cn_matched_filtered_part2 = filter_matched(df_cn_matched_part2,cutoff=0.65)
df_cn_traditional_matched_filtered_part2 = filter_matched(df_cn_traditional_matched_part2,cutoff=0.67)


df_cn_matched_filtered_part2.to_csv('data/pooled_cnen_news/matched_headline/cn_articles_matched_filtered_part2.csv.gz',index=False)
df_cn_traditional_matched_filtered_part2.to_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles_matched_filtered_part2.csv.gz',index=False)




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# for matched results, translate the articles to english
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import os
from openai import OpenAI
import json
import time
from datetime import datetime
from datetime import timedelta
import glob
GET_LUCY_KEY = os.getenv("GPT_LUCY_KEY")

def write_command_for_gpt_translate(list_of_string, index_start,input_route = 'data/gpt_results/translation/input/consolidated_pooled_part_two/',
                                    file_name='gpt_cn_headline_translate', batch_count=1):
    file_name = file_name + f'_{batch_count}.jsonl'
    command_file_path = input_route + file_name
    # Open the file in write mode
    with open(command_file_path, 'w') as file:
        for i, string_to_translate in enumerate(list_of_string, start=index_start):
            # Create a dictionary for each record
            record = {
                "custom_id": f"request{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system",
                         "content": "I need you to translate the provided text from Chinese to English, you should only return the translated text:"},
                        {"role": "user",
                         "content": str(string_to_translate)}
                    ],
                    "max_tokens": 10000,
                }
            }
            # Write the JSON record to the file, followed by a newline character
            json.dump(record, file)
            file.write('\n')
    return command_file_path





def write_execute_translate_batch_commands(df_to_prompt,INSERT_API, batch_size=50,
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
    # to translate headlines replace with CN_headline
    list_of_headline = df_to_prompt['cn_body'].to_list()

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
        temp_command_file = write_command_for_gpt_translate(list_of_string=slice_of_headline,input_route=input_path, index_start=start_index,
                                                            file_name=file_base, batch_count=i)
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
                    print('current state for creating work is failed, retry after 5 minutes')
                    time.sleep(300)
            break

    # sleep for 10 minutes before checking status
    print('sleeping for 10 min before pulling batch status')
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

# run for part 1

list_for_work_id_cn_en,batch_result_id_cn_en =write_execute_translate_batch_commands(df_cn_matched_filtered,GET_LUCY_KEY,batch_size=1000,
                                                                                     file_base ='gpt_cn_translate_command',
                                                input_route = 'data/gpt_results/body_translate/input/part1/',
                                                output_route = 'data/gpt_results/body_translate/output/part1/',
                                                work_create_time_sleep=10)
list_for_work_id_cn_traditional_en,batch_result_id_cn_traditional_en = write_execute_translate_batch_commands(df_cn_traditional_matched_filtered,
                                                                                                              batch_size=1000,
                                                                                                              file_base='gpt_cn_traditional_translate_command',
                                                                                                              input_route='data/gpt_results/body_translate/input/part1/',
                                                                                                              output_route='data/gpt_results/body_translate/output/part1/',
                                                                                                              work_create_time_sleep=10)



# run for part 2


list_for_work_id_cn_en2,batch_result_id_cn_en2 =write_execute_translate_batch_commands(df_cn_matched_filtered_part2,GET_LUCY_KEY,batch_size=1000,
                                                                                     file_base ='gpt_cn_body_translate_part2',
                                                input_route = 'data/gpt_results/body_translate/input/part2/',
                                                output_route = 'data/gpt_results/body_translate/output/part2/',
                                                work_create_time_sleep=10)
list_for_work_id_cn_traditional_en2,batch_result_id_cn_traditional_en2 = write_execute_translate_batch_commands(df_cn_traditional_matched_filtered_part2,GET_LUCY_KEY,
                                                                                                              batch_size=1000,
                                                                                                              file_base='gpt_cn_traditional_body_translate_part2',
                                                                                                              input_route='data/gpt_results/body_translate/input/part2/',
                                                                                                              output_route='data/gpt_results/body_translate/output/part2/',
                                                                                                              work_create_time_sleep=600)




# consolidate gpt results back to original df
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






# merge back results to part 1
df_cn_matched_filtered=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_articles_matched_filtered.csv.gz')
df_cn_traditional_matched_filtered=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles_matched_filtered.csv.gz')



df_cn_matched_filtered_translated = consolidate_batch_results(df_to_merge_back=df_cn_matched_filtered,result_column_name='cn_body_translated',
                                                                     output_path='data/gpt_results/body_translate/output/part1/',
                                                                     batch_base_name='gpt_cn_translate_command_outputs*.jsonl')

df_cn_traditional_matched_filtered_translated = consolidate_batch_results(df_to_merge_back=df_cn_traditional_matched_filtered,result_column_name='cn_body_translated',
                                                                     output_path='data/gpt_results/body_translate/output/part1/',
                                                                     batch_base_name='gpt_cn_traditional_translate_command_outputs*.jsonl')


df_cn_matched_filtered_translated.to_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated.csv.gz',index=False)
df_cn_traditional_matched_filtered_translated.to_csv('data/pooled_cnen_news/matched_headline/cn_traditional_matched_filtered_translated.csv.gz',index=False)


# merge back results to part 2
df_cn_matched_filtered_part2=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_articles_matched_filtered_part2.csv.gz')
df_cn_traditional_matched_filtered_part2=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles_matched_filtered_part2.csv.gz')



df_cn_matched_filtered_part2_translated = consolidate_batch_results(df_to_merge_back=df_cn_matched_filtered_part2,result_column_name='cn_body_translated',
                                                                     output_path='data/gpt_results/body_translate/output/part2/',
                                                                     batch_base_name='gpt_cn_body_translate_part2_outputs*.jsonl')
df_cn_traditional_matched_filtered_part2_translated = consolidate_batch_results(df_to_merge_back=df_cn_traditional_matched_filtered_part2,result_column_name='cn_body_translated',
                                                                     output_path='data/gpt_results/body_translate/output/part2/',
                                                                     batch_base_name='gpt_cn_traditional_body_translate_part2_outputs*.jsonl')



df_cn_matched_filtered_part2_translated.to_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated_part2.csv.gz',index=False)
df_cn_traditional_matched_filtered_part2_translated.to_csv('data/pooled_cnen_news/matched_headline/cn_traditional_matched_filtered_translated_part2.csv.gz',index=False)












# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# read data and clean the articles so that it does not include any extra information indicative of source of lanaguage
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
df_cn_matched_filtered_translated=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated.csv.gz')
df_cn_traditional_matched_filtered_translated=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_matched_filtered_translated.csv.gz')

df_cn_matched_filtered_part2_translated=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated_part2.csv.gz')
df_cn_traditional_matched_filtered_part2_translated=pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_matched_filtered_translated_part2.csv.gz')

import re

def remove_trailing_bracket_groups(text):
    stack = []
    i = len(text) - 1
    end = i

    while i >= 0:
        char = text[i]
        if char in ')}]':
            stack.append(char)
        elif char in '({[':
            if stack and (
                (char == '(' and stack[-1] == ')') or
                (char == '[' and stack[-1] == ']') or
                (char == '{' and stack[-1] == '}')
            ):
                stack.pop()
                if not stack:
                    # Entire bracket group matched — update end pointer
                    end = i
            else:
                break
        elif not stack and not char.isspace():
            break
        i -= 1

    return text[:end].rstrip()

def remove_please_click_pattern(text):
    if not isinstance(text, str):
        return text
    return re.sub(r'please\s+click\s+\[[^\[\]]*\]', '', text, flags=re.IGNORECASE).strip()

def remove_click_pattern_and_trailing_bracket_groups(text):
    text = remove_trailing_bracket_groups(text)
    text = remove_please_click_pattern(text)
    return text



body_list = ['body','cn_body_translated']
for temp_column in body_list:
    df_cn_matched_filtered_translated[temp_column+'_cleaned'] = df_cn_matched_filtered_translated[temp_column].apply(lambda x: remove_click_pattern_and_trailing_bracket_groups(x))
    df_cn_traditional_matched_filtered_translated[temp_column+'_cleaned'] = df_cn_traditional_matched_filtered_translated[temp_column].apply(lambda x: remove_click_pattern_and_trailing_bracket_groups(x))
    df_cn_matched_filtered_translated[temp_column+'_cleaned'] = df_cn_matched_filtered_translated.apply(lambda row: row[temp_column] if str(row[temp_column+'_cleaned']).strip() == '' else row[temp_column+'_cleaned'],axis=1)
    df_cn_traditional_matched_filtered_translated[temp_column+'_cleaned'] = df_cn_traditional_matched_filtered_translated.apply(lambda row: row[temp_column] if str(row[temp_column+'_cleaned']).strip() == '' else row[temp_column+'_cleaned'],axis=1)

for temp_column in body_list:
    df_cn_matched_filtered_translated=df_cn_matched_filtered_translated.rename(columns={temp_column:temp_column+'_org'})
    df_cn_traditional_matched_filtered_translated=df_cn_traditional_matched_filtered_translated.rename(columns={temp_column:temp_column+'_org'})
    df_cn_matched_filtered_translated = df_cn_matched_filtered_translated.rename(columns={temp_column+'_cleaned':temp_column})
    df_cn_traditional_matched_filtered_translated = df_cn_traditional_matched_filtered_translated.rename(columns={temp_column+'_cleaned':temp_column})


# do it for part2
for temp_column in body_list:
    df_cn_matched_filtered_part2_translated[temp_column+'_cleaned'] = df_cn_matched_filtered_part2_translated[temp_column].apply(lambda x: remove_click_pattern_and_trailing_bracket_groups(x))
    df_cn_traditional_matched_filtered_part2_translated[temp_column+'_cleaned'] = df_cn_traditional_matched_filtered_part2_translated[temp_column].apply(lambda x: remove_click_pattern_and_trailing_bracket_groups(x))
    df_cn_matched_filtered_part2_translated[temp_column+'_cleaned'] = df_cn_matched_filtered_part2_translated.apply(lambda row: row[temp_column] if str(row[temp_column+'_cleaned']).strip() == '' else row[temp_column+'_cleaned'],axis=1)
    df_cn_traditional_matched_filtered_part2_translated[temp_column+'_cleaned'] = df_cn_traditional_matched_filtered_part2_translated.apply(lambda row: row[temp_column] if str(row[temp_column+'_cleaned']).strip() == '' else row[temp_column+'_cleaned'],axis=1)

for temp_column in body_list:
    df_cn_matched_filtered_part2_translated=df_cn_matched_filtered_part2_translated.rename(columns={temp_column:temp_column+'_org'})
    df_cn_traditional_matched_filtered_part2_translated=df_cn_traditional_matched_filtered_part2_translated.rename(columns={temp_column:temp_column+'_org'})
    df_cn_matched_filtered_part2_translated = df_cn_matched_filtered_part2_translated.rename(columns={temp_column+'_cleaned':temp_column})
    df_cn_traditional_matched_filtered_part2_translated = df_cn_traditional_matched_filtered_part2_translated.rename(columns={temp_column+'_cleaned':temp_column})




# Filter headline again
headline_filter_supplement_two = ["growth goal", 'bank adviser', 'world bank', 'u.s. bond', 'sovereign ratings',
                                  'soveriegn rating','global economic outlook', 'bbb+','a-', 'global growth forecast',
                                  'export orders', 'banker', 'jumps to', 'exports rise', 'exports fall', 'exports increase', 'exports decrease',
                                  'exports recover', 'export orders fall', 'investor morale', 'survey', 'central bank',
                                  'gdp', 'q1', 'q2', 'q3', 'q4',
                                  'fitch', 'fitch rates', 'fitch ratings', 'bullish', 'hawkish', 'manufacturing growth',
                                  'lipper', 'domestic stocks',
                                  'job growth', 'consumer confidence', 'growth outlook', 'consumer spending',
                                  'trade_surplus']

headline_pattern = '|'.join(headline_filter_supplement_two)



def filter_headline_again(df,headline_pattern=headline_pattern):
    df = df.dropna(subset=['matched_cleaned_headline_toembed'])
    df = df[~df['matched_cleaned_headline_toembed'].str.contains(headline_pattern, na=False, case=False)]
    return df


df_cn_matched_filtered_translated = filter_headline_again(df_cn_matched_filtered_translated)
df_cn_traditional_matched_filtered_translated = filter_headline_again(df_cn_traditional_matched_filtered_translated)
df_cn_matched_filtered_part2_translated = filter_headline_again(df_cn_matched_filtered_part2_translated)
df_cn_traditional_matched_filtered_part2_translated = filter_headline_again(df_cn_traditional_matched_filtered_part2_translated)






df_cn_matched_filtered_translated.to_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated_cleaned.csv.gz',index=False)
df_cn_traditional_matched_filtered_translated.to_csv('data/pooled_cnen_news/matched_headline/cn_traditional_matched_filtered_translated_cleaned.csv.gz',index=False)
df_cn_matched_filtered_part2_translated.to_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated_cleaned_part2.csv.gz',index=False)
df_cn_traditional_matched_filtered_part2_translated.to_csv('data/pooled_cnen_news/matched_headline/cn_traditional_matched_filtered_translated_cleaned_part2.csv.gz',index=False)
















