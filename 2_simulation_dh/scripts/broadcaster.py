#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TransformStamped
from rclpy import qos
import tf2_ros as tf
import numpy as np
import math
import sys

def get_transform(x, y, z, orientation, link, base):

    temp = TransformStamped()

    temp.header.stamp, temp.header.frame_id, temp.child_frame_id = node.get_clock().now().to_msg(), base, link
    temp.transform.translation.x, temp.transform.translation.y, temp.transform.translation.z = float(x), float(y), float(z)
    temp.transform.rotation.x, temp.transform.rotation.y, temp.transform.rotation.z, temp.transform.rotation.w = orientation[0], orientation[1], orientation[2], orientation[3]
    
    return temp

def quaternion_from_euler(ai, aj, ak):
    ai /= 2.0
    aj /= 2.0
    ak /= 2.0
    ci = math.cos(ai)
    si = math.sin(ai)
    cj = math.cos(aj)
    sj = math.sin(aj)
    ck = math.cos(ak)
    sk = math.sin(ak)
    cc = ci*ck
    cs = ci*sk
    sc = si*ck
    ss = si*sk

    q = np.empty((4, ))
    q[0] = cj*sc - sj*cs
    q[1] = cj*ss + sj*cc
    q[2] = cj*cs - sj*sc
    q[3] = cj*cc + sj*ss

    return q

def broadcaster():
    
    # Tracing from base and link1
    global d1, a2, new_d1, new_a2, new_alpha1, new_alpha3, theta3, new_theta3, d4, new_d4, dummy_a3, new_dummy_a3, link1_orientation, link2_orientation, link3_orientation, link4_orientation

    #Transform data is sent 
    link1_to_base.sendTransform(get_transform(0, 0, d1, link1_orientation, 'link1', 'base'))
    link2_to_link1.sendTransform(get_transform(a2, 0, 0, link2_orientation, 'link2', 'link1'))
    link3_to_link2.sendTransform(get_transform(dummy_a3, 0, 0, link3_orientation, 'link3', 'link2'))
    link4_to_link3.sendTransform(get_transform(0, 0, d4, link4_orientation, 'link4', 'link3'))
    if new_d1 < d1:
        new_d1 = new_d1 + 0.005
        print("new_d1 updated", new_d1)
        new_link1_orientation = quaternion_from_euler(new_alpha1, 0, 0)
        mobile1_to_link1.sendTransform(get_transform(0, 0, new_d1, new_link1_orientation, 'mobile1', 'base'))            
    if new_alpha1 < alpha1 and new_d1>= d1:
        print("mobile1_to_link1")
        new_alpha1 = new_alpha1 + 0.015
        print("new_alpha1 updated", new_alpha1)
        new_link1_orientation = quaternion_from_euler(new_alpha1, 0, 0)
        mobile1_to_link1.sendTransform(get_transform(0, 0, new_d1, new_link1_orientation, 'mobile1', 'base'))            
    
    # Tracing from link1 and link2
    if new_alpha1 >= alpha1 and new_d1 >= d1 and new_a2 < a2 :            
        print("mobile2_to_link2")
        if new_a2 < a2:
            new_a2 = new_a2 + 0.005
            print("new_a2 updated", new_a2)
            mobile2_to_link2.sendTransform(get_transform(new_a2, 0, 0, link2_orientation, 'mobile2', 'link1'))
        
    # Tracing from link2 and link3
    if new_alpha1 >= alpha1 and new_d1 >= d1 and new_a2 >= a2 :            
        print("mobile3_to_link3")
        if new_theta3 < theta3:
            new_theta3 = new_theta3 + 0.015
            new_link3_orientation = quaternion_from_euler(new_alpha3, 0, new_theta3)
            mobile3_to_link3.sendTransform(get_transform(0, 0, 0, new_link3_orientation, 'mobile3', 'link2'))
            print("new_theta3 updated", new_theta3)
        if new_alpha3 < alpha3 and new_theta3 >= theta3:
            new_alpha3 = new_alpha3 + 0.015
            new_dummy_a3 = new_dummy_a3 + 0.00095493
            new_link3_orientation = quaternion_from_euler(new_alpha3, 0, new_theta3)
            mobile3_to_link3.sendTransform(get_transform(new_dummy_a3, 0, 0, new_link3_orientation, 'mobile3', 'link2'))
            print("new_alpha3 updated", new_alpha3)
    
    # Tracing from link3 and link4
    if new_alpha1 >= alpha1 and new_d1 >= d1 and new_a2 >= a2 and new_theta3 >= theta3 and new_alpha3 >= alpha3 and new_d4 < d4:
                new_d4 = new_d4 + 0.005
                print("new_d4_updated", new_d4)
                mobile4_to_link4.sendTransform(get_transform(0, 0, new_d4, link4_orientation, 'mobile4', 'link3'))       

    # All parameters values are reset
    if new_alpha1 >= alpha1 and new_d1 >= d1 and new_a2 >= a2 and new_theta3 >= theta3 and new_alpha3 >= alpha3 and new_d4 >= d4:
        print("all values of theta,d,alpha,a rest")
        new_alpha1 = 0
        new_d1 = 0
        new_a2 = 0
        new_theta3 = 0
        new_alpha3 = 0
        new_d4 = 0
        new_dummy_a3 = 0

if __name__ == "__main__":

    global d1, a2, new_d1, new_a2, new_alpha1, new_alpha3, theta3, new_theta3, d4, new_d4, dummy_a3, new_dummy_a3, link1_orientation, link2_orientation, link3_orientation, link4_orientation
    rclpy.init(args=sys.argv)
    node = Node('simulation_dh')

    #tf broadcaster defined
    link1_to_base = tf.TransformBroadcaster(node)
    mobile1_to_link1 = tf.TransformBroadcaster(node)
    link2_to_link1 = tf.TransformBroadcaster(node)
    mobile2_to_link2 = tf.TransformBroadcaster(node)
    link3_to_link2 = tf.TransformBroadcaster(node)
    mobile3_to_link3 = tf.TransformBroadcaster(node)
    link4_to_link3 = tf.TransformBroadcaster(node)
    mobile4_to_link4 = tf.TransformBroadcaster(node)
    
    #DH parameters for link 1
    alpha1 = math.pi/2
    link1_orientation = quaternion_from_euler(alpha1, 0, 0)
    new_alpha1 = 0 
    d1 = 0.5
    new_d1 = 0
    
    #DH parameters for link 2
    a2 = 0.5
    new_a2 = 0
    link2_orientation = quaternion_from_euler(0, 0, 0)
    
    #DH parameters for link 3
    theta3 = math.pi/2
    new_theta3 = 0
    alpha3 = math.pi/2
    new_alpha3 = 0
    dummy_a3 = 0.1
    new_dummy_a3 = 0
    link3_orientation = quaternion_from_euler(alpha3, 0, theta3)

    #DH parameters for link 4
    d4 = 0.5
    new_d4 = 0
    link4_orientation = quaternion_from_euler(0, 0, 0)
    
    #Transform data is sent 
    link1_to_base.sendTransform(get_transform(0, 0, d1, link1_orientation, 'link1', 'base'))
    link2_to_link1.sendTransform(get_transform(a2, 0, 0, link2_orientation, 'link2', 'link1'))
    link3_to_link2.sendTransform(get_transform(dummy_a3, 0, 0, link3_orientation, 'link3', 'link2'))
    link4_to_link3.sendTransform(get_transform(0, 0, d4, link4_orientation, 'link4', 'link3'))
    node.create_timer(0.2, broadcaster)
    rclpy.spin(node)
    rclpy.shutdown()