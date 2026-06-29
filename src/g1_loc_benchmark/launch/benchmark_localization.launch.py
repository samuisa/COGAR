## @file benchmark_localization.launch.py
#  @brief Launch file for the RTAB-Map localization test.
#  @details Supports different mapping modalities (multimodal, lidar, rgbd).

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import LaunchConfigurationEquals
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """!
    @brief Generates the launch description for advanced localization (SLAM).
    
    @details Configures RTAB-Map for localization in various modalities (multimodal, lidar, rgbd),
             manages sensor remappings, and starts the navigation nodes with a delay 
             to allow Gazebo and TF to stabilize.
             
    @return A LaunchDescription object.
    """
    pkg_gazebo_g1 = get_package_share_directory('gazebo_g1')
    pkg_benchmark = get_package_share_directory('g1_loc_benchmark')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup') 
    
    gui_script_path = os.path.join(pkg_benchmark, 'scripts', 'g1_controller.py')
    database_path = os.path.join(pkg_gazebo_g1, 'maps', 'small_house.db')

    rtabmap_remappings = [
        ('rgb/image', '/camera/color/image_raw'),
        ('depth/image', '/camera/depth/image_raw'),
        ('rgb/camera_info', '/camera/color/camera_info'),
        ('scan_cloud', '/lidar/points'),
        ('odom', '/odom'),
        ('grid_map', '/map')
    ]

    delayed_navigation_nodes = TimerAction(
        period=12.0, 
        actions=[
            Node(
                package='pointcloud_to_laserscan', executable='pointcloud_to_laserscan_node', name='pc_to_scan',
                remappings=[('cloud_in', '/lidar/points'), ('scan', '/scan')],
                parameters=[{
                    'target_frame': 'base_footprint', 
                    'use_sim_time': True, 
                    'range_min': 0.3,  
                    'range_max': 15.0, 
                    'min_height': 0.02,
                    'max_height': 1.60, 
                    'qos_overrides./scan.publisher.reliability': 'best_effort'
                }]
            ),
            
            Node(
                condition=LaunchConfigurationEquals('modality', 'multimodal'),
                package='rtabmap_slam', executable='rtabmap', name='rtabmap', output='screen',
                parameters=[{
                    'frame_id': 'base_footprint', 'use_sim_time': True, 'approx_sync': True,
                    'database_path': database_path, 'Mem/IncrementalMemory': 'false', 'Mem/InitWMWithAllNodes': 'true',
                    'subscribe_depth': True, 'subscribe_rgb': True, 'subscribe_scan_cloud': True,
                    'Reg/Strategy': '2', 'Grid/RangeMax': '10.0', 'wait_for_transform': 2.0
                }],
                remappings=rtabmap_remappings
            ),

            Node(
                condition=LaunchConfigurationEquals('modality', 'lidar'),
                package='rtabmap_slam', executable='rtabmap', name='rtabmap', output='screen',
                parameters=[{
                    'frame_id': 'base_footprint', 'use_sim_time': True, 'approx_sync': True,
                    'database_path': database_path, 'Mem/IncrementalMemory': 'false', 'Mem/InitWMWithAllNodes': 'true',
                    'subscribe_depth': False, 'subscribe_rgb': False, 'subscribe_scan_cloud': True,
                    'Reg/Strategy': '1', 'Icp/PointToPlane': 'true',
                    'Grid/RangeMax': '10.0', 'wait_for_transform': 2.0
                }],
                remappings=rtabmap_remappings
            ),

            Node(
                condition=LaunchConfigurationEquals('modality', 'rgbd'),
                package='rtabmap_slam', executable='rtabmap', name='rtabmap', output='screen',
                parameters=[{
                    'frame_id': 'base_footprint', 'use_sim_time': True, 'approx_sync': True,
                    'database_path': database_path, 'Mem/IncrementalMemory': 'false', 'Mem/InitWMWithAllNodes': 'true',
                    'subscribe_depth': True, 'subscribe_rgb': True, 'subscribe_scan_cloud': False,
                    'Reg/Strategy': '0', 'Grid/RangeMax': '10.0', 'wait_for_transform': 2.0
                }],
                remappings=rtabmap_remappings
            ),

            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')),
                launch_arguments={'use_sim_time': 'true', 'autostart': 'true'}.items()
            )
        ]
    )

    return LaunchDescription([
        DeclareLaunchArgument('modality', default_value='multimodal'),

        # A. IMMEDIATE START: Gazebo, Controller Spawner and TF Broadcaster
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_g1, 'launch', 'spawn_g1_3d.launch.py'))),
        
        # INTERFACE AND ANIMATOR (DISABLED BECAUSE THE ROBOT IS NOW A RIGID STATUE)
        # ExecuteProcess(cmd=['python3', gui_script_path], output='screen'),
        
        ExecuteProcess(cmd=['python3', os.path.join(pkg_benchmark, 'scripts', 'odom_tf_broadcaster.py')], output='screen'),

        # B. DELAYED START: Nodes that need the complete TF Tree
        delayed_navigation_nodes
    ])