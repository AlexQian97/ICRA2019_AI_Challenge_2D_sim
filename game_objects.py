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

import math
from copy import deepcopy
from physics import dynamic_update, Movement2D, Vector2D, Orient2D, Pose2D, Velocity2D, Acceleration2D
import time

class Shape:
    """Base class of geometry shape"""
    def __init__(self, pose, type=[]):
        self.pose = pose
        self.type = type


class Circle(Shape):
    """Circle shape class"""
    def __init__(self, pose, radius):
        Shape.__init__(self, pose)
        self.type.append('circle')
        self.radius = radius


class Polygon(Shape):
    """Polygon shape class"""
    def __init__(self, pose, vertex):
        Shape.__init__(self, pose)
        self.type.append('poly')
        self.vertex = vertex


class GameObject:
    """Base class of game object"""

    def __init__(self, pose, velocity, acceleration, shape_set=[]):
        self.pose = pose
        self.velocity = velocity
        self.acceleration = acceleration
        self.shape_set = shape_set

    def update(self, t_interval=0.02):
        dx, vx = dynamic_update(
            self.velocity.linear.x, t_interval, self.acceleration.linear.x
        )
        dy, vy = dynamic_update(
            self.velocity.linear.y, t_interval, self.acceleration.linear.y
        )
        dz, vz = dynamic_update(
            self.velocity.angular.z, t_interval, self.acceleration.angular.z
        )

        # Perform movements
        self.pose += Movement2D(
            Vector2D(dx, dy).rotate(self.pose.orientation.z),
            Orient2D(dz)
        )

        # Update physical status
        self.velocity = Velocity2D(
            Vector2D(vx, vy), Orient2D(vz)
        )


    def move(self, offset):
        self.pose += offset

    def moveTo(self, destination):
        offset = destination - self.pose
        self.move(offset)

    def __str__(self):
        return "Game object:\n\tpose: {:}\n\tvel: {:}\n\tacclr: {:}".format(
            self.pose, self.velocity, self.acceleration
        )


class Wall(GameObject):
    """Wall in game"""

    def __init__(self, pose, length, width):
        velocity = Velocity2D(
            linear=Vector2D(0, 0),
            angular=Orient2D(0)
        )
        acceleration = Acceleration2D(
            linear=Vector2D(0, 0),
            angular=Orient2D(0)
        )
        shape_set = [
            Polygon(
                Pose2D(
                    Vector2D(0, 0),
                    Orient2D(0)
                ),
                vertex=[
                    Vector2D(0, 0),
                    Vector2D(length, 0),
                    Vector2D(length, -width),
                    Vector2D(0, -width),
                ]
            )
        ]
        GameObject.__init__(self, pose, velocity, acceleration, shape_set)


class Zone(GameObject):
    """Zone in game"""

    def __init__(self, pose, side_length, zone_id, zone_type):
        velocity = Velocity2D(
            linear=Vector2D(0, 0),
            angular=Orient2D(0)
        )
        acceleration = Acceleration2D(
            linear=Vector2D(0, 0),
            angular=Orient2D(0)
        )
        shape_set = [
            Polygon(
                Pose2D(
                    Vector2D(0, 0),
                    Orient2D(0)
                ),
                vertex=[
                    Vector2D(0, 0),
                    Vector2D(side_length, 0),
                    Vector2D(side_length, -side_length),
                    Vector2D(0, -side_length),
                ]
            )
        ]
        zone_team = zone_id[0] # 'R' or 'B'

        GameObject.__init__(self, pose, velocity, acceleration, shape_set)
        # ZoneMixin.__init__(self, zone_type, zone_team)
        self.type = zone_type
        self.team = zone_team 
        self.id = zone_id
        self.side_length = side_length
        self.type = zone_type

        now = time.time()
        self.clock = now
        self.defence_buff_timer = now
        self.defence_buff_ready = 1

        self.supply_times_ready = 2
        self.added_ammo = False
        self.robot = None # cache the robot which is in this zone
    
    def is_robot_inside(self, robot):
        in_left_border=(self.pose.position.x + robot.width/2 < robot.pose.position.x)
        in_right_border=(self.pose.position.x + self.side_length > robot.pose.position.x + robot.width/2)
        in_top_border=(self.pose.position.y > robot.pose.position.y + robot.length/2)
        in_bottom_border=(self.pose.position.y - self.side_length < robot.pose.position.y - robot.length/2)
        
        return in_bottom_border and in_left_border and in_right_border and in_top_border
    
    def update(self, t_interval=0.02):
        super(Zone, self).update(t_interval)

        self.update_clock_and_buffs(t_interval)
        
    
    def update_clock_and_buffs(self, t_interval):
        now = time.time()
        if now - self.clock > 60:
            self.clock = now
            self.defence_buff_ready = 1
            self.supply_times_ready = 2
            print("zone:<{}> buffs and supply refreshed.\n".format(self.id))

    def is_friendly(self, robot):
        return robot.id[0] == self.team

    def handle_as_defence_zone(self, robot, t_interval):
        now = time.time()
        if self.is_robot_inside(robot) and self.is_friendly(robot):
            self.robot = robot
            if now - self.defence_buff_timer > 5 and self.defence_buff_ready > 0:
                print("\n### waited for 5 seconds.\n")
                self.robot.start_buff_defence()
                self.defence_buff_ready -= 1
                self.defence_buff_timer = now
        elif self.robot is None or robot.id == self.robot.id:
            # the robot left the self. 
            self.defence_buff_timer = now
            self.robot = None
    
    def handle_as_supply_zone(self, robot, t_interval):
        if self.is_robot_inside(robot):
            self.robot = robot
            if self.supply_times_ready > 0 and not self.added_ammo:
                print("\n### adding ammo to <{}>\n".format(robot.id))
                self.supply_times_ready -= 1
                robot.ammo += 50
                self.added_ammo = True
            elif not self.added_ammo:
                print("\n### no more ammo to supply.\n")
                self.added_ammo = True
        elif self.robot is None or robot.id == self.robot.id:
            # this robot has left the zone.
            self.added_ammo = False
            self.robot = None


class Bullet(GameObject):
    """Bullet in game"""

    def __init__(self, pose, velocity, team, radius=17/2):
        acceleration = Acceleration2D(
            linear=Vector2D(0, 0),
            angular=Orient2D(0)
        )
        shape_set = [
            Circle(
                Pose2D(
                    Vector2D(0, 0),
                    Orient2D(0)
                ),
                radius=radius
            )
        ]
        GameObject.__init__(self, pose, velocity, acceleration)
        self.radius = radius
        self.team = team

    def update(self, t_interval):
        self.last_pose = deepcopy(self.pose)
        GameObject.update(self, t_interval)


class Robot(GameObject):
    """Wall in game"""

    def __init__(self, pose, length, width, robot_id, health=2000, ammo=0, defence=25):
        velocity = Velocity2D(
            linear=Vector2D(0, 0),
            angular=Orient2D(0)
        )
        acceleration = Acceleration2D(
            linear=Vector2D(0, 0),
            angular=Orient2D(0)
        )
        shape_set = [
            # Robot's rectangle body
            Polygon(
                Pose2D(
                    Vector2D(0, 0),
                    Orient2D(0)
                ),
                vertex=[
                    Vector2D(-length/2, width/2),
                    Vector2D(length/2, width/2),
                    Vector2D(length/2, -width/2),
                    Vector2D(-length/2, -width/2),
                ]
            ),
            # Robot's canon
            Polygon(
                Pose2D(
                    Vector2D(0, 0),
                    Orient2D(0)
                ),
                vertex=[
                    Vector2D(0, width/20),
                    Vector2D(length*5/8, width/20),
                    Vector2D(length*5/8, -width/20),
                    Vector2D(0, -width/20),
                ]
            )
        ]
        GameObject.__init__(self, pose, velocity, acceleration, shape_set)
        self.length = length
        self.width = width
        self.id = robot_id
        self.health = health
        self.cancelled_damage = 0
        self.defence = defence
        self.ammo = ammo

        self.defence_buff_timer = time.time()
        
    def start_buff_defence(self):
        self.cancelled_damage = self.defence
        self.defence_buff_timer = time.time()
        print("buff start!")
    
    def update(self, t_interval=0.02):
        super(Robot, self).update(t_interval)
       
        if self.cancelled_damage != 0:
            now = time.time()
            if now - self.defence_buff_timer > 30: 
                print("buff ends!")
                self.defence_buff_timer = now
                self.cancelled_damage = 0


    @property
    def radius(self):
        return math.sqrt((self.length/2)**2 + (self.width/2)**2)
