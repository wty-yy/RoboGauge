from setuptools import find_namespace_packages, setup

setup(
    name="robogauge",
    version="1.1.6",
    author="Wu Tianyang",
    author_email="993660140@qq.com",
    description="A generic robot RL model evaluation library based on MuJoCo",
    url="https://github.com/wty-yy/robot_gauge",
    packages=find_namespace_packages(include=["robogauge*"]),
    install_requires=[
        "requests",
    ],
    python_requires=">=3.8",
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Robotics",
    ],
)
