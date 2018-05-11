# virtual-router
centralized_routing
v1.0
文件分类
1.Controller.py：控制器代码
2.Router.py：路由器代码
3.tools.py：一些函数
协议明确
1.总体介绍：控制器负责存储整个网络的拓扑信息，根据网络拓扑计算出网络中任意两个节点间的最短路径，生成路由表并发给相应的路由器；
并处理各个路由器的上线和下线；每个路由器都存储着当前的路由表，路由器要发送数据时，会根据路由表决定下一跳地址。当有别的路由器
上线或者下线时，路由器会收到控制器发送的新路由表
2.具体实施：
i.路由器上线：
Router -> Controller：WANT ON 
Controller: 
（1）随机选择已上线的IP（个数随机）与该新上线ip邻接，并随机设置距离（邻接和距离信息存储在一个邻接表中：map<str,map<str,int>> adjlist）;
	（2）根据邻接表计算每两个节点间的最短路径，并将结果存储在另一个字典中，map<str,map<str,str>> pathlist，比如ip3=pathlist[ip1][ip2]表
  示在ip1到ip2的最短路径中，ip1的下一跳是ip3。这样就生成了每一个路由器的路由表（pathlist[ip1]就是路由器ip1的路由表
​ -> each Router：UPDATE msgsize, msg(该路由器的路由表pathlist[x])
each Router：接收信息并更新本地路由表
​ -> Controller：UPDATE END
Controller：接收所有的UPDATE END信息，接收完成则
​ -> 之前想上线的Router：ON OK     
ii.路由器下线：
Router -> Controller：WANT OFF 
Controller：在邻接表中删除想下线的路由器IP，重新计算任意两个节点之间的最短路径，并更新pathlist
​ ->each Router (except 想要下线的Router)：UPDATE msgsize msg(该路由器的路由表pathlist[x])
each Router：接收信息并更新本地路由表
​ -> Controller：UPDATE END	
Controller：接收所有的finish信息，接收完成则
​ -> 之前想下线的Router：OFF OK
iii.路由表实现：
iv. map<str, str> routeList
	routeList[ipdest] = ip（下一跳ip）
v.路由器直接发送数据：
src Router1：sent ipdest，判断输入是否合法（由本地实现）
​ data_sent = input()
​ 根据路由表得出下一跳
​ -> 下一跳：SENT ipsrc ipdest msgsize, msg(data_sent)
Router2：接收信息，由ipdest和路由表获取下一跳
​ ->下一跳：SENT ipsrc ipdest msgsize, msg(data_sent)
… …
->下一跳：SENT ipsrc ipdest msgsize, msg(data_sent)
dest Routerx：接收信息，输出
​ ->src Router1：SENT OK ipsrc ipdest
中间路由：接收信息
​ -> SENT OK ipsrc ipdest
… …
src Router1：收到回复了
一些函数或语法
1.列表与字符串的相互转换
2.    str --> list  string.split(' ')
3.    list --> str  string.join(list)  
4.
5.    list = ['a', 'b']
    ','.join(list) --> 'a,b'
6.多线程的使用
7.import threading
8.
9.while True:
10.
11.            conn, addr = self.serverSocket.accept()          
12.
13.            p = threading.Thread(target=self.handle, args=(conn,addr, ))
14.
            p.start()
15.建立套接字
16.#Client:
17.self.Tsock = socket.socket()
18.self.Tsock.connect((tractorAddr, tractorPort))
19.
20.#Server:
21.self.serverSocket = socket.socket()
22.
23.self.serverSocket.bind(('127.0.0.1', port))
24.
self.serverSocket.listen(MaxConnect)
25.发送接收数据
26.#从连接读取指定长度的数据
27.HEADER_SIZE= 32
28.
29.#获取size大小的数据，存储在data里
30.def readNbytes(conn, data, size):
31.    count = 0
32.    #recv流式读取，可能不能一次性全部读取完
33.    while count != size:
34.        buffer = conn.recv(size - count)
35.        data[count:count + len(buffer)] = buffer
36.        count += len(buffer)
37.
38.#获取头部字符串
39.def getHeader(conn, size = HEADER_SIZE):
40.    data = [0 for x in range(size)]
41.    readNbytes(conn, data, size)
42.    header = bytes(data).decode()
43.    return header.strip()
44.
45.#Client:
46.        header = header.encode('utf8')
47.        padding = [32 for x in range(HEADER_SIZE - len(header))]
48.        self.Tsock.sendall(header)
49.        self.Tsock.sendall(bytes(padding))
50.        self.Tsock.sendall(send_data)
51.        
52.        
53.#Server:
54.	    header = "SET OK".encode('utf8')
55.        padding = [32 for x in range(HEADER_SIZE - len(header))]
56.        conn.send(header)
57.        conn.send(padding)
        
​
58.打开文件
59.            with open(newFileName, 'ab') as fw:
60.                for i in range(len(ipList)):
61.                    #读取分片文件 
62.                    with open(fileName + '_temp' + str(i), 'rb') as fr:
63.                        for line in fr.readlines():
                            fw.write(line)
​
64.补充，加油
