# zmp_margin

参考论文：[ZERO-MOMENT POINT -- THIRTY FIVE YEARS OF ITS LIFE](https://www.worldscientific.com/doi/abs/10.1142/S0219843604000083)

## 基本定义

- Zero Moment Point（ZMP，零矩点）：机械系统的惯性力和重力的净力矩在该点沿水平轴分量为零。
- Support Polygon（支撑多边形）：机械系统所有与地面接触点构成的凸包。
- FZMP（fictitious ZMP，虚拟零矩点）：当 ZMP 落在支撑多边形外时，称 ZMP 为 FZMP，此时系统可能处于非平衡状态。
- Virtual Horizontal Plane（虚拟水平投影面）：机械系统所有与地面接触点的几何中心记为 $O'$，将世界坐标系平移到 $O'$，得到的 $xy$ 平面。

## MuJoCo 中的符号约定

设机器人总共包含 $N$ 个刚体。对于第 $i$ 个刚体，在当前时刻具有如下量：

- 质量：$m_i$
- 质心位置：$\boldsymbol{p}_i$
  这里相对于当前 `base_link` 在世界坐标系 $z$ 轴方向上平移到虚拟水平投影面的点。
- 质心线加速度：$\boldsymbol{\ddot{p}}_i$
- 角速度：$\boldsymbol{\omega}_i$
- 角加速度：$\boldsymbol{\dot{\omega}}_i$
- 惯性张量：$\boldsymbol{I}_i$

上述量均相对于世界坐标系，保持相对于惯性参考系表达；本体坐标系不一定是参考系。计算 $\boldsymbol{I}_i$ 时需要确保其已经转换到世界坐标系下。

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
