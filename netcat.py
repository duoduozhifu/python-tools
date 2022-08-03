# -*- coding: utf-8 -*-
# @Time : 20220803
# @Author 山丘
# @File netcat.py

import argparse
import socket
import shlex
# 模块允许我们启动一个新进程，并连接到它们的输入/输出/错误管道，从而获取返回值。
import subprocess
import sys
import textwrap
import threading

# execute()括号内的信息是指出其为完成任务需要什么样的信息，让函数接受你给cmd指定的任何值


def execute(cmd):
    # strip删除开头和结尾的空格
    cmd = cmd.strip()
    if not cmd:
        return
    # subprocess.check_output() 作用是在本机执行一条命令，然后返回该命令输出
    # shlex.split(cmd)使得cmd命令能够按照shell语法拆分，stderr=subprocess.STDOUT使得错误信息作为标准输出到控制台
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    # check_output的返回值的类型是bytes， 如果想用str， 可以使用decode方法进行解码
    return output.decode()

# 客户端代码
# 创建NetCat对象


class NetCat:
    # 初始化，为NetCat对象添加了两个属性args,buffer
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        # 创建一个socket对象
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # setsockopt(level, optname, value)；SO_REUSEADDR，打开或关闭地址复用功能
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # NetCat对象的执行入口
    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)
        try:
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                if response:
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
        # ctrl+c可以退出循环
        except KeyboardInterrupt:
            print('User terminated')
            self.socket.close()
            sys.exit()

    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()

    def handle(self, client_socket):
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break

            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())

        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'hill: #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()

# 解析命令行和调用其他函数
# __name__ == '__main__'确保只有单独运行该模块时，此表达式才成立

if __name__ == '__main__':
    # 首先创建一个解析对象
    parser = argparse.ArgumentParser(
        # desciption表示在参数帮助文档之后显示的文本
        description='bluese net tool',
        # formatter_class入参来控制所输出的帮助格式。比如，通过指定 formatter_class=argparse.RawTextHelpFormatter，我们可以让输出帮助内容遵循原始格式：
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # epilog表示在参数帮助文档之后显示的文本，textwrap.dedent使得删除任何常见的前导空格，左边对齐
        epilog=textwrap.dedent('''Example:
            netcat.py -t 192.168.153.155 -p 5555 -l -c                     #command shell
            netcat.py -t 192.168.153.155 -p 5555 -l -u=mytest.txt          #upload to file
            netcat.py -t 192.168.153.155 -p 5555 -l -e=\"cat /etc/passwd\"  #execute command
            echo 'ABC' | ./netcat.py -t 192.168.153.155 -p 135             #executr command
            netcat.py -t 192.168.153.155 -p 5555 #connext to server 
            ''')
    )
    # 然后向解析对象中添加需要的参数和选项，action='store_true'：有传参，就改为true
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int, default='5555', help='specified port')
    parser.add_argument('-t', '--target', default='192.168.153.155', help='specified ip')
    parser.add_argument('-u', '--upload', help='upload file')
    # 接着使用parse_args()方法解析上边添加的参数
    args = parser.parse_args()
    # 因为有可能是接收端、也有可能是客户端，需要判断是监听还是执行命令
    if args.listen:
        buffer = ''
    else:
        # 默认输入字符串，其他类型强制转换
        buffer = sys.stdin.read()
    # 传给NetCat对象

    nc = NetCat(args, buffer.encode())
    nc.run()
