#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import math
import csv
import time
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry

def get_yaw_from_quaternion(q):
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)

class LocalizationBenchmark(Node):
    def __init__(self):
        super().__init__('localization_benchmark')
        
        # Sottoscrizione al Ground Truth
        self.sub_gt = self.create_subscription(Odometry, '/ground_truth_pose', self.gt_callback, 10)
        
        # Sottoscrizioni MULTIPLE: il giudice ascolterà sia AMCL che RTAB-Map!
        self.sub_amcl = self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.estimate_callback, 10)
        self.sub_rtabmap = self.create_subscription(PoseWithCovarianceStamped, '/rtabmap/pose', self.estimate_callback, 10)
        
        self.latest_gt_pose = None
        self.start_time = time.time()
        
        self.csv_filename = 'localization_results.csv'
        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Colonne aggiornate con nomi generici (EST_X, EST_Y = Estimated)
            writer.writerow(['Time_s', 'Error_Translation_m', 'Error_Rotation_deg', 'GT_X', 'GT_Y', 'EST_X', 'EST_Y'])
            
        self.get_logger().info('🟢 Benchmark Universale Avviato! In attesa dei dati (AMCL o RTAB-Map)...')

    def gt_callback(self, msg):
        self.latest_gt_pose = msg.pose.pose

    def estimate_callback(self, msg):
        if self.latest_gt_pose is None:
            return 
            
        est_x = msg.pose.pose.position.x
        est_y = msg.pose.pose.position.y
        est_yaw = get_yaw_from_quaternion(msg.pose.pose.orientation)
        
        gt_x = self.latest_gt_pose.position.x
        gt_y = self.latest_gt_pose.position.y
        gt_yaw = get_yaw_from_quaternion(self.latest_gt_pose.orientation)
        
        error_trans = math.sqrt((est_x - gt_x)**2 + (est_y - gt_y)**2)
        
        error_rot_rad = abs(est_yaw - gt_yaw)
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
                round(est_x, 4), 
                round(est_y, 4)
            ])
            
        self.get_logger().info(f'Errore: {error_trans:.3f}m | X: {gt_x:.2f}, Y: {gt_y:.2f}')

def main(args=None):
    rclpy.init(args=args)
    node = LocalizationBenchmark()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Benchmark fermato. Dati salvati in localization_results.csv')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()