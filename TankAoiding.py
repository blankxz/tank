# encoding: utf-8
import pygame
import sys
import math
import random
import numpy as np
from Vector2d import Vec2d

#SCREEN_SIZE = (1024, 768)
SCREEN_SIZE = (950, 750)
TANK_SIZE = 50
SEARCH_RANGE = 200.  # 搜索范围
COMMUNICATION_RANGE = 400.  # 通信范围
AVOID_RANGE = 71.  # 避障范围   之前设置的是50 现在设置成50根2
position_all = []
global cishu
cishu = 0

zhangai = [Vec2d(400,200),Vec2d(400,550),Vec2d(500,550),Vec2d(500,200)]

# 这个保存每次的目的地
global LotoDe
LotoDe = Vec2d(0,0)

global VoidState
VoidState = 4


for num in range(1,285+1):
    if num == 105 or num ==124 or num ==143 or num ==162 or num ==181 or num ==200:
        pass
    else:
        position_all.append(num)
print(position_all)

class State(object):
    """状态"""

    def __init__(self, name):
        self.name = name

    def do_actions(self):
        """  状态动作 """
        pass

    def check_conditions(self):
        """  状态转移检查 """
        pass

    def entry_actions(self):
        """ 状态进入动作 """
        pass

    def exit_actions(self):
        """  状态退出动作 """
        pass


class StateMachine(object):
    """智能体的状态切换通过有限状态机来体现
    有限状态机以字典的形式存在
    key是策略名称
    value是策略具体内容，即操纵智能体执行动作
    每个智能体具有独立的有限状态机，即可进行自我思考，进而执行不同的策略"""

    def __init__(self):
        self.states = {}  # 存储状态   字典
        self.active_state = None  # 当前有效状态

    def add_state(self, state):
        """  增加状态 """
        self.states[state.name] = state

    def think(self):
        """  判断状态 """
        if self.active_state is None:
            return
        self.active_state.do_actions()  # 执行有效状态的动作
        new_state_name = self.active_state.check_conditions()  # 转移检查
        if new_state_name is not None:
            self.set_state(new_state_name)  # 设置新状态

    def set_state(self, new_state_name):
        """  执行状态 """
        if self.active_state is not None:
            self.active_state.exit_actions()  # 执行旧退出动作
        self.active_state = self.states[new_state_name]  # 更改有效状态
        self.active_state.entry_actions()  # 执行新状态进入动作


class World(object):
    """通过sprite.group的形式控制世界中的所有实体
    具体通过操纵sprite.group.spritedict来实现
    实质是通过操纵字典实现"""

    def __init__(self):
        self.entities_group = pygame.sprite.Group()

    def add_entity(self, entity):
        """增加一个新的实体"""
        self.entities_group.add(entity)

    def remove_entity(self, entity):
        """删除实体 """
        self.entities_group.remove(entity)

    def get_entity(self, entity_id):
        """通过key给出实体，没有的话返回None"""
        return self.entities_group.sprites()[entity_id]

    def process(self, time_passed):
        """ 通过实体自身的update处理世界中的每一个实体 """
        time_passed_seconds = time_passed / 100.0  # 之前设置的是1000
        self.entities_group.update(time_passed_seconds)

    def render(self, screen):
        """ 通过实体自身的render绘制背景和每一个实体 """
        for entity in self.entities_group.sprites():
            entity.render(screen)

    def get_close_entity(self, name, location, range=SEARCH_RANGE):
        """
        寻找一个固定范围内的特定实体"
        :param name: 被寻找的实体的名称
        :param location: 寻找者的位置
        :param range: 寻找者搜索范围
        :return:当前时刻范围内符合条件的所有实体
        """
        location = Vec2d(*location)  # 解析搜索者位置
        for entity in self.entities_group.sprites():
            if entity.name == name:
                distance = location.get_distance(entity.location)  # 得到搜索者与目标的距离
                if distance < range and distance != 0:  # 判断距离是否在搜索范围内
                    return entity
        return None

    def get_radar_search(self, tank, range=SEARCH_RANGE):
        """
        坦克寻找一个范围内的敌方单位"
        :param name: 被寻找的实体的名称
        :param location: 寻找者的位置
        :param range: 寻找者搜索范围
        :return:当前时刻范围内符合条件的所有实体
        """
        location = Vec2d(*tank.location)  # 解析搜索者位置
        teams = []
        enemies = []
        search_result = [teams, enemies]
        for entity in self.entities_group.sprites():
            if entity.name == 'tank':
                distance = location.get_distance(entity.location)  # 得到搜索者与目标的距离
                if distance < range and distance != 0:  # 判断距离是否在搜索范围内
                    if tank.team == entity.team:
                        teams.append(entity)  # 队友
                    else:
                        enemies.append(entity)  # 敌人
        return search_result


class BaseGameEntity(pygame.sprite.Sprite):
    """实体基类
    继承于pygame.sprite
    实体具有独立的名称、图像、位置、大脑（有限状态机）以及对世界的感知等特性"""

    def __init__(self, world, name, image):
        super().__init__()
        self.world = world  # 感知世界
        self.name = name  # 名字
        self.image = image.convert_alpha()  # 图像
        self.location = Vec2d(0, 0)  # 位置
        self.id = 0  # 编号

    def render(self, screen):
        """绘制实体"""
        screen.blit(self.image, self.location)


class Tank(BaseGameEntity):
    """游戏坦克智能体
    继承自实体基类"""

    def __init__(self, world, name, image, team):
        BaseGameEntity.__init__(self, world, name, image)  # 执行基类构造方法
        self.rect = self.image.get_rect()
        self.destination = Vec2d(0, 0)  # 目标位置
        self.brain = StateMachine()  # 有限状态机
        self.speed = 0  # 速度
        self.team = team  # 编组
        self.radar = []  # 雷达
        self.enemy_id = None
        self.bombs = pygame.sprite.Group()  # 导弹组
        self.memory = {}  # 记忆搜索过的位置

        # 创建坦克智能体状态
        seeking_state = TankStateSeeking(self)  # 靠近
        avoiding_state = TankStateAvoiding(self)  # 避障
        exploring_state = TankStateExploring(self)  # 搜索
        hunting_state = TankStateHunting(self)  # 追击
        hiding_state = TankStateHiding(self)  # 躲避

        # 将状态添加至智能体有限状态机
        self.brain.add_state(seeking_state)
        self.brain.add_state(avoiding_state)
        self.brain.add_state(exploring_state)
        self.brain.add_state(hunting_state)
        self.brain.add_state(hiding_state)

    def update(self, time_elapsed):
        """ 移动实体，先通过有限状态机进行思考，之后执行移动操作 """
        # 通过有限状态机判断是否修改状态
        self.brain.think()

        # 移动
        if self.speed > 0. and self.location != self.destination:
            vec_to_destination = self.destination - self.location  # 计算向量形式的距离
            distance_to_destination = vec_to_destination.get_length()  # 通过向量差计算实际距离
            heading = vec_to_destination.get_normalized()  # 计算向量形式距离的单位向量
            travel_distance = min(distance_to_destination, time_elapsed * self.speed)  # 取计算距离与v * t的最小值
            self.location += heading * travel_distance  # 通过修改自身位置实现移动

            self.rect.top = self.location[1]
            self.rect.left = self.location[0]


class Grass(BaseGameEntity):
    """草地，继承自实体基类"""

    def __init__(self, world, image):
        BaseGameEntity.__init__(self, world, 'grass', image)


class River(BaseGameEntity):
    """河流，继承自实体基类"""

    def __init__(self, world, image):
        BaseGameEntity.__init__(self, world, 'river', image)


class Brick(BaseGameEntity):
    """砖块，继承自实体基类"""

    def __init__(self, world, image):
        BaseGameEntity.__init__(self, world, 'brick', image)


class Bomb(pygame.sprite.Sprite):
    """炸弹，继承自精灵类"""

    def __init__(self, pos):
        super().__init__()
        self.image = pygame.image.load('resources/bomb.png').convert_alpha()
        self.rect = self.image.get_rect(left=pos[0] + 15, top=pos[1] + 15)

    def update(self, enemy_loaction, tank_loaction):
        bomb_direction = enemy_loaction - tank_loaction
        bomb_direction = bomb_direction.get_normalized()
        bomb_direction = bomb_direction * 10

        self.rect.move_ip(bomb_direction[0], bomb_direction[1])  # move_ip 直接改变对象   move 还返回一个改变后的对象

        if self.rect.top > SCREEN_SIZE[1] \
                or self.rect.bottom < 0 \
                or self.rect.left > SCREEN_SIZE[0] \
                or self.rect.right < 0:
            self.kill()


class TankStateSeeking(State):
    """坦克靠近动作"""

    def __init__(self, tank):
        State.__init__(self, 'seeking')
        self.tank = tank

    def check_conditions(self):
        """检查状态"""
        target_agent = self.tank.world.get_entity(self.tank.target_id)
        if target_agent is None:
            return 'exploring'

    def entry_actions(self):
        """靠近状态进入动作"""
        target_agent = self.tank.world.get_entity(self.tank.target_id)  # 依据目标id得到目标实体
        if target_agent is not None:
            self.tank.destination = target_agent.location  # 设置目的地
            self.tank.speed = 100.  # 设置移动速度


class TankStateAvoiding(State):
    """坦克避障动作"""


    def __init__(self, tank):
        State.__init__(self, 'avoiding')
        self.tank = tank

    def check_conditions(self):
        """检查状态"""
        # target_agent = self.tank.world.get_entity(self.tank.target_id)
        # if target_agent is None:
        #     return 'exploring'
        # if target_agent.location.get_distance(self.tank.location) > AVOID_RANGE:
        #     return 'exploring'

    # def entry_actions(self):
    #     """避障状态进入动作"""
    #     target_agent = self.tank.world.get_entity(self.tank.target_id)  # 依据目标id得到目标实体
    #     if target_agent is not None:
    #         self.tank.destination = self.tank.location - (target_agent.location - self.tank.location)  # 设置目的地
    #         print("坦克坐标("  ,'%.2f'%self.tank.location[0] ,"," ,'%.2f'%self.tank.location[1] ,")")
    #         print("目标坐标(" , '%.2f'%target_agent.location[0] , "," , '%.2f'%target_agent.location[1] , ")")
    #         print("目的地坐标(" , '%.2f'%self.tank.destination[0] , "," , '%.2f'%self.tank.destination[1] , ")")
    #         self.tank.speed = 1.  # 设置移动速度
        global LotoDe
        if self.tank.location == LotoDe:
            return 'exploring'


    def entry_actions(self):
        pass

    def do_actions(self):
        global VoidState
        global LotoDe


        if self.tank.location == self.tank.destination:
            VoidState = (VoidState +1) % 4

            if (LotoDe[0]>=0 and LotoDe[0]<=400 and LotoDe[1]==250 and VoidState == 0) or (LotoDe[1]>=550 and LotoDe[1]<=700 and LotoDe[0]==450 and VoidState == 1) or (LotoDe[0]>=500 and LotoDe[0]<=900 and LotoDe[1]==250 and VoidState == 1) or (LotoDe[1]>=0 and LotoDe[1]<=200 and LotoDe[0]==450 and VoidState == 2):
                pass
            elif self.RightTo():
                self.tank.destination = LotoDe
                VoidState =4

        if not VoidState == 4:
            for i in range(0,4):
                if VoidState == i:
                    self.tank.destination = zhangai[i]

    def RightTo(self):  # 判断能否直接去目的地
        global VoidState
        zhangai1 = self.tank.location
        zhangai2 =Vec2d(zhangai1[0]+50,zhangai1[1]+50)

        global LotoDe

        x1 = LotoDe[0]
        y1 = LotoDe[1]
        x0 = zhangai1[0]
        y0 = zhangai1[1]
        x00 = zhangai2[0]
        y00 = zhangai2[1]

        datax1 = x1 - x0
        datax2 = x1 - x00

        # if (LotoDe[0] == 450 and LotoDe[1] < 250) or(LotoDe[0] == 450 and LotoDe[1] >= 550) or(LotoDe[0] == 500 and LotoDe[1] < 250) or (LotoDe[0] == 500 and LotoDe[1] >= 550)or (LotoDe[0] < 450 and LotoDe[1] == 250) or(LotoDe[0] >= 500 and LotoDe[1] == 250)or(LotoDe[0] < 450 and LotoDe[1] == 550)or(LotoDe[0] >= 500 and LotoDe[1] == 550):
        #     return False
        if datax1 == 0 or datax2 ==0 :
            return True

        if (y1 -y0) == 0:
            return True
        mm1 = int(zhangai1[1] + ((y1 -y0)/datax1) * (450 - zhangai1[0] ))
        mm2 = int(zhangai1[1] + ((y1 -y0)/datax1) * (500 - zhangai1[0] ))
        nn1 = int(zhangai2[1] + ((y1 -y00)/datax2) * (450 - zhangai2[0] ))
        nn2 = int(zhangai2[1] + ((y1 -y00)/datax2) * (500 - zhangai2[0] ))
        print(mm1,mm2,nn1,nn2)

        if((mm1<=250 and mm2<=250 and nn1<=250 and nn2<=250) or (mm1>=550 and mm2>=550 and nn1>550 and nn2>550) ):
            return True

        return  False






class TankStateExploring(State):
    """坦克的探索策略"""

    def __init__(self, tank):
        State.__init__(self, 'exploring')
        self.tank = tank
    def trans(self):
        if not self.tank.memory:
            self.tank.speed = 100
            self.random_destination()
        else:
            i = random.randint(0, 9)
            if i < 3:
                self.tank.destination = random.sample(self.tank.memory.values(), 1)
            else:
                target_entity = self.tank.world.get_close_entity(self, 'brick', self.tank.location, range=SEARCH_RANGE)
                if target_entity is not None and target_entity.id not in self.tank.memory:
                    self.tank.destination = target_entity.location
                    self.tank.memory[target_entity.id] = target_entity.location
                else:
                    target_agent = self.tank.world.get_close_entity(self, 'river', self.tank.location,
                                                                    range=SEARCH_RANGE)
                    if target_agent is not None and target_agent.id not in self.tank.memory:
                        self.tank.destination = target_agent.location
                        self.tank.memory[target_agent.id] = target_agent.location

    def random_destination(self):
        """设置随机目的地"""
        m = self.check_random()   # m 是目的地
        if m != None:
            (x,y) = m
            global cishu
            cishu += 1
            print("第",cishu,"个目的地")
            print((x , y))
            self.tank.destination = Vec2d(x,y)

            # 保存目的地
            global LotoDe
            LotoDe = Vec2d(x,y)

    def check_random(self):
        global cishu
        if cishu == 279:
            return None
        r = np.random.randint(1, 280-cishu)
        r= position_all[r-1]
        position_all.remove(r)
        print("r：", r)
        y = int(r/19)

        x = r%19
        if r%19 ==0 :
            x = 19

        x = x*50 -50

        if r!=0 and r%19==0:
            y = y-1
        y = y*50
        print((x, y))
        return (x,y)


    def do_actions(self):
        """执行随机移动，更新移动位置，同时寻找敌方"""

        if self.tank.destination == self.tank.location:
            if np.random.randint(1, 20) == 1:  #20分之一的概率
               self.random_destination()

        # 寻找敌方
        self.tank.radar = self.tank.world.get_radar_search(self.tank)
        if len(self.tank.radar[1]) > 0:  # 找到了敌人
            self.tank.enemy_id = self.tank.radar[1][0].id  # 锁定搜索到的第一个敌方

    def check_conditions(self):
        """检查状态"""
        # 坦克策略
        if len(self.tank.radar[1]) == 1:  # 雷达内只有一个目标，追击
            return 'hunting'
        if len(self.tank.radar[1]) > 1:  # 雷达内大于一个目标，躲避
            return 'hiding'

        # 躲避障碍
        # target_agent = self.tank.world.get_close_entity('tank', self.tank.location, range=AVOID_RANGE)
        # if target_agent is not None:
        #     pass
        #
        # target_agent = self.tank.world.get_close_entity('brick', self.tank.location, range=AVOID_RANGE)
        # if target_agent is not None:
        #     self.tank.target_id = target_agent.id  # 锁定目标
        #     return 'avoiding'
        # target_agent = self.tank.world.get_close_entity('river', self.tank.location, range=AVOID_RANGE)
        # if target_agent is not None:
        #     self.tank.target_id = target_agent.id  # 锁定目标
        #     return 'avoiding'

        # if int(self.tank.location[0]) == (462 - 50) and int(self.tank.location[1])>=(238 - 50) and int(self.tank.location[1]) <= (488+50) :
        #     return 'avoiding'
        # if int(self.tank.location[0]) == (562) and int(self.tank.location[1])>=(238 - 50) and int(self.tank.location[1]) <= (488+50) :
        #     return 'avoiding'
        # if int(self.tank.location[1]) == (238 - 50) and int(self.tank.location[0])>=(462 - 50) and int(self.tank.location[0]) <= (562) :
        #     return 'avoiding'
        # if int(self.tank.location[1]) == (538) and int(self.tank.location[0])>=(462 - 50) and int(self.tank.location[0]) <= (562) :
        #     return 'avoiding'

        # if int(self.tank.location[0]) >= (412-5) and int(self.tank.location[0]) <= (412+5) and int(self.tank.location[1])>=(188-5) and int(self.tank.location[1]) <= (538+5) :
        #     print(1)
        #     return 'avoiding'
        # if int(self.tank.location[0]) >= (562-5) and int(self.tank.location[0]) <= (562+5) and int(self.tank.location[1])>=(188-5) and int(self.tank.location[1]) <= (538+5) :
        #     print(2)
        #     return 'avoiding'
        # if int(self.tank.location[1]) >= (188-5) and int(self.tank.location[1]) <= (188+5) and int(self.tank.location[0])>=(412-5) and int(self.tank.location[0]) <= (562+5) :
        #     print(3)
        #     return 'avoiding'
        # if int(self.tank.location[1]) >= (538-5) and int(self.tank.location[1]) <= (538+5) and int(self.tank.location[0])>=(412-5) and int(self.tank.location[0]) <= (562+5) :
        #     print(4)
        #     return 'avoiding'

        global VoidState
        if int(self.tank.location[0]) >= (400-5) and int(self.tank.location[0]) <= (400+5) and int(self.tank.location[1])>=(200-5) and int(self.tank.location[1]) <= (550+5) :
            VoidState = 1
            return 'avoiding'
        if int(self.tank.location[0]) >= (500-5) and int(self.tank.location[0]) <= (500+5) and int(self.tank.location[1])>=(200-5) and int(self.tank.location[1]) <= (550+5) :
            VoidState = 3
            return 'avoiding'
        if int(self.tank.location[1]) >= (200-5) and int(self.tank.location[1]) <= (200+5) and int(self.tank.location[0])>=(400-5) and int(self.tank.location[0]) <= (500+5) :
            VoidState = 0
            return 'avoiding'
        if int(self.tank.location[1]) >= (550-5) and int(self.tank.location[1]) <= (550+5) and int(self.tank.location[0])>=(400-5) and int(self.tank.location[0]) <= (500+5) :
            VoidState = 2
            return 'avoiding'

        #   4         (400,200)   (500,200)
        # 1   3
        #   2         (400,550)   (500,550)
        #
        # 写如何判断遇到了障碍物


        return None

    def entry_actions(self):
        """探索策略进入动作"""
        self.tank.speed = 30.
        self.random_destination()


class TankStateHiding(State):
    """坦克的躲避动作"""

    def __init__(self, tank):
        State.__init__(self, 'hiding')
        self.tank = tank

    def do_actions(self):
        """执行躲避"""
        if self.tank.enemy_id is not None:
            enemy = self.tank.world.get_entity(self.tank.enemy_id)  # 锁定躲避目标
            if enemy is not None:
                self.tank.destination = self.tank.location - (enemy.location - self.tank.location)  # 设置目的地

    def check_conditions(self):
        """检查状态"""
        # 坦克策略
        self.tank.radar = self.tank.world.get_radar_search(self.tank)
        if len(self.tank.radar[1]) == 0:  # 雷达内没有目标，探索
            return 'exploring'
        if len(self.tank.radar[1]) == 1:  # 雷达内只有一个目标，追击
            return 'hunting'

        # 躲避障碍
        target_agent = self.tank.world.get_close_entity('brick', self.tank.location, range=AVOID_RANGE)
        if target_agent is not None:
            self.tank.target_id = target_agent.id  # 锁定目标
            return 'avoiding'
        target_agent = self.tank.world.get_close_entity('river', self.tank.location, range=AVOID_RANGE)
        if target_agent is not None:
            self.tank.target_id = target_agent.id  # 锁定目标
            return 'avoiding'

    def entry_actions(self):
        """远离状态进入动作"""
        self.tank.speed = 150.  # 设置移动速度


class TankStateHunting(State):
    """坦克的追击策略"""

    def __init__(self, tank):
        State.__init__(self, 'hunting')
        self.tank = tank

    def do_actions(self):
        """执行追击"""
        if self.tank.enemy_id is not None:
            enemy = self.tank.world.get_entity(self.tank.enemy_id)  # 获取追击目标
            self.tank.destination = enemy.location
            # # 攻击
            if np.random.randint(1, 30) == 1:
                bomb = Bomb(self.tank.location)
                self.tank.bombs.add(bomb)

    def check_conditions(self):
        """检查状态"""
        # 坦克策略
        self.tank.radar = self.tank.world.get_radar_search(self.tank)
        if len(self.tank.radar[1]) == 0:  # 雷达内没有目标，探索
            return 'exploring'
        if len(self.tank.radar[1]) > 1:  # 敌方人数大于1个
            return 'hiding'

        # 躲避障碍
        target_agent = self.tank.world.get_close_entity('brick', self.tank.location, range=AVOID_RANGE)
        if target_agent is not None:
            self.tank.target_id = target_agent.id  # 锁定目标
            return 'avoiding'
        target_agent = self.tank.world.get_close_entity('river', self.tank.location, range=AVOID_RANGE)
        if target_agent is not None:
            self.tank.target_id = target_agent.id  # 锁定目标
            return 'avoiding'

    def entry_actions(self):
        """追击策略进入动作"""
        self.tank.speed = 1000.


class TankStateTeaming(State):
    """坦克编组动作"""

    def __init__(self, tank):
        State.__init__(self, 'seeking')
        self.tank = tank

    def check_conditions(self):
        """检查状态"""
        target_agent = self.tank.world.get_entity(self.tank.target_id)
        if target_agent is None:
            return 'exploring'

    def entry_actions(self):
        """靠近状态进入动作"""
        target_agent = self.tank.world.get_entity(self.tank.target_id)  # 依据目标id得到目标实体
        if target_agent is not None:
            self.tank.destination = target_agent.location  # 设置目的地
            self.tank.speed = 100.  # 设置移动速度


class Game():
    def __init__(self):
        """初始化游戏参数"""
        pygame.init()
        self.screen_width, self.screen_height = SCREEN_SIZE
        self.screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
        pygame.display.set_caption('Tank War Ⅱ')

        # 初始化世界, 时钟, 随机种子
        self.world = World()
        self.clock = pygame.time.Clock()
        # np.random.seed(1)
        # 加载图像
        grass_image = pygame.image.load('resources/grass.png')
        river_image = pygame.image.load('resources/river.png')
        brick_image = pygame.image.load('resources/brick.png')

        tank_scout_white_image = pygame.image.load('resources/MBT61.png')
        tank_battle_white_image = pygame.image.load('resources/指挥者.png')
        tank_support_white_image = pygame.image.load('resources/月面行者支援型.png')
        tank_scout_blue_image = pygame.image.load('resources/巨蜥.png')
        tank_battle_blue_image = pygame.image.load('resources/雷兽.png')
        tank_support_blue_image = pygame.image.load('resources/沙漠军团.png')

        # brick = Brick(self.world, self.brick_image)
        # brick.location = Vec2d(359, 359)
        # self.world.add_entity(brick)
        #
        # river = River(self.world, self.river_image)
        # river.location = Vec2d(615, 359)
        # self.world.add_entity(river)

        # brick_pos = [Vec2d(206, 71), Vec2d(256, 71), Vec2d(306, 71), Vec2d(356, 71),
        #              Vec2d(231, 597), Vec2d(231, 647),
        #              Vec2d(743, 71), Vec2d(743, 121),
        #              Vec2d(618, 647), Vec2d(668, 647), Vec2d(718, 647), Vec2d(768, 647)]
        #
        # river_pos = [Vec2d(450, 250), Vec2d(450, 300), Vec2d(450, 350), Vec2d(450, 400),
        #              Vec2d(450, 450), Vec2d(450, 500), Vec2d(500, 250), Vec2d(500, 300),
        #              Vec2d(500, 350), Vec2d(500, 400), Vec2d(500, 450), Vec2d(500, 500)]


        river_pos = [Vec2d(450, 250), Vec2d(450, 300), Vec2d(450, 350), Vec2d(450, 400),
                     Vec2d(450, 450), Vec2d(450, 500)]
        brick_pos = []
        #river_pos = []
        entity_id = 0
        self.brick_group = pygame.sprite.Group()
        #草地实例化

        # for y in range(8):
        #     grass = Grass(self.world, grass_image)
        #     grass.id = entity_id
        #     grass.location = Vec2d(x * 128, y * 96)
        #     self.world.add_entity(grass)
        #     entity_id += 1

        for x in range(int(self.screen_width / 100) + 1):
            for y in range(int(self.screen_height / 100) + 1):
                grass = Grass(self.world, grass_image)
                grass.location = Vec2d(x * 100, y * 100)
                self.world.add_entity(grass)
                entity_id += 1

        print("草地",entity_id)
        # 砖块实例化
        for pos in brick_pos:
            brick = Brick(self.world, brick_image)
            brick.id = entity_id
            brick.location = pos
            self.world.add_entity(brick)
            entity_id += 1

        print("砖块",entity_id)
        # 河流实例化
        for pos in river_pos:
            river = River(self.world, river_image)
            river.id = entity_id
            river.location = pos
            self.world.add_entity(river)
            entity_id += 1

        print("河流",entity_id)
        # 实例化坦克 # 哈哈
        # self.tank_scout_white = Tank(self.world, 'tank', tank_scout_white_image, 'white')
        # self.tank_scout_white.id = entity_id
        # self.tank_scout_white.location = Vec2d(78, 167)
        # self.tank_scout_white.brain.set_state('exploring')
        # self.world.add_entity(self.tank_scout_white)
        # entity_id += 1

        self.tank_battle_white = Tank(self.world, 'tank', tank_battle_white_image, 'white')
        self.tank_battle_white.id = entity_id
        #self.tank_battle_white.location = Vec2d(78, 359)
        #self.tank_battle_white.location = Vec2d(0, 0)
        #self.tank_battle_white.location = Vec2d(900, 0)
        #elf.tank_battle_white.location = Vec2d(0, 700)
        self.tank_battle_white.location = Vec2d(900, 700)

        self.tank_battle_white.brain.set_state('exploring')
        self.world.add_entity(self.tank_battle_white)
        entity_id += 1
        # 哈哈
        # self.tank_support_white = Tank(self.world, 'tank', tank_support_white_image, 'white')
        # self.tank_support_white.id = entity_id
        # self.tank_support_white.location = Vec2d(78, 551)
        # self.tank_support_white.brain.set_state('exploring')
        # self.world.add_entity(self.tank_support_white)
        # entity_id += 1
        # 哈哈
        # self.tank_scout_blue = Tank(self.world, 'tank', tank_scout_blue_image, 'blue')
        # self.tank_scout_blue.id = entity_id
        # self.tank_scout_blue.location = Vec2d(896, 167)
        # self.tank_scout_blue.brain.set_state('exploring')
        # self.world.add_entity(self.tank_scout_blue)
        # entity_id += 1



        # self.tank_battle_blue = Tank(self.world, 'tank', tank_battle_blue_image, 'blue')
        # self.tank_battle_blue.id = entity_id
        # self.tank_battle_blue.location = Vec2d(896, 359)
        # self.tank_battle_blue.brain.set_state('exploring')
        # self.world.add_entity(self.tank_battle_blue)
        # entity_id += 1



        # 哈哈
        # self.tank_support_blue = Tank(self.world, 'tank', tank_support_blue_image, 'blue')
        # self.tank_support_blue.id = entity_id
        # self.tank_support_blue.location = Vec2d(896, 551)
        # self.tank_support_blue.brain.set_state('exploring')
        # self.world.add_entity(self.tank_support_blue)
        # entity_id += 1
        print(entity_id)

    def run(self):
        """执行游戏"""
        while True:

            global LotoDe

            self.screen.fill(0)  # 重绘前刷新屏幕

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            time_passed = self.clock.tick(100)  # 设置更新时间

            self.world.process(time_passed)
            self.world.render(self.screen)
            pygame.draw.circle(self.screen, (255, 255, 0), LotoDe, 10, 10)
            # pygame.sprite.spritecollide(self.tank_battle_white.bombs, self.brick_group, True)

            if len(self.tank_battle_white.bombs) != 0:
                if self.tank_battle_white.enemy_id is not None:
                    self.tank_battle_white.bombs.draw(self.screen)
                    enemy_location = self.world.get_entity(self.tank_battle_white.enemy_id).location
                    self.tank_battle_white.bombs.update(enemy_location, self.tank_battle_white.location)

                # if pygame.sprite.spritecollideany(self.tank_scout_blue, self.tank_battle_white.bombs):
                #     self.tank_battle_white.enemy_id = None
                #     self.tank_battle_white.radar.clear()
                #     self.world.remove_entity(self.tank_scout_blue)
                if pygame.sprite.spritecollideany(self.tank_battle_blue, self.tank_battle_white.bombs):
                    self.tank_battle_white.enemy_id = None
                    self.tank_battle_white.radar.clear()
                    self.world.remove_entity(self.tank_battle_blue)
                # 哈哈
                if pygame.sprite.spritecollideany(self.tank_battle_white, self.tank_battle_blue.bombs):  # 这个函数的意思就是 碰撞之后删除
                    self.tank_battle_blue.enemy_id = None
                    self.tank_battle_blue.radar.clear()
                    self.world.remove_entity(self.tank_battle_white)

                # if pygame.sprite.spritecollideany(self.tank_support_blue, self.tank_battle_white.bombs):
                #     self.tank_battle_white.enemy_id = None
                #     self.tank_battle_white.radar.clear()
                #     self.world.remove_entity(self.tank_support_blue)

            pygame.display.update()


if __name__ == '__main__':
    """游戏入口"""
    Game().run()
    """bug1: Tank击败对方tank之后此tank后面发出来的子弹消失
       bug2；Tank出现卡在墙上或者河流上之后不动的情形   
       bug3: 只有白方其中的一个tank可以发子弹
       bug4: 击败tank后不能从屏幕上消失
       bug5: 子弹拐弯问题

       bug1问题，每个tank的子弹是封装在一个组里面，因此，当一个子弹要毁灭是，会删除本组的子弹
       bug2问题，河流和砖块并不是过不去，而是Tank检测到敌方Tank之后，同时又检测到障碍物，
       检测障碍物时会后退，而检测到敌方Tank时执行追击状态
       bug3问题，未初始化完成，
       bug5问题，在Bomb类中的update函数中子弹的方向为‘敌机位置-友机位置’，
       两个tank的方向在变，子弹的方向随之而变，出现子弹拐弯问题
       """

