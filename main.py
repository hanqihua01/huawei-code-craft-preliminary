#!/bin/bash
import sys
import time
from map import map



def read_util_ok():
    line = input()
    while line != "OK":
        line = input()


def finish():
    sys.stdout.write('OK\n')
    sys.stdout.flush()


if __name__ == '__main__':
    # initailize read whole map
    my_map = map()
    my_map.read_map()
    finish()
    

    # after 5s, start read frame
    while True:
        line = sys.stdin.readline().strip("\n")
        if not line:
            break

        # 读入新一帧的状态
        parts = line.split(' ')
        frame_id = int(parts[0])
        money = int(parts[1])
        my_map.add_new_frame(frame_id=frame_id, money = money)

        # 进行决策
        my_map.decision()

        # 输出指令给判题器
        my_map.print_out_instruction()
        finish()
