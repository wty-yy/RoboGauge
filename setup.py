from setuptools import setup, find_packages

setup(
    name="robogauge",
    version="1.1.6",
    author="Wu Tianyang",
    author_email="993660140@qq.com",
    description="A generic robot RL model evaluation library based on MuJoCo",
    url="https://github.com/wty-yy/robot_gauge",
    packages=find_packages(),
    install_requires=[
        "torch",  # Refer: https://pytorch.org/get-started/locally/
        "numpy==1.20.0",
        "pillow==9.0.0",
        "mujoco==3.2.3",
        "dm_control==1.0.23",
        "scipy",
        "matplotlib==3.6.3",
        "tqdm",
        "imageio[ffmpeg]",
        "tensorboard",
        "PyYAML",
        "fastapi",
        "uvicorn",
        "pygame",
    ],
    python_requires=">=3.8",
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Robotics",
    ],
)
