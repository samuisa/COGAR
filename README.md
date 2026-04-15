# COGAR

# Subgroup K2: Localization with G1 EDU in Gazebo

# Assignment 2: Standalone Localization Benchmark for Humanoid Robot Indoor Operation (SIMULATION)

What to do: Develop and evaluate a standalone localization framework for the G1 EDU robot in Gazebo using ROS2 Humble, comparing multiple pose estimation methods in indoor environments with known maps and ground truth
1) Set up the G1 EDU robot or equivalent mobile robot base in Gazebo with LiDAR and/or RGB‑D sensing
2) Use a fixed indoor map provided directly in Gazebo for localization experiments
3) Implement one or more localization methods (e.g. AMCL, ICP scan matching, visual localization, RGB‑D relocalization)
4) Create localization benchmark scenarios including nominal conditions, sensor noise, dynamic obstacles, and kidnapped robot recovery
5) Measure translational and rotational localization error, convergence time, and robustness to disturbances
6) Compare localization performance across sensor modalities (LiDAR only, RGB‑D only, multimodal)
7) Analyze which localization strategy is most robust for indoor robot operation
   
Software needed: Gazebo, ROS2 Humble, Nav2 localization stack, AMCL / RTAB‑Map / ICP / Open3D / PCL, RViz2

Research needed: Indoor localization methods, scan matching, Monte Carlo localization, visual relocalization, sensor fusion for robot pose estimation

Deliverables: Standalone localization benchmark pipeline, quantitative comparison across localization methods, robustness evaluation report, recommended localization strategy


# Command robot spawn

```bash

source /opt/ros/humble/setup.bash
colcon build
source install/local_setup.sh

ros2 launch bme_gazebo_sensors spawn_robot_ex.launch.py

```

In the RVIZ2 simulation select **pelvis** as fixed frame for the G1 robot

# Stating point:
- The robot Unitree G1 29 degrees of freedom (DOF).
- 3D LIDAR (LIVOX-MID360) + Depth Camera Intel RealSense (D435i)
