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
        "mujoco>=3.0.0",       # 必须依赖
        "dm_control>=1.0.14",  # 之前推荐用来组合地形的库
        "scipy",               # 计算信号处理、统计指标常用
        "matplotlib",          # 用于画出评估图表
        "pandas",              # 用于生成评估报告表格
        "tqdm",                # 显示评估进度条
        # "gymnasium",         # 如果你的接口兼容 gym
        # "torch",             # 如果你需要加载 pytorch 模型
    ],
    python_requires=">=3.8",
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Robotics",
    ],
)
