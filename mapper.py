# -*- coding:UTF-8 -*-
# @Time:2022/8/16 16:05
# @FIle:mapper.py
# @Author:duoduozhifu
import contextlib
import os
import queue
import requests
import sys
import threading
import time

FILTERED = ['.jpg', '.gif', '.png', '.css']
TARGET = "http://127.0.0.1/wordpress/"
THREADS = 10

answers = queue.Queue()
web_paths = queue.Queue()

def gather_paths():
    # os.walk() 输出目录及其中的文件名；root表示当前目录、dirs表示目录名字、files表示文件名字
    for root, _, files in os.walk('.'):
        for fname in files:
            # os.path.splitext(fname) 分割路径，返回路径名和文件扩展名的元组
            if os.path.splitext(fname)[1] in FILTERED:
                continue
            # os.path.join() 把目录和文件名合成一个路径
            path = os.path.join(root, fname)
            # path.startswith(str, beg=0,end=len(string))检查是否包含指定字符串
            if path.startswith('.'):
                path = path[1:]
            print(path)
            # 往队列中添加元素
            web_paths.put(path)

# 目的在于将此解释器函数转换为简单的上下文管理器
@contextlib.contextmanager
def chdir(path):
    """
    On enter,change directory to specified path.
    On exit,change directory back to original.
    :param path:
    :return:
    """
    # os.getcwd() 用于返回当前工作目录
    this_dir = os.getcwd()
    # os.chdir() 用于改变当前目录
    os.chdir(path)
    try:
        # chdir的生成器函数在初始化上下文时候，会把当前目录保存下来并跳转到新的目录，将控制权交给gather_paeths()
        yield
    finally:
        os.chdir(this_dir)


def test_remote():
    while not  web_paths.empty():
        path = web_paths.get()
        url = f'{TARGET}{path}'
        time.sleep(2)
        r = requests.get(url)
        if r.status_code == 200:
            answers.put(url)
            sys.stdout.write('+')
        else:
            sys.stdout.write('x')
        sys.stdout.flush()

def run():
    mythreads = list()
    for i in range(THREADS):
        print(f'spawning thread {i}')
        t = threading.Thread(target=test_remote)
        mythreads.append(t)
        t.start()

    for thread in mythreads:
        # 目的在于等待子线程完毕
        thread.join()

if __name__ == '__main__':
    with chdir("D:\pythonProject1\wordpress-5.4"):
        gather_paths()
    input('Press return to continue.')

    run()
    with open('myanswers.txt', 'w') as f:
        while not answers.empty():
            f.write(f'{answers.get()}\n')
        print('done')
