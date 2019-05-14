# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import datetime
import scrapy
import re
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose,TakeFirst,Join
from ArticleSpider.utils.common import extract_num
from ArticleSpider.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


# def add_jobbole(value)：
#     return value + "-jobbole"


def date_convert(create_date):
    try:
        create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


def get_nums(value):
    match_obj = re.match(r".*?(\d+).*$", value)
    if match_obj:
        nums = int(match_obj.group(1))
    else:
        nums = 0

    return nums


def remove_comment_tags(value):
    #去掉tag中提取的评论
    if "评论" in value:
        return ""
    else:
        return value


def return_value(value):
    return value


class ArticleItemLoader(ItemLoader):
    #自定义itemloader
    default_output_processor = TakeFirst()


#定义(用来获取文章的)item
class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field(
        #input_processor = MapCompose(lambda x:x+"-jobbole")
    )
    create_date = scrapy.Field(
        input_processor=MapCompose(lambda x:x.strip().replace("·","").strip(), date_convert),
        #output_processor=TakeFirst()
    )
    url = scrapy.Field()
    # md5
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into jobbole_article(title, url, create_date, fav_nums, front_image_url)
                    VALUES(%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE fav_nums=VALUES(fav_nums)
                """
        params = (self["title"], self["url"], self["create_date"], self["fav_nums"], self["front_image_url"][0])

        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):

    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num, 
              watch_user_num, click_num, crawl_time
              ) 
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content),answer_num=VALUES(answer_num),
               comments_num=VALUES(comments_num),watch_user_num=VALUES(watch_user_num),click_num=VALUES(click_num)
        """

        zhihu_id = self['zhihu_id'][0] #不能用''.join(self['zhihu_id'])因为list里面是int
        topics = ','.join(self['topics'])
        url = ''.join(self['url'])
        title = ''.join(self['title'])
        content = ''.join(self['content'])
        answer_num = extract_num(''.join(self['answer_num'])) if self.get('answer_num', '') else 0
        comments_num = extract_num(''.join(self['comments_num']))
        watch_user_num = int(self['watch_user_num'][1].replace(',', ''))
        click_num = int(self['watch_user_num'][0].replace(',', ''))
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, comments_num,
              watch_user_num, click_num, crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):

    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, 
              praise_num, comments_num, create_time, update_time, crawl_time 
              ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num),
              praise_num=VALUES(praise_num), update_time=VALUES(update_time)
        """

        create_time = datetime.datetime.fromtimestamp(self['create_time']).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self['update_time']).strftime(SQL_DATETIME_FORMAT)
        params = (self['zhihu_id'], self['url'], self['question_id'], self['author_id'],
                  self['content'], self['praise_num'], self['comments_num'],
                  create_time, update_time, self['crawl_time'].strftime(SQL_DATETIME_FORMAT))

        return insert_sql, params
