import socket
import hashlib
import threading
import time
import random
from tools import *

import os
UNFIN_BIG=1000  #正无穷
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
            resourceMap:  {filename1:[ip1, ...], ...}
            adjlist: {ip_src1:{ip_dest1:dis, ...}, ...}
            pathlist:  {ip_src1:{ip_dest1:ip_next，...}, ...}
        """

        self.port = port

        self.serverSocket = socket.socket()

        self.serverSocket.bind(('127.0.0.1', port))

        self.serverSocket.listen(MaxConnect)

        #存储文件名到具有该文件的ip的映射
        self.resourceMap={}
        #邻接表（二阶字典）。
        self.adjlist = {}
        #存储客户端ip到与其连接的本地套接字的映射
        self.connlist={}
        #收到回复的数量
        self.replycount=0

        
    def waitForPeer(self):
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
            Peer->Controller: WANT ON msgSize msg(filenames) /WANT OFF （也可能是GET filename）　
            Controller-> all Routers:UPDATE msgSize msg(RouteTable)
            all Routers->Controller:UPDATE END
            Controller->peer: OFF/ON OK
        """
    
        while True:
            #32位头部信息。链路层协议。
            header = getHeader(conn).decode().split(' ')
            ip=addr[0]

            if header[0]=='GET':
                self.handleGET(header[1],conn)
            elif header[1]=='ON' or header[1]=='OFF':
                self.handleOnOff(header,ip,conn)
                if header[1]=='OFF':
                    conn.close()
                    break 
            else:
                print('Unknown message')
        pass
 
    def handleOnOff(self,header,ip,conn):
        """
            处理上线下线请求
        """

        #更新邻接表
        if header[1]=='ON':
            #将该peer的资源信息加入到resourceMap
            msgSize=int(header[2])
            data=[0 for x in range(msgSize)]
            readNbytes(conn,data,msgSize)
            strfiles=bytes(data).decode('utf8')
            filelist=strfiles.split(',')
            for file in filelist:
                if file in self.resourceMap:
                    self.resourceMap[file].append(ip)
                else:
                    self.resourceMap[file]=[ip]

            #更新邻接表
            adjs={} #存储邻接点和距离
            adjnum=random.randint(2,4) #随机确定邻接点数量
            currPeers=list(self.adjlist.keys())
            for i in range(adjnum):
                adj=random.choice(currPeers) #随机选择一个邻接点
                dis=random.randint(1,5)     #随机确定链路代价
                adjs[adj]=dis
                currPeers.remove(adj)
            self.adjlist[ip]=adjs
            for key,val in adjs.items():
                self.adjlist[key][ip]=val
            
        elif header[1]=='OFF':
            #更新resourceMap
            for key ,val in self.resourceMap.items():
                if ip in val:
                    self.resourceMap[key].remove(ip) 

            #更新adjlist和connlist
            for key,val in self.adjlist[ip].items():
                del self.adjlist[key][ip]
            del self.adjlist[ip]
            del self.connlist[ip]

            #回复   
            header = "OFF OK".encode('utf8')
            padding = [32 for x in range(HEADER_SIZE - len(header))]
            conn.sendall(header)
            conn.sendall(bytes(padding))


        #计算任意两点间最短路径，用pathlist保存（map<str,map<str,str>>)  
        pathlist=self.shortestPaths()

        #给每个路由器发送更新后的路由表并等待回复
        for key, val in pathlist:
            p=threading.Thread(target=self.sendRouteAndWait,args=(key,val,conn,header[1],))
            p.start()
        pass

    def handleGET(self,filename,conn):
        """
            处理文件请求
        """
        send_data=(','.join(self.resourceMap[filename])).encode('utf8')
        header=('GET OK '+str(len(send_data))).encode('utf8')
        padding=[32 for x in range(HEADER_SIZE-len(header))]
        conn.sendall(header)
        conn.sendall(bytes(padding))
        conn.sendall(send_data)
        pass


    def shortestPaths(self):
        """
            根据adjlist计算出任意两点间最短路径，结果存储在一个二阶字典pathlist中，并返回
        """
        pathlist={}
        distlist={}  #存储ip1到ip2的距离
        known={}   #存储ip1到ip2的最短路径是否已经知道
        for ip1 in self.adjlist.keys():
            pathlist[ip1]={}
            distlist[ip1]={}
            known[ip1]={}
            for ip2 in self.adjlist.keys():
                known[ip1][ip2]=True if ip1==ip2 else False
                if ip2 in self.adjlist[ip1].keys():
                    distlist[ip1][ip2]=self.adjlist[ip1][ip2]
                    pathlist[ip2][ip1]=ip1
                else:
                    distlist[ip1][ip2]=UNFIN_BIG
                    pathlist[ip1][ip2]=''
                
        for ip1 in self.adjlist.keys():
            while True:
                if False not in known[ip1].values():
                    break
                _min=ip1
                for key, val in distlist[ip1].items():
                    if val<distlist[ip1][_min]:
                        _min=key
                known[ip1][_min]=True
                for key,val in self.adjlist[_min].items():
                    if known[ip1][key]==False:
                        new_dis=distlist[ip1][_min]+self.adjlist[_min][key]
                        if new_dis<distlist[ip1][key]:
                            distlist[ip1][key]=new_dis
                            pathlist[key][ip1]=_min 

        return pathlist
        pass


    def sendRouteAndWait(self,ip,routeTable,conn,on_off):
        """
            给路由器ip发送路由表并等待回复
        """
        routeTableStr=''
        for key,val in routeTable.items():
            routeTableStr+=key+' '+val+' '
        send_data=routeTable.rstrip().encode('utf8')
        header = ("UPDATE "+str(len(send_data))).encode('utf8')
        padding=[32 for x in range(HEADER_SIZE-len(header))]

        self.connlist[ip].sendall(header)
        self.connlist[ip].sendall(bytes(padding))
        self.connlist[ip].sendall(send_data)

        #等待回复
        reply=getHeader(self.connlist[ip]).decode().rstrip()
        if reply=='UPDATE END':
            self.replycount+=1
            #判断是否收到全部路由器的回复
            if self.replycount>=len[adjlist]:
                print('All routers have updated')
                self.replycount=0
                if on_off=='ON':#回复想要上线的路由器
                    header = "ON OK".encode('utf8')
                    padding = [32 for x in range(HEADER_SIZE - len(header))]
                    conn.sendall(header)
                    conn.sendall(bytes(padding))

        pass

if __name__ == '__main__':

    t = Controller()

    #t.waitForPeer()  #不知道为什么有这一行就会编译的时候一直卡在那里没有输出

    pass
