import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import os
import glob

# ================= 配置区域 =================
data_root = "/root/Coding/RoboGauge/logs_latent"

# 地形列表 (我们需要遍历所有地形来收集同一个指令的数据)
terrains = ['flat', 'wave', 'slope_fd', 'slope_bd', 'stairs_fd', 'stairs_bd', 'obstacle']

# 指令 ID 与含义的映射 (根据你的描述)
command_map = {
    0: "Pos X",
    1: "Neg X",
    2: "Pos Y",
    3: "Neg Y",
    4: "Pos Yaw",
    5: "Neg Yaw"
}

# 颜色映射 (为6种指令分配不同颜色)
cmd_colors = {
    0: '#d62728',  # 红
    1: '#1f77b4',  # 蓝
    2: '#2ca02c',  # 绿
    3: '#ff7f0e',  # 橙
    4: '#9467bd',  # 紫
    5: '#8c564b'   # 棕
}

# 每种指令最大保留样本数
# 因为我们要把7个地形的数据合起来，数据量会很大，必须采样
# 建议 1000 - 2000，太少看不出分布，太多会糊成一团
MAX_SAMPLES_PER_CMD = 3000 

# ================= 功能函数 =================

def load_combined_command_data(root_path, terrain_list, cmd_id):
    """
    遍历所有地形文件夹，寻找指定 cmd_id 的 npz 文件，并将它们全部合并
    """
    cmd_latents = []
    
    filename = f"moe_info_{cmd_id}.npz"
    
    for t_name in terrain_list:
        # 搜索路径: /root/.../go2_moe_{terrain}_latent/*/moe_info_{id}.npz
        search_pattern = os.path.join(root_path, f"go2_moe_{t_name}_latent", "*", filename)
        files = glob.glob(search_pattern)
        
        for f in files:
            try:
                data = np.load(f)
                if 'latent' in data:
                    cmd_latents.append(data['latent'])
            except:
                pass

    if not cmd_latents:
        return None
        
    # 合并该指令下所有地形的数据
    combined = np.concatenate(cmd_latents, axis=0)
    
    return combined

# ================= 主程序 =================

print(f"Start processing. Grouping by COMMAND (0-5)...")

# 1. 数据收集与预处理
all_data = []    # 存放 latent 向量
all_labels = []  # 存放对应的指令 ID (0, 1, 2...)

for cmd_id, cmd_name in command_map.items():
    print(f"  - Loading data for Command {cmd_id}: {cmd_name} ...", end=" ")
    
    # 获取该指令在所有地形下的数据汇总
    raw_data = load_combined_command_data(data_root, terrains, cmd_id)
    
    if raw_data is not None:
        # 随机下采样 (防止数据量过大)
        n_total = len(raw_data)
        if n_total > MAX_SAMPLES_PER_CMD:
            indices = np.random.choice(n_total, MAX_SAMPLES_PER_CMD, replace=False)
            data_sample = raw_data[indices]
        else:
            data_sample = raw_data
            
        all_data.append(data_sample)
        # 记录标签：有多少个数据，就存多少个 label
        all_labels.extend([cmd_id] * len(data_sample))
        print(f"Got {len(data_sample)} samples (from {n_total})")
    else:
        print("No data found!")

if not all_data:
    print("Error: No data loaded.")
    exit()

# 将列表转换为大矩阵
X = np.concatenate(all_data, axis=0)
y = np.array(all_labels)

# 2. PCA 降维
print(f"Running PCA on total {X.shape[0]} samples...")
pca = PCA(n_components=2)
X_2d = pca.fit_transform(X)

# 3. 可视化绘制
plt.figure(figsize=(10, 8), dpi=120)

# 遍历 0-5 进行绘制
for cmd_id in command_map.keys():
    # 提取属于当前指令的 2D 点
    indices = (y == cmd_id)
    points = X_2d[indices]
    
    if len(points) > 0:
        plt.scatter(
            points[:, 0], 
            points[:, 1], 
            c=cmd_colors[cmd_id], 
            label=command_map[cmd_id], 
            alpha=0.6,  # 透明度
            s=15        # 点大小
        )

plt.title("PCA of Latent Space grouped by Control Command (All Terrains Mixed)")
plt.xlabel("PC 1")
plt.ylabel("PC 2")
plt.legend(title="Control Commands", markerscale=1.5)
plt.grid(True, linestyle='--', alpha=0.4)

save_path = 'latent_pca_by_command_mixed.png'
plt.savefig(save_path)
print(f"Done! Visualization saved to {save_path}")
plt.show()