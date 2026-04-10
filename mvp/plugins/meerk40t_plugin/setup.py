from setuptools import setup, find_packages

setup(
    name="lasercam-meerk40t-plugins",
    version="0.1.0",
    description="LaserCam Laser and Camera Emulator plugins for MeerK40t",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.11.0.86",
        "numpy>=1.26.4",
    ],
    entry_points={
        "meerk40t.extension": [
            "laser_emulator = mvp.plugins.meerk40t_plugin.laser_emulator_plugin:plugin",
            "camera_emulator = mvp.plugins.meerk40t_plugin.camera_emulator_plugin:plugin",
        ],
    },
    python_requires=">=3.8",
)
