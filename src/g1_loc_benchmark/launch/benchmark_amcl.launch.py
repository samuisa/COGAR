## @file benchmark_amcl.launch.py
#  @brief Launch file to start the navigation benchmark with AMCL.
#  @details This script launches Gazebo, Nav2, dynamic obstacles, and the results evaluator.

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """!
    @brief Generates the launch description for the AMCL benchmark.
    
    @details Configures and launches the nodes required to simulate the G1 robot in Gazebo,
             start the Nav2 stack with AMCL, insert any dynamic obstacles, 
             and record error metrics via the evaluator node.
             
    @return A LaunchDescription object containing all configured processes and nodes.
    """
    pkg_gazebo_g1 = get_package_share_directory('gazebo_g1')
    pkg_benchmark = get_package_share_directory('g1_loc_benchmark')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    aws_house_dir = get_package_share_directory('aws_robomaker_small_house_world')

    map_yaml = os.path.join(aws_house_dir, 'maps', 'turtlebot3_waffle_pi', 'map.yaml')
    
    gui_script_path = os.path.join(pkg_benchmark, 'scripts', 'g1_controller.py')
    odom_tf_path = os.path.join(pkg_benchmark, 'scripts', 'odom_tf_broadcaster.py')
    evaluator_path = os.path.join(pkg_benchmark, 'scripts', 'benchmark_evaluator.py')
    obstacles_path = os.path.join(pkg_benchmark, 'scripts', 'dynamic_obstacles.py')

    # Dynamic arguments
    use_actors = DeclareLaunchArgument('use_actors', default_value='false')
    # By default uses the perfect robot
    model_arg = DeclareLaunchArgument('model', default_value='g1_29dof_2d.urdf')
    # By default uses base Nav2 parameters
    params_file_arg = DeclareLaunchArgument('params_file', default_value='/opt/ros/humble/share/nav2_bringup/params/nav2_params.yaml')
    # Folder name for results
    scenario_name = DeclareLaunchArgument('scenario', default_value='amcl')

    return LaunchDescription([
        use_actors,
        model_arg,
        params_file_arg,
        scenario_name,

        # 1. SIMULATION (Pass the URDF model)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_g1, 'launch', 'spawn_g1_2d.launch.py')),
            launch_arguments={'model': LaunchConfiguration('model')}.items()
        ),

        # 2. NAV2 (Pass dynamic parameters)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': map_yaml,
                'use_sim_time': 'true',
                'autostart': 'true',
                'params_file': LaunchConfiguration('params_file')
            }.items()
        ),

        # 3. ACTORS
        ExecuteProcess(
            cmd=['python3', obstacles_path],
            output='screen',
            condition=IfCondition(LaunchConfiguration('use_actors'))
        ),

        # 4. SUPPORT AND ODOMETRY
        ExecuteProcess(cmd=['python3', gui_script_path], output='screen'),
        ExecuteProcess(cmd=['python3', odom_tf_path], output='screen'),

        # 5. EVALUATOR (Pass the scenario name directly!)
        ExecuteProcess(
            cmd=['python3', evaluator_path, '--scenario', LaunchConfiguration('scenario')],
            output='screen'
        )
    ])