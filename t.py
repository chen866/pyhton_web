'''class Solution:
    def reverse(self, x):
        rev = 0
        sign = 1
        if x < 0:
            sign = -1
            x *= -1
        while x != 0:
            temp = rev
            pop = x % 10
            x //= 10
            rev = temp * 10 + pop
        if sign == -1:
            rev *= -1
        if rev > 2 ** 31 - 1 or rev < 2 ** 31:
            return 0
        else:
            return rev


class Solution:
    def reverse(self, x):
        """
        :type x: int
        :rtype: int
        """
        rtn = ""
        neg = 1 if int(x) > 0 else -1
        for i in range(len(str(abs(x)))):
            rtn += str(x)[-1 - i]
        return neg * (int(rtn) if -2 ** 31 <= int(rtn) <= 2 ** 31 - 1 else 0)

import requests
from bs4 import BeautifulSoup
# import bs4
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
headers={"User-Agent":user_agent}  #请求头,headers是一个字典类型

html = requests.get('http://www.qiushibaike.com/text/',headers=headers).content
soup = BeautifulSoup(html,'lxml')
'''


import re
import requests
from lxml import etree

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
headers = {"User-Agent": user_agent}  # 请求头,headers是一个字典类型

html = requests.get('http://spyun.gen58.com/mp4/', headers=headers).content

selector = etree.HTML(html)

parent_links = selector.xpath('//a/@href')
parent_links.remove(parent_links[0])

pattern1 = re.compile(r'[0-9]{5,16}')
name = 535
pause_str = '2018_02_21'
pause = 0
pause_1 = 5
for link in parent_links:
    if pause_str in link:
        pause += 1
    if pause < 1:
        continue
    number = 0
    two_html = requests.get('http://spyun.gen58.com' + link, headers=headers).content
    two_selector = etree.HTML(two_html)
    if two_selector is None:
        continue
    sizes = two_selector.xpath('/html/body/pre/text()')
    links = two_selector.xpath('/html/body/pre/a/@href')
    links.remove(links[0])
    for i in range(len(links)):
        if links[i].split('.')[-1] == 'mp4' and re.search(pattern1, sizes[i]) is not None and len(
                re.search(pattern1, sizes[i]).group()) < 9:
            number += 1
            print(str(number) + "\t" + links[i] + "\t" + re.search(pattern1, sizes[i]).group()[0:-3] + 'K')
            if pause_str in links[i]:
                pause += 1
            if pause < pause_1:
                continue
            with open('C:/迅雷下载/mp4/' + str(name) + '.mp4', 'wb') as handle:
                name += 1
                response = requests.get(url='http://spyun.gen58.com' + links[i], headers=headers)
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)

import requests
from lxml import etree

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
headers = {"User-Agent": user_agent}  # 请求头,headers是一个字典类型

html = requests.get('http://spyun.gen58.com/mp4/2017_06_30/', headers=headers).content

selector = etree.HTML(html)

p = selector.xpath('/html/body/pre/text()')

pattern1 = re.compile('^\d{5,20}$')
re.search(pattern1, w).group()

two_html = requests.get('http://spyun.gen58.com/mp4/2018_06_26/', headers=headers).content
two_selector = etree.HTML(two_html)
sizes = two_selector.xpath('/html/body/pre/text()')
links = two_selector.xpath('/html/body/pre/a/@href')
links.pop(0)
for i in range(len(links)):
    if links[i].split('.')[-1] == 'mp4' and len(re.search(pattern1, sizes[i]).group()) < 9:
        print(i)
        with open('C:/迅雷下载/mp4/' + str(name) + '.mp4', 'wb') as handle:
            name += 1
            response = requests.get(url='http://spyun.gen58.com' + links[i], headers=headers)
            for block in response.iter_content(1024):
                if not block:
                    break
                handle.write(block)
