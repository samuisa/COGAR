#!/usr/bin/env python3
import math
from typing import List, Tuple, Dict

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class FakeWalkAnimator(Node):
    def __init__(self) -> None:
        super().__init__('fake_walk_animator')

        # --- Topic Parameters ---
        self.declare_parameter('cmd_topic', '/cmd_vel')
        self.declare_parameter('traj_topic', '/position_controller/joint_trajectory')
        self.declare_parameter('joint_state_topic', '/joint_states')
        self.declare_parameter('timer_period', 0.05) 

        # --- IK & Geometria del Robot (G1) ---
        self.declare_parameter('l1', 0.25)
        self.declare_parameter('l2', 0.25)
        self.declare_parameter('pelvis_height', 0.5)
        
        # --- Parametri del Passo ---
        self.declare_parameter('step_height', 0.08)
        self.declare_parameter('max_step_length', 0.25)
        self.declare_parameter('base_freq', 0.0)
        self.declare_parameter('speed_freq_gain', 1.5)
        
        self.declare_parameter('max_linear_speed', 0.50)
        self.declare_parameter('max_angular_speed', 1.0)
        self.declare_parameter('move_linear_threshold', 0.015)
        self.declare_parameter('move_angular_threshold', 0.04)
        self.declare_parameter('filter_alpha', 0.20)

        # Inizializzazione variabili
        self.phase = 0.0
        self.last_cmd = Twist()
        self.filtered_v = 0.0
        self.filtered_w = 0.0

        # Lettura parametri
        self.timer_period = float(self.get_parameter('timer_period').value)
        self.filter_alpha = float(self.get_parameter('filter_alpha').value)
        
        self.l1 = float(self.get_parameter('l1').value)
        self.l2 = float(self.get_parameter('l2').value)
        self.pelvis_height = float(self.get_parameter('pelvis_height').value)
        
        self.step_height = float(self.get_parameter('step_height').value)
        self.max_step_length = float(self.get_parameter('max_step_length').value)
        self.speed_freq_gain = float(self.get_parameter('speed_freq_gain').value)
        
        self.max_linear_speed = float(self.get_parameter('max_linear_speed').value)
        self.max_angular_speed = float(self.get_parameter('max_angular_speed').value)
        self.move_linear_threshold = float(self.get_parameter('move_linear_threshold').value)
        self.move_angular_threshold = float(self.get_parameter('move_angular_threshold').value)

        self.cmd_topic = str(self.get_parameter('cmd_topic').value)
        self.traj_topic = str(self.get_parameter('traj_topic').value)

        self.cmd_sub = self.create_subscription(Twist, self.cmd_topic, self.cmd_callback, 10)
        self.traj_pub = self.create_publisher(JointTrajectory, self.traj_topic, 10)

        self.timer = self.create_timer(self.timer_period, self.on_timer)

        # LA LISTA COMPLETA DEI 29 GIUNTI
        self.joint_names: List[str] = [
            'left_hip_pitch_joint', 'left_hip_roll_joint', 'left_hip_yaw_joint', 
            'left_knee_joint', 'left_ankle_pitch_joint', 'left_ankle_roll_joint',
            'right_hip_pitch_joint', 'right_hip_roll_joint', 'right_hip_yaw_joint', 
            'right_knee_joint', 'right_ankle_pitch_joint', 'right_ankle_roll_joint',
            'waist_yaw_joint', 'waist_roll_joint', 'waist_pitch_joint',
            'left_shoulder_pitch_joint', 'left_shoulder_roll_joint', 'left_shoulder_yaw_joint', 
            'left_elbow_joint', 'left_wrist_roll_joint', 'left_wrist_pitch_joint', 'left_wrist_yaw_joint',
            'right_shoulder_pitch_joint', 'right_shoulder_roll_joint', 'right_shoulder_yaw_joint', 
            'right_elbow_joint', 'right_wrist_roll_joint', 'right_wrist_pitch_joint', 'right_wrist_yaw_joint'
        ]

        # Creiamo un dizionario base con tutto a zero (fermo, rigido)
        self.base_posture: Dict[str, float] = {name: 0.0 for name in self.joint_names}
        
        # Puoi anche pre-impostare una posa per le braccia (es: un po' piegate) per farle sembrare più naturali
        self.base_posture['left_shoulder_roll_joint'] = 0.2
        self.base_posture['right_shoulder_roll_joint'] = -0.2
        self.base_posture['left_elbow_joint'] = 0.5
        self.base_posture['right_elbow_joint'] = 0.5

        # Calcoliamo la posizione di stand fissa (IK) per le gambe
        hip_stand, knee_stand, ankle_stand = self.calculate_leg_ik(0.0, self.pelvis_height)
        self.stand_posture = self.base_posture.copy()
        self.stand_posture['left_hip_pitch_joint'] = hip_stand
        self.stand_posture['right_hip_pitch_joint'] = hip_stand
        self.stand_posture['left_knee_joint'] = knee_stand
        self.stand_posture['right_knee_joint'] = knee_stand
        self.stand_posture['left_ankle_pitch_joint'] = ankle_stand
        self.stand_posture['right_ankle_pitch_joint'] = ankle_stand

        self.current_posture = self.stand_posture.copy()

    def cmd_callback(self, msg: Twist) -> None:
        self.last_cmd = msg

    @staticmethod
    def clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    def calculate_leg_ik(self, x: float, z_depth: float) -> Tuple[float, float, float]:
        max_reach = self.l1 + self.l2 - 0.001
        distance = math.hypot(x, z_depth)
        
        if distance > max_reach:
            scale = max_reach / distance
            x *= scale
            z_depth *= scale
            distance = max_reach
            
        cos_knee = (distance**2 - self.l1**2 - self.l2**2) / (2 * self.l1 * self.l2)
        cos_knee = self.clamp(cos_knee, -1.0, 1.0)
        knee_angle = math.acos(cos_knee) 
        
        alpha = math.atan2(x, z_depth)
        beta = math.atan2(self.l2 * math.sin(knee_angle), self.l1 + self.l2 * math.cos(knee_angle))
        
        hip_angle = alpha - beta
        ankle_angle = -(hip_angle + knee_angle)
        
        return hip_angle, knee_angle, ankle_angle

    def get_foot_trajectory(self, phase: float, step_length: float) -> Tuple[float, float]:
        p = (phase / (2 * math.pi)) % 1.0
        
        if p < 0.5:
            progress = p * 2.0 
            x = self.lerp(-step_length/2.0, step_length/2.0, progress)
            z_depth = self.pelvis_height - (self.step_height * math.sin(progress * math.pi))
        else:
            progress = (p - 0.5) * 2.0
            x = self.lerp(step_length/2.0, -step_length/2.0, progress)
            z_depth = self.pelvis_height
            
        return x, z_depth

    def publish_trajectory(self, posture: Dict[str, float]) -> None:
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.joint_names = self.joint_names

        pt = JointTrajectoryPoint()
        # Estrae i valori nel corretto ordine definito da self.joint_names
        pt.positions = [posture[name] for name in self.joint_names]
        pt.time_from_start.sec = 0
        pt.time_from_start.nanosec = int(self.timer_period * 1e9)

        msg.points = [pt]
        self.traj_pub.publish(msg)

    def on_timer(self) -> None:
        raw_v = float(self.last_cmd.linear.x)
        raw_w = float(self.last_cmd.angular.z)

        self.filtered_v = self.lerp(self.filtered_v, raw_v, self.filter_alpha)
        self.filtered_w = self.lerp(self.filtered_w, raw_w, self.filter_alpha)

        v = self.filtered_v
        w = self.filtered_w
        
        av = abs(v)
        aw = abs(w)

        moving = av > self.move_linear_threshold or aw > self.move_angular_threshold
        
        # Partiamo sempre dalla posa di base (tutto fermo a 0 o alle posizioni di riposo)
        target_posture = self.base_posture.copy()

        if moving:
            speed_ratio = self.clamp(v / self.max_linear_speed, -1.0, 1.0)
            freq = self.speed_freq_gain * abs(speed_ratio)
            
            if freq < 0.2 and aw > self.move_angular_threshold:
                freq = 0.5 

            self.phase = (self.phase + self.timer_period * freq * 2.0 * math.pi) % (2.0 * math.pi)

            phase_l = self.phase
            phase_r = self.phase + math.pi

            step_length = self.max_step_length * speed_ratio
            turn_bias = (w / self.max_angular_speed) * 0.10
            
            x_l, z_l = self.get_foot_trajectory(phase_l, step_length)
            x_r, z_r = self.get_foot_trajectory(phase_r, step_length)
            
            x_l += turn_bias
            x_r -= turn_bias

            lhip, lknee, lankle = self.calculate_leg_ik(x_l, z_l)
            rhip, rknee, rankle = self.calculate_leg_ik(x_r, z_r)

            arm_amp = 0.15 * abs(speed_ratio)
            larm = arm_amp * math.sin(phase_r)
            rarm = arm_amp * math.sin(phase_l)

            # Inseriamo i valori attivi per le gambe
            target_posture['left_hip_pitch_joint'] = lhip
            target_posture['right_hip_pitch_joint'] = rhip
            target_posture['left_knee_joint'] = lknee
            target_posture['right_knee_joint'] = rknee
            target_posture['left_ankle_pitch_joint'] = lankle
            target_posture['right_ankle_pitch_joint'] = rankle
            
            # Sovrascriviamo le braccia per l'animazione di oscillazione
            target_posture['left_shoulder_pitch_joint'] = larm
            target_posture['right_shoulder_pitch_joint'] = rarm
            
        else:
            self.phase *= 0.90
            target_posture = self.stand_posture.copy()

        # Smoothing finale: interpola gradualmente da current a target per evitare scatti improvvisi
        for name in self.joint_names:
            self.current_posture[name] = self.lerp(self.current_posture[name], target_posture[name], 0.20)

        self.publish_trajectory(self.current_posture)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FakeWalkAnimator()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()