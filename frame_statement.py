
class frame_statement:
    def __init__(self, id, money):
        self.id = id
        self.money = money
        # 记录这些信息方便调试
        self.worker_statement = []
        self.robot_statement = []

        # 该帧的所有指令
        self.instructions = []