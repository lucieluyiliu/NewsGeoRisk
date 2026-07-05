# Repo copy of Henry_updated pipeline. Data stays in Henry_updated/data; paths
# below are relative, so switch the working directory there (see config.py).
import os as _os; from config import HENRY_ROOT as _HR; _os.chdir(_HR)

# This piece of code cleans and embeds the headlines of news, in order to match CN-US articles using headlines embeddings and a 24 hour publication window
# Procedure: 1. further clean and filter the translated headliens (so that it does not include irrelavant news)
# 2. while cleaning, identify and split data into english and articles

# Further filter the translated headlines and data. identify traditional chinese articles split data to en cn 2 parts- - - - - - - - - - - - - - - - - - - - - - - - --  -
import pandas as pd
import opencc
import re


def detect_trad_cn_and_split_encn(df_headline_cn,df_consolidated,outcome_suffix='part2'):
    # collect chinese and english headlines
    headline_en = df_consolidated[~df_consolidated['language'].isin(['zh','ZH','cn','CN'])]
    headline_cn = df_headline_cn

    # Use openCC for traditional chinese identification instead of hanzidentifer (since later seems to be a bit inaccurate)
    def contains_traditional_chinese(text: str) -> bool:
        """
        Returns True if the given text contains at least one
        Traditional Chinese character.
        """
        # Create an OpenCC converter: 't2s' means Traditional to Simplified
        converter = opencc.OpenCC('t2s')
        # Convert the text from Traditional to Simplified
        converted_text = converter.convert(text)
        # If the result is different, at least one Traditional character was converted
        return (converted_text != text)


    # detect traditional chinese from body
    traditional_chinese = pd.DataFrame(headline_cn.apply(lambda row: contains_traditional_chinese(row['body']),axis=1))
    traditional_chinese = traditional_chinese.merge(headline_cn[['headline']], left_index=True, right_index=True, how='left')
    traditional_chinese = traditional_chinese.rename(columns={0: "traditional_flag_cc"})

    # merge back to original dataset
    headline_cn = headline_cn.merge(traditional_chinese[['traditional_flag_cc']],left_index=True,right_index=True,how='left')

    # clean dfs headline non null
    headline_cn = headline_cn[headline_cn['headline'].notnull()]
    headline_en = headline_en[headline_en['headline'].notnull()]

    # split traditional and simple chinese
    headline_cn_traditional = headline_cn[headline_cn['traditional_flag_cc'] == True]
    headline_cn = headline_cn[headline_cn['traditional_flag_cc'] == False]

    # sort values by timestamp
    def sort_df_by_timestamp(df):
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
        df['timestamp_yyyymm'] = df['timestamp_dt'].dt.strftime('%Y-%m')
        df = df.sort_values(by=['timestamp_dt'], ascending=True)
        return df

    headline_en = sort_df_by_timestamp(headline_en)
    headline_cn = sort_df_by_timestamp(headline_cn)
    headline_cn_traditional = sort_df_by_timestamp(headline_cn_traditional)

    # need to filter furthermore based on headline (remember to update headline filter parameters in master parameters)
    # clean based on supplement list of headlines
    headline_filter_supplement = ['SUBJECT CODE DIRECTORY', 'Asian News Highlights', 'PRESS DIGEST', '韩国数据',
                                  '韓國數據', '一周回顧', '一周回顾', '专题新闻快速浏览', '專題新聞快速瀏覽',
                                  '台湾数据', '台灣數據', '路透調查', '路透调查',
                                  'News Highlights', 'crude swaps and cash trades', 'Air Cargo', 'nan', '新聞摘要',
                                  '新闻摘要', 'CBOT', '恆生指數',
                                  '報摘', '报摘', '香港股市', '報紙新聞摘要', '亞洲股市', 'A股', '新股',
                                  '重要新聞快速瀏覽', '经济指标', '政经日程', '股价', '一览表', '油市',
                                  '中国股市', '全球主要央行动态', '日本数据', '股價表現表', '經濟事件', '主要央行動態',
                                  '一周经济焦点', '加拿大股市', '中国数据',
                                  '外幣期貨', '東京股市', '東南亞股市', '歐洲美元', '紐約美元', '商品貿易數據', '金盤',
                                  '收盤', '開盤', '早盤', '晚盤', 'B股', '重要行事曆',
                                  '海關統計', '東京美元', '盤初', '尾盤', '中國金屬', '匯率預測', '上海國債',
                                  '重要行曆', '黃金焦點', '道瓊工業指數', '金屬期市', '上市報價一覽', 'Nasdaq指數',
                                  '金融市場假期代碼一覽', '滬綜指', '台灣股市', '债市', '汇市', '匯市']

    headline_pattern = '|'.join(headline_filter_supplement)

    def clean_filtered_again(df_clean_again):
        df_clean_again = df_clean_again[
            ~df_clean_again['headline'].str.contains(headline_pattern, na=False, case=False)]
        return df_clean_again

    headline_en_clean_again = clean_filtered_again(headline_en).reset_index(drop=True)
    headline_cn_clean_again = clean_filtered_again(headline_cn).reset_index(drop=True)
    headline_cn_traditional_clean_again = clean_filtered_again(headline_cn_traditional).reset_index(drop=True)

    # sometimes the same headline still appears after only obtaining latest take of an article grouped by altid
    # clean by grouping by headline and only keeping the record with highest takesequence
    headline_en_clean_again = headline_en_clean_again.loc[
        headline_en_clean_again.groupby('headline')['takeSequence'].idxmax()].reset_index(drop=True)
    headline_cn_clean_again = headline_cn_clean_again.loc[
        headline_cn_clean_again.groupby('headline')['takeSequence'].idxmax()].reset_index(drop=True)
    headline_cn_traditional_clean_again = headline_cn_traditional_clean_again.loc[
        headline_cn_traditional_clean_again.groupby('headline')['takeSequence'].idxmax()].reset_index(drop=True)
    headline_en_clean_again = headline_en_clean_again.sort_values(by=['timestamp_dt'], ascending=True).reset_index(
        drop=True)
    headline_cn_clean_again = headline_cn_clean_again.sort_values(by=['timestamp_dt'], ascending=True).reset_index(
        drop=True)
    headline_cn_traditional_clean_again = headline_cn_traditional_clean_again.sort_values(by=['timestamp_dt'],ascending=True).reset_index(
        drop=True)

    # Clean headlines before embedding - - - - - -  - - - - - -  - - - - - -  - - - - - -  - - - - - -  - - - - - -  - - - - - -  - - - - - -  - - - - - -
    def clean_text_match_part(text):
        # Regex to remove bylines: looks for patterns with names followed by a location and date
        text = re.sub(r'\bBy\s[\w\s,]+(?:and\s[\w\s]+)?\s+[A-Z]{2,}\,\s\w+\s\d{1,2}\b', '', text)

        # Remove parenthetical and bracketed information
        text = re.sub(r'\(.*?\)|\[\[.*?\]\]', '', text)

        # Remove email addresses, URLs, and other non-relevant metadata
        text = re.sub(r'\S*@\S*\s?', '', text)
        text = re.sub(r'http\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'www.\S+', '', text)  # URLs without http
        text = re.sub(r'@\S+', '', text)  # Twitter handles
        text = re.sub(r'\d{3} \d{3} \d{4}', '', text)  # US phone numbers

        patterns = [
            r'Reporting by [^\;]+',  # Removes "Reporting by" followed by any characters not including a semicolon
            r'Editing by [^\;]+',  # Removes "Editing by" followed by any characters not including a semicolon
            r'[\w\.]+@[\w\.]+\.[\w\.]+',  # Removes email addresses
            r'Reuters Messaging:.*',  # Removes any text following "Reuters Messaging:"
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text)

        return text

    headline_en_clean_again['cleaned_headline_toembed'] = headline_en_clean_again['headline'].apply(
        lambda x: (clean_text_match_part(str(x))).lower())
    headline_cn_clean_again['cleaned_headline_toembed'] = headline_cn_clean_again['cn_headline_translated'].apply(
        lambda x: (clean_text_match_part(str(x))).lower())
    headline_cn_traditional_clean_again['cleaned_headline_toembed'] = headline_cn_traditional_clean_again[
        'cn_headline_translated'].apply(lambda x: (clean_text_match_part(str(x))).lower())

    # save cleaned headlines
    headline_en_clean_again.to_csv(f'data/pooled_cnen_news/matching_pool/en_articles_{outcome_suffix}.csv.gz', index=False)
    headline_cn_traditional_clean_again.to_csv(f'data/pooled_cnen_news/matching_pool/cn_traditional_articles_{outcome_suffix}.csv.gz',index=False)
    headline_cn_clean_again.to_csv(f'data/pooled_cnen_news/matching_pool/cn_articles_{outcome_suffix}.csv.gz', index=False)



# read dataframes and run
df_consolidated_part1 = pd.read_csv('data/pooled_cnen_news/consolidated_pooled_dfs_part1.csv.gz')
df_headline_cn_part1 = pd.read_csv('data/pooled_cnen_news/consolidated_pooled_headline_translated_part1.csv.gz')
detect_trad_cn_and_split_encn(df_headline_cn_part1, df_consolidated_part1,'part1')



# read dataframes and run
df_consolidated_part2 = pd.read_csv('data/pooled_cnen_news/consolidated_pooled_dfs_part2.csv.gz')
df_headline_cn_part2 = pd.read_csv('data/pooled_cnen_news/consolidated_pooled_headline_translated_part2.csv.gz')
detect_trad_cn_and_split_encn(df_headline_cn_part2, df_consolidated_part2,'part2')




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Start process for text embedding and match/save results
import numpy as np
from openai import OpenAI
import json
from datetime import datetime
from datetime import timedelta
import time
import os
import glob

GET_LUCY_KEY = os.getenv("GPT_LUCY_KEY")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def write_embedding_command_for_gpt(list_to_embed,start_index,
                          file_path = 'data/gpt_results/headline_embedding/input/'   ,
                          file_name='headline_en_clean_again_headline', batch_count=1):
    file_name = file_name + f'_{batch_count}.jsonl'
    command_file_path = file_path + file_name
    # Open the file in write mode
    with open(command_file_path, 'w') as file:
        for i in range(0,len(list_to_embed)):
            # Create a dictionary for each record
            record = {
                "custom_id": f"request{i+start_index}",
                "method": "POST",
                "url": "/v1/embeddings",
                "body": {
                    "input":list_to_embed[i],
                    "model": "text-embedding-3-small",
                    "encoding_format": "float",
                }
            }
            # Write the JSON record to the file, followed by a newline character
            json.dump(record, file)
            file.write('\n')
    return command_file_path


def write_execute_embed_batch_commands(df_to_prompt, chosen_column_to_embed, batch_size=100000,
                                       file_input_path = 'data/gpt_results/headline_embedding/input/',
                                       file_output_path = 'data/gpt_results/headline_embedding/output/',
                                       file_base='headline_en_clean_again_headline',
                                       work_create_time_sleep=60, INSERT_KEY=GET_LUCY_KEY):
    # unify and clean the df to translate
    df_to_prompt = df_to_prompt.reset_index(drop=True)
    list_to_embed = df_to_prompt[chosen_column_to_embed].to_list()

    # split the translation lists into batches
    number_batches = len(list_to_embed) // batch_size + 1

    list_for_batch_command_ids = []
    for i in range(1, number_batches + 1):
        # index base on batch number
        if i != number_batches:
            start_index = (i - 1) * batch_size
            end_index = i * batch_size

        if i == number_batches:
            start_index = (i - 1) * batch_size
            end_index = len(list_to_embed) + 1

        slice_body_en = list_to_embed[start_index:end_index]
        if len(slice_body_en) == 0:
            break

        # start writing commands for gpt ( can replace with other command functions)
        temp_command_file = write_embedding_command_for_gpt(slice_body_en, start_index,file_input_path,file_name=file_base, batch_count=i)
        print(temp_command_file)
        # start executing commands
        client = OpenAI(api_key=INSERT_KEY)
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
                endpoint="/v1/embeddings",
                completion_window="24h",
            )
            time.sleep(60)
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
                    time.sleep(5)
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
        output_file_path = file_output_path + file_base + f'_outputs_{z + 1}.jsonl'

        # Open the file in write mode and write the decoded content
        with open(output_file_path, 'w') as file:
            file.write(temp_file_response_string)

        print(f"Data has been successfully saved to {output_file_path}.")
    return list_for_work_id, batch_result_id






GET_LUCY_KEY = os.getenv("GPT_LUCY_KEY")
# run for part 1 - - - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -
# read dfs
headline_en_clean_again=pd.read_csv('data/pooled_cnen_news/matching_pool/en_articles_part1.csv.gz')
headline_cn_traditional_clean_again=pd.read_csv(
    'data/pooled_cnen_news/matching_pool/cn_traditional_articles_part1.csv.gz')
headline_cn_clean_again=pd.read_csv('data/pooled_cnen_news/matching_pool/cn_articles_part1.csv.gz')
headline_en_clean_again_headline = headline_en_clean_again[['timestamp_dt','cleaned_headline_toembed']]
headline_cn_clean_again_headline = headline_cn_clean_again[['timestamp_dt','headline','cleaned_headline_toembed']]
headline_cn_traditional_clean_again_headline = headline_cn_traditional_clean_again[['timestamp_dt','headline','cleaned_headline_toembed']]

list_for_work_id, batch_result_id = write_execute_embed_batch_commands(headline_en_clean_again_headline, 'cleaned_headline_toembed', batch_size=10000,
                                                                       file_input_path = 'data/gpt_results/headline_embedding/input/part1/',
                                                                       file_output_path = 'data/gpt_results/headline_embedding/output/part1/',
                                                                       file_base='headline_en_clean_again_headline',
                                                                       work_create_time_sleep=60, INSERT_KEY=GET_LUCY_KEY)
list_for_work_id2, batch_result_id2 = write_execute_embed_batch_commands(headline_cn_clean_again_headline, 'cleaned_headline_toembed', batch_size=10000,
                                                                         file_input_path = 'data/gpt_results/headline_embedding/input/part1/',
                                                                         file_output_path = 'data/gpt_results/headline_embedding/output/part1/',
                                                                         file_base='headline_cn_clean_again_headline',
                                                                         work_create_time_sleep=60, INSERT_KEY=GET_LUCY_KEY)
list_for_work_id3, batch_result_id3 = write_execute_embed_batch_commands(headline_cn_traditional_clean_again_headline, 'cleaned_headline_toembed', batch_size=10000,
                                                                         file_input_path = 'data/gpt_results/headline_embedding/input/part1/',
                                                                         file_output_path = 'data/gpt_results/headline_embedding/output/part1/',
                                                                         file_base='headline_cn_traditional_clean_again_headline',
                                                                         work_create_time_sleep=60, INSERT_KEY=GET_LUCY_KEY)

# run for part2 - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -
# read dfs
headline_en_clean_again_part2=pd.read_csv('data/pooled_cnen_news/matching_pool/en_articles_part2.csv.gz')
headline_cn_traditional_clean_again_part2=pd.read_csv('data/pooled_cnen_news/matching_pool/cn_traditional_articles_part2.csv.gz')
headline_cn_clean_again_part2=pd.read_csv('data/pooled_cnen_news/matching_pool/cn_articles_part2.csv.gz')
# collect columns
headline_en_clean_again_headline_part2 = headline_en_clean_again_part2[['timestamp_dt','cleaned_headline_toembed']]
headline_cn_clean_again_headline_part2 = headline_cn_clean_again_part2[['timestamp_dt','headline','cleaned_headline_toembed']]
headline_cn_traditional_clean_again_headline_part2 = headline_cn_traditional_clean_again_part2[['timestamp_dt','headline','cleaned_headline_toembed']]

list_for_work_id, batch_result_id = write_execute_embed_batch_commands(headline_en_clean_again_headline_part2, 'cleaned_headline_toembed', batch_size=10000,
                                                                       file_input_path = 'data/gpt_results/headline_embedding/input/part2/',
                                                                       file_output_path = 'data/gpt_results/headline_embedding/output/part2/',
                                                                       file_base='headline_en_clean_again_headline_part2',
                                                                       work_create_time_sleep=60, INSERT_KEY=GET_LUCY_KEY)
list_for_work_id2, batch_result_id2 = write_execute_embed_batch_commands(headline_cn_clean_again_headline_part2, 'cleaned_headline_toembed', batch_size=10000,
                                                                         file_input_path = 'data/gpt_results/headline_embedding/input/part2/',
                                                                         file_output_path = 'data/gpt_results/headline_embedding/output/part2/',
                                                                         file_base='headline_cn_clean_again_headline_part2',
                                                                         work_create_time_sleep=60, INSERT_KEY=GET_LUCY_KEY)
list_for_work_id3, batch_result_id3 = write_execute_embed_batch_commands(headline_cn_traditional_clean_again_headline_part2, 'cleaned_headline_toembed', batch_size=10000,
                                                                         file_input_path = 'data/gpt_results/headline_embedding/input/part2/',
                                                                         file_output_path = 'data/gpt_results/headline_embedding/output/part2/',
                                                                         file_base='headline_cn_traditional_clean_again_headline_part2',
                                                                         work_create_time_sleep=60, INSERT_KEY=GET_LUCY_KEY)





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Consolidate gpt results back to original df
def consolidate_batch_results_emebddings(df_to_merge_back,
                                         input_path = 'data/gpt_results/headline_embedding/output/part1/',
                                         batch_base_name='headline_cn_clean_again_headline_outputs*.jsonl'):
    # crucial for defining a list as an element
    df_to_merge_back['headline_embedding'] = pd.Series(dtype=object)
    # record results from each line to df
    file_path_raw_outputs_pattern = input_path +batch_base_name
    file_path_raw_outputs = glob.glob(file_path_raw_outputs_pattern)
    for i in range(0,len(file_path_raw_outputs)):
        temp_file_path = file_path_raw_outputs[i]
        with open(temp_file_path, 'r') as file:
            # for line in file:
            #     data = json.loads(line)
            #     index_response = data['custom_id']
            #     index_response = pd.to_numeric(index_response.strip('request'))
            #     content = data['response']['body']['data'][0]['embedding']
            #     df_to_merge_back.at[index_response, 'headline_embedding'] = content

            for line in file:
                try:
                    data = json.loads(line)
                    # Extract the index of the response and clean it
                    index_response = data['custom_id']
                    index_response = pd.to_numeric(index_response.strip('request'))
                    content = data['response']['body']['data'][0]['embedding']
                    # Assign the embedding to the appropriate location in the DataFrame
                    df_to_merge_back.at[index_response, 'headline_embedding'] = content
                except KeyError as e:
                    print(f"Error parsing line {line}: Missing key {e}")
                except Exception as e:
                    print(f"Unexpected error while processing line: {e}")
    return df_to_merge_back




# consolidate for part 1
df_en = consolidate_batch_results_emebddings(df_to_merge_back=headline_en_clean_again_headline,input_path='data/gpt_results/headline_embedding/output/part1/',batch_base_name='headline_en_clean_again_headline_outputs*.jsonl')
df_cn = consolidate_batch_results_emebddings(df_to_merge_back=headline_cn_clean_again_headline,input_path='data/gpt_results/headline_embedding/output/part1/',batch_base_name='headline_cn_clean_again_headline_outputs*.jsonl')
df_cn_traditional =  consolidate_batch_results_emebddings(df_to_merge_back=headline_cn_traditional_clean_again_headline,input_path='data/gpt_results/headline_embedding/output/part1/',batch_base_name='headline_cn_traditional_clean_again_headline_outputs*.jsonl')


# consolidate for part 2
df_en_part2 = consolidate_batch_results_emebddings(df_to_merge_back=headline_en_clean_again_headline_part2,input_path='data/gpt_results/headline_embedding/output/part2/',batch_base_name='headline_en_clean_again_headline_part2_outputs*.jsonl')
df_cn_part2 = consolidate_batch_results_emebddings(df_to_merge_back=headline_cn_clean_again_headline_part2,input_path='data/gpt_results/headline_embedding/output/part2/',batch_base_name='headline_cn_clean_again_headline_part2_outputs*.jsonl')
df_cn_traditional_part2 =  consolidate_batch_results_emebddings(df_to_merge_back=headline_cn_traditional_clean_again_headline_part2,input_path='data/gpt_results/headline_embedding/output/part2/',batch_base_name='headline_cn_traditional_clean_again_headline_part2_outputs*.jsonl')



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Use embeddings to calculate consine similarities between CN and English headlines
# Note that for each record construct a time window of +/- 2 days for potential matches
# extract the embeddings and calculate the cos-sim score, take the max pair out of the potential matches
# start with traditional cn

def matching_headlines(df1,df2):
    # clean data
    df2['timestamp_dt'] = pd.to_datetime(df2['timestamp_dt'],format='mixed')
    df2['obs_id'] = df2.index
    df1['timestamp_dt'] = pd.to_datetime(df1['timestamp_dt'],format='mixed')
    df1['matched_headline_embedding'] = pd.Series(dtype=object)
    # for each record, get the date, construct a window +/- 2 days for slicing en articles, extract embeddings and calculate cos_sim, take max as match
    for i in range(0,len(df1)):

        embedding_df1 = df1.loc[i,'headline_embedding']
        # slice base on window
        window_mid_point = pd.to_datetime(df1.loc[i,'timestamp_dt'])
        window_start = window_mid_point - pd.Timedelta(days=2)
        window_end = window_mid_point + pd.Timedelta(days=2)

        slice_df2 = df2[(pd.to_datetime(df2['timestamp_dt'])>=window_start) &
                        (pd.to_datetime(df2['timestamp_dt'])<=window_end)]

        # calculate cosine similarity and obtain highest match
        slice_df2['cos_sim'] = slice_df2.apply(lambda row: cosine_similarity(row['headline_embedding'],embedding_df1),axis=1)
        slice_df2['cos_sim'] = pd.to_numeric(slice_df2['cos_sim'], errors='coerce')
        # choose_slice = slice_df2[slice_df2['cos_sim'] == slice_df2['cos_sim'].max()]
        choose_slice = slice_df2.nlargest(1, 'cos_sim')
        choose_slice = choose_slice.add_prefix('matched_')
        for k in range(0,len(choose_slice.columns)):
            df1.at[i, choose_slice.columns[k]] = choose_slice.iloc[0,k]

        print ((i+1)/len(df1))

    return df1

# run for part 1
df_cn_matched = matching_headlines(df1=df_cn,df2=df_en)
df_cn_traditional_matched = matching_headlines(df1=df_cn_traditional,df2=df_en)


# df_cn_matched.to_csv('data/pooled_cnen_news/matched_headline/cn_articles.csv.gz',index=False)
# df_cn_traditional_matched.to_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles.csv.gz',index=False)

df_cn_matched = pd.read_csv('data/pooled_cnen_news/matched_headline/cn_articles.csv.gz')
df_cn_traditional_matched= pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles.csv.gz')





# run for part 2
df_cn_matched_part2 = matching_headlines(df1=df_cn_part2,df2=df_en_part2)
df_cn_traditional_matched_part2 = matching_headlines(df1=df_cn_traditional_part2,df2=df_en_part2)


# df_cn_matched_part2.to_csv('data/pooled_cnen_news/matched_headline/cn_articles_part2.csv.gz',index=False)
# df_cn_traditional_matched_part2.to_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles_part2.csv.gz',index=False)

df_cn_matched_part2 = pd.read_csv('data/pooled_cnen_news/matched_headline/cn_articles_part2.csv.gz')
df_cn_traditional_matched_part2= pd.read_csv('data/pooled_cnen_news/matched_headline/cn_traditional_articles_part2.csv.gz')









