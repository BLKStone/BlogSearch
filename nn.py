# -*- coding:utf-8 -*-
from math import tanh
from pysqlite2 import dbapi2 as sqlite


class Searchnet:

    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def maketables(self):
        self.con.execute('create table hiddennode(create_key)')
        self.con.execute('create table wordhidden(fromid,toid,strength)')
        self.con.execute('create table hiddenurl(fromid,toid,strength)')
        self.con.commit()

    # 获取权重
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

    # 设置权重
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


if __name__ == '__main__':
    starttime = datetime.datetime.now()

    # long running
    searchnet = Searchnet('nn.db')
    maketables()
    wWorld, wRiver, wBank = 101, 102, 103
    uWorldBank, uRiver, uEarth = 201, 202, 203

    endtime = datetime.datetime.now()

    print (endtime - starttime).microseconds / 1000.0, 'ms'
    print (endtime - starttime).seconds, 's'
