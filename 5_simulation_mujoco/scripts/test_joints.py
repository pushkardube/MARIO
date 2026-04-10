import mujoco
import mujoco.viewer
import numpy as np
import threading
import time
import queue

model = mujoco.MjModel.from_xml_path('/Users/abhi/sra/MARIO/5_simulation_mujoco/models/manipulator.xml')
data = mujoco.MjData(model)

cmd_queue = queue.Queue()
running = [True]

def input_loop():
    print("\nJoint test - enter values in degrees")
    print("Format: j1 j2 j3")
    print("Example: 90 45 30")
    print("Type 'q' to quit\n")
    while running[0]:
        try:
            line = input("> ")
        except EOFError:
            running[0] = False
            return
        if line.strip().lower() == 'q':
            running[0] = False
            return
        try:
            vals = [float(x) for x in line.strip().split()]
            if len(vals) != 3:
                print("Need 3 values")
                continue
            cmd_queue.put(vals)
            print(f"Queued: {vals}")
        except ValueError:
            print("Invalid")

t = threading.Thread(target=input_loop, daemon=True)
t.start()

with mujoco.viewer.launch_passive(model, data) as viewer:
    while viewer.is_running() and running[0]:
        while not cmd_queue.empty():
            vals = cmd_queue.get()
            data.ctrl[0] = np.radians(vals[0])
            data.ctrl[1] = np.radians(vals[1])
            data.ctrl[2] = np.radians(-vals[2]) + np.radians(10)  # negated, real zero is at +10 deg physical
            
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)

running[0] = False
