# COGAR

# Subgroup K2: Localization with G1 EDU in Gazebo

## Assignment 2: Standalone Localization Benchmark for Humanoid Robot Indoor Operation (SIMULATION)

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


## Command robot spawn

```bash

source /opt/ros/humble/setup.bash &&
colcon build &&
source /opt/ros/humble/setup.bash
colcon build
source install/local_setup.sh

ros2 launch bme_gazebo_sensors spawn_robot_ex.launch.py

```

## Simulation Environment

The simulation utilizes the `small_house.sdf` world from the `aws-robomaker-small-house-world` repository as the primary environment for the G1 robot. The layout, featuring several distinct rooms, facilitates the simulation of the **"kidnapped robot scenario,"**

## Sensors and Visualization (RViz2)

The G1 robot is configured with a complete perception system integrated into Gazebo Ignition. Data is transmitted to ROS 2 via the `parameter_bridge` using the following standardized topics:

### Sensor Topics
- **LiDAR (Mid360)**: 
    1. ROS 2 Topic: `/lidar/points`
    2. Msg Type: `sensor_msgs/PointCloud2`
- **RGB Camera**:
    1. ROS 2 Topic: `/camera/color/image_raw`
    2. Msg Type: `sensor_msgs/Image`
- **Depth Camera**:
    1. ROS 2 Topic: `/camera/depth/image_raw`
    2. Msg Type: `sensor_msgs/Image`
- **Camera Info**:
    1. ROS 2 Topic: `/camera/color/camera_info`
    2. Msg Type: `sensor_msgs/CameraInfo`

### Visualization Guide
To correctly visualize the robot and sensor data in **RViz2**:

1. **Fixed Frame**: In the *Global Options* panel, set the `Fixed Frame` to **`pelvis`**.
2. **LiDAR**: Click `Add` -> `By Topic` and select `/lidar/points` (**PointCloud2**).
3. **Camera**: Click `Add` -> `By Topic` and select `/camera/color/image_raw` (**Image**).
4. **3D Point Cloud (Camera)**: 
   - Add the topic `/camera/depth/image_raw` using the **DepthCloud** display plugin.

# Starting point:
- The robot Unitree G1 29 degrees of freedom (DOF).
- 3D LIDAR (LIVOX-MID360) + Depth Camera Intel RealSense (D435i)
