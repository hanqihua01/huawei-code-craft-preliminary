from math import sqrt, acos, asin, pi, sin, cos, atan
from sys import argv

class robot:
    def __init__(self, id, px, py, sx=0, sy=0, w=0, near_worker_id=-1, production_tpye=0, time_value=0, crash_value=0):
        self.id = id
        self.position_x = px
        self.position_y = py
        self.speed_x = sx
        self.speed_y = sy
        self.angle_speed = w
        self.near_worker_id = near_worker_id # 表示附近可以进行买卖的工作台id
        self.production_tpye = production_tpye # 携带物品类型,1-7,0表示没有携带物品
        self.time_value = time_value
        self.crash_value = crash_value

        self.mission_system_id = -1 # 指示机器人所属任务系统
        self.task_id = -1 # 指示机器人所属任务系统中，负责的基础任务的id（不是工作台的id）
        self.in_task = 0 # 0表示机器人不在执行任务，1表示机器人正在执行任务
        self.high_order_task = 0 # 0表示机器人不在执行高级任务，1表示正在执行高级任务
        self.high_start = -1 # 如果正在执行高级任务，则表示起点worker的id
        self.high_end = -1 # 如果正在执行高级任务，则表示终点worker的id

        self.reserve_information = [-1, -1] # 预定的高级任务的起点id与目的地id
        self.reserve_transport_production_flag = 0 # 是否已经预定了高级任务

        self.avoid_crash = 0b0000
        self.crash_end = 0b0000
        self.by_crash_end = 0b0000
    
    def update_statement(self, state):
        self.near_worker_id = int(state[0])
        self.production_tpye = int(state[1])
        self.time_value = float(state[2])
        self.crash_value = float(state[3])
        self.angle_speed = float(state[4])
        self.speed_x = float(state[5])
        self.speed_y = float(state[6])
        self.orientation = float(state[7])
        self.position_x = float(state[8])
        self.position_y = float(state[9])

    def update_task(self, mission_id, task_id, mission_list, worker_list, execute_isntantly=0):
        '''
        #FIXME 更新机器人负责的基础任务
        '''
        if mission_id != self.mission_system_id:
            # 如果机器人更换了任务系统
            # 更新机器人所在任务系统与负责的任务
            old_mission = mission_list[self.mission_system_id]
            old_mission.remove_robot(self.id)

            new_mission = mission_list[mission_id]
            new_mission.append_robot(self.id, task_id)
        else:
            # 只更新机器人负责的基础任务
            current_mission = mission_list[mission_id]
            current_mission.change_task(self.task_id, task_id, self.id)

        self.mission_system_id = mission_id
        self.task_id = task_id

        # 判断是否可以立马开始执行该任务
        current_task = mission_list[self.mission_system_id].task_list[self.task_id]
        if execute_isntantly == 1:
            # 说明可以马上执行
            self.continue_task(current_task, worker_list)
        else:
            if current_task.can_continue(worker_list):
                # 可以继续该基础任务
                self.continue_task(current_task, worker_list)
            else:
                # # 目前的逻辑运行到这里就出问题了
                # raise RuntimeError
                self.pause_task()

    def transport_base_production(self, start_id, end_id, worker_list, end_worker_type):
        '''
        # FIXME 领取运送成品的任务 未验证
        ''' 
        self.in_task = 1
        self.high_order_task = 1
        self.high_start = start_id
        self.high_end = end_id
        
        # 更新成品和材料的预定标志位
        start_worker = worker_list[start_id]
        end_worker = worker_list[end_id]

        # 因为是基础任务，因此不需要预留它的成品
        start_worker.reserve_production_flag = 0
        if end_worker.worker_type not in end_worker_type:
            end_worker.raw_materials[start_worker.worker_type][2] = 1
        else:
            end_worker.raw_materials[start_worker.worker_type][2] = 0
        

    def transport_production(self, start_id, end_id, worker_list, end_worker_type):
        '''
        # FIXME 领取运送成品的任务 未验证
        ''' 
        self.in_task = 1
        self.high_order_task = 1
        self.high_start = start_id
        self.high_end = end_id
        
        # 更新成品和材料的预定标志位
        start_worker = worker_list[start_id]
        end_worker = worker_list[end_id]
        start_worker.reserve_production_flag = 1
        if end_worker.worker_type not in end_worker_type:
            end_worker.raw_materials[start_worker.worker_type][2] = 1
        else:
            end_worker.raw_materials[start_worker.worker_type][2] = 0
        
    def transport_production_special(self, start_id, end_id, worker_list, end_worker_type):
        '''
        # FIXME 领取运送成品的任务 未验证
        ''' 
        self.in_task = 1
        self.high_order_task = 1
        self.high_start = start_id
        self.high_end = end_id
        
        # 更新成品和材料的预定标志位
        start_worker = worker_list[start_id]
        end_worker = worker_list[end_id]
        start_worker.reserve_production_flag = 1
        if end_worker.worker_type not in end_worker_type:
            end_worker.raw_materials[start_worker.worker_type][2] = 1
        else:
            end_worker.raw_materials[start_worker.worker_type][2] = 0 

        self.reserve_information = [-1, -1]
        self.reserve_transport_production_flag = 0

    def reserve_transport_production(self, start_id, end_id, worker_list, end_worker_type):
        '''
        预定一个可以执行的高级任务
        '''
        self.reserve_information = [start_id, end_id]
        self.reserve_transport_production_flag = 1

        # 更新成品和材料的预定标志位
        start_worker = worker_list[start_id]
        end_worker = worker_list[end_id]
        start_worker.reserve_production_flag = 1
        if end_worker.worker_type not in end_worker_type:
            end_worker.raw_materials[start_worker.worker_type][2] = 1
        else:
            end_worker.raw_materials[start_worker.worker_type][2] = 0


    def continue_task(self, taski, worker_list):
        '''
        # FIXME 机器人继续完成自己的基础任务
        不需要修改任务系统中的信息
        '''
        self.in_task = 1
        # 更新成品和材料的预定标志位
        # 会继续执行基础任务，而且基础任务的成品预定位置为0（意思是不会缺货）
        # 父工作台的材料预定位设为1
        worker_list[taski.son_id].reserve_production_flag = 0
        worker_list[taski.father_id].raw_materials[taski.production_type][2] = 1


        self.high_order_task = 0 # 0表示机器人不在执行高级任务，1表示正在执行高级任务
        self.high_start = -1 # 如果正在执行高级任务，则表示起点worker的id
        self.high_end = -1 # 如果正在执行高级任务，则表示终点worker的id

    def continue_transport_production(self):
        '''
        执行之前预定的高级任务
        '''
        self.in_task = 1
        self.high_order_task = 1
        
        self.high_start = self.reserve_information[0]
        self.high_end = self.reserve_information[1]
        self.reserve_transport_production_flag = 0
        self.reserve_information = [-1, -1]
        

    def pause_task(self):
        '''
        # FIXME 机器人暂停当前的基础任务, 此时应该停下来（不改变它负责的基础任务）
        '''
        self.in_task = 0 # 0表示机器人不在执行任务，1表示机器人正在执行任务
        
        self.high_order_task = 0 # 0表示机器人不在执行高级任务，1表示正在执行高级任务
        self.high_start = -1 # 如果正在执行高级任务，则表示起点worker的id
        self.high_end = -1 # 如果正在执行高级任务，则表示终点worker的id

        # # 此时如果携带有成品，则是出问题了
        # if self.production_tpye != 0:
        #     raise RuntimeError


    def get_destination_worker_id(self, mission_list):
        '''
        获得当前机器人的目的地工作台
        '''
        if self.high_order_task == 1:
            if self.production_tpye != 0:
                return self.high_end
            else:
                return self.high_start
        else:
            current_task = mission_list[self.mission_system_id].task_list[self.task_id]
            if self.production_tpye != 0:
                return current_task.father_id
            else:
                return current_task.son_id
    
    def get_task_father_worker_id(self, mission_list):
        '''
        获得机器人正在执行的任务的父工作台
        '''
        if self.high_order_task == 1:
            return self.high_end
        else:
            current_mission = mission_list[self.mission_system_id]
            current_task = current_mission.task_list[self.task_id]
            return current_task.father_id

    def calculate_angle(self, x, y):
        if (x == 0 and y > 0):
            return pi / 2
        if (x == 0 and y < 0):
            return 3 * pi / 2
        if (y == 0 and x > 0):
            return 0
        if (y == 0 and x < 0):
            return pi
        ret = atan(y / x)
        if (x < 0 and y > 0):
            return ret + pi
        if (x < 0 and y < 0):
            return ret + pi
        if (x > 0 and y < 0):
            return ret + pi * 2
        return ret


    def run_to_worker(self, target_worker_id, worker_list, robot_list, map_id):
        '''
        FIXME 返回一个指令列表，让机器人靠近目标工作台
        '''

        instruction_list = [] # 机器人self的两条指令
        final_speed = 0 # 设置机器人self的线速度
        final_angle = 0 # 设置机器人self的角速度

        target_worker = worker_list[target_worker_id] # 目标工作台
        
        cx = self.position_x # self的x坐标
        cy = self.position_y # self的y坐标
        wx = target_worker.position_x # target_worker的x坐标
        wy = target_worker.position_y # target_worker的y坐标
        dx = wx - cx # self与target_worker的x坐标差值
        dy = wy - cy # self与target_worker的y坐标差值
        d = sqrt(dx ** 2 + dy ** 2) # self与target_worker的距离
        udx = dx / d # x坐标差值单位化
        udy = dy / d # y坐标差值单位化

        vx = self.speed_x # self的x速度
        vy = self.speed_y # self的y速度
        v = sqrt(vx ** 2 + vy ** 2) # self的线速度
        ori = self.orientation # self的朝向
        if v != 0:
            uvx = vx / v # self的x速度单位化
            uvy = vy / v # self的y速度单位化
        else:
            uvx = cos(ori) # self的x虚拟速度单位化
            uvy = sin(ori) # self的y虚拟速度单位化

        theta = acos(udx * uvx + udy * uvy) # self的速度向量与目标向量的夹角，范围0-pi
        multi = uvx * udy - uvy * udx # 判断self的速度向量与目标向量夹角正负
        omega = theta if multi > 0 else -theta # self需要旋转的角速度（小）
        omega1 = pi if multi > 0 else -pi # self需要旋转的角速度（大）
        threshold = asin(0.4 / d) # self朝向目标的阈值

        if self.production_tpye == 0:
            r = 0.45 # self没有携带物品时的半径
        else:
            r = 0.53 # self携带物品时的半径

        '''
        不考虑机器人相撞，设置线速度和角速度
        '''
        # ----------可调节参数列表begin----------
        robot_boundary = 0.75 # 机器人位于边界判定阈值
        next_to_boundary = 0.75 - r # 机器人紧贴边界的判定阈值
        speed_in_boundary = 0.5 # 位于边界内且不紧贴边界时线速度

        speed_far_small_angle = 6.0 # 离目标远且不朝向目标且夹角小于二分之派时线速度
        speed_far_big_angle = 1.25 # 离目标远且不朝向目标且夹角大于二分之派时线速度

        worker_boundary = 1.25 # 工作台位于边界判定阈值
        speed_short_worker_in_boundary_in_direction = 2.0 # 离目标近且朝向目标且工作台在边界时线速度
        # -----------可调节参数列表end-----------
        # FIXME 如何制定边界减速条件
        if (cy >= 50 - robot_boundary and ori > 0 and ori < pi): # self位于上边界
            if (cy + r + next_to_boundary >= 50): # self紧贴上边界
                final_speed = 0.0
                final_angle = omega1
            else: # self不紧贴上边界
                final_speed = speed_in_boundary
                if (theta < threshold): # self朝向目标
                    final_angle = 0.0
                else: # self未朝向目标
                    final_angle = omega1
        elif (cy <= robot_boundary and ori > -pi and ori < 0): # self位于下边界
            if (cy <= r + next_to_boundary): # self紧贴下边界
                final_speed = 0.0
                final_angle = omega1
            else: # self不紧贴下边界
                final_speed = speed_in_boundary
                if (theta < threshold): # self朝向目标
                    final_angle = 0.0
                else: # self未朝向目标
                    final_angle = omega1
        elif (cx >= 50 - robot_boundary and ori > -pi / 2 and ori < pi / 2): # self位于右边界
            if (cx + r + next_to_boundary >= 50): # self紧贴右边界
                final_speed = 0.0
                final_angle = omega1
            else: # self不紧贴右边界
                final_speed = speed_in_boundary
                if (theta < threshold): # self朝向目标
                    final_angle = 0.0
                else: # self未朝向目标
                    final_angle = omega1
        elif (cx <= robot_boundary and ((ori > pi / 2 and ori <= pi) or (ori >= -pi and ori < -pi / 2))): # self位于左边界
            if (cx <= r + next_to_boundary): # self紧贴左边界
                final_speed = 0.0
                final_angle = omega1
            else: # self不紧贴左边界
                final_speed = speed_in_boundary
                if (theta < threshold): # self朝向目标
                    final_angle = 0.0
                else: # self未朝向目标
                    final_angle = omega1
        else: # self不位于任何边界
            if (d > 1.91): # self离目标较远
                if (theta < threshold): # self朝向目标
                    final_speed = 6.0
                    final_angle = 0.0
                else: # self未朝向目标
                    if (theta < pi / 2): # self速度与目标夹角小于pi / 2，设置小角速度
                        final_speed = speed_far_small_angle
                        final_angle = omega * 2
                    else: # self速度与目标夹角大于pi / 2，设置大角速度
                        final_speed = speed_far_big_angle
                        final_angle = omega1
            else: # self离目标较近
                if (wx > worker_boundary and wx < 50 - worker_boundary and wy > worker_boundary and wy < 50 - worker_boundary): # 工作台不在边界
                    if (theta < threshold): # self朝向目标
                        final_speed = 6.0
                        final_angle = 0.0
                    else: # self未朝向目标
                        final_speed = 1.25
                        final_angle = omega1
                else: # 工作台在边界
                    if (theta < threshold): # self朝向目标
                        final_speed = speed_short_worker_in_boundary_in_direction
                        final_angle = 0.0
                    else: # self未朝向目标
                        final_speed = 1.25
                        final_angle = omega1

        '''
        考虑机器人相撞，设置线速度和角速度
        '''
        # ----------可调节参数列表begin----------
        distance_check_crash = 4 # 两机器人距离多远以内进行碰撞检测
        crash_end_threshold = pi / 8 # 追尾情况下两速度夹角阈值
        speed_avoid_crash = 0 # 避障模式机器人线速度
        angle_avoid_crash = pi # 避障模式机器人角速度
        # -----------可调节参数列表end-----------
        # FIXME 如何判断机器人相撞
        for i in range(self.id + 1, 4):
            avoid_crash_flag = False # self与i是否会相撞标志
            crash_end_flag = 0 # self与i是否会追尾标志
            robot = robot_list[i]
            robot_px = robot.position_x # i的x坐标
            robot_py = robot.position_y # i的y坐标
            robot_vx = robot.speed_x # i的x速度
            robot_vy = robot.speed_y # i的y速度
            dis = sqrt((robot_px - cx) ** 2 + (robot_py - cy) ** 2) # self与i的距离
            if (dis < distance_check_crash):
                vx_combine = vx - robot_vx # 将i的速度反向加在self的速度上
                vy_combine = vy - robot_vy # 将i的速度反向加在self的速度上
                if (robot.production_tpye == 0):
                    rr = 0.45 # i的半径
                else:
                    rr = 0.53 # i的半径
                a = vy_combine # 点到之间距离方程系数
                b = -vx_combine # 点到之间距离方程系数
                c = vx_combine * cy - vy_combine * cx # 点到之间距离方程系数
                if (sqrt(a ** 2 + b ** 2) == 0): # 除零判断
                    self.avoid_crash = self.avoid_crash & (~(1 << i))
                    robot.avoid_crash = robot.avoid_crash & (~(1 << self.id))
                    self.crash_end = self.crash_end & (~(1 << i))
                    robot.crash_end = robot.crash_end & (~(1 << self.id))
                    self.by_crash_end = self.by_crash_end & (~(1 << i))
                    robot.by_crash_end = robot.by_crash_end & (~(1 << self.id))
                    continue
                d = abs(a * robot_px + b * robot_py + c) / sqrt(a ** 2 + b ** 2) # 点到直线距离
                uvx_combine = vx_combine / sqrt(vx_combine ** 2 + vy_combine ** 2)
                uvy_combine = vy_combine / sqrt(vx_combine ** 2 + vy_combine ** 2)
                udx_combine = (robot_px - cx) / dis
                udy_combine = (robot_py - cy) / dis
                theta = acos(udx_combine * uvx_combine + udy_combine * uvy_combine)
                if (d <= r + rr and theta < pi / 2):
                    avoid_crash_flag = True
                    # 追尾判断
                    robot_v = sqrt(robot_vx ** 2 + robot_vy ** 2)
                    if (robot_v == 0):
                        if (self.crash_end & (1 << i)):
                            crash_end_flag = 1
                        if (self.by_crash_end & (1 << i)):
                            crash_end_flag = 2
                    else:
                        robot_uvx = robot_vx / robot_v
                        robot_uvy = robot_vy / robot_v
                        theta_v = acos(uvx * robot_uvx + uvy * robot_uvy)
                        if (theta_v < crash_end_threshold):
                            if (robot_v < v):
                                crash_end_flag = 1
                            else:
                                crash_end_flag = 2
                                    
            if (avoid_crash_flag): # 如果会相撞
                self.avoid_crash = self.avoid_crash | (1 << i)
                robot.avoid_crash = robot.avoid_crash | (1 << self.id)
                # 设置追尾位
                self.crash_end = self.crash_end & (~(1 << i))
                robot.crash_end = robot.crash_end & (~(1 << self.id))
                self.by_crash_end = self.by_crash_end & (~(1 << i))
                robot.by_crash_end = robot.by_crash_end & (~(1 << self.id))
                if (crash_end_flag == 1):
                    self.crash_end = self.crash_end | (1 << i)
                    robot.by_crash_end = robot.by_crash_end | (1 << self.id)
                elif (crash_end_flag == 2):
                    robot.crash_end = robot.crash_end | (1 << self.id)
                    self.by_crash_end = self.by_crash_end | (1 << i)
            else:
                self.avoid_crash = self.avoid_crash & (~(1 << i))
                robot.avoid_crash = robot.avoid_crash & (~(1 << self.id))
                # 追尾位置零
                self.crash_end = self.crash_end & (~(1 << i))
                robot.crash_end = robot.crash_end & (~(1 << self.id))
                self.by_crash_end = self.by_crash_end & (~(1 << i))
                robot.by_crash_end = robot.by_crash_end & (~(1 << self.id))

        if (self.avoid_crash):
            if (self.crash_end):
                final_speed = speed_avoid_crash
                final_angle = 0.0
            elif (self.by_crash_end):
                final_speed = final_speed
                final_angle = final_angle
            else:
                final_speed = speed_avoid_crash
                final_angle = angle_avoid_crash

        instruction_list.append('forward %d %f\n' % (self.id, final_speed))
        instruction_list.append('rotate %d %f\n' % (self.id, final_angle))
        return instruction_list
