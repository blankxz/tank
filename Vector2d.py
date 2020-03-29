"""2d vector class supports vector and scalar operators, and also provides a bunch of high-level functions"""

import math


class Vec2d(object):
    def __init__(self, x_or_pair, y=None):
        if y is None:
            self.x = x_or_pair[0]
            self.y = x_or_pair[1]
        else:
            self.x = x_or_pair
            self.y = y

    def __len__(self):
        return 2

    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError("Invalid subscript " + str(key) + " to Vec2d")

    def __setitem__(self, key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Invalid subscript " + str(key) + " to Vec2d")

    # String representaion (for debugging)
    def __repr__(self):
        return 'Vec2d(%s, %s)' % (self.x, self.y)

    def __add__(self, other):
        " 重载加法 "
        if isinstance(other, Vec2d):
            return Vec2d(self.x + other.x, self.y + other.y)
        elif hasattr(other, "__getitem__"):
            return Vec2d(self.x + other[0], self.y + other[1])
        else:
            return Vec2d(self.x + other, self.y + other)

    def __sub__(self, other):
        " 重载减法 "
        if isinstance(other, Vec2d):
            return Vec2d(self.x - other.x, self.y - other.y)
        elif hasattr(other, "__getitem__"):
            return Vec2d(self.x - other[0], self.y - other[1])
        else:
            return Vec2d(self.x - other, self.y - other)

    def __mul__(self, other):
        " 重载乘法 "
        if isinstance(other, Vec2d):
            # return Vec2d(self.x * other.x, self.y * other.y)
            return self.x * other.x + self.y * other.y
        elif hasattr(other, "__getitem__"):
            return Vec2d(self.x * other[0], self.y * other[1])
        else:
            return Vec2d(self.x * other, self.y * other)

    def __truediv__(self, other):
        " 重载除法 "
        if isinstance(other, Vec2d):
            return Vec2d(self.x / other.x, self.y / other.y)
        elif hasattr(other, "__getitem__"):
            return Vec2d(self.x / other[0], self.y / other[1])
        else:
            return Vec2d(self.x / other, self.y / other)

    def __eq__(self, other):
        """重载=="""
        if self.x == other.x and self.y == other.y:
            return True
        else:
            return False

    def __lt__(self, other):
        """重载>"""
        if self.x < other.x and self.y < other.y:
            return True
        else:
            return False

    def __gt__(self, other):
        """重载<"""
        if self.x > other.x and self.y >other.y:
            return True
        else:
            return False

    @classmethod
    def get_distance_to(cls, p1, p2):
        " 得到两点间距离的坐标形式 "
        return cls(p2[0] - p1[0], p2[1] - p1[1])

    def get_distance(self, other):
        " 得到实体与目标的距离 "
        return math.sqrt((self.x - other[0]) ** 2 + (self.y - other[1]) ** 2)

    def get_length(self):
        " 得到向量长度 "
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def get_normalized(self):
        " 得到单位向量 "
        length = self.get_length()
        if length == 0:
            length = 1
        self.x /= length
        self.y /= length
        return Vec2d(self)

    def get_dot(self, other):
        " 得到实体与目标的点积 "
        return float(self.x * other[0] + self.y * other[1])

    @classmethod
    def rectangle_detection(cls, point, rect1, rect2):
        """传入一个点和矩形对角的两个点，返回这个点是否在矩形内部"""
        rect_x = [rect1[0], rect2[0]]
        rect_x.sort()
        rect_y = [rect1[1], rect2[1]]
        rect_y.sort()
        print(rect_x, rect_y)
        print(point)
        if (rect_x[0] <= point.x <= rect_x[1]) and (rect_y[0] <= point.y <= rect_y[1]):
            return True
        else:
            return False


if __name__ == "__main__":
    a = Vec2d(1, 1)
    b = Vec2d(7, 7)
    c = Vec2d(3, 4)
    d = Vec2d(3, 4)
    d2 = Vec2d(*d)
    print(d2)
    ab = Vec2d.get_distance_to(a, b)
    print('a = ', a)
    print('b = ', b)
    print('ab = ', ab)
    print('ab + 1 = ', ab + 1)
    print('a + b = ', a + b)
    print('ab - 1 = ', ab - 1)
    print('a - b = ', a - b)
    print('ab * 2 = ', ab * 2.1)
    print('a * b = ', a * b)
    print('ab / 2 = ', ab / 2.2)
    print('a / b = ', a / b)
    print('ab.get_length = ', ab.get_length())
    print('ab.get_normalized = ', ab.get_normalized())
    print('c = ', c)
    print('c.get_length = ', c.get_length())
    print('c.get_distance = ', c.get_distance((0, 0)))
    print('c.get_normalized = ', c.get_normalized())
    print(Vec2d.rectangle_detection(d, a, b))