# -*- coding:utf-8 -*-

# http://drops.wooyun.org/tips/823
# http://www.36dsj.com/archives/25819?utm_source=tuicool&utm_medium=referral
# Bloom Filter
# 数学之美系列二十一 － 布隆过滤器（Bloom Filter）
# http://www.cnblogs.com/KevinYang/archive/2009/02/01/1381803.html
# BloomFilter（布隆过滤器）
# http://blog.csdn.net/zhaoyl03/article/details/8653391
# 如何用布隆过滤器过滤重复url，求Python代码实现
# http://www.v2ex.com/t/71719

# !/usr/bin/python
# -*- coding: utf-8 -*-


from bs4 import BeautifulSoup
from urlparse import *
import urllib2
import re
import sys

reload(sys)
sys.setdefaultencoding('utf8')


def mytest():
    page = 'http://movie.douban.com/top250'
    c = urllib2.urlopen(page)
    # print c.read()
    soup = BeautifulSoup(c.read())

    links = soup('a')

    for link in links:
        # print link.text
        # if link.text=='': print "I'm null!"
        # print '内容',link
        if 'href' in dict(link.attrs):
            url = urljoin(page, link['href'])
            print url


def mytest2():
    page = 'http://movie.douban.com/top250'
    c = urllib2.urlopen(page)
    # print c.read()
    soup = BeautifulSoup(c.read())

    text = gettextonly(soup)
    text = drytext(text)
    print text

# 重构
def mytest3():

    # page = 'http://movie.douban.com/top250'
    page = 'http://movie.douban.com/subject/1292052/'
    c = urllib2.urlopen(page)
    html = c.read()
    soup = BeautifulSoup(html)

    content = gettextonly2(soup)
    print content




def drytext(text):
    text = text.strip()
    text = ' '.join(text.split())
    return text


def gettextonly(soup):
    v = soup.string
    if v == None:
        c = soup.contents
        resultText = ''
        for t in c:
            subText = gettextonly(t)
            resultText += subText + '\n'
        return resultText
    else:
        return v.strip()


def gettextonly2(soup):
    # 清理script标签
    [script.extract() for script in soup.findAll('script')]
    [style.extract() for style in soup.findAll('style')]

    reg = re.compile("<[^>]*>")
    content = reg.sub('', soup.prettify()).strip()
    content = " ".join(content.split())

    return content



class Graph(object):
    def __init__(self, *args, **kwargs):
        self.node_neighbors = {}
        self.visited = {}

    def add_nodes(self, nodelist):

        for node in nodelist:
            self.add_node(node)

    def add_node(self, node):
        if not node in self.nodes():
            self.node_neighbors[node] = []

    def add_edge(self, edge):
        u, v = edge
        if (v not in self.node_neighbors[u]) and (u not in self.node_neighbors[v]):
            self.node_neighbors[u].append(v)

            if (u != v):
                self.node_neighbors[v].append(u)

    def nodes(self):
        return self.node_neighbors.keys()

    def depth_first_search(self, root=None):
        order = []

        def dfs(node):
            self.visited[node] = True
            order.append(node)
            for n in self.node_neighbors[node]:
                if not n in self.visited:
                    dfs(n)

        if root:
            dfs(root)

        for node in self.nodes():
            if not node in self.visited:
                dfs(node)

        print order
        return order

    def breadth_first_search(self, root=None):
        queue = []
        order = []

        def bfs():
            while len(queue) > 0:
                node = queue.pop(0)

                self.visited[node] = True
                for n in self.node_neighbors[node]:
                    if (not n in self.visited) and (not n in queue):
                        queue.append(n)
                        order.append(n)

        if root:
            queue.append(root)
            order.append(root)
            bfs()

        for node in self.nodes():
            if not node in self.visited:
                queue.append(node)
                order.append(node)
                bfs()
        print order

        return order


def TestGraph():
    g = Graph()
    g.add_nodes([i + 1 for i in range(8)])
    g.add_edge((1, 2))
    g.add_edge((1, 3))
    g.add_edge((2, 4))
    g.add_edge((2, 5))
    g.add_edge((4, 8))
    g.add_edge((5, 8))
    g.add_edge((3, 6))
    g.add_edge((3, 7))
    g.add_edge((6, 7))
    print "nodes:", g.nodes()

    order = g.breadth_first_search(1)
    order = g.depth_first_search(1)


