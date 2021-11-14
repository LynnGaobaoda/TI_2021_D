import queue
import struct
import time
from numpy import asarray
from cv2 import cv2


cmd_count = 0
cmd_flag = False
class VideoClient(object):
    def __init__(self, socket, add, is_left=True):
        self.m_socket = socket
        self.m_add = add  # add and port
        self.is_left = is_left  # 默认显示在左边
        self.pic = cv2.imread("lanpin.png", 0)
        self.no_sig_win = False
        self.other_name = '<no signal>client on right:' + str(is_left)  # 另一个无信号
        self.char_name = str(self.m_add)
        self.show_win = False
        self.win_last_full = False
        self.sig_last_full = False
        self.other_live = False
        self.has_l_flag = False
        self.has_a_flag = False


    def read_all(self, count):
        buf = b''
        if count > 100000:
            err_data = self.m_socket.recv(10000)
            return len(err_data)
        while count:
            new_buf = self.m_socket.recv(count)
            if not new_buf: return None
            buf += new_buf
            count -= len(new_buf)
        return buf

    def hand_data(self, G_queue, l_queue, x_queue, y_queue, cmd_q, finish_q,  f_l_q, f_a_q):
        global cmd_count, cmd_flag
        length = ''
        angle = ''

        while True:
            a_bit = self.m_socket.recv(3)
            # 读取文件类型
            # 0 = frame, 4 = cmd, 5 = (len>100000) 6=recv_success
            # 1 = length
            # 2 = x
            # 3 = y
            if a_bit == b'0f0':

                # 读取图片长度
                head_struct = self.m_socket.recv(4)
                image_len = struct.unpack('<L', head_struct)[0]
                # print("rev data len:%d" % image_len)
                if not image_len:  # 长度为0表示发送结束
                    break

                frame_byte = self.read_all(int(image_len))

                # if self.start_cmd:
                cmd_count += 1
                if cmd_count > 100:
                    cmd_count = 0
                    cmd_flag = False

                if (not cmd_q.empty()) and (cmd_flag == False):
                    # print("class-client hand data 下cmd_q get开始")
                    cmd_q.get()
                    # print("class-client hand data 下cmd_q get完毕")
                    self.m_socket.sendall(b'4c4')
                    cmd_flag = True
                    cmd_count = 0
                    print("发送启动命令")
                else:
                    if image_len > 100000:
                        self.m_socket.sendall(b'5e5')  # 恢复接收失败丢弃此帧
                        # print("err============================")
                        continue

                    # 图片显示在窗口
                    self.m_socket.sendall(b'6d6')  # 接收成功
                # 2进制转矩阵 带图片header信息
                img_np_arr = asarray(bytearray(frame_byte), dtype="uint8")
                image = cv2.imdecode(img_np_arr, 1)
                # image = cv2.resize(image, (480, 600))

                # todo 判断显示模式
                where = 12  # 默认全显 两个都有
                global_data = G_queue.get()

                # 另外一个是否存活
                if global_data.client_num == 1:
                    self.other_live = False
                elif global_data.client_num == 2:
                    self.other_live = True

                if global_data.show_mode == 0:  # 全显
                    if global_data.client_num == 1:  # 只有自己一个
                        where = 11  # "全显，只有自己"
                    elif global_data.client_num == 2:
                        where = 12  # "全显，两个都有"

                elif global_data.show_mode == 1:  # 显示左边的
                    where = 2  # "只显示左边的"
                elif global_data.show_mode == 2:  # 显示右边一个
                    where = 3  # "只显示右边的"
                G_queue.put(global_data)

                if not f_l_q.empty() and (not self.has_l_flag) :
                    self.has_l_flag = True
                    length = str(f_l_q.get())
                if not f_a_q.empty() and (not self.has_a_flag):
                    self.has_a_flag = True
                    angle = str(f_a_q.get())

                cv2.putText(image, "length: {}".format(length), (image.shape[1]-200, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(image, "angle : {}".format(angle), (image.shape[1] - 200, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                self.show_image(image, where)
                # todo 手动交互
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    global_data = G_queue.get()
                    global_data.set_mode()
                    G_queue.put(global_data)

            # todo 接收图像处理数据
            elif a_bit == b'1l1':
                head_struct = self.m_socket.recv(4)
                l_length = struct.unpack('<L', head_struct)[0]
                self.m_socket.sendall(b'1l1')
                l_queue.put(l_length)
                print("收到半径:%dfrom%s" % (l_length, str(self.m_add)))

            elif a_bit == b'2x2':
                head_struct = self.m_socket.recv(4)
                l_x = struct.unpack('<L', head_struct)[0]
                self.m_socket.sendall(b'2x2')
                x_queue.put(l_x)
                print("收到X:%d from %s" % (l_x, str(self.m_add)))

            elif a_bit == b'3y3':
                head_struct = self.m_socket.recv(4)
                l_y = struct.unpack('<L', head_struct)[0]
                self.m_socket.sendall(b'3y3')
                y_queue.put(l_y)
                #self.data_calculating = False
                print("收到y:%d from %s" % (l_y, str(self.m_add)))
                finish_q.put('1')
                self.has_l_flag = False
                self.has_a_flag = False
    def show_image(self, frame, where):
            # 全屏专用 cv2.setWindowProperty(char_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_AUTOSIZE)
        if where == 11:  # "全显，只有自己":
            self.add_no_sig( frame.shape[0],  frame.shape[1], False)
            self.add_self_win( frame.shape[0],  frame.shape[1], False)
            if self.is_left:
                cv2.moveWindow(self.char_name, 50, 20)
                cv2.moveWindow(self.other_name, 50 + frame.shape[0] + 10, 20)
            else:
                cv2.moveWindow(self.char_name, 50 + frame.shape[0] + 10, 20)
                cv2.moveWindow(self.other_name, 50, 20)
            cv2.imshow(self.other_name, self.pic)  # 另外一个显示无信号
            # cv2.waitKey(1)

        elif where == 12:  # "全显，两个都有":
            self.del_no_sig()  # 不显示无信号
            self.add_self_win(frame.shape[0],  frame.shape[1], False)
            if self.is_left:
                cv2.moveWindow(self.char_name, 50, 20)
            else:
                cv2.moveWindow(self.char_name, 50 + frame.shape[0] + 10, 20)

        elif where == 2:  # "只显示左边的":
            if self.is_left:  # 如果自己是左边的
                self.del_no_sig()  # 不显示无信号
                self.add_self_win(frame.shape[0],  frame.shape[1], True)
                # cv2.moveWindow(self.char_name, 50, 20)
            else:  # 自己是右边的不显示
                # todo 判断另外一个是否存活
                self.del_self_win()
                if self.other_live:
                    self.del_no_sig()
                else:
                    self.add_no_sig(frame.shape[0],  frame.shape[1], True)
                    # cv2.moveWindow(self.other_name, 50, 20)
                    cv2.imshow(self.other_name, self.pic)  # 另外一个显示无信号
                return

        elif where == 3:  # "只显示右边的":
            if not self.is_left:
                self.del_no_sig()  # 不显示无信号
                self.add_self_win(frame.shape[0], frame.shape[1], True)
                # cv2.moveWindow(self.char_name, 50 + frame.shape[0] + 10, 20)
            else:
                # todo 判断另外一个是否存活
                self.del_self_win()
                if self.other_live:
                    self.del_no_sig()
                else:
                    self.add_no_sig(frame.shape[0], frame.shape[1], True)
                    # cv2.moveWindow(self.other_name, 50 + frame.shape[0] + 10, 20)
                    cv2.imshow(self.other_name, self.pic)  # 另外一个显示无信号
                    # cv2.waitKey(1)
                return
        cv2.imshow(self.char_name, frame)
        return


    def add_no_sig(self, size_x, size_y, is_full):

        if not self.no_sig_win :  # 设置无信号窗口
            self.no_sig_win = True
            cv2.namedWindow(self.other_name, 0)
            if is_full:
                self.sig_last_full = True
                cv2.setWindowProperty(self.other_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                self.sig_last_full = False
                cv2.resizeWindow(self.other_name, size_x, size_y)
        if self.no_sig_win and (not self.sig_last_full) and is_full:
            self.sig_last_full = True
            cv2.setWindowProperty(self.other_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        elif self.no_sig_win and self.sig_last_full and (not is_full):
            self.sig_last_full = False
            cv2.resizeWindow(self.other_name, size_x, size_y)

    def add_self_win(self, size_x, size_y, is_full):
        if not self.show_win:  # 从没有窗口 到有窗口
            self.show_win = True
            cv2.namedWindow(self.char_name, 0)
            if is_full:
                self.win_last_full = True
                cv2.setWindowProperty(self.char_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                self.win_last_full = False
                cv2.resizeWindow(self.char_name, size_x, size_y)

        if self.show_win and (not self.win_last_full) and is_full:  # 从非全屏 到全屏
            self.win_last_full = True
            cv2.setWindowProperty(self.char_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        elif self.show_win and self.win_last_full and (not is_full):
            self.win_last_full = False
            cv2.resizeWindow(self.char_name, size_x, size_y)

    def del_no_sig(self):
        if self.no_sig_win:
            self.no_sig_win = False
            cv2.destroyWindow(self.other_name)  # 不显示无信号nb

    def del_self_win(self):
        if self.show_win:
            self.show_win = False
            cv2.destroyWindow(self.char_name)



class Global_Info(object):
    def __init__(self):
        self.client_num = 0
        self.show_mode = 0  # 0 1 2
        self.has_left = False

    def set_mode(self):
        self.show_mode = (self.show_mode + 1) % 3

    def sub_client(self):
        self.client_num -= 1

    def is_has_left(self):
        return self.has_left

    def turn_has_left(self, bool_h):
        self.has_left = bool_h
