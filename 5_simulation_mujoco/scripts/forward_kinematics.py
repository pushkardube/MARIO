#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import forward_kinematics_module
import math
import sys

#Transformation Matrix Calculated Parameters
d = [10, 0, 0, 13]
alpha = [math.pi/2, 0, math.pi/2, 0]
a = [0, 6, 0, 0]

def forward_kinematics_publisher():
    global node, Joints

    try:
        theta_base     = float(input("{:22s}".format("Enter theta_base (0-180): ")))
        theta_shoulder = float(input("{:22s}".format("Enter theta_shoulder (0-180): ")))
        theta_elbow    = float(input("{:22s}".format("Enter theta_elbow (0-180): ")))
        gripper_open   = float(input("{:22s}".format("Gripper (0=close / 1=open): ")))
    except ValueError:
        print("Invalid input — enter numbers only")
        return

    if not (0.0 <= theta_base <= 180.0 and
            0.0 <= theta_shoulder <= 180.0 and
            0.0 <= theta_elbow <= 180.0):
        print("Angles must be between 0 and 180 — not published")
        return

    if gripper_open not in (0.0, 1.0):
        print("Gripper must be 0 (close) or 1 (open) — not published")
        return

    theta = [theta_base, theta_shoulder, theta_elbow, 0]
    final_transformation_matrix = forward_kinematics_module.compute_coordinates(theta, d, alpha, a)

    print("*************************")
    print("{:21s}".format("x-coordinate"), "{0:.5f}".format(final_transformation_matrix[0, 3]))
    print("{:21s}".format("y-coordinate"), "{0:.5f}".format(final_transformation_matrix[1, 3]))
    print("{:21s}".format("z-coordinate"), "{0:.5f}".format(final_transformation_matrix[2, 3]))

    joint = Float64MultiArray()
    joint.data = [
        theta_base     * math.pi / 180.0,   # base (rad)
        theta_shoulder * math.pi / 180.0,   # shoulder (rad)
        theta_elbow    * math.pi / 180.0,   # elbow (rad)
        1.57 if gripper_open else 0.0,       # gripper (rad)
    ]

    print("\ntheta_base =     ", joint.data[0])
    print("theta_shoulder = ", joint.data[1])
    print("theta_elbow =    ", joint.data[2])
    print("gripper =        ", "open" if gripper_open else "closed")
    print("=========================\n")

    Joints.publish(joint)


if __name__ == '__main__':
    rclpy.init(args=sys.argv)
    global node, Joints
    node = Node('forward_kinematics_publisher')
    Joints = node.create_publisher(Float64MultiArray, '/forward_position_controller/commands', 10)
    node.create_timer(0.2, forward_kinematics_publisher)
    rclpy.spin(node)
    rclpy.shutdown()
