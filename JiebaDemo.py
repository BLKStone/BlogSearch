# -*- coding:utf-8 -*-
import jieba
import re
import sys 
reload(sys)
sys.setdefaultencoding('utf8') 


def separatewords(text):
    splitter=re.compile('\\W*')
    return [s.lower() for s in splitter.split(text) if s!='']

text = "Hello my name is xiaoming, nice to meet you!"

lis = separatewords(text)

for li in lis:
    print type(li)
    print li

def CHseparatewords(text):
    
    seg_list = jieba.cut_for_search(text)
    result = []
    for seg in seg_list:
        result.append(seg)
    return result

lis = CHseparatewords('小明硕士毕业于中国科学院计算所，后在日本京都大学深造。')
for li in lis:
    print type(li)
    print li