#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data
import math

class AutoExplorer(Node):
    def __init__(self):
        super().__init__('auto_explorer')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, qos_profile_sensor_data)
        
        # 🟢 PARAMETRI OTTIMIZZATI (Molto più simili al comportamento 2D)
        self.speed_linear = 0.20   # Camminata un po' più decisa
        self.speed_angular = 0.35  # Rotazione più reattiva
        self.safe_distance = 0.5   # 🔴 Ridotto a 50cm per muoversi fluidamente nella casa!
        
        self.is_turning = False
        self.turn_direction = 1.0
        
        self.get_logger().info("🤖 Mapper Autonomo V3 avviato! Parametri distanze ottimizzati per interni.")

    def scan_callback(self, msg):
        num_rays = len(msg.ranges)
        if num_rays == 0:
            return
            
        def get_min_dist(start_idx, end_idx):
            # Gestione sicura degli indici
            valid_rays = []
            for i in range(start_idx, end_idx):
                idx = i % num_rays
                r = msg.ranges[idx]
                if not math.isinf(r) and not math.isnan(r) and r > 0.05:
                    valid_rays.append(r)
            return min(valid_rays) if valid_rays else 10.0

        # 🟢 STRINGIAMO IL CONO DI VISIONE
        # Ora il robot valuta un angolo molto più stretto (ca 30°) per decidere se c'è un ostacolo dritto a lui
        center_idx = num_rays // 2
        offset = num_rays // 12 

        right_dist = get_min_dist(center_idx - offset*3, center_idx - offset)
        front_dist = get_min_dist(center_idx - offset, center_idx + offset)
        left_dist  = get_min_dist(center_idx + offset, center_idx + offset*3)

        cmd = Twist()

        # LOGICA "STOP & TURN"
        if front_dist > self.safe_distance and not self.is_turning:
            # Strada libera: Vai dritto tranquillo
            cmd.linear.x = self.speed_linear
            cmd.angular.z = 0.0
        else:
            # Ostacolo vicino o robot già in fase di rotazione
            cmd.linear.x = 0.0  # STOP ASSOLUTO dell'avanzamento per non slittare
            
            if not self.is_turning:
                # Appena vedo il muro, scelgo una direzione e mi blocco in rotazione
                self.is_turning = True
                if left_dist > right_dist:
                    self.turn_direction = 1.0
                    self.get_logger().info(f"Ostacolo a {front_dist:.2f}m! Mi fermo e giro a SINISTRA.")
                else:
                    self.turn_direction = -1.0
                    self.get_logger().info(f"Ostacolo a {front_dist:.2f}m! Mi fermo e giro a DESTRA.")
            
            # Applica solo la rotazione pura
            cmd.angular.z = self.speed_angular * self.turn_direction
            
            # 🔴 Esci dalla rotazione più velocemente (0.15 di margine invece di 0.4)
            if front_dist > self.safe_distance + 0.15:
                self.is_turning = False
                self.get_logger().info("Via libera, riparto dritto.")

        self.cmd_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = AutoExplorer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Esplorazione interrotta dall'utente.")
    finally:
        # Ferma tutto prima di spegnersi
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()