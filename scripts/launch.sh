#!/usr/bin/env bash

echo "Project menu:"
echo "--------------------------------"
echo "1. Compile, launch Gazebo environment and spawn robot G1"
echo "2. Execute walking script"
echo "3. Terminal for input commands (Teleop)"
echo "--------------------------------"

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "Building workspace and launching Gazebo..."
        cd /workspace

        # Configura l'ambiente ROS2 di base
        source /opt/ros/humble/setup.bash
        
        # Compila il workspace (operazione che prima magari faceva l'entrypoint)
        colcon build
        
        # Carica le variabili del workspace appena compilato
        source install/local_setup.bash

        # Lancia la simulazione
        ros2 launch bme_gazebo_sensors spawn_robot_ex.launch.py
        ;;
        
    2)
        echo "Executing walking script..."
        cd /workspace

        # Serve sempre ricaricare l'ambiente in ogni nuovo terminale
        source /opt/ros/humble/setup.bash
        source install/local_setup.bash

        python3 src/g1_description/src/fake_walk_animator.py
        ;;
        
    3)
        echo "Starting teleop for input commands..."
        cd /workspace

        source /opt/ros/humble/setup.bash
        source install/local_setup.bash

        ros2 run teleop_twist_keyboard teleop_twist_keyboard
        ;;
        
    *)
        echo "Invalid option."
        read -p "Press Enter to exit..."
        exit 1
        ;;
esac