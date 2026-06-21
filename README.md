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
│   └── Dockerfile.base                    # Dockerfiles (Base and Project)
├── scripts/                               # Management and Launch scripts
│   ├── docker.sh                          # Host-side script for Docker container management
│   └── launch.sh                          # Container-side script for ROS2 operations
├── src/                                   # ROS2 Workspace source code
│   ├── bme_gazebo_sensors/                # Gazebo simulation, environments, and launch files
│   ├── g1_description/                    # Robot URDF, meshes, and walking scripts
│   └── aws-robomaker-small-house-world/   # Small house indoor environment assets
├── docker-compose.yml                     # Docker Compose configuration
└── README.md

```


## Build and Run the Container

You can launch the script `./scripts/docker.sh`, which provides an interactive menu with all the commands to build, run, and enter the container.

To open additional terminals, simply run ./docker.sh again and select the option to wake up and attach to the already running container (Option 2).

## ROS 2 Commands & Simulation Setup

Once inside the container, you can use the `./scripts/launch.sh` script to easily manage all the ROS 2 nodes.

For a complete navigation setup, you just need to run the master launch file (e.g., selecting **Option 1** to launch Gazebo and spawn the robot via `master_g1_2d.launch.py`).

### RViz Configuration for Navigation
Once the simulation and RViz are running, follow these steps to initialize the robot's navigation:

1. **Set the Initial Pose:** * Ensure the *Fixed Frame* (Global Options) is set to `map`. 
   * Click on the **2D Pose Estimate** button in the top toolbar.
   * Click and drag on the grid to set the exact starting position and orientation of the robot.

2. **Visualize the Map:**
   * Click the **Add** button in the bottom-left corner.
   * Switch to the **By topic** tab.
   * Scroll down, expand the `/map` topic, and select `map`.
   * In the left panel, under the newly added Map display settings, change the **Durability Policy** to `Transient Local`. The environment map should now become visible.

3. **Send a Navigation Goal:**
   * Click on the **2D Goal Pose** button in the top toolbar.
   * Click and drag on the map to define the destination and final orientation. The robot will start planning and moving towards it.

### Testing Dynamic Obstacles
The Nav2 stack is fully equipped to handle dynamic environments. While the robot is navigating towards its goal, you can switch to the **Gazebo** window and manually move objects (like boxes or furniture) into the robot's path. 

The local costmap will detect the simulated dynamic obstacles in real-time via the LiDAR, and the robot will automatically adjust its trajectory to avoid them!