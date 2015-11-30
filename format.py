# -*- coding:utf-8 -*-
import sys  # 模块，sys指向这个模块对象
import inspect
import fnmatch as m
import bs4

def foo():
    pass  # 函数，foo指向这个函数对象


class Cat(object):  # 类，Cat指向这个类对象
    def __init__(self, name='kitty'):
        self.name = name

    def sayHi(self):  # 实例方法，sayHi指向这个方法对象，使用类或实例.sayHi访问
        print self.name, 'says Hi!'  # 访问名为name的字段，使用实例.name访问


cat = Cat()  # cat是Cat类的实例对象

print Cat.sayHi  # 使用类名访问实例方法时，方法是未绑定的(unbound)
print cat.sayHi  # 使用实例访问实例方法时，方法是绑定的(bound)

cat = Cat('kitty')

print cat.name  # 访问实例属性

cat.sayHi()  # 调用实例方法

print dir(cat)  # 获取实例的属性名，以列表形式返回

if hasattr(cat, 'name'):  # 检查实例是否有这个属性
    setattr(cat, 'name', 'tiger')  # same as: a.name = 'tiger'

print getattr(cat, 'name')  # same as: print a.name
getattr(cat, 'sayHi')()  # same as: cat.sayHi()

print bs4.__file__


# import fnmatch as m
print m.__doc__.splitlines()[0]     # Filename matching with shell patterns.
print m.__name__                    # fnmatch
print m.__file__                    # /usr/lib/python2.6/fnmatch.pyc
print m.__dict__.items()[0]         # ('fnmatchcase', )


class Akcx(object):
    pass

aakcx = Akcx()
print 'test', aakcx.__class__.__bases__


print Cat.__doc__           # None
print Cat.__name__          # Cat
print Cat.__module__        # __main__
print Cat.__bases__         # (,)
print Cat.__dict__          # {'__module__': '__main__', ...}


class Luyou(object):
    def __init__(self):
        self.a = 5
        self.b = 6
        self.f = Fulang()


class Fulang(object):
    def __init__(self):
        self.c = 9

print 'start-----------'

luyou = Luyou()
# print luyou.f.__self__

print 'start=========='


def gen():
    for q in xrange(5):
        yield q

g = gen()

print g                 # <generator object gen at 0x...>
print g.gi_code         # <code object gen at 0x...>
print g.gi_frame        # <frame object at 0x...>
print g.gi_running      # 0
print g.next()          # 0
print g.next()          # 1

for n in g:
    print n,            # 2 3 4

co = cat.sayHi.func_code

print 'next ---'
print co.co_argcount         # 1
print co.co_names            # ('name',)
print co.co_varnames         # ('self',)
print co.co_flags & 0b100    # 0
print co.co_filename


def add(x, y=1):
    f = inspect.currentframe()
    print f.f_locals            # same as locals()
    print f.f_back              # <frame object at 0x...>
    return x + y

add(2)


def div(x, y):
    try:
        return x/y
    except:
        tb = sys.exc_info()[2]   # return (exc_type, exc_value, traceback)
        print tb
        print tb.tb_lineno       # "return x/y" 的行号

div(1, 0)

im = cat.sayHi

if inspect.isroutine(im):
    im()