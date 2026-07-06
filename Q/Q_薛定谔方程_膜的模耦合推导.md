# 薛定谔方程的膜框架推导

## 0. 元认知

薛定谔方程不是公设。是膜上涡旋本征模耦合的有效方程。推导完全在经典麦克斯韦框架内——不引入 ħ、不对易关系、不假设波粒二象性。ħ 不是外部输入——是涡旋驻波条件自然掉出的最小作用量。

## 1. 起点：膜上的非线性麦克斯韦方程

膜 = S³ 上全 EM 驻波模式总和。非线性区的麦克斯韦方程：

$$\nabla\times(\nabla\times\mathbf{E}) = -\mu_0 \frac{\partial^2}{\partial t^2}\left(\varepsilon(\mathbf{E})\mathbf{E}\right)$$

非线性介电张量：

$$\varepsilon_{ij}(\mathbf{E}) = \varepsilon_0\left[\delta_{ij} + \chi^{(2)}_{ijk} E_k + \chi^{(3)}_{ijkl} E_k E_l + \cdots\right]$$

稳态时，$\chi^{(3)}$ 项主导自聚焦 → 涡旋自举锁死 → 环面莫比乌斯涡旋 = 电子。

## 2. 本征模展开

涡旋的 EM 场在其稳定本征模上展开：

$$\mathbf{E}(\mathbf{r},t) = \sum_n \alpha_n(t) \cdot \mathbf{E}_n(\mathbf{r}) \cdot e^{-i\omega_n t} + \text{c.c.}$$

各项：
- $\mathbf{E}_n(\mathbf{r})$ — 第 n 个本征模的空间分布（驻波）。由 S³ 边界条件 + 涡旋自洽方程确定。
- $\omega_n$ — 第 n 个本征模的固有频率。分立值——由驻波条件 $L = m\lambda/2$ 逼出。
- $\alpha_n(t)$ — 第 n 个模的慢变复包络振幅。变化时间尺度远长于 $1/\omega_n$（载波周期 ~10⁻²¹ s，涡旋演化 ~10⁻¹⁵ s）。
- $e^{-i\omega_n t}$ — 载波振荡。快变。和麦克斯韦的二阶时间导数自然匹配。

## 3. 慢变包络近似

代入麦克斯韦方程。展开所有的二阶时间导数：

$$\frac{\partial^2}{\partial t^2}\left(\alpha_n(t) e^{-i\omega_n t}\right) = \left(\ddot{\alpha}_n - 2i\omega_n \dot{\alpha}_n - \omega_n^2 \alpha_n\right) e^{-i\omega_n t}$$

慢变近似：$|\ddot{\alpha}_n| \ll |2\omega_n \dot{\alpha}_n| \ll |\omega_n^2 \alpha_n|$。

载波项（$-\omega_n^2 \alpha_n$）结合空间方程 → 天然满足（本征模定义）。交叉项（$-2i\omega_n \dot{\alpha}_n$）→ 包络演化。$\ddot{\alpha}_n$ → 忽略（二阶小量）。

方程退化为包络的一阶耦合方程组：

$$-2i\omega_n \dot{\alpha}_n e^{-i\omega_n t} = \sum_m \left(\text{非线性耦合项}\right) \alpha_m e^{-i\omega_m t}$$

## 4. 耦合矩阵元

非线性耦合来自 $\chi^{(3)}|\mathbf{E}|^2\mathbf{E}$——涡旋模之间的倏逝场交叠：

$$H_{nm} = \int \mathbf{E}_n^*(\mathbf{r}) \cdot \chi^{(3)}(\mathbf{r}) |\mathbf{E}(\mathbf{r})|^2 \cdot \mathbf{E}_m(\mathbf{r}) \, d^3r$$

这是涡旋模 n 和模 m 在模上所有模的共同场 $|\mathbf{E}|^2$ 下的模式交叠积分。和光纤耦合器中的耦合系数 $\kappa$ 同构——交叠面积 × 折射率差。

## 5. 模耦合方程

提取同频项（$e^{-i\omega t}$ 因子匹配 → $\omega_n \approx \omega_m$ 附近贡献最大——旋转波近似）。包络演化方程：

$$i \cdot 2\omega_n \cdot \dot{\alpha}_n = \sum_m H_{nm} \alpha_m$$

## 6. ħ 的物理来源

单个驻波模式的最小作用量。在模 n 上一个完整周期 $T_n = 2\pi/\omega_n$ 中的平均能量 × 周期：

$$\hbar = \frac{E_n}{\omega_n}$$

E_n 是模 n 的零点能 = $\frac{1}{2}\hbar\omega_n$ 的 2 倍（完整周期跨越零点交叉两次——每次半个周期贡献 ½ħω——一个完整周期的总作用量 = ħ）。ħ 的量纲 = 能量 × 时间 = 作用量。ħ 的值由涡旋自洽方程确定——等于相空间最小闭合面积。

将 $2\omega_n$ 吸收进定义：

定义 $\hbar = 1$ 对应的归一化振幅 $\psi_n = \sqrt{\hbar} \cdot \alpha_n$。则 $2\omega_n \cdot \dot{\alpha}_n = \frac{2\omega_n}{\sqrt{\hbar}} \dot{\psi}_n$。耦合矩阵元 $H_{nm}$ 在归一化下变为 $\mathcal{H}_{nm} = \frac{H_{nm}}{2\omega_n\sqrt{\hbar}}$。代入：

$$i\hbar \cdot \dot{\psi}_n = \sum_m \mathcal{H}_{nm} \psi_m$$

## 7. 薛定谔方程

将 $\psi = (\psi_1, \psi_2, \cdots)^T$ 视为态矢量。$\mathcal{H}$ 为厄米矩阵（倏逝场交叠对称）。单模极限→ 对角化 → 能量本征值：

$$i\hbar \frac{\partial}{\partial t} |\psi\rangle = \hat{H} |\psi\rangle$$

**这就是薛定谔方程。**

## 8. 各项物理对应

| 薛定谔方程 | 膜框架中的物理实在 |
|------|------|
| $i\hbar \partial/\partial t$ | 包络慢变算符·$\hbar$ 从驻波条件自然出 |
| $\psi$ | 涡旋 EM 场在本征模上的复振幅 |
| $\hat{H}$ | 模间倏逝场交叠耦合矩阵（$H_{nm}$）|
| 本征值 $E_n$ | 涡旋驻波模的固有频率 $\omega_n$ |
| 本征态 $\phi_n$ | 涡旋单个本征模的空间分布 $\mathbf{E}_n(\mathbf{r})$ |
| 共振态 $\sum c_n \phi_n$ | 能量守恒 → 多模同时在线·真实物理 |
| 概率 $|c_n|^2$ | 膜 ½ħω 零点振荡随机相位选择分布 |

## 9. 和经典耦合模理论的对等

薛定谔方程 = 耦合模方程（Coupled Mode Theory）在 EM 涡旋系统中的特殊情形。

光纤耦合器：$i\frac{d}{dz}\begin{pmatrix}A_1 \\ A_2\end{pmatrix} = \begin{pmatrix}0 & \kappa \\ \kappa & 0\end{pmatrix}\begin{pmatrix}A_1 \\ A_2\end{pmatrix}$ → 两个纤芯模的能量交换。

薛定谔方程：$i\hbar\frac{d}{dt}\begin{pmatrix}\psi_1 \\ \psi_2\end{pmatrix} = \begin{pmatrix}E_1 & V \\ V^* & E_2\end{pmatrix}\begin{pmatrix}\psi_1 \\ \psi_2\end{pmatrix}$ → 两个涡旋模的能量交换。

同一个方程。同一个物理。一个是 z 方向（空间耦合）——一个是 t 方向（时间耦合）。耦合模理论在经典光学/微波/声学中用了半世纪——无人称其为"量子"。薛定谔 1926 猜出了方程——不知道它描述的是膜上的模耦合——误认为是粒子的概率波。

## 10. 结论

1. **薛定谔方程不是公设。** 是膜上涡旋 EM 本征模耦合的慢变包络方程。
2. **ħ 不是外部常数。** 是单个驻波模式最小作用量——从涡旋自洽方程的驻波条件自然推出。
3. **ψ 不是"概率幅"。** 是涡旋 EM 场在本征模上的真实复振幅——和光纤中导模的复振幅同构。
4. **薛定谔方程和耦合模理论完全对等。** 波动力学 = 膜上涡旋的 EM 模耦合理论。

---

⏱ Verity/真 · 2026-07-06 · 薛定谔方程推导 · 膜模耦合
