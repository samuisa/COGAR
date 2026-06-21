#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import math
import csv
import time
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry

def get_yaw_from_quaternion(q):
    """Converts a quaternion into a yaw angle in radians."""
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)

class LocalizationBenchmark(Node):
    def __init__(self):
        super().__init__('localization_benchmark')
        
        self.sub_gt = self.create_subscription(Odometry, '/ground_truth_pose', self.gt_callback, 10)
        self.sub_amcl = self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_callback, 10)
        
        self.latest_gt_pose = None
        self.start_time = time.time()
        
        self.csv_filename = 'localization_results.csv'
        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            # NEW COLUMNS ADDED HERE
            writer.writerow(['Time_s', 'Error_Translation_m', 'Error_Rotation_deg', 'GT_X', 'GT_Y', 'AMCL_X', 'AMCL_Y'])
            
        self.get_logger().info('🟢 Benchmark Started! Waiting for data...')

    def gt_callback(self, msg):
        self.latest_gt_pose = msg.pose.pose

    def amcl_callback(self, msg):
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
            # SAVING COORDINATE DATA
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
    rclpy.init(args=args)
    node = LocalizationBenchmark()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Benchmark stopped. Data saved in localization_results.csv')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()