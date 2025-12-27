from setuptools import setup, find_packages

setup(
    name="robogauge",  # 包名
    version="0.1.0",   # 版本号
    author="wty-yy", # 你的名字
    author_email="993660140@qq.com",
    description="A generic robot RL model evaluation library based on MuJoCo",
    url="https://github.com/wty-yy/robot_gauge", # 如果有仓库地址
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "mujoco>=3.0.0",
        "dm_control>=1.0.14",
        "scipy",
        "matplotlib==3.6.3",
        "tqdm",
        "imageio[ffmpeg]",
        "tensorboard",
        "PyYAML",
    ],
    python_requires=">=3.8",
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Robotics",
    ],
)
