# -*- coding:utf-8 -*-

# https://github.com/jaybaird/python-bloomfilter/

import datetime
import urllib2
from BeautifulSoup import *
from urlparse import *
from pysqlite2 import dbapi2 as sqlite
from pybloom import BloomFilter
import jieba
import sys

reload(sys)
sys.setdefaultencoding('utf8')

ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it', '-', '，', '。', "'", '', u'的', u'是'])


# ignorewords = set(['the','of','to','and','a','in','is','it',])


class Crawler:
    # 初始化Crawler的类并传入数据库名称
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)
        self.visited = BloomFilter(capacity=1000000, error_rate=0.001)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    # 辅助函数，用于获取条目的id，并且如果条目不存在，就将其加入数据库中
    def getentryid(self, table, field, value, createnew=True):

        # print "select rowid from \
        #     %s where %s='%s'" % (table,field,value)
        cur = self.con.execute("select rowid from \
            %s where %s='%s'" % (table, field, value))
        res = cur.fetchone()

        # 如果条目不存在，就加入一条新数据
        if res is None:
            cur = self.con.execute("insert into %s \
                (%s) values ('%s')" % (table, field, value))
            return cur.lastrowid

        else:
            return res[0]

    # 为每个网页建立索引
    def addtoindex(self, url, soup):

        if self.isindexed(url):
            return

        print 'Indexing %s' % url

        # 获取每个单词
        text = self.gettextonly(soup)
        # 清理空格
        text = self.drytext(text)
        # 分词
        words = self.separatewords(text)

        # 得到URL的id
        urlid = self.getentryid('urllist', 'url', url)

        # 将每个单词与该url关联
        for i in range(len(words)):
            word = words[i]
            if word in ignorewords:
                continue
            wordid = self.getentryid('wordlist', 'word', word)
            self.con.execute("insert into wordlocation(urlid,wordid,location) \
                values (%d,%d,%d)" % (urlid, wordid, i))

    # 地址过滤器
    def urlfilter(self, url):
        matcher_1 = re.compile(r'http://movie.douban.com/top250\?start=\d+.*')
        matcher_2 = re.compile(r'^http://movie.douban.com/subject/\d+/$')

        if (matcher_1.match(url) is not None or
                    matcher_2.match(url) is not None):
            return True

        return False

    # 从一个HTML页面中提取文字（不带标签的）
    # 需要重构，删掉多余信息
    # javascript 去除
    # html 标签去除
    def gettextonly(self, soup):
        v = soup.string
        if v is None:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.gettextonly(t)
                resulttext += subtext + '\n'
            return resulttext
        else:
            return v.strip()

    # 删除空格
    # 此处还可以优化
    # 不要把\n 删掉
    def drytext(self, text):
        text = text.strip()
        text = ' '.join(text.split())
        return text

    # 根据任何非空白字符进行分词处理
    # 此处需要重写
    # 注意一下此处list中的元素原先是 str
    # 修改后 返回的list中元素变成 unicode 类型
    def separatewords(self, text):
        seg_list = jieba.cut_for_search(text)
        result = []
        for seg in seg_list:
            result.append(seg)
        return result

    # 如果url已经建立过索引，则返回True
    def isindexed(self, url):
        u = self.con.execute("select rowid from urllist \
            where url='%s'" % url).fetchone()

        if u is not None:
            # 检查它是否被检索过了
            v = self.con.execute('select * from \
                wordlocation where urlid=%d' % u[0]).fetchone()
            if v is not None:
                return True

        return False

    # isindexed 的布隆过滤器实现
    def isindexedbloom(self, url):
        return url in self.visited

    # 添加一个关联两个网页的链接
    def addlinkref(self, urlFrom, urlTo, linkText):

        fromid = self.getentryid('urllist', 'url', urlFrom)
        toid = self.getentryid('urllist', 'url', urlTo)

        cur = self.con.execute("insert into link\
            (fromid,toid) values (%d,%d)" % (fromid, toid))

        linkid = cur.lastrowid

        # 如果超链接的描述text为空的话就不添加数据库记录
        if linkText != '':
            # 拆分单词
            words = self.separatewords(linkText)

            for word in words:
                # print word
                wordid = self.getentryid('wordlist', 'word', word)
                # print ("insert into linkwords (wordid,linkid) values (%d,%d)" % (wordid,linkid))
                self.con.execute("insert into linkwords\
                    (wordid,linkid) values (%d,%d)" % (wordid, linkid))

        # self.dbcommit()
        return

    # 粒度适中便于分析的核心函数在于
    # crawl 和 addtoindex
    # 对每个页面的处理都是addtoindex
    # 从一小组网页开始进行广度优先搜索。直至某一给定深度，
    # 期间为网页建立索引
    def crawl(self, pages, depth=3):
        for i in range(depth):
            newpages = set()
            for page in pages:
                try:
                    c = urllib2.urlopen(page)
                except:
                    print "Could not open %s" % page
                    continue

                # soup = BeautifulSoup(c.read().decode('utf-8'))
                soup = BeautifulSoup(c.read())
                self.addtoindex(page, soup)
                self.visited.add(page)  # 加入布隆过滤器

                links = soup('a')

                for link in links:
                    if 'href' in dict(link.attrs):
                        url = urljoin(page, link['href'])
                        url = url.split('<')[0]
                        url = url.split('#')[0]

                        if url[0:4] == 'http' and not self.isindexedbloom(url):
                            if self.urlfilter(url):
                                newpages.add(url)
                                linktext = self.drytext(link.text)
                                self.addlinkref(page, url, linktext)

                self.dbcommit()
            pages = newpages

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


# 排序算法
class Searcher:
    # 初始化Searcher的类并传入数据库名称
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)
        self.debug_mode = False

    def __del__(self):
        self.con.close()

    def changedebugmode(self, switch):
        self.debug_mode = switch

    def dbcommit(self):
        self.con.commit()

    # 根据任何非空白字符进行分词处理
    # 此处需要重写
    # 注意一下此处list中的元素原先是 str
    # 修改后 返回的list中元素变成 unicode 类型
    def separatewords(self, text):
        seg_list = jieba.cut_for_search(text)
        result = []
        for seg in seg_list:
            result.append(seg)
        return result

    def getmatchrows(self, q):

        # 构造查询的字符串
        fieldlist = 'w0.urlid'
        tablelist = ''
        clauselist = ''
        wordids = []

        # 拆分单词
        words = self.separatewords(q)

        # 删除停词
        for word in words:
            if word in ignorewords:
                words.remove(word)

        # print words
        tablenumber = 0

        for word in words:

            # 检查语句
            print "select rowid from wordlist where word='%s'" % word

            # 获取单词的ID
            wordrow = self.con.execute(
                "select rowid from wordlist where word='%s'" % word).fetchone()

            if wordrow is not None:
                wordid = wordrow[0]
                wordids.append(wordid)

                if tablenumber > 0:
                    tablelist += ','
                    clauselist += ' and '
                    clauselist += 'w%d.urlid=w%d.urlid and ' % (tablenumber - 1, tablenumber)

                fieldlist += ',w%d.location' % tablenumber
                tablelist += 'wordlocation w%d' % tablenumber
                clauselist += 'w%d.wordid=%d' % (tablenumber, wordid)
                tablenumber += 1

        # 根据各个分组，建立查询
        fullquery = 'select %s from %s where %s' % (fieldlist, tablelist, clauselist)
        # debug 用于检查sql语句
        print fullquery
        cur = self.con.execute(fullquery)
        rows = [row for row in cur]
        return rows, wordids

    # 获取排序评分
    # wordids 查询的关键词分词后的id集合
    # rows 查询到的相关网页集合 (urlid,w0.location,w1.location,w2.location)
    def getscorelist(self, rows, wordids):
        totalscores = dict([(row[0], 0) for row in rows])

        # 此处是稍后放置评价函数的地方
        weights = [(1.0, self.frequencyscore(rows)), (0, self.locationscore(rows)),
                   (0, self.distancescore(rows))]

        for (weight, scores) in weights:
            for url in totalscores:
                totalscores[url] += weight * scores[url]

        return totalscores

    # 根据 urlid 查询url
    def geturlname(self, urlid):
        return self.con.execute(
            "select url from urllist where rowid=%d" % urlid).fetchone()[0]

    # 测试查询
    def query(self, q):
        rows, wordids = self.getmatchrows(q)
        print "测试点1", len(rows)
        scores = self.getscorelist(rows, wordids)
        print "测试点2", len(scores)
        # print scores[wordids[0]]
        rankedscores = sorted([(score, url) for (url, score) in scores.items()], reverse=1)
        for (score, urlid) in rankedscores[0:10]:
            print '%f\t%s' % (score, self.geturlname(urlid))

    # 归一化函数
    def normalizescore(self, scores, smallIsBetter = 0):
        vsmall = 0.00001  # 避免被0整除
        if smallIsBetter:
            minscore = min(scores.values())
            return dict([(u, float(minscore) / max(vsmall, l)) for (u, l) \
                         in scores.items()])
        else:
            maxscore = max(scores.values())
            if (maxscore - 0) < 1e-4:
                maxscore = vsmall

            return dict([(u, float(c) / maxscore) for (u, c) in scores.items()])

    # 单词频度 Word Frequency
    # rows 查询到的相关网页集合 (urlid,w0.location,w1.location,w2.location)
    def frequencyscore(self, rows):
        counts = dict([(row[0], 0) for row in rows])
        for row in rows:
            counts[row[0]] += 1

        return self.normalizescore(counts)

    # 文档位置
    def locationscore(self, rows):
        locations = dict([(row[0], 1000000) for row in rows])
        for row in rows:
            loc = sum(row[1:])
            if loc < locations[row[0]]: locations[row[0]] = loc

        return self.normalizescore(locations, smallIsBetter=1)

    # 单词距离
    def distancescore(self, rows):

        # 如果仅有一个单词，则得分都一样
        if len(rows[0]) <= 2: return dict([(row[0], 1.0) for row in rows])

        # 初始化字典
        mindistance = dict([(row[0], 100000) for row in rows])

        for row in rows:
            dist = sum(abs(row[i] - row[i - 1]) for i in range(2, len(row)))
            if dist < mindistance[row[0]]: mindistance[row[0]] = dist
        return self.normalizescore(mindistance, smallIsBetter=1)

    # 简单计数
    def inboundlinkscore(self, rows):
        uniqueurls = set([row[0] for row in rows])
        inboundcount = dict([(u, self.con.execute(
            'select count(*) from link where toid=%d' % u).fetchone()[0]
                              ) for u in uniqueurls])

        return self.normalizescore(inboundcount)

    # 简易PageRank
    def calculatepagerank(self, iterations=20):
        # 清除当前的 PageRank 表
        self.con.execute('drop table if exists pagerank')
        self.con.execute('create table pagerank(urlid primary key,score)')

        # 初始化每个url，令其PageRank值为1
        self.con.execute('insert into pagerank select rowid, 1.0 from urllist')
        self.dbcommit()

        for i in range(iterations):
            print ("Iterations %d" % i)

            for (urlid,) in self.con.execute('select rowid from urllist'):

                # 设置PageRank最小值
                pr = 0.15

                # 循环遍历指向当前网页的所有其他网页
                for (linker,) in self.con.execute('select distinct fromid  from link where toid=%d' % urlid):
                    # 得到链接源对应网页的 PageRank值
                    linkingpr = self.con.execute(
                        "select score from pagerank where urlid=%d" % linker).fetchone()[0]

                    # 根据链接源，求得总的链接数
                    linkingcount = self.con.execute(
                        "select count(*) from link where fromid=%d" % linker).fetchone()[0]

                    pr += 0.85 * (linkingpr / linkingcount)

                # 更新 PageRank值
                self.con.execute(
                    "update pagerank set score=%f where urlid=%d" % (pr, urlid))

            # 每轮迭代结束commit一次
            self.dbcommit()

    def linktextscore(self, rows, wordids):
        linkscores = dict([(row[0], 0) for row in rows])
        for wordid in wordids:
            cur = self.con.execute('select link.fromid,link.toid from\
             linkwords,link where wordid =%d and linkwords.linkid=link.rowid\
             ' % wordid)

            for (fromid, toid) in cur:
                if toid in linkscores:
                    pr = self.con.execute('select score from pagerank where urlid\
                        =%d' % fromid).fetchone()[0]
                    linkscores[toid] += pr

        maxscore = max(linkscores.values())
        normalizescores = dict([(u, float(l) / maxscore) for (u, l) in linkscores.items()])
        return normalizescores

if __name__ == '__main__':

    # pagelist = ['http://movie.douban.com/top250']
    # crawler = Crawler('Test2.db')
    # crawler.createindextables()
    # crawler.crawl(pagelist)

    starttime = datetime.datetime.now()

    # long running
    searcher = Searcher('depth3.db')
    searcher.query("教父是肖申克的救赎")

    endtime = datetime.datetime.now()

    print (endtime - starttime).microseconds/1000.0, 'ms'
    print (endtime - starttime).seconds, 's'

