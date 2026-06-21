#!/usr/bin/env bash

echo ""
echo "PROJECT MENU:"
echo "--------------------------------"
echo "1. Compile, launch Gazebo environment and spawn robot G1 (3D Mapping/SLAM)"
echo "2. Compile, launch Gazebo environment and spawn robot G1 (2D Mapping/SLAM)"
echo "3. Run 3D Localization Benchmark (Multimodal / LiDAR / RGB-D)"
echo "4. Run Benchmark evaluator "
echo "5. Create results dashboard"
echo "--------------------------------"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "Building workspace and launching Gazebo..."
        cd /workspace

        source /opt/ros/humble/setup.bash
        colcon build
        source install/local_setup.bash

        echo "Avvio il ponte TF in background..."
        python3 src/gazebo_g1/scripts/odom_tf_broadcaster.py &
        
        TF_PID=$!

        echo "Avvio Gazebo e RViz..."
        ros2 launch gazebo_g1 master_g1_3d.launch.py

        echo "Chiudendo il ponte TF..."
        kill $TF_PID
        ;;

    2)
        echo "Running master script"

        cd /workspace

        source /opt/ros/humble/setup.bash
        colcon build
        source install/local_setup.bash

        ros2 launch gazebo_g1 benchmark_amcl.launch.py 
        ;;

    3)
        echo "--------------------------------"
        echo "Choose 3D Localization Modality:"
        echo "1. Multimodal (LiDAR 3D + RGB-D)"
        echo "2. LiDAR Only (ICP Puro)"
        echo "3. RGB-D Only (Visual Only)"
        echo "--------------------------------"

        read -p "Enter your choice (1-3): " mod_choice
        
        echo "Building workspace..."
        cd /workspace
        source /opt/ros/humble/setup.bash
        colcon build
        source install/local_setup.bash

        echo "Avvio il ponte TF in background..."
        python3 src/gazebo_g1/scripts/odom_tf_broadcaster.py &
        TF_PID=$!

        case $mod_choice in
            1)
                echo "Avvio Benchmark: MULTIMODALE"
                ros2 launch gazebo_g1 benchmark_localization.launch.py modality:=multimodal
                ;;
            2)
                echo "Avvio Benchmark: LiDAR ONLY"
                ros2 launch gazebo_g1 benchmark_localization.launch.py modality:=lidar
                ;;
            3)
                echo "Avvio Benchmark: RGB-D ONLY"
                ros2 launch gazebo_g1 benchmark_localization.launch.py modality:=rgbd
                ;;
            *)
                echo "Invalid option."
                kill $TF_PID
                exit 1
                ;;
        esac

        echo "Chiudendo il ponte TF..."
        kill $TF_PID
        ;;

    4)
        echo "--------------------------------"
        echo "Choose between 2D or 3D simulation"
        echo "1. 2D Benchmark Evaluator"
        echo "2. 3D Benchmark Evaluator"
        echo "--------------------------------"

        read -p "Enter your choice (1-2): " eval_choice

        case $eval_choice in
            1)
                echo "Running 2D Evaluator..."
                cd /workspace
                python3 src/gazebo_g1/scripts/benchmark_evaluator_2D.py 
                ;;
            2)
                echo "Running 3D Evaluator..."
                cd /workspace
                python3 src/gazebo_g1/scripts/benchmark_evaluator_3D.py 
                ;;
            *)
                echo "Invalid option."
                read -p "Press Enter to exit..."
                exit 1
                ;;
        esac
        ;;

    5)
        echo "--------------------------------"
        echo "Choose between 2D or 3D Dashboard"
        echo "1. 2D Dashboard"
        echo "2. 3D Dashboard"
        echo "--------------------------------"

        read -p "Enter your choice (1-2): " dash_choice

        case $dash_choice in
            1)
                echo "Running 2D Dashboard..."
                cd /workspace
                python3 src/gazebo_g1/scripts/dashboard_app_2D.py 
                ;;
            2)
                echo "Running 3D Dashboard..."
                cd /workspace
                python3 src/gazebo_g1/scripts/dashboard_app_3D.py 
                ;;
            *)
                echo "Invalid option."
                read -p "Press Enter to exit..."
                exit 1
                ;;
        esac
        ;;

    *)
        echo "Invalid option."
        read -p "Press Enter to exit..."
        exit 1
        ;;
esac