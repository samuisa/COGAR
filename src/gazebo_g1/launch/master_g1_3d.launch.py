import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_gazebo_g1 = get_package_share_directory('gazebo_g1')
    
    # Percorso esatto del tuo script Python
    gui_script_path = os.path.join(pkg_gazebo_g1, 'scripts', 'g1_controller.py')

    return LaunchDescription([
        # 1. AVVIA LA SIMULAZIONE GAZEBO E IL ROBOT 3D
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_g1, 'launch', 'spawn_g1_3d.launch.py'))
        ),

        # 2. CONVERTITORE LASER 3D -> 2D (Lo teniamo per compatibilità con Nav2 in futuro)
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

        # 3. 🟢 RTAB-MAP IN MODALITÀ SLAM (MAPPATURA MULTIMODALE RGB-D + LiDAR 3D)
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output='screen',
            parameters=[{
                'frame_id': 'base_footprint', # Il nodo radice del robot
                'use_sim_time': True,
                
                # Iscrizione ai sensori
                'subscribe_depth': True,
                'subscribe_rgb': True,
                'subscribe_scan_cloud': True, # Abilita il LiDAR 3D
                
                # Sincronizzazione per Gazebo (I topic non arrivano allo stesso millisecondo)
                'approx_sync': True,          
                
                # Parametri Core di RTAB-Map
                'Reg/Strategy': '2',          # 2 = Usa feature Visive + ICP geometrico (LiDAR)
                'RGBD/NeighborLinkRefining': 'True', # Affina le chiusure di anello
                
                # Generazione automatica della mappa 2D (occupancy grid) per Nav2
                'Grid/FromDepth': 'false',    # Usa il LiDAR per la griglia 2D, non la camera
                'Grid/RangeMax': '10.0',      # Raggio massimo per tracciare i muri

                'wait_for_transform': 0.5,             # Dà a TF mezzo secondo di margine all'avvio prima di dare errore
                'Mem/DepthCompressionFormat': '.png',
            }],
            remappings=[
                ('rgb/image', '/camera/color/image_raw'),
                ('depth/image', '/camera/depth/image_raw'),
                ('rgb/camera_info', '/camera/color/camera_info'),
                ('scan_cloud', '/lidar/points'),
                ('odom', '/odom')
            ],
            # 🔴 ARGOMENTO CRITICO: '--delete_db_on_start' cancella la vecchia mappa e ne inizia una nuova. 
            # Rimuovilo quando vorrai fare SOLO localizzazione in futuro.
            arguments=['--delete_db_on_start'] 
        ),

        # 4. AVVIA LA TUA INTERFACCIA E L'ANIMATORE
        ExecuteProcess(
            cmd=['python3', gui_script_path],
            output='screen'
        ),

        ExecuteProcess(
            cmd=['python3', os.path.join(pkg_gazebo_g1, 'scripts', 'odom_tf_broadcaster.py')],
            output='screen'
        )
    ])