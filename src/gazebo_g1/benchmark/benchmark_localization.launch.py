import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import LaunchConfigurationEquals
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_gazebo_g1 = get_package_share_directory('gazebo_g1')
    gui_script_path = os.path.join(pkg_gazebo_g1, 'scripts', 'g1_controller.py')

    # 🟢 ARGOMENTO CHIAVE: Scegli la modalità dal terminale!
    # Valori accettati: 'multimodal', 'lidar', 'rgbd'
    modality_arg = DeclareLaunchArgument(
        'modality', 
        default_value='multimodal',
        description='Scegli la modalità di localizzazione: multimodal, lidar, o rgbd'
    )

    # Remapping comuni per RTAB-Map
    rtabmap_remappings = [
        ('rgb/image', '/camera/color/image_raw'),
        ('depth/image', '/camera/depth/image_raw'),
        ('rgb/camera_info', '/camera/color/camera_info'),
        ('scan_cloud', '/lidar/points'),
        ('odom', '/odom')
    ]

    return LaunchDescription([
        modality_arg,

        # 1. AVVIA GAZEBO E IL ROBOT
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_g1, 'launch', 'spawn_g1_3d.launch.py'))
        ),

        # 2. CONVERTITORE LASER (Per Nav2/Ostacoli)
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pc_to_scan',
            remappings=[('cloud_in', '/lidar/points'), ('scan', '/scan')],
            parameters=[{'target_frame': 'mid360_link', 'use_sim_time': True, 'range_max': 30.0}]
        ),

        # =================================================================================
        # 3A. NODO RTAB-MAP: CONFIGURAZIONE MULTIMODALE (LiDAR 3D + RGB-D)
        # =================================================================================
        Node(
            condition=LaunchConfigurationEquals('modality', 'multimodal'),
            package='rtabmap_slam', executable='rtabmap', name='rtabmap', output='screen',
            parameters=[{
                'frame_id': 'base_footprint', 'use_sim_time': True, 'approx_sync': True,
                'Mem/IncrementalMemory': 'false',   # 🔴 LOCALIZZAZIONE PURA (Mappa bloccata)
                'Mem/InitWMWithAllNodes': 'true',   # Carica tutto il database in memoria
                'subscribe_depth': True, 'subscribe_rgb': True, 'subscribe_scan_cloud': True,
                'Reg/Strategy': '2',                # Usa sia feature Visive che ICP geometrico
                'RGBD/NeighborLinkRefining': 'True', 
                'Grid/RangeMax': '10.0', 'Grid/RangeMin': '0.4', 'wait_for_transform': 0.5
            }],
            remappings=rtabmap_remappings
        ),

        # =================================================================================
        # 3B. NODO RTAB-MAP: CONFIGURAZIONE LiDAR ONLY (ICP PURO)
        # =================================================================================
        Node(
            condition=LaunchConfigurationEquals('modality', 'lidar'),
            package='rtabmap_slam', executable='rtabmap', name='rtabmap', output='screen',
            parameters=[{
                'frame_id': 'base_footprint', 'use_sim_time': True, 'approx_sync': True,
                'Mem/IncrementalMemory': 'false',   # 🔴 LOCALIZZAZIONE PURA
                'Mem/InitWMWithAllNodes': 'true',
                'subscribe_depth': False, 'subscribe_rgb': False, 'subscribe_scan_cloud': True, # Camere SPENTE!
                'Reg/Strategy': '1',                # 1 = Solo ICP (Nessuna feature visiva usata)
                'Icp/PointToPlane': 'true',         # Fondamentale per l'ICP 3D
                'Grid/RangeMax': '10.0', 'Grid/RangeMin': '0.4', 'wait_for_transform': 0.5
            }],
            remappings=rtabmap_remappings
        ),

        # =================================================================================
        # 3C. NODO RTAB-MAP: CONFIGURAZIONE RGB-D ONLY (VISUAL ONLY)
        # =================================================================================
        Node(
            condition=LaunchConfigurationEquals('modality', 'rgbd'),
            package='rtabmap_slam', executable='rtabmap', name='rtabmap', output='screen',
            parameters=[{
                'frame_id': 'base_footprint', 'use_sim_time': True, 'approx_sync': True,
                'Mem/IncrementalMemory': 'false',   # 🔴 LOCALIZZAZIONE PURA
                'Mem/InitWMWithAllNodes': 'true',
                'subscribe_depth': True, 'subscribe_rgb': True, 'subscribe_scan_cloud': False, # LiDAR SPENTO!
                'Reg/Strategy': '0',                # 0 = Solo feature Visive
                'Grid/RangeMax': '10.0', 'Grid/RangeMin': '0.4', 'wait_for_transform': 0.5,
                'Mem/DepthCompressionFormat': '.png'
            }],
            remappings=rtabmap_remappings
        ),

        # 4. AVVIA L'INTERFACCIA/CONTROLLER
        ExecuteProcess(cmd=['python3', gui_script_path], output='screen')
    ])