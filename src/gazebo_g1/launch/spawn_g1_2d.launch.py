import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_gazebo_g1 = get_package_share_directory('gazebo_g1')
    pkg_g1_description = get_package_share_directory('g1_description')
    pkg_aws_house = get_package_share_directory('aws_robomaker_small_house_world')

    bme_models_path, _ = os.path.split(pkg_gazebo_g1)
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
        DeclareLaunchArgument('model', default_value='g1_29dof_2d.urdf'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        # Avvio Ignition Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_g1, 'launch', 'world.launch.py')),
            launch_arguments={'world': LaunchConfiguration('world')}.items()
        ),

        # Robot State Publisher (FIXATO per ROS 2 Humble)
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': ParameterValue(Command(['xacro', ' ', urdf_file_path]), value_type=str), 
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }]
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
                "-z", "0.2", # Alzato per la nuova collisione sferica
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
                "/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist",
                "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry",
                "/model/g1_robot/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan",
                "/camera/image@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/camera/depth_image@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
                "/camera/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked",
                "/ground_truth_pose@nav_msgs/msg/Odometry[ignition.msgs.Odometry" 
            ],
            remappings=[
                ("/model/g1_robot/tf", "/tf"),
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
            arguments=['-d', PathJoinSubstitution([pkg_gazebo_g1, 'rviz', LaunchConfiguration('rviz_config')])],
            condition=IfCondition(LaunchConfiguration('rviz')),
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
        ),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint'],
            output='screen'
        ),
    ])