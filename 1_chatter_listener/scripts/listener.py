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
## A multiple listenr demo that subscribes std_msgs/Strings messages
## from the 3 different 'talker' topics 

import sys
import rclpy
from std_msgs.msg import String

def cb1(node, msg:String):
    node.get_logger().info("Heard from talker1 %s" %(msg.data))

def cb2(node, msg:String):
    node.get_logger().info("Heard from talker2 %s" %(msg.data))
    
def cb3(node, msg:String):
    node.get_logger().info("Heard from talker3 %s" %(msg.data))

def main(args=None):
    rclpy.init(args=sys.argv)
    node = rclpy.create_node("listener")
    sub1 = node.create_subscription(String, "talker_1", lambda msg: cb1(node, msg), 10)
    sub2 = node.create_subscription(String, "talker_2", lambda msg: cb2(node, msg), 10)
    sub3 = node.create_subscription(String, "talker_3", lambda msg: cb3(node, msg), 10)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown() 

if __name__ == "__main__":
    main()
