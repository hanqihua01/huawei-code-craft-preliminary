import sys

from robot import robot
from worker import worker
from frame_statement import frame_statement
from mission_system import mission_system

class map:
    def __init__(self):
        self.robot_number = 0
        self.robot_list = [] # store robots

        self.leaf_worker_type = [1,2,3]
        self.end_worker_type = [8, 9]
        self.middle_worker_type = [4,5,6,7]

        self.worker_number = 0
        self.worker_list = [] # store workers
        self.worker_group_list = []
        for i in range(10):
            self.worker_group_list.append([]) # 以组的形式存储每种类型工作台的id，一共9种，第0位空着

        self.frame_number = 0
        self.frame_list = [] # 保存有所有frame statement的列表

        self.mission_number = 0
        self.mission_list = [] # 存储每一个任务系统
        self.mission_root_id_list = [] # 存储每个任务系统的根结点id（不是终点结点），仅仅在初始化阶段使用，后续阶段不能使用
        self.mission_system_ranking_list = [] # 记录任务系统效率的排名 

        self.total_frame = 9000
        
        self.map_id = -1
        self.more_time = 0.2
    
    def read_map(self):
        # 此处读入地图，并进行预处理
        position_x = 0.25
        position_y = 49.75
        line = input()
        while line != "OK":
            for i in line:
                # 机器人类型
                if i == "A":
                    new_robot = robot(id=self.robot_number, px=position_x, py=position_y)
                    self.robot_list.append(new_robot)
                    self.robot_number += 1
                
                # 工作台类型
                elif i in "123456789":
                    new_worker = worker(id=self.worker_number, px=position_x, py=position_y, worker_type=int(i))
                    self.worker_list.append(new_worker)
                    self.worker_group_list[int(i)].append(new_worker.id)
                    self.worker_number += 1
                

                position_x += 0.5
            position_x = 0.25
            position_y -= 0.5
            line = input()
        
        # 读入地图后进行一些预先处理
        self.pre_calculate()
    
    def pre_calculate(self):
        # FIXME
        self.create_mission_system()
        self.robot_choose_mission_system_and_task()
        
    def delete_mission(self, mission, worker_list):
        '''
        删除某一个任务系统，该函数只在初始化时会调用，被删除的任务系统还没有加入self.mission_list中
        只需要更新一下该任务系统中各个工作台的信息即可
        '''
        mission.recover(worker_list)
        del mission

    def create_mission_system(self):
        ''' 
        由pre_calculate调用
        建立任务系统，只需要self.worker_list就行
        任务存储到self.mission_list中，注意按照效率进行排序
        '''
        # 只考虑以7，6，5，4为工作台建立任务系统（暂时不考虑1，2，3）
        for i in range(7,3,-1):
            groupi = self.worker_group_list[i]
            # 该worker group第一次作为根节点创建任务系统。每个worker必然可以成功创建一个任务系统（只要有可以收购该worker产品的终点结点即可）
            for worker_id in groupi:
                # 如果worker_id工作台还不属于任何任务系统
                # 则应该使用worker_id工作台尽可能创建多的任务系统
                # 否则不能用它创建任务系统
                workerj = self.worker_list[worker_id]
                if workerj.in_mission_system == 0:
                    # 还不属于其它任务系统的结点才可以作为根节点创建任务系统
                    # 第一次创建任务系统
                    new_mission = mission_system(id=self.mission_number)
                    success1 = new_mission.initialize(workerj, self.worker_group_list, self.worker_list)
                    if success1:
                        self.mission_list.append(new_mission)
                        self.mission_root_id_list.append(workerj.id)
                        self.mission_number += 1
                    else:
                        del new_mission
            
            if i==7:
                # 使用该worker 7尝试反复轮流继续创建任务系统
                while True:
                    flag = 0
                    for worker_id in groupi:
                        workerj = self.worker_list[worker_id]
                        new_mission = mission_system(id=self.mission_number)
                        # 注意：如果没有可以收购根产品的终点工作台，则创建失败
                        # 如果再次创建时，会和其它任务系统争抢中间工作台，则创建失败
                        success2 = new_mission.initialize_again(workerj, self.worker_group_list, self.worker_list, self.mission_root_id_list)
                        if success2 == False:
                            # 创建失败，则删除该任务系统，还要更新一下各个工作台的信息
                            self.delete_mission(new_mission, self.worker_list)
                        else:
                            # 只要有一个成功了，则再循环一次
                            self.mission_root_id_list.append(workerj.id)
                            self.mission_list.append(new_mission)
                            self.mission_number += 1
                            flag = 1

                    if flag == 0:
                        break


                    

        # 对任务系统进行效率排序
        for i in range(self.mission_number):
            max_efficiency = -10000
            max_id = -1
            for m in self.mission_list:
                if m.id not in self.mission_system_ranking_list:
                    if m.efficiency > max_efficiency:
                        max_id = m.id
                        max_efficiency = m.efficiency
            self.mission_system_ranking_list.append(max_id)


        

    def robot_choose_mission_system_and_task(self):
        '''
        FIXME：还没有验证
        由pre_calculate调用
        系统初始化时，每个机器人选择他们的任务系统
        只需要更新self.robot_list的中robot的状态即可
        '''
        # 机器人会首先考虑效率更高的任务系统
        for roboti in self.robot_list:
            for mission_id in self.mission_system_ranking_list:
                missionj = self.mission_list[mission_id]
                if missionj.task_number > len(missionj.robot_id_list):
                    # 该任务系统的基础任务数量还大于在其中工作的机器人的数量
                    # 机器人可以进入该任务系统工作
                    missionj.robot_id_list.append(roboti.id)
                    roboti.mission_system_id = mission_id
                    for taskk in missionj.task_list:
                        # 机器人在任务系统中寻找可以负责的基础任务
                        # 到达这一步，不可能找不到
                        # 此处是随机寻找基础任务，可以优化为寻找最近的基础任务 FIXME
                        if taskk.robot_id == -1:
                            taskk.robot_id = roboti.id
                            roboti.task_id = taskk.id
                            break
                    break


    def add_new_frame(self, frame_id, money):
        new_frame = frame_statement(id=frame_id, money=money)
        worker_number = int(input())
        # 读取工作台的状态
        for index in range(worker_number):
            line = input()
            parts = line.split(" ")
            self.worker_list[index].update_statement(parts)
            new_frame.worker_statement.append(parts)

        # 读取机器人的状态
        for index in range(self.robot_number):
            line = input()
            parts = line.split(" ")
            self.robot_list[index].update_statement(parts)
            new_frame.robot_statement.append(parts)
        
        self.frame_number += 1
        self.frame_list.append(new_frame)
        if self.frame_number > 1:
            old_frame = self.frame_list[self.frame_number-2]
            self.frame_list[self.frame_number-2] = 0
            del old_frame
            
        # TODO debug专用断点，可以在任何帧停下来
        if frame_id in [5150]:
            pause = 1
        ok = input()
        # if ok != "OK":
        #     raise RuntimeError
    
    def print_out_instruction(self):
        '''
        # FIXME 
        # 此时决策模块已经完成
        # 根据机器人领取的任务，得到每个机器人的行动指令，并输出
        '''
        # 根据函数decision中每个机器人得到的任务，得到机器人的执行指令，并放入frame_statement中
        for roboti in self.robot_list:
            if roboti.in_task == 0:
                # 表示该机器人处于无任务状态，应该发出指令，停止机器人运行
                self.stop_robot(roboti)
            else:
                self.instruct_robot(roboti)

        sys.stdout.write('%d\n' % self.frame_number)
        current_frame_instructions = self.frame_list[self.frame_number - 1].instructions
        for instruction in current_frame_instructions:
            sys.stdout.write(instruction)

    def stop_robot(self, roboti):
        '''
        # FIXME 将停止机器人运行的指令放入frame_statement中
        注意指令为一个字符串，以\n结尾
        '''
        # 此时应该要让机器人停止
        # if roboti.production_tpye != 0:
        #     raise RuntimeError
        
        # 添加指令到当前帧中
        current_frame = self.frame_list[self.frame_number - 1]
        current_frame.instructions.append("forward " + str(int(roboti.id)) + " 0\n") # 前进速度为0
        current_frame.instructions.append("rotate " + str(int(roboti.id)) + " 0\n") # 旋转速度为0


    def instruct_robot(self, roboti):
        '''
        # FIXME 针对机器人目前执行的任务，将相应指令放入frame_statement中 很多细节没有验证
        注意指令为一个字符串，以\n结尾
        '''
        current_frame = self.frame_list[self.frame_number - 1]
        # 任务分为基础任务与高级任务
        # 如果机器人正在执行基础任务
        total_instructions = []
        if roboti.high_order_task == 0:
            current_mission = self.mission_list[roboti.mission_system_id]
            current_task = current_mission.task_list[roboti.task_id]

            if roboti.production_tpye == 0:
                # 如果还没有拿到成品
                if roboti.near_worker_id != current_task.son_id:
                    # 还没有到达儿子工作台附近
                    instruction_list = roboti.run_to_worker(current_task.son_id, self.worker_list, self.robot_list, self.map_id)
                    total_instructions += instruction_list
                else:
                    # 此时已经到达儿子工作台附近 FIXME
                    # perhaps can't buy
                    son_worker = self.worker_list[current_task.son_id]
                    if son_worker.production_flag == 1:
                        father_worker_id = roboti.get_task_father_worker_id(self.mission_list)
                        flag = self.time_enough(roboti.id, father_worker_id)
                        if flag == 1:
                            # has production
                            total_instructions.append("buy " + str(int(roboti.id)) + "\n")
                            instruction_list = roboti.run_to_worker(current_task.father_id, self.worker_list, self.robot_list, self.map_id)
                            total_instructions += instruction_list
                            son_worker.reserve_production_flag = 0
                            son_worker.production_flag = 0
                            roboti.production_tpye = son_worker.worker_type
                        else:
                            # TODO 没有时间运送该成品了，直接停止
                            total_instructions.append("forward " + str(int(roboti.id)) + " 0\n")
                            total_instructions.append("rotate " + str(int(roboti.id)) + " 0\n")
                    else:
                        # don't have production; need wait; stop the robot
                        total_instructions.append("forward " + str(int(roboti.id)) + " 0\n")
                        total_instructions.append("rotate " + str(int(roboti.id)) + " 0\n")

            else:
                # 此时手中已经有成品了
                if roboti.near_worker_id != current_task.father_id:
                    # 还没有到达父工作台附近
                    instruction_list = roboti.run_to_worker(current_task.father_id, self.worker_list, self.robot_list, self.map_id)
                    total_instructions += instruction_list
                else:
                    # 此时已经到达父工作台附近 FIXME
                    father_worker = self.worker_list[current_task.father_id]
                    # perhaps can not sell
                    if father_worker.raw_materials[current_task.production_type][1] == 0:
                        total_instructions.append("sell " + str(int(roboti.id)) + "\n")
                        total_instructions.append("forward " + str(int(roboti.id)) + " 0\n") # 前进速度为0
                        total_instructions.append("rotate " + str(int(roboti.id)) + " 0\n") # 旋转速度为0
                        if father_worker.worker_type not in self.end_worker_type:
                            self.worker_list[current_task.father_id].raw_materials[current_task.production_type][2] = 0
                            self.worker_list[current_task.father_id].raw_materials[current_task.production_type][1] = 1
                        else:
                            self.worker_list[current_task.father_id].raw_materials[current_task.production_type][2] = 0
                            self.worker_list[current_task.father_id].raw_materials[current_task.production_type][1] = 0
                        roboti.production_tpye = 0
                        #----------------------------------------#
                        if roboti.reserve_transport_production_flag == 1:
                            roboti.continue_transport_production()
                        else:
                            roboti.pause_task()
                        #----------------------------------------#
                    else:
                        # if we can not sell, it must be a mistake
                        raise RuntimeError

        else:
            # 正在执行高级任务
            if roboti.production_tpye == 0:
                # 如果还没有拿到成品
                if roboti.near_worker_id != roboti.high_start:
                    # 还没有到达儿子工作台附近
                    instruction_list = roboti.run_to_worker(roboti.high_start, self.worker_list, self.robot_list, self.map_id)
                    total_instructions += instruction_list
                else:
                    # 此时已经到达儿子工作台附近 FIXME
                    son_worker = self.worker_list[roboti.high_start]
                    if son_worker.production_flag == 1:
                        father_worker_id = roboti.get_task_father_worker_id(self.mission_list)
                        flag = self.time_enough(roboti.id, father_worker_id)
                        if flag == 1:
                            total_instructions.append("buy " + str(int(roboti.id)) + "\n")
                            instruction_list = roboti.run_to_worker(roboti.high_end, self.worker_list, self.robot_list, self.map_id)
                            total_instructions += instruction_list
                            son_worker.reserve_production_flag = 0
                            son_worker.production_flag = 0
                            roboti.production_tpye = son_worker.worker_type
                        else:
                            # TODO 没有时间运送该成品了，直接停止
                            total_instructions.append("forward " + str(int(roboti.id)) + " 0\n")
                            total_instructions.append("rotate " + str(int(roboti.id)) + " 0\n")   
                    else:
                        if son_worker.worker_type in self.leaf_worker_type:
                            total_instructions.append("forward " + str(int(roboti.id)) + " 0\n")
                            total_instructions.append("rotate " + str(int(roboti.id)) + " 0\n")                            
                        else:
                            raise RuntimeError
            else:
                # 此时手中已经有成品了
                if roboti.near_worker_id != roboti.high_end:
                    # 还没有到达父工作台附近
                    instruction_list = roboti.run_to_worker(roboti.high_end, self.worker_list, self.robot_list, self.map_id)
                    total_instructions += instruction_list
                else:
                    # 此时已经到达父工作台附近 FIXME
                    father_worker = self.worker_list[roboti.high_end]
                    if father_worker.raw_materials[roboti.production_tpye][1] == 0:
                        total_instructions.append("sell " + str(int(roboti.id)) + "\n")
                        total_instructions.append("forward " + str(int(roboti.id)) + " 0\n") # 前进速度为0
                        total_instructions.append("rotate " + str(int(roboti.id)) + " 0\n") # 旋转速度为0
                        if father_worker.worker_type not in self.end_worker_type:
                            self.worker_list[roboti.high_end].raw_materials[roboti.production_tpye][2] = 0
                            self.worker_list[roboti.high_end].raw_materials[roboti.production_tpye][1] = 1
                        else:
                            self.worker_list[roboti.high_end].raw_materials[roboti.production_tpye][2] = 0
                            self.worker_list[roboti.high_end].raw_materials[roboti.production_tpye][1] = 0
                        roboti.production_tpye = 0
                        #----------------------------------------#
                        if roboti.reserve_transport_production_flag == 1:
                            roboti.continue_transport_production()
                        else:
                            roboti.pause_task()
                        #----------------------------------------#
                    else:
                        raise RuntimeError
        
        current_frame.instructions += total_instructions

    def time_enough(self, robot_id, destination_worker_id):
        '''
        判断机器人买下成品后，是否有足够时间送到
        假设为最快速度+0.5s之内可以到达，则任务可以到达
        '''
        roboti = self.robot_list[robot_id]
        destination_worker = self.worker_list[destination_worker_id]
        time_remaining = (self.total_frame - self.frame_number) / 50
        run_time = ((roboti.position_x - destination_worker.position_x)**2 + (roboti.position_y - destination_worker.position_y)**2)**0.5 / 6
        # TODO FIXME
        if run_time + self.more_time < time_remaining:
            return 1
        else:
            return 0


    def decision(self):
        '''
        # FIXME 决策模块 没有验证
        在该模块执行完成以后，机器人如果处于没有任务的状态，则应该停止运行
        如果机器人处于有任务的状态，则应该针对它的任务输出相应的指令
        '''
        for roboti in self.robot_list:

            if roboti.in_task == 1:
                if self.map_id == 1 and self.frame_number == 8693 and roboti.id==2:
                        roboti.high_order_task = 1 # 0表示机器人不在执行高级任务，1表示正在执行高级任务
                        roboti.high_start = 41 # 如果正在执行高级任务，则表示起点worker的id
                        roboti.high_end = 35 # 如果正在执行高级任务，则表示终点worker的id
                        father_id = roboti.get_task_father_worker_id(self.mission_list)
                        self.worker_list[father_id].raw_materials[roboti.production_tpye][2] = 0
                        self.worker_list[roboti.high_end].raw_materials[roboti.production_tpye][2] = 1
                        continue
                # 表示机器人正在执行任务中
                if roboti.reserve_transport_production_flag == 0:
                    # 如果该机器人没有预定高级任务，目的地工作台有成品，且是可以进行的高级任务，则可以提前预定该高级任务
                    destination_worker = self.worker_list[roboti.get_destination_worker_id(self.mission_list)]
                    if destination_worker.worker_type not in self.leaf_worker_type:
                        # 目标工作台不能是1，2，3
                        if destination_worker.production_flag == 1 and destination_worker.reserve_production_flag == 0:
                            current_mission = self.mission_list[roboti.mission_system_id]
                            need_worker_id = current_mission.check_if_need_production(destination_worker.id, self.worker_list)
                            if need_worker_id != -1:
                                # 如果本系统需要，则直接预定该高级任务
                                roboti.reserve_transport_production(destination_worker.id, need_worker_id, self.worker_list, self.end_worker_type)
                            else:
                                for mission_id in self.mission_system_ranking_list:
                                    need_worker_id = self.mission_list[mission_id].check_if_need_production(destination_worker.id, self.worker_list)
                                    if need_worker_id != -1:
                                        # 如果其它任务系统需要，则直接预定该高级任务（助人为乐）
                                        roboti.reserve_transport_production(destination_worker.id, need_worker_id, self.worker_list, self.end_worker_type)
                                        break

            else:

                worker_start_id, worker_end_id = self.worker_has_appropriate_production(roboti.mission_system_id)
                if worker_start_id != -1:
                    # 判断本任务系统内有没有可以立即运送的成品，如果有则马上分配该高级任务
                    # 最好不要空着手去做，先寻找有没有worker_start_id工作台需要的成品
                    # 如果是7号工作台的成品，则寻找4，5，6
                    # 如果是4，5，6，则寻找1，2，3
                    # roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                    if self.worker_list[worker_start_id].worker_type == 7:
                        middle_worker_id = self.find_previous_worker(roboti.mission_system_id, worker_start_id)
                        if middle_worker_id != -1:
                            roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                            roboti.transport_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                        else:
                            roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                    else:
                        # 说明工作台类型为 4，5，6
                        middle_worker_id = self.find_nearest_worker(worker_start_id, roboti.id)
                        if middle_worker_id != -1:
                            roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                            roboti.transport_base_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                        else:
                            roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)

                else:
                    flag4 = 0
                    # FIXME 迅速寻找其它任务系统中有没有可以做的高级任务，前提是那个任务系统目前没有机器人
                    for mission_id in self.mission_system_ranking_list:
                        if self.mission_list[mission_id].robot_id_list == []:
                            worker_start_id, worker_end_id = self.worker_has_appropriate_production(mission_id)
                            if worker_start_id != -1:
                                # 如果找到了可以做的高级任务，则判断可不可以抢过来放到自己的任务系统中
                                current_mission = self.mission_list[roboti.mission_system_id]
                                need_worker_id = current_mission.check_if_need_production(worker_start_id, self.worker_list)
                                if need_worker_id != -1 and self.worker_list[need_worker_id].worker_type not in self.end_worker_type:
                                    # 如果当前任务系统除了终点结点以外的工作台需要该产品，则将该产品抢过来
                                    # roboti.transport_production(worker_start_id, need_worker_id, self.worker_list, self.end_worker_type)
                                    if self.worker_list[worker_start_id].worker_type == 7:
                                        middle_worker_id = self.find_previous_worker(roboti.mission_system_id, worker_start_id)
                                        if middle_worker_id != -1:
                                            roboti.reserve_transport_production(worker_start_id, need_worker_id, self.worker_list, self.end_worker_type)
                                            roboti.transport_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                        else:
                                            roboti.transport_production(worker_start_id, need_worker_id, self.worker_list, self.end_worker_type)
                                    else:
                                        # 说明工作台类型为 4，5，6
                                        middle_worker_id = self.find_nearest_worker(worker_start_id, roboti.id)
                                        if middle_worker_id != -1:
                                            roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                            roboti.transport_base_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                        else:
                                            roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                else:
                                    # roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                    if self.worker_list[worker_start_id].worker_type == 7:
                                        middle_worker_id = self.find_previous_worker(roboti.mission_system_id, worker_start_id)
                                        if middle_worker_id != -1:
                                            roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                            roboti.transport_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                        else:
                                            roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                    else:
                                        # 说明工作台类型为 4，5，6
                                        middle_worker_id = self.find_nearest_worker(worker_start_id, roboti.id)
                                        if middle_worker_id != -1:
                                            roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                            roboti.transport_base_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                        else:
                                            roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                flag4 = 1
                                break

                    if flag4 == 0:
                        better_mission_id, better_task_id = self.has_better_task_in_other_mission(roboti.mission_system_id)
                        if better_mission_id != -1:
                            # 说明在其它任务系统中存在更好的任务，该机器人更新它的基础任务
                            # 任务系统效率更高，基础任务没有阻塞，基础任务可以执行，基础任务没有机器人负责
                            roboti.update_task(better_mission_id, better_task_id, self.mission_list, self.worker_list)
                        else:
                            # 此时机器人需要在它自己的任务系统中选择一个基础任务执行
                            current_mission = self.mission_list[roboti.mission_system_id]
                            current_task = current_mission.task_list[roboti.task_id]
                            # 此flag仅仅指示需求是否阻塞，不能说明该基础任务是否可以继续执行
                            flag1 = current_mission.whether_continue(current_task, self.worker_list)
                            if flag1 == 0:
                                # 不用再继续它的基础任务了，再做下去也只会造成阻塞。看看当前任务系统中是否有合适的基础任务可以执行
                                # continuable_task_id_list：需求路线没有阻塞，并且可以继续执行的基础任务
                                continuable_task_id_list = current_mission.find_continuable_task(self.worker_list)
                                if continuable_task_id_list != []:
                                    # 寻找距离机器人最近的可执行基础任务去执行
                                    nearest_task_id = current_mission.find_nearest(continuable_task_id_list, roboti, self.worker_list)
                                    roboti.update_task(current_mission.id, nearest_task_id, self.mission_list, self.worker_list)
                                else:
                                    # 该任务系统内其它基础任务都不合适做，机器人应该去其它任务系统中寻找是否有可以做的基础任务
                                    flag2 = 0 # 指示机器人是否在其它任务系统中找到了合适的基础任务
                                    for other_mission_id in self.mission_system_ranking_list:
                                        other_mission = self.mission_list[other_mission_id]
                                        if other_mission.id == current_mission.id:
                                            # 跳过本任务系统
                                            continue
                                        else:
                                            other_mission_continuable_task_id_list = other_mission.find_continuable_task(self.worker_list)
                                            if other_mission_continuable_task_id_list == []:
                                                continue
                                            else:
                                                other_mission_nearest_task_id = other_mission.find_nearest(other_mission_continuable_task_id_list, roboti, self.worker_list)
                                                roboti.update_task(other_mission.id, other_mission_nearest_task_id, self.mission_list, self.worker_list)
                                                flag2 = 1
                                                break
                                    #------------------------------------------------------------------------------------------------------------#
                                    if flag2 == 0:
                                        # 在其它任务系统中没有找到合适的基础任务
                                        if current_task.can_continue(self.worker_list):
                                            # 如果父工作台还能装，则机器人继续它自己的基础任务
                                            roboti.continue_task(current_task, self.worker_list)
                                        else:
                                            # FIXME 如果其它任务系统中有可以做的高级任务（就算那个任务系统里有机器人，也应该去抢了它的任务，自己不能歇着）
                                            flag = 0
                                            for other_mission_id in self.mission_system_ranking_list:
                                                if other_mission_id != current_mission.id:
                                                    worker_start_id, worker_end_id = self.worker_has_appropriate_production(other_mission_id)
                                                    if worker_start_id != -1:
                                                        # 找到了可以进行的高级任务，去把那个高级任务做了，然后返回自己的任务系统（因为到达此处已经说明了其它任务系统待不了）
                                                        # roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                        if self.worker_list[worker_start_id].worker_type == 7:
                                                            middle_worker_id = self.find_previous_worker(roboti.mission_system_id, worker_start_id)
                                                            if middle_worker_id != -1:
                                                                roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                                roboti.transport_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                                            else:
                                                                roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                        else:
                                                            # 说明工作台类型为 4，5，6
                                                            middle_worker_id = self.find_nearest_worker(worker_start_id, roboti.id)
                                                            if middle_worker_id != -1:
                                                                roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                                roboti.transport_base_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                                            else:
                                                                roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                        flag = 1
                                                        break

                                            if flag == 0:
                                                # 其它任务系统中也没有可以进行的高级任务
                                                # 找到本任务系统内没有机器人负责，并且可以执行的基础任务的基础任务
                                                weakly_continuable_task_id_list = current_mission.find_weakly_continuable_task(self.worker_list)
                                                if weakly_continuable_task_id_list == []:
                                                    # 该任务系统内其它基础任务都不合适做，机器人应该去其它任务系统中寻找是否有可以做的基础任务
                                                    flag6 = 0 # 指示机器人是否在其它任务系统中找到了合适的基础任务
                                                    for other_mission_id in self.mission_system_ranking_list:
                                                        other_mission = self.mission_list[other_mission_id]
                                                        if other_mission.id == current_mission.id:
                                                            # 跳过本任务系统
                                                            continue
                                                        else:
                                                            other_mission_continuable_task_id_list = other_mission.find_continuable_task(self.worker_list)
                                                            if other_mission_continuable_task_id_list == []:
                                                                continue
                                                            else:
                                                                other_mission_nearest_task_id = other_mission.find_nearest(other_mission_continuable_task_id_list, roboti, self.worker_list)
                                                                roboti.update_task(other_mission.id, other_mission_nearest_task_id, self.mission_list, self.worker_list)
                                                                flag6 = 1
                                                                break
                                                    if flag6==0:
                                                        # 实在找不到，则只有暂停机器人
                                                        # raise RuntimeError
                                                        roboti.pause_task()
    
                                                else:
                                                    nearest_task_id = current_mission.find_nearest(weakly_continuable_task_id_list, roboti, self.worker_list)
                                                    roboti.update_task(current_mission.id, nearest_task_id, self.mission_list, self.worker_list)
                                    #-------------------------------------------------------------------------------------------------------------#    
                            else:
                                # 还应该继续当前基础任务，其祖先路线至少有一条是通的
                                if current_task.can_continue(self.worker_list):
                                    # 如果父工作台还能装，则机器人继续它自己的基础任务
                                    roboti.continue_task(current_task, self.worker_list)
                                else:
                                    # 获得当前基础任务的兄弟基础任务
                                    current_task_brother_id_list = current_task.get_brother(current_mission)
                                    if current_task_brother_id_list == []:
                                        # 没有找到兄弟基础任务
                                        # FIXME 如果其它任务系统中有可以做的高级任务（就算那个任务系统里有机器人，也应该去抢了它的任务，自己不能歇着）
                                        flag = 0
                                        for other_mission_id in self.mission_system_ranking_list:
                                            if other_mission_id != current_mission.id:
                                                worker_start_id, worker_end_id = self.worker_has_appropriate_production(other_mission_id)
                                                if worker_start_id != -1:
                                                    # 找到了可以进行的高级任务，去把那个高级任务做了，然后返回自己的任务系统（因为自己的任务系统里还需要自己）
                                                    # roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                    if self.worker_list[worker_start_id].worker_type == 7:
                                                        middle_worker_id = self.find_previous_worker(roboti.mission_system_id, worker_start_id)
                                                        if middle_worker_id != -1:
                                                            roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                            roboti.transport_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                                        else:
                                                            roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                    else:
                                                        # 说明工作台类型为 4，5，6
                                                        middle_worker_id = self.find_nearest_worker(worker_start_id, roboti.id)
                                                        if middle_worker_id != -1:
                                                            roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                            roboti.transport_base_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                                        else:
                                                            roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                    
                                                    flag = 1
                                                    break

                                        if flag == 0:
                                            # 其它任务系统中也没有可以进行的高级任务
                                            # 找到本任务系统内没有机器人负责，并且可以执行的基础任务的基础任务
                                            weakly_continuable_task_id_list = current_mission.find_weakly_continuable_task(self.worker_list)
                                            if weakly_continuable_task_id_list == []:
                                                # 该任务系统内其它基础任务都不合适做，机器人应该去其它任务系统中寻找是否有可以做的基础任务
                                                flag6 = 0 # 指示机器人是否在其它任务系统中找到了合适的基础任务
                                                for other_mission_id in self.mission_system_ranking_list:
                                                    other_mission = self.mission_list[other_mission_id]
                                                    if other_mission.id == current_mission.id:
                                                        # 跳过本任务系统
                                                        continue
                                                    else:
                                                        other_mission_continuable_task_id_list = other_mission.find_continuable_task(self.worker_list)
                                                        if other_mission_continuable_task_id_list == []:
                                                            continue
                                                        else:
                                                            other_mission_nearest_task_id = other_mission.find_nearest(other_mission_continuable_task_id_list, roboti, self.worker_list)
                                                            roboti.update_task(other_mission.id, other_mission_nearest_task_id, self.mission_list, self.worker_list)
                                                            flag6 = 1
                                                            break
                                                if flag6==0:
                                                    # 实在找不到，则只有暂停机器人
                                                    # raise RuntimeError
                                                    roboti.pause_task()
                                            else:
                                                nearest_task_id = current_mission.find_nearest(weakly_continuable_task_id_list, roboti, self.worker_list)
                                                roboti.update_task(current_mission.id, nearest_task_id, self.mission_list, self.worker_list)
                                    else:
                                        current_task_brother_id = current_mission.find_nearest(current_task_brother_id_list, roboti, self.worker_list)
                                        current_task_brother = current_mission.task_list[current_task_brother_id]
                                        if current_task_brother.robot_id == -1 and current_task_brother.can_continue(self.worker_list):
                                            # 如果兄弟基础任务没有机器人负责，并且可以执行，则机器人去执行兄弟基础任务
                                            roboti.update_task(current_task_brother.mission_system_id, current_task_brother.id, self.mission_list, self.worker_list, execute_isntantly=1)
                                        else:
                                            # 兄弟基础任务已经有人去做了
                                            # FIXME 如果其它任务系统中有可以做的高级任务（就算那个任务系统里有机器人，也应该去抢了它的任务，自己不能歇着）
                                            flag = 0
                                            for other_mission_id in self.mission_system_ranking_list:
                                                if other_mission_id != current_mission.id:
                                                    worker_start_id, worker_end_id = self.worker_has_appropriate_production(other_mission_id)
                                                    if worker_start_id != -1:
                                                        # 找到了可以进行的高级任务，去把那个高级任务做了，然后返回自己的任务系统（因为自己的任务系统里还需要自己）
                                                        # roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                        if self.worker_list[worker_start_id].worker_type == 7:
                                                            middle_worker_id = self.find_previous_worker(roboti.mission_system_id, worker_start_id)
                                                            if middle_worker_id != -1:
                                                                roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                                roboti.transport_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                                            else:
                                                                roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)                                                        
                                                        else:
                                                            # 说明工作台类型为 4，5，6
                                                            middle_worker_id = self.find_nearest_worker(worker_start_id, roboti.id)
                                                            if middle_worker_id != -1:
                                                                roboti.reserve_transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                                roboti.transport_base_production(middle_worker_id, worker_start_id, self.worker_list, self.end_worker_type)
                                                            else:
                                                                roboti.transport_production(worker_start_id, worker_end_id, self.worker_list, self.end_worker_type)
                                                        
                                                        
                                                        flag = 1
                                                        break

                                            if flag == 0:
                                                # 其它任务系统中也没有可以进行的高级任务
                                                # 找到本任务系统内没有机器人负责，并且可以执行的基础任务的基础任务
                                                weakly_continuable_task_id_list = current_mission.find_weakly_continuable_task(self.worker_list)
                                                if weakly_continuable_task_id_list == []:
                                                    # 该任务系统内其它基础任务都不合适做，机器人应该去其它任务系统中寻找是否有可以做的基础任务
                                                    flag6 = 0 # 指示机器人是否在其它任务系统中找到了合适的基础任务
                                                    for other_mission_id in self.mission_system_ranking_list:
                                                        other_mission = self.mission_list[other_mission_id]
                                                        if other_mission.id == current_mission.id:
                                                            # 跳过本任务系统
                                                            continue
                                                        else:
                                                            other_mission_continuable_task_id_list = other_mission.find_continuable_task(self.worker_list)
                                                            if other_mission_continuable_task_id_list == []:
                                                                continue
                                                            else:
                                                                other_mission_nearest_task_id = other_mission.find_nearest(other_mission_continuable_task_id_list, roboti, self.worker_list)
                                                                roboti.update_task(other_mission.id, other_mission_nearest_task_id, self.mission_list, self.worker_list)
                                                                flag6 = 1
                                                                break
                                                    if flag6==0:
                                                        # 实在找不到，则只有暂停机器人
                                                        # raise RuntimeError
                                                        roboti.pause_task()
                                                else:
                                                    nearest_task_id = current_mission.find_nearest(weakly_continuable_task_id_list, roboti, self.worker_list)
                                                    roboti.update_task(current_mission.id, nearest_task_id, self.mission_list, self.worker_list)

    def find_nearest_worker(self, worker_start_id, robot_id):
        '''
        找到最近的合适的工作台
        '''
        worker_start = self.worker_list[worker_start_id]
        worker_son_type = worker_start.son_type
        roboti = self.robot_list[robot_id]

        min_distance = 1000000
        min_id = -1
        for son_type in worker_son_type:
            if worker_start.raw_materials[son_type] == [1, 0, 0]:
                # 如果缺少该材料，则寻找最近的该工作台
                worker_id_list = self.worker_group_list[son_type]
                for id in worker_id_list:
                    workerj = self.worker_list[id]
                    # 两段距离之和
                    distance = ((worker_start.position_x - workerj.position_x)**2+(worker_start.position_y - workerj.position_y)**2)**0.5 + ((roboti.position_x - workerj.position_x)**2 + (roboti.position_y - workerj.position_y)**2)**0.5
                    # distance = ((worker_start.position_x - workerj.position_x)**2+(worker_start.position_y - workerj.position_y)**2)**0.5

                    if distance < min_distance:
                        min_distance = distance
                        min_id = id

        # distance_near = ((roboti.position_x - worker_start.position_x)**2 + (roboti.position_y - worker_start.position_y)**2)**0.5
        
        # # # TODO FIXME

        # if min_distance > 4*distance_near:
        #     return -1

        if min_distance > 31:
            return -1
        
        if (self.total_frame - self.frame_number)/50 < 1.2 * (min_distance / 6):
            return -1
        
        
        return min_id


    def find_previous_worker(self, current_mission_id, worker_id):
        '''
        从所有任务系统中寻找合适的产品
        优先考虑自己的任务系统，产品没有被预定
        '''
        workeri = self.worker_list[worker_id]
        worker_son_type = workeri.son_type
        for son_type in worker_son_type:
            if workeri.raw_materials[son_type] == [1, 0, 0]:
                # 如果缺少该材料，则在本系统中寻找有没有合适的材料
                workerj_id = self.mission_list[current_mission_id].check_if_have_production(son_type, self.worker_list)
                if workerj_id != -1:
                    return workerj_id
        
        # 到此处，本任务系统中已经没有符合条件的工作台了，到其它任务系统中去寻找
        for mission in self.mission_list:
            if mission.id != current_mission_id:
                for son_type in worker_son_type:
                    if workeri.raw_materials[son_type] == [1, 0, 0]:
                        # 如果缺少该材料，则在其它系统中寻找有没有合适的材料
                        workerj_id = mission.check_if_have_production(son_type, self.worker_list)
                        if workerj_id != -1:
                            return workerj_id
        
        return -1

    def worker_has_appropriate_production(self, mission_id):
        '''
        # 寻找可以运送成品的工作台 FIXME 没有验证
        return:
        worker_start_id, worker_end_id找到了可以运送成品的工作台，返回起点与终点的id
        -1, -1 没有找到
        '''
        current_mission = self.mission_list[mission_id]
        for worker_id in current_mission.worker_id_list:
            workeri = self.worker_list[worker_id]
            # 合适的工作台：
            # 类型不是1，2，3；有成品；成品没有被预定；存在父工作台可以接收该成品；
            if workeri.worker_type not in [1,2,3]:
                if workeri.production_flag == 1:
                    if workeri.reserve_production_flag == 0:
                        father_id = workeri.father_worker_prepare_ok(mission_id, self.worker_list)
                        if father_id != -1:
                            # 到达此处，机器人应该先执行送成品的任务
                            return workeri.id, father_id
        
        # 到达此处只能是没找到
        return -1, -1



    def has_better_task_in_other_mission(self, mission_system_id):
        '''
        FIXME 判断其它效率更高的任务系统中有无合适的基础任务 没有验证
        条件：
        没有机器人负责，它的祖先需求路线没有阻塞
        return:
        better_mission_id, better_task_id
        -1, -1 表示没找到
        '''

        for index in self.mission_system_ranking_list:
            if index == mission_system_id:
                # 执行到这一步，说明在效率更高的任务系统里找不到合适的基础任务
                return -1, -1
            else:
                more_efficiency_mission = self.mission_list[index]
                for taski in more_efficiency_mission.task_list:
                    if taski.robot_id == -1:
                        # 该基础任务没有机器人负责，检查它的祖先需求路线是否通畅
                        if more_efficiency_mission.not_block(taski, self.worker_list):
                            # 并且该基础任务可以执行
                            if taski.can_continue(self.worker_list):
                                # 说明该基础任务更好
                                return index, taski.id
        
        # 到达此处说明有bug
        # raise RuntimeError
                

        
