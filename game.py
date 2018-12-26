#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018 Chenrui Lei
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from tkinter import *
import time
import random
import math
import json
from copy import deepcopy
from game_objects import Wall, Zone, Ball, Robot2D, Robot2DPos, Robot2DModel, Velocity2D, ICRA_2019_ROBOT_MODEL
from collision_engine_2d import CollisionEngine2D, LineSegment2D, Point2D

class Game:
    font = ('calibri', 50)
    font_color = "#ddd"

    def __init__(self, width, height):
        # game setting
        self.update_time_interval = 0.01

        # tk setup
        self.tk = Tk()
        self.tk.title("ICRA 2019 2D Simulation")
        self.tk.resizable(0, 0)
        self.tk.wm_attributes("-topmost", 1)
        self.tk.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.win_closing = False

        # create canvas
        self.canvas_width = width
        self.canvas_height = height
        self.canvas = Canvas(self.tk, width=width, height=height,
                             bd=0, highlightthickness=0)
        self.canvas.pack()
        self.tk.update()

        # Keys
        self.canvas.bind_all('r', self.reset)
        # self.canvas.bind_all('<ButtonPress-1>', self._fire_key_handler)
        self.canvas.bind_all('<KeyPress-a>', self._on_key_press_repeat)
        self.canvas.bind_all('<KeyRelease-a>', self._on_key_release_repeat)
        self.canvas.bind_all('<KeyPress-w>', self._on_key_press_repeat)
        self.canvas.bind_all('<KeyRelease-w>', self._on_key_release_repeat)
        self.canvas.bind_all('<KeyPress-s>', self._on_key_press_repeat)
        self.canvas.bind_all('<KeyRelease-s>', self._on_key_release_repeat)
        self.canvas.bind_all('<KeyPress-d>', self._on_key_press_repeat)
        self.canvas.bind_all('<KeyRelease-d>', self._on_key_release_repeat)
        self.canvas.bind_all('<KeyPress-l>', self._on_key_press_repeat)
        self.canvas.bind_all('<KeyRelease-l>', self._on_key_release_repeat)
        self.canvas.bind_all('<KeyPress-j>', self._on_key_press_repeat)
        self.canvas.bind_all('<KeyRelease-j>', self._on_key_release_repeat)
        self.canvas.bind_all('<KeyPress-space>', self._on_key_press_repeat)
        self.canvas.bind_all('<KeyRelease-space>', self._on_key_release_repeat)
        self.canvas.bind_all('<space>', self._fire)
        self._has_prev_key_release = None
        self.pressing_keys = set()

        self.map_config_path = 'map_mini_config.json'
        self.map_scale = min(
            self.canvas_width / 8500, self.canvas_height / 5500
        )
        self.reset(None)

        self.debug_text_id = self.show_debug_text(None, '')


    def show_debug_text(self, text_id, text):
        canvas = self.canvas
        if text_id is not None:
            canvas.delete(text_id)
        text_id = canvas.create_text(
            self.canvas_width//2,
            50,
            text=str(text),
            font=Game.font,
            fill=Game.font_color
        )
        return text_id

    def reset(self, evt):
        self.canvas.delete("all")

        # create game objects
        self.game_objects = []

        # Load json format map configration
        with open(self.map_config_path, 'r') as f:
            map_config = json.load(f)

        for zone in map_config['config']['zones']:
            self.game_objects.append(
                Zone(
                    self.canvas,
                    Point2D(
                        zone['coords']['x']*self.map_scale,
                        zone['coords']['y']*self.map_scale,
                    ),
                    zone['width']*self.map_scale,
                    math.radians(zone['orientation']),
                    zone['team']
                )
            )

        for wall in map_config['config']['walls']:
            self.game_objects.append(
                Wall(
                    self.canvas,
                    Point2D(
                        wall['coords']['x']*self.map_scale,
                        wall['coords']['y']*self.map_scale
                    ),
                    wall['width']*self.map_scale, wall['length']*self.map_scale,
                    math.radians(wall['orientation'])
                )
            )

        for robot in map_config['config']['robot_starting_points']:
            self.game_objects.insert(0,
                Robot2D(
                    robot['team'],
                    Robot2DPos(
                        Point2D(
                            robot['coords']['x']*self.map_scale,
                            robot['coords']['y']*self.map_scale
                        ),
                        math.radians(robot['orientation'])
                    ),
                    ICRA_2019_ROBOT_MODEL*self.map_scale,
                    Velocity2D(Point2D(0, 0), 0),
                    self.canvas,
                    robot['robot_id']
                )
            )


    def _fire(self, event):
        bullet = Ball(
            self.canvas,
            color=self.game_objects[0].team,
            central=self.game_objects[0].pose.getRobotPoints(
                ICRA_2019_ROBOT_MODEL*self.map_scale
            )[-1],
            # radius=17/2*self.map_scale
        )
        bullet.as_a_bullet(self.game_objects[0].pose, 19000*self.map_scale)
        self.game_objects.append(bullet)


    # Source: https://gist.github.com/vtsatskin/8e3c0c636339b2228138
    def _on_key_release(self, event):
        self._has_prev_key_release = None
        # print("on_key_release", repr(event.char))
        key = event.char
        if key in self.pressing_keys:
            self.pressing_keys.remove(key)

    # Source: https://gist.github.com/vtsatskin/8e3c0c636339b2228138
    def _on_key_press(self, event):
        # print("on_key_press", repr(event.char))
        self.pressing_keys.add(event.char)

    # Source: https://gist.github.com/vtsatskin/8e3c0c636339b2228138
    def _on_key_release_repeat(self, event):
        self._has_prev_key_release = self.tk.after_idle(self._on_key_release, event)
        # print("on_key_release_repeat", repr(event.char))

    # Source: https://gist.github.com/vtsatskin/8e3c0c636339b2228138
    def _on_key_press_repeat(self, event):
        if self._has_prev_key_release:
            self.tk.after_cancel(self._has_prev_key_release)
            self._has_prev_key_release = None
            # print("on_key_press_repeat", repr(event.char))
        else:
            self._on_key_press(event)

    def _on_closing(self):
        self.win_closing = True
        self.tk.destroy()

    def update(self):
        # for object_i in range(len(self.game_objects)):
        for object_i in range(1):
            for object_j in range(object_i+1, len(self.game_objects)):
                obj_a = self.game_objects[object_i]
                obj_b = self.game_objects[object_j]

                va, ea = obj_a.getVetexEdges()
                vna, ena = obj_a.getVetexEdges(obj_a.pose)
                vb, eb = obj_b.getVetexEdges()
                vnb, enb = obj_b.getVetexEdges(obj_b.pose)

                # print("A position:", obj_a.pose.position)
                # print("last A:", obj_a.last_pose.position)
                # print("A position:", obj_a.pose.position)
                # print("last A:", obj_a.last_pose.position)
                # if (obj_a.pose.position - obj_a.last_pose.position!=Point2D(0, 0)):
                #     print("A is moving")

                # # print("B position:", obj_b.pose.position)
                # if (obj_b.pose.position - obj_b.last_pose.position!=Point2D(0, 0)):
                #     print("B is moving")

                for i in range(len(va)):
                    v = va[i]
                    for e in eb:
                        moved_line = LineSegment2D(vb[e[0]], vb[e[1]])
                        point_movement = vna[i] - v
                        line_segment_movement = obj_b.pose.position - obj_b.last_pose.position

                        if CollisionEngine2D.point_line_collision(
                            v, point_movement,
                            moved_line, line_segment_movement
                        ):

                            point_moving_line_seg = LineSegment2D(v, v+point_movement-line_segment_movement)
                            intersect_point = LineSegment2D.find_intersection(
                                point_moving_line_seg,
                                moved_line
                            )

                            print("Collision!!!!! on", intersect_point)

                            # obj_a.move(Velocity2D(intersect_point - vna[i], 0))
                            # obj_a.move(Velocity2D(v - vna[i], obj_a.last_pose.orientation - obj_a.pose.orientation))
                            # obj_a.move(Velocity2D(obj_a.last_pose.position, obj_a.last_pose.orientation))
                            obj_a.moveTo(obj_a.last_pose)

                for i in range(len(vb)):
                    v = vb[i]
                    for e in ea:
                        moved_line = LineSegment2D(va[e[0]], va[e[1]])
                        point_movement = vnb[i] - v
                        line_segment_movement = obj_a.pose.position - obj_a.last_pose.position

                        if CollisionEngine2D.point_line_collision(
                            v, point_movement,
                            moved_line, line_segment_movement
                        ):
                            point_moving_line_seg = LineSegment2D(v, v+point_movement-line_segment_movement)
                            intersect_point = LineSegment2D.find_intersection(
                                point_moving_line_seg,
                                moved_line
                            )
                            print("Collision!!*** on", intersect_point)
                            obj_a.moveTo(obj_a.last_pose)

                obj_a.last_pose = deepcopy(obj_a.pose)
                obj_b.last_pose = deepcopy(obj_b.pose)

        self.debug_text_id = self.show_debug_text(
            self.debug_text_id, str(self.pressing_keys)
        )
        new_v = Point2D(0, 0)
        new_angular = 0
        if 's' in self.pressing_keys:
            new_v.x -= 1000 * self.map_scale
        if 'w' in self.pressing_keys:
            new_v.x += 1000 * self.map_scale
        if 'd' in self.pressing_keys:
            new_v.y += 1000 * self.map_scale
        if 'a' in self.pressing_keys:
            new_v.y -= 1000 * self.map_scale
        if 'j' in self.pressing_keys:
            new_angular -= 8*math.pi  * self.map_scale
        if 'l' in self.pressing_keys:
            new_angular += 8*math.pi  * self.map_scale
        self.game_objects[0].change_vel( Velocity2D(new_v, new_angular) )
        self.canvas.after(10, self.update)
        # print(self.pressing_keys)

    def run(self):
        # # game start running here
        self.update()
        self.tk.mainloop()


if __name__ == "__main__":
    game = Game(1200, 776)
    # game = Game(650, 650)
    game.run()
