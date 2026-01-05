import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import os
import glob
import pandas as pd
from sklearn.metrics import silhouette_score, silhouette_samples, calinski_harabasz_score

# ================= 配置区域 =================
data_root = "/root/Coding/RoboGauge/logs_latent/moe"
terrains = ['flat', 'wave', 'slope_fd', 'slope_bd', 'stairs_fd', 'stairs_bd', 'obstacle']

command_map = {
    0: "Pos X (Forward)",
    1: "Neg X (Backward)",
    2: "Pos Y (Left)",
    3: "Neg Y (Right)",
    4: "Pos Yaw (Turn Left)",
    5: "Neg Yaw (Turn Right)"
}

cmd_colors = {
    0: '#d62728', 1: '#1f77b4', 2: '#2ca02c',
    3: '#ff7f0e', 4: '#9467bd', 5: '#8c564b'
}

# t-SNE 计算较慢，且点太多会严重重叠
# 建议每种指令采样 800 - 1000 个点即可，足以看清分布
MAX_SAMPLES_PER_CMD = 2000 

# t-SNE 参数
# perplexity: 困惑度，通常在 5-50 之间。越大越关注全局结构，越小越关注局部邻居。
TSNE_PERPLEXITY = 30
TSNE_ITER = 1000

# ================= 功能函数 =================

# key = 'weights' # 'latent'
key = 'latent'

def load_combined_command_data(root_path, terrain_list, cmd_id):
    """读取指定指令在所有地形下的数据并合并"""
    cmd_latents = []
    filename = f"moe_info_{cmd_id}.npz"
    
    for t_name in terrain_list:
        search_pattern = os.path.join(root_path, f"go2_moe_{t_name}_latent", "*", filename)
        files = glob.glob(search_pattern)
        for f in files:
            try:
                data = np.load(f)
                if key in data:
                    cmd_latents.append(data[key])
            except: pass

    if not cmd_latents: return None
    return np.concatenate(cmd_latents, axis=0)

# ================= 主程序 =================

print(f"Start processing t-SNE visualization...")

all_data = []    
all_labels = []  

# 1. 数据收集
for cmd_id, cmd_name in command_map.items():
    raw_data = load_combined_command_data(data_root, terrains, cmd_id)
    
    if raw_data is not None:
        # 随机下采样
        n_total = len(raw_data)
        if n_total > MAX_SAMPLES_PER_CMD:
            indices = np.random.choice(n_total, MAX_SAMPLES_PER_CMD, replace=False)
            data_sample = raw_data[indices]
        else:
            data_sample = raw_data
            
        all_data.append(data_sample)
        all_labels.extend([cmd_id] * len(data_sample))
        print(f"  - Cmd {cmd_id}: {len(data_sample)} samples")

if not all_data:
    print("Error: No data loaded.")
    exit()

X = np.concatenate(all_data, axis=0)
y = np.array(all_labels)

print(f"Running t-SNE on {X.shape} matrix...")
print(f"  (Perplexity={TSNE_PERPLEXITY}, Iterations={TSNE_ITER})")
print("  This may take a moment...")

# 2. t-SNE 降维
# init='pca' 通常比 'random' 更稳定，能更好地保留全局结构
tsne = TSNE(
    n_components=2, 
    perplexity=TSNE_PERPLEXITY, 
    n_iter=TSNE_ITER, 
    init='pca', 
    learning_rate='auto',
    random_state=42,
    verbose=1,
)
X_embedded = tsne.fit_transform(X)

# 3. 可视化
plt.figure(figsize=(12, 10), dpi=120)

for cmd_id in command_map.keys():
    indices = (y == cmd_id)
    points = X_embedded[indices]
    
    if len(points) > 0:
        plt.scatter(
            points[:, 0], 
            points[:, 1], 
            c=cmd_colors[cmd_id], 
            label=command_map[cmd_id], 
            alpha=0.6, 
            s=20 #稍微大一点的点
        )

plt.title(f"t-SNE Visualization of {key.capitalize()} Space by Command\n(Perplexity={TSNE_PERPLEXITY}, Mixed Terrains)")
# t-SNE 的坐标轴没有物理意义，所以隐藏刻度通常更好看
plt.xticks([])
plt.yticks([])
plt.legend(title="Control Commands", markerscale=2, bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

save_path = os.path.join(data_root, f'{key}_tsne_by_command.png')
plt.savefig(save_path)
print(f"Done! Visualization saved to {save_path}")
plt.show()

def evaluate_latent_space(X, y, command_map):
    """
    X: (N, D) 原始高维 Latent 向量 (例如 32维)
    y: (N,) 对应的指令标签 (0-5)
    command_map: label到名称的映射字典
    """
    print(f"--- Evaluating Latent Space (Samples: {X.shape[0]}, Dim: {X.shape[1]}) ---")
    
    # 1. 全局指标 (Global Metrics)
    # 轮廓系数 (Silhouette): 越接近 1 越好
    global_sil = silhouette_score(X, y)
    # Calinski-Harabasz Index (CHI): 数值越大越好 (表示类间离散度高，类内离散度低)
    global_chi = calinski_harabasz_score(X, y)
    
    print(f"Global Silhouette Score: {global_sil:.4f} (范围 -1 到 1, 越大越好)")
    print(f"Global Calinski-Harabasz: {global_chi:.1f} (数值越大越好)")
    print("-" * 30)

    # 2. 逐类指标 (Per-Class Metrics)
    # 计算每个样本的轮廓系数
    sample_silhouette_values = silhouette_samples(X, y)
    
    class_scores = []
    
    for label in sorted(command_map.keys()):
        # 提取当前类的所有样本的轮廓系数
        ith_class_silhouette_values = sample_silhouette_values[y == label]
        
        # 计算该类的平均分
        avg_score = np.mean(ith_class_silhouette_values)
        
        # 计算该类的紧密度 (Intra-class distance) - 可选
        # 这里直接用轮廓系数代表聚集程度
        
        class_scores.append({
            "Command ID": label,
            "Command Name": command_map[label],
            "Silhouette Score": avg_score,
            "Sample Count": len(ith_class_silhouette_values)
        })
    
    # 转为 DataFrame 展示
    df = pd.DataFrame(class_scores)
    print(df.to_string(index=False))
    print("-" * 30 + "\n")
    
    return df, global_sil

# 1. 评估原始高维空间 (Intrinsic Quality)
print(">>> Evaluating Original High-Dim Latent Space Quality...")
df_original, score_original = evaluate_latent_space(X, y, command_map)
print(f"Original Space Score: {score_original:.4f}")

# 2. 评估 t-SNE 降维后的 2D 空间 (Visual Cluster Quality)
print("\n>>> Evaluating t-SNE Embedded Space Quality (2D)...")
# 直接传入 X_embedded 即可，evaluate_latent_space 函数对维度不敏感
df_tsne, score_tsne = evaluate_latent_space(X_embedded, y, command_map) 

# 保存 t-SNE 的评估结果
save_path_tsne = os.path.join(data_root, f'{key}_tsne_2d_evaluation.csv')
df_tsne.to_csv(save_path_tsne, index=False)
print(f"t-SNE 2D Evaluation results saved to {save_path_tsne}")
print(f"t-SNE Space Score: {score_tsne:.4f}")