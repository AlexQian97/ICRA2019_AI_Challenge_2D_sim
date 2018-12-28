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
import math
from copy import deepcopy
from physics import Vector2D, Orient2D, Velocity2D
from game_objects import Bullet, Wall, Robot, Zone, Polygon, Circle
from game import Game

class GameUI:
    font = ('calibri', 50)
    font_color = "#ddd"

    def __init__(self, width, height=None):
        # game setting
        # self.map_config_path = 'map_mini_config.json'
        self.map_config_path = 'map_mini_config.json'
        self.update_time_interval = 0.02
        self.game = Game(self.map_config_path)

        # tk setup
        self.tk = Tk()
        self.tk.title("ICRA 2019 2D Simulation")
        self.tk.resizable(0, 0)
        self.tk.wm_attributes("-topmost", 1)
        self.tk.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.win_closing = False

        # create canvas
        if height is None:
            height = width * self.game.map.height / self.game.map.width

        self.map_scale = min(
            width / self.game.map.width,
            height / self.game.map.height
        )

        self.canvas_width = width + 2 * self.game.map.wall_thickness * self.map_scale
        self.canvas_height = height + 2 * self.game.map.wall_thickness * self.map_scale
        self.canvas = Canvas(self.tk, width=self.canvas_width, height=self.canvas_height,
                             bd=0, highlightthickness=0)
        self.canvas.pack()
        # self.tk.update()

        # Keys
        self.canvas.bind_all('r', self.reset)

        self.key_dict = {"R1": ['2', 'w', 'q', 'e', '1', '3', '0'],
                         "R2": ['5', 't', 'r', 'y', '4', '6', 'p'],
                         "B1": ['s', 'x', 'z', 'c', 'a', 'd', 'l'],
                         "B2": ['g', 'b', 'v', 'n', 'f', 'h', 'm']}

        for key, value in self.key_dict.items():
            for char in value[:-1]:
                self.canvas.bind_all('<KeyPress-' + char + '>', self._on_key_press_repeat)
                self.canvas.bind_all('<KeyRelease-' + char + '>', self._on_key_release_repeat)

        self.canvas.bind_all('<0>', self._fire1)
        self.canvas.bind_all('<p>', self._fire2)
        self.canvas.bind_all('<l>', self._fire3)
        self.canvas.bind_all('<m>', self._fire4)

        # self.canvas.bind_all('<KeyPress-a>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-a>', self._on_key_release_repeat)
        # self.canvas.bind_all('<KeyPress-1>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-1>', self._on_key_release_repeat)
        # self.canvas.bind_all('<KeyPress-s>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-s>', self._on_key_release_repeat)
        # self.canvas.bind_all('<KeyPress-d>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-d>', self._on_key_release_repeat)
        # self.canvas.bind_all('<KeyPress-l>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-l>', self._on_key_release_repeat)
        # self.canvas.bind_all('<KeyPress-j>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-j>', self._on_key_release_repeat)
        # # self.canvas.bind_all('<KeyPress-space>', self._on_key_press_repeat)
        # # self.canvas.bind_all('<KeyRelease-space>', self._on_key_release_repeat)
        # self.canvas.bind_all('<x>', self._fire2)
        #
        # self.canvas.bind_all('<KeyPress-f>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-f>', self._on_key_release_repeat)
        # self.canvas.bind_all('<KeyPress-t>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-t>', self._on_key_release_repeat)
        # self.canvas.bind_all('<KeyPress-g>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyRelease-g>', self._on_key_release_repeat)
        # self.canvas.bind_all('<KeyPress-h>', self._on_key_press_repeat)
        # self.canvas.bind_all('<KeyReleimport mathase-h>', self._on_key_release_repeat)
        # self.canvas.bind_all('<Down>', self._fire3)
        self._has_prev_key_release = None
        self.pressing_keys = set()


        # self.reset(None)
        self.debug_text_id = self.show_debug_text(None, '')


    def show_debug_text(self, text_id, text):
        canvas = self.canvas
        if text_id is not None:
            canvas.delete(text_id)
        text_id = canvas.create_text(
            self.canvas_width//2,
            50,
            text=str(text),
            font=GameUI.font,
            fill=GameUI.font_color
        )
        return text_id

    def reset(self, evt):
        del self.game
        self.game = Game(self.map_config_path)

    def clean(self):
        self.canvas.delete("all")

    def real_coord_2_display_coord(self, real_coords):
        x = real_coords.x * self.map_scale
        y = (self.game.map.height-real_coords.y) * self.map_scale
        x += self.game.map.wall_thickness * self.map_scale
        y += self.game.map.wall_thickness * self.map_scale
        return Vector2D(x, y)

    def draw(self):
        for obj in self.game.game_objects:
            color = '#888'

            if type(obj) is Wall:
                vertex = deepcopy(obj.shape_set[0].vertex)
                coords = []
                for v in vertex:
                    new_v = v.rotate(
                        obj.pose.orientation.z
                    )
                    new_v += obj.pose.position
                    new_v = self.real_coord_2_display_coord(new_v)
                    coords.append(new_v.x)
                    coords.append(new_v.y)
                self.canvas.create_polygon(coords, fill=color, outline=color)

            elif type(obj) is Zone:
                if 'R' in obj.id:
                    color = 'red'
                elif 'B' in obj.id:
                    color = 'blue'

                vertex = deepcopy(obj.shape_set[0].vertex)
                vertex[0]+=Vector2D(obj.side_length*0.02, -obj.side_length*0.02)
                vertex[1]+=Vector2D(-obj.side_length*0.02, -obj.side_length*0.02)
                vertex[2]+=Vector2D(-obj.side_length*0.02, obj.side_length*0.02)
                vertex[3]+=Vector2D(obj.side_length*0.02, obj.side_length*0.02)

                coords = []
                for v in vertex:
                    new_v = v.rotate(
                        obj.pose.orientation.z
                    )
                    new_v += obj.pose.position
                    new_v = self.real_coord_2_display_coord(new_v)
                    coords.append(new_v.x)
                    coords.append(new_v.y)
                self.canvas.create_polygon(
                    coords, fill="", outline=color, width=obj.side_length*0.04*self.map_scale
                )


            elif type(obj) is Robot:
                radius = obj.radius * self.map_scale
                central = obj.pose.position
                display_c = self.real_coord_2_display_coord(central)
                color = '#ddd'
                coords = [
                    display_c.x-radius, display_c.y-radius,
                    display_c.x+radius, display_c.y+radius,
                ]
                self.canvas.create_oval(coords, fill=color, outline=color)

                level = int(15 - obj.health * 15 / self.game.robot_top_health)
                # color = 'black'
                # print(level)
                color = '#{:x}{:x}{:x}'.format(level, 0, 0)
                if obj.health == 0:
                    color = '#fff'

                for shape_i in range(len(obj.shape_set)):
                    if shape_i>0:
                        if 'R' in obj.id:
                            color = 'red'
                        elif 'B' in obj.id:
                            color = 'blue'

                    vertex = deepcopy(obj.shape_set[shape_i].vertex)
                    coords = []
                    for v in vertex:
                        new_v = v.rotate(
                            obj.pose.orientation.z
                        )
                        new_v += obj.pose.position
                        new_v = self.real_coord_2_display_coord(new_v)
                        coords.append(new_v.x)
                        coords.append(new_v.y)
                    self.canvas.create_polygon(coords, fill=color, outline=color)

            elif type(obj) is Bullet:
                radius = obj.radius * self.map_scale
                central = obj.pose.position
                display_c = self.real_coord_2_display_coord(central)
                if 'R' in obj.team:
                    color = 'red'
                if 'B' in obj.team:
                    color = 'blue'
                coords = [
                    display_c.x-radius, display_c.y-radius,
                    display_c.x+radius, display_c.y+radius,
                ]
                self.canvas.create_oval(coords, fill=color, outline=color)



    def _fire1(self, event):
        self.game.fire('R1')

    def _fire2(self, event):
        self.game.fire('R2')

    def _fire3(self, event):
        self.game.fire('B1')

    def _fire4(self, event):
        self.game.fire('B2')


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
        # Update game
        self.game.update(self.update_time_interval)

        # Clean canvas
        self.clean()

        # Re-draw
        self.draw()

        # User command
        self.debug_text_id = self.show_debug_text(
            self.debug_text_id, str(self.pressing_keys)
        )
        for key, value in self.key_dict.items():
            new_v = Vector2D(0, 0)
            new_angular = 0
            if value[0] in self.pressing_keys:
                new_v.x += 1000
            if value[1] in self.pressing_keys:
                new_v.x -= 1000
            if value[2] in self.pressing_keys:
                new_v.y += 1000
            if value[3] in self.pressing_keys:
                new_v.y -= 1000
            if value[4] in self.pressing_keys:
                new_angular += math.pi
            if value[5] in self.pressing_keys:
                new_angular -= math.pi
            for obj in self.game.game_objects:
                if type(obj) is Robot and obj.id==key:
                    obj.velocity = Velocity2D(new_v, Orient2D(new_angular))

        # new_v = Vector2D(0, 0)
        # new_angular = 0
        # if 'w' in self.pressing_keys:
        #     new_v.x += 1000
        # if 's' in self.pressing_keys:
        #     new_v.x -= 1000
        # if 'a' in self.pressing_keys:
        #     new_v.y += 1000
        # if 'd' in self.pressing_keys:
        #     new_v.y -= 1000
        # if 'j' in self.pressing_keys:
        #     new_angular += math.pi
        # if 'l' in self.pressing_keys:
        #     new_angular -= math.pi
        # for obj in self.game.game_objects:
        #     if type(obj) is Robot and obj.id=='R2':
        #         obj.velocity = Velocity2D(new_v, Orient2D(new_angular))

        # Next update iteration
        self.canvas.after(int(self.update_time_interval*1000), self.update)

    def run(self):
        # game start running here
        self.update()
        self.tk.mainloop()


if __name__ == "__main__":
    # game = GameUI(1200, 776)
    # game = GameUI(800, 500)
    game = GameUI(width=1200)
    # game = GameUI(width=800)
    game.run()
