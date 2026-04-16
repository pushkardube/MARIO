#!/usr/bin/env python3
import math
import sys
import threading
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header


class ArmPublisher(Node):
    def __init__(self):
        super().__init__("arm_publisher")
        self.pub = self.create_publisher(JointState, "/joint_states", 10)
        self.get_logger().info("MARIO Robot Arm — Joint State Publisher")

    def publish_joints(self, theta_base, theta_shoulder, theta_elbow, gripper_open):
        rad_base = theta_base * math.pi / 180.0
        rad_shoulder = theta_shoulder * math.pi / 180.0
        rad_elbow = theta_elbow * math.pi / 180.0
        gripper_rad = math.pi / 2 if gripper_open else 0.0

        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ["base", "shoulder", "elbow", "gripper"]
        msg.position = [round(r, 4) for r in [rad_base, rad_shoulder, rad_elbow, gripper_rad]]
        msg.velocity = []
        msg.effort = []
        self.pub.publish(msg)

        print(
            f"  -> base={theta_base:.1f}  shoulder={theta_shoulder:.1f}  "
            f"elbow={theta_elbow:.1f}  gripper={'open' if gripper_open else 'closed'}"
        )
        print("  published.")


def input_loop(node, stop_event):
    while not stop_event.is_set():
        print("\n--- new pose ---")
        try:
            base = float(input("  base     [0-180] : "))
            shoulder = float(input("  shoulder [0-180] : "))
            elbow = float(input("  elbow    [0-180] : "))
            grip_in = input("  gripper  [0/1]   : ").strip()
        except (KeyboardInterrupt, EOFError):
            stop_event.set()
            break
        except ValueError:
            print("  ! enter a number")
            continue

        if grip_in not in ("0", "1"):
            print("  ! gripper must be 0 (closed) or 1 (open)")
            continue

        if not all(0.0 <= a <= 180.0 for a in [base, shoulder, elbow]):
            print("  ! angles must be in [0, 180]")
            continue

        node.publish_joints(base, shoulder, elbow, grip_in == "1")


def main():
    rclpy.init(args=sys.argv)

    node = ArmPublisher()

    stop_event = threading.Event()
    t = threading.Thread(target=input_loop, args=(node, stop_event), daemon=True)
    t.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
