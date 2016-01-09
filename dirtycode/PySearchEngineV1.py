# -*- coding:utf-8 -*-

import urllib2
from BeautifulSoup import *
from urlparse import *
from pysqlite2 import dbapi2 as sqlite
import jieba
import sys 
reload(sys)
sys.setdefaultencoding('utf8') 

# ignorewords = set(['the','of','to','and','a','in','is','it','-','，','。'])
ignorewords = set(['the','of','to','and','a','in','is','it',])


# 过滤地址用的正则表达式
# r'http://movie.douban.com/top250\?start=\d+.*'
# r'http://movie.douban.com/subject/\d+'


class crawler:

    # 初始化crawler的类并传入数据库名称
    def __init__(self,dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    # 辅助函数，用于获取条目的id，并且如果条目不存在，就将其加入数据库中
    def getentryid(self,table,field,value,createnew=True):
        return None

    # 为每个网页建立索引
    def addtoindex(self,url,soup):
        if self.isindexed(url): return
        print 'Indexing %s' % url


    # 从一个HTML页面中提取文字（不带标签的）
    def gettextonly(self,soup):
        return None

    # 根据任何非空白字符进行分词处理
    # 此处需要重写
    # 注意一下此处list中的元素原先是 str
    # 修改后 返回的list中元素变成 unicode 类型
    def separatewords(self,text):
        return None

    # 如果url已经建立过索引，则返回True
    def isindexed(self,url):
        return False

    # 添加一个关联两个网页的链接
    def addlinkref(self,urlFrom,urlTo,linkText):
        pass

    # 地址过滤器
    def urlfilter(self,url):
        matcher_1 = re.compile(r'http://movie.douban.com/top250\?start=\d+.*')
        matcher_2 = re.compile(r'http://movie.douban.com/subject/\d+')

        if ( matcher_1.match(url) != None or matcher_2.match(url) != None ):
            return True

        return False


    # 从一小组网页开始进行广度优先搜索。直至某一给定深度，
    # 期间为网页建立索引
    def crawl(self,pages,depth=3):
        for i in range(depth):
            newpages = set()
            for page in pages:
                try:
                    c = urllib2.urlopen(page)
                except:
                    print "Could not open %s" % page
                    continue

                #soup = BeautifulSoup(c.read().decode('utf-8'))
                soup = BeautifulSoup(c.read())
                self.addtoindex(page,soup)

                links=soup('a')
                for link in links:
                    if ('href' in dict(link.attrs)):
                        url=urljoin(page,link['href'])
                        if url.find("'")!=-1: continue
                        url=url.split('#')[0]
                        if url[0:4]=='http' and not self.isindexed(url):
                            if self.urlfilter(url):
                                newpages.add(url)
                                linkText=self.gettextonly(link)
                                self.addlinkref(page,url,linkText)

                self.dbcommit()
            pages=newpages

    # 创建数据库表
    def createindextables(self):
        self.con.execute('create table urllist(url)')
        self.con.execute('create table wordlist(word)')
        self.con.execute('create table wordlocation(urlid,wordid,location)')
        self.con.execute('create table link(fromid integer,toid integer)')
        self.con.execute('create table linkwords(wordid,linkid)')
        self.con.execute('create index wordidx on wordlist(word)')
        self.con.execute('create index urlidx on urllist(url)')
        self.con.execute('create index wordurlidx on wordlocation(wordid)')
        self.con.execute('create index urltoidn on link(toid)')
        self.con.execute('create index urlfromidx on link(fromid)')
        self.con.commit()


