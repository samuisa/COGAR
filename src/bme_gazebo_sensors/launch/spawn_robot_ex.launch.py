import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_bme_gazebo_sensors = get_package_share_directory('bme_gazebo_sensors')
    pkg_g1_description = get_package_share_directory('g1_description')
    pkg_aws_house = get_package_share_directory('aws_robomaker_small_house_world')

    bme_models_path, _ = os.path.split(pkg_bme_gazebo_sensors)
    g1_models_path, _ = os.path.split(pkg_g1_description)
    aws_models_path, _ = os.path.split(pkg_aws_house)

    # Percorsi per Ignition Gazebo
    os.environ["IGN_GAZEBO_RESOURCE_PATH"] = os.pathsep.join([
        os.environ.get("IGN_GAZEBO_RESOURCE_PATH", ""), 
        bme_models_path, 
        g1_models_path,
        aws_models_path,
        os.path.join(pkg_aws_house, 'models')
    ])

    urdf_file_path = PathJoinSubstitution([pkg_g1_description, "urdf", LaunchConfiguration('model')])

    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('rviz_config', default_value='rviz.rviz'),
        DeclareLaunchArgument('world', default_value=os.path.join(pkg_aws_house, 'worlds', 'small_house.sdf')),
        DeclareLaunchArgument('model', default_value='g1_29dof.urdf'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        # Avvio Ignition Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_bme_gazebo_sensors, 'launch', 'world.launch.py')),
            launch_arguments={'world': LaunchConfiguration('world')}.items()
        ),

        # Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': Command(['xacro', ' ', urdf_file_path]), 'use_sim_time': LaunchConfiguration('use_sim_time')}]
        ),

        # Spawn Robot in Ignition
        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=[
                "-name", "g1_robot", 
                "-topic", "robot_description", 
                "-x", LaunchConfiguration('x'), 
                "-y", LaunchConfiguration('y'), 
                "-z", "0.1",
                "-Y", LaunchConfiguration('yaw')
            ],
            parameters=[{'use_sim_time': True}]
        ),

        # Bridge tra ROS 2 e Ignition
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock",
                "/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist", # FONDAMENTALE: Da ROS a IGN
                "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry",
                "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/tf_static@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/lidar/points/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked",
                "/camera/image@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/camera/depth_image@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
                "/camera/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked"
            ],
            remappings=[
                ("/lidar/points/points", "/lidar/points"),
                ("/camera/image",       "/camera/color/image_raw"),
                ("/camera/depth_image", "/camera/depth/image_raw"),
                ("/camera/camera_info", "/camera/color/camera_info"),
                ("/camera/points",      "/camera/depth/color/points"),
            ],
            output='screen'
        ),

        # Spawner Controller - Ritardati di 5 secondi per dare tempo a Ignition di caricare il robot
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"]
                ),
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["position_controller", "--controller-manager", "/controller_manager"]
                )
            ]
        ),

        # RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([pkg_bme_gazebo_sensors, 'rviz', LaunchConfiguration('rviz_config')])],
            condition=IfCondition(LaunchConfiguration('rviz')),
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
        )
    ])