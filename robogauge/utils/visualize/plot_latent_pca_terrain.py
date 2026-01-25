# -*- coding: utf-8 -*-
'''
@File    : plot_latent_pca_terrain.py
@Time    : 2026/01/22 23:31:55
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : PCA Visualization of Latent Space Grouped by Terrain for Command 0 (Forward)
'''
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import os
import glob
from pathlib import Path

# ================= 配置区域 =================
data_root = "/root/Coding/RoboGauge/logs_latent/rem"
# data_root = "/root/Coding/RoboGauge/logs_latent/cts"
# data_root = "/root/Coding/RoboGauge/logs_latent/moe"
# data_root = "/root/Coding/RoboGauge/logs_latent/rem_0.6357"
# data_root = "/root/Coding/RoboGauge/logs_latent/moe_0.6637"

# 地形列表
# terrains = ['flat', 'wave', 'slope_fd', 'slope_bd', 'stairs_fd', 'stairs_bd', 'obstacle']
terrains = ['flat', 'wave', 'stairs_fd', 'obstacle']

# 我们只关注 指令 0 (Pos X)
TARGET_CMD_ID = 0 
TARGET_CMD_NAME = "Pos X"

# 每个地形最大采样数 (防止绘图过慢或重叠严重)
MAX_SAMPLES_PER_TERRAIN = 3000

# 地形颜色映射 (使用 matplotlib 的 tab10 色板，确保区分度)
# 为每个地形分配一个固定颜色
terrain_colors = {
    'flat': '#1f77b4',      # 蓝
    'wave': '#ff7f0e',      # 橙
    'slope_fd': '#2ca02c',  # 绿
    'slope_bd': '#d62728',  # 红
    'stairs_fd': '#9467bd', # 紫
    'stairs_bd': '#8c564b', # 棕
    'obstacle': '#e377c2'   # 粉
}

# ================= 数据加载函数 =================

def load_cmd0_data_by_terrain(root_path, terrain_list, cmd_id):
    """
    加载指定 cmd_id 的数据，并按地形分类返回。
    返回结构: { 'flat': np.array((N, dim)), 'wave': ... }
    """
    data_dict = {}
    
    filename = f"moe_info_{cmd_id}.npz"
    print(f"[*] Loading data for Command {cmd_id} ({TARGET_CMD_NAME})...")

    for t_name in terrain_list:
        # 构建搜索路径: root/go2_moe_{terrain}_latent/*/moe_info_{id}.npz
        # 注意：中间有个 "*" 匹配时间戳文件夹
        search_pattern = os.path.join(root_path, f"go2_moe_{t_name}_latent", "*", filename)
        files = glob.glob(search_pattern)
        
        terrain_vectors = []
        
        for f in files:
            try:
                raw = np.load(f)
                if 'latent' in raw:
                    vec = raw['latent']
                    # 确保是二维数组 (N, D)
                    if len(vec.shape) == 1:
                        vec = vec.reshape(1, -1)
                    terrain_vectors.append(vec)
            except Exception as e:
                print(f"Error loading {f}: {e}")

        if terrain_vectors:
            # 合并该地形下所有文件的向量
            full_data = np.vstack(terrain_vectors)
            
            # --- 采样处理 ---
            n_samples = full_data.shape[0]
            if n_samples > MAX_SAMPLES_PER_TERRAIN:
                # 随机采样索引
                indices = np.random.choice(n_samples, MAX_SAMPLES_PER_TERRAIN, replace=False)
                full_data = full_data[indices]
            
            data_dict[t_name] = full_data
            print(f"    -> Terrain '{t_name}': Loaded {full_data.shape[0]} samples (Original: {n_samples})")
        else:
            print(f"    -> Terrain '{t_name}': No data found.")
            
    return data_dict

# ================= 主程序 =================

# 1. 加载数据
terrain_data = load_cmd0_data_by_terrain(data_root, terrains, TARGET_CMD_ID)

if not terrain_data:
    print("Error: No data loaded. Please check the path.")
    exit()

# 2. 准备 PCA 数据
#我们需要将所有数据堆叠在一起进行 PCA fit，以便它们处于同一个坐标系中
all_vectors = []
all_labels = [] # 用于记录每一行数据属于哪个地形

for t_name, vectors in terrain_data.items():
    all_vectors.append(vectors)
    # 记录对应的标签，长度与 vectors 的行数相同
    all_labels.extend([t_name] * vectors.shape[0])

X = np.vstack(all_vectors)
print(f"[*] Starting PCA on matrix shape: {X.shape} ...")

# 3. 执行 PCA 降维
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X)

# 计算解释方差比 (Explained Variance Ratio)
evr = pca.explained_variance_ratio_
print(f"[*] PCA Done. Explained Variance: PC1={evr[0]:.2%}, PC2={evr[1]:.2%}")

# 4. 绘图
plt.figure(figsize=(10, 8), dpi=100)

# 当前绘图的起止索引
start_idx = 0

for t_name in terrains:
    if t_name not in terrain_data:
        continue
        
    count = terrain_data[t_name].shape[0]
    end_idx = start_idx + count
    
    # 提取该地形对应的 PCA 坐标
    # X_pca 的行顺序与我们构建 all_vectors 的顺序一致
    subset = X_pca[start_idx:end_idx]
    
    plt.scatter(
        subset[:, 0], 
        subset[:, 1], 
        s=20, # 点的大小
        alpha=0.6, # 透明度，防止重叠完全遮挡
        c=terrain_colors.get(t_name, 'gray'), 
        label=t_name
    )
    
    start_idx = end_idx

plt.title(f'PCA of Latent Space - Command {TARGET_CMD_ID}: {TARGET_CMD_NAME}\n(Colored by Terrain)', fontsize=14)
plt.xlabel(f'Principal Component 1 ({evr[0]:.2%} variance)', fontsize=12)
plt.ylabel(f'Principal Component 2 ({evr[1]:.2%} variance)', fontsize=12)
plt.legend(title="Terrain", loc='best')
plt.grid(True, linestyle='--', alpha=0.3)

# 保存图片
save_path = Path(data_root) / "pca_terrain_cmd0.png"
plt.savefig(save_path)
print(f"[*] Plot saved to {save_path}")
plt.show()
