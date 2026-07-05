import gzip
import json
import pandas as pd
from datetime import datetime, timedelta

import nltk
nltk.download('punkt')


def construct_raw_df(file_path):
    with gzip.open(file_path, 'rt', encoding='utf-8') as file:
        # Step 2: Read and parse the JSON data
        json_sample = json.load(file)

    # Step 1: Decompress the GZIP file
    with gzip.open(file_path, 'rt', encoding='utf-8') as file:
        # Step 2: Read and parse the JSON data
        json_sample = json.load(file)

    # Step 3: Construct the dataframe
    df = pd.DataFrame([x['data'] for x in json_sample['Items']])
    time = pd.DataFrame([x['timestamps'][0] for x in json_sample['Items']])
    df = pd.concat([time, df], axis=1)
    return df



def construct_macro_filter_subject_list():
    manual_subjects = pd.read_csv("utility/filters/subject_code_manually_labelled.csv")
    subject_filter = manual_subjects[manual_subjects['Filter'] != 1]
    subject_filter = subject_filter[['RCS', "N2000"]].reset_index(drop=True)
    subject_filter['N2000'] = "N2:" + subject_filter['N2000']
    subject_RCS_list = subject_filter['RCS'].tolist()
    subject_N2000_list = subject_filter['N2000'].tolist()

    subject_filter_list = subject_N2000_list + subject_RCS_list
    return subject_filter_list


def construct_macro_filter_suffix_list():
    manual_suffix = pd.read_csv("utility/filters/consolidated_suffix_manually_labelled.csv")
    # clean suffix due to starting with 0.
    manual_suffix['Code'] = manual_suffix['Code'].apply(lambda x: str(x).lstrip('0') if str(x).startswith('0') else x)
    suffix_filter = manual_suffix[manual_suffix['Filter'] != 1]
    suffix_filter = suffix_filter[['Code']].drop_duplicates().reset_index(drop=True)
    suffix_list = suffix_filter['Code'].tolist()

    return suffix_list




# Note for Reuters data the current max range is from 1996-01 to 2023-09
def construct_webfile_path(year, month):
    # Creating a datetime object with the random year and month
    yr_mth = datetime(year, month, 1)
    formatted_date = yr_mth.strftime("%Y-%m")

    # Constructing the file path
    file_path = (
        rf"\\mediaflux.researchsoftware.unimelb.edu.au\proj-3330_refinitiv-1128.4.1342\STORY.RTRS.{formatted_date}.REC.JSON.txt.gz"
    )
    return file_path


def construct_col_list_type_unique(df, column):
    unique_elements = set()
    df[column].apply(lambda x: unique_elements.update(x))
    unique_vals_col = pd.DataFrame(list(unique_elements), columns=[column])
    return unique_vals_col


def construct_col_nonlist_type_unique(df, column):
    # Extract unique elements from the specified column
    unique_elements = df[column].unique()

    # Create a new DataFrame from the unique elements
    unique_vals_col = pd.DataFrame(unique_elements, columns=[column])

    return unique_vals_col


def construct_negative_killer_exact(df, judge_column, exact_filter_list):
    df_new = df[[judge_column]]
    new_columns = exact_filter_list
    for column in new_columns:
        df_new[column] = df[judge_column].apply(lambda x: column in x)
    return df_new


def construct_sum_of_kills(dfsum, judge_column):
    dfsum = dfsum.drop(columns=[judge_column]).sum().sort_values(ascending=False)
    return dfsum


def construct_negative_killer_fuzzy(df, judge_column, fuzzy_filter_list):
    df_new = df[[judge_column]]
    new_columns = fuzzy_filter_list

    for column in new_columns:
        df_new[column] = df[judge_column].apply(lambda x: any(column in item for item in x))
    return df_new

# Complete filtering process, subject+suffix filter, remove TOPNEWS records. Subject to changes in future (2024/06/30), use construct_df_remove_top_news first!!!
# (If top news is required to be removed)
def construct_subjects_filtered_df(df, subject_filter, suffix_filter):
    df_new = df[df['body'] != ""]
    df_new = df_new[~df_new['headline'].str.contains('TOP NEWS')]
    df_new = df_new[~df_new['headline'].str.contains('BUZZ')]
    df_new = df_new[~df_new['subjects'].apply(lambda x: any(element in x for element in subject_filter))]
    df_new = df_new[
        ~df_new['subjects'].apply(lambda x: any(any(fuzzystr in item for fuzzystr in suffix_filter) for item in x))]
    df_new = df_new.drop_duplicates(subset=['body'])
    return df_new


# For stricter filtering apply a 2nd layer of filter
def construct_macro_filter_subject_list_extra():
    manual_subjects = pd.read_csv("utility/filters/subject_code_manually_labelled_miscellaneous.csv")
    subject_filter = manual_subjects[manual_subjects['Filter'] != 1]
    subject_filter = subject_filter[['RCS', "N2000"]].reset_index(drop=True)
    subject_filter['N2000'] = "N2:" + subject_filter['N2000']
    subject_RCS_list = subject_filter['RCS'].tolist()
    subject_N2000_list = subject_filter['N2000'].tolist()

    subject_filter_list_extra = subject_N2000_list + subject_RCS_list
    return subject_filter_list_extra

# For stricter filtering apply a 2nd layer of filter
def construct_subjects_filtered_df_extra(df, subject_filter_extra):
    df_new = df[~df['subjects'].apply(lambda x: any(element in x for element in subject_filter_extra))]
    return df_new

def construct_headline_filtered_df(temp_df,headlinefilter):
    for i in headlinefilter:
        temp_df = temp_df[~temp_df['headline'].str.contains(i)]
    return temp_df


def construct_excluded_records_df(unfiltered_df, subject_filter, suffix_filter):
    df_excluded = unfiltered_df[unfiltered_df['subjects']
    .apply(lambda x: any(element in x for element in subject_filter) or any(
        any(fuzzystr in item for fuzzystr in suffix_filter) for item in x))]
    return df_excluded


def construct_killer_lists_as_column(input_list, subject_list, suffix_list):
    list_holder = []
    # First, check for the exact match in the consolidated list
    for element in input_list:
        if element in subject_list:
            list_holder.append(element)

    # Next, check if any substring of the element is in the suffix list
    for element in input_list:
        # Avoid adding the same element twice
        if element in list_holder:
            continue
        for i in range(len(element)):
            for j in range(i + 1, len(element) + 1):
                substring = element[i:j]
                if substring in suffix_list:
                    list_holder.append(element)
                    break  # Found a valid substring, no need to check other substrings of this element
            if element in list_holder:
                break  # Once the element is added to list_holder, no need to check further
    return list_holder




def construct_filter_and_report(df_raw,subject_filter, suffix_filter):
    df_raw = df_raw[df_raw['body'] != ""]
    df_raw = df_raw[~df_raw['headline'].str.contains('TOP NEWS')]
    df_raw_test = df_raw[~df_raw['subjects'].apply(lambda x: any(element in x for element in subject_filter))]
    print("removed " + str(len(df_raw) - len(df_raw_test)) + " out of " + str(len(df_raw)) + " rows")
    df_raw_test_pass_two = df_raw_test[~df_raw_test['subjects'].apply(
        lambda x: any(any(fuzzystr in item for fuzzystr in suffix_filter) for item in x))]
    print("removed " + str(len(df_raw_test) - len(df_raw_test_pass_two)) + " out of " + str(len(df_raw_test)) + " rows")
    return df_raw_test_pass_two


def construct_df_remove_top_news(df_raw,top_news_list):
    df_raw = df_raw[~df_raw['subjects'].apply(lambda x: any(element in x for element in top_news_list))]
    return df_raw

# translation function, chinese to english, will break-down to chunks of sentences to satisfy query limitation (500 characters)
# https://pypi.org/project/translate/
def construct_translation_to_en(text):
    translator = Translator(from_lang='autodetect', to_lang='en')
    max_chunk_size = 300

    # Tokenize the text into sentences
    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Check if adding the next sentence would exceed the max_chunk_size
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())

    translations = []

    for chunk in chunks:
        translation = translator.translate(chunk)
        translations.append(translation)

    # Combine the translated chunks into a single string
    full_translation = ' '.join(translations)
    print(f"Translated text: {full_translation}")

def construct_translation_to_en_return(text):
    translator = Translator(from_lang='autodetect', to_lang='en')
    max_chunk_size = 300

    # Tokenize the text into sentences
    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Check if adding the next sentence would exceed the max_chunk_size
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())

    translations = []

    for chunk in chunks:
        translation = translator.translate(chunk)
        translations.append(translation)

    # Combine the translated chunks into a single string
    full_translation = ' '.join(translations)
    return full_translation

# return exlcuded records from two dataframes(larger df must be inclusive of smaller df)
def construct_df_diff(df1,df2):
    diff_df = pd.concat([df1, df2]).drop_duplicates(keep=False)
    return diff_df