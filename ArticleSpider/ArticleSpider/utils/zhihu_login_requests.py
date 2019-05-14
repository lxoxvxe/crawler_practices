# -*- coding: utf-8 -*-

import requests

#python2和python3兼容代码
try:
    import cookielib
except:
    from http import cookiejar

import re
import time
import hmac
import hashlib
import json
import base64
from PIL import Image
import matplotlib.pyplot as plt

agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
header = {
    'Connection':'keep-alive',
    'Host':'www.zhihu.com',
    'Referer':'https://www.zhihu.com/',
    'User-Agent':agent
}

login_url = "https://www.zhihu.com/"
login_api = "https://www.zhihu.com/api/v3/oauth/sign_in"
form_data = {
    "client_id":"c3cef7c66a1843f8b3a9e6a1e3160e20",
    "grant_type":"password",
    #"timestamp",
    "source":"com.zhihu.web",
    #"signature",
    "username":"",
    "password":"",
    #"captcha",

    #改为 "cn" 是倒立汉字验证码
    "lang":"en",

    "ref_source":"other_",
    "utm_source":""
}

class ZhihuAccount(object):


    def __init__(self):
        self.login_url = login_url
        self.login_api = login_api
        self.login_data = form_data.copy()
        self.session = requests.session()
        self.session.headers = header.copy()
        self.session.cookies = cookiejar.LWPCookieJar(filename='./cookies.txt')


    def login(self, username=None, password=None, load_cookies=True):
        if load_cookies and self.load_cookies():
            if self.check_login():
                return True

        headers = self.session.headers.copy()
        self.get_xsrf_dc0()
        headers.update({
            'x-udid':self.udid,
            'x-xsrftoken':self.xsrf
        })
        username, password = self._check_user_pass(username, password)
        self.login_data.update({
            'username':username,
            'password':password
        })
        timestamp = str(int(time.time()*1000))
        self.login_data.update({
            'captcha':self._get_captcha(self.login_data['lang'], headers),
            'timestamp':timestamp,
            'signature':self._get_signature(timestamp)
        })

        response = self.session.post(self.login_api, data=self.login_data, headers=headers)
        if "error" in response.text:
            print(json.loads(response.text)['error']['message'])
        elif self.check_login():
            return True
        print('登录失败')
        return False


    def load_cookies(self):
        try:
            self.session.cookies.load(ignore_discard=True)
            return True
        except FileNotFoundError:
            return False


    def check_login(self):
        #通过"个人资料编辑页面"返回的状态码来判断是否登陆
        response = self.session.get("https://www.zhihu.com/people/edit", allow_redirects=False)
        if response.status_code == 200 or response.status_code == 302:
            self.session.cookies.save()
            print('登录成功')
            return True
        return False


    def get_xsrf_dc0(self):
        response = self.session.get(self.login_url)
        #贪婪匹配
        match_object = re.match(r"(.+)\|\d*", response.cookies["d_c0"])
        self.udid = match_object.group(1)
        self.xsrf = response.cookies["_xsrf"]


    def _check_user_pass(self, username, password):
        if username is None:
            username = self.login_data.get("username")
            if not username:
                username = input("请输入台湾手机号:")
        if "+886" not in username:
            username = '+886' + username[1:]

        if password is None:
            password = self.login_data.get("password")
            if not password:
                password = input("请输入密码:")
        return username, password


    def _get_captcha(self, lang, headers):
        if lang == 'cn':
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
        else:
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        response = self.session.get(api, headers=headers)
        show_captcha = re.search(r'true', response.text)

        if show_captcha:
            put_resp = self.session.put(api, headers=headers)
            json_data = json.loads(put_resp.text)
            #??? 为什么是r'\n' 。。。这样等于replace了'\\n'
            img_base64 = json_data["img_base64"].replace(r'\n', '')
            with open('./captcha.jpg', 'wb') as f:
                f.write(base64.b64decode(img_base64))
            img = Image.open('./captcha.jpg')
            if lang == 'cn':
                plt.imshow(img)
                print('点击所有倒立的汉字，按回车提交')
                points = plt.ginput(7)
                capt = json.dumps({
                    'img_size':[200, 44],
                    'input_points':[[i[0]/2, i[1]/2] for i in points]
                })
            else:
                img.show()
                capt = input('请输入图片里的验证码:')

            self.session.post(api, data={'input_text':capt}, headers=headers)
            return capt
        return ''


    def _get_signature(self, timestamp):
        ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
        grant_type = self.login_data['grant_type']
        client_id = self.login_data['client_id']
        source = self.login_data['source']
        ha.update(bytes((grant_type + client_id + source + timestamp), 'utf-8'))
        return ha.hexdigest()


if __name__ == "__main__":
    acount = ZhihuAccount()
    acount.login(username="+886966722263", password="rxjmn456", load_cookies=True)
    #!!!只支持使用台湾的电话号码登陆!!!