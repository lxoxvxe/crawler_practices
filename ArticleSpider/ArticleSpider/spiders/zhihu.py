# -*- coding: utf-8 -*-
import scrapy
import json
import time
import base64
import hmac
import hashlib
import re
import datetime
import matplotlib.pyplot as plt
from PIL import Image
from urllib import parse
from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuQuestionItem, ZhihuAnswerItem


class ZhihuSpider(scrapy.Spider):

    name = 'zhihu'

    allowed_domains = ['www.zhihu.com']

    start_urls = ['https://www.zhihu.com/']

    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data[*].is_normal,\
    admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,\
    is_sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,\
    reshipment_settings,comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,\
    relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[*].mark_infos[*].url;data[*].author.follower_count,\
    badge[?(type=best_answerer)].topics&limit={1}&offset={2}&sort_by=default'
    #教程里，有把url最后的'&sort_by=default'去掉

    headers = {

        'Connection': 'keep-alive',

        'Host': 'www.zhihu.com',

        'Referer': 'https://www.zhihu.com/',

        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'

    }


    def parse(self, response):

        # #失败。。。
        # with open('./zhihu5.html', 'wb') as f:
        #
        #     f.write(response.body)

        # 设置检查
        # yield scrapy.Request('https://www.zhihu.com/question/23246712', headers=self.headers, callback=self.test, \
        #                      meta={'dont_redirect': True, "handle_httpstatus_list": [301, 302, 303]})


        """
        (深度优先)
        提取出html页面中的所有url，并跟踪这些url做进一步爬取
        如果提取的url中格式为/question/xxx 就下载之后直接进入解析函数
        """

        all_urls = response.css("a::attr(href)").extract()

        all_urls = [parse.urljoin(response.url, url) for url in all_urls]

        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)

        for url in all_urls:

            match_obj = re.match(r'(.*/question/(\d+))(/|$).*', url)

            if match_obj:

                request_url = match_obj.group(1)

                question_id = int(match_obj.group(2))

                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question,\
                                     meta={'zhihu_id':question_id, 'dont_redirect': True, "handle_httpstatus_list": [301, 302, 303]})
                #请求https://www.zhihu.com/question/286459762时，发生了Redirecting

                break #检测点

            # else:
            #
            #     yield scrapy.Request(url, headers=self.headers)


    def test(self, response):
        with open('./zhihu_check.html', 'wb') as f:
            f.write(response.body)
            pass


    def parse_question(self, response):

        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)

        item_loader.add_css('title', 'h1.QuestionHeader-title::text')

        # item_loader.add_xpath('title', "//h1[@class='QuestionHeader-title']/text()|//h1[@class='QuestionHeader-title']/a/text()")

        item_loader.add_css('content', '.QuestionHeader-detail')

        item_loader.add_value('url', response.url)

        item_loader.add_value('zhihu_id', response.meta.get('zhihu_id', ''))

        item_loader.add_css('answer_num', 'h4.List-headerText span::text')

        item_loader.add_css('comments_num', '.QuestionHeader-Comment button::text')

        item_loader.add_css('watch_user_num', 'strong.NumberBoard-itemValue::text')

        item_loader.add_css('topics', '.QuestionHeader-topics .Popover div::text')

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(response.meta.get('zhihu_id', ''), 20, 0),

                             headers=self.headers,

                             callback=self.parse_answer)

        # yield question_item

        # for i in self.parse(response):
        #
        #     yield i

        # all_urls = response.css("a::attr(href)").extract()
        #
        # all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        #
        # all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        #
        # for url in all_urls:
        #
        #     match_obj = re.match(r'(.*/question/(\d+))(/|$).*', url)
        #
        #     if match_obj:
        #
        #         request_url = match_obj.group(1)
        #
        #         question_id = int(match_obj.group(2))
        #
        #         yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question,
        #                              meta={'zhihu_id': question_id})
        #
        #     else:
        #
        #         yield scrapy.Request(url, headers=self.headers)


    def parse_answer(self, response):

        ans_json = json.loads(response.text)

        is_end = ans_json['paging']['is_end']

        # totals_anwer = ans_json['paging']['totals']

        next_url = ans_json['paging']['next']

        for answer in ans_json['data']:

            answer_item = ZhihuAnswerItem()

            answer_item['zhihu_id'] = answer['id']

            answer_item['url'] = answer['url']

            answer_item['question_id'] = answer['question']['id']

            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None

            answer_item['content'] = answer['content'] if 'content' in answer else None #answer['excerpt']

            answer_item['praise_num'] = answer['voteup_count']

            answer_item['comments_num'] = answer['comment_count']

            answer_item['create_time'] = answer['created_time']

            answer_item['update_time'] = answer['updated_time']

            answer_item['crawl_time'] = datetime.datetime.now()

            yield answer_item

        if not is_end:

            scrapy.Request(next_url,

                           headers=self.headers,

                           callback=self.parse_answer)


    #重写scrap.Spider里的start_requests
    def start_requests(self):

        return [scrapy.Request('https://www.zhihu.com/signup',

                               headers=self.headers,

                               callback=self.cap1)]


    def cap1(self, response):

        # 错!!!没有response.cookies
        # token = response.cookies['_xsrf']

        #也可用"utf-8" decode bytes object
        token = response.headers.getlist('Set-Cookie')[1].split(b';')[0].split(b'=')[1]

        self.headers.update({

            'X-Xsrftoken': token

        })

        return [scrapy.Request('https://www.zhihu.com/api/v3/oauth/captcha?lang=en',

                               headers=self.headers,

                               callback=self.check_need_capt)]


    #这个函数这样写不知道对不对
    def check_need_capt(self, response):

        if 'true' in response.text:

            return self.cap2()

        return self.login(None)


    def cap2(self):

        return [scrapy.Request('https://www.zhihu.com/api/v3/oauth/captcha?lang=en',

                             headers=self.headers,

                             method='PUT',

                             callback=self.cap3,

                             dont_filter=True)]


    def cap3(self, response):

        json_data = json.loads(response.text)

        img_base64 = json_data['img_base64'].replace(r'\n', '')

        with open('./captcha.jpg', 'wb') as f:

            f.write(base64.b64decode(img_base64))

        img = Image.open('./captcha.jpg')

        img.show()

        capt = input('请输入图片里的验证码：')

        # 这里必须先把参数 POST 验证码接口
        return [scrapy.FormRequest(

            'https://www.zhihu.com/api/v3/oauth/captcha?lang=en',

            headers = self.headers,

            formdata = {'input_text': capt},

            method = 'POST',

            callback = self.login,

            dont_filter = True,

            meta= {'capt': capt}

        )]


    def login(self, response):

        capt = response.meta['capt'] if response != None else ''

        timestamp = str(int(time.time() * 1000))

        self.post_data = {

            'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',

            'grant_type': 'password',

            'source': 'com.zhihu.web',

            'username': '+886966722263',

            'password': 'rxjmn456',

            # 改为'cn'是倒立汉字验证码
            'lang': 'en',

            'ref_source': 'other_',

            'captcha': capt,

            'timestamp': timestamp,

        }

        self.post_data.update({

            'signature': self._get_signature(timestamp)

        })

        return [scrapy.FormRequest(

            'https://www.zhihu.com/api/v3/oauth/sign_in',

            formdata=self.post_data,

            headers=self.headers,

            method='POST',

            callback=self.check_login

        )]


    def _get_signature(self, timestamp):

        ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)

        grant_type = self.post_data['grant_type']

        client_id = self.post_data['client_id']

        source = self.post_data['source']

        ha.update(bytes((grant_type + client_id + source + timestamp), 'utf-8'))

        return ha.hexdigest()


    def check_login(self, response):

        return [scrapy.Request(

            'https://www.zhihu.com/signup',

            headers=self.headers,

            callback=self.check_login2,

            dont_filter=True,

            meta={

                'dont_redirect': True,

                'handle_httpstatus_list': [302]

            }

        )]


    def check_login2(self, response):

        if response.status == 302:

            print('登录成功！')

            for url in self.start_urls:

                yield scrapy.Request(

                    url,

                    headers=self.headers,

                    dont_filter=True,

                )
















