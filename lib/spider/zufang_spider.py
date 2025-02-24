#!/usr/bin/env python
# coding=utf-8
# author: zengyuetian
# 此代码仅供学习与交流，请勿用于商业用途。
# 爬取租房数据的爬虫派生类

import re
import csv
import time
import threadpool
from bs4 import BeautifulSoup
from lib.item.zufang import *
from lib.spider.base_spider import *
from lib.utility.date import *
from lib.utility.path import *
from lib.zone.area import *
from lib.zone.city import get_city
import lib.utility.version


def write_information(info, path):
    with open(path, "a") as f:
        csv_write = csv.writer(f)
        csv_write.writerow(info)
    return None


def look_up_detail(url):
    headers = create_headers()
    response = requests.get(url, timeout=30, headers=headers)
    html = response.content
    soup = BeautifulSoup(html, "lxml")

    ans_dict = {}

    basic_info = soup.find('div', class_='content__article__info')
    if basic_info:
        info_dict = {}
        for item in basic_info.find_all('li'):
            try:
                item.get_text()
            except Exception as e:
                print('!!!', e)
                continue

            if item.get_text() == '基本信息':
                continue
            if '：' in item.get_text():
                try:
                    spliced = item.get_text().split('：', 1)
                    info_dict[spliced[0]] = spliced[1]
                except Exception as e:
                    print('split fail', e)
                    print("=" * 20)
        ans_dict['basic'] = str(info_dict)

    facility_info = soup.find('ul', class_='content__article__info2')
    if facility_info:
        info_dict = {}
        for item in facility_info.find_all('li'):
            # if item.get_text() == '配套设施':
            if len(item.find_all('i')) == 0:
                continue
            if 'fl oneline' not in str(item):
                continue
            if 'facility_no' in str(item['class']):
                info_dict[item.get_text()] = False
            else:
                info_dict[item.get_text()] = True
        ans_dict['facility'] = str(info_dict)

    description = soup.find('div', class_='content__article__info3')
    if description:
        try:
            text = description.find('p', {'data-el': 'houseComment'})
            if text:
                ans_dict['comment'] = text.get_text()
            else:
                print(url)
        except Exception as e:
            print('comment fail', e)
            print("=" * 20)

    subway_related = soup.find('div', {'class': re.compile('content__article__info4.*')})
    subway_string = ''
    if subway_related:
        for item in subway_related.find_all('li'):
            if '距离' in item.get_text():
                for tmp in item.find_all('span'):
                    subway_string += tmp.get_text()
                    subway_string += ' '
    ans_dict['subway'] = subway_string

    return str(ans_dict)


class ZuFangBaseSpider(BaseSpider):
    def collect_area_zufang_data(self, city_name, area_name, fmt="csv"):
        """
        对于每个板块,获得这个板块下所有出租房的信息
        并且将这些信息写入文件保存
        :param city_name: 城市
        :param area_name: 板块
        :param fmt: 保存文件格式
        :return: None
        """
        district_name = area_dict.get(area_name, "")
        csv_file = self.today_path + "/{0}_{1}.csv".format(district_name, area_name)
        with open(csv_file, "w") as f:
            # 开始获得需要的板块数据
            zufangs = self.get_area_zufang_info(city_name, area_name)
            # 锁定
            if self.mutex.acquire(1):
                self.total_num += len(zufangs)
                # 释放
                self.mutex.release()
            if fmt == "csv":
                for zufang in zufangs:
                    f.write(self.date_string + "," + zufang.text() + "\n")
        print("Finish crawl area: " + area_name + ", save data to : " + csv_file)

    @staticmethod
    def get_area_zufang_info(city_name, area_name):
        matches = None
        """
        通过爬取页面获取城市指定版块的租房信息
        :param city_name: 城市
        :param area_name: 版块
        :return: 出租房信息列表
        """
        total_page = 1
        district_name = area_dict.get(area_name, "")
        chinese_district = get_chinese_district(district_name)
        chinese_area = chinese_area_dict.get(area_name, "")
        zufang_list = list()
        page = 'http://{0}.{1}.com/zufang/{2}/'.format(city_name, 'lianjia', area_name)
        print(page)

        headers = create_headers()
        response = requests.get(page, timeout=10, headers=headers)
        html = response.content
        soup = BeautifulSoup(html, "lxml")

        # 获得总的页数
        try:
            if SPIDER_NAME == "lianjia":
                page_box = soup.find_all('div', class_='page-box')[0]
                matches = re.search('.*"totalPage":(\d+),.*', str(page_box))
            elif SPIDER_NAME == "ke":
                page_box = soup.find_all('div', class_='content__pg')[0]
                # print(page_box)
                matches = re.search('.*data-totalpage="(\d+)".*', str(page_box))
            total_page = int(matches.group(1))
            # print(total_page)
        except Exception as e:
            print("\tWarning: only find one page for {0}".format(area_name))
            print(e)

        # 从第一页开始,一直遍历到最后一页
        headers = create_headers()
        for num in range(1, total_page + 1):
            page = 'http://{0}.{1}.com/zufang/{2}/pg{3}'.format(city_name, 'lianjia', area_name, num)
            print(page)
            BaseSpider.random_delay()
            response = requests.get(page, timeout=30, headers=headers)
            html = response.content
            soup = BeautifulSoup(html, "lxml")

            # 获得有小区信息的panel
            if SPIDER_NAME == "lianjia":
                ul_element = soup.find('ul', class_="house-lst")
                house_elements = ul_element.find_all('li')
            else:
                ul_element = soup.find('div', class_="content__list")
                house_elements = ul_element.find_all('div', class_="content__list--item")

            if len(house_elements) == 0:
                continue
            # else:
            #     print(len(house_elements))

            for house_elem in house_elements:
                if SPIDER_NAME == "lianjia":
                    price = house_elem.find('span', class_="num")
                    xiaoqu = house_elem.find('span', class_='region')
                    layout = house_elem.find('span', class_="zone")
                    size = house_elem.find('span', class_="meters")
                else:
                    price = house_elem.find('span', class_="content__list--item-price")
                    desc1 = house_elem.find('p', class_="content__list--item--title")
                    desc2 = house_elem.find('p', class_="content__list--item--des")

                    # add detail url
                    detail_url = page + desc1.find('a')['href']

                    # add picture url
                    picture_url = ''
                    try:
                        picture_url = house_elem.find('img')['data-src']
                    except Exception as e:
                        print('picture not found because', e)
                        print("=" * 20)

                    # add 'bikanhaofang'
                    bikan = False
                    if '必看好房' in str(desc1):
                        bikan = True

                    # add detailed information
                    detail_info = ''
                    try:
                        detail_info = look_up_detail(detail_url)
                    except Exception as e:
                        error_info = str(e)+'\n'+detail_info+'\n'
                        write_information(error_info, 'log.txt')

                try:
                    if SPIDER_NAME == "lianjia":
                        price = price.text.strip()
                        xiaoqu = xiaoqu.text.strip().replace("\n", "")
                        layout = layout.text.strip()
                        size = size.text.strip()
                    else:
                        # 继续清理数据
                        price = price.text.strip().replace(" ", "").replace("元/月", "")
                        # print(price)
                        desc1 = desc1.text.strip().replace("\n", "")
                        desc2 = desc2.text.strip().replace("\n", "").replace(" ", "")
                        # print(desc1)

                        infos = desc1.split(' ')
                        xiaoqu = infos[0]
                        layout = infos[1]
                        descs = desc2.split('/')
                        # print(descs[1])
                        size = descs[1].replace("㎡", "平米")

                    # print("{0} {1} {2} {3} {4} {5} {6}".format(
                    #     chinese_district, chinese_area, xiaoqu, layout, size, price))

                    # 作为对象保存
                    zufang = ZuFang(chinese_district, chinese_area, xiaoqu, layout, size, price, picture_url,
                                    detail_url, bikan, detail=detail_info)
                    zufang_list.append(zufang)
                except Exception as e:
                    print("=" * 20 + " page no data")
                    print(e)
                    print(page)
                    print("=" * 20)
        return zufang_list

    def start(self):
        # for log
        localtime = time.asctime(time.localtime(time.time()))
        log_path = 'error_info_'+localtime+'.txt'

        city = get_city()
        self.today_path = create_date_path("{0}/zufang".format(SPIDER_NAME), city, self.date_string)
        # collect_area_zufang('sh', 'beicai')  # For debugging, keep it here
        t1 = time.time()  # 开始计时

        # 获得城市有多少区列表, district: 区县
        districts = get_districts(city)
        print('City: {0}'.format(city))
        print('Districts: {0}'.format(districts))

        # 获得每个区的板块, area: 板块
        areas = list()
        for district in districts:
            areas_of_district = get_areas(city, district)
            print('{0}: Area list:  {1}'.format(district, areas_of_district))
            # 用list的extend方法,L1.extend(L2)，该方法将参数L2的全部元素添加到L1的尾部
            areas.extend(areas_of_district)
            # 使用一个字典来存储区县和板块的对应关系, 例如{'beicai': 'pudongxinqu', }
            for area in areas_of_district:
                area_dict[area] = district
        print("Area:", areas)
        print("District and areas:", area_dict)

        # 准备线程池用到的参数
        nones = [None for i in range(len(areas))]
        city_list = [city for i in range(len(areas))]
        args = zip(zip(city_list, areas), nones)
        # areas = areas[0: 1]

        # 针对每个板块写一个文件,启动一个线程来操作
        pool_size = thread_pool_size
        pool = threadpool.ThreadPool(pool_size)
        my_requests = threadpool.makeRequests(self.collect_area_zufang_data, args)
        [pool.putRequest(req) for req in my_requests]
        pool.wait()
        pool.dismissWorkers(pool_size, do_join=True)  # 完成后退出

        # 计时结束，统计结果
        t2 = time.time()
        print("Total crawl {0} areas.".format(len(areas)))
        print("Total cost {0} second to crawl {1} data items.".format(t2 - t1, self.total_num))


if __name__ == '__main__':
    # get_area_zufang_info("sh", "xinchang")
    spider = ZuFangBaseSpider(SPIDER_NAME)
    spider.get_area_zufang_info('sh', 'xinchang')
    print()
