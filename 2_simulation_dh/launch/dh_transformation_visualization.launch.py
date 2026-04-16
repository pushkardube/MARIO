#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument,  ExecuteProcess, RegisterEventHandler
from launch.substitutions import Command
from launch_ros.actions import Node
import launch_ros.actions
from launch.event_handlers import (OnProcessStart, OnProcessExit)
from launch_ros.descriptions import ParameterValue
import random

# this is the main function, which the launch system will look for and execute

def generate_launch_description():
    package_description = "simulation_dh"
    
# creating the node 'rviz_launch' which will launch RVIZ simulator
    rviz_launch = Node(
    
# defining the package that should be executed
            package='rviz2', 
            namespace='',
            executable='rviz2',
            name='rviz2',
# defining the parameters that are to be used during the simulation, and passing the argument
            parameters=[{'use_sim_time' : True}],
            arguments=['-d' + os.path.join(get_package_share_directory(package_description), 'rviz', 'rviz_config.rviz')]
        )
# creating an object of type 'node' in ros2
    python_node = Node(
        package=package_description,
        executable='broadcaster.py'
    )
    return LaunchDescription([  
        python_node,
        rviz_launch,
    ])

