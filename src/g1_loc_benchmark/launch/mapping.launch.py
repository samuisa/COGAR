## @file mapping.launch.py
#  @brief Launch file to start environment mapping.
#  @details Starts the robot in Gazebo and configures RTAB-Map for 3D and 2D map creation.

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """!
    @brief Generates the launch description for the mapping session.
    
    @details Includes starting the simulator, converting pointcloud to laserscan, 
             and the main RTAB-Map node in SLAM mode. Deletes the previous database 
             on startup.
             
    @return A LaunchDescription object.
    """
    pkg_gazebo_g1 = get_package_share_directory('gazebo_g1')
    
    # Python script paths
    gui_script_path = os.path.join(pkg_gazebo_g1, 'scripts', 'g1_controller.py')
    # explorer_script_path = os.path.join(pkg_gazebo_g1, 'scripts', 'auto_explorer.py') # 🟢 Added path

    return LaunchDescription([
        # 1. START GAZEBO SIMULATION AND 3D ROBOT
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_g1, 'launch', 'spawn_g1_3d.launch.py'))
        ),

        # 2. 3D TO 2D LASER CONVERTER (Kept for future Nav2 compatibility)
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pc_to_scan',
            remappings=[('cloud_in', '/lidar/points'), ('scan', '/scan')],
            parameters=[{
                'target_frame': 'mid360_link',
                'transform_tolerance': 0.01,
                'min_height': 0.1,
                'max_height': 1.5,
                'angle_min': -3.14159,
                'angle_max': 3.14159,
                'angle_increment': 0.0087,
                'scan_time': 0.1,
                'range_min': 0.2,
                'range_max': 30.0,
                'use_inf': True,
                'use_sim_time': True,
                'qos_overrides./scan.publisher.reliability': 'reliable'
            }]
        ),

        # 3. 🟢 RTAB-MAP IN SLAM MODE (MULTIMODAL RGB-D + 3D LiDAR MAPPING)
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output='screen',
            parameters=[{
                'frame_id': 'base_footprint', # The robot's root node
                'use_sim_time': True,
                
                # Sensor subscriptions
                'subscribe_depth': True,
                'subscribe_rgb': True,
                'subscribe_scan_cloud': True, # Enable 3D LiDAR
                
                # Synchronization for Gazebo (Topics do not arrive at the exact same millisecond)
                'approx_sync': True,      

                'Grid/FromDepth': 'false',            # Use LiDAR
                'Grid/MaxGroundHeight': '0.02',      # Everything below 5cm is ground
                'Grid/MinObstacleHeight': '0.02',    # Everything above 5cm is obstacle
                'Grid/MaxObstacleHeight': '1.8',    
                
                # RTAB-Map Core Parameters
                'Reg/Strategy': '2',                 # 2 = Use Visual features + geometric ICP (LiDAR)
                'RGBD/NeighborLinkRefining': 'True', # Refine loop closures
                
                # Automatic generation of 2D map (occupancy grid) for Nav2
                'Grid/FromDepth': 'false',    # Use LiDAR for the 2D grid, not the camera
                'Grid/RangeMax': '10.0',      # Maximum radius to trace walls

                'wait_for_transform': 0.5,             # Gives TF half a second margin on startup before throwing an error
                'Mem/DepthCompressionFormat': '.png',
            }],
            remappings=[
                ('rgb/image', '/camera/color/image_raw'),
                ('depth/image', '/camera/depth/image_raw'),
                ('rgb/camera_info', '/camera/color/camera_info'),
                ('scan_cloud', '/lidar/points'),
                ('odom', '/odom')
            ],

            arguments=['--delete_db_on_start'] 
        ),

        # 4. START INTERFACE/ANIMATOR (⚠️ See note below)
        ExecuteProcess(
            cmd=['python3', gui_script_path],
            output='screen'
        ),

        # 5. START ODOMETRY TF BROADCASTER
        ExecuteProcess(
            cmd=['python3', os.path.join(pkg_gazebo_g1, 'scripts', 'odom_tf_broadcaster.py')],
            output='screen'
        ),
        
        # 6. 🟢 START AUTONOMOUS EXPLORER (Random Walk)
        # ExecuteProcess(
        #     cmd=['python3', explorer_script_path],
        #     output='screen'
        # )
    ])