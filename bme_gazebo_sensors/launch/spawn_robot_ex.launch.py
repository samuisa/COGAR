import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_bme_gazebo_sensors = get_package_share_directory('bme_gazebo_sensors')
    pkg_g1_description = get_package_share_directory('g1_description')

    bme_models_path, _ = os.path.split(pkg_bme_gazebo_sensors)
    g1_models_path, _ = os.path.split(pkg_g1_description)
    os.environ["GZ_SIM_RESOURCE_PATH"] = os.pathsep.join([os.environ.get("GZ_SIM_RESOURCE_PATH", ""), bme_models_path, g1_models_path])

    urdf_file_path = PathJoinSubstitution([pkg_g1_description, "urdf", LaunchConfiguration('model')])

    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('rviz_config', default_value='rviz.rviz'),
        DeclareLaunchArgument('world', default_value='world_empty.sdf'),
        DeclareLaunchArgument('model', default_value='g1_29dof.urdf'),
        DeclareLaunchArgument('x', default_value='2.5'),
        DeclareLaunchArgument('y', default_value='1.5'),
        DeclareLaunchArgument('yaw', default_value='-1.5707'),
        DeclareLaunchArgument('use_sim_time', default_value='True'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_bme_gazebo_sensors, 'launch', 'world.launch.py')),
            launch_arguments={'world': LaunchConfiguration('world')}.items()
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': Command(['xacro', ' ', urdf_file_path]), 'use_sim_time': True}]
        ),

        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=["-name", "g1_robot", "-topic", "robot_description", "-x", "2.5", "-y", "1.5", "-z", "0.8"]
        ),

        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
                "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
                "/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
                "/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan"
            ]
        ),

        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"]
        ),

        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["position_controller", "--controller-manager", "/controller_manager"]
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([pkg_bme_gazebo_sensors, 'rviz', LaunchConfiguration('rviz_config')])],
            condition=IfCondition(LaunchConfiguration('rviz'))
        )
    ])
