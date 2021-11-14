import math
import multiprocessing
import socket
import threading
import time
from math import atan
from multiprocessing import Process

from class_client import *

server_port = 1105
server_ip = "0.0.0.0"
import RPi.GPIO as GPIO

PIN_BEEP = 40 #GPIO编号，可自定义
PIN_LED = 31
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN_BEEP, GPIO.OUT)
GPIO.setup(PIN_LED, GPIO.OUT)


def beep(seconds):
    GPIO.output(PIN_BEEP, GPIO.HIGH)
    time.sleep(0.1 * seconds)
    GPIO.output(PIN_BEEP, GPIO.LOW)
    time.sleep(0.1 * seconds)
    GPIO.output(PIN_BEEP, GPIO.HIGH)
    time.sleep(0.1 * seconds)
    GPIO.output(PIN_BEEP, GPIO.LOW)
    time.sleep(0.7 * seconds)


def led():
    GPIO.output(PIN_LED, GPIO.HIGH)
    time.sleep(0.4)
    GPIO.output(PIN_LED, GPIO.LOW)
    time.sleep(0.2)
    GPIO.output(PIN_LED, GPIO.HIGH)


def angle(a, b):
    if a == 66:
        return 66
    agl = math.atan(a/b)
    return math.degrees(agl)


def main_logic(l_q, x_q, y_q, f_l_q, f_a_q):
    while True:
        l1 = l_q.get()
        l2 = l_q.get()
        x1 = x_q.get()
        x2 = x_q.get()
        y1 = y_q.get()
        y2 = y_q.get()

        if l1 == 66 or l1 < 50 or l1 > 150:
            final_data_l = l2
        elif l2 == 66 or l2 < 50 or l2 > 150:
            final_data_l = l1
        else:
            final_data_l = (l1 + l2) / 2

        degree1 = angle(x1, y2)
        degree2 = angle(x2, y1)

        final_degree = (degree1 + degree2) / 2

        f_l_q.put(final_data_l)
        f_l_q.put(final_data_l)

        print("***********************************")
        print("最终数据：！！！！！！ 绳长(单位cm)：", final_data_l)
        if not (l1 == 66 or l2 == 66):
            print("最终数据，！！！！！！ 角度(单位 °)：", final_degree)
            print("***********************************")
            f_a_q.put(final_degree)
            f_a_q.put(final_degree)

            led()
            beep(1)
            time.sleep(3)
            continue
        print("***********************************")

        # 没有角度
        f_a_q.put(0)
        f_a_q.put(0)

        led()
        beep(1)
        time.sleep(3)


def create_new_client(client_tuple, g_q) -> object:
    global_data = g_q.get()
    if global_data.is_has_left():  # 确保一个在左 一个在右边
        is_left = False
    else:
        is_left = True
        global_data.turn_has_left(True)
    n_client = VideoClient(client_tuple[0], client_tuple[1], is_left)
    g_q.put(global_data)
    return n_client


def client_thread(server_socket, n_client, g_queue, l_q, x_q, y_q, cmd_q, finish_q, f_l_q, f_a_q):
    server_socket.close()
    print("成功和客户端建立间接！！！！ ", n_client.m_add)  # 地址 端口
    finish_q.put('1')
    n_client.hand_data(g_queue, l_q, x_q, y_q, cmd_q, finish_q,  f_l_q, f_a_q)


def join_client(g_q, thread_q, client_q):
    while True:

        a_thread = thread_q.get()
        a_client = client_q.get()
        a_thread.join(3)  # 超时时间 1s 1s内 客户端线程未结束则回收下一个线程
        if not a_thread.is_alive():  # 客户机已经挂了
            print("摄像头%s断开连接............" % str(a_client.m_add))
            # todo   !!!!!!!!!
            # a_client.m_socket.close()  # 关闭套接字
            g_data = g_q.get()
            if a_client.is_left:
                g_data.turn_has_left(False)
            g_data.client_num -= 1  # 处理完毕，客户端关闭，数量减一
            g_q.put(g_data)
        else:
            thread_q.put(a_thread)  # 视频线程 未结束，入队，等待下一次join
            client_q.put(a_client)
        time.sleep(3)


def control_client(cmd_q, finish_q):
    key_pin = 12
    GPIO.setmode(GPIO.BOARD)
    # GPIO.setup(11, GPIO.OUT)
    GPIO.setup(key_pin, GPIO.IN)
    GPIO.setwarnings(False)
    while True:
        # todo 两个客户端分别发送命令.

        if finish_q.empty():  # 正在测量
            print("正在测量 或 等待摄像头连接")
            time.sleep(3)
        else:
            # todo 手动交互 开启检测命令
            # todo 确定两个视频 都连上才能按键
            finish_q.get()
            print("已成功连上一个摄像头")
            finish_q.get()
            print("已成功连上第二个摄像头")

            print("等待按键")
            while not GPIO.input(key_pin):
                time.sleep(0.01)
            GPIO.output(PIN_LED, GPIO.LOW)
            cmd_q.put('1')
            cmd_q.put('1')

        time.sleep(0.1)


if __name__ == '__main__':
    try:
        Global_data = Global_Info()
        l_queue = multiprocessing.Queue()
        x_queue = multiprocessing.Queue()
        y_queue = multiprocessing.Queue()

        G_queue = multiprocessing.Queue()
        G_queue.put(Global_data)

        thread_queue = queue.Queue()
        client_queue = queue.Queue()

        cmd_queue = multiprocessing.Queue()
        finish_queue = multiprocessing.Queue()

        final_length_queue = multiprocessing.Queue()
        final_angle_queue =  multiprocessing.Queue()
        # 网络通信基本流程

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((server_ip, server_port))
        server_socket.listen(3)
        # 计算结果 进程
        main_thread = Process(target=main_logic, args=(l_queue, x_queue, y_queue, final_length_queue, final_angle_queue))
        main_thread.start()
        # 回收子线程 线程 减少线程，增加稳定性
        join_thread = threading.Thread(target=join_client, args=(G_queue, thread_queue, client_queue))
        join_thread.start()
        # 命令控制 线程
        cmd_thread = Process(target=control_client, args=(cmd_queue, finish_queue))
        cmd_thread.start()
        print("等待客户端连接")
        # 监听客户端
        while True:
            connection, address = server_socket.accept()
            tem_q = G_queue.get()
            if tem_q.client_num < 2:
                tem_q.client_num += 1
                G_queue.put(tem_q)
            elif tem_q.client_num == 2:
                connection.close()
                G_queue.put(tem_q)
                time.sleep(1)
                continue

            new_client = create_new_client((connection, address), G_queue)
            new_client_thread = Process(target=client_thread, args=(server_socket,
                new_client, G_queue, l_queue, x_queue, y_queue,
                cmd_queue, finish_queue, final_length_queue,
                final_angle_queue))

            new_client_thread.start()
            connection.close()
            # 进程入队 等待被回收
            thread_queue.put(new_client_thread)
            client_queue.put(new_client)

    finally:
        print("finally 服务器 宕机了！！！！！！！！！！")
