from lib.spider.zufang_spider import *

if __name__ == "__main__":
    # spider = ZuFangBaseSpider(SPIDER_NAME)
    # spider.get_area_zufang_info('sh', 'xinchang')
    page = 'https://sh.lianjia.com/zufang/SH2832727017697583104.html?nav=0&unique_id=eef0f59d-14fe-4fd0-93ae-1625d6b2aefazufanglonghuapg31627017711434'
    look_up_detail(page)
    print()
