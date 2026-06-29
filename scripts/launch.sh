#!/usr/bin/env bash

echo ""
echo "PROJECT MENU:"
echo "--------------------------------"
echo "1. Compile, launch Gazebo environment and spawn robot G1 (3D Mapping/SLAM)"
echo "2. Run AMCL Localization Benchmark"
echo "3. Run Localization Benchmark (Multimodal / LiDAR / RGB-D)"
echo "4. Create results dashboard"
echo "--------------------------------"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Cleaning up workspace..."

        cd /workspace
        
        pkill -9 ruby; pkill -9 ign; pkill -9 gzserver; 
        pkill -9 gzclient; pkill -9 rtabmap; pkill -9 rviz2

        rm -rf build/ install/ log/

        echo "Building workspace and launching Gazebo..."

        cd /workspace

        source /opt/ros/humble/setup.bash
        colcon build
        source install/local_setup.bash

        mkdir -p src/g1_loc_benchmark/log

        echo "Avvio Gazebo e RViz..."
        ros2 launch g1_loc_benchmark mapping.launch.py > src/g1_loc_benchmark/log/launch_output.log 2>&1

        ;;

    2)
        echo "--------------------------------"
        echo "1. Benchmark Navigazione Standard"
        echo "2. Benchmark Navigazione con Attori (Ostacoli)"
        echo "3. Benchmark Rumore Sensori"
        echo "4. Benchmark Kidnapping (Recovery)"
        echo "--------------------------------"
        read -p "Scegli modalità (1-4): " nav_choice

        echo "Cleaning up workspace..."

        cd /workspace
        
        pkill -9 ruby; pkill -9 ign; pkill -9 gzserver; 
        pkill -9 gzclient; pkill -9 rtabmap; pkill -9 rviz2

        rm -rf build/ install/ log/

        cd /workspace

        source /opt/ros/humble/setup.bash
        colcon build
        source install/local_setup.bash

        mkdir -p src/g1_loc_benchmark/log

        if [ "$nav_choice" == "1" ]; then
            echo "Avvio Benchmark Standard..."
            ros2 launch g1_loc_benchmark benchmark_amcl.launch.py scenario:=amcl

        elif [ "$nav_choice" == "2" ]; then
            echo "Avvio Benchmark con Ostacoli Dinamici..."
            ros2 launch g1_loc_benchmark benchmark_amcl.launch.py use_actors:=true scenario:=amcl_actors

        elif [ "$nav_choice" == "3" ]; then
            echo "Avvio Benchmark con Rumore Sensori..."
            ros2 launch g1_loc_benchmark benchmark_amcl.launch.py \
                model:=g1_29dof_2d_noisy.urdf \
                params_file:=/workspace/src/gazebo_g1/config/nav2_noise_params.yaml \
                scenario:=amcl_noise

        elif [ "$nav_choice" == "4" ]; then
            echo "Avvio Benchmark Kidnapping..."
            ros2 launch g1_loc_benchmark benchmark_amcl.launch.py \
                params_file:=/workspace/src/gazebo_g1/config/nav2_noise_params.yaml \
                scenario:=amcl_kidnapping
        else
            echo "Scelta non valida!"
            exit 1
        fi
        ;;

    3)
        echo "--------------------------------"
        echo "Choose 3D Localization Modality:"
        echo "1. Multimodal (LiDAR 3D + RGB-D)"
        echo "2. LiDAR Only (ICP Puro)"
        echo "3. RGB-D Only (Visual Only)"
        echo "--------------------------------"

        read -p "Enter your choice (1-3): " mod_choice
        
        echo "Cleaning up workspace..."

        cd /workspace
        
        pkill -9 ruby; pkill -9 ign; pkill -9 gzserver; 
        pkill -9 gzclient; pkill -9 rtabmap; pkill -9 rviz2

        rm -rf build/ install/ log/

        echo "Building workspace..."

        cd /workspace

        source /opt/ros/humble/setup.bash
        colcon build
        source install/local_setup.bash

        mkdir -p src/g1_loc_benchmark/log

        case $mod_choice in
            1)
                echo "Avvio Benchmark: MULTIMODALE"
                ros2 launch g1_loc_benchmark benchmark_localization.launch.py modality:=multimodal > src/g1_loc_benchmark/log/multimodal.log 2>&1
                ;;
            2)
                echo "Avvio Benchmark: LiDAR ONLY"
                ros2 launch g1_loc_benchmark benchmark_localization.launch.py modality:=lidar > src/g1_loc_benchmark/log/lidar.log 2>&1
                ;;
            3)
                echo "Avvio Benchmark: RGB-D ONLY"
                ros2 launch g1_loc_benchmark benchmark_localization.launch.py modality:=rgbd > src/g1_loc_benchmark/log/rgbd.log 2>&1
                ;;
            *)
                echo "Invalid option."
                exit 1
                ;;
        esac

        echo "Chiudendo il ponte TF..."
        kill $TF_PID
        ;;

    4)
        
        echo "Running 2D Dashboard..."
        cd /workspace
        python3 src/g1_loc_benchmark/scripts/dashboard.py 
        ;;
        
    *)
        echo "Invalid option."
        read -p "Press Enter to exit..."
        exit 1
        ;;
esac