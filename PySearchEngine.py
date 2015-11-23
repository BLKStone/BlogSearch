# -*- coding:utf-8 -*-

import urllib2
from BeautifulSoup import *
from urlparse import *
from pysqlite2 import dbapi2 as sqlite
import jieba
import sys 
reload(sys)
sys.setdefaultencoding('utf8') 

ignorewords = set(['the','of','to','and','a','in','is','it','-','，','。',"'",''])
# ignorewords = set(['the','of','to','and','a','in','is','it',])


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

        # print "select rowid from \
        #     %s where %s='%s'" % (table,field,value)
        cur = self.con.execute("select rowid from \
            %s where %s='%s'" % (table,field,value))
        res = cur.fetchone()

        if res == None:
            cur=self.con.execute("insert into %s \
                (%s) values ('%s')" % (table,field,value))
            return cur.lastrowid

        else:
            return res[0]

        return None

    # 为每个网页建立索引
    def addtoindex(self,url,soup):
        if self.isindexed(url): return

        print 'Indexing %s' % url

        # 获取每个单词 
        text = self.gettextonly(soup)
        words = self.separatewords(text)

        # 得到URL的id
        urlid = self.getentryid('urllist','url',url)

        # 将每个单词与该url关联
        for i in range(len(words)):
            word = words[i]
            if word in ignorewords: continue
            wordid = self.getentryid('wordlist','word',word)
            self.con.execute("insert into wordlocation(urlid,wordid,location) \
                values (%d,%d,%d)" % (urlid,wordid,i))


    # 地址过滤器
    def urlfilter(self,url):
        matcher_1 = re.compile(r'http://movie.douban.com/top250\?start=\d+.*')
        matcher_2 = re.compile(r'http://movie.douban.com/subject/\d+')

        if ( matcher_1.match(url) != None or matcher_2.match(url) != None ):
            return True

        return False

    # 从一个HTML页面中提取文字（不带标签的）
    def gettextonly(self,soup):
        v=soup.string
        if v==None:
            c=soup.contents
            resultText=''
            for t in c:
                subText=self.gettextonly(t)
                resultText+=subText+'\n'
            return resultText
        else:
            return v.strip()

    # 根据任何非空白字符进行分词处理
    # 此处需要重写
    # 注意一下此处list中的元素原先是 str
    # 修改后 返回的list中元素变成 unicode 类型
    def separatewords(self,text):
        seg_list = jieba.cut_for_search(text)
        result = []
        for seg in seg_list:
            result.append(seg)
        return result

    # 如果url已经建立过索引，则返回True
    def isindexed(self,url):
        u=self.con.execute("select rowid from urllist \
            where url='%s'" % url).fetchone()

        if u != None:
            # 检查它是否被检索过了
            v=self.con.execute('select * from \
                wordlocation where urlid=%d' % u[0]).fetchone()
            if v != None: return True

        return False

    # 添加一个关联两个网页的链接
    def addlinkref(self,urlFrom,urlTo,linkText):
        pass

    # 从一小组网页开始进行广度优先搜索。直至某一给定深度，
    # 期间为网页建立索引
    def crawl(self,pages,depth=2):
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


class searcher:
    def __init__(self,dbname):
        self.con=sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def getmatchrows(self,q):
        
        # 构造查询的字符串
        fieldlist='w0.urlid'
        tablelist=''
        clauselist=''
        wordids=[]

        # 拆分单词
        seg_list = jieba.cut_for_search(q)
        words = []
        for seg in seg_list:
            words.append(seg)

        # print words
        tablenumber=0


        for word in words:
            
            # 检查语句
            print "select rowid from wordlist where word='%s'" % word

            # 获取单词的ID
            wordrow = self.con.execute(
                "select rowid from wordlist where word='%s'" % word).fetchone()

            if wordrow != None:
                wordid=wordrow[0]
                wordids.append(wordid)

                if tablenumber>0:
                    tablelist+=','
                    clauselist+=' and '
                    clauselist+='w%d.urlid=w%d.urlid and ' % (tablenumber-1,tablenumber)

                fieldlist+=',w%d.location' % tablenumber
                tablelist+='wordlocation w%d' % tablenumber
                clauselist+='w%d.wordid=%d' % (tablenumber,wordid)
                tablenumber+=1

        # 根据各个分组，建立查询    
        fullquery='select %s from %s where %s' % (fieldlist,tablelist,clauselist)
        # debug 用于检查sql语句 
        # print fullquery
        cur = self.con.execute(fullquery)
        rows = [row for row in cur]
        return rows,wordids


    # 获取排序评分
    def getscorelist(self,rows,wordids):
        totalscores = dict([(row[0],0) for row in rows])

        # 此处是稍后放置评价函数的地方
        weights = [(0,self.frequencyscore(rows)),(0,self.locationscore(rows)),
                    (1.0,self.distancescore(rows))]

        for (weight,scores) in weights:
            for url in totalscores:
                totalscores[url]+=weight*scores[url]

        return totalscores

    # 根据 urlid 查询url
    def geturlname(self,id):
        return self.con.execute(
            "select url from urllist where rowid=%d" % id).fetchone()[0]

    # 查询
    def query(self,q):
        rows,wordids = self.getmatchrows(q)
        scores = self.getscorelist(rows,wordids)
        rankedscores = sorted([(score,url) for (url,score) in scores.items()],reverse=1)
        for (score,urlid) in rankedscores[0:10]:
            print '%f\t%s' % (score,self.geturlname(urlid))


    # 归一化函数
    def normalizescore(self,scores,smallIsBetter=0):
        vsmall=0.00001 #避免被0整除
        if smallIsBetter:
            minscore=min(scores.values())
            return dict([(u,float(minscore)/max(vsmall,l)) for (u,l) \
                in scores.items()])
        else:
            maxscore=max(scores.values())
            if (maxscore-0)<1e-4:
                maxscore=vsmall

            return dict([(u,float(c)/maxscore) for (u,c) \
               in scores.items()])

    # 单词频度 Word Frequency
    def frequencyscore(self,rows):
        counts=dict([(row[0],0) for row in rows])
        for row in rows:
            counts[row[0]]+=1

        return self.normalizescore(counts)


    # 文档位置
    def locationscore(self,rows):
        locations=dict([(row[0],1000000) for row in rows])
        for row in rows:
            loc=sum(row[1:])
            if loc < locations[row[0]]: locations[row[0]]=loc

        return self.normalizescore(locations,smallIsBetter=1)

    # 单词距离
    def distancescore(self,rows):

        # 如果仅有一个单词，则得分都一样
        if len(rows[0]) <= 2: return dict([(row[0],1.0) for row in rows])

        # 初始化字典
        mindistance=dict([(row[0],100000) for row in rows])

        for row in rows:
            dist=sum(abs(row[i]-row[i-1]) for i in range(2,len(row)))
            if dist<mindistance[row[0]]: mindistance[row[0]]=dist
        return self.normalizescore(mindistance,smallIsBetter=1)




