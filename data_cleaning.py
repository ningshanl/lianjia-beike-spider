import pandas as pd
import numpy as np
import re
import os
import time
from functools import reduce


BASIC_KEY = []
FACILITY_KEY = []


def decode_detail_info(detail_string):
    detail_dict = eval(detail_string)
    basic_dict, facility_dict, subway, comment = None, None, None, None
    if 'basic' in detail_dict.keys():
        basic_dict = eval(detail_dict['basic'])
    if 'facility' in detail_dict.keys():
        facility_dict = eval(detail_dict['facility'])
    if 'subway' in detail_dict.keys():
        subway = detail_dict['subway']
    if 'comment' in detail_dict.keys():
        comment = detail_dict['comment']
    return detail_dict


def combine_data():
    data_path = os.path.join('.', 'data')
    file_list = []
    non_alignment_file_list = []
    error_list = []
    sum_df = pd.DataFrame(columns=['chinese_district', 'chinese_area', 'xiaoqu', 'layout', 'size', 'price',
                                   'picture_url',
                                   'detail_url', 'bikan', 'detail_info'])
    for root, dirs, files in os.walk(data_path, topdown=False):
        for name in files:
            file_name = os.path.join(root, name)
            file_list.append(file_name)

    for f in file_list:
        try:
            df = pd.read_csv(f, sep='\t',
                             names=['chinese_district', 'chinese_area', 'xiaoqu', 'layout', 'size', 'price',
                                    'picture_url',
                                    'detail_url', 'bikan', 'detail_info'])
        except Exception as e:
            non_alignment_file_list.append(f)
            error_list.append(e)
            continue
        else:
            sum_df = pd.concat([sum_df, df], ignore_index=True)
    sum_df.to_csv('sum_data.csv', sep='\t')


def generate_key(df, name):
    values = df['detail_info'].values.tolist()

    def map_func(item):
        root_dic = eval(item)
        if name in root_dic.keys():
            item_dic = eval(root_dic[name])
            key = item_dic.keys()
        else:
            key = []
        return set(key)

    def reduce_func(item1, item2):
        if not item1:
            return item2
        elif not item2:
            return item1
        else:
            return item1.update(item2)

    return reduce(reduce_func, map(map_func, values))


def decode_basic_dic(row):
    root_dic = eval(row['detail_info'])
    row_ans = []
    if 'basic' in root_dic.keys():
        item_dic = eval(root_dic['basic'])
        for key in BASIC_KEY:
            if key in item_dic.keys():
                row_ans.append(item_dic[key])
            else:
                row_ans.append('')
    else:
        row_ans = ['' for i in range(len(BASIC_KEY))]
    return row_ans


def decode_facility_dic(row):
    root_dic = eval(row['detail_info'])
    row_ans = []
    if 'facility' in root_dic.keys():
        item_dic = eval(root_dic['facility'])
        for key in FACILITY_KEY:
            if key in item_dic.keys():
                row_ans.append(item_dic[key])
            else:
                row_ans.append('')
    else:
        row_ans = ['' for i in range(len(BASIC_KEY))]
    return row_ans


def decode_comment(row):
    root_dic = eval(row['detail_info'])
    if 'comment' in root_dic.keys():
        return root_dic['comment']
    else:
        return ''


def decode_subway(row):
    root_dic = eval(row['detail_info'])
    if 'subway' in root_dic.keys():
        return root_dic['subway']
    else:
        return ''


def decode_whole(df):
    basic_info_per_row = list(df.apply(decode_basic_dic, axis=1))
    facility_info_per_row = list(df.apply(decode_facility_dic, axis=1))
    basic_info_per_col = list(zip(*basic_info_per_row))
    facility_info_per_col = list(zip(*facility_info_per_row))

    comment = list(df.apply(decode_comment, axis=1))
    subway = list(df.apply(decode_subway, axis=1))

    for i in range(len(BASIC_KEY)):
        name = BASIC_KEY[i]
        df[name] = basic_info_per_col[i]
    for i in range(len(FACILITY_KEY)):
        name = FACILITY_KEY[i]
        df[name.strip()] = facility_info_per_col[i]

    df['comment'] = comment
    df['subway'] = subway
    df.drop(columns=['detail_info'], axis=1, inplace=True)


def trivial_modify(df):
    def split_district(r):
        text = r['chinese_district']
        if ',' in text:
            _, name = text.split(',', 1)
        else:
            name = ''
        return name
    df['district'] = df.apply(split_district, axis=1)
    df.drop(columns=['chinese_district'], axis=1, inplace=True)

    def split_xiaoqu(r):
        text = r['xiaoqu']
        if '·' in text:
            rent_type, name = text.split('·', 1)
        else:
            rent_type, name = '', ''
        return [rent_type, name]
    xiaoqu_per_row = list(df.apply(split_xiaoqu, axis=1))
    rent_types, names = zip(*xiaoqu_per_row)
    df['rent_type'] = rent_types
    df['xiaoqu_name'] = names
    df.drop(columns=['xiaoqu'], axis=1, inplace=True)


def deal_layout(df):
    def func(r):
        text = r['layout']
        shi_list = re.findall(r'(.*)室', text)
        ting_list = re.findall(r'室(.*)厅', text)
        shi = 0
        ting = 0
        if shi_list:
            shi = int(shi_list[0])
        if ting_list:
            ting = int(ting_list[0])
        return [shi, ting]
    layout_per_row = list(df.apply(func, axis=1))
    room, hall = zip(*layout_per_row)
    df['room'] = room
    df['hall'] = hall
    df.drop(columns=['layout'], axis=1, inplace=True)


def deal_size(df):
    def func(r):
        text = r['size']
        size_list = re.findall(r'(.*)平米', text)
        size = 0
        if size_list:
            size = float(size_list[0])
        return size
    df['numberic_size'] = df.apply(func, axis=1)
    df.drop(columns=['size'], axis=1, inplace=True)
    df.drop(columns=['面积'], axis=1, inplace=True)


def deal_duration(df):
    def func(r):
        text = r['租期']
        negative_list = re.findall(r'(.*)年以内', text)
        positive_list = re.findall(r'(.*)年以上', text)
        duration = 0
        if negative_list:
            duration = -1*int(negative_list[0])
        elif positive_list:
            duration = int(positive_list[0])
        return duration
    df['duration'] = df.apply(func, axis=1)
    df.drop(columns=['租期'], axis=1, inplace=True)


def deal_floor(df):
    def func(r):
        text = r['楼层']
        type_list = re.findall(r'(.*)楼层', text)
        floor_list = re.findall(r'/(.*)层', text)
        floor_type = ''
        floor_number = 0
        if type_list:
            floor_type = type_list[0]
        if floor_list:
            floor_number = int(floor_list[0])
        return [floor_type, floor_number]
    floor_per_row = list(df.apply(func, axis=1))
    f_type, f_num = zip(*floor_per_row)
    df['floor_type'] = f_type
    df['floor_number'] = f_num
    df.drop(columns=['楼层'], axis=1, inplace=True)


def deal_maintain(df):
    def func(r):
        text = r['维护']
        day = -1
        if '今天' in text:
            return 0
        day_list = re.findall(r'(.*)天前', text)
        week_list = re.findall(r'(.*)周前', text)
        if day_list:
            day = int(day_list[0])
        elif week_list:
            day = 7*int(day_list[0])
        return day
    df['maintain'] = df.apply(func, axis=1)
    df.drop(columns=['维护'], axis=1, inplace=True)


def deal_check_in(df, today):
    # today is a string of time with format 'xxxx-xx-xx'
    today_stamp = time.mktime(time.strptime(today, "%Y-%m-%d"))

    def func(r):
        text = r['入住']
        gap = -1
        if '随时入住' in text:
            return 0
        if re.match(r'\d\d\d\d-\d\d-\d\d', text):
            check_time = time.mktime(time.strptime(text, "%Y-%m-%d"))
            gap = check_time-today_stamp
        return gap
    df['gap'] = df.apply(func, axis=1)
    df.drop(columns=['入住'], axis=1, inplace=True)


def deal_subway(df):
    def func(r):
        text = r['subway']
        # text = '13号线 - 武宁路 689m 3号线,4号线,11号线(花桥-迪士尼),11号线(嘉定北-迪士尼) - 曹杨路 1044m 13号线,11号线(嘉定北-迪士尼),11号线(花桥-迪士尼) - 隆德路 1112m '
        station_list = re.findall(r'(\d+)m', text)
        if station_list:
            minimal = min(station_list)
            return minimal
        else:
            return -1
    df['min_subway_dist'] = df.apply(func, axis=1)
    df.drop(columns=['subway'], axis=1, inplace=True)


def feature_extract(df):
    # extract information from text
    deal_layout(df)
    deal_size(df)
    deal_duration(df)
    deal_floor(df)
    deal_maintain(df)
    deal_check_in(df, '2021-07-23')
    deal_subway(df)


if __name__ == '__main__':
    # combine_data()
    # file = '/Users/apple/Desktop/lianjia-beike-spider/data/ke/zufang/sh/20210723/pudong_zhangjiang.csv'
    # df = pd.read_csv(file, sep='\t',
    #                  names=['chinese_district', 'chinese_area', 'xiaoqu', 'layout', 'size', 'price',
    #                         'picture_url',
    #                         'detail_url', 'bikan', 'detail_info'])
    file = 'sum_data.csv'
    df = pd.read_csv(file, sep='\t')

    # generate global information
    BASIC_KEY = list(generate_key(df, 'basic'))
    FACILITY_KEY = list(generate_key(df, 'facility'))

    decode_whole(df)
    trivial_modify(df)
    feature_extract(df)
    df.to_csv('standard_data.csv', sep='\t')
