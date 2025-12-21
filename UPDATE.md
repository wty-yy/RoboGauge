# UPDATE
TODO: 即使模型崩溃也要继续测完后续的goals
## 20251221
### v0.1.12
1. 在模型崩溃时也记录下最后的gauge信息, 修改single/multi pipeline逻辑
2. 添加slope全等级地形, 关系式: 斜率$0.1+0.47d$，角度范围$5.7\sim29.7^\circ$, 发现29.7度在2.4摩擦系数下可以稳定通过
## 20251220
### v0.1.11
1. 加入`os.environ["OMP_NUM_THREADS"] = "2"; os.environ["MKL_NUM_THREADS"] = "2"`避免并行时cpu线程爆炸, `--multi`模式能稳定提高速度了
2. 完成target_position_goal, 超参数包含: 目标点位置, 最大线速度角速度, 最长追踪时间, 追踪到达阈值范围; 并在mujoco中绘制红色目标点, result.yaml中记录当前terrain和success
3. 修改goal的reset逻辑
    旧版: 在sub_goal开始时通过实现类中的get_goal异常返回None判断当前goals全部结束, 并且goals全部结束也不reset环境;
    新版: 加入goal.pre_get_goal, 判断当前系列goals是否全部结束, 并根据sim_data更新当前的sub_goal索引, 实现类中无需考虑异常处理, 并且goals全部结束时判断为change goal执行一次reset环境, 保证新的goal可以直接无缝衔接上
4. 添加vscode python debug启动配置文件, 支持参数输入调试
Fix Bugs: 修复sub_goal重名, 日志info不显示的问题
## 20251218
### v0.1.10
1. 加入`--write-tensorboard`参数, 默认为`False`即不记录`gauge`的日志信息
2. 指令系数改为1.8 (比2.0稳定点)
3. 完成全部指标, 新增`dof_power, orientation_stability, torque_smoothness`
4. 加入雷达图绘图
Fix Bugs: 日志记录重复的问题
### v0.1.9
1. 在`MaxVelocityGoal`基础上加入`end_stance`, 最终保持站立姿态
2. 在开始goal控制前, 先等机器人落地, 通过线速度小于0.05阈值判断静止后, 执行goal
3. 支持1920x1080录像保存
Fix Bugs: 修复Video frame skip过大问题
## 20251206
### v0.1.8
1. 加入run_eval_models.sh多模型评估bash脚本
2. 加入域随机化, `action delay`, 基于配置修改的`base mass`, `friction`
3. 加入MultiPipeline支持多种seeds, frictions, base masses并行评估
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