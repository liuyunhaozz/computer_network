"""
服务器端，采用单线程异步IO
"""

import selectors
import socket


class EventLoop:
    """事件循环类，用于异步IO操作"""
    def __init__(self, selector=None):
        if selector is None:
            selector = selectors.DefaultSelector()
        self.selector = selector

    def run_forever(self):
        """主循环，该函数在调用select函数后阻塞，等待读/写socket事件发生后调用相应的回调函数"""
        while True:
            events = self.selector.select()
            # print('timeout, but still run on')
            for key, mask in events:
                if mask == selectors.EVENT_READ:
                    callback = key.data # callback is _on_read or _accept
                    callback(key.fileobj) 
                else:
                    callback, msg = key.data # callback is on_write
                    callback(key.fileobj, msg)


class TCPChatServer:
    """服务器的类，采用TCP协议，异步IO"""
    def __init__(self, host, port, loop):
        self.host = host
        self.port = port
        self._loop = loop
        self.s = socket.socket()
        self.clients = []

    def run(self):
        """类的主要运行函数"""
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 将服务器的host和port绑定到socket上
        self.s.bind((self.host, self.port))
        self.s.listen(128)
        self.s.setblocking(False)
        # 注册
        self._loop.selector.register(self.s, selectors.EVENT_READ, self._accept)
        # 启动事件循环
        self._loop.run_forever()
    
    def get_socket(self, name):
        """在当前连接的客户端中查找给定的name，并返回对应的socket"""
        for client in self.clients:
            if client['name'] == name:
                return client['socket']
        return None
        
    def get_loginmessage(self, client):
        """当一个用户登陆后，给所有用户发送必要的信息"""
        msg1 = f'用户{client["name"]}已上线\n'.encode('utf8')
        msg2 = f'当前在线人数为 {len(self.clients)}\n'.encode('utf8')
        msg3 = f'当前在线人员为\n'
        for client in self.clients:
            msg3 += f"| {client['name']} |\n" 
        msg3 = msg3.encode('utf8')        
        return msg1 + msg2 + msg3

    def _accept(self, sock):
        """回调函数，针对每个连接的客户端生成一个socket，并将其加入clients中便于广播消息"""
        conn, addr = sock.accept()
        # print(addr)
        client_addr, client_port = conn.getpeername()
        client = {}
        client['socket'] = conn
        client['name'] = f'{client_addr}/{client_port}'
        self.clients.append(client)
        print('accepted', conn, 'from', addr)
        conn.setblocking(False)
        msg = self.get_loginmessage(client)
        # print(self.clients)
        for client in self.clients:
            each_conn = client['socket']
            try:
                self._loop.selector.register(each_conn, selectors.EVENT_WRITE, (self._on_write, msg)) 
            except KeyError:
                self._loop.selector.modify(each_conn, selectors.EVENT_WRITE, (self._on_write, msg))
    
    def _on_read(self, conn):
        """回调函数，读取客户端发送的数据"""
        client_addr, client_port = conn.getpeername()
        msg = conn.recv(1024)
        # print(msg)
        if msg != 'exit\n'.encode('utf8'):
            atmsg = msg.decode('utf8').split(' ')
            # 为客户端发来的信息加上客户端的IP和端口号，便于分辨不同用户
            msg = f'{client_addr}/{client_port}: '.encode('utf8') + msg
            
            # 消息有@时，进行两个人之间的消息发送
            if len(atmsg) > 1 and atmsg[0][0] == '@':
                print(msg.decode('utf8'))
                atname = atmsg[0][1:]
                atconn = self.get_socket(atname)
                if atconn:
                    self._loop.selector.modify(conn, selectors.EVENT_WRITE, (self._on_write, msg))
                    self._loop.selector.modify(atconn, selectors.EVENT_WRITE, (self._on_write, msg))
                else:
                    msg = '发送失败，找不到该用户'.encode('utf8')
                    self._loop.selector.modify(conn, selectors.EVENT_WRITE, (self._on_write, msg))
            
            # 消息没有@时，对所有用户发送
            else:
                # print('echoing', repr(msg), 'to', conn)
                print(msg.decode('utf8'))
                # 收到信息后，将每个客户端的事件修改为写事件，即把一个消息对所有客户端广播
                for client in self.clients:
                    each_conn = client['socket']
                    self._loop.selector.modify(each_conn, selectors.EVENT_WRITE, (self._on_write, msg))
        else:
            print('closing', conn)
            conn.sendall('shutdown'.encode('utf8'))
            self._loop.selector.unregister(conn)
            conn.close()

    def _on_write(self, conn, msg):
        """回调函数，向客户端发送数据"""
        conn.sendall(msg) # 该函数为阻塞式
        self._loop.selector.modify(conn, selectors.EVENT_READ, self._on_read)


event_loop = EventLoop()
# '0.0.0.0'表示可以接受任何IP建立TCP连接
echo_server = TCPChatServer('0.0.0.0', 8888, event_loop)
echo_server.run()
