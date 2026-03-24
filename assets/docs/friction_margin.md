# friction_margin

## 基本定义

该指标用于度量当前足端接触是否仍然处于可接受的库仑摩擦锥内。实现上，它不是直接对每个原始接触点求平均，而是先按足端 `geom` 聚合，再对每只参与计算的脚求摩擦裕度，最后使用法向力进行加权平均。

## MuJoCo 中的实现约定

在代码中，仅统计机器人配置 `foot_geom_names` 中声明的足端 `geom`。这里使用的是 `dynamics.contacts` 中已经整理出的机器人与外界之间的接触信息，并不会像 ZMP 指标那样额外按接触距离阈值再筛选一次。

设当前共有 $N$ 只足端参与摩擦裕度计算。对于第 $i$ 只足端，其可能包含多个原始接触点。将这些接触点的接触力聚合后，定义：

- 切向力总和：$f_i^{\text{tangent}}$
- 法向力总和：$f_i^{\text{normal}}$
- 摩擦极限：$f_i^{\text{limit}}$

其中

$$
f_i^{\text{normal}} = \sum_{j \in \mathcal{C}_i} f_{ij}^{\text{normal}}
$$

$$
f_i^{\text{tangent}} = \sum_{j \in \mathcal{C}_i} f_{ij}^{\text{tangent}}
$$

$$
f_i^{\text{limit}} = \sum_{j \in \mathcal{C}_i} \mu_{ij} f_{ij}^{\text{normal}}
$$

这里 $\mathcal{C}_i$ 表示第 $i$ 只脚对应的原始接触点集合，$\mu_{ij}$ 是第 $j$ 个接触点的摩擦系数。注意，代码中使用的是各接触点切向力模长的逐点求和结果，而不是先做二维切向合力向量相加后再取范数。

## 单足摩擦裕度

对第 $i$ 只足端，定义其摩擦利用率为

$$
\nu_i = \frac{f_i^{\text{tangent}}}{f_i^{\text{limit}}}
$$

则单足摩擦裕度为

$$
m_i^{\text{friction}} = \max \left(0, 1 - \nu_i \right)
$$

当某只脚的摩擦极限 $f_i^{\text{limit}}$ 过小或数值异常时，代码会直接将该足端的摩擦裕度记为 $0$。当某只脚的总法向力 $f_i^{\text{normal}}$ 不超过阈值 `force_threshold` 时，该脚不会参与最终平均。

## 总体 friction_margin

整体指标使用各足端法向力作为权重进行加权平均。令

$$
w_i = \frac{f_i^{\text{normal}}}{\sum_{k=1}^{N} f_k^{\text{normal}}}
$$

则总的 `friction_margin` 定义为

$$
m_{\text{friction margin}} = \sum_{i=1}^{N} w_i \, m_i^{\text{friction}} = \sum_{i=1}^{N} w_i \max \left(0, 1 - \frac{f_i^{\text{tangent}}}{f_i^{\text{limit}}} \right)
$$

等价地，也可写为

$$
m_{\text{friction margin}} = \sum_{i=1}^{N} w_i \max \left(0, 1 - \frac{f_i^{\text{tangent}}}{\sum_{j \in \mathcal{C}_i} \mu_{ij} f_{ij}^{\text{normal}}} \right)
$$

## 与代码一致的边界情况

- 当没有任何接触点时，指标直接返回 $1.0$。
- 当存在接触，但没有任何接触点匹配到 `foot_geom_names` 时，指标也返回 $1.0$。
- 当某只脚的总法向力小于等于阈值 `force_threshold` 时，该脚不会参与平均。
- 日志中的 `friction_margin_contact_count` 统计的是匹配到足端 `geom` 的原始接触点数量，不是足端数量。
- 日志中的 `friction_margin_foot_count` 统计的是最终参与计算的足端数量。
- 日志中的 `friction_margin_worst_utilization` 记录的是所有参与计算足端中最大的摩擦利用率。
