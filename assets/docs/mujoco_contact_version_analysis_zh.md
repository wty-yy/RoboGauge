# MuJoCo 3.2.3 与 3.10 接触动力学差异排查

最终还是不能提高代码版本，版本维持在`<3.3.0`以下

本文记录 RoboGauge 中 Go2 MoE 策略在 MuJoCo 3.2.3 与 3.10.0 下的接触动力学差异、wave 地形失败、flat 评分差异，以及 `solref`、native CCD 和摩擦指标之间的关系。

## 1. 测试环境

本次排查使用两个 Python 环境：

| 环境 | Python 路径 | MuJoCo | dm_control |
|---|---|---:|---:|
| RoboGauge | `/home/user/Coding/robotics/RoboGauge/.venv/bin/python` | 3.2.3 | 1.0.23 |
| 新版本 | `/home/user/isaaclab/bin/python` | 3.10.0 | 1.0.43 |

主要测试命令：

```bash
python robogauge/scripts/run.py \
    --task go2_moe.wave \
    --experiment-name debug \
    --headless
```

```bash
python robogauge/scripts/run.py \
    --task go2_moe.flat \
    --experiment-name debug \
    --headless
```

Go2 脚部碰撞配置位于 [`resources/robots/go2/go2.xml`](../resources/robots/go2/go2.xml)：

```xml
<option cone="elliptic" impratio="100" />

<default class="foot">
  <geom size="0.022" pos="-0.002 0 -0.213"
        priority="1" condim="6"
        friction="0.4 0.02 0.01"
        solref="0.006 1"/>
</default>
```

仿真步长为：

```text
simulation_dt = 0.002 s
```

## 2. 结论摘要

1. wave 地形上的巨大轨迹差异主要来自高度场接触点和接触法线的细微变化，随后被闭环策略快速放大。
2. MuJoCo 3.10 的 native CCD 不是普遍更差，而是策略训练时使用的接触动力学分布与新接触实现不一致。
3. 将脚部 `solref` 从默认的 `0.02 1` 改为 `0.006 1`，可以显著减少 3.10 native CCD 在高度场上的脚部下陷，并恢复 wave run 42 的成功。
4. `solref="0.006 1"` 不是一个小修改：法向刚度约提高 11.1 倍，阻尼约提高 3.33 倍。
5. 当脚部使用 `condim="6"` 和椭圆摩擦锥时，动态生成的接触默认让摩擦维度继承同一个 `solref`。因此 `0.006` 不仅改变法向穿透，还会显著改变切向摩擦冲量。
6. flat 地面使用球–平面的解析碰撞，不依赖通用 native-CCD 碰撞管线。flat 分数差异主要不是 native CCD，而是新的接触约束求解结果在摩擦锥边界附近产生了更多低摩擦裕度样本。
7. RoboGauge 使用逐帧几何平均计算质量分数；一个为零的摩擦指标就可能把该帧质量分数压到约 `0.1`，因此少量接触力异常会被明显放大。
8. `solreffriction` 不是 `<geom>` 属性，只能用于显式 `<contact><pair>`。在当前 RoboGauge 架构中，机器人和地形分别解析后再 attach，因此脚–地面 contact pair 必须在 attach 后、模型编译前由 Python 创建。

## 3. native CCD 的版本变化

MuJoCo 3.2.3 引入了实验性的 `nativeccd` 开关：

- 默认仍使用旧的 libccd 路径；
- native CCD 当时处于早期测试阶段；
- 在本项目的 3.2.3 高度场任务中，强制开启 native CCD 会在运行阶段触发 MuJoCo 原生层 segmentation fault，Python 无法捕获。

MuJoCo 3.3.0 将 native CCD 设为默认实现。它使用 MuJoCo 原生的 GJK/EPA 管线替代旧 libccd/MPR 路径。

后续版本还改变了其他默认行为，例如：

- 3.3.6：constraint island 默认开启，并修改了 `qacc_warmstart` 的更新时间；
- 3.8.0：multiccd 默认开启；
- 3.10.0：继续改进约束求解器收敛和 constraint island 内部实现。

关闭 `nativeccd`、`island` 和 `multiccd` 只能关闭对应功能，不能把 MuJoCo 3.10 的全部约束求解代码恢复成 3.2.3。

官方参考：

- [MuJoCo changelog](https://mujoco.readthedocs.io/en/stable/changelog.html)
- [MuJoCo computation](https://mujoco.readthedocs.io/en/latest/computation/index.html)

## 4. wave 地形：微小接触差异如何被策略放大

在 MuJoCo 3.10 中仅切换 native CCD，第一次 RR 脚与高度场接触发生在约 `0.056 s`：

- 接触位置差异约 `0.26 mm`；
- 接触法线方向差异约 `0.05°`。

机器人构型差异随后快速增加：

| 时间 | 构型差异超过 |
|---:|---:|
| 0.060 s | `1e-6` |
| 0.174 s | `1e-3` |
| 0.694 s | `0.1` |

放大链路如下：

```text
接触点/法线轻微变化
        ↓
地面反作用力与摩擦冲量变化
        ↓
关节速度和机身姿态变化
        ↓
策略观测变化
        ↓
MoE 选择或输出不同动作
        ↓
下一次落脚位置变化
        ↓
下一步产生更大的接触差异
```

这是一个典型的闭环混沌放大过程。初始接触差异小，并不意味着一秒后的轨迹仍然接近。

### 4.1 二值成功指标也会放大表面差异

wave 的成功条件是机器人底座在超时前进入目标周围半径 `0.1 m` 的区域。相关逻辑位于 [`robogauge/tasks/gauge/goals/velocity_goals.py`](../robogauge/tasks/gauge/goals/velocity_goals.py)。

因此，3.10 的失败轨迹不一定代表机器人已经失稳。原始失败结果仍有相近的质量分数和较好的姿态稳定性，只是轨迹发生偏移，未在 20 秒内进入很小的目标区域。

## 5. wave 地形的脚部下陷测量

测量实际 foot–heightfield `contact.dist` 后得到：

| 配置 | 平均穿透 | P95 | P99 | 最大穿透 | 成功 | 质量分数 |
|---|---:|---:|---:|---:|---:|---:|
| 3.10 native，默认 `solref=.020` | 9.818 mm | 23.0 mm | 24.4 mm | 31.661 mm | 0 | 0.4992 |
| 3.10 native，`solref=.010` | 1.261 mm | 5.62 mm | 8.61 mm | 15.64 mm | 1 | 0.5120 |
| 3.10 native，`solref=.006` | 0.540 mm | 2.603 mm | 4.609 mm | 8.592 mm | 1 | 0.5061 |
| 3.10 legacy，默认接触 | 4.83 mm | 16.0 mm | 20.6 mm | 29.8 mm | 1 | 0.4041 |

`solref=.006` 在 3.10 native CCD 下将平均穿透从约 `9.8 mm` 降到 `0.54 mm`，并恢复 run 42 成功。

以下尝试没有解决问题，部分设置反而恶化结果：

- 增大 geom margin 到 `0.003`；
- 只提高 `solimp`；
- 将 `impratio` 从 100 降到 10 或 1；
- 将脚部 `condim` 从 6 改为 3；
- 同时修改 `solref` 和更硬的 `solimp`。

因此，针对当前策略和模型，最有效的单项修改是缩短脚部接触 time constant。

## 6. `solref` 的物理含义

当 `solref` 两个值均为正数时，其格式为：

```text
(timeconst, dampratio)
```

MuJoCo 使用近似关系：

```text
k ∝ 1 / timeconst²
b ∝ 1 / timeconst
```

从默认 `0.02` 改成 `0.006`：

```text
法向刚度比例 ≈ (0.02 / 0.006)² ≈ 11.1
阻尼比例     ≈  0.02 / 0.006    ≈ 3.33
```

因此 `0.006` 代表明显更硬、更快的接触响应。

MuJoCo 建议：

```text
timeconst >= 2 × timestep
```

本项目中：

```text
timestep = 0.002
2 × timestep = 0.004
```

所以：

- `0.006` 等于 3 个仿真步，虽然高于推荐下限，但已经比较硬；
- `0.004` 正好位于推荐下限，数值安全余量较小；
- 如果还需要进一步减少瞬态穿透，更合理的方法是减小 timestep，再重新调整 `solref`，而不是继续在 `dt=0.002` 下无限减小 time constant。

官方参考：

- [MuJoCo modeling: solver parameters](https://mujoco.readthedocs.io/en/stable/modeling.html)

## 7. 为什么 flat 分数也会变化

flat 对比结果：

- 3.2.3：[`logs/go2_moe_flat_debug_mj3.2.3/20260722-20-10-25_run_42/results.yaml`](../logs/go2_moe_flat_debug_mj3.2.3/20260722-20-10-25_run_42/results.yaml)
- 3.10：[`logs/go2_moe_flat_debug_mj3.10/20260722-20-10-33_run_42/results.yaml`](../logs/go2_moe_flat_debug_mj3.10/20260722-20-10-33_run_42/results.yaml)

总体结果：

| 配置 | 总质量分数 | max-velocity 分数 | max-velocity `mean@25` |
|---|---:|---:|---:|
| 3.2.3，`solref=.006` | 0.8033 | 0.8519 | 0.7491 |
| 3.10，`solref=.006` | 0.7884 | 0.8279 | 0.6569 |

总体平均分只下降约 `0.0149`，即约 1.5 个百分点。看起来特别大的部分主要是 max-velocity 的最差 25% 样本。

### 7.1 机器人的主要运动指标实际上非常接近

| 指标 | 3.2.3 | 3.10 |
|---|---:|---:|
| lin_vel_err | 0.7947 | 0.7941 |
| orientation_stability | 0.9769 | 0.9772 |
| dof_power | 0.9026 | 0.9028 |
| torque_smoothness | 0.8265 | 0.8264 |

这说明主要运动质量没有发生同等幅度的恶化。

差异集中在摩擦指标：

| 指标 | 3.2.3 | 3.10 |
|---|---:|---:|
| max-velocity friction mean | 0.7613 | 0.7564 |
| max-velocity friction `mean@25` | 0.6069 | 0.5366 |

## 8. flat 上不是 native CCD 导致的

flat 地面是脚部球体与无限平面的接触：

```text
sphere foot ↔ plane floor
```

MuJoCo 对 sphere–plane 使用解析 primitive collision，而不是通用 GJK/EPA native-CCD 管线。

隔离实验结果：

| MuJoCo 3.10 配置 | 总分 | max-velocity | max-velocity `mean@25` |
|---|---:|---:|---:|
| 默认，`solref=.006` | 0.7884 | 0.8279 | 0.6569 |
| 关闭 native CCD，`.006` | 0.7875 | 0.8261 | 0.6505 |
| native/island/multiccd 全关闭，`.006` | 0.7864 | 0.8221 | 0.6353 |
| 默认新特性，`solref=.020` | 0.7987 | 0.8496 | 0.7427 |
| 3.2.3，`solref=.006` | 0.8033 | 0.8519 | 0.7491 |

结论：

- 关闭 native CCD 没有恢复分数；
- 关闭 island 和 multiccd 也没有恢复分数；
- 将 `solref` 恢复为 `0.02` 后，3.10 的 flat 分数明显接近 3.2.3。

因此 flat 差异不是 native CCD 的碰撞点差异，而是硬接触参数在两个版本的约束求解实现中产生了不同的摩擦力尖峰和摩擦锥饱和样本。

## 9. 为什么法向 `solref` 会影响摩擦分数

脚部使用：

```xml
condim="6"
```

同时全局使用：

```xml
cone="elliptic"
```

在椭圆摩擦锥中，摩擦维度的位置残差恒为零，因此：

- 摩擦维度的刚度项为零；
- `timeconst` 控制切向约束速度的指数衰减；
- `dampratio` 在正数格式下对摩擦维度不生效；
- 如果没有显式指定 `solreffriction`，摩擦维度继承接触的 `solref`。

所以：

```text
solref=.006
    ↓
法向接触更硬
    +
切向摩擦速度衰减更快
    ↓
切向冲量更尖锐
    ↓
更多样本接近或达到摩擦锥边界
```

## 10. RoboGauge 评分如何放大少量摩擦异常

摩擦裕度在 [`robogauge/tasks/gauge/metrics/stable_metric.py`](../robogauge/tasks/gauge/metrics/stable_metric.py) 中近似计算为：

```text
friction_margin = max(0, 1 - ||Ft|| / (μ Fn))
```

其中：

- `Fn` 是法向接触力；
- `Ft` 是两个切向分量的范数；
- `μ` 是滑动摩擦系数。

当：

```text
||Ft|| >= μ Fn
```

该脚的摩擦裕度会被截断为零。

质量分数在 [`robogauge/tasks/gauge/goals/base_goal.py`](../robogauge/tasks/gauge/goals/base_goal.py) 中逐帧使用加权几何平均：

```text
quality = geometric_mean(metrics)
```

零指标会先被限制为 `1e-9`。当前质量指标权重之和为 10，因此一个权重为 1 的零摩擦指标会贡献：

```text
(1e-9)^(1/10) ≈ 0.126
```

其他指标再与其相乘后，该帧质量分数通常约为 `0.1`。

原始逐帧统计显示：

| max-velocity 统计 | 3.2.3 | 3.10 |
|---|---:|---:|
| quality minimum | 0.070 | 0.100 |
| quality P1 | 0.634 | 0.106 |
| friction minimum | 0.035 | 0.000 |
| worst-quality 帧上的 friction mean | 0.692 | 0.630 |

3.10 出现了多个摩擦裕度恰好为零的样本，因此 quality P1 从 `0.634` 降至 `0.106`。

### 10.1 `mean@25` 的含义

`mean@25` 不是仿真的前 25% 时间。

实现会：

1. 将全部指标样本从小到大排序；
2. 取最差的 25%；
3. 对这些最差样本求平均。

因此几个接近零的异常帧会显著拉低 `mean@25`，即使总体平均运动质量变化不大。

## 11. 3.2.3 与 3.10 的“结算”差异在哪里

两边编译后的主要外部选项一致：

| 参数 | 3.2.3 | 3.10 |
|---|---:|---:|
| solver | Newton | Newton |
| integrator | Euler | Euler |
| iterations | 100 | 100 |
| tolerance | `1e-8` | `1e-8` |
| cone | elliptic | elliptic |
| impratio | 100 | 100 |

flat 上的差异不主要发生在接触点生成阶段，而发生在约束力求解阶段：

```text
相同的 sphere–plane 解析接触
        ↓
构造法向与切向约束 Jacobian
        ↓
根据 solref/solimp 计算 K、B 和 impedance
        ↓
Newton 求解、warm-start、摩擦锥约束
        ↓
得到 Fn、Ft 和广义约束力
        ↓
RoboGauge 计算 Ft / (μ Fn)
```

MuJoCo 3.2.3 到 3.10 之间对约束 warm-start、island、接触数据管线和求解器收敛实现进行了多次修改。即使两个版本的机器人位姿和速度十分接近，单个时刻的 `Fn`/`Ft` 分配仍可能略有不同。

当 `solref=.02` 时，接触较软，两个版本的细微差异通常不会频繁跨过摩擦锥边界。

当 `solref=.006` 时，接触响应更快、更硬，摩擦利用率更容易接近：

```text
||Ft|| / (μ Fn) = 1
```

此时非常小的数值差异就可能让 RoboGauge 摩擦裕度从一个小正数直接变成零。

需要注意：目前的隔离实验可以确认差异位于接触约束求解/力分配以及评分放大链路，但如果要把剩余差异精确归因到某一个 MuJoCo commit，仍需要在 3.2.3 到 3.10 之间做版本二分测试。

## 12. `solreffriction` 的正确用法

以下写法是无效的：

```xml
<geom solref="0.006 1" solreffriction="0.02 1"/>
```

MuJoCo 会报错：

```text
AttributeError: 'solreffriction' is not a valid attribute for <geom>
```

`solreffriction` 只支持显式 contact pair：

```xml
<contact>
  <pair geom1="FL" geom2="floor"
        condim="6"
        friction="0.4 0.4 0.02 0.01 0.01"
        solref="0.006 1"
        solreffriction="0.02 1"/>
</contact>
```

其中：

- `solref="0.006 1"` 控制法向接触；
- `solreffriction="0.02 1"` 控制椭圆摩擦锥的切向维度；
- `solreffriction="0 0"` 表示继续继承 `solref`。

官方参考：

- [MuJoCo XML contact/pair reference](https://mujoco.readthedocs.io/en/latest/XMLreference.html)

## 13. 为什么不能直接把 contact pair 写进 `flat.xml`

当前加载流程位于 [`robogauge/tasks/simulator/mujoco_simulator.py`](../../robogauge/tasks/simulator/mujoco_simulator.py)：

```python
robot_mjcf = mjcf.from_path(robot_xml)
terrain_mjcf = mjcf.from_path(terrain_xmls[0])

attachment_frame = terrain_mjcf.attach(robot_mjcf)
self.mj_physics = mjcf.Physics.from_mjcf_model(terrain_mjcf)
```

机器人和地形首先被分别解析：

- `go2.xml` 中不存在 `floor`；
- `flat.xml` 中不存在 `FL`、`FR`、`RL`、`RR`；
- attach 后机器人 geom 还会获得类似 `go2/FL` 的命名空间。

因此脚–地面显式 pair 必须在 attach 后、`Physics.from_mjcf_model()` 前创建。

RoboGauge 目前已在统一的 MuJoCo 加载入口实现这一逻辑。配置位于
`MujocoConfig.physics.foot_contact_solreffriction`，默认值为
`[0.02, 1.0]`。pipeline 会把
`robot_cfg.assets.foot_geom_names` 传给 simulator；simulator 在 attach
机器人之前记录所有地形 geom（包括附加的 wall），再为每只脚与每个地形
geom 创建显式 pair。

实现的核心形式如下：

```python
floor = terrain_mjcf.find('geom', 'floor')
feet = [
    robot_mjcf.find('geom', name)
    for name in ('FL', 'FR', 'RL', 'RR')
]

attachment_frame = terrain_mjcf.attach(robot_mjcf)
attachment_frame.add('freejoint', name='root')

for foot in feet:
    terrain_mjcf.contact.add(
        'pair',
        geom1=foot,
        geom2=floor,
        condim=6,
        friction=[0.4, 0.4, 0.02, 0.01, 0.01],
        solref=[0.006, 1.0],
        solreffriction=[0.02, 1.0],
    )

self.mj_physics = mjcf.Physics.from_mjcf_model(terrain_mjcf)
```

显式 pair 会接管 geom 自动合成的接触参数，因此实现还会复制足端继承到的
`condim`、friction、`solref`、`solimp`、margin 和 gap，只单独覆盖
`solreffriction`。domain randomization 修改 friction 时也会同步修改 pair 的
两个滑动摩擦系数。

编译后两个版本都能正确保存：

```text
pair_solref         = [0.006, 1.0]
pair_solreffriction = [0.020, 1.0]
```

验证覆盖了资源目录中的 43 个主地形 XML：MuJoCo 3.2.3 和 3.10.0
均成功编译。根据地形 geom 数量，每个模型生成 4 到 152 个 foot–terrain
pair。flat 实际运行时生成 4 个 pair；wave（floor、heightfield 和四面 wall）
实际运行时生成 24 个 pair。

## 14. 推荐方案

### 方案 A：按地形使用不同 `solref`

这是实现最简单、风险最低的方案：

```text
flat / 普通平面：solref = 0.02 1
wave / hfield：  solref = 0.006 1
```

优点：

- flat 保持平滑摩擦响应；
- wave 减少 native CCD 高度场穿透；
- 不需要显式 contact pair。

缺点：

- 需要 terrain-specific 模型或加载时覆盖；
- 同一个机器人 XML 无法单独表达这种差异。

### 方案 B：分离法向和摩擦 `solref`

使用显式 contact pair：

```text
normal solref       = 0.006 1
friction solref     = 0.02 1
```

优点：

- 法向接触足够硬，可减少高度场下陷；
- 切向摩擦保持原先较平滑的动力学；
- 物理含义最清晰。

缺点：

- 需要在机器人与地形 attach 后创建 pair；
- 每类地形碰撞 geom 都需要覆盖；
- 显式 pair 会覆盖由两个 geom 自动混合得到的接触参数，需要完整指定 `condim`、friction、solref 和 solimp 相关行为并回归测试。

### 方案 C：使用折中 time constant

例如：

```text
solref = 0.01 1
```

已有 wave 测试中，`0.01` 可以成功，并将平均穿透降到约 `1.26 mm`。它比 `0.006` 更软，可能减少 flat 上的摩擦力尖峰。

但该方案必须对 flat、wave、slope、stairs 和 obstacle 做完整回归，不能仅凭单个 run 选择。

## 15. 推荐的回归测试矩阵

修改接触参数后至少测试：

| 版本 | flat | wave | slope | stairs | obstacle |
|---|---|---|---|---|---|
| MuJoCo 3.2.3 | 必测 | 必测 | 建议 | 建议 | 建议 |
| MuJoCo 3.10 | 必测 | 必测 | 建议 | 建议 | 建议 |

每个任务同时关注：

- overall quality score；
- `mean@25` 和 `mean@50`；
- 线速度与角速度误差；
- orientation stability；
- friction margin，尤其是零值数量；
- ZMP margin；
- 最大和 P95 接触穿透；
- 是否在目标区域判定上成功；
- 是否出现 segmentation fault、penetration reset 或数值发散。

不要只比较最终 success。对闭环策略来说，二值成功可能因为很小的终点位置差异发生翻转。

## 16. 最终建议

针对当前 Go2 MoE 策略，建议优先采用以下顺序：

1. 保留 MuJoCo 3.10 的 native CCD 默认行为；
2. 不在 MuJoCo 3.2.3 高度场任务中强制开启实验性 native CCD；
3. wave/hfield 使用更短的法向 time constant，例如 `0.006` 或经过回归后的 `0.01`；
4. flat 不要无条件继承同样硬的切向摩擦 time constant；
5. 若需要统一模型，使用 attach 后显式 contact pair，将 `solref` 与 `solreffriction` 分离；
6. 若优先追求代码简单，采用 terrain-specific `solref`；
7. 评估版本差异时同时查看逐项指标和原始接触力，不要仅依赖几何平均总分及二值 success。

这组实验说明：`solref` 不是单纯的“防穿透参数”。在 `condim=6`、椭圆摩擦锥和闭环策略评估中，它会同时改变法向接触、切向摩擦、策略轨迹和评分分布。
