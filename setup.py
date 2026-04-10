from setuptools import setup, find_packages

setup(
    name="lasercam",
    version="0.1.0",
    description="LaserCam Alignment Assistant",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.11.0.86",
        "numpy>=1.26.4",
        "pillow>=10.4.0",
        "pyserial>=3.5",
        "pywin32>=306; platform_system == 'Windows'",
    ],
    python_requires=">=3.8",
)
