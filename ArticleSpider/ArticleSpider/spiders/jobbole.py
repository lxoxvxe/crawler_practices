# -*- coding: utf-8 -*-
import re
import scrapy
import datetime
from scrapy.http import Request
from urllib import parse
from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5
from scrapy.loader import ItemLoader


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):

        #解析列表页中的所有文章url，并交给scrapy下载后 并进行分析
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            #！！！上面可以用extract_first是因为post_node又经过css select过, 又变回了一个{SelectorList}

            #如果post_url里没有域名，可用
            #response.url + post_url
            #但是response.url可能不只是域名(ex:'http://blog.jobbole.com/all-posts/')
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url":parse.urljoin(response.url, image_url)}, callback=self.parse_detail)

        #提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        #这边extract_first("")的功用非常重要
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):

        #实例化
        article_item = JobBoleArticleItem()

        #提取文章的具体字段
        #fire fox: /html/body/div[1]/div[3]/div[1]/div[1]/h1
        #re_selector = response.xpath("/html/body/div[1]/div[3]/div[1]/div[1]/h1")
        #re2_selector = response.xpath('//*[@id="post-114093"]/div[1]/h1/text()')
        '''title = response.xpath('//div[@class="entry-header"]/h1/text()').extract()[0]

        create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract()[0].strip().replace("·","").strip()

        praise_nums = response.xpath("//span[contains(@class, 'vote-post-up')]/h10/text()").extract()[0]'''
        #praise_nums = response.xpath("//*[@id='114093votetotal']/text()").extract()[0]

        '''match_obj = re.match(r".*?(\d+).*$",response.xpath("//span[contains(@class, 'bookmark-btn')]/text()").extract()[0])'''
        #其中，(\d*)如果写成(\d+)的话，执行print(match_obj.group(1))，有可能会报错 AttributeError: 'NoneType' object has no attribute 'group'
        #因为有可能根本没有数字(根本没人收藏),致使正则表达式无法match
        '''if match_obj:
            fav_nums = match_obj.group(1)
        else:
            fav_nums = 0

        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0]
        match_obj = re.match(r".*?(\d+).*$",comment_nums)
        if match_obj:
            comment_nums = match_obj.group(1)
        else:
            comment_nums = 0

        content = response.xpath("//div[@class='entry']").extract()[0]

        tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        tags = ",".join(tag_list)'''


        #通过css选择器提取字段
        '''
        
        title = response.css(".entry-header h1::text").extract_first("没有元素")

        create_date = response.css("p.entry-meta-hide-on-mobile::text").extract()[0].strip().replace("·","").strip()

        praise_nums = response.css(".vote-post-up h10::text").extract_first("没有元素")
        praise_nums = int(praise_nums)

        fav_nums = response.css(".bookmark-btn::text").extract_first("没有元素")
        match_obj = re.match(r".*?(\d+).*$",fav_nums)
        if match_obj:
            fav_nums = int(match_obj.group(1))
        else:
            fav_nums = 0

        comment_nums = response.css("a[href='#article-comment'] span::text").extract_first("没有元素")
        match_obj = re.match(r".*?(\d+).*$", comment_nums)
        if match_obj:
            comment_nums = int(match_obj.group(1))
        else:
            comment_nums = 0

        content = response.css("div.entry").extract_first("没有元素")

        tag_list = response.css("p.entry-meta-hide-on-mobile a::text").extract()
        tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        tags = ",".join(tag_list)

        #list0 = response.css("p.entry-meta-hide-on-mobile a::text")

        
        #list0 = response.css("p.entry-meta-hide-on-mobile a::text")
        #tag_list = []
        #for each in list0:
            #tag_list.append([each].extract_first("没有元素"))
            #AttributeError: list object has no attribute extract_first
            #下次可尝试用tag_list.append(each.css("").extract_first("没有元素"))
        #tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        #tags = ",".join(tag_list)

        article_item["url_object_id"] = get_md5(response.url)
        article_item["url"] = response.url
        article_item["title"] = title
        try:
            create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        article_item["create_date"] = create_date
        article_item["front_image_url"] = [front_image_url]
        article_item["praise_nums"] = praise_nums
        article_item["fav_nums"] = fav_nums
        article_item["comment_nums"] = comment_nums
        article_item["tags"] = tags
        article_item["content"] = content
        '''


        #通过item loader加载item
        front_image_url = response.meta.get("front_image_url", "")  # 文章封面图
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_value("front_image_url", [front_image_url]) # 其实不用加[]的
        item_loader.add_css("praise_nums", ".vote-post-up h10::text")
        item_loader.add_css("fav_nums", ".bookmark-btn::text")
        item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        article_item = item_loader.load_item()

        #对item调用yield后， 这个item会传递到pipelines
        yield article_item