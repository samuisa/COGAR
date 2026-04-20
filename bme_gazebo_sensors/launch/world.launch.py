import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import  LaunchConfiguration, TextSubstitution

def generate_launch_description():
    pkg_bme_gazebo_sensors = get_package_share_directory('bme_gazebo_sensors')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Impostiamo il path completo di default per my.sdf
    default_world_path = os.path.join(pkg_bme_gazebo_sensors, 'worlds', 'my.sdf')

    world_arg = DeclareLaunchArgument(
        'world', default_value=default_world_path,
        description='Full path of the Gazebo world file to load'
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'),
        ),
        # Ora passiamo direttamente il percorso completo senza fare PathJoinSubstitution!
        launch_arguments={'gz_args': [
            LaunchConfiguration('world'),
            TextSubstitution(text=' -r -v -v1')
        ],
        'on_exit_shutdown': 'true'}.items()
    )

    launchDescriptionObject = LaunchDescription()

    launchDescriptionObject.add_action(world_arg)
    launchDescriptionObject.add_action(gazebo_launch)

    return launchDescriptionObject