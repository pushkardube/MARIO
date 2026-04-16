#!/usr/bin/env python3
# MIT License

# Copyright (c) 2024 Society of Robotics and Automation

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import rclpy
import sys
from rclpy import qos
from geometry_msgs.msg import Twist

def draw_circle():
    global pub_vel
    msg = Twist()
    msg.linear.x = 3.0
    msg.angular.z = 5.0   
    pub_vel.publish(msg)

def main(args=None):
    rclpy.init(args=sys.argv)
    global pub_vel
    node = rclpy.create_node("Circle")
    pub_vel = node.create_publisher(Twist,"turtle1/cmd_vel",qos_profile=qos.qos_profile_parameters)
    node.get_logger().info("Circle started")
    timer = node.create_timer(0.1,draw_circle)
    try:
        rclpy.spin(node)  # Spin only one node to handle callbacks
    except KeyboardInterrupt:
        pass

    rclpy.shutdown()
    
if __name__=="__main__":
    main()
