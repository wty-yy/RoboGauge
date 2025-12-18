"""
python robogauge/utils/radar_plot.py \
    /home/xfy/Coding/robot_gauge/logs/go2_moe_flat_debug_multi/20251218-22-49-29_run_multi/aggregated_results.yaml \
    /home/xfy/Coding/robot_gauge/logs/go2_flat_debug_multi/20251218-22-59-04_run_multi/aggregated_results.yaml \
    --out logs/go2_flat_vs_moe_flat.png
"""
import matplotlib.pyplot as plt
config = {
    "font.family": 'serif', # 衬线字体
    "figure.figsize": (6, 6),  # 图像大小
    "font.size": 14, # 字号大小
    "mathtext.fontset": 'cm', # 渲染数学公式字体
    'axes.unicode_minus': False # 显示负号
}
plt.rcParams.update(config)

import numpy as np
import yaml
import argparse
import os
import sys

# 设置字体，尝试匹配参考图的衬线体风格 (如果系统没有会回退到默认)
plt.rcParams['font.family'] = 'serif' 
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'serif']

def parse_value_string(val_str):
    if isinstance(val_str, (int, float)):
        return float(val_str)
    if isinstance(val_str, str):
        if '±' in val_str:
            return float(val_str.split('±')[0].strip())
        return float(val_str)
    return 0.0

def load_data(file_paths):
    all_data = []
    
    # 指标键名
    metric_keys = [
        'lin_vel_err', 
        'ang_vel_err', 
        'orientation_stability', 
        'dof_limits', 
        'torque_smoothness', 
        'dof_power'
    ]
    
    # 标签 (增加换行以避免拥挤)
    labels_map = {
        'lin_vel_err': 'Lin Vel\nAccuracy',
        'ang_vel_err': 'Ang Vel\nAccuracy',
        'dof_limits': 'Joint Limits\nMargin',
        'dof_power': 'Energy\nEfficiency',
        'orientation_stability': 'Orientation\nStability',
        'torque_smoothness': 'Torque\nSmoothness',
    }

    for path in file_paths:
        if not os.path.exists(path):
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
            
        raw_path = content.get('model_path', 'Unknown_Model')
        # 简化图例名称：只取文件名，去掉 .pt
        model_name = os.path.basename(raw_path).replace('.pt', '')
        
        # 如果名称过长，可以考虑进一步截断，例如：
        # if len(model_name) > 20: model_name = model_name[:10] + "..." + model_name[-5:]

        values = []
        for k in metric_keys:
            if k in content:
                raw_val = content[k]['mean']
                values.append(parse_value_string(raw_val))
            else:
                values.append(0.0)
        
        all_data.append({'name': model_name, 'values': values})
        
    return all_data, [labels_map[k] for k in metric_keys]

def plot_radar(data_list, labels, output_file=None):
    if not data_list:
        print("No data to plot.")
        return

    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1] # 闭合
    
    # --- 颜色设置 ---
    # 使用参考图类似的配色 (深蓝、浅蓝、绿等)
    # 或者使用 'tab10', 'Set2' 等
    colors = plt.cm.get_cmap("tab10", len(data_list))
    
    # 创建画布，稍微宽一点以便放图例
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
    
    # --- 核心修改：调整布局 ---
    # left=0.1, bottom=0.1, top=0.9 是为了给标题留空
    # right=0.75 是关键！这意味着图表只占画布左边 75% 的宽度，右边 25% 留给图例
    plt.subplots_adjust(left=0.05, right=0.75, top=0.9, bottom=0.1)

    # 设置方向
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    # --- 绘制标签 ---
    plt.xticks(angles[:-1], labels, color='#444444', size=13)
    
    # 标签对齐优化
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        if angle in (0, np.pi):
            label.set_horizontalalignment('center')
        elif 0 < angle < np.pi:
            label.set_horizontalalignment('left')
        else:
            label.set_horizontalalignment('right')

    # --- 绘制刻度 ---
    ax.set_rlabel_position(0)
    # 字体稍微调淡一点，不要抢眼
    plt.yticks([0.25, 0.50, 0.75, 1.00], ["0.25", "0.50", "0.75", "1.00"], 
               color="grey", size=10)
    plt.ylim(0, 1.05)
    
    # 网格线：点状虚线，稍微粗一点
    ax.grid(True, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
    ax.spines['polar'].set_visible(False)

    # --- 绘制数据 ---
    # 加粗线条以匹配 bsuite 风格
    linewidth = 3.0 
    
    for idx, item in enumerate(data_list):
        values = item['values']
        name = item['name']
        values_closed = values + values[:1]
        
        color = colors(idx)
        
        ax.plot(angles, values_closed, linewidth=linewidth, linestyle='-', label=name, color=color)
        ax.fill(angles, values_closed, color=color, alpha=0.2) # 填充透明度低一点

    # --- 核心修改：图例位置 ---
    # bbox_to_anchor=(1.1, 0.2) 的意思是：
    # 锚点位于坐标轴右侧(1.1倍宽位置)，垂直方向在底部(0.2倍高位置)
    # loc='upper left' 意思是图例的左上角对齐这个锚点
    legend = plt.legend(
        loc='upper left', 
        bbox_to_anchor=(1.1, 0.3),  # 调整这里的 0.3 可以上下移动图例
        title="Models", 
        title_fontsize=16,
        fontsize=12,
        frameon=False, # 无边框
        labelspacing=0.8 # 图例行间距
    )
    
    # 设置图例标题对齐方式 (左对齐)
    legend._legend_box.align = "left"

    plt.title('Multi-Model Performance Comparison', size=18, y=1.08, color='#333333')
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight') # bbox_inches='tight' 会自动裁剪白边
        print(f"Plot saved to {output_file}")
    else:
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files', metavar='F', type=str, nargs='+', help='YAML files')
    parser.add_argument('--out', type=str, default=None, help='Output file')
    
    # 调试用（如果你直接运行脚本，请取消注释并填入你的文件名）
    # sys.argv = ['plot.py', 'aggregated_results.yaml', 'aggregated_results2.yaml', '--out', 'fixed_radar.png']

    args = parser.parse_args()
    data, metrics_labels = load_data(args.files)
    plot_radar(data, metrics_labels, output_file=args.out)
