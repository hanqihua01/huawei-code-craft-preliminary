class worker:
    def __init__(self, id, px, py, worker_type, time_remaining=-1, raw_materials=0, production_flag=0):
        self.id = id # 就是该工作台在worker list中的序号
        self.position_x = px
        self.position_y = py

        self.worker_type = worker_type # 工作台类型，int
        self.son_type = [] # 可能的儿子的类型，也就是原材料的类型
        self.father_type = [] # 可能的父亲的类型，也就是可以收购该工作台成品的工作台类型

        # 在每个任务系统中的son与father的id
        self.son_id_in_mission = [] # [mission_id, [son_id, ...]]
        self.father_id_in_mission = [] # [mission_id, [father_id, ...]]
        self.in_mission_system = 0 # 是否是已经在任务系统中了.

        self.time_remaining = time_remaining # -1：不在生产中；0：成品格占用造成阻塞；>=0：生产剩余帧数
        self.raw_materials = [] # 二进制表示的原材料格状态 [是否有该原材料格子，是否已有该原材料，该原材料是否已经从其它地方预定好了]
        for i in range(10):
            self.raw_materials.append([0,0,0])
        
        self.production_flag = production_flag # 是否有成品
        self.reserve_production_flag = 0 # 成品是否被预定了

        self.initialize()
    
    def initialize(self):
        if self.worker_type == 9:
            self.son_type = [1,2,3,4,5,6,7]
        elif self.worker_type == 8:
            self.son_type = [7]
        elif self.worker_type == 7:
            self.son_type = [4,5,6]
            self.father_type = [8, 9]
        elif self.worker_type == 6:
            self.son_type = [2,3]
            self.father_type = [7,9]
        elif self.worker_type == 5:
            self.son_type = [1,3]
            self.father_type = [7,9]
        elif self.worker_type == 4:
            self.son_type = [1,2]
            self.father_type = [7,9]
        elif self.worker_type == 3:
            self.father_type = [5,6,9]
        elif self.worker_type == 2:
            self.father_type = [4,6,9]
        elif self.worker_type == 1:
            self.father_type = [4,5,9]
        else:
            raise RuntimeError

        # 指明自己需要的原材料的类型
        for materials_type in self.son_type:
            self.raw_materials[materials_type][0] = 1


    def update_statement(self, state):
        # 下面三个可以不更新
        # self.worker_type = int(state[0])
        # self.position_x = float(state[1])
        # self.position_y = float(state[2])

        self.time_remaining = int(state[3])

        raw_materials_statement = int(state[4])
        tmp_str = str(bin(raw_materials_statement))[2:][::-1]
        for i in range(10-len(tmp_str)):
            tmp_str += "0"
        for raw_materials_id in range(10):
            if tmp_str[raw_materials_id] == "1":
                self.raw_materials[raw_materials_id][1] = 1
            else:
                self.raw_materials[raw_materials_id][1] = 0
        
        self.production_flag = int(state[5])

    def find_all_children(self, worker_group_list, worker_list, mission_system_id, father_id):
        '''
        在初始化任务系统时使用，找到所有后代worker的id
        return 
        [id] 如果是1，2，3类型，则返回自己的id列表
        递归调用子孙的find_all_children
        '''

        # 到达这里，一定已经在某个任务系统中了
        self.in_mission_system = 1


        if father_id != -1:
            # 记录在该任务中父工作台的id
            # 这里是为了防止叶子结点反复加入父结点id才这样写的。因为叶子结点可能有多个父亲，因此先判断一下以前有没有append过信息列表
            flag = 0
            for item in self.father_id_in_mission:
                if item[0] == mission_system_id:
                    item[1].append(father_id)
                    flag = 1
                    break
            if flag == 0:
                self.father_id_in_mission.append([mission_system_id, [father_id]])

        if self.worker_type in [1,2,3]:
            # 这里是为了防止叶子结点反复加入父结点id才这样写的。因为叶子结点可能有多个父亲，因此先判断一下以前有没有append过信息列表
            flag = 0
            for item in self.son_id_in_mission:
                if item[0] == mission_system_id:
                    flag = 1
                    break
            if flag == 0:
                self.son_id_in_mission.append([mission_system_id ,[]])
            return [self.id]
        else:
            # 寻找距离最近的son的id号
            son_id_list = []
            for son_type in self.son_type:
                son_id_group = worker_group_list[son_type]
                if son_id_group == []:
                    raise RuntimeError
                min_distance = 1000000
                min_son_id = -1
                for son_id in son_id_group:
                    son = worker_list[son_id]
                    distance = (self.position_x - son.position_x)**2 + (self.position_y - son.position_y)**2
                    if distance < min_distance:
                        min_son_id = son_id
                        min_distance = distance
                
                # 此时找到了距离最近的son
                son_id_list.append(min_son_id)
            
            # FIXME 这里需要注意的是，对于非叶子结点，只有一个父结点，因此不需要判断是否已经有了儿子id列表。直接append即可
            self.son_id_in_mission.append([mission_system_id, son_id_list])


            # 找到所有son id后，对son进行递归搜索
            grandson_id_list = []
            for son_id in son_id_list:
                son = worker_list[son_id]
                grandson_id_list += son.find_all_children(worker_group_list, worker_list, mission_system_id, self.id)

            return son_id_list + grandson_id_list


    def find_all_children_not_in_mission(self, worker_group_list, worker_list, mission_system_id, father_id):
        '''
        在初始化任务系统时使用，找到所有后代worker的id，对于非叶子结点，它不能属于其它任务系统
        return 
        [id] 如果是1，2，3类型，则返回自己的id列表
        递归调用子孙的find_all_children_not_in_mission
        '''

        # 到达这里，一定已经在某个任务系统中了
        self.in_mission_system = 1

        if father_id != -1:
            # 记录在该任务中父工作台的id
            # 这里是为了防止叶子结点反复加入父结点id才这样写的。因为叶子结点可能有多个父亲，因此先判断一下以前有没有append过信息列表
            flag = 0
            for item in self.father_id_in_mission:
                if item[0] == mission_system_id:
                    item[1].append(father_id)
                    flag = 1
                    break
            if flag == 0:
                self.father_id_in_mission.append([mission_system_id, [father_id]])

        if self.worker_type in [1,2,3]:
            # 这里是为了防止叶子结点反复加入父结点id才这样写的。因为叶子结点可能有多个父亲，因此先判断一下以前有没有append过信息列表
            flag = 0
            for item in self.son_id_in_mission:
                if item[0] == mission_system_id:
                    flag = 1
                    break
            if flag == 0:
                self.son_id_in_mission.append([mission_system_id ,[]])
            return [self.id]
        else:
            # 寻找son的id号，如果son是叶子结点，则是寻找最近的son；否则寻找最近的不属于任何任务系统的son（如果没有找到，则返回-1）
            son_id_list = []
            
            for son_type in self.son_type:
                son_id_group = worker_group_list[son_type]
                if son_id_group == []:
                    raise RuntimeError
                min_distance = 1000000
                min_son_id = -1
                for son_id in son_id_group:
                    son = worker_list[son_id]
                    if son.in_mission_system == 0 or son.worker_type in [1,2,3]:
                        distance = (self.position_x - son.position_x)**2 + (self.position_y - son.position_y)**2
                        if distance < min_distance:
                            min_son_id = son_id
                            min_distance = distance
                
                # 此时找到了距离最近的son，如果加入的是-1，则说明该类型son都属于某个任务系统了，该任务系统最后会创建失败
                son_id_list.append(min_son_id)

                # TODO 
                if min_son_id == -1:
                    for son_id in son_id_group:
                        son = worker_list[son_id]
                        distance = (self.position_x - son.position_x)**2 + (self.position_y - son.position_y)**2
                        if distance < min_distance:
                            min_son_id = son_id
                            min_distance = distance
                    son_id_list.append(min_son_id)
            
            # FIXME 这里需要注意的是，对于非叶子结点，只有一个父结点，因此不需要判断是否已经有了儿子id列表。直接append即可
            tmp_son_id_list = []
            for son_id in son_id_list:
                if son_id != -1:
                    tmp_son_id_list.append(son_id)
            
            self.son_id_in_mission.append([mission_system_id, tmp_son_id_list])

            # if -1 in son_id_list:
            #     # 没必要再递归搜索下去了
            #     return son_id_list
            # else:
            #     # 找到所有son id后，对son进行递归搜索
            #     grandson_id_list = []
            #     for son_id in son_id_list:
            #         son = worker_list[son_id]
            #         grandson_id_list += son.find_all_children_not_in_mission(worker_group_list, worker_list, mission_system_id, self.id)

            #     return son_id_list + grandson_id_list

            # 找到所有son id后，对son进行递归搜索
            grandson_id_list = []
            for son_id in tmp_son_id_list:
                son = worker_list[son_id]
                grandson_id_list += son.find_all_children_not_in_mission(worker_group_list, worker_list, mission_system_id, self.id)

            return son_id_list + grandson_id_list

    def father_worker_prepare_ok(self, mission_id, worker_list):
        '''
        判断该工作台是否存在父工作台可以接收自己的成品
        '''
        for tmp in self.father_id_in_mission:
            # 找到指定任务系统中的父工作台们的id
            if tmp[0] == mission_id:
                father_id_list = tmp[1]
                for father_id in father_id_list:
                    # 如果有father缺少该原材料并且没有预定该材料
                    father = worker_list[father_id]
                    if father.lack_and_not_book_raw_materials(self.worker_type):
                        return father_id
                # 所有父工作台都有该材料了
                return -1
        
        return -1
        # # 到达此处只能是出错了
        # raise RuntimeError

    def lack_and_not_book_raw_materials(self, materials_type):
        # 缺少该原材料并且没有预定该材料
        if self.raw_materials[materials_type][1] != 1 and self.raw_materials[materials_type][2] != 1:
            return True
        else:
            return False

    def get_father_id_list(self, mission_id):
        '''
        获得在任务系统mission_id中的父工作台id
        '''
        for tmp in self.father_id_in_mission:
            if tmp[0] == mission_id:
                return tmp[1]
        
        # 没找到只能是出错了
        raise RuntimeError
    
    def get_son_id_list(self, mission_id):
        '''
        获得在任务系统mission_id中的儿子工作台id
        '''
        for tmp in self.son_id_in_mission:
            if tmp[0] == mission_id:
                return tmp[1]
        
        # 没找到只能是出错了
        raise RuntimeError

    def check_block(self, mission_id, worker_list):
        '''
        FIXME 递归检测需求路线是否阻塞 还没有验证
        自己有成品，则返回1
        没有成品则返回0
        '''
        if self.production_flag == 1:
            # 自己有成品，说明在自己这里被阻塞了
            return 1
        else:
            # 去问该工作台在这个任务系统中的父工作台是否被成品堵塞了
            total_flag = 1
            father_id_list_in_mission = self.get_father_id_list(mission_id)
            if father_id_list_in_mission == []:
                # 说明是终点工作台，肯定没有成品，直接返回0
                return 0
            else:
                # 询问父工作台们是否堵塞。只要有一个父工作台没有堵塞即可
                for father_id in father_id_list_in_mission:
                    father_worker = worker_list[father_id]
                    flag = father_worker.check_block(mission_id, worker_list)
                    total_flag = total_flag * flag
                
                if total_flag == 0:
                    # 到这一步，自己肯定是没有成品的。如果total_flag为1，说明父工作台们
                    # 全部阻塞了。如果total_flag为0，则说明至少有一条路线通往了终点工作台
                    return 0
                else:
                    return 1

    def lack_raw_materials(self, materials_type):
        '''
        检查是否缺少某一种原材料
        1 缺少
        0 不缺少
        '''
        flag = self.raw_materials[materials_type][1]
        if flag == 0:
            return 1
        else:
            return 0

    def calculate_son_distance_sum(self, worker_list, mission_id):
        '''
        
        '''

        if self.worker_type in [1,2,3]:
            return 0
        else:
            distance_sum = 0
            son_id_list = self.get_son_id_list(mission_id)
            for son_id in son_id_list:
                son = worker_list[son_id]
                distance_sum += ((self.position_x-son.position_x)**2+(self.position_y-son.position_y)**2)**0.5
                distance_sum += worker_list[son_id].calculate_son_distance_sum(worker_list, mission_id)
            return distance_sum
