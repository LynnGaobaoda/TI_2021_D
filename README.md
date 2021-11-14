# TI_2021_D
2021TI杯电赛D题
## 设备
1 树莓派三个：带显示屏+安装OPENCV python库  
2 USB摄像头两个  
3 交换机一个  
4 网线若干  

## 连接方式
根据题目要求连接，两个摄像节点各自使用一个树莓派，并且连接USB摄像头  
三个树莓派均通过网线，连在交换机上  

## 快速开始
0 修改client_pi_vedio.py 下的 IP 地址为终端服务器树莓派IP地址  
1 将三个py文件拷贝到三个树莓派下  
2 服务器终端树莓派 python3 server_pi_vedio.py  
3 两个摄像头节点 python3 client_pi_vedio.py  
4 按键启动可开始测量，测量超时时间25s  
