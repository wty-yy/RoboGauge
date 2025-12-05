# UPDATE
## 20251205
### v0.1.7
1. 加入moe模型的测试, 及moe模型, 平地的指令最大范围开到2
## 20251203
### v0.1.6.1
1. 加入lin_vel, ang_vel err指标
## 20251202
### v0.1.6
1. 加入新目标`diagonal_velocity`, 记录的信息中仅保留总goal的metrics信息, metrics加入@25, @50两个后25%和50%的平均值
## 20251201
### v0.1.5
1. 加入goals, metrics结果存储
2. 优化路径存储: `logs/experiment_name/`下分别有两个文件`{time_tag}_{run_name}`存储实验启动的参数, 保存视频; `data/robot/model/goal/{time_tag}_{run_name}`下存储tensorboard
3. 优化视频存储, 优先记录可视化界面, 否则使用跟随base的相机
4. 修改`go2.xml`大腿的电机范围不超过base的高度
## 20251130
### v0.1.4
1. 加入velocity_goals中的MaxVelocityGoal, 依次执行每种维度上的极值
2. 加入metrics中的dof_limits_metric, 计算关节扭矩超过soft_dof_limit的比例
## 20251128
### v0.1.3
1. 完成go2模型预测

## 20251127
### v0.1.2
1. 修改logger
2. 完成mujoco的sensor数据, sim_data数据类处理

## 20251124-25
### v0.1.1
1. 完成初始化
2. 架构设计