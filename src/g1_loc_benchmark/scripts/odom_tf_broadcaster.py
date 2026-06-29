#!/usr/bin/env python3
## @file odom_tf_broadcaster.py
#  @brief Broadcasting of spatial transforms (TF) to connect odometry.
#  @details Transforms and publishes the odometry from /odom onto the TF tree by creating the 
#           odom -> base_footprint and base_footprint -> base_link connections.

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
import math

class OdomTFBroadcaster(Node):
    """!
    @brief Node acting as a bridge by publishing odom coordinates in the TF tree.
    """

    def __init__(self):
        """!
        @brief Configures the topic subscriber and the TF broadcaster.
        """
        super().__init__('odom_tf_broadcaster')
        self.sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.tf_broadcaster = TransformBroadcaster(self)

    def odom_cb(self, msg: Odometry):
        """!
        @brief Callback executed on each odometric update.
        
        @details Transforms the Odometry message into two TransformStamped and publishes them. 
                 Keeps base_footprint rooted to the ground by zeroing heights.
        
        @param msg Incoming message from the /odom topic.
        """
        t1 = TransformStamped()
        t1.header.stamp = msg.header.stamp
        t1.header.frame_id = 'odom'
        t1.child_frame_id = 'base_footprint'
        
        t1.transform.translation.x = msg.pose.pose.position.x
        t1.transform.translation.y = msg.pose.pose.position.y
        t1.transform.translation.z = 0.0 
        
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        t1.transform.rotation.x = 0.0
        t1.transform.rotation.y = 0.0
        t1.transform.rotation.z = math.sin(yaw / 2.0)
        t1.transform.rotation.w = math.cos(yaw / 2.0)
        
        # 2. BASE_FOOTPRINT -> BASE_LINK (The bridge that saves RTAB-Map!)
        t2 = TransformStamped()
        t2.header.stamp = msg.header.stamp
        t2.header.frame_id = 'base_footprint'
        t2.child_frame_id = 'base_link'
        
        t2.transform.translation.x = 0.0
        t2.transform.translation.y = 0.0
        t2.transform.translation.z = 0.0
        t2.transform.rotation.x = 0.0
        t2.transform.rotation.y = 0.0
        t2.transform.rotation.z = 0.0
        t2.transform.rotation.w = 1.0

        # Simultaneous broadcast
        self.tf_broadcaster.sendTransform([t1, t2])

def main():
    """!
    @brief Starts the OdomTFBroadcaster node.
    """
    rclpy.init()
    node = OdomTFBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()