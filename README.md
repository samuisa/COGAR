# Subgroup K2: Localization with G1 EDU in Gazebo

## Assignment 2: Standalone Localization Benchmark for Humanoid Robot Indoor Operation (SIMULATION)

**What to do:** Develop and evaluate a standalone localization framework for the G1 EDU robot in Gazebo using ROS2 Humble, comparing multiple pose estimation methods in indoor environments with known maps and ground truth
1) Set up the G1 EDU robot or equivalent mobile robot base in Gazebo with LiDAR and/or RGB‑D sensing
2) Use a fixed indoor map provided directly in Gazebo for localization experiments
3) Implement one or more localization methods (e.g. AMCL, ICP scan matching, visual localization, RGB‑D relocalization)
4) Create localization benchmark scenarios including nominal conditions, sensor noise, dynamic obstacles, and kidnapped robot recovery
5) Measure translational and rotational localization error, convergence time, and robustness to disturbances
6) Compare localization performance across sensor modalities (LiDAR only, RGB‑D only, multimodal)

Analyze which localization strategy is most robust for indoor robot operation
Software needed: Gazebo, ROS2 Humble, Nav2 localization stack, AMCL / RTAB‑Map / ICP / Open3D / PCL, RViz2
Research needed: Indoor localization methods, scan matching, Monte Carlo localization, visual relocalization, sensor fusion for robot pose estimation
Deliverables: Standalone localization benchmark pipeline, quantitative comparison across localization methods, robustness evaluation report, recommended localization strategy

## Project structure

The repository is organized to clearly separate the Docker infrastructure from the ROS2 application code:

```bash
.
├── docker/
│   ├── Dockerfile
│   └── Dockerfile.base               # Dockerfiles (Base and Project)
├── scripts/                # Management and Launch scripts
│   ├── docker.sh           # Host-side script for Docker container management
│   └── launch.sh           # Container-side script for ROS2 operations
├── src/                    # ROS2 Workspace source code
│   ├── bme_gazebo_sensors/ # Gazebo simulation, environments, and launch files
│   ├── g1_description/     # Robot URDF, meshes, and walking scripts
│   └── aws-robomaker-small-house-world/   # Small house indoor environment assets
│   └── bme_gazebo_sensors  # Gazebo environment
├── docker-compose.yml      # Docker Compose configuration
└── README.md

```


## Build and Run the Container

You can launch the script `./scripts/docker.sh`, which provides an interactive menu with all the commands to build, run, and enter the container.

To open additional terminals, simply run ./docker.sh again and select the option to wake up and attach to the already running container (Option 2).

## ROS2 Commands

Once inside the container, you can launch the `./scripts/launch.sh` script to easily manage all the ROS2 nodes.

For a complete simulation setup, you will need to use three separate terminals:

- First terminal: Launch Gazebo and spawn the robot (Option 1).

- Second terminal: Execute the walking script (Option 2).

- Third terminal: Start the teleop keyboard node to control the robot manually (Option 3).

