import pandas as pd
import numpy as np
import textwrap


# used for choosing data if elements in a list type column contains a string of interest
def observer_func_contain_str_filter(df, column, string_of_interest):
    filtered = df[df[column].apply(lambda x: string_of_interest in x)]
    return filtered


# used for choosing data if elements in a list type column starts with a string of interest
def observer_func_start_header_filter(df, column, string_of_interest):
    filtered_start = df[df[column].apply(lambda x: any(item.startswith(string_of_interest) for item in x))]
    return filtered_start


def observer_reader_index_body(df, index, body=True, subjects=False, headline=True,time=True,altId=True):
    wrapper = textwrap.TextWrapper(width=80)
    if time:
        print ("Time")
        print (wrapper.fill(df.loc[index, "timestamp"]))
        print ('\n')
    if headline:
        print ("Headline")
        print (wrapper.fill(df.loc[index, "headline"]))
        print ('\n')
    if body:
        print("Body:")
        print(wrapper.fill(df.loc[index, "body"]))
        print('\n')
    if subjects:
        print ("Subjects:")
        print(wrapper.fill(str(df.loc[index, "subjects"])))
    if altId:
        print ("altId:")
        print(wrapper.fill(str(df.loc[index, "altId"])))


def observer_reader_index_body_ret_text(df, index, body=True, subjects=False, headline=True, time=True, altId=True):
    wrapper = textwrap.TextWrapper(width=80)
    result = []

    if time:
        result.append("Time")
        result.append(wrapper.fill(df.loc[index, "timestamp"]))
        result.append('\n')
    if headline:
        result.append("Headline")
        result.append(wrapper.fill(df.loc[index, "headline"]))
        result.append('\n')
    if body:
        result.append("Body:")
        result.append(wrapper.fill(df.loc[index, "body"]))
        result.append('\n')
    if subjects:
        result.append("Subjects:")
        result.append(wrapper.fill(str(df.loc[index, "subjects"])))
        result.append('\n')
    if altId:
        result.append("altId:")
        result.append(wrapper.fill(str(df.loc[index, "altId"])))
        result.append('\n')

    return '\n'.join(result)

def observer_body_text(df, index):
    wrapper = textwrap.TextWrapper(width=80)
    text = wrapper.fill(df.loc[index, "body"])
    return text


def observer_clean(df):
    df_clean = df[['timestamp', 'body', 'headline', 'subjects']]
    return df_clean


def observer_reader_index_all(df, index):
    wrapper = textwrap.TextWrapper(width=80)

    for column in df.columns:
        print(f"{column.capitalize()}:")
        print(wrapper.fill(str(df.loc[index, column])))
        print('\n')