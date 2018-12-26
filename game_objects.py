from tkinter import *
import time
import random
import numpy as np
import cmath
import math
from copy import deepcopy
from collision_engine_2d import CollisionEngine2D, LineSegment2D, Point2D

def dynamic_update(current_v, t_interval, acceleration):
    dist = current_v * t_interval + \
        (1/2) * acceleration * t_interval**2
    new_v = current_v + acceleration * t_interval
    return dist, new_v

def obj_coord_2_world_coord(obj_vel, pose_in_world):
    return Velocity2D(
        Point2D(
            -( obj_vel.linear.x * math.cos(pose_in_world.orientation) + obj_vel.linear.y * math.cos(pose_in_world.orientation+np.pi/2) ),
            -( obj_vel.linear.x * math.sin(pose_in_world.orientation) + obj_vel.linear.y * math.sin(pose_in_world.orientation+np.pi/2) )
        ),
        obj_vel.angular_z
    )


class Pose2D:
    def __init__(self, position=None, orientation=0):
        self.position = position  # Point2D
        self.orientation = orientation  # In randian

class ComplexGameObject:
    def __init__(self, canvas, pose=None, ids=list()):
        self.canvas = canvas
        self.canvas_height = canvas.winfo_height()
        self.canvas_width = canvas.winfo_width()
        self.ids = ids
        self.velocity = Velocity2D(
            Point2D(0, 0), 0
        )
        self.acceleration = Velocity2D(
            Point2D(0, 0), 0
        )
        self.pose = pose
        if pose is None:
            self.pose = Pose2D(
                Point2D(
                    self.canvas_width//2, self.canvas_height//2
                ),
                0
            )
        self.last_pose = deepcopy(self.pose)


    def move(self, d_movement):
        """Move game object by a difference.

        Args:
            d_movement (:obj:`Velocity2D`)

        """
        # Perform movements
        self.pose.position += d_movement.linear
        self.pose.orientation += d_movement.angular_z
        for id in self.ids:
            # Linear
            self.canvas.move(id, d_movement.linear.x, d_movement.linear.y)

            # Angular
            coords = self.canvas.coords(id)
            new_coords = []
            for i in range(0, len(coords), 2):
                new_point = Point2D(coords[i], coords[i+1]).rotate(d_movement.angular_z, self.pose.position)
                new_coords.append(new_point.x)
                new_coords.append(new_point.y)
            self.canvas.coords(id, *new_coords)

    def moveTo(self, pose):
        linear = pose.position - self.pose.position
        angular_z = pose.orientation - self.pose.orientation
        self.move(Velocity2D(linear, angular_z))


    def update(self):
        t_interval = 0.05  # seconds

        dx, vx = dynamic_update(
            self.velocity.linear.x, t_interval, self.acceleration.linear.x
        )
        dy, vy = dynamic_update(
            self.velocity.linear.y, t_interval, self.acceleration.linear.y
        )
        dz, vz = dynamic_update(
            self.velocity.angular_z, t_interval, self.acceleration.angular_z
        )

        # Perform movements
        self.pose.position += Point2D(dx, dy)
        self.pose.orientation += dz
        for id in self.ids:
            # Linear
            self.canvas.move(id, dx, dy)

            # Angular
            coords = self.canvas.coords(id)
            new_coords = []
            for i in range(0, len(coords), 2):
                new_point = Point2D(coords[i], coords[i+1]).rotate(dz, self.pose.position)
                new_coords.append(new_point.x)
                new_coords.append(new_point.y)
            self.canvas.coords(id, *new_coords)

        # Update physical status
        self.velocity = Velocity2D(
            Point2D(vx, vy), vz
        )

        self.canvas.after(int(t_interval*1000), self.update)


class GameObject:
    def __init__(self, canvas, id):
        self.canvas = canvas
        self.canvas_height = canvas.winfo_height()
        self.canvas_width = canvas.winfo_width()
        self.id = id
        self.velocity = Point2D(0, 0)
        self.acceleration = Point2D(0, 0)

    def update(self, t_interval = 0.05):
        # t_interval = 0.05  # seconds
        dx, vx = dynamic_update(self.velocity.x, t_interval, self.acceleration.x)
        dy, vy = dynamic_update(self.velocity.y, t_interval, self.acceleration.y)
        self.canvas.move(self.id, dx, dy)
        self.velocity = Point2D(vx, vy)

        self.canvas.after(int(t_interval*1000), self.update)



class Ball(GameObject):
    def __init__(self, canvas, color, central=None, radius=None):
        GameObject.__init__(self, canvas, None)
        if radius is None:
            radius = min(self.canvas_width, self.canvas_height) * 7 // 500
        if central is None:
            central = Point2D(
                canvas.winfo_width()//2, canvas.winfo_height()//2
            )
        object_id = canvas.create_oval(
            central.x-radius, central.y-radius,
            central.x+radius, central.y+radius,
            fill=color
        )
        self.id = object_id

        self.update(0.01)

    def as_a_bullet(self, pose, initial_speed):
        self.velocity = obj_coord_2_world_coord(
            Velocity2D(
                Point2D(initial_speed, 0), 0
            ), pose
        ).linear



class Wall(GameObject):
    def __init__(self, canvas, tl_cornor, width, length, orientation, color='#888'):
        GameObject.__init__(self, canvas, None)
        raw_pts = [
            tl_cornor,
            tl_cornor+Point2D(0, width),
            tl_cornor+Point2D(length, width),
            tl_cornor+Point2D(length, 0),
        ]
        coords = []
        for p in raw_pts:
            p = p.rotate(orientation, tl_cornor)
            coords.append(p.x)
            coords.append(p.y)
        self.id = canvas.create_polygon(coords, fill=color, outline=color)
        self.pose = Pose2D(
            Point2D(
                self.canvas_width//2, self.canvas_height//2
            ),
            0
        )
        self.last_pose = deepcopy(self.pose)

    def getVetexEdges(self, pose=None):
        vertex = []
        edges = []
        coords = self.canvas.coords(self.id)
        index = 0
        for i in range(0, len(coords), 2):
            vertex.append(Point2D(coords[i], coords[i+1]))
            edges.append((index, int((index+1) % (len(coords)/2))))
            index += 1
        return vertex, edges





class Zone(GameObject):
    def __init__(self, canvas, tl_cornor, side_length, orientation, team):
        GameObject.__init__(self, canvas, None)
        raw_pts = [
            tl_cornor+Point2D(side_length*0.02, side_length*0.02),
            tl_cornor+Point2D(0, side_length)+Point2D(side_length*0.02, -side_length*0.02),
            tl_cornor+Point2D(side_length, side_length)+Point2D(-side_length*0.02, -side_length*0.02),
            tl_cornor+Point2D(side_length, 0)+Point2D(-side_length*0.02, side_length*0.02),
        ]
        coords = []
        for p in raw_pts:
            p = p.rotate(orientation, tl_cornor)
            coords.append(p.x)
            coords.append(p.y)
        self.id = canvas.create_polygon(coords, fill='', outline=team, width=side_length*0.04)







class Robot2DPos(Pose2D):
    def __init__(self, center, dir):
        """
        dir: the radian between robot facing direction and the left direction on 2d map
        """
        Pose2D.__init__(self, center, dir)

    def getRobotPoints(self, robot_2d_model):
        half_x = robot_2d_model.width // 2
        half_y = robot_2d_model.height // 2

        # top_left_point = Point2D( -half_x, -half_y)
        top_left_point = Point2D(self.position.x - half_x, self.position.y - half_y)
        top_right_point = Point2D( top_left_point.x + robot_2d_model.width, top_left_point.y)
        bottom_right_point = Point2D(top_left_point.x + robot_2d_model.width, top_left_point.y + robot_2d_model.height)
        bottom_left_point = Point2D(top_left_point.x, top_left_point.y + robot_2d_model.height)
        front_point = Point2D(top_left_point.x - half_x//2, self.position.y)

        top_left_point = top_left_point.rotate(self.orientation, self.position)
        top_right_point = top_right_point.rotate(self.orientation, self.position)
        bottom_right_point = bottom_right_point.rotate(self.orientation, self.position)
        bottom_left_point = bottom_left_point.rotate(self.orientation, self.position)
        front_point = front_point.rotate(self.orientation, self.position)

        return (top_left_point, top_right_point, bottom_right_point, bottom_left_point, front_point)

class Robot2D(ComplexGameObject):
    def __init__(self, team, robot_2d_pos, robot_2d_model, vel_2d, canvas, id):
        ComplexGameObject.__init__(self, canvas, pose=robot_2d_pos)
        self.team = team # red or blue
        self.robot_model = robot_2d_model
        self.vel = vel_2d
        self.ids = list()
        self.draw()
        self.update()

    def getVetexEdges(self, pose=None):
        if pose is None:
            pose = self.last_pose
        vertex = []
        edges = []
        raw_pts = pose.getRobotPoints(self.robot_model)
        index = 0
        for p in raw_pts[:4]:
            vertex.append(p)
            edges.append((index, int((index+1) % 4)))
            index += 1
        return vertex, edges

    # def draw(self, canvas, color, thickness=1, scale=0.1):
    def draw(self, thickness=1, scale=0.1):
        raw_pts = self.pose.getRobotPoints(self.robot_model)
        coords = []
        for p in raw_pts[:4]:
            coords.append(p.x)
            coords.append(p.y)
        new_obj_id = self.canvas.create_polygon(coords)
        self.ids.append(new_obj_id)

        coords = []
        for p in raw_pts[4:]:
            coords.append(p.x)
            coords.append(p.y)
        coords.append(self.pose.position.x)
        coords.append(self.pose.position.y)
        new_obj_id = self.canvas.create_line(coords, fill=self.team, width=self.robot_model.width/12)
        self.ids.append(new_obj_id)

    def change_vel(self, velocity):
        self.vel = velocity
        self.velocity = obj_coord_2_world_coord(self.vel, self.pose)

    # def update(self):
    #     last_ball_pos = self.canvas.coords(self.id)
    #     super(Robot2D, self).update()
    #     ball_pos = self.canvas.coords(self.id)

    # def draw_as_obstical(self, img, scale=0.1):
    #     raw_pts = self.pose.getRobotPoints(self.robot_model)
    #     pts = []
    #     for pt in raw_pts[:4]:
    #         pts.append(list(pt.to_tuple(scale)))
    #     pts = np.array(pts, np.int32)
    #     pts = pts.reshape((-1,1,2))
    #     cv2.fillConvexPoly(img, pts, 0xff)

class Robot2DModel:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __mul__(self, scale):
        return Robot2DModel(self.width*scale, self.height*scale)
ICRA_2019_ROBOT_MODEL = Robot2DModel(600, 480)  # Millimeter

class Velocity2D:
    def __init__(self, linear, angular_z):
        self.linear = linear
        self.angular_z = angular_z
