"""
客户端，采用多线程IO, 带有图形界面
"""

import socket
import tkinter
import threading
import time


class Mythread(threading.Thread):
    """子线程，用于从服务器中读取数据并在图形界面进行显示"""
    def __init__(self, func):
        threading.Thread.__init__(self, daemon=True)
        self.running = True
        self.func = func

    def stop(self):
        self.running = False
    
    def run(self):
        while self.running:
            self.func()



class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.s = socket.socket()

        # 创建图形化界面窗口
        self.root = tkinter.Tk()
        # 为窗口设置标题
        self.root.title('聊天室')

        # 创建面板
        # 看消息的面板
        self.message_frame = tkinter.Frame(width=480, height=300, bg='white')
        # 输入消息的面板
        self.text_frame = tkinter.Frame(width=480, height=100)
        # 发送消息的面板
        self.send_frame = tkinter.Frame(width=480, height=30)

        # 创建文本和按钮区域
        self.text_message = tkinter.Text(self.message_frame)
        self.text_text = tkinter.Text(self.text_frame)
        self.button_send = tkinter.Button(self.send_frame, text='发送', command=lambda :self.send_msg(self.s))

    def send_msg(self, conn):
        """在文本框输入信息，在向服务器端发送后清除信息"""
        msg = self.text_text.get('0.0', tkinter.END)
        conn.send(msg.encode('utf8'))
        self.text_text.delete('0.0', tkinter.END)
    
    def get_msg(self, conn):
        """接受来自服务器端的信息吧，并在显示框中更新"""
        while True:
            try:
                msg = conn.recv(1024).decode('utf8')
                if msg == 'shutdown':
                    self.thread.stop()
                    self.root.destroy()
                else:
                    self.text_message.insert(tkinter.END, msg)
            except:
                break

    def setWindow(self):
        """设置tkinter窗口"""

        # 容器位置摆放
        self.message_frame.grid(row=0, column=0, padx=3, pady=6)
        self.text_frame.grid(row=1, column=0, padx=3, pady=6)
        self.send_frame.grid(row=2, column=0)

        # 固定容器大小
        self.message_frame.grid_propagate(0)
        self.text_frame.grid_propagate(0)
        self.send_frame.grid_propagate(0)

        # 将文本和按钮添加到容器中
        self.text_message.grid()
        self.text_text.grid()
        self.button_send.grid()

    def run(self):
        """启动两个线程，一个线程进行调用button发送数据给服务器操作，一个线程进行从服务器中读取数据并显示的操作"""
        self.s.connect((self.host, self.port))
        name, port = self.s.getsockname()
        self.root.title(f'聊天室--用户{name}/{port}')
        self.setWindow()
        self.thread = Mythread(lambda :self.get_msg(self.s))
        self.thread.start()
        self.root.mainloop()

        


# 连接一台我的腾讯云服务器，输入公网IP地址和端口号
client = ChatClient('110.42.156.205', 8888)
client.run()

    