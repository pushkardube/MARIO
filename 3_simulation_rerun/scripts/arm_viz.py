#!/usr/bin/env python3
import math
import sys
import threading
import numpy as np
import rerun as rr
import trimesh
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

MESH_DIR = Path(get_package_share_directory("simulation_rerun")) / "meshes"

GRAY   = [160, 160, 160, 255]
BLUE   = [202, 209, 238, 255]
SILVER = [198, 193, 188, 255]

LINKS = [
    ("robot/base_link",  "base_link.STL",  GRAY,   [ 0.0,    0.0,    0.0    ]),
    ("robot/link_1",     "link_1.STL",     BLUE,   [ 0.0,    0.0,    0.0    ]),
    ("robot/link_2",     "link_2.STL",     BLUE,   [ 0.0,    0.0,    0.0    ]),
    ("robot/link_3",     "link_3.STL",     BLUE,   [ 0.0,    0.0,    0.0    ]),
    ("robot/claw_right", "claw_right.STL", SILVER, [ 0.0,    0.0,    0.0    ]),
    ("robot/claw_left",  "claw_left.STL",  SILVER, [ 0.0,   -0.014,  0.0075 ]),
]


def rot(axis, angle):
    ax, ay, az = np.array(axis, dtype=float)
    c, s, t = math.cos(angle), math.sin(angle), 1.0 - math.cos(angle)
    return np.array([
        [t*ax*ax + c,    t*ax*ay - s*az, t*ax*az + s*ay],
        [t*ax*ay + s*az, t*ay*ay + c,    t*ay*az - s*ax],
        [t*ax*az - s*ay, t*ay*az + s*ax, t*az*az + c   ],
    ])


def tf(R, t):
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def fk(theta_base, theta_shoulder, theta_elbow, theta_claw1, theta_claw2):
    T0 = np.eye(4)
    T1 = T0 @ tf(rot([0,  0, 1], theta_base),    [-0.0030196,  0.046937,   0.0635   ])
    T2 = T1 @ tf(rot([0, -1, 0], theta_shoulder), [ 0.00031511,-0.0095653,  0.034407 ])
    T3 = T2 @ tf(rot([0, -1, 0], theta_elbow),    [ 0.071531,   0.011279,  -0.0041348])
    T4 = T3 @ tf(rot([-1, 0, 0], theta_claw1),   [ 0.020925,  -0.013767,  -0.090331 ])
    T5 = T3 @ tf(rot([ 1, 0, 0], theta_claw2),   [ 0.0091023,  0.0182709, -0.090512 ])
    return [T0, T1, T2, T3, T4, T5]


def load_meshes():
    meshes = {}
    for entity, stl, color, offset in LINKS:
        mesh = trimesh.load(str(MESH_DIR / stl), force="mesh")
        verts = np.array(mesh.vertices, dtype=np.float32) + np.array(offset, dtype=np.float32)
        faces = np.array(mesh.faces,    dtype=np.uint32)
        colors = np.tile(color, (len(verts), 1)).astype(np.uint8)
        meshes[entity] = rr.Mesh3D(
            vertex_positions=verts,
            triangle_indices=faces,
            vertex_colors=colors,
        )
    return meshes


class ArmPublisher(Node):
    def __init__(self, meshes):
        super().__init__("arm_publisher")
        self.pub = self.create_publisher(JointState, "/joint_states", 10)
        self.meshes = meshes
        self.step = 0
        for entity, mesh in self.meshes.items():
            rr.log(entity, mesh, static=True)
        self.get_logger().info("MARIO Robot Arm — Joint State Publisher")

    def publish_joints(self, theta_base, theta_shoulder, theta_elbow, gripper_open):
        # Motor publishing: 180-angle inversion for servo direction
        rad_base = (180.0 - theta_base) * math.pi / 180.0
        rad_shoulder = (180.0 - theta_shoulder) * math.pi / 180.0
        rad_elbow = (180.0 - theta_elbow) * math.pi / 180.0
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

        # Rerun visualization: use the raw user angles (not inverted) for the 3D model
        vis_rad = [a * math.pi / 180.0 for a in [theta_base, theta_shoulder, theta_elbow]]
        vis_claw = gripper_rad / 2
        transforms = fk(vis_rad[0], vis_rad[1], vis_rad[2], vis_claw, vis_claw)
        rr.set_time("pose", sequence=self.step)
        for (entity, *_), T in zip(LINKS, transforms):
            rr.log(entity, rr.Transform3D(translation=T[:3, 3], mat3x3=T[:3, :3]))
        self.step += 1


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
    rr.init("mario_arm", spawn=True)

    rr.log("world", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)
    rr.log("robot", rr.Transform3D(translation=[0, 0, 0]), static=True)

    print("Loading meshes...")
    meshes = load_meshes()

    node = ArmPublisher(meshes)

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
