from selenium.webdriver.common.action_chains import ActionChains
import math
import numpy as np
import time
import random
from Code import Utilities as Util
from selenium.common.exceptions import WebDriverException

from selenium import webdriver


class BotInterface:
    """
    test here: https://codepen.io/falldowngoboone/pen/PwzPYv
    """

    def __init__(self, driver):
        self.driver = driver
        self.height = self.driver.get_window_size()['height']
        self.width = self.driver.get_window_size()['width']
        self.y_scroll_loc = 0
        self.x_scroll_loc = 0
        self.device_speed = 1

        self.x_mouse_loc = 0
        self.y_mouse_loc = 0

    def __str__(self):
        return f'cursor: ({self.x_mouse_loc}, {self.y_mouse_loc})\n' \
               f'scrol:({self.x_scroll_loc}, {self.y_scroll_loc}) '

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, n):
        n = int(n)
        if n > 0:
            self._height = n
        else:
            raise ValueError(f'{n} is not a valid height')

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, n):
        n = int(n)
        if n > 0:
            self._width = n
        else:
            raise ValueError(f'{n} is not a valid width')

    @property
    def y_scroll_loc(self):
        return self._y_scroll_loc

    @y_scroll_loc.setter
    def y_scroll_loc(self, y):
        if not (type(y) is int or type(y) is float):
            y = 0
        if y < 0: y = 0
        self._y_scroll_loc = y

    @property
    def x_scroll_loc(self):
        return self._x_scroll_loc

    @x_scroll_loc.setter
    def x_scroll_loc(self, x):
        self._x_scroll_loc = x

    @property
    def x_mouse_loc(self):
        return self._x_mouse_loc

    @x_mouse_loc.setter
    def x_mouse_loc(self, x):
        if x is None:
            x = random.randint(0, self.height)
        self._x_mouse_loc = x

    @property
    def y_mouse_loc(self):
        return self._y_mouse_loc

    @y_mouse_loc.setter
    def y_mouse_loc(self, y):
        if y is None:
            y = random.randint(0, self.width)
        self._y_mouse_loc = y

    @property
    def device_speed(self):
        return self._device_speed

    @device_speed.setter
    def device_speed(self, speed):
        self._device_speed = speed

    def mouse_deviation(self, loc_1, axis, allways_deviate, d):
        """
        :param loc_1: target location (loc_0 is the current mouse position in axis)
        :param axis: {'x','y'} indicates the axis
        :param allways_deviate: boolean, deviate along this axis even if there is not
                                much movement along it
        :param d: numeric, indicates the total diagonal distance (both axis)
        :return r: numeric

        Calculate a random deviation from the straight line along a specified axis
        """
        axis_dict = {'x': {'mouse': self.x_mouse_loc, 'limit': self.width},
                     'y': {'mouse': self.y_mouse_loc, 'limit': self.height}
                     }
        loc_0, lim = axis_dict[axis].values()
        if (dist := abs(loc_0 - loc_1)) > 4:
            min_loc = min(loc_1, loc_0) + dist / 4
            max_loc = min(loc_1, loc_0) + 3 * dist / 4
            r = int(random.uniform(min_loc, max_loc))
        elif allways_deviate:
            max_offset = int(np.ceil(d ** (3 / 4))) // 6
            min_offset = max_offset // 5
            offset = random.choice([-1, 1]) * random.randint(min_offset,
                                                             max_offset)
            r = loc_0 + offset
        else:
            r = loc_0
        r = Util.clamp(r, lim)
        return r

    def partial_mouse(self, x_goal, y_goal, fast=False):
        """
        Execute a mouse movement to (x_goal, y_goal)
        :param x_goal: numeric within (0, self.width) target x_val
        :param y_goal: numeric within (0, self.height)
        :param fast: when dist<100 speed will be doubled when fast == True
        :return: None

        """
        # restrict x_goal and y_goal to valid range
        x_goal = Util.clamp(x_goal, self.width)
        y_goal = Util.clamp(y_goal, self.height)

        # calculate diagonal distance for mouse to travel
        d = Util.dist(self.x_mouse_loc, x_goal, self.y_mouse_loc, y_goal)
        significant_movement = d > 10

        # calculate speed of mouse, uses an s curve with an aditional growth factor
        a = random.uniform(7, 10)
        b = random.uniform(4, 6)
        speed = (a / (1 + math.exp(-0.1 * (d - 100))) + math.sqrt(d / 4) + b)

        # n_jums is given by the inverse of speed times distance
        # uses 1 when distance is 0
        n_jumps = max(1, d) * (1 / speed)

        # speed up movement in case this is desired
        if fast and d < 90:
            n_jumps = n_jumps // 2

        # convert n_jums to int and ensure > 0
        n_jumps = max(int(np.ceil(n_jumps)), 1)

        # Calculate splines for x and y
        r_x = self.mouse_deviation(x_goal, 'x', significant_movement, d)
        r_y = self.mouse_deviation(y_goal, 'y', significant_movement, d)

        points = [[self.x_mouse_loc, self.y_mouse_loc],
                  [self.x_mouse_loc, self.y_mouse_loc], [r_x, r_y],
                  [x_goal, y_goal], [x_goal, y_goal]]
        points = np.array(points)

        x = points[:, 0]

        y = points[:, 1]

        t = [0, 0.1, 0.5, 0.9, 1]

        ipl_t = np.linspace(0.0, 1, n_jumps)

        x_i = Util.calc_spline(t, ipl_t, x)

        y_i = Util.calc_spline(t, ipl_t, y)

        # Execute Mouse movement
        action = ActionChains(self.driver)
        for mouse_x, mouse_y in zip(x_i, y_i):
            mouse_x = int(mouse_x)
            mouse_y = int(mouse_y)
            action.move_by_offset(mouse_x - self.x_mouse_loc,
                                  mouse_y - self.y_mouse_loc)
            self.x_mouse_loc = mouse_x
            self.y_mouse_loc = mouse_y
        action.perform()

    def mouse_to(self, x_goal, y_goal):
        """
        Moves the cursor to (x_goal, y_goal), if this is a long motion
        it is split into two discrete, randomized moves
        :param x_goal: numeric in [0,self.width] target x
        :param y_goal: numeric in [0,self.height] target y
        :return: none
        """
        interim_move = False
        direction_x = np.sign(self.x_mouse_loc - x_goal)
        x_dist = max(x_goal, self.x_mouse_loc) - min(x_goal, self.x_mouse_loc)

        direction_y = np.sign(self.y_mouse_loc - y_goal)
        y_dist = max(y_goal, self.y_mouse_loc) - min(y_goal, self.y_mouse_loc)

        if x_dist > 90:
            x_interim = x_goal + direction_x * random.randint(30, 90)
            interim_move = True
        if y_dist > 90:
            y_interim = y_goal + direction_y * random.randint(30, 90)
            interim_move = True
        if interim_move:
            if 0 < x_dist <= 90:
                x_interim = x_goal + direction_x * random.randint(0, x_dist)
            elif x_dist == 0:
                x_interim = x_goal + direction_x * random.randint(0, 10)

            if 0 < y_dist <= 90:
                y_interim = y_goal + direction_y * random.randint(0, y_dist)
            elif y_dist == 0:
                y_interim = y_goal + direction_y * random.randint(0, 10)
        if interim_move:
            self.partial_mouse(x_interim, y_interim, fast=True)
        self.partial_mouse(x_goal, y_goal)

    def click(self):
        action = ActionChains(self.driver)
        action.click()
        action.perform()

    def scroll(self, y_goal):
        """
        :param y_goal: target y location
        :return: self.y_scroll_loc returns realized y location
        Scroll around y_goal, does not go to y_goal exactly
        """
        d = Util.dist(0, 0, y_goal, self.y_scroll_loc)
        direction = np.sign(y_goal - self.y_scroll_loc)

        # determine acceleration
        if d > 2000:
            a0 = random.uniform(5, 8)
            a1 = 1
        elif d > 400:
            a0 = random.uniform(2, 6)
            a1 = 1
        else:
            a0 = random.uniform(0.2, 2)
            a1 = random.uniform(0.5, 2)
        t_min = math.ceil(np.sqrt(2 * d * a1 / (a0 ** 2 * (a1 + 1))))
        t0 = random.randint(t_min, t_min + 2)
        a0 = direction * a0
        a1 = - direction * a1
        v = 0
        while np.sign(y_goal - self.y_scroll_loc) == direction:
            y_next = self.y_scroll_loc + int(v)
            # try:
            self.driver.execute_script(f'window.scrollTo(0,{y_next})')
            self.y_scroll_loc = self.driver.execute_script(
                'return window.pageYOffset;')
            # except WebDriverException:
            #     return None

            if self.y_scroll_loc is None:
                self.y_scroll_loc = 0
            if t0 > 0:
                v += a0
                t0 -= 1
            else:
                v += a1
                if direction * v <= 0:
                    break
            time.sleep(0.02)
        return self.y_scroll_loc

    def set_cursor_loc(self):
        """
        Finds the cursor location and scrolls to 0
        :return: None
        """
        # moves cursor to html element with known coordinates
        almost_empty = 'https://this-page-intentionally-left-blank.org'
        Util.connection_handler(self.driver, almost_empty)

        # Fix height (maybe move this to a more reasonable location)
        e = self.driver.find_element_by_tag_name('html')
        self.height = int(e.get_attribute('clientHeight'))

        element_path = '//*[@id="this-page-intentionally-left-blank.org"]/p'
        e = self.driver.find_element_by_xpath(element_path)
        action = ActionChains(self.driver)
        action.move_to_element_with_offset(e, 0, 0)
        action.perform()
        coordinates = e.location
        self.x_mouse_loc = int(coordinates['x'])
        self.y_mouse_loc = int(coordinates['y'])

        self.mouse_to(random.randint(0, self.width),
                      random.randint(0, self.height))
        self.scroll(0)

    def move_and_click(self, element_x_path, safe=False):

        button = self.driver.find_element_by_xpath(element_x_path)
        where = button.rect
        x_dev = random.randint(1, max(int(where['width'] - 1), 1))
        y_dev = random.randint(1, max(int(where['height'] - 1), 1))
        x_loc = int(where['x']) + x_dev
        y_loc = int(where['y']) + y_dev
        self.mouse_to(x_loc, y_loc)
        if safe:
            self.driver.move_to_element_with_offset(button, x_dev, y_dev)
        self.click()

    def scroll_to_bottom(self, slow=False, fast=False, limit=None):
        scroll_loc_prev = -5
        if slow:
            scroll_dist = int(random.uniform(200, 350))
        elif fast:
            scroll_dist = int(random.uniform(600, 900))
        else:
            scroll_dist = int(random.uniform(400, 600))
        while self.y_scroll_loc > scroll_loc_prev + 2:
            scroll_loc_prev = self.y_scroll_loc
            sucess = self.scroll(self.y_scroll_loc + scroll_dist)
            if sucess is None:
                break
            time.sleep(random.uniform(2, 5))
            if limit is not None:
                if self.y_scroll_loc >= limit:
                    break
            scroll_dist = scroll_dist + int(random.uniform(-20, 20))
            self.partial_mouse(self.x_mouse_loc + int(random.uniform(-7, 7)),
                               self.y_mouse_loc + int(random.uniform(-7, 7)))

    def scroll_to_top(self, slow=False, fast=False):
        scroll_loc_prev = self.reset_scroll_loc()

        if slow:
            scroll_dist = int(random.uniform(200, 350))
        elif fast:
            scroll_dist = int(random.uniform(900, 1200))
        else:
            scroll_dist = int(random.uniform(400, 600))
        do = True
        while do or self.y_scroll_loc < scroll_loc_prev - 2:
            scroll_loc_prev = self.y_scroll_loc
            do = False
            sucess = self.scroll(self.y_scroll_loc - scroll_dist)
            if sucess is None:
                break
            if fast:
                time.sleep(random.uniform(0, 0.5))
            else:
                time.sleep(random.uniform(2, 5))

            scroll_dist = scroll_dist + int(random.uniform(-20, 20))
            self.partial_mouse(self.x_mouse_loc + int(random.uniform(-7, 7)),
                               self.y_mouse_loc + int(random.uniform(-7, 7)))

    def reset_scroll_loc(self):
        self.y_scroll_loc = self.driver.execute_script(
            'return window.pageYOffset;')
        return self.y_scroll_loc

    def safe_click(self, element, x_dev, y_dev):
        action = ActionChains(self.driver)
        action.move_to_element_with_offset(element, x_dev, y_dev)
        action.click()
        action.perform()
