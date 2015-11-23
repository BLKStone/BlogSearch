pagelist = ['http://github.com/BLKStone/']


import PySearchEngineV1
pagelist = ['http://movie.douban.com/top250']
crawler = PySearchEngineV1.crawler('searchindex.db')
#crawler.createindextables()
crawler.crawl(pagelist)

import PySearchEngine
pagelist = ['http://movie.douban.com/top250']
crawler = PySearchEngine.crawler('searchindex.db')
#crawler.createindextables()
crawler.crawl(pagelist)


import PySearchEngine
pagelist = ['http://movie.douban.com/top250']
crawler = PySearchEngine.crawler('searchindex2.db')
crawler.createindextables()
crawler.crawl(pagelist)


# 数据库查询
sqlite3 searchindex.db
.quit
.help
select rowid,word from wordlist where rowid<100;



# 搜索部分debug
import PySearchEngine
reload(PySearchEngine)
e = PySearchEngine.searcher('searchindex.db')
searchtext='东西 集市 小组 阅读'
e.getmatchrows(searchtext)

c = urllib2.urlopen('http://movie.douban.com/top250')

'''
In [10]: pagelist = ['http://github.com/BLKStone/']

In [11]: crawler.crawl(pagelist)
Indexing http://github.com/BLKStone/
Indexing https://status.github.com/
Indexing https://github.com
Indexing https://help.github.com/articles/why-are-my-contributions-not-showing-up-on-my-profile
Indexing https://github.com/pricing
Indexing https://github.com/blog
Indexing http://github.com/iissnan/hexo-theme-next
Indexing https://training.github.com
Indexing http://github.com/explore
Indexing http://github.com/BLKStone/XcodeGhost
Indexing http://github.com/BLKStone/cxlab
Indexing http://github.com/login?return_to=%2FBLKStone
Indexing https://enterprise.github.com/
Indexing http://github.com/BLKStone
Indexing https://developer.github.com
Indexing http://github.com/features
Indexing http://github.com/BLKStone/BLKStone.github.io/commits?author=BLKStone
Indexing https://github.com/site/terms
Indexing http://github.com/stars/BLKStone
Indexing https://shop.github.com
Indexing http://github.com/BLKStone?tab=repositories
Indexing http://github.com/filow/cxlab
Indexing http://github.com/pricing
Indexing https://github.com/
Indexing http://github.com/BLKStone/EasyPyPR
Indexing http://github.com/fan-wenjie/EasyPR-Java
Indexing https://github.com/about
Indexing http://github.com/BLKStone/followers
Indexing https://github.com/security
Indexing http://github.com/BLKStone/cos
Indexing http://github.com/BLKStone/
Indexing https://avatars2.githubusercontent.com/u/8243595?v=3&s=400
Indexing http://github.com/join
Indexing http://github.com/BLKStone/ChinaAPI
Indexing http://github.com/BLKStone?tab=activity
Indexing http://github.com/BLKStone/following
Indexing https://help.github.com
Indexing https://github.com/site/privacy
Indexing https://github.com/contact

'''


爬行豆瓣
'''
Indexing http://movie.douban.com/top250
Indexing http://help.douban.com/?app=movie
Indexing http://book.douban.com/
Indexing http://movie.douban.com/subject/1292001/
Indexing http://www.douban.com/
Indexing http://www.douban.com/location/
Indexing http://www.douban.com/about
Indexing http://movie.douban.com/subject/1292064/
Indexing http://music.douban.com/
Indexing http://www.douban.com/about?policy=disclaimer
Indexing http://douban.fm/
Indexing http://movie.douban.com/subject/1291841/
Indexing http://www.douban.com/doubanapp/redirect?channel=top-nav&direct_dl=1&download=iOS
Indexing http://movie.douban.com/subject/1300267/
Indexing http://movie.douban.com/review/best/
Indexing http://movie.douban.com/top250?start=75&filter=&type=
Indexing http://movie.douban.com/subject/6786002/
Indexing http://movie.douban.com/subject/2131459/
Indexing http://developers.douban.com/
Indexing http://movie.douban.com/top250?start=50&filter=&type=
Indexing http://www.douban.com/hnypt/variformcyst.py
Indexing http://www.douban.com/doubanapp/
Indexing http://www.douban.com/accounts/login?source=movie
Indexing http://www.douban.com/doubanapp/frodo
Indexing http://movie.douban.com/subject/1291552/
Indexing http://movie.douban.com/subject/3793023/
Indexing http://market.douban.com/
Indexing http://movie.douban.com/subject/1292000/
Indexing http://movie.douban.com
Indexing http://www.douban.com/jobs
Indexing http://movie.douban.com/top250?start=100&filter=&type=
Indexing http://dongxi.douban.com/?dcs=top-nav&dcm=douban
Indexing http://movie.douban.com/subject/1292063/
Indexing http://movie.douban.com/subject/1291546/
Indexing http://movie.douban.com/subject/3541415/
Indexing http://movie.douban.com/top250?start=200&filter=&type=
Indexing http://movie.douban.com/subject/1295124/
Indexing http://movie.douban.com/subject/1295644/
Indexing http://movie.douban.com/nowplaying/
Indexing http://movie.douban.com/subject/1849031/
Indexing http://movie.douban.com/tv/
Indexing http://moment.douban.com
Indexing http://ypy.douban.com
Indexing http://www.douban.com/partner/
Indexing http://movie.douban.com/subject/1292213/
Indexing http://movie.douban.com/subject/1292720/
Indexing http://www.douban.com/accounts/register?source=movie
Indexing http://movie.douban.com/subject/1293839/
Indexing http://movie.douban.com/subject/1291549/
Indexing http://movie.douban.com/trailers
Indexing http://movie.douban.com/top250?start=25&filter=&type=
Indexing http://movie.douban.com/top250?start=150&filter=&type=
Indexing http://movie.douban.com/subject/1292722/
Indexing http://movie.douban.com/
Indexing http://movie.douban.com/tag/
Indexing http://movie.douban.com/top250?start=225&filter=&type=
Indexing http://www.douban.com/group/
Indexing http://movie.douban.com/top250
Indexing http://movie.douban.com/top250?start=175&filter=&type=
Indexing http://read.douban.com/?dcs=top-nav&dcm=douban
Indexing http://www.douban.com/doubanapp/app?channel=top-nav
Indexing http://9.douban.com
Indexing http://movie.douban.com/top250?start=125&filter=&type=
Indexing http://movie.douban.com/explore
Indexing http://movie.douban.com/askmatrix/hot_questions/all
Indexing http://movie.douban.com/subject/1291828/
Indexing http://movie.douban.com/subject/1291560/
Indexing http://movie.douban.com/subject/1292052/
Indexing http://www.douban.com/doubanapp/redirect?channel=top-nav&direct_dl=1&download=Android
Indexing http://movie.douban.com/chart
Indexing http://movie.douban.com/subject/1291561/
Indexing http://movie.douban.com/subject/3011091/
Indexing http://www.douban.com/about?topic=contactus

'''

# 地址过滤器
def urlfilter(url):
    matcher_1 = re.compile(r'http://movie.douban.com/top250\?start=\d+.*')
    matcher_2 = re.compile(r'http://movie.douban.com/subject/\d+')
    if matcher_1.match(url) != None or matcher_2.match(url) != None:
        return True
    return False

urlfilter('http://movie.douban.com/top250?start=175&filter=&type=')
urlfilter('http://movie.douban.com/top250?start=50&filter=&type=')
urlfilter('http://movie.douban.com/subject/3793023/')
urlfilter('http://movie.douban.com/subject/1292000/')
urlfilter('http://www.douban.com/accounts/register?source=movie')
urlfilter('http://movie.douban.com/review/best/')
urlfilter('http://movie.douban.com/askmatrix/hot_questions/all')

