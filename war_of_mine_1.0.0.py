import pygame
from vector2 import Vec2d as v
from sys import exit
from random import randint
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans
import threading

class StateMachine(object):
    def __init__(self):
        self.states = {}
        self.active_state = None

    def add_state(self, state):
        self.states[state.name] = state

    def think(self):
        if self.active_state is None:
            return
        self.active_state.do_actions()
        new_state_name = self.active_state.check_conditions()
        if new_state_name is not None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):
        if self.active_state is not None:
            self.active_state.exit_actions()
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()

class GameEntity(pygame.sprite.Sprite):
    def __init__(self, world, name, image, *groups):
        super().__init__(*groups)
        self.world = world 
        self.name = name
        self.image = image
        self.location = v(0,0)
        self.destination = v(0,0)
        self.speed = 0.
        self.brain = StateMachine()
        self.id = 0

    def draw(self, surface):
        x, y = self.location
        w, h = self.image.get_size()
        surface.blit(self.image,(x-w/2,y-h/2))

    def process(self, time_passed):
        self.brain.think()
        if self.speed > 0 and self.location != self.destination:
            vec_to_destination = self.destination - self.location
            distance_to_destination = vec_to_destination.get_length()
            heading = vec_to_destination.get_normalized()
            travel_distance = min(distance_to_destination, time_passed * self.speed)
            self.location += travel_distance * heading

class World(object):
    def __init__(self):
        self.entities = {}
        self.entity_id = 0
        self.groups = {}
        self.groups_id = 0
        self.background = pygame.image.load('./img/grass.jpg').convert()
    def add_entity(self, entity):
        # 增加一个新的实体
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1
    def add_group(self, group):
        self.groups[self.groups_id] = group
        self.groups_id += 1
    def remove_entity(self, entity):
        del self.entities[entity.id]
    def get(self, entity_id):
        # 通过id给出实体，没有的话返回None
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None
    def process(self, time_passed):
        # 处理世界中的每一个实体
        time_passed_seconds = time_passed / 1000.0
        for entity in self.entities.itervalues():
            entity.process(time_passed_seconds)
    def draw(self, screen):
        # 绘制背景和每一个实体
        screen.blit(self.background, (0, 0))
        for entity in self.entities.values():
            entity.draw(screen)
        for group in self.groups.values():
            group.draw(screen)
    def get_close_entity(self, name, location, range=100.):
        # 通过一个范围寻找之内的所有实体
        location = v(*location)
        for entity in self.entities.values():
            if entity.name == name:
                distance = location.get_distance_to(entity.location)
                if distance < range:
                    return entity
        return None

class Rock(GameEntity):
    def __init__(self,world,image,position):
        GameEntity.__init__(self,world,'rock',image)
        self.location = position
        self.rect = self.image.get_rect()       #※ 精灵图片的大小
        self.rect.topleft = position
        self.name = 'rock'
        long = self.rect.size[0]+randint(-1*randint(1,10),1*randint(1,10))*self.rect.size[0]*randint(1,200)*0.0001
        width = self.rect.size[1]+randint(-1*randint(1,10),1*randint(1,10))*self.rect.size[1]*randint(1,200)*0.0001
        s = long * width
        global rock_id
        id = rock_id
        self.datas = {'id':id,'long':long,'width':width,'s':s}
        rock_id += 1


class Tank(GameEntity):
    def __init__(self,world,image,position):
        GameEntity.__init__(self,world,'tank',image)
        self.barrier_flag = 0
        self.toward = 0 # 0为左
        self.search_data = []
        self.stop = 0
        self.step = 0
        self.step_wight = 0
        self.step_toward = 0
        self.step_flag = 0
        self.through = 0
        self.hight_barrier = 0
        self.wight_barrier = 0
        self.num = 0
        self.target = 0
        self.ka = 0
        self.ttt = 0
        self.location = position
        self.left_right_toward = 0 # 0为左 
        self.up_down_toward = 0 # 0为上
        self.rect = self.image.get_rect()       #※ 精灵图片的大小
        self.rect.topleft = position
        self.second = 3333
        self.temp1 = 0
        self.temp2 = 0
        self.temp3 = 0

    def left_move(self):
        if not self.stop:
            if self.step == 0:
                if self.toward == 1:
                    self.image = pygame.transform.flip(self.image, True, False)
                    self.toward = 0
                self.location = v(self.location[0]-self.speed*0.01,self.location[1])
            self.judge()

    def right_move(self):
        if not self.stop:
            if self.step == 0:
                if self.toward == 0:
                    self.image = pygame.transform.flip(self.image, True, False)
                    self.toward = 1
                self.location = v(self.location[0]+self.speed*0.01,self.location[1])
            self.judge()

    def up_move(self):
        if not self.stop:
            dic_collide = pygame.sprite.groupcollide(tank_group,rock_group,False,False)       
            if dic_collide:
                self.ka = 1
                self.location = v(self.location[0],self.location[1]+self.speed*0.01+self.speed*0.01)
                self.up_down_toward = 1
            else:
                self.ka = 0
            self.location = v(self.location[0],self.location[1]-self.speed*0.01)
            self.judge()

    def down_move(self):
        if not self.stop:
            dic_collide = pygame.sprite.groupcollide(tank_group,rock_group,False,False)       
            if dic_collide:
                self.ka = 1
                self.location = v(self.location[0],self.location[1]-self.speed*0.01-self.speed*0.01)
                self.up_down_toward = 0
            else:
                self.ka = 0
            self.location = v(self.location[0],self.location[1]+self.speed*0.01)
            self.judge()
    
    def update(self):
        self.rect.left, self.rect.top = self.location[0] - self.image.get_width() / 2,self.location[1] - self.image.get_height() / 2
        # self.rect.topleft = self.location

    def judge(self):
        self.random_move()
        if self.location[0]<0:
            self.location[0] += self.speed*0.01+1
            self.num = 1
            self.left_right_toward = 1

        if self.location[0] > 1200:
            self.location[0] -= self.speed*0.01+1
            self.num = 1
            self.left_right_toward = 0
            self.down_move()

        if self.location[1] <0:
            self.location[1] += self.speed*0.01+1
            self.up_down_toward = 0
            self.step_toward = 0

        if self.location[1] >700:
            self.location[1] -= self.speed*0.01+1
            self.up_down_toward = 1
            self.step_toward = 1

    def search(self):
        
        dic_collide = pygame.sprite.groupcollide(tank_group,rock_group,False,False)
        # for i in dic_collide:
        #     rock_group.remove(dic_collide[i])
        if dic_collide:
            if self.left_right_toward == 1:
                self.left_move()
            else:
                self.right_move()

            self.barrier(dic_collide)
            global text_1_
            for i in dic_collide:
                if not sprite.search_data:
                    sprite.search_data.append(dic_collide[i][0].datas)

                    self.target += 1
                    temp = 'un known'
                    if sprite.temp1 != 0 and sprite.temp2 != 0 and sprite.temp3 !=0:
                        s = dic_collide[i][0].datas['s']
                        a1 = abs(s-sprite.temp1)
                        a2 = abs(s - sprite.temp2)
                        a3 = abs(s - sprite.temp3)
                        if a1<=a2 and a1<=a3:
                            temp = 'type1'
                        else:
                            if a2<=a3 and a2<=a1:
                                temp = 'type2'
                            else:
                                if a3<=a1 and a3<=a2:
                                    temp = 'type3'

                    text_1_ = 'Found new stone : Num' + str(self.target) + " type: " + temp
                else:
                    if dic_collide[i][0].datas not in sprite.search_data:
                        sprite.search_data.append(dic_collide[i][0].datas)
                        self.target += 1
                        temp = ''
                        if sprite.temp1 != 0 and sprite.temp2 != 0:
                            s = dic_collide[i][0].datas['s']
                            if s <= sprite.temp1:
                                temp = 'type1'
                            else:
                                if s < sprite.temp2:
                                    temp = 'type2'
                                else:
                                    temp = 'type3'

                        text_1_ = 'Found new stone : Num' + str(self.target) + " type: " + temp
                # for j in rocks:
                #     if dic_collide[i][0] == j:
                #         name = j.name + str(rocks.index(j)+1)
                #         if name not in sprite.search_data:
                #             # data = {}
                #             # data['rect_size']  = j.rect.size
                #             # data['location'] = j.location
                #             # sprite.search_data[name] = data
                #             # global text_1_
                #             # self.target += 1
                #             # size = " long:" + str(j.rect.size[0]) + " width:" + str(j.rect.size[0])
                #             # pos = " position:(" + str(j.location[0])+","+str(j.location[1])+")"
                #             text_1_ = 'Found new stone : Num' + str(rocks.index(j)+1) + size + pos
            global zzz
            zzz += 1

        if self.num == 0:
            if self.left_right_toward == 0:
                self.left_move()
            else:
                self.right_move()
        else:
            if self.up_down_toward == 0:
                if self.ka == 0:
                    self.down_move()
                else:
                    self.ttt += 1
                    if self.ttt > 20:
                        self.ka = 0
                        self.ttt = 0
            else:
                if self.ka == 0:
                    self.ttt += 1
                    self.up_move()
                else:
                    self.ttt += 1
                    if self.ttt >20:
                        self.ka = 0
                        self.ttt = 0
            self.num += 1
            if self.num == 20:
                self.num = 0
        if self.step > 0:
            if self.step_toward == 0:
                self.down_move()
            else:
                self.up_move()
            self.step += 1
            if (self.step)*self.speed*0.01 > self.hight_barrier-20:
                self.step = 0
                self.step_flag = 0

    def barrier(self,collide):
        for i in collide:
            if collide[i][0].datas in sprite.search_data:
                self.hight_barrier = collide[i][0].rect.size[1]
                self.wight_barrier = collide[i][0].rect.size[0]
                global text_1_
                temp = ''

                if sprite.temp1 != 0 and sprite.temp2 != 0:
                    s = collide[i][0].datas['s']
                    if s <= sprite.temp1:
                        temp = 'type1'
                    else:
                        if s < sprite.temp2:
                            temp = 'type2'
                        else:
                            temp = 'type3'
                text_1_ = 'Found stone : Num' + str(self.target) + ' Type: ' + temp
        if not self.step_flag:
            self.step_flag = 1
            self.step  += 1

    def random_move(self):
        if self.target >= 2:
            if randint(1, 100000) > 89800:
                for j in rocks:
                    rock_group.remove(j)
                rocks.clear()
                for m in range(3):
                    p = (randint(0, 1200), randint(0, 700))
                    rocks.append(Rock(world, rock[m], p))
                    rock_group.add(rocks[m])
            if self.ka == 0:
                if randint(1,1000000)>999000:
                    if self.up_down_toward == 0:
                        self.up_down_toward = 1
                    else:
                        self.up_down_toward = 0
                if randint(1,100000)>99900:
                    if self.left_right_toward == 0:
                        self.left_right_toward = 1
                    else:
                        self.left_right_toward = 0
            if self.target >2:
                if self.second%3333 == 0:
                    self.paint()
                self.second += 1

    def paint(self):
        thread_paint = myThread()
        thread_paint.start()


class myThread(threading.Thread):   #继承父类threading.Thread
    def __init__(self):
        super().__init__()

    def run(self):                   #把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        data = sprite.search_data
        res = []
        for i in data:
            d = []
            d.append(i['long'])
            d.append(i['width'])
            d.append(i['s']/1000)
            res.append(d)

        X = np.array(res)
        print("石块数据库：")
        print(X)
        y = []
        for i in range(0, len(X)):
            y.append(randint(0, 3))
        y = np.array(y)

        kmeans = KMeans(n_clusters=3)
        kmeans = kmeans.fit(X)
        C = kmeans.cluster_centers_

        fig = plt.figure()
        ax = Axes3D(fig)
        print("聚类结果：")
        print(C)
        sprite.temp1 = C[0][2]*1000
        sprite.temp2 = C[1][2]*1000
        sprite.temp3 = C[2][2] * 1000
        ax.scatter(X[:, 0], X[:, 1], X[:, 2], c=y)
        ax.scatter(C[:, 0], C[:, 1], C[:, 2], marker='^', c='red', s=500)
        plt.savefig('hello.png')
        print("图像已重新绘制")

zzz = 0
pygame.init()
screen = pygame.display.set_mode((1200,700),0,32)
pygame.display.set_caption("我的战争")
world = World()
rock_group = pygame.sprite.Group()


rock_id = 1
rock = []
for i in range(3):
    rock.append(pygame.image.load('./img/rock'+ str(i+1) + '.png').convert_alpha())
rocks = []
for i in range(3):
    # rocks.append(Rock(world, rock[i]))
    p = (randint(0,1200),randint(0,700))
    # p = (0,0)
    # if i == 0:
    #     p = (150,150)
    # if i == 1:
    #     p = (800,300)
    # if i == 2:
    #     p = (300,500)
    rocks.append(Rock(world, rock[i], p))
    rock_group.add(rocks[i])
       # rocks[i].location = v(p)



world.add_group(rock_group)
tank_group = pygame.sprite.Group()
sprite = pygame.image.load('./img/tank1.png').convert_alpha()
sprine = pygame
sprite_pos = v(0, 0)
sprite = Tank(world,sprite,sprite_pos)
sprite.speed = 800.
tank_group.add(sprite)
clock = pygame.time.Clock()
text_1_ = 'Patrolling……'
font = pygame.font.SysFont('宋体',40)


def run():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
        world.draw(screen)
        pressed_keys = pygame.key.get_pressed()
        sprite.search()
        # key_direction = v(0, 0)
        if pressed_keys[pygame.K_LEFT]:
            sprite.left_move()
        elif pressed_keys[pygame.K_RIGHT]:
            sprite.right_move()
        if pressed_keys[pygame.K_UP]:
            sprite.up_move()
        elif pressed_keys[pygame.K_DOWN]:
            sprite.down_move()
        # sprite.search() # 巡逻功能
        # key_direction.normalized()

        # screen.blit(sprite, sprite_pos)
        # sprite_pos += key_direction * sprite_speed * 0.01
        sprite.draw(screen)
        text_1 = font.render(text_1_, True, (200,200,23))
        screen.blit(text_1, (20, 5))
        tank_group.update()
        tank_group.draw(screen)
        pygame.display.update()


if __name__ == "__main__":
    run()
