# -*- coding: utf-8 -*-
'''
@File    : plot_terrain_levels.py
@Time    : 2025/12/27 23:04:01
@Author  : wty-yy, Gemini3 Pro
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : None
@Desc    : 可视化不同地形下随着摩擦力变化的关卡通过等级 (Terrain Level vs Friction)
'''
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import yaml
import argparse
import os
import re

# --- 配置 Matplotlib 样式 ---
config = {
    "font.family": 'serif',
    "figure.figsize": (18, 10),
    "font.size": 12,
    "mathtext.fontset": 'cm',
    'axes.unicode_minus': False
}
plt.rcParams.update(config)
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'serif']

def load_terrain_data(file_paths):
    """
    加载数据并按模型、地形、摩擦力组织
    Returns:
        model_data: {model_name: {terrain_type: {friction: level}}}
    """
    target_terrains = ['wave', 'slope_fd', 'slope_bd', 'stairs_fd', 'stairs_bd', 'obstacle']
    model_data = {}
    
    # 用于从键名中提取 friction 的正则 (例如 friction1.25)
    friction_pattern = re.compile(r'friction([\d\.]+)')

    for path in file_paths:
        if not os.path.exists(path):
            print(f"[ERROR] File not found: {path}")
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        # 获取模型名称
        raw_path = content.get('model_path', 'Unknown_Model')
        model_name = os.path.basename(raw_path).replace('.pt', '')
        
        if model_name not in model_data:
            model_data[model_name] = {t: {} for t in target_terrains}
            
        # 遍历YAML中的每个测试条目
        for key, value in content.items():
            if key in ['model_path', 'summary']:
                continue
            
            # 1. 检查地形是否在目标列表中
            t_name = value.get('terrain_name')
            if t_name not in target_terrains:
                continue
            
            # 2. 从 key 中提取摩擦力
            match = friction_pattern.search(key)
            if not match:
                continue
            friction = float(match.group(1))
            
            # 3. 获取地形等级 (取该条件下该地形的最大值，防止重复)
            level = value.get('terrain_level', 0)
            
            # 记录数据
            current_max = model_data[model_name][t_name].get(friction, -1)
            if level > current_max:
                model_data[model_name][t_name][friction] = level
                
    return model_data, target_terrains

def plot_results(model_data, terrain_labels, output_file=None):
    """绘制 2x3 的子图"""
    if not model_data:
        print("No data to plot.")
        return

    # 设置 2行3列 的布局
    fig, axes = plt.subplots(2, 3, figsize=(18, 10), sharex=True, sharey=True)
    axes = axes.flatten()
    
    # 自动获取颜色映射
    colors = plt.cm.get_cmap("tab10", len(model_data))
    
    # 遍历前5个地形进行绘图
    for i, t_name in enumerate(terrain_labels):
        ax = axes[i]
        
        for idx, (model_name, terrains) in enumerate(model_data.items()):
            data_points = terrains.get(t_name, {})
            if not data_points:
                continue
            
            # 排序 (Friction, Level)
            sorted_points = sorted(data_points.items())
            xs, ys = zip(*sorted_points)
            
            ax.plot(xs, ys, marker='o', linestyle='-', linewidth=2, 
                    label=model_name, color=colors(idx), alpha=0.8)
        
        ax.set_title(t_name.replace('_', ' ').title(), fontsize=14)
        ax.grid(True, linestyle='--', alpha=0.6)

    # --- 第6张图：绘制平均值 (Average) ---
    ax_avg = axes[5]
    for idx, (model_name, terrains) in enumerate(model_data.items()):
        # 聚合该模型下所有地形的数据用于计算平均值
        # 结构: friction -> [level_slope, level_wave, ...]
        friction_agg = {}
        for t_name in terrain_labels:
            for f, l in terrains[t_name].items():
                if f not in friction_agg:
                    friction_agg[f] = []
                friction_agg[f].append(l)
        
        if not friction_agg:
            continue
            
        # 计算平均值并排序
        sorted_frictions = sorted(friction_agg.keys())
        avg_levels = [np.mean(friction_agg[f]) for f in sorted_frictions]
        
        ax_avg.plot(sorted_frictions, avg_levels, marker='s', linestyle='-', linewidth=2,
                    label=model_name, color=colors(idx), alpha=0.8)

    ax_avg.set_title('Average Performance', fontsize=14)
    ax_avg.grid(True, linestyle='--', alpha=0.6)
    
    # 仅在最后一张图显示图例，避免遮挡
    ax_avg.legend(loc='best', frameon=False, title="Models")

    # 最下面一行设置 X 轴标签
    for i in [3, 4, 5]:
        axes[i].set_xlabel('Friction ($\mu$)')

    # 最左边一列设置 Y 轴标签
    for i in [0, 3]:
        axes[i].set_ylabel('Terrain Level')

    plt.tight_layout()
    # 稍微调整间距防止标签重叠
    # plt.subplots_adjust(wspace=0.1, hspace=0.15)
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    else:
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot terrain level vs friction curves.")
    parser.add_argument('files', metavar='F', type=str, nargs='+', help='YAML result files')
    parser.add_argument('--out', type=str, default='terrain_analysis.jpg', help='Output image filename')
    args = parser.parse_args()
    
    data, labels = load_terrain_data(args.files)
    plot_results(data, labels, output_file=args.out)