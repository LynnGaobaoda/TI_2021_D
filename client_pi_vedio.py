#!/usr/bin/python3
# -*- coding:utf-8 -*-

import socket
import struct
import datetime
import threading
import imutils
import time
import cv2
import math
import queue

ip = '169.254.3.33'  # 服务器IP地址

port = 1105
data_queue = queue.Queue()
# 连接服务器
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((ip, port))
my_ip = client_socket.getsockname()[0]

camera = cv2.VideoCapture(0)  # 直接打开摄像头0获取图像

key = [0, 0, 0, 0, 0, 0, 0, 0]
stand = []
key_y = []
ax = 0
ay = 0
server_cmd = False


def init_param():
    global data_queue, client_socket, key, stand, key_y, ax, ay, server_cmd

    key = [0, 0, 0, 0, 0, 0, 0, 0]
    stand = []
    key_y = []
    ax = 0
    ay = 0
    server_cmd = False


def shijue():
    """
    计算 摆动周期、测量角度所用参数（未实现）
    :return: None
    """
    global camera
    flag = 0
    mean = 0
    count = 0
    cishu = 0
    time_start = time.time()

    stand = []
    print("进入shijue")

    ab_mount = 0
    time_value = 0.0
    time_out = 0.0
    a_du = 0  # x
    b_du = 0  # y
    # 遍历视频的每一帧
    # 初始化视频流的第一帧
    shot_idx = 0
    firstFrame = None
    out_win = "calclute Feed" + str(my_ip)
    cv2.namedWindow(out_win, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(out_win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:

        # 读入摄像头的帧
        (grabbed, frame) = camera.read()
        text = "Stop"
        # 如果不能抓取到一帧，说明我们到了视频的结尾
        if not grabbed:
            break
        # cv2.imshow('frame',frame)
        # 调整该帧的大小，转换为灰阶图像并且对其进行高斯模糊
        frame = imutils.resize(frame, width=500)
        # 对帧进行预处理，先转灰度图，再进行高斯滤波。
        # 用高斯滤波进行模糊处理，进行处理的原因：每个输入的视频都会因自然震动、光照变化或者摄像头本身等原因而产生噪声。对噪声进行平滑是为了避免在运动和跟踪时将其检测出来。
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        # cv2.imshow('gray', gray)
        # 如果第一帧是None，对其进行初始化

        if firstFrame is None:
            firstFrame = gray  # 一开始检测的话首帧会不存在，那么就把灰度图作为首帧
            continue
        # 计算当前帧和第一帧的不同
        # 对于每个从背景之后读取的帧都会计算其与北京之间的差异，并得到一个差分图（different map）。
        # 还需要应用阈值来得到一幅黑白图像，并通过下面代码来膨胀（dilate）图像，从而对孔（hole）和缺陷（imperfection）进行归一化处理
        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 10, 255, cv2.THRESH_BINARY)[1]
        firstFrame = gray

        # 扩展阀值图像填充孔洞，然后找到阀值图像上的轮廓
        thresh = cv2.dilate(thresh, None, iterations=2)
        # 搜索轮廓
        # images, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        a_tuple = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = a_tuple[-2]
        # 这里用的是opencv4，cv2.findContours返回了2个参数，但是用opencv3的话会返回3给参数，你要确保有足够的变量承接返回值可改成 binary, contours, hierarchy = cv.findContours(thresh, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        # 返回值:contours:一个列表，每一项都是一个轮廓， 不会存储轮廓所有的点，只存储能描述轮廓的点hierarchy:一个ndarray, 元素数量和轮廓数量一样， 每个轮廓contours[i]对应4个hierarchy元素hierarchy[i][0] ~hierarchy[i][3]，分别表示后一个轮廓、前一个轮廓、父轮廓、内嵌轮廓的索引编号，如果没有对应项，则该值为负数

        """
            cv.findContours()
                参数：
                    1 要寻找轮廓的图像 只能传入二值图像，不是灰度图像
                    2 轮廓的检索模式，有四种：
                        cv2.RETR_EXTERNAL表示只检测外轮廓
                        cv2.RETR_LIST检测的轮廓不建立等级关系
                        cv2.RETR_CCOMP建立两个等级的轮廓，上面的一层为外边界，
                            里面的一层为内孔的边界信息。
                            如果内孔内还有一个连通物体，这个物体的边界也在顶层
                        cv2.RETR_TREE建立一个等级树结构的轮廓
                    3 轮廓的近似办法
                        cv2.CHAIN_APPROX_NONE存储所有的轮廓点，
                            相邻的两个点的像素位置差不超过1，
                            即max（abs（x1-x2），abs（y2-y1））==1
                        cv2.CHAIN_APPROX_SIMPLE压缩水平方向，垂直方向，对角线方向的元素，
                            只保留该方向的终点坐标，例如一个矩形轮廓只需4个点来保存轮廓信息
                返回值:
                    contours:一个列表，每一项都是一个轮廓， 不会存储轮廓所有的点，只存储能描述轮廓的点
                    hierarchy:一个ndarray, 元素数量和轮廓数量一样， 
                        每个轮廓contours[i]对应4个hierarchy元素hierarchy[i][0] ~hierarchy[i][3]，
                        分别表示后一个轮廓、前一个轮廓、父轮廓、内嵌轮廓的索引编号，如果没有对应项，则该值为负数
            """
        # 遍历轮廓
        time_out = time.time() - time_start
        for c in contours:
            # 轮廓太小忽略 有可能是斑点噪声

            if cv2.contourArea(c) < 500:  # 该为args["min_area"]
                continue
            # 将轮廓画出来
            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            # 计算轮廓的边界框，在当前帧中画出该框
            flat = 1  # 设置一个标签，当有运动的时候为1
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            text = "Moving"

            key.append(x)
            key_y.append(y)
            if (key[-1] != 0 and flag < 80):
                stand.append(key[-1])
                flag = flag + 1
                if (flag == 80):
                    for f in range(0, len(stand)):
                        mean = mean + stand[f]
                    mean = mean / 80
            if (len(key) >= 88):
                count = count + 1
                if (((mean - 6) <= key[-1] <= (mean + 6)) and count >= 6):
                    cishu = cishu + 1
                    count = 0
                # print(cishu)
                if (cishu == 1):
                    time_start = time.time()

                if (cishu == 16):
                    time_end = time.time()
                    time_value = time_end - time_start

            if len(key) == 101:
                for i in range(0, 50):
                    ab_mount = ab_mount + key[50+i]
                ab_mean = ab_mount // 50
                ab_max = max(key[50:100])
                ab_mix = min(key[50:100])

                a_du = ab_max - ab_mean  # x
                b_du = ab_mean - ab_mix  # y

        if time_out >= 25.0:
            cv2.destroyAllWindows()
            return 0, 66, 66

        # draw the text and timestamp on the frame
        # 在当前帧上写文字以及时间戳
        cv2.putText(frame, "Movement State: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        cv2.imshow(out_win, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # 摄像头屏蔽按键
            pass
        # frame = cv2.resize(frame, (480, 600))

        data_queue.put('f')
        data_queue.put(frame)

        if (cishu == 17):
            cv2.destroyAllWindows()
            print(a_du, b_du, time_value, time_out)
            return time_value, a_du*10 , b_du*10


def line_long(zhouqi):

    """
    半径数据较准、根据数次实验数据测量得出
    不同实验环境需要重新测量
    """

    if zhouqi == 0:
        return 66
    last = (((zhouqi / 8) / (2 * math.pi)) ** 2) * 9.8
    if (1.35 <= last < 1.50):
        last = last + 0.05
    if (1.15 <= last < 1.35):
        last = last + 0.05
    if (1.00 <= last < 1.15):
        last = last + 0.02

    if 1.40 <= last < 1.50:
        last = last + 0.02
    if 1.30 <= last < 1.40:
        last = last + 0.02
    if 1.20 <= last < 1.30:
        last = last + 0.01
    if 1.10 <= last < 1.20:
        last = last + 0.02
    if 1.00 <= last < 1.10:
        last = last + 0.03
    if 0.80 <= last < 1.00:
        last = last + 0.01
    if 0.50 <= last < 0.65:
        last = last - 0.02

    return last * 100 // 1


def send_data():
    """发送一帧图片及采样信息"""
    global server_cmd, data_queue
    data_1 = data_queue.get()
    data_2 = data_queue.get()

    # 0f0 = frame, 4c4 = cmd, 5e5 = (len>100000) 6d6=recv_success
    # 1 = length
    # 2 = x
    # 3 = y
    if data_1 == 'f':  # 视频帧
        client_socket.sendall(b'0f0')  # 视频帧 帧头
        #  像素矩阵编码添加header
        _, img_encode = cv2.imencode('.jpg', data_2)
        frame_byte = img_encode.tobytes()  # frame带头矩阵 转2进制流
        # 写入图片长度
        # print("发送长度 %d" % len(frame_byte))
        new_pack = struct.pack('<L', len(frame_byte))
        client_socket.sendall(new_pack)
        client_socket.sendall(frame_byte)  # 写入图片数据
        # print("等待服务器ack")
        server_char = client_socket.recv(3)
        # print("服务器是否完整接收%s" % str(server_char))
        if server_char == b'6d6':
            pass

        elif server_char == b'5e5':
            pass
        # todo 如果接收到的是命令 则开始测量数据
        elif server_char == b'4c4':
            # print("收到命令")
            server_cmd = True
        return True

    elif data_1 == 'l':  # 半径
        client_socket.sendall(b'1l1')
        int_data = int(data_2)
        new_pack = struct.pack('<L', int_data)
        client_socket.sendall(new_pack)
        server_char = client_socket.recv(3)
        if server_char == b'1l1':
            pass  # print("服务器收到半径")
        else:
            pass  # print("服务器没有收到半径")

        return True  # False 标识发送结束

    #########################
    elif data_1 == 'x':  # 角度 第一个参数
        client_socket.sendall(b'2x2')
        int_data = int(data_2)
        new_pack = struct.pack('<L', int_data)
        client_socket.sendall(new_pack)
        server_char = client_socket.recv(3)
        if server_char == b'2x2':
            pass
        else:
            pass
        return True
    elif data_1 == 'y':  # 角度 第二个参数
        client_socket.sendall(b'3y3')
        int_data = int(data_2)
        new_pack = struct.pack('<L', int_data)
        client_socket.sendall(new_pack)
        server_char = client_socket.recv(3)
        if server_char == b'3y3':
            pass
        else:
            pass
        return True


# 角度测量方案 废弃
# def angle(x, y):
#     middle = 0
#     while '' in x:
#         x.remove()
#     for i in range(len(x)):
#         middle = middle + x[i]
#         # todo
#     middle = middle / (len(x) - 8)
#     most_x = max(x[:110])
#     ax1 = most_x - middle
#     ay1 = (max(y) - min(y))
#     # print(ax, ay)
#     return ax1, ay1


def socket_free(socket_connection):
    """关闭连接"""
    socket_connection.close()
    print("socket连接 关闭成功 socket free ****")


def thread_send_data():
    print("thread_send_data trun************")
    while send_data():
        pass


def thread_handle_data():
    global camera
    global time_value, data_queue
    print("thread_handle_data run***********")
    time_value, a_du, b_du = shijue()
    print("shijue 结束")
    last = line_long(time_value)
    # angle(a_du, b_du)  # 角度 测量方案 废弃
    data_queue.put("l")
    data_queue.put(last)
    data_queue.put('x')
    data_queue.put(a_du)
    data_queue.put('y')
    data_queue.put(b_du)

    print("client 计算得到 绳长->：%d " %  last)


def waite_cmd():
    global camera, server_cmd
    firstFrame = None
    print("int waiting func")
    out_win = "wati for cmd" + str(my_ip)
    cv2.namedWindow(out_win, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(out_win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    while not server_cmd:

        # 读入摄像头的帧
        (grabbed, frame) = camera.read()
        text = "Stop"
        # 如果不能抓取到一帧，说明我们到了视频的结尾
        if not grabbed:
            break
        # 调整该帧的大小，转换为灰阶图像并且对其进行高斯模糊
        frame = imutils.resize(frame, width=500)
        # 对帧进行预处理，先转灰度图，再进行高斯滤波。
        # 用高斯滤波进行模糊处理，进行处理的原因：每个输入的视频都会因自然震动、光照变化或者摄像头本身等原因而产生噪声。对噪声进行平滑是为了避免在运动和跟踪时将其检测出来。
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # 如果第一帧是None，对其进行初始化
        if firstFrame is None:
            firstFrame = gray  # 一开始检测的话首帧会不存在，那么就把灰度图作为首帧
            continue
        # 计算当前帧和第一帧的不同
        # 对于每个从背景之后读取的帧都会计算其与北京之间的差异，并得到一个差分图（different map）。
        # 还需要应用阈值来得到一幅黑白图像，并通过下面代码来膨胀（dilate）图像，从而对孔（hole）和缺陷（imperfection）进行归一化处理
        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        firstFrame = gray

        # 扩展阀值图像填充孔洞，然后找到阀值图像上的轮廓
        thresh = cv2.dilate(thresh, None, iterations=2)

        # todo opencv 版本不一样需要修改
        # 搜索轮廓
        # images, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 3.x版本
        # contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 4.x 版本
        tuple_1 = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 4.x 版本
        contours = tuple_1[-2]
        # 这里用的是opencv4，cv2.findContours返回了2个参数，但是用opencv3的话会返回3给参数，你要确保有足够的变量承接返回值可改成 binary, contours, hierarchy =
        # cv.findContours(thresh, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE) 返回值:contours:一个列表，每一项都是一个轮廓，
        # 不会存储轮廓所有的点，只存储能描述轮廓的点hierarchy:一个ndarray, 元素数量和轮廓数量一样， 每个轮廓contours[i]对应4个hierarchy元素hierarchy[i][0]
        # ~hierarchy[i][3]，分别表示后一个轮廓、前一个轮廓、父轮廓、内嵌轮廓的索引编号，如果没有对应项，则该值为负数

        # 遍历轮廓
        for c in contours:
            # 轮廓太小忽略 有可能是斑点噪声

            if cv2.contourArea(c) < 800:  # 该为args["min_area"]
                continue
            # 将轮廓画出来
            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            # 计算轮廓的边界框，在当前帧中画出该框
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            text = "Moving"
            # 在画面上显示运动

        # draw the text and timestamp on the frame
        # 在当前帧上写文字以及时间戳
        cv2.putText(frame, "Movement State: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # todo
        cv2.imshow(out_win, frame)
        # 显示当前帧并记录用户是否按下按键
        if cv2.waitKey(1) & 0xFF == ord('q'):  # 摄像头屏蔽按键
            pass
        # frame = cv2.resize(frame, (480, 600))
        data_queue.put('f')
        data_queue.put(frame)
    server_cmd = False
    cv2.destroyAllWindows()


if __name__ == '__main__':
    """
    opencv 线程内存泄漏严重、推荐使用进程或者 直接调用函数
    """
    try:
        # 与服务器一直连接，发送视频数据
        send_thread = threading.Thread(target=thread_send_data, args=())
        send_thread.start()

        while True:

            waite_cmd()  # 阻塞 等待启动 命令

            thread_handle_data()  # 测量数据

            init_param()  # 重置参数，等待进行下一次数据测量命令

    finally:
        socket_free(client_socket)
