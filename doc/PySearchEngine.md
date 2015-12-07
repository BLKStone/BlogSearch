title: 一个简易搜索引擎(Python)
categories: Python
tags:
  - 信息检索
  - 爬虫
  - python
description: PySearchEngine的代码梳理，算是参考文档
date: 2015-12-06 20:02:42
---


> 本文代码参考 《集体智慧编程》第四章 搜索与排名


# 总体架构

![Alt text](http://7xke9x.com1.z0.glb.clouddn.com/2015-12/Architecture.png)

# Crawler爬虫模块

## 类设计

```
# 初始化Crawler的类并传入数据库名称
def __init__(self, dbname):
    self.con = sqlite.connect(dbname)
    self.visited = BloomFilter(capacity=1000000, error_rate=0.001)

def __del__(self):
    self.con.close()

def dbcommit(self):
    self.con.commit()
```

## 控制流程

爬虫模块基本抓取方式按一下流程图工作，其工作原理近似于针对图遍历的广度优先搜索（Breadth First Search, BFS）。将所有要查询的页面放在一个pagelist(类型为list)中，在循环深度小于depth的情况下，如果此时pagelist中还有，从list中取出一个页面的url，对该页面进行解析和建立索引，之后将该页面中的所有超链接加入到newpage(类型为set,可以帮助去重)。在本轮pagelist遍历完成后，用newpage替代pagelist。



流程图
![Alt text](http://7xke9x.com1.z0.glb.clouddn.com/2015-12/flowchart.png)



代码如下所示

```
def crawl(self, pages, depth=3):
    for i in range(depth):
        newpages = set()
        for page in pages:
            try:
                c = urllib2.urlopen(page)
            except:
                print "Could not open %s" % page
                continue

            html = c.read()
            soup = BeautifulSoup(html)

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
```

## 页面抽取

该部分的主要工作是，获取HTML并解析，之后在数据库建立索引。

页面内容获取主要使用urllib2，发出HTTP请求，从服务器获取相应的HTML。
```
try:
    c = urllib2.urlopen(page)
except:
    print "Could not open %s" % page
    continue
html = c.read()
```

再用BeautifulSoup 4解析HTML。
```
soup = BeautifulSoup(html)
```

在数据库中建立索引，其中的细节下一阶段再详述。
```
self.addtoindex(page, soup)
```

为了过滤重复的URL，这里引入了布隆过滤器，所有访问过的url都会加入布隆过滤器中。
```
self.visited.add(page) 
```

页面抽取过程中,需要将HTML转换成纯文本，HTML中的< script >标签中的JavaScript和< style >定义的CSS样式表是没必要在建立索引时考虑的。另外过多的空格也会引起分词模块的误判,因此引入gettextonly函数进行预处理。

```
def gettextonly(soup):

    # 清理script标签和style标签之间的内容
    [script.extract() for script in soup.findAll('script')]
    [style.extract() for style in soup.findAll('style')]
    
    # 清理标签('<'与'>'之间包裹的所有内容)
    reg = re.compile("<[^>]*>")
    content = reg.sub('', soup.prettify()).strip()
    
    # 清除过多空格 若干个空格=>一个空格
    content = " ".join(content.split())

    return content
```

## 建立索引

在讨论索引建立之前，先说明一下数据库设计，如下图所示。

![Alt text](http://7xke9x.com1.z0.glb.clouddn.com/2015-12/SearchindexDB.png)

建立数据库的语句

```
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
```

建立索引的过程就是在数据库的urllist表中加入url记录，在wordlist表中加入word记录，以及在wordlocation中加入新的记录，这样我们就记住了某个单词在某个页面的某个位置的信息，用于Searcher模块的查询。

这个部分最重要的逻辑就是执行一下语句
```
insert into wordlocation(urlid,wordid,location) values (1,4,0)
insert into wordlocation(urlid,wordid,location) values (1,8,1)
insert into wordlocation(urlid,wordid,location) values (1,15,2)
....
insert into wordlocation(urlid,wordid,location) values (1,1124,503)
```

代码
```
# 为每个网页建立索引
def addtoindex(self, url, soup):

    if self.isindexed(url):
        return
        
    print 'Indexing %s' % url

    # 获取经过预处理的HTML文本
    text = self.gettextonly(soup)
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
```

上文的getentryid的逻辑是，如果表中有该记录则返回该记录的id，如果没有该记录，则在表中插入一条记录，并返回插入的记录的id。
```
# 辅助函数，用于获取条目的id，并且如果条目不存在，就将其加入数据库中
def getentryid(self, table, field, value, createnew=True):

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
```

中文分词部分使用的是现成的模块叫做[结巴分词](https://github.com/fxsjy/jieba)(Jieba)，具体采用的算法根据文档应该是TF-IDF算法和TextRank算法，当然这部分我并没有深究太多。

```
def separatewords(self, text):
    seg_list = jieba.cut_for_search(text)
    result = []
    for seg in seg_list:
        if seg in ignorewords:
            continue
        else:
            result.append(seg)
    return result
```

关于分词还有一点要说明，在汉语中，“的”、“是”之类的词，最好不要加入到wordlist中，这些词并没有什么实际含义，却会严重影响数据库检索效率。
所以addtoindex

```
ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it', '-', '，', '。', "'", '', u'的', u'是'])

# 将每个单词与该url关联
for i in range(len(words)):
    word = words[i]
    if word in ignorewords:
        continue
    wordid = self.getentryid('wordlist', 'word', word)
    self.con.execute("insert into wordlocation(urlid,wordid,location) \
        values (%d,%d,%d)" % (urlid, wordid, i))
```

## URL过滤

因为我只想抓豆瓣电影Top250的内容，所以对URL进行了过滤。

```
if url[0:4] == 'http' and not self.isindexedbloom(url):
                        if self.urlfilter(url):
                            newpages.add(url)
                            linktext = self.drytext(link.text)
                            self.addlinkref(page, url, linktext)
```

判断url是否曾经加入过布隆过滤器
```
def isindexedbloom(self, url):
    return url in self.visited
```

利用正则表达式过滤URL地址
```
def urlfilter(self, url):
    matcher_1 = re.compile(r'http://movie.douban.com/top250\?start=\d+.*')
    matcher_2 = re.compile(r'^http://movie.douban.com/subject/\d+/$')

    if (matcher_1.match(url) is not None or
                matcher_2.match(url) is not None):
        return True
    return False
```

这里还补充了一部分建立索引的过程。在link表中，我们描述了页面之间相互指向的关系。另外，超链接的说明文字通常也有很高的参考价值，所以我们要把它存到linkword表中。

关键SQL
```
insert into link (fromid,toid) values(1,2)
insert into link (fromid,toid) values(1,3)
......
insert into link (fromid,toid) values(1,17)


insert into linkword (wordid,linkid) values (32,1)
insert into linkword (wordid,linkid) values (413,1)
......
insert into linkword (wordid,linkid) values (86,1)

```

代码
```
# 添加一个关联两个网页的链接,记录描述超链接的关键词
def addlinkref(self, urlFrom, urlTo, linkText):

    fromid = self.getentryid('urllist', 'url', urlFrom)
    toid = self.getentryid('urllist', 'url', urlTo)

    cur = self.con.execute("insert into link\
        (fromid,toid) values (%d,%d)" % (fromid, toid))

    linkid = cur.lastrowid

    # 如果超链接的描述text为空的话就不添加记录
    # 若不为空，先分词，再向linkword表添加记录
    if linkText != '':
        # 拆分单词
        words = self.separatewords(linkText)

        for word in words:
            wordid = self.getentryid('wordlist', 'word', word)
            self.con.execute("insert into linkwords\
                (wordid,linkid) values (%d,%d)" % (wordid, linkid))
    return
```

## 运行

```
import PySearchEngine
crawler = PySearchEngine.Crawler('searchindex.db')
crawler.createindextables()
pages = ['http://movie.douban.com/top250']
crawler.crawl(pages)
```

# Searcher搜索模块

## 类设计

```
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
```

## 查询相关URL

将输入的查询分词，构造查询SQL语句，返回结果。
如果单词不在wordlist中则忽略该单词。

构造的SQL如下，假设查询可分为5个有效单词
```
select w0.urlid,w0.location,w1.location,w2.location,w3.location,w4.location 
from wordlocation w0,wordlocation w1,wordlocation w2,wordlocation w3,wordlocation w4 
where w0.wordid=609 and w0.urlid=w1.urlid 
and w1.wordid=331 and w1.urlid=w2.urlid 
and w2.wordid=144 and w2.urlid=w3.urlid 
and w3.wordid=67 and w3.urlid=w4.urlid
and w4.wordid=145
```

代码
```
def getmatchrows(self, q):

    # 构造查询的字符串的基本元素
    fieldlist = 'w0.urlid'
    tablelist = ''
    clauselist = ''
    wordids = []

    # 拆分查询query单词
    words = self.separatewords(q)

    # 删除停词
    for word in words:
        if word in ignorewords:
            words.remove(word)
    
    # 统计是几张表联合查询
    tablenumber = 0
    
    for word in words:
        # 获取单词的ID，如果单词不在wordlist中则忽略
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
    cur = self.con.execute(fullquery)
    rows = [row for row in cur]
    return rows, wordids
```

## 查询接口

查询到的相关网页集合，其形式为`(urlid,w0.location,w1.location,w2.location)`
```
def query(self, q):

    # rows 查询到的相关网页集合 
    rows, wordids = self.getmatchrows(q)

    # 计算url总分
    scores = self.getscorelist(rows, wordids)
    # 排序展示
    rankedscores = sorted([(score, url) for (url, score) in scores.items()], reverse=1)
    for i, (score, urlid) in enumerate(rankedscores[0:10]):
        print '%d %f\t%s' % (i, score, self.geturlname(urlid))
```


## 多指标排序

到目前为止，我们已经成功获得了与查询条件相匹配的网页。不过，其返回结果的排列顺序却很简单，即其被检索时的顺序。而面对大量的网页，我们该如何判断哪些URL对用户价值比较高，哪些URL对用户价值比较低呢（也就是给URL排序的问题）

这里我们综合考虑三种情况：
* 基于内容排名
* 利用外部回指链接
* 跟踪点击的人工神经网络

当然这三种情况还可以进一步细分，详细的指标之后详述。

```
def getscorelist(self, rows, wordids):
    totalscores = dict([(row[0], 0) for row in rows])

    # 各类评价函数
    weights = [(1.0, self.frequencyscore(rows)),
               (1.0, self.locationscore(rows)),
               (1.0, self.distancescore(rows)),
               (1.0, self.inboundlinkscore(rows)),
               (1.0, self.linktextscore(rows, wordids)),
               (1.0, self.nnscore(rows,wordids))]
    
    # 加权计算总分
    for (weight, scores) in weights:
        for url in totalscores:
            totalscores[url] += weight * scores[url]

    return totalscores
```

## 归一化函数

在详细说明各种评价指标之前，先说明一个公用的辅助函数――归一化函数。这个函数的功能是接收一个包含urlid和评价分数score的字典，并返回一个带有相同urlid，而评价分数score介于0和1之间的新字典。

```
# 归一化函数
def normalizescore(self, scores, smallIsBetter = 0):
    vsmall = 0.0001  # 避免被0整除
    if smallIsBetter:
        minscore = min(scores.values())
        return dict([(u, float(minscore) / max(vsmall, l)) for (u, l) \
                     in scores.items()])
    else:
        maxscore = max(scores.values())
        if abs(maxscore - 0) < 1e-4:
            maxscore = vsmall

        return dict([(u, float(c) / maxscore) for (u, c) in scores.items()])
```


## 基于内容的排名

###单词频度

单词频度的基本思想是：位于查询条件中的单词在文档中出现的次数能有助于我们判断文档的相关程度。**位于查询条件中的单词在文档中出现的次数越多，这篇文档的价值越高.**

```
# 单词频度 Word Frequency
# rows 查询到的相关网页集合 (urlid,w0.location,w1.location,w2.location)
# counts 记录的是
# w0 出现的词频 + w1 出现的词频 + .... wN 出现的词频
def frequencyscore(self, rows):
    counts = dict([(row[0], 0) for row in rows])
    for row in rows:
        counts[row[0]] += 1

    return self.normalizescore(counts)

```

###文档位置

文档位置的基本思想是：位于查询条件中的单词在文档中出现在靠近文档开始处的时候，它很有可能是文档的主题。

```
# 文档位置
# 记录所有关键词的位置索引的和loc
# loc越小认为相关性越强
def locationscore(self, rows):
    locations = dict([(row[0], 10000000) for row in rows])
    for row in rows:
        loc = sum(row[1:])
        if loc < locations[row[0]]: locations[row[0]] = loc

    return self.normalizescore(locations, smallIsBetter=1)
```

###单词距离

单词距离的基本思想是：如果查询条件中有多个单词，则它们在文档中出现的位置越近越好。

```
# 单词距离
# 词与词之间的位置差的绝对值的和
# 越小越好
def distancescore(self, rows):

    # 如果仅有一个单词，则得分都一样
    if len(rows[0]) <= 2: return dict([(row[0], 1.0) for row in rows])

    # 初始化字典
    mindistance = dict([(row[0], 10000000) for row in rows])

    for row in rows:
        dist = sum(abs(row[i] - row[i - 1]) for i in range(2, len(row)))
        if dist < mindistance[row[0]]: mindistance[row[0]] = dist
    return self.normalizescore(mindistance, smallIsBetter=1)
```

## 利用外部回指链接

### 简单计数

处理外部回指链接最为简单的做法，是在每个网页上统计链接的数目，并将链接总数作为针对网页的度量。科研论文的评价就经常采用这样的方式，人们将论文的重要程度与其他论文对该论文的引用次数联系了起来。

```
# 简单统计指向该页面的连接数
def inboundlinkscore(self, rows):
    uniqueurls = set([row[0] for row in rows])
    inboundcount = dict([(u, self.con.execute(
        'select count(*) from link where toid=%d' % u).fetchone()[0]
                          ) for u in uniqueurls])

    return self.normalizescore(inboundcount)
```

### PageRank

理论上，PageRank计算的是某个人在任意次链接点击后到达某一网页的可能性。如果某个网页拥有来自其他热门网页的外部回指链接越多，人们无意间到达该网页的可能性就会越大。当然，如果用户始终不停地点击，那么他们最终将到达每一个网页，但大多数人在浏览一段时间之后都会停止了点击。为了反映这一情况，PageRank还使用了一个值为0.85的**阻尼因子**，用以指示用户持续点击每个网页中链接的概率为85%。

```
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
```

### 利用链接文本

另一种对搜索结果进行排名的非常有效的方法，是根据指向某一网页的链接文本来决定网页的相关程度。大多数时候，相比与被链接的网页自身所提供的信息而言，我们从指向该网页的链接中(就是标签< a > 和 < /a > 之间包裹的内容)所得到的信息会更有价值。

```
# 从链接文本中抽取有效信息
def linktextscore(self, rows, wordids):

    linkscores = dict([(row[0], 0) for row in rows])
    for wordid in wordids:
        cur = self.con.execute('select link.fromid,link.toid from\
         linkwords,link where wordid=%d and linkwords.linkid=link.rowid\
         ' % wordid)

        # 显然有时 cur 可能是 None
        # 如果无匹配的查询结果
        if cur is None:
            return linkscores

        for (fromid, toid) in cur:
            if toid in linkscores:
                pr = self.con.execute('select score from pagerank where urlid\
                    =%d' % fromid).fetchone()[0]
                linkscores[toid] += pr

    return self.normalizescore(linkscores)
```

## 跟踪点击的人工神经网络设计

跟踪点击率的神经网络单独成为一个模块 Searchnet 。

这个模块的效果是，**对于同一个输入查询，用户对某个网页点击次数越多，该网页的得分就会越高**。

如图所示，直接说明一下神经网络(准确的说是用反向传播算法训练的MLP)的设计，输入层是各种单词，隐含层是各种单词的组合，输出层则是对应文档URL，激活函数是反双曲正切变换函数(tanh)。

![Alt text](http://7xke9x.com1.z0.glb.clouddn.com/2015-12/nn.png)

点击跟踪的神经网络设计

### 类设计

```
class Searchnet:

    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

```

###  数据库设计

```
def maketables(self):
    self.con.execute('create table hiddennode(create_key)')
    self.con.execute('create table wordhidden(fromid,toid,strength)')
    self.con.execute('create table hiddenurl(fromid,toid,strength)')
    self.con.commit()
```

### 辅助函数

获取权值
```
def getstrength(self, fromid, toid, layer):
    if layer == 0:
        table = 'wordhidden'
    else:
        table = 'hiddenurl'

    res = self.con.execute('select strength from %s where fromid=%d\
     and toid=%d' % (table, fromid, toid)).fetchone()

    if res == None:
        if layer == 0: return -0.2
        if layer == 1: return 0

    return res[0]
```
设置权值
```
def setstrength(self, fromid, toid, layer, strength):

    if layer == 0:
        table = 'wordhidden'
    else:
        table = 'hiddenurl'

    res = self.con.execute('select rowid from %s where fromid=%d \
        and toid=%d' % (table, fromid, toid)).fetchone()

    if res == None:
        self.con.execute('insert into %s (fromid,toid,strength) \
            values (%d,%d,%f)' % (table, fromid, toid, strength))
    else:
        rowid = res[0]
        self.con.execute('update %s set strength=%f where \
            rowid=%d' % (table, strength, rowid))
```

### 建立新的隐含层节点

此处有一个问题，我们只针对2个单词组合成的词建立了隐含层节点。
```
def generatehiddennode(self, wordids, urls):

    if len(wordids) > 3: return None

    # 检查我们是否已经为这组单词建好了一个节点
    createkey = '_'.join(sorted([str(wi) for wi in wordids]))
    res = self.con.execute("select rowid from hiddennode \
        where create_key='%s'" % createkey).fetchone()

    # 如果没有，则建立之
    if res == None:
        cur = self.con.execute("insert into hiddennode (create_key)\
            values ('%s')" % createkey)
        hiddenid = cur.lastrowid

        # 设置默认权重
        for wordid in wordids:
            self.setstrength(wordid, hiddenid, 0, 1.0 / len(wordids))
        for urlid in urls:
            self.setstrength(hiddenid, urlid, 1, 0.1)
        self.con.commit()
```

### 查询相关隐层节点

在开始执行前馈算法之前，searchnet类的代码必须先从数据库中查询出节点与连接的信息，然后在内存中建立起与某项查询相关的所有节点。

```
# 获取所有与检索结果相关的隐含层id
def getallhiddenids(self, wordids, urlids):
    l1 = {}

    for wordid in wordids:
        cur = self.con.execute('select toid from wordhidden where fromid=%d' %
                                wordid)
        for row in cur:
            l1[row[0]] = 1

    for urlid in urlids:
        cur = self.con.execute('select fromid from hiddenurl where toid=%d' %
                               urlid)

        for row in cur:
            l1[row[0]] = 1

    return l1.keys()
```

### 设置网络初始权值

```
# 建立网络
def setupnetwork(self, wordids, urlids):
    # 值列表
    self.wordids = wordids 
    self.hiddenids = self.getallhiddenids(wordids, urlids)
    self.urlids = urlids

    # 节点输出
    self.ai = [1.0] * len(self.wordids)
    self.ah = [1.0] * len(self.hiddenids)
    self.ao = [1.0] * len(self.urlids)

    # 建立权重矩阵
    self.wi = [[self.getstrength(wordid,hiddenid,0)
                for hiddenid in self.hiddenids]
                for wordid in self.wordids]
    self.wo = [[self.getstrength(hiddenid,urlid,1)
                for urlid in self.urlids]
                for hiddenid in self.hiddenids]
```
### 前向传播

神经网络的计算过程
```
# 前向传播
def feedforward(self):

    # 查询单词是仅有的输入
    for i in range(len(self.wordids)):
        self.ai[i] = 1.0

    # 隐藏层节点的活跃程度
    for j in range(len(self.hiddenids)):
        sum = 0.0
        for i in range(len(self.wordids)):
            sum = sum + self.ai[i] * self.wi[i][j]
        self.ah[j] = tanh(sum)

    # 输出层节点的活跃程度
    for k in range(len(self.urlids)):
        sum = 0.0
        for j in range(len(self.hiddenids)):
            sum = sum + self.ah[j] * self.wo[j][k]
        self.ao[k] = tanh(sum)

    return self.ao[:]
```

输出结果
```
# 计算神经网络输出结果
def getresult(self,wordids,urlids):
    self.setupnetwork(wordids, urlids)
    return self.feedforward()
```

### 反向传播(backpropagate)训练

```
# 反向传播算法
def backpropagate(self, targets, N = 0.5 ):

    # 计算输出层误差
    output_deltas = [0.0] * len(self.urlids)
    for k in range(len(self.urlids)):
        error = targets[k] - self.ao[k]
        output_deltas[k] = dtanh(self.ao[k]) * error

    # 计算隐藏层误差
    hidden_deltas = [0.0] * len(self.hiddenids)
    for j in range(len(self.hiddenids)):
        error = 0
        for k in range(len(self.urlids)):
            error = error + output_deltas[k] * self.wo[j][k]
        hidden_deltas[j] = dtanh(self.ah[j]) * error

    # 更新输出权重
    for j in range(len(self.hiddenids)):
        for k in range(len(self.urlids)):
            change = output_deltas[k] * self.ah[j]
            self.wo[j][k] = self.wo[j][k] + N*change

    # 更新输入权重
    for i in range(len(self.wordids)):
        for j in range(len(self.hiddenids)):
            change = hidden_deltas[j] * self.ai[i]
            self.wi[i][j] = self.wi[i][j] + N*change
```

### 训练接口

```
def trainquery(self, wordids, urlids, selecturl ):

    self.generatehiddennode(wordids, urlids)
    self.setupnetwork(wordids, urlids)
    self.feedforward()

    targets = [0.0] * len(urlids)
    targets[urlids.index(selecturl)]=1
    self.backpropagate(targets)
    self.updatedatabase()
```
数据库操作

```
# 更新数据库
def updatedatabase(self):
    # 将值存入数据库中
    for i in range(len(self.wordids)):
        for j in range(len(self.hiddenids)):
            self.setstrength(self.wordids[i],self.hiddenids[j],0,
                             self.wi[i][j])

    for j in range(len(self.hiddenids)):
        for k in range(len(self.urlids)):
            self.setstrength(self.hiddenids[j],self.urlids[k],1,
                             self.wo[j][k])

    self.con.commit()
```

### 与搜索引擎集成

在query结束处添加
```
return wordids, [r[1] for r in rankedscores[0:10]]
```

在Searchnet 中添加
```
# 神经网络评价指标
def nnscore(self, rows, wordids):
    # 获得一个由唯一的URL ID构成的有序列表
    urlids = [urlid for urlid in set([row[0] for row in rows])]
    nnres = mynet.getresult(wordids, urlids)
    scores = dict([(urlids[i], nnres[i]) for i in range(len(urlids))])
    return self.normalizescore(scores)
```

# 改进与建议

这个项目其实仍然是一个非常粗糙的作品，不过其优势在于麻雀虽小，五脏俱全，详细介绍了各种排序算法的基本思想，让我们能了解建立索引的基本步骤。

不足之处

1. **支持的数据量**。按照原文的说法，这个项目应该能支撑十万量级的查询。不过在我的实验环境下，我只抓了豆瓣电影top250大概 260个页面，并没有测试在大量数据情况下该项目的运行情况。
2.  **神经网络设计**。因为原来该项目是针对英文页面设计的，由于一些语言特性上的不同，换到汉语环境下仍有一些不适应之处。例如在神经网络的**隐含层设计**部分，只考虑了两个单词的组合，并没有考虑更多单词组合的情况。这一部分的设计最重要的是能**让神经网络学习一些词组**，让词组和url关联；还有一个问题则是神经网络的**初始权重和阈值**，应该如何分配，理由是什么。
3.  **ignorewords不完善**。这里只例举了“的”,“是”等最常用的无意义的词，除此以外应该还有很多类似的词。
4. **数据库操作异常处理**。如果遇到某些查不到的情况，或者重复建表的情况应处理异常，以提高程序鲁棒性。
5. **汉语分词的困境**。以“团购网站的本质是什么”这句话为例，汉语分词的结果可能是“团购”，“团购网” ，“网站” ，“团购网站”，“本质”，“是”，“什么”;如果在英语语境下，“what is groupon”，分词的结果是显而易见的，“what”,“is”“groupon”。我们在建立索引的时候会记录每个词在每个页面中的位置，这种分词结果的区别可能会影响位置的记录。
6. **删除停词**的部分可以移到separateword里面。

其他想改进的地方

1.  **Web UI**。现在只能在shell里查询结果，需要添加一个Web UI。
2. **引入ORM**。与数据库的连接部分现在都是直接通过拼接字符串构造SQL，并且现阶段是和SQLite捆绑死的。希望能通过引入ORM机制，可以替换数据库层而不修改上层模块。加入对MySQL和MongoDB的支持。  
3.  **深入了解分词模块**。这里是直接引用现成的项目，有机会的话想更深入地了解分词的算法。
4. **拼写检查**。这里有两个英文语境下的算法可以参考， Edit(Levenstein) Distance 和 LCS(Longest Common Subsequence)。
5. **同义词转换**。
6. **搜索框支持 and、or 和 not语法**。
7. **基于本体的搜索(语义网)**。说到这一块的话，其实整个搜索引擎的设计理念都改变了。似乎有一些现成的学术上的数据集称为WordNet，另外可以参考一下维基百科的**消除歧义**页面的设计思想(比如同样是苹果这个词，在不同语境下有水果，或者某电子产品品牌的含义)。


# 相似项目
Python 全文搜索
https://pypi.python.org/pypi/Flask-PonyWhoosh

# 参考资料
\[1\] 《集体智慧编程》
\[2\]  < Mordern Information Retrieval > - Ricardo Baeza-Yates
\[3\] [Jieba分词](https://github.com/fxsjy/jieba)
\[4\] [有哪些比较好的中文分词方案](http://www.zhihu.com/question/19578687)
