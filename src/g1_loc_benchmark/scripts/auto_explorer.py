#!/usr/bin/env python3
## @file auto_explorer.py
#  @brief ROS 2 node for the autonomous exploration of the robot (Random Walk).
#  @details Implements an obstacle avoidance logic based on LaserScan data.

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data
import math
import random
import time

class AutoExplorer(Node):
    """!
    @brief Node that handles random movements to map the environment.
    
    @details Subscribes to the /scan topic to read obstacle distances and publishes
             commands on the /cmd_vel topic to guide the robot while avoiding 
             collisions using a simple heuristic approach.
    """

    def __init__(self):
        """!
        @brief Constructor of the AutoExplorer class.
        
        @details Initializes publishers/subscribers and defines the kinematic parameters
                 and safety distances of the robot.
        """
        super().__init__('auto_explorer')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, qos_profile_sensor_data)
        
        # OPTIMIZED PARAMETERS
        self.speed_linear = 0.25   # Cruising speed
        self.speed_angular = 0.40  # Rotation speed
        self.safe_distance = 0.6   # Safety distance from the wall
        
        # Robot state
        self.is_turning = False
        self.turn_direction = 1.0
        self.turn_end_time = 0.0   # Timer to force direction change
        
        self.get_logger().info("🤖 Autonomous Explorer V4 started! (Random Walk for SLAM)")

    def scan_callback(self, msg):
        """!
        @brief Callback executed upon receiving a new LaserScan message.
        
        @param msg sensor_msgs/LaserScan message containing LiDAR data.
        """
        num_rays = len(msg.ranges)
        if num_rays == 0:
            return
            
        def get_min_dist(start_idx, end_idx):
            """!
            @brief Extracts the minimum measured distance in a specific cone.
            
            @param start_idx Starting index of the rays to consider.
            @param end_idx Ending index of the rays to consider.
            @return Minimum valid distance found (in meters). Returns 10.0 if no valid obstacle is found.
            """
            valid_rays = []
            # Circular index management (for 360° Lidar)
            for i in range(int(start_idx), int(end_idx)):
                idx = i % num_rays
                r = msg.ranges[idx]
                # Filter invalid or too close values (sensor noise)
                if not math.isinf(r) and not math.isnan(r) and r > 0.05:
                    valid_rays.append(r)
            return min(valid_rays) if valid_rays else 10.0

        # VISION CONE
        center_idx = num_rays // 2
        offset = num_rays // 8  # Wider cone to avoid getting stuck on the sides

        right_dist = get_min_dist(center_idx - offset*3, center_idx - offset)
        front_dist = get_min_dist(center_idx - offset, center_idx + offset)
        left_dist  = get_min_dist(center_idx + offset, center_idx + offset*3)

        cmd = Twist()
        current_time = time.time()

        # "RANDOM WALK" LOGIC TO EXPLORE ROOMS
        if self.is_turning:
            # Keep turning until the random timer expires AND the path is clear
            if current_time < self.turn_end_time or front_dist < self.safe_distance + 0.2:
                cmd.linear.x = 0.0
                cmd.angular.z = self.speed_angular * self.turn_direction
            else:
                # Timer expired and path clear ahead: exit rotation
                self.is_turning = False
                self.get_logger().info("Clear path, starting towards a new area.")
                cmd.linear.x = self.speed_linear
                cmd.angular.z = 0.0
        else:
            if front_dist > self.safe_distance:
                # Clear path: Go straight
                cmd.linear.x = self.speed_linear
                cmd.angular.z = 0.0
            else:
                # Obstacle found: start a new rotation phase
                self.is_turning = True
                
                # Choose how long to turn (between 1 and 3 seconds) to vary the exit angle
                turn_duration = random.uniform(1.0, 3.0)
                self.turn_end_time = current_time + turn_duration
                
                # Choose the clearest direction to turn
                if left_dist > right_dist:
                    self.turn_direction = 1.0
                    self.get_logger().info(f"Wall at {front_dist:.2f}m! Turning LEFT for {turn_duration:.1f}s.")
                else:
                    self.turn_direction = -1.0
                    self.get_logger().info(f"Wall at {front_dist:.2f}m! Turning RIGHT for {turn_duration:.1f}s.")
                
                cmd.linear.x = 0.0
                cmd.angular.z = self.speed_angular * self.turn_direction

        self.cmd_pub.publish(cmd)

def main(args=None):
    """!
    @brief Main function to initialize and run the node.
    
    @param args Default arguments passed to ROS 2.
    """
    rclpy.init(args=args)
    node = AutoExplorer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Exploration interrupted by the user.")
    finally:
        # Stop the robot before closing the node
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()