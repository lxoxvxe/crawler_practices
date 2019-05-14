# -*- coding: utf-8 -*-
import hashlib
import re

def get_md5(url):

    #判断传进来的url是否为unicode。如果是unicode,把它转为utf-8
    if isinstance(url, str):
        url = url.encode("utf-8")

    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


def extract_num(text):

    text.replace(',', '')
    match_obj = re.match(r".*?(\d+).*$", text)
    if match_obj:
        nums = int(match_obj.group(1))
    else:
        nums = 0

    return nums


if __name__ == "__main__":
    print(get_md5("http://jobbole.com"))