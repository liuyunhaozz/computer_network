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
    
    def _accept(self, sock):
        """回调函数，针对每个连接的客户端生成一个socket，并将其加入clients中便于广播消息"""
        conn, addr = sock.accept()
        # print(addr)
        self.clients.append(conn)
        print('accepted', conn, 'from', addr)
        conn.setblocking(False)
        self._loop.selector.register(conn, selectors.EVENT_READ, self._on_read)
    
    def _on_read(self, conn):
        """回调函数，读取客户端发送的数据"""
        client_addr, client_port = conn.getpeername()
        msg = conn.recv(1024)
        if msg:
            # print('echoing', repr(msg), 'to', conn)
            # 为客户端发来的信息加上客户端的IP和端口号，便于分辨不同用户
            msg = f'{client_addr}/{client_port}: '.encode('utf8') + msg
            print(msg.decode('utf8'))
            # 收到信息后，将每个客户端的事件修改为写事件，即把一个消息对所有客户端广播
            for each_conn in self.clients:
                self._loop.selector.modify(each_conn, selectors.EVENT_WRITE, (self._on_write, msg))
        else:
            print('closing', conn)
            self._loop.selector.unregister(conn)
            conn.close()

    def _on_write(self, conn, msg):
        """回调函数，向客户端发送数据"""
        conn.sendall(msg)
        self._loop.selector.modify(conn, selectors.EVENT_READ, self._on_read)


event_loop = EventLoop()
# '0.0.0.0'表示可以接受任何IP建立TCP连接
echo_server = TCPChatServer('0.0.0.0', 8888, event_loop)
echo_server.run()
