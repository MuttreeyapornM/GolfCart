from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_file = LaunchConfiguration('config_file')
    start_joy_node = LaunchConfiguration('start_joy_node')

    default_config = PathJoinSubstitution([
        FindPackageShare('golfcart_low_level'),
        'config',
        'golfcart_low_level.yaml',
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            'config_file',
            default_value=default_config,
            description='YAML file with golfcart_low_level node parameters.',
        ),
        DeclareLaunchArgument(
            'start_joy_node',
            default_value='false',
            description='Start the ROS 2 joy driver node in addition to joy_cmd_vel.',
        ),
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen',
            condition=IfCondition(start_joy_node),
        ),
        Node(
            package='golfcart_low_level',
            executable='ros_can_bridge',
            name='ros_can_bridge',
            output='screen',
            parameters=[config_file],
        ),
        Node(
            package='golfcart_low_level',
            executable='steering_node',
            name='steering_node',
            output='screen',
            parameters=[config_file],
        ),
        Node(
            package='golfcart_low_level',
            executable='joy_cmd_vel',
            name='joy_cmd_vel',
            output='screen',
            parameters=[config_file],
        ),
    ])
