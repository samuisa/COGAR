#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class OdomTFBroadcaster(Node):
    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        
        # Nav2 cerca esattamente "odom" e "base_link"
        self.odom_frame_id = 'odom'
        self.base_frame_id = 'base_link'
        
        # Iscrizione al topic /odom (o /ground_truth_pose) in arrivo da Gazebo
        self.sub = self.create_subscription(
            Odometry,
            '/odom',  
            self.odom_cb,
            10)
            
        self.tf_broadcaster = TransformBroadcaster(self)

    def odom_cb(self, msg: Odometry):
        t = TransformStamped()
        
        # Usiamo il timestamp del messaggio originale per sincronia perfetta
        t.header.stamp = msg.header.stamp
        t.header.frame_id = self.odom_frame_id
        t.child_frame_id = self.base_frame_id
        
        # Copiamo la posizione...
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        
        # ... e la rotazione (quaternione)
        t.transform.rotation = msg.pose.pose.orientation
        
        # Pubblichiamo la TF Dinamica!
        self.tf_broadcaster.sendTransform(t)

def main():
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