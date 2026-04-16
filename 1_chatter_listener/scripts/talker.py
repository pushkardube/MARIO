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

## A multiple talker demo that published std_msgs/Strings messages
## to the 3 different 'talker' topics 

import sys
import rclpy
from rclpy import qos
from std_msgs.msg import String
 


def timer_call():
    msg = String()
    msg.data = "Hello from SRA%d %d" %(timer_call.id,timer_call.counter)
    if timer_call.id==1:
        pub1.publish(msg)
    elif timer_call.id == 2:
        pub2.publish(msg)
    elif timer_call.id == 3:
        pub3.publish(msg)           
                
    node.get_logger().info('Publishing: "%s"' % msg.data)
    timer_call.counter += 1
    if timer_call.counter > 50:
        timer_call.counter = 1
        timer_call.id += 1
    if timer_call.id > 3:
        timer_call.id = 1
     

def main(args=None):
    rclpy.init(args=sys.argv)       
    
    global node,pub1,pub2,pub3
    node = rclpy.create_node("talker")
    pub1 = node.create_publisher(String, "talker_1", qos_profile=qos.qos_profile_parameters)
    pub2 = node.create_publisher(String, "talker_2", qos_profile=qos.qos_profile_parameters)
    pub3 = node.create_publisher(String, "talker_3", qos_profile=qos.qos_profile_parameters)
    timer_call.counter = 1
    timer_call.id = 1
    timer = node.create_timer(0.1,timer_call)


    
    try:
        rclpy.spin(node)  # Spin only one node to handle callbacks
    except KeyboardInterrupt:
        pass

    rclpy.shutdown()

if __name__ == "__main__":
    main()



    

