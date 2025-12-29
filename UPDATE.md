# UPDATE
## 20251229
### v1.0.0
1. 完成stress pipeline的客户端, 服务端代码, 支持异步推理
2. 加入MultiPipeline和LevelPipeline分开的种子数量`seeds, search_seeds`, Level 5个, Multi 3个, 这样可以显著提高速度, 并且保证评估精度不掉 (两种评估总分前三位都是相同的), 速度提升`3m 32s -> 2m 47s`
3. 删除stairs_down任务, 将stairs_up重命名为stairs
4. 对于slope, stairs再分化为两个任务, slope_fd, slope_bd, stairs_fd, stairs_bd, 分别表示正向/背向朝更高处的初始化, target_pos_velocity中指令同时根据是否backward反转
## 20251228
### v0.1.18
1. 将final_score改为merge_metrics, 并在multi_pipeline中也进行该评估
2. [放弃, 好像也没这个必要] 上下台阶取二者的最小等级, 实现中都计算出来, 统计地形得分时仅计算二者种较低等级的一个
3. 对有难度地形设置goals, 但是忘记设置到地形的正中心了!!!在每种地形上调出对应的中心初始位置
4. 添加`--spawn-type`配置, 根据评估和搜索修改初始生成点, 完成slope, wave, stairs up, stairs down, obstacle
5. 重新详细设计整个打分标准, 引入几个阶段性得分: quality_score, terrain_quality_score, robust_score, benchmark_score
6. 对于楼梯环境, 计算benchmark_score和统计每个metrics平均分时, 不计算下楼梯, 因为下楼梯几乎对模型没有仍和区分度 (都是最高难度)
Fix bug: 修复零难度的地形个数计算问题
## 20251227
### v0.1.17
1. args中添加`goals`配置, 在LevelPipeline和MultiPipeline中指定goals, 修正压力测试中评估的目标不对的问题
2. 评估必须使用5个种子, 否则LevelPipeline中的80%通过率就没有意义了, 并且提高5个种子最终的评级影响可能非常大 (moe.stairs_up Friction 2.0从Lv 7->10)
3. 在StressPipeline测试中, 不再保存
4. 添加obstacles地形
5. 优化分数计算方法, 按照`(level-1)*0.1+metric_score`计算
6. 加入日志文件夹递归保存, StressPipeline -> LevelPipeline -> MultiPipeline, 加入压缩参数`--compress-logs`, 将日志文件夹压缩为`subtasks.tar.xz`, 日志文件压缩`4M->100kb` (6种地形的全部评估测试日志压缩后`29M->539K`)
7. StressPipeline和MultiPipeline同时工作时, 很大概率发生死锁 (StressPipeline传入的任务超过10个以上), 将MultiPipeline的num-processes设置为1即可避免该问题 (不创建Process), 为了提高速度可以将flat的不同域随机化也展平
8. 将进度条换成当前时间/剩余时间
9. 添加`plot_terrain_levels.py`绘图代码, 绘制5种可变等级的地形与摩擦系数的关系图
## 20251226
### v0.1.16
1. 基本完成StressPipeline, 加入绘制进度条的线程, 其他进程通过Queue更新主进程的进度条
2. wave地形的穿模判定非常容易触发, 加入最多穿模判定重启次数为1次, 超过该次数后穿模就不再自动重启了
3. 当全部地形等级均失败时, 需要将全部metric都按0计算

FIX Bugs: (level_results会存储到MultiPipeline下, 因为MultiPipeline不是子进程启动的, 会覆盖LevelPipeline的Logger冲突) 通过创建新的Logger实现
## 20251225
### v0.1.15
1. 统一terrain的大小为10x10m, 某一边的中点在(0,0,0), 对全部的带等级的terrain都加上边界墙高度10m
2. 完成stairs_up调试台阶高度范围改为(0.05-0.23m)非线性增加, 简单测试了5个种子下moe和mlp能达到的最大地形等级

    | frction | 0.5 | 0.75 | 1.0 | 1.5 | 2.0 |
    | - | - | - | - | - | - |
    | moe | 1 | 7 | 9 | 8 | 10 |
    | mlp | 1 | 4 | 7 | 8 | 9 |

3. 发现有穿模问题, 加入穿模判定0.035m, BaesPipeline新增一个warning穿模报错, 发生穿模重置当前goal并重置环境, 不计入失败
    3.1. 穿模判定在斜坡上会有很大的问题, 对slope一侧加上0.8m的可供站立平地, 并取消关于wall和floor的穿模判定
4. 发现可以通过同时增加台阶的宽度从而避免产生体积为0的接触点, 一定程度减少穿模问题
5. 判定Level通过比例为0.8, 也就是5个种子有4个通过即可
6. 完成stairs_down地形调试, 简单比较moe和mlp通过地形难度, 初始点和中点在y方向上有3m差距, 避免直接滚下去恰好通过

    | frction | 0.5 | 0.75 | 1.0 | 1.5 | 2.0 |
    | - | - | - | - | - | - |
    | moe | 5 | 10 | 10 | 10 | 10 |
    | mlp | 3 | 6 | 7 | 10 | 10 |

## 20251224
### v0.1.14
1. 处理LevelPipeline返回的result信息, 保存最高等级可通过地形返回的aggregated_results和level等级
2. 完成wave地形的LevelPipeline支持
3. 各种Pipeline的run直接返回dict信息, 不再是路径
## 20251222
### v0.1.13
1. 即使模型崩溃也要继续测完后续的goals, 但是跳过当前的sub goals
2. 加入当翻滚角>2.5rad时认为崩溃, 自动切换为下一个goal
3. 初步完成二分查找level等级, 细节如下
    LevelPipeline: 一种二分查找当前域随机化(friction, base_mass)下的最大成功terrain等级, 每次测试中采用三个seeds, 调用MultiPipeline同时测试三个seeds, 如果同时全部成功, 则判定为通过
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