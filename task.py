

class task:
    '''
    只存储基础任务。高级任务通过上层结点状态判断
    '''
    def __init__(self, id, father_id, son_id, mission_system_id, production_type):
        self.id = id # 该基础任务在任务系统中的id
        self.father_id = father_id # 基础任务收购成品的工作台id
        self.son_id = son_id # 基础任务的用于生产的工作台id
        self.mission_system_id = mission_system_id # 该基础任务所属的任务系统的id
        self.production_type = production_type # 该基础任务的产品类型，也就是son的类型

        self.robot_id = -1 # 负责该基础任务的机器人的id
        

    def can_continue(self, worker_list):
        '''
        # FIXME 判断自己的父工作台是否还能接受材料
        return
        1 可以
        0 不可以
        '''
        father_worker = worker_list[self.father_id]
        son_worker = worker_list[self.son_id]
        flag = father_worker.lack_and_not_book_raw_materials(son_worker.worker_type)
        if flag == 1:
            # 缺少该原材料，并且没有预定该材料，可以继续进行该基础任务
            return 1
        else:
            return 0


    def get_brother(self, mission):
        '''
        # FIXME 获得当前基础任务的兄弟基础任务
        return：
        [] 没有兄弟任务
        [id,] 表示该任务系统中，该基础任务的兄弟基础任务的id
        '''
        # if mission.id != self.mission_system_id:
        #     raise RuntimeError
        
        brother_id_list = []
        for taski in mission.task_list:
            if taski.father_id == self.father_id:
                if taski.son_id != self.son_id:
                    brother_id_list.append(taski.id)

        return brother_id_list

