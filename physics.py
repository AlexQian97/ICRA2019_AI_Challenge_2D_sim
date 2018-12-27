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

import cmath
import math

def dynamic_update(current_v, t_interval, acceleration):
    """Calculate the dynamic change in a degree of freedom

    Args:
        current_v (:obj:`int or float`): The current value in millimeter per second.
        t_interval (:obj:`int or float`): The time interval in seconds.
        acceleration (:obj:`int or float`): The acceleration in millimeter per second^2.

    """
    dist = current_v * t_interval + \
        (1/2) * acceleration * t_interval**2
    new_v = current_v + acceleration * t_interval
    return dist, new_v


class Vector3D:
    """Vector representation in 3-dimensional space."""
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        if isinstance(other, Vector3D) and self.x==other.x \
        and self.y==other.y and self.z==other.z:
            return True
        return False

    def __add__(self, other):
        if type(other) is not Vector3D:
            raise TypeError("Unsupport addition with type {:} and type {:}".format(
                type(self), type(other)
            ))
        x = self.x + other.x
        y = self.y + other.y
        z = self.z + other.z
        return self.__class__(x, y, z)

    def __str__(self):
        return "Vector3D({:}, {:}, {:})".format(self.x, self.y, self.z)

    def __repr__(self):
        return self.__str__()


class Vector2D(Vector3D):
    """Vector representation in 2-dimensional space."""
    def __init__(self, x, y):
        Vector3D.__init__(self, x, y, None)

    def __add__(self, other):
        if not isinstance(other, Vector2D):
            raise TypeError("Unsupport addition with type {:} and type {:}".format(
                type(self), type(other)
            ))
        x = self.x + other.x
        y = self.y + other.y
        return Vector2D(x, y)

    def __sub__(self, other):
        if not isinstance(other, Vector2D):
            raise TypeError("Unsupport subtraction with type {:} and type {:}".format(
                type(self), type(other)
            ))
        x = self.x - other.x
        y = self.y - other.y
        return Vector2D(x, y)

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            raise TypeError("Unsupport multiply with type {:} and type {:}".format(
                type(self), type(scalar)
            ))
        x = self.x * scalar
        y = self.y * scalar
        return Vector2D(x, y)

    def __neg__(self):
        x = -self.x
        y = -self.y
        return Vector2D(x, y)

    def __str__(self):
        return "Vector2D({:}, {:})".format(self.x, self.y)

    def rotate(self, theta, center=None):
        """
        theta: in radian
        center: a Point2D object
        """
        if center is None:
            center = Vector2D(0, 0)

        # Source: http://effbot.org/zone/tkinter-complex-canvas.htm
        cangle = cmath.exp(theta*1j)
        offset = complex(center.x, center.y)
        v = cangle * (complex(self.x, self.y) - offset) + offset
        return Vector2D(v.real, v.imag)

    def find_distance(self, another_vec):
        if not isinstance(another_vec, Vector3D):
            raise TypeError("Unsupport find_distance with type {:} and type {:}".format(
                type(self), type(another_vec)
            ))
        return math.sqrt(
            (another_vec.x - self.x)**2 + (another_vec.y - self.y)**2
        )


class Orient2D(Vector3D):
    """Orientation representation in 3-dimensional space."""
    def __init__(self, z):
        Vector3D.__init__(self, None, None, z)

    def __add__(self, other):
        if not isinstance(other, Orient2D):
            raise TypeError("Unsupport addition with type {:} and type {:}".format(
                type(self), type(other)
            ))
        z = self.z + other.z
        return Orient2D(z)

    def __sub__(self, other):
        if not isinstance(other, Orient2D):
            raise TypeError("Unsupport subtraction with type {:} and type {:}".format(
                type(self), type(other)
            ))
        z = self.z - other.z
        return Orient2D(z)

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            raise TypeError("Unsupport multiply with type {:} and type {:}".format(
                type(self), type(scalar)
            ))
        z = self.z * scalar
        return Orient2D(z)

    def __neg__(self):
        z = -self.z
        return Orient2D(z)

    def __str__(self):
        return "{:} radians".format(self.z)


class GeoUnit2D:
    """The unit representation in 2-dimension space."""

    def __init__(self, transfer, rotation):
        """Geomatric Unit in 2D spcae constructor.

        Args:
            transfer (:obj:`Vector2D`): Coordinator transfer representation.
            rotation (:obj:`Orient2D`): Rotation representation.

        """
        self.transfer = transfer
        self.rotation = rotation

    def __eq__(self, other):
        if isinstance(other, GeoUnit2D) and self.transfer == other.transfer \
        and self.rotation == other.rotation:
            return True
        return False

    def __add__(self, other):
        if not isinstance(other, GeoUnit2D):
            raise TypeError("Unsupport addition with type {:} and type {:}".format(
                type(self), type(other)
            ))
        transfer = self.transfer + other.transfer
        rotation = self.rotation + other.rotation
        return self.__class__(transfer, rotation)

    def __sub__(self, other):
        if not isinstance(other, GeoUnit2D):
            raise TypeError("Unsupport subtraction with type {:} and type {:}".format(
                type(self), type(other)
            ))
        transfer = self.transfer - other.transfer
        rotation = self.rotation - other.rotation
        return self.__class__(transfer, rotation)

    def __neg__(self):
        transfer = -self.transfer
        rotation = -self.rotation
        return self.__class__(transfer, rotation)

    def __str__(self):
        return "GeoUnit2D(\n\ttransfer: {:}, \n\trotation: {:}\n)".format(
            self.transfer, self.rotation
        )

    def __repr__(self):
        return self.__str__()


class Velocity2D(GeoUnit2D):
    """The velocity representaion in 2-dimensional space."""
    def __init__(self, linear, angular):
        """Velocity representation in 2D spcae constructor.

        Args:
            linear (:obj:`Vector2D`): Linear velocity.
            angular (:obj:`Orient2D`): Angular velocity.

        """
        GeoUnit2D.__init__(self, linear, angular)
        self.linear = self.transfer
        self.angular = self.rotation


class Acceleration2D(GeoUnit2D):
    """The acceleration representaion in 2-dimensional space."""
    def __init__(self, linear, angular):
        """Velocity representation in 2D spcae constructor.

        Args:
            linear (:obj:`Vector2D`): Linear acceleration.
            angular (:obj:`Orient2D`): Angular acceleration.

        """
        GeoUnit2D.__init__(self, linear, angular)
        self.linear = self.transfer
        self.angular = self.rotation


class Movement2D(GeoUnit2D):
    """The movement representaion in 2-dimensional space."""
    def __init__(self, linear, angular):
        """Movement representation in 2D spcae constructor.

        Args:
            linear (:obj:`Vector2D`): Linear movement.
            angular (:obj:`Orient2D`): Angular movement.

        """
        GeoUnit2D.__init__(self, linear, angular)
        self.linear = self.transfer
        self.angular = self.rotation


class Pose2D(GeoUnit2D):
    """The pose representaion in 2-dimensional space."""
    def __init__(self, position, orientation):
        """Pose in 2D spcae constructor.

        Args:
            position (:obj:`Vector2D`): Position representation.
            orientation (:obj:`Orient2D`): Orientation representation.

        """
        GeoUnit2D.__init__(self, position, orientation)
        self.position = self.transfer
        self.orientation = self.rotation
