import socket
import hashlib
import threading
import time
from tools import *

import os


'''错误重复的信息
    每个路由器会保持一个和controller之间的连接。定时发送在线信息并更新路由表。
    路由器和路由器之间的连接是固定的，但是数据包转发的连接时由路由表决定的。
    简易IP报文格式:(sourceIp,destinationIp,msgsize)msg
    注意Router和Controller之间的信息交换应该是通过广播或者底层协议。（这里使用链路层协议，即直接通信）
    Router与Controller之间（链路层协议）：
    Router:(GET Table itemsize)items
    Controller:(GET OK tabsize)table
    Router会通过路由表选择合适的连接转发数据报。
'''

'''
添加路由表(成员变量)
修改recv函数里的handle, peer上线时, 分配peer与其相连(随机确定链路代价), 修改邻接表，计算任意两点间的最短路径
添加peer路由请求回应方法
修改EXEComm函数，添加路由请求回应
'''

class Controller():

    def __init__(self, port=5555, MaxConnect=100):
        """
            初始化函数，会根据参数建立socket连接。并设置侦听数量，但是要获得连接，使用recv函数
            port=5555:指定端口用于连接
            MaxConnect=100:指定最大连接数 
            resourceMap: dict, (file(str): [(str(ip)...])
            routing_table: dict, (str(ip_src): [str(ip_dest), int(dis)])
        """

        self.port = port

        self.serverSocket = socket.socket()

        self.serverSocket.bind(('127.0.0.1', port))

        self.serverSocket.listen(MaxConnect)

        #邻接表（二阶字典）。
        self.adjlist = {}
        #存储客户端ip到与其连接的本地套接字的映射
        self.connlist={}
        #收到回复的数量
        self.replycount=0

        
    def waitForPeer():
        """
            等待并接受peer的连接请求
        """
        while True:

            conn, addr = self.serverSocket.accept()  

            self.connlist[addr[0]]=conn        

            p = threading.Thread(target=self.handle, args=(conn,addr, ))

            p.start()
        pass

    def handle(self, conn, addr):
        """
            处理conn收到的peer上线下线或文件请求
            conn:连接套接字
            addr:客户端地址
            如果是上线/下线请求：
            修改邻接表，计算最短路径，发送新的路由表给路由器
            Peer->Controller: WANT ON/OFF （也可能是GET filename）　
            Controller-> all Routers:UPDATE msgSize msg(RouteTable)
            all Routers->Controller:UPDATE END
            Controller->peer: OFF/ON OK
        """
    
        while True:
            #32位头部信息。链路层协议。
            header = getHeader(conn).decode().split(' ')
            ip=addr[0]

            if header[0]=='GET':
                self.handleGET()
            elif header[1]=='ON' or header[1]=='OFF':
                self.handleOnOff(header[1],ip,conn)
                if header[1]=='OFF':
                    conn.close()
                    break 

        pass
 
    def handleOnOff(on_off,ip,conn):
        """
            处理上线下线请求
        """

        #更新邻接表
        if on_off=='ON':
            self.adjlist[ip]={}
            #随机分配邻接点与距离
            #
        elif on_off=='OFF':
            for key,val in self.adjlist[ip].items():
            del self.adjlist[key][ip]
            del self.adjlist[ip]
            del self.connlist[ip]
            #回复   
            header = "OFF OK".encode('utf8')
            padding = [32 for x in range(HEADER_SIZE - len(header))]
            conn.sendall(header)
            conn.sendall(padding)


        #计算任意两点间最短路径，用pathlist保存（map<str,map<str,str>>)  
        pathlist=self.shortestPaths()

        #给每个路由器发送更新后的路由表并等待回复
        for key, val in pathlist:
            p=threading.Thread(target=self.sendRouteAndWait,args=(key,val,conn,on_off,))
            p.start()


    def handleGET():
        """
            处理文件请求
        """
        pass

    def shortestPaths():
        """
            根据adjlist计算出任意两点间最短路径，结果存储在一个二阶字典中，并返回
        """
        pass

    def sendRouteAndWait(ip,routeTable,conn,on_off):
        """
            给路由器ip发送路由表并等待回复
        """
        routeTableStr=''
        for key,val in routeTable:
            routeTableStr+=key+' '+val+' '
        send_data=routeTable.rstrip().encode('utf8')
        header = ("UPDATE "+str(len(send_data))).encode('utf8')
        padding=[32 for x in range(HEADER_SIZE-len(header))]

        connlist[ip].sendall(header)
        connlist[ip].sendall(padding)
        connlist[ip].sendall(send_data)

        #等待回复
        reply=getHeader(connlist[ip]).decode().rstrip()
        if reply=='UPDATE END'
            replycount+=1
            #判断是否收到全部路由器的回复
            if replycount>=len[adjlist]:
                print('All routers have updated')
                replycount=0
                if on_off=='ON':
                    header = "ON OK".encode('utf8')
                    padding = [32 for x in range(HEADER_SIZE - len(header))]
                    conn.sendall(header)
                    conn.sendall(padding)

        pass

if __name__ == '__main__':

    t = Controller()

    t.waitForPeer()

    pass
