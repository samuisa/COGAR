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
    
    pkg_aws_house = get_package_share_directory('aws_robomaker_small_house_world')

    bme_models_path, _ = os.path.split(pkg_bme_gazebo_sensors)
    g1_models_path, _ = os.path.split(pkg_g1_description)
    aws_models_path, _ = os.path.split(pkg_aws_house)

    # Diciamo a Gazebo dove trovare i mobili della casa
    os.environ["GZ_SIM_RESOURCE_PATH"] = os.pathsep.join([
        os.environ.get("GZ_SIM_RESOURCE_PATH", ""), 
        bme_models_path, 
        g1_models_path,
        aws_models_path,
        os.path.join(pkg_aws_house, 'models')
    ])

    urdf_file_path = PathJoinSubstitution([pkg_g1_description, "urdf", LaunchConfiguration('model')])

    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('rviz_config', default_value='rviz.rviz'),
        
        # ---> ECCO LA MODIFICA: Ora cerca il file .sdf! <---
        DeclareLaunchArgument('world', default_value='small_house.sdf'),
        
        DeclareLaunchArgument('model', default_value='g1_29dof.urdf'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
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
            arguments=[
                "-name", "g1_robot", 
                "-topic", "robot_description", 
                "-x", LaunchConfiguration('x'), 
                "-y", LaunchConfiguration('y'), 
                "-z", "0.8",
                "-Y", LaunchConfiguration('yaw')
            ]
        ),

        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock",
                "/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist",
                "/odom@nav_msgs/msg/Odometry@ignition.msgs.Odometry",
                "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/tf_static@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                
                # LiDAR
                "/lidar/points/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked",
                
                # CAMERA
                "/camera/image@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/camera/depth_image@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
                "/camera/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked"
            ],
            remappings=[
                # Correzione Lidar: da /lidar/points/points a /lidar/points
                ("/lidar/points/points", "/lidar/points"),
                
                # Nomi standard per la Camera (stile Realsense)
                ("/camera/image",       "/camera/color/image_raw"),
                ("/camera/depth_image", "/camera/depth/image_raw"),
                ("/camera/camera_info", "/camera/color/camera_info"),
                ("/camera/points",      "/camera/depth/color/points"),
            ],
            output='screen'
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