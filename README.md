# Subgroup K2: Localization with G1 EDU in Gazebo

##  Assignment 2: Standalone Localization Benchmark for Humanoid Robot Indoor Operation (SIMULATION)

What to do: Develop and evaluate a standalone localization framework for the G1 EDU robot in Gazebo using ROS2 Humble, comparing multiple pose estimation methods in indoor environments with known maps and ground truth.

1) Set up the G1 EDU robot or equivalent mobile robot base in Gazebo with LiDAR and/or RGB‑D sensing.

2) Use a fixed indoor map provided directly in Gazebo for localization experiments.

3) Implement one or more localization methods (e.g. AMCL, ICP scan matching, visual localization, RGB‑D relocalization).

4) Create localization benchmark scenarios including nominal conditions, sensor noise, dynamic obstacles, and kidnapped robot recovery.

5) Measure translational and rotational localization error, convergence time, and robustness to disturbances.

6) Compare localization performance across sensor modalities (LiDAR only, RGB‑D only, multimodal).

Deliverables: Standalone localization benchmark pipeline, quantitative comparison across localization methods, robustness evaluation report, recommended localization strategy.

## Project Structure

The repository is organized to clearly separate the Docker infrastructure from the ROS 2 application code:

.
├── docker/
│   ├── Dockerfile
│   └── Dockerfile.base                    # Dockerfiles (Base and Project)
├── docs/                                  # Documentation (Doxygen)
│   ├── output/                         
│   └── Doxyfile 
├── results/                               # Generated benchmark data (CSVs)
│   ├── amcl/
│   ├── amcl_actors/
│   ├── amcl_extr/
│   ├── amcl_kidnapping/
│   └── amcl_noise/
├── scripts/                               # Management and Launch scripts
│   ├── docker.sh                          # Host-side script for Docker container management
│   └── launch.sh                          # Container-side script for ROS2 operations
├── src/                                   # ROS 2 Workspace source code
│   ├── gazebo_g1/                         # Gazebo simulation and robot configuration
│   ├── g1_description/                    # Robot URDF, meshes
│   ├── aws-robomaker-small-house-world/   # Small house indoor environment assets
│   └── g1_loc_benchmark/                  # Core launch files and Python evaluation scripts
├── docker-compose.yml                     # Docker Compose configuration
└── README.md


## How the Benchmark Works

This project is designed to evaluate how accurately the robot can estimate its own position in a mapped environment using different algorithms and sensor modalities.

The core of the evaluation is the benchmark_evaluator.py node. While the robot navigates, this node simultaneously subscribes to two topics:

Ground Truth (`/ground_truth_pose`): The absolute, mathematically perfect position of the robot provided directly by the Gazebo physics engine.

Estimated Pose (`/amcl_pose` or RTAB-Map equivalent): The position calculated by the localization algorithm using noisy sensor data (LiDAR, Cameras).

At a fixed frequency, the evaluator computes the Translational Error (Euclidean distance in meters) and the Rotational Error (Yaw difference in degrees) between the Ground Truth and the Estimate. All data is stamped with the elapsed time and saved in a .csv file inside the `results/` directory for post-analysis.

## Implemented Scenarios

To thoroughly test the robustness of the localization algorithms, we have implemented several distinct test scenarios:

1. Standard Navigation (`amcl`)

   The baseline scenario. The robot navigates in a static, clean environment without external disturbances. This tests the nominal accuracy of the AMCL (2D LiDAR) and RTAB-Map (3D Multimodal) algorithms.

2. Dynamic Obstacles (`amcl_actors`):
   
   Real-world environments are rarely static. By executing dynamic_obstacles.py, we spawn 6 moving cylinders (representing humans) that walk back and forth across the rooms.
   Impact: The LiDAR beams get continuously occluded. The localization algorithm must distinguish between the static map walls and the moving entities to prevent the pose estimation from drifting.

3. Sensor Noise (`amcl_noise & amcl_extr`)

   Simulates degraded hardware. Gaussian noise is artificially injected into the LiDAR scans and Odometry via Gazebo plugins to simulate cheap sensors, wheel slippage, or uneven terrain.

4. The "Kidnapping" Problem (`amcl_kidnapping`)

   Tests the algorithm's global localization and recovery capabilities. While the robot is navigating smoothly, it is abruptly teleported to a completely different room in Gazebo without updating its odometry.

Goal: The algorithm must realize that its current sensor readings no longer match the map, expand its particle cloud (in AMCL), and successfully re-localize in the new area.

## Build and Run the Container

You can launch the script `./scripts/docker.sh`, which provides an interactive menu with all the commands to build, run, and enter the container.

To open additional terminals, simply run `./scripts/docker.sh` again and select the option to wake up and attach to the already running container (Option 2).

## ROS 2 Commands & Simulation Setup

Once inside the container, you can use the ./scripts/launch.sh script to easily manage all the ROS 2 nodes.

PROJECT MENU:
--------------------------------
1. Compile, launch Gazebo environment and spawn robot G1 (3D Mapping/SLAM)
2. Run AMCL Localization Benchmark
3. Run Localization Benchmark (Multimodal / LiDAR / RGB-D)
4. Create results dashboard
--------------------------------


- **Option 1**: Starts the initial Mapping phase using RTAB-Map to create the map of the environment.

- **Option 2**: Launches the benchmark_amcl.launch.py file, which runs standard Nav2 with 2D AMCL localization. It prompts you to choose the specific scenario (Dynamic Obstacles, Noise, etc.).

- **Option 3**: Launches the benchmark_localization.launch.py file to test RTAB-Map SLAM in pure localization mode, allowing you to compare Visual (RGB-D), LiDAR-only, or Multimodal approaches.

### RViz Configuration for Navigation with AMCL

Once the simulation and RViz are running, follow these steps to initialize the robot's navigation:

1. **Set the Initial Pose**: * Ensure the Fixed Frame (Global Options) is set to map.

   - Click on the 2D Pose Estimate button in the top toolbar.
   - Click and drag on the grid to set the exact starting position and orientation of the robot.

2. **Visualize the Map**:

   - Click the Add button in the bottom-left corner.
   - Switch to the By topic tab.
   - Scroll down, expand the /map topic, and select map.
   - In the left panel, under the newly added Map display settings, change the Durability Policy to Transient Local. The environment map should now become visible.

3. **Send a Navigation Goal**:

   - Click on the 2D Goal Pose button in the top toolbar.
   - Click and drag on the map to define the destination and final orientation. The robot will start planning and moving towards it.

### RViz Configuration for Navigation with ICP, RGB‑D, multimodal

Once the simulation and RViz are running, follow these steps to initialize the robot's navigation:

1. **Visualize the Map**:

   - Click the Add button in the bottom-left corner.
   - Switch to the By topic tab.
   - Scroll down, expand the /map topic, and select map.
   - In the left panel, under the newly added Map display settings, change the Durability Policy to Transient Local. The environment map should now become visible.

2. **Set the Initial Pose**: * Ensure the Fixed Frame (Global Options) is set to map.

   - Click on the 2D Pose Estimate button in the top toolbar.
   - Click and drag on the grid to set the exact starting position and orientation of the robot.

The initialization is reversed compared to AMCL because, upon switching the frame to 'map', the robot does not spawn at the origin (0,0). I determined the correct initial position using Gazebo as a reference.

## Data Analysis & Dashboard

Once you have completed a few benchmark runs, the metrics will be saved in the `results/` folder. We have developed a custom web-based dashboard using Plotly Dash to visualize this data.

To launch the dashboard, run Option 4 from the launch.sh menu (or execute `python3 src/g1_loc_benchmark/results/dashboard.py`).

Open a web browser and navigate to http://localhost:8050. The dashboard provides:

- **Grouped Bar Charts**: A quick overview of the average translational and rotational errors across all scenarios.

- **Interactive Map Trajectory**: A 2D plot comparing the Ground Truth path (blue) against the Estimated path (orange). Spikes in error (e.g., during Kidnapping) are highlighted with red vectors.

- **Error over Time**: A dual-axis line chart detailing the exact moment the localization drifted or recovered during the run.