#!/usr/bin/env python3

from multiprocessing import Process
import os
import time

def info(title):
    print('Title is ', title)
    print('*** module name:', __name__)
    print('*** parent process:', os.getppid())
    print('*** process id:', os.getpid())

def f(name):
    info('function f')
    print('hello', name)
    time.sleep(10)
    print('child: returning')

if __name__ == '__main__':
    info('main line')
    p = Process(target=f, args=('bob',))
    p.start()
    info('second occurance')
