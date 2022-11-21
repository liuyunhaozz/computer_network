"""
客户端，采用单线程阻塞式IO
"""

import socket


# 1.创建套接字
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 2.准备连接服务器，建立连接
serve_ip = '127.0.0.1'
serve_port = 8000  # 端口，比如8000
tcp_socket.connect((serve_ip,serve_port))  # 连接服务器，建立连接,参数是元组形式

while True:
    # 准备需要传送的数据
    client_msg = input('向服务器发送数据: ')
    tcp_socket.send(client_msg.encode("utf-8"))
    if client_msg == 'exit':
        print('结束通信，向服务器发送终止信号...')
        break
    # 从服务器接收数据
    # 注意这个1024byte，大小根据需求自己设置
    server_msg = tcp_socket.recv(1024).decode('utf-8')
    print('服务器发送的数据:', server_msg)


# 关闭连接
tcp_socket.close()
