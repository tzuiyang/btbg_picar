from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'btbg_nodes'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='BTBG Developer',
    maintainer_email='your@email.com',
    description='BTBG Robot Car ROS2 Nodes',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'hardware_bridge_node = btbg_nodes.hardware_bridge_node:main',
            'sensor_node = btbg_nodes.sensor_node:main',
            'car_control_node = btbg_nodes.car_control_node:main',
            'patrol_node = btbg_nodes.patrol_node:main',
        ],
    },
)
