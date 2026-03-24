# zmp_margin

参考论文：[ZERO-MOMENT POINT -- THIRTY FIVE YEARS OF ITS LIFE](https://www.worldscientific.com/doi/abs/10.1142/S0219843604000083)

## 基本定义

- Zero Moment Point（ZMP，零矩点）：机械系统的惯性力与重力对某点的合力矩在水平轴方向上的分量为零时，该点称为 ZMP。
- Support Polygon（支撑多边形）：所有有效地面接触点在水平面上的投影构成的凸包。
- FZMP（fictitious ZMP，虚拟零矩点）：当 ZMP 落在支撑多边形外时，称其为 FZMP，此时系统可能处于非平衡状态。
- Virtual Horizontal Plane（虚拟水平投影面）：记所有有效接触点的三维几何中心为 $O'$，将世界坐标系平移到 $O'$ 后，其 $xy$ 平面即本文使用的参考平面。

## MuJoCo 中的符号约定

在实现中，首先选出满足接触距离阈值的有效接触点 $\{\boldsymbol{c}_k\}_{k=1}^{K}$，并定义其几何中心为

$$
O' = \frac{1}{K} \sum_{k=1}^{K} \boldsymbol{c}_k
$$

这里的 $O'$ 就是代码中的 `support_center`。注意它是所有有效接触点的简单平均，不是按接触力加权的中心，也不是支撑多边形的面积质心。

随后以 $O'$ 为原点建立平移后的参考平面，其方向仍与世界坐标系保持一致。

设机器人总共包含 $N$ 个动态刚体。这里的“动态刚体”指质量 $m_i > 0$ 的刚体。对于第 $i$ 个刚体，在当前时刻具有如下量：

- 质量：$m_i$
- 质心位置：$\boldsymbol{p}_i$
  这里表示该刚体质心相对于 $O'$ 的位置。
- 质心线加速度：$\boldsymbol{\ddot{p}}_i$
- 角速度：$\boldsymbol{\omega}_i$
- 角加速度：$\boldsymbol{\dot{\omega}}_i$
- 惯性张量：$\boldsymbol{I}_i$，并且需要是世界坐标系下的惯性张量。

除 $\boldsymbol{p}_i$ 是相对于 $O'$ 的相对位置外，其余运动学与动力学量均在世界坐标系下表达，并保持相对于惯性参考系计算。

## 总力与总力矩

整个系统的总力与总力矩定义为：

$$
\boldsymbol{F}_{\text{total}} = \sum_{i=1}^{N} m_i \left(\boldsymbol{g} - \boldsymbol{\ddot{p}}_i\right)
$$

$$
\boldsymbol{M}_{\text{total}} =
\sum_{i=1}^{N}
\left[
\left(\boldsymbol{p}_i \times m_i \left(\boldsymbol{g} - \boldsymbol{\ddot{p}}_i\right)\right)
- \left(\boldsymbol{I}_i \boldsymbol{\dot{\omega}}_i + \boldsymbol{\omega}_i \times \left(\boldsymbol{I}_i \boldsymbol{\omega}_i\right)\right)
\right]
$$

## ZMP 坐标

由

$$
\boldsymbol{M} = \boldsymbol{r} \times \boldsymbol{F}
$$

可得

$$
\begin{cases}
\boldsymbol{M}_y = -x_{\text{zmp}} \boldsymbol{F}_z + z_{\text{zmp}} \boldsymbol{F}_x \\
\boldsymbol{M}_x = \phantom{-}y_{\text{zmp}} \boldsymbol{F}_z + z_{\text{zmp}} \boldsymbol{F}_y
\end{cases}
$$

当 $z_{\text{zmp}} = 0$ 时，有

$$
\begin{cases}
x_{\text{zmp}} = -\dfrac{\boldsymbol{M}_y}{\boldsymbol{F}_z} \\
y_{\text{zmp}} = \phantom{-}\dfrac{\boldsymbol{M}_x}{\boldsymbol{F}_z}
\end{cases}
$$

## 最终指标

令默认状态下的对角足端距离为 $D_{\text{norm}}$，则总的 `zmp_margin` 定义为：

$$
m_{\text{zmp_margin}} =
\max \left(
0,
1 - \dfrac{\left\| (x_{\text{zmp}}, y_{\text{zmp}}) \right\|_2}{D_{\text{norm}}}
\right)
$$
