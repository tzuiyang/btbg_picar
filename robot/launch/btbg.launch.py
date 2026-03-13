#!/usr/bin/env python3
"""
BTBG Launch File - Starts all ROS2 nodes and rosbridge.

Usage:
    ros2 launch btbg_nodes btbg.launch.py
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package share directory for config files
    pkg_share = get_package_share_directory('btbg_nodes')
    params_file = os.path.join(pkg_share, 'config', 'btbg_params.yaml')

    # Check if params file exists, use defaults if not
    if not os.path.exists(params_file):
        print(f"WARNING: {params_file} not found, using default parameters")
        params_file = None

    nodes = []

    # Hardware Bridge Node (must start first - owns Picarx instance)
    hardware_bridge = Node(
        package='btbg_nodes',
        executable='hardware_bridge_node',
        name='hardware_bridge_node',
        output='screen',
        parameters=[params_file] if params_file else [],
        emulate_tty=True,
    )
    nodes.append(hardware_bridge)

    # Sensor Node
    sensor_node = Node(
        package='btbg_nodes',
        executable='sensor_node',
        name='sensor_node',
        output='screen',
        parameters=[params_file] if params_file else [],
        emulate_tty=True,
    )
    nodes.append(sensor_node)

    # Car Control Node (mode arbiter)
    car_control = Node(
        package='btbg_nodes',
        executable='car_control_node',
        name='car_control_node',
        output='screen',
        parameters=[params_file] if params_file else [],
        emulate_tty=True,
    )
    nodes.append(car_control)

    # Patrol Node (autonomous mode)
    patrol_node = Node(
        package='btbg_nodes',
        executable='patrol_node',
        name='patrol_node',
        output='screen',
        parameters=[params_file] if params_file else [],
        emulate_tty=True,
    )
    nodes.append(patrol_node)

    # rosbridge WebSocket server
    rosbridge = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{'port': 9090}],
        emulate_tty=True,
    )
    nodes.append(rosbridge)

    return LaunchDescription(nodes)
