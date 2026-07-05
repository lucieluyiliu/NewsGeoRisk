# Repo copy of Henry_updated pipeline. Data stays in Henry_updated/data; paths
# below are relative, so switch the working directory there (see config.py).
import os as _os; from config import HENRY_ROOT as _HR; _os.chdir(_HR)

# the purpose for this code is to collect macro level news by utilizing Thomson Reuters tagging system and a bag of words filter on newspaper headlines
# the tagging system has 2 components: 1. suffix tags indicative of the news is related to a certain public company and its corresponding listing market
# 2. subject tags which indicate the topic of a certain news such as N2:XXXX
# Additional requirements: the article must be in English, Chinese or traditional Chinese
# It must also be an article where China and America are both discussed (achieved by bag of words)
# A dataframe showing the number of articles is also generated

# Finally the code translates the headlines for further matching in part 002

from utility.functions.construct_raw_df import *
from utility.parameters.parameters import *
import os

# initialize the filtering lists ------------------------------------------------------------------------------
# load related filters for newspaper articles
subject_filter = construct_macro_filter_subject_list()
suffix_filter = construct_macro_filter_suffix_list()
subject_filter_extra = construct_macro_filter_subject_list_extra()
# filter by topnews and headlines
TopNewsList = TopNewsList()
top_news_list = TopNewsList.TopNewsList
HeadlineFilterList = HeadlineFilterList()
headline_filter_list = HeadlineFilterList.HeadlineFilterList

# initialize the list of bag of words related to mentioning of CN and US
ChinaAmericaList = ChinaAmericaList()
cn_us_list = ChinaAmericaList.ChinaAmericaList

ChinaAmericaListCN = ChinaAmericaListCN()
cn_us_listCN = ChinaAmericaListCN.ChinaAmericaListCN
cn_us_listCN_compound = ChinaAmericaListCN.ChinaAmericaListCompound
cn_us_listCN_complex = ChinaAmericaListCN.ChinaAmericaListCNTranditional


def count_crit_compound_word(text, temp_list):
    for word in temp_list:
        if word.lower() in text.lower():
            return 2
    return 0





# filter and count teh articles
def establish_pooled_event(year, month, flag_list, flag_list_cn, extra_layer=True):
    # establish the file route based on year and month
    temp_file_path = construct_webfile_path(year, month)

    # remove top news
    temp_raw_df = construct_raw_df(temp_file_path)
    temp_raw_df = construct_df_remove_top_news(temp_raw_df, top_news_list)

    # filter the raw data set by remove null body, and null headline apply 2 filters (subject filter and suffix filter)
    temp_raw_df = temp_raw_df[temp_raw_df['headline'].notnull()]
    temp_raw_df = temp_raw_df[(temp_raw_df['body'].notna()) & (temp_raw_df['body'].str.strip() != "")]
    temp_raw_df = temp_raw_df[temp_raw_df['body'].fillna('').str.strip().astype(bool)]
    filtered_temp_raw_df = construct_subjects_filtered_df(temp_raw_df, subject_filter, suffix_filter)
    filtered_temp_raw_df = construct_headline_filtered_df(filtered_temp_raw_df, headline_filter_list)
    if extra_layer:
        filtered_temp_raw_df = construct_subjects_filtered_df_extra(filtered_temp_raw_df, subject_filter_extra)

    # remove historical takes of the same news, keep only the latest version
    temp_idx = filtered_temp_raw_df.groupby(['altId'])['takeSequence'].idxmax()
    filtered_temp_raw_df = filtered_temp_raw_df.loc[temp_idx].sort_index()

    # pool news according to the flag ----------------------------------------------------------------
    # initialize the flag indicator and split articles into Chinese and English articles to check if US and China bag of words were mentioned
    filtered_temp_raw_df['flag'] = 0

    slice_for_en_flag = filtered_temp_raw_df[filtered_temp_raw_df['language'].isin(['en', 'EN'])].copy()
    slice_for_cn_flag = filtered_temp_raw_df[filtered_temp_raw_df['language'].isin(['cn', 'CN', 'zh', 'ZH'])].copy()
    slice_for_cn_flag['flag_traditional'] = 0

    # construct flag according to language of record and ensure the article is China nad US related--------------------------------------------------------------
    # flag is 1 if US related bag of words is mentioned

    # check whether there is critical word within the body of the df (ensure an article discusses US and CN at same time)
    def count_crit_word(text, temp_list):
        for word in temp_list:
            if word.lower() in text.lower():
                return 1
        return 0



    for temp_list in flag_list:
        slice_for_en_flag['flag'] = slice_for_en_flag['flag'] + slice_for_en_flag['body'].apply(
            lambda x: count_crit_word(x, temp_list))


    # flag is 1 if Chinese related bag of words is mentioned
    for temp_list in flag_list_cn:
        slice_for_cn_flag['flag'] = slice_for_cn_flag['flag'] + slice_for_cn_flag['body'].apply(
            lambda x: count_crit_word(x, temp_list))
    # flag_traditional is 1 if Chinese (traditional) related bag of words is mentioned
    for temp_list in cn_us_listCN_complex:
        slice_for_cn_flag['flag_traditional'] = slice_for_cn_flag['flag_traditional'] + slice_for_cn_flag['body'].apply(
            lambda x: count_crit_word(x, temp_list))
    # flag is 1 if Chinese US compounded (e.g. US-Cino, US-China etc.) related bag of words is mentioned
    slice_for_cn_flag['flag'] = slice_for_cn_flag['flag'] + slice_for_cn_flag['body'].apply(
        lambda x: count_crit_word(x, cn_us_listCN_compound))



    # get id's where the flags are greater than 2 (meaning both China and US are mentioned) and count the number of articles based on index
    pooled_events_en_index = slice_for_en_flag[slice_for_en_flag['flag'] >= 2].index
    pooled_events_cn_index = slice_for_cn_flag[slice_for_cn_flag['flag'] >= 2].index
    pooled_events_cn_complex_index = slice_for_cn_flag[slice_for_cn_flag['flag_traditional'] >= 2].index

    # combine 3 ids and collect the pool of events
    combined_indices = pooled_events_en_index.union(pooled_events_cn_index)
    combined_indices = combined_indices.union(pooled_events_cn_complex_index)
    pool_of_events = filtered_temp_raw_df.loc[combined_indices]

    return pool_of_events







def filter_loop_for_whole_data(start_year, start_month, end_year, end_month):
    """
    Run establish_pooled_event from start_year/start_month to end_year/end_month inclusive.

    save results to local
    """

    year = start_year
    month = start_month

    # create folder
    os.makedirs("data/pooled_cnen_news", exist_ok=True)
    while (year < end_year) or (year == end_year and month <= end_month):
        try:
            temp_result = establish_pooled_event(year, month, cn_us_list, cn_us_listCN, extra_layer=True)
            temp_result.to_csv(f"data/pooled_cnen_news/pooled_records{year}_{month}.csv.gz")
            print(f"Finished {year}-{month:02d}")
        except Exception as e:
            print(f"Skipped {year}-{month:02d} because of error: {e}")

        # move to next month
        month += 1
        if month > 12:
            month = 1
            year += 1


filter_loop_for_whole_data(2023,10,2024,12)

# translate headlines ----------------------------------------------------------------
def consolidate_pooled_events(start_year, start_month, end_year, end_month):
    """
    Consolidate dataframes within range
    """
    # read dataframes

    year = start_year
    month = start_month
    consolidated_pooled = pd.DataFrame()
    while (year < end_year) or (year == end_year and month <= end_month):
        try:
            temp_df = pd.read_csv(f"data/pooled_cnen_news/pooled_records{year}_{month}.csv.gz")
            consolidated_pooled = pd.concat([consolidated_pooled, temp_df])
            print(f"Finished {year}-{month:02d}")
        except Exception as e:
            print(f"Skipped {year}-{month:02d} because of error: {e}")

        # move to next month
        month += 1
        if month > 12:
            month = 1
            year += 1

    return consolidated_pooled


# consolidate the pooled events (split to 2 parts, part2 is updated 202310-202412)
consolidated_pooled_dfs = consolidate_pooled_events(1996,1,2023,9)
consolidated_pooled_dfs.to_csv("data/pooled_cnen_news/consolidated_pooled_dfs.csv.gz",index=False)
consolidated_pooled_dfs_part2 = consolidate_pooled_events(2023,10,2024,12)
consolidated_pooled_dfs_part2.to_csv("data/pooled_cnen_news/consolidated_pooled_dfs_part2.csv.gz",index=False)


# get Chinese records that need translate and label whether it is traditional chinese or simplified chiense
def get_records_need_translate(df):
    consolidated_pooled_need_translate = df[
        df['language'].isin(['zh', 'ZH', 'cn', 'CN'])]

    return consolidated_pooled_need_translate

consolidated_pooled_dfs_part1_need_translate = get_records_need_translate(consolidated_pooled_dfs)
consolidated_pooled_dfs_part2_need_translate = get_records_need_translate(consolidated_pooled_dfs_part2)




# Module for GPT block, translating the headlines - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import time
from openai import OpenAI
import glob


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
    list_of_headline = df_to_prompt['headline'].to_list()

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




# run GPT procedure and collect results for part 1 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
GET_LUCY_KEY = os.getenv("GPT_LUCY_KEY")
list_for_translate_work_id, batch_headline_translate_result_id = write_execute_translate_batch_commands(
    df_to_prompt=consolidated_pooled_dfs_part1_need_translate, batch_size=2000,INSERT_API=GET_LUCY_KEY, file_base='gpt_cn_headline_translate',
    input_route='data/gpt_results/translation/input/consolidated_pooled_part_one/',
    output_route='data/gpt_results/translation/output/consolidated_pooled_part_one/',
    work_create_time_sleep=10)




consolidated_pooled_dfs_part1_need_translate  = consolidated_pooled_dfs_part1_need_translate.reset_index(drop=True)
consolidated_pooled_translated_part1 = consolidate_batch_results(df_to_merge_back=consolidated_pooled_dfs_part1_need_translate, result_column_name='cn_headline_translated',
                                            batch_base_name='gpt_cn_headline_translate*.jsonl')

consolidated_pooled_translated_part1.to_csv('data/pooled_cnen_news/consolidated_pooled_headline_translated_part1.csv.gz',index=False)


# run GPT procedure and collect results for part 2 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
GET_LUCY_KEY = os.getenv("GPT_LUCY_KEY")
list_for_translate_work_id, batch_headline_translate_result_id = write_execute_translate_batch_commands(
    df_to_prompt=consolidated_pooled_dfs_part2_need_translate, batch_size=2000,INSERT_API=GET_LUCY_KEY, file_base='gpt_cn_headline_translate',
    input_route='data/gpt_results/translation/input/consolidated_pooled_part_two/',
    output_route='data/gpt_results/translation/output/consolidated_pooled_part_two/',
    work_create_time_sleep=10)



consolidated_pooled_dfs_part2_need_translate  = consolidated_pooled_dfs_part2_need_translate.reset_index(drop=True)
consolidated_pooled_translated_part2 = consolidate_batch_results(df_to_merge_back=consolidated_pooled_dfs_part2_need_translate, result_column_name='cn_headline_translated',
                                                                 output_path='data/gpt_results/translation/output/consolidated_pooled_part_two/',
                                            batch_base_name='gpt_cn_headline_translate*.jsonl')

consolidated_pooled_translated_part2.to_csv('data/pooled_cnen_news/consolidated_pooled_headline_translated_part2.csv.gz',index=False)




