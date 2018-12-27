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

    def update(self, t_interval=0.05):
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

    def __init__(self, pose, side_length, zone_id):
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
        GameObject.__init__(self, pose, velocity, acceleration, shape_set)
        self.id = zone_id
        self.side_length = side_length


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

    def __init__(self, pose, length, width, robot_id):
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

    @property
    def radius(self):
        return math.sqrt((self.length/2)**2 + (self.width/2)**2)
