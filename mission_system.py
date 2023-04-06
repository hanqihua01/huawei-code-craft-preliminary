from task import task


class mission_system:
    '''
    任务系统，里面包括多个基础任务，高级任务等信息
    '''
    def __init__(self, id=-1) -> None:
        self.id = id # 表示该任务系统的id

        self.income = -1 # 表示该任务系统的总收益
        self.time = - 1 # 表示最理想情况下，该任务系统完成一次所需要的时间
        self.efficiency = 0 # 效率为 income / time

        self.task_number = 0 # 该任务系统的基础任务数量
        self.task_list = [] # 存储基础任务的列表，一旦系统初始化完成后，这些都是不会再发生改变的

        self.worker_num = 0 # 该任务系统的工作台数量
        self.worker_id_list = [] # 该任务系统的工作台id

        self.root_id = -1 # 作为根结点的worker的id，只可能是7，6，5，4类型工作台
        self.root_type = -1 # 表示根节点worker的类型
        self.end_worker_id = -1 # 终点结点的id，类型只可能是8或9

        self.robot_id_list = [] # 当前在该任务系统中工作的机器人的id

        self.type_time = {7: 1000, 6: 500, 5: 500, 4: 500, 3: 50, 2: 50, 1: 50} # 生产每种类型产品所需的帧数

    def recover(self, worker_list):
        '''
        该任务系统的所有工作台退出该任务系统
        '''
        if self.worker_id_list == []:
            # 如果此时还没有任何工作台加入该任务系统
            return
        else:
            for worker_id in self.worker_id_list:
                workeri = worker_list[worker_id]
                tmp_son_id_in_mission = []
                tmp_father_id_in_mission = []
                for item in workeri.son_id_in_mission:
                    if item[0] != self.id:
                        tmp_son_id_in_mission.append(item)
                
                for item in workeri.father_id_in_mission:
                    if item[0] != self.id:
                        tmp_father_id_in_mission.append(item)
                
                workeri.son_id_in_mission = tmp_son_id_in_mission
                workeri.father_id_in_mission = tmp_father_id_in_mission

                if tmp_son_id_in_mission==[] and tmp_father_id_in_mission==[]:
                    workeri.in_mission_system = 0


    
    def whether_continue(self, taski, worker_list):
        '''
        FIXME 判断当前的任务系统内，该基础任务是否需要继续 没有验证
        return:
        1 可以继续该基础任务
        0 不需要继续该基础任务
        '''
        block_flag = self.not_block(taski, worker_list)
        return block_flag

    def find_continuable_task(self, worker_list):
        '''
        FIXME 找到本任务系统内需求不阻塞，并且没有机器人负责的基础任务，并且该基础任务可以执行 没有验证
        return
        [] 表示没有找到
        [some task ids] 符合条件的基础任务的id列表
        '''
        task_id_list = []
        for taski in self.task_list:
            if taski.robot_id == -1:
                block_flag = self.not_block(taski, worker_list)
                if block_flag == 1:
                    if taski.can_continue(worker_list):
                        task_id_list.append(taski.id)
        return task_id_list


    def find_weakly_continuable_task(self, worker_list):
        '''
        FIXME 找到本任务系统内没有机器人负责的基础任务，并且该基础任务可以执行
        return
        [] 表示没有找到
        [some task ids] 符合条件的基础任务的id列表
        '''
        task_id_list = []
        for taski in self.task_list:
            if taski.robot_id == -1:
                if taski.can_continue(worker_list):
                        task_id_list.append(taski.id)
        return task_id_list

    def find_nearest(self, task_id_list, robot, worker_list):
        '''
        # 从给定基础任务中寻找距离robot最近的基础任务
        return
        id 基础任务的id
        '''
        min_distance = 100000
        min_task_id = -1

        for task_id in task_id_list:
            son_worker_in_task = worker_list[self.task_list[task_id].son_id]
            distance = (robot.position_x - son_worker_in_task.position_x)**2 + (robot.position_y - son_worker_in_task.position_y)**2
            if distance < min_distance:
                min_distance = distance
                min_task_id = task_id
        
        return min_task_id


    def initialize(self, worker_root, worker_group_list, worker_list):
        '''
        FIXME 
        以worker_root为根节点，创建任务系统
        注意在创建的同时就计算出：总收益，总耗时和效率
        '''
        # 确定该任务系统的终点worker
        if worker_root.worker_type == 7:
            possible_end_id = worker_group_list[8]+worker_group_list[9]
        else:
            possible_end_id = worker_group_list[9]
        
        if possible_end_id == []:
            # 没有能够收购该根节点的终点工作台，因此创建任务系统失败
            return False



        self.root_id = worker_root.id
        self.root_type = worker_root.worker_type
        self.worker_id_list.append(self.root_id)

        # 寻找根worker的所有后代worker的id号列表
        children_id_list = worker_root.find_all_children(worker_group_list, worker_list, self.id, father_id=-1)
        self.worker_id_list += children_id_list
        self.worker_id_list = list(set(self.worker_id_list))


        # 添加终点结点到任务系统中，8或9，它们是根节点的父亲结点
        min_distance = 1000000
        min_end_id = -1
        for end_id in possible_end_id:
            end_worker = worker_list[end_id]
            distance = (worker_root.position_x - end_worker.position_x)**2 + (worker_root.position_y - end_worker.position_y)**2
            if distance < min_distance:
                min_end_id = end_id
                min_distance = distance
        self.end_worker_id = min_end_id

        # 根节点的父亲是终点工作台
        worker_root.father_id_in_mission.append([self.id, [min_end_id]])

        # 终点工作台的儿子是根结点
        min_end_worker = worker_list[min_end_id]
        min_end_worker.son_id_in_mission.append([self.id, [worker_root.id]])

        # 终点工作台没有父亲结点
        min_end_worker.father_id_in_mission.append([self.id, []])

        # 完整的任务系统也包括终点工作台
        self.worker_id_list.append(min_end_id)
        self.worker_num = len(self.worker_id_list)
        
        # FIXME 需要对self.worker_id_list进行排序，从高层到底层排序
        # 遍历所有数组元素
        for i in range(self.worker_num):
            # Last i elements are already in place
            for j in range(0, self.worker_num-i-1):
                workerj0 = worker_list[self.worker_id_list[j]]
                workerj1 = worker_list[self.worker_id_list[j+1]]
                if workerj0.worker_type < workerj1.worker_type:
                    tmp = self.worker_id_list[j]
                    self.worker_id_list[j] = self.worker_id_list[j+1]
                    self.worker_id_list[j+1] = tmp


        # 获得该任务系统所有的基础任务
        for id in self.worker_id_list:
            workeri = worker_list[id]
            if workeri.worker_type in [1,2,3]:
                for item in workeri.father_id_in_mission:
                    if item[0] == self.id:
                        father_id_list = item[1]
                        for father_id in father_id_list:
                            new_task = task(self.task_number, father_id, id, self.id, workeri.worker_type)
                            self.task_list.append(new_task)
                            self.task_number += 1

        # 计算该任务系统的总耗时,总收益和效率
        self.time = self.calculate_time(worker_list=worker_list, root_id=self.root_id)
        self.income = self.calculate_income()
        self.efficiency = self.income / self.time

        return True

    def initialize_again(self, worker_root, worker_group_list, worker_list, mission_root_id_list):
        '''
        FIXME
        以worker_root为根节点，再次创建任务系统
        注意在创建的同时就计算出：总收益，总耗时和效率
        '''

        if worker_root.in_mission_system == 0:
            # 如果此时根工作台不在某个任务系统中，则说明没有可以收购它的工作台
            return False
        else:
            if worker_root.id not in mission_root_id_list:
                # 虽然在任务系统中，但是不是作为根工作台
                return False

        # 确定该任务系统的终点worker
        if worker_root.worker_type == 7:
            possible_end_id = worker_group_list[8]+worker_group_list[9]
        else:
            possible_end_id = worker_group_list[9]
        
        # if possible_end_id == []:
        #     # 到达此处，肯定有能够收购该根节点产品的终点工作台
        #     raise RuntimeError
        
        self.root_id = worker_root.id
        self.root_type = worker_root.worker_type
        self.worker_id_list.append(self.root_id)

        # 寻找根worker的所有后代worker的id号列表
        children_id_list = worker_root.find_all_children_not_in_mission(worker_group_list, worker_list, self.id, father_id=-1)
        self.worker_id_list += children_id_list
        

        if self.worker_id_list.count(-1) > 1:
            # 说明会和其它任务系统争抢中间结点
            return False

        self.worker_id_list = list(set(self.worker_id_list))
        if -1 in self.worker_id_list:
            self.worker_id_list.remove(-1)

        # 添加终点结点到任务系统中，8或9，它们是根节点的父亲结点
        min_distance = 1000000
        min_end_id = -1
        for end_id in possible_end_id:
            end_worker = worker_list[end_id]
            distance = (worker_root.position_x - end_worker.position_x)**2 + (worker_root.position_y - end_worker.position_y)**2
            if distance < min_distance:
                min_end_id = end_id
                min_distance = distance
        self.end_worker_id = min_end_id

        # 根节点的父亲是终点工作台
        worker_root.father_id_in_mission.append([self.id, [min_end_id]])

        # 终点工作台的儿子是根结点
        min_end_worker = worker_list[min_end_id]
        min_end_worker.son_id_in_mission.append([self.id, [worker_root.id]])

        # 终点工作台没有父亲结点
        min_end_worker.father_id_in_mission.append([self.id, []])

        # 完整的任务系统也包括终点工作台
        self.worker_id_list.append(min_end_id)
        self.worker_num = len(self.worker_id_list)

        # FIXME 需要对self.worker_id_list进行排序，从高层到底层排序
        # 遍历所有数组元素
        for i in range(self.worker_num):
            # Last i elements are already in place
            for j in range(0, self.worker_num-i-1):
                workerj0 = worker_list[self.worker_id_list[j]]
                workerj1 = worker_list[self.worker_id_list[j+1]]
                if workerj0.worker_type < workerj1.worker_type:
                    tmp = self.worker_id_list[j]
                    self.worker_id_list[j] = self.worker_id_list[j+1]
                    self.worker_id_list[j+1] = tmp


        # 获得该任务系统所有的基础任务
        for id in self.worker_id_list:
            workeri = worker_list[id]
            if workeri.worker_type in [1,2,3]:
                for item in workeri.father_id_in_mission:
                    if item[0] == self.id:
                        father_id_list = item[1]
                        for father_id in father_id_list:
                            new_task = task(self.task_number, father_id, id, self.id, workeri.worker_type)
                            self.task_list.append(new_task)
                            self.task_number += 1

        # 计算该任务系统的总耗时,总收益和效率
        self.time = self.calculate_time(worker_list=worker_list, root_id=self.root_id)
        self.income = self.calculate_income()

        if self.root_type != 7:
            self.efficiency = self.time / 10000
        else:
            self.efficiency = self.income / self.time
        return True


    def calculate_time(self, worker_list, root_id):
        '''
        FIXME 计算完成该任务系统的总时间
        '''
        root_worker = worker_list[root_id]
        total_distance = root_worker.calculate_son_distance_sum(worker_list, self.id)
        root_x = root_worker.position_x
        root_y = root_worker.position_y
        end_x = worker_list[self.end_worker_id].position_x
        end_y = worker_list[self.end_worker_id].position_y
        dis_x = root_x - end_x
        dis_y = root_y - end_y
        total_distance += (dis_x * dis_x + dis_y * dis_y)**0.5

        return total_distance

    def calculate_income(self):
        '''
        FIXME 计算完成该任务系统的总收益
        '''
        type_money = {7: 71400, 6: 14900, 5: 14200, 4: 13300, 3: 3400, 2: 3200, 1: 3000}
        return type_money[self.root_type]


    def not_block(self, taski, worker_list):
        '''
        FIXME 判断taski的祖先需求路线是否阻塞 还没有验证
        只要有一条需求路线是通的就可以
        1: 说明没有阻塞
        0: 说明阻塞了
        '''
        father_worker_in_task = worker_list[taski.father_id]
        block_flag = father_worker_in_task.check_block(self.id, worker_list)
        if block_flag == 0:
            return 1
        else:
            return 0

    def remove_robot(self, robot_id):
        '''
        从任务系统中移除一个机器人
        '''
        self.robot_id_list.remove(robot_id)
        for taski in self.task_list:
            if taski.robot_id == robot_id:
                taski.robot_id = -1
                return
        
        # # 到这里肯定有错误
        # raise RuntimeError
        
    def append_robot(self, robot_id, task_id):
        '''
        在任务系统中加入一个机器人
        '''
        self.robot_id_list.append(robot_id)
        for taski in self.task_list:
            if taski.id == task_id:
                # debug
                # if taski.robot_id != -1:
                #     raise RuntimeError
                taski.robot_id = robot_id
                return
        
        # # 到这里肯定有错误
        # raise RuntimeError

    def change_task(self, old_task_id, new_task_id, robot_id):
        '''
        更新机器人负责的基础任务
        '''
        old_task = self.task_list[old_task_id]
        old_task.robot_id = -1

        new_task = self.task_list[new_task_id]
        new_task.robot_id = robot_id


    def check_if_need_production(self, worker_id, worker_list):
        '''
        判断任务系统中是否需要该产品
        return:
        -1 不需要该产品
        id 需要该产品的工作台序号
        '''
        worker_type = worker_list[worker_id].worker_type
        for worker_idj in self.worker_id_list[1:]:
            workerj = worker_list[worker_idj]
            if workerj.raw_materials[worker_type] == [1, 0, 0]: # 有该材料位，没有该材料，并且没有预定该材料
                return worker_idj

        return -1

    def check_if_have_production(self, production_type, worker_list):
        '''
        判断本任务系统中是否有合适的成品：没有被预定
        return
        -1 没有找到
        id 有该成品的工作台
        '''
        for worker_id in self.worker_id_list:
            workeri = worker_list[worker_id]
            if workeri.worker_type == production_type and workeri.production_flag == 1 and workeri.reserve_production_flag == 0:
                return worker_id
        
        return -1










































