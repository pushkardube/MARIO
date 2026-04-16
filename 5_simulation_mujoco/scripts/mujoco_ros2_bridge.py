#!/usr/bin/env mjpython
# macOS: mujoco.viewer requires mjpython (handles AppKit main-thread requirement).
# Threading pattern: viewer owns the main thread, rclpy.spin runs in a background thread.
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
import mujoco
import mujoco.viewer
import numpy as np
import os
import time
import threading
from ament_index_python.packages import get_package_share_directory


class MujocoRosBridge(Node):
    def __init__(self):
        super().__init__('mujoco_ros_bridge')

        package_share = get_package_share_directory('simulation_mujoco')
        model_path = os.path.join(package_share, 'models', 'manipulator.xml')

        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)
        self.running = True
        self.joint_names = ['joint_1', 'joint_2', 'joint_3', 'joint_4']
        self.target_positions = np.zeros(4)

        self.joint_state_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.command_sub = self.create_subscription(
            Float64MultiArray,
            '/forward_position_controller/commands',
            self.command_callback,
            10
        )
        self.pub_timer = self.create_timer(0.02, self.publish_joint_states)

        self.get_logger().info('MuJoCo-ROS2 bridge ready')

    def command_callback(self, msg):
        if len(msg.data) >= 4:
            self.target_positions = np.array(msg.data[:4])
            self.get_logger().info(f'command: {self.target_positions}')

    def publish_joint_states(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = self.data.qpos[:4].tolist()
        msg.velocity = self.data.qvel[:4].tolist()
        msg.effort = self.data.qfrc_actuator[:4].tolist()
        self.joint_state_pub.publish(msg)

    def shutdown(self):
        self.running = False


def main(args=None):
    rclpy.init(args=args)
    node = MujocoRosBridge()

    # rclpy.spin runs in background — viewer must own the main thread on macOS
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    # Viewer on main thread (required by mjpython / macOS AppKit)
    with mujoco.viewer.launch_passive(node.model, node.data) as viewer:
        while viewer.is_running() and node.running:
            node.data.ctrl[:4] = node.target_positions
            mujoco.mj_step(node.model, node.data)
            viewer.sync()
            time.sleep(0.005)   # ~200 Hz simulation step

    node.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
