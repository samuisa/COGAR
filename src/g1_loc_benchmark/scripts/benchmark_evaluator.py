#!/usr/bin/env python3
## @file benchmark_evaluator.py
#  @brief Evaluator to compare estimated odometry against Ground Truth.
#  @details Exports error results (translation/rotation) into a CSV file.

import rclpy
from rclpy.node import Node
import math
import csv
import time
import os
import sys
import datetime
import argparse  
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry

def get_yaw_from_quaternion(q):
    """!
    @brief Extracts the yaw angle from a quaternion.
    
    @param q Quaternion object (with x, y, z, w members).
    @return Yaw angle expressed in radians.
    """
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)

class LocalizationBenchmark(Node):
    """!
    @brief Node that calculates the error between the Ground Truth pose and the AMCL estimate.
    
    @details Subscribes to the /ground_truth_pose and /amcl_pose topics, comparing the two poses 
             and periodically saving the metrics in a CSV file for analysis.
    """

    def __init__(self, scenario_name="amcl"):
        """!
        @brief Initializes the node and configures the data log file.
        
        @param scenario_name Destination folder name to isolate different experiments.
        """
        super().__init__('localization_benchmark')
        
        # 1. Dynamic configuration of the destination folder
        output_dir = f'/workspace/results/{scenario_name}'
            
        # 2. Safely create the folder and parents (if they don't exist)
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. Create unique file with timestamp to avoid overwriting old tests
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = os.path.join(output_dir, f'localization_results_{timestamp}.csv')
        
        self.sub_gt = self.create_subscription(Odometry, '/ground_truth_pose', self.gt_callback, 10)
        self.sub_amcl = self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_callback, 10)
        
        self.latest_gt_pose = None
        self.start_time = time.time()
        
        # Initialize CSV file
        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time_s', 'Error_Translation_m', 'Error_Rotation_deg', 'GT_X', 'GT_Y', 'AMCL_X', 'AMCL_Y'])
            
        self.get_logger().info('🟢 Benchmark Started! Waiting for data...')
        self.get_logger().info(f'📁 Data will be saved in: {self.csv_filename}')

    def gt_callback(self, msg):
        """!
        @brief Saves the real pose (Ground Truth) when received.
        
        @param msg nav_msgs/Odometry message containing real data.
        """
        self.latest_gt_pose = msg.pose.pose

    def amcl_callback(self, msg):
        """!
        @brief Calculates the error between the received AMCL pose and the GT pose.
        
        @param msg geometry_msgs/PoseWithCovarianceStamped message containing the AMCL estimate.
        """
        if self.latest_gt_pose is None:
            return 
            
        amcl_x = msg.pose.pose.position.x
        amcl_y = msg.pose.pose.position.y
        amcl_yaw = get_yaw_from_quaternion(msg.pose.pose.orientation)
        
        gt_x = self.latest_gt_pose.position.x
        gt_y = self.latest_gt_pose.position.y
        gt_yaw = get_yaw_from_quaternion(self.latest_gt_pose.orientation)
        
        error_trans = math.sqrt((amcl_x - gt_x)**2 + (amcl_y - gt_y)**2)
        
        error_rot_rad = abs(amcl_yaw - gt_yaw)
        if error_rot_rad > math.pi:
            error_rot_rad = 2 * math.pi - error_rot_rad
        error_rot_deg = math.degrees(error_rot_rad)
        
        t_elapsed = time.time() - self.start_time
        
        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                round(t_elapsed, 2), 
                round(error_trans, 4), 
                round(error_rot_deg, 2),
                round(gt_x, 4), 
                round(gt_y, 4), 
                round(amcl_x, 4), 
                round(amcl_y, 4)
            ])
            
        self.get_logger().info(f'Error: {error_trans:.3f}m | X: {gt_x:.2f}, Y: {gt_y:.2f}')

def main(args=None):
    """!
    @brief Entry point for the Benchmark Evaluator.
    
    @param args Default ROS 2 arguments and custom options like --scenario.
    """
    # Use argparse to safely capture the "--scenario" argument
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', type=str, default='amcl')
    
    # parse_known_args intercepts our parameters and ignores garbage added by ROS (--ros-args)
    parsed_args, unknown = parser.parse_known_args()
    scenario = parsed_args.scenario

    rclpy.init(args=args)
    
    node = LocalizationBenchmark(scenario_name=scenario)
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info(f'🛑 Benchmark stopped. Data saved in {node.csv_filename}')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()