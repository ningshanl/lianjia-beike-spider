#!/usr/bin/env python
# coding=utf-8
# author: zengyuetian
# 此代码仅供学习与交流，请勿用于商业用途。
# 二手房信息的数据结构


class ZuFang(object):
    def __init__(self, district, area, xiaoqu, layout, size, price, picture_url, detail_url, bikan, detail=''):
        self.district = district
        self.area = area
        self.xiaoqu = xiaoqu
        self.layout = layout
        self.size = size
        self.price = price
        self.pic_url = picture_url
        self.detail_url = detail_url
        self.bikan = str(bikan)
        self.detail = detail

    def text(self):
        return self.district + "\t" + \
               self.area + "\t" + \
               self.xiaoqu + "\t" + \
               self.layout + "\t" + \
               self.size + "\t" + \
               self.price + "\t" + \
               self.pic_url + "\t" + \
               self.detail_url + "\t" + \
               self.bikan + "\t" + \
               self.detail
