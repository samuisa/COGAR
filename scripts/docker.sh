#!/usr/bin/env bash

cd "$(dirname "$0")/.."

# Function to show the reminder once inside
print_reminder() {
    echo ""
    echo "========================================================="
    echo " IMPORTANT - Once inside the container:"
    echo " -> Run: ./launch.sh    (to access the ROS2 menu)"
    echo " -> Run: exit           (to exit the container)"
    echo "========================================================="
    echo ""
}

echo "Docker Container Management Menu"
echo "--------------------------------"
echo "1. Build and Run Container"
echo "2. Wakeup and attach to Container"
echo "3. Close Container (Compose Down)"
echo "4. Remove Container and Images (Total cleanup)"
echo "5. Exit"
echo "--------------------------------"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "Starting Build procedure..."
        echo ""
        read -p "INFO: do you want to rebuild the base image (cogar_base)? [Do this the first time or if you modify Dockerfile.base] (y/n): " build_base
        if [[ "$build_base" =~ ^[yY]$ ]]; then
            echo "Building base image..."
            sudo docker build -t cogar_base -f docker/Dockerfile.base .
        fi
        
        echo "Building Compose image..."
        sudo docker compose build

        xhost +local:root
        
        echo "Starting the container in the background..."
        sudo docker compose up -d
        
        print_reminder
        sudo docker exec -it cogar_container bash || read -p "Connection error. Press Enter to exit..."
        
        ;;
        
    2)
        echo "Starting and connecting to the container..."
        
        echo "Setting xhost permissions..."
        xhost +local:root
        
        echo "Starting the container in the background..."
        sudo docker compose up -d
        
        print_reminder
        sudo docker exec -it cogar_container bash || read -p "Connection error. Press Enter to exit..."
        ;;
        
    3)
        echo "Closing the container..."
        sudo docker compose down
        ;;
        
    4)
        echo "Removing the container and cleaning local images..."
        sudo docker compose down --rmi local
        ;;
        
    5)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        echo "Invalid option."
        read -p "Press Enter to exit..."
        exit 1
        ;;
esac