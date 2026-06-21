import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_gazebo_g1 = get_package_share_directory('gazebo_g1')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    aws_house_dir = get_package_share_directory('aws_robomaker_small_house_world')

    # Percorso della mappa esistente nel pacchetto AWS
    map_yaml = os.path.join(aws_house_dir, 'maps', 'turtlebot3_waffle_pi', 'map.yaml')
    
    # Percorso esatto del tuo script Python
    gui_script_path = os.path.join(pkg_gazebo_g1, 'scripts', 'g1_controller.py')

    return LaunchDescription([
        # 1. AVVIA LA SIMULAZIONE GAZEBO E IL ROBOT
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_g1, 'launch', 'spawn_g1_2d.launch.py'))
        ),

        # 2. AVVIA NAV2 COMPLETO
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': map_yaml,
                'use_sim_time': 'true',
                'autostart': 'true'
            }.items()
        ),

        # 3. AVVIA LA TUA INTERFACCIA E L'ANIMATORE
        ExecuteProcess(
            cmd=['python3', gui_script_path],
            output='screen'
        ),

        ExecuteProcess(
            cmd=['python3', os.path.join(pkg_gazebo_g1, 'scripts', 'odom_tf_broadcaster.py')],
            output='screen'
        )
    ])