#!/usr/bin/env python3
## @file dynamic_obstacles.py
#  @brief Manager and spawner of dynamic obstacles in Gazebo.
#  @details Generates simplified models (humans) via system commands on Ignition Gazebo 
#           and manages their rhythmic locomotion.

import os
import subprocess
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

# SDF Template for a simplified "Human" (Cylinder that doesn't fall)
ACTOR_SDF = """<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="{actor_name}">
    <link name="base_link">
      <inertial>
        <pose>0 0 -0.8 0 0 0</pose> 
        <mass>50.0</mass>
        <inertia><ixx>10.0</ixx><iyy>10.0</iyy><izz>10.0</izz></inertia>
      </inertial>
      <collision name="collision">
        <geometry><cylinder><radius>0.15</radius><length>1.7</length></cylinder></geometry>
        <surface>
          <friction><ode><mu>0.0</mu><mu2>0.0</mu2></ode></friction>
        </surface>
      </collision>
      <visual name="visual">
        <geometry><cylinder><radius>0.15</radius><length>1.7</length></cylinder></geometry>
        <material><ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse></material>
      </visual>
    </link>
    <plugin filename="ignition-gazebo-velocity-control-system" name="ignition::gazebo::systems::VelocityControl">
      <link_name>base_link</link_name>
      <topic>/model/{actor_name}/cmd_vel</topic>
    </plugin>
  </model>
</sdf>
"""

class DynamicObstacles(Node):
    """!
    @brief Node that periodically sends velocities to Gazebo topics to animate obstacles.
    """

    def __init__(self):
        """!
        @brief Creates Twist publishers for each actor.
        """
        super().__init__('dynamic_obstacles')
        
        # Publishers for the 6 actors
        self.pub1 = self.create_publisher(Twist, '/model/actor1/cmd_vel', 10)
        self.pub2 = self.create_publisher(Twist, '/model/actor2/cmd_vel', 10)
        self.pub3 = self.create_publisher(Twist, '/model/actor3/cmd_vel', 10)
        self.pub4 = self.create_publisher(Twist, '/model/actor4/cmd_vel', 10) # New
        self.pub5 = self.create_publisher(Twist, '/model/actor5/cmd_vel', 10) # New
        self.pub6 = self.create_publisher(Twist, '/model/actor6/cmd_vel', 10) # New
        
        self.timer = self.create_timer(0.1, self.timer_cb)
        
        self.state_time = 8.0 # Reverse gear
        self.last_switch = self.get_clock().now()
        self.direction = 1.0

    def timer_cb(self):
        """!
        @brief Periodic callback that moves the actors forward and reverses their direction.
        """
        now = self.get_clock().now()
        # Check if the set time has passed
        if (now - self.last_switch).nanoseconds > (self.state_time * 1e9):
            self.direction *= -1.0
            self.last_switch = now
            self.get_logger().info(f"🔄 Actors are reversing direction!")

        # 1. Actor 1 (Red) - Moves on Y
        msg1 = Twist()
        msg1.linear.y = 0.15 * self.direction 
        
        # 2. Actor 2 (Blue) - Moves on Y
        msg2 = Twist()
        msg2.linear.y = 0.15 * self.direction

        # 3. Actor 3 (Green) - Moves on Y (Fast)
        msg3 = Twist()
        msg3.linear.y = 0.75 * self.direction
        
        # 4. Actor 4 (Yellow) - Moves on Y
        msg4 = Twist()
        msg4.linear.y = 1.5 * self.direction

        # 5. Actor 5 (Cyan) - Moves on X
        msg5 = Twist()
        msg5.linear.x = 0.15 * self.direction

        # 6. Actor 6 (Magenta) - Moves on Y
        msg6 = Twist()
        msg6.linear.y = 1.25 * self.direction

        # Publish all messages
        self.pub1.publish(msg1)
        self.pub2.publish(msg2)
        self.pub3.publish(msg3)
        self.pub4.publish(msg4)
        self.pub5.publish(msg5)
        self.pub6.publish(msg6)

def spawn_actor(name, x, y, r, g, b):
    """!
    @brief Creates an SDF file on the fly and calls the system to insert the obstacle.
    
    @param name Name of the entity in Gazebo.
    @param x Initial X coordinate.
    @param y Initial Y coordinate.
    @param r Red channel of the material (0.0-1.0).
    @param g Green channel of the material (0.0-1.0).
    @param b Blue channel of the material (0.0-1.0).
    """
    # Compile the SDF template
    sdf_content = ACTOR_SDF.format(actor_name=name, r=r, g=g, b=b)
    sdf_path = f"/tmp/{name}.sdf"
    with open(sdf_path, "w") as f:
        f.write(sdf_content)
    
    print(f"🧍 Spawning {name} at x={x}, y={y}...")
    # Use ros_gz_sim to spawn the model in Gazebo
    subprocess.run([
        "ros2", "run", "ros_gz_sim", "create", 
        "-file", sdf_path, 
        "-name", name, 
        "-x", str(x), "-y", str(y), "-z", "0.9"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(args=None):
    """!
    @brief Main function that summons the models and creates the bridge to ros_gz.
    
    @param args Standard ROS 2 arguments.
    """
    print("=========================================================")
    print("🚀 Initializing DYNAMIC OBSTACLES scenario...")
    print("=========================================================")
    
    # Original actors
    spawn_actor("actor1", x=2.0,  y=0.0,  r=1.0, g=0.2, b=0.2) # Red
    spawn_actor("actor2", x=0.0,  y=1.5,  r=0.2, g=0.2, b=1.0) # Blue
    spawn_actor("actor3", x=-2.0, y=-3.0, r=0.2, g=1.0, b=0.2) # Green
    
    # The 3 new actors
    spawn_actor("actor4", x=5.0,  y=-3.0, r=1.0, g=1.0, b=0.2) # Yellow
    spawn_actor("actor5", x=0.0,  y=2.0,  r=0.2, g=1.0, b=1.0) # Cyan
    spawn_actor("actor6", x=-5.0, y=0.0,  r=1.0, g=0.2, b=1.0) # Magenta
    
    # 2. Starting the ROS-Gazebo bridge to control actors
    print("🌉 Starting the ROS-Gazebo bridge to control actors...")
    bridge_cmd = [
        "ros2", "run", "ros_gz_bridge", "parameter_bridge",
        "/model/actor1/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist",
        "/model/actor2/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist",
        "/model/actor3/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist",
        "/model/actor4/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist", # New
        "/model/actor5/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist", # New
        "/model/actor6/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist"  # New
    ]
    bridge_process = subprocess.Popen(bridge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Starting the ROS node to move them
    rclpy.init(args=args)
    node = DynamicObstacles()
    
    try:
        print("🏃 Moving obstacles! Press CTRL+C to stop and remove them from memory.")
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n🛑 Stopping obstacles...")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        bridge_process.terminate()
        print("✅ Processes safely terminated.")

if __name__ == '__main__':
    main()