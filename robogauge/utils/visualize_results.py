import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import yaml
import argparse
import os

# --- 配置 Matplotlib 样式 ---
config = {
    "font.family": 'serif',
    "figure.figsize": (8, 6),
    "font.size": 12,
    "mathtext.fontset": 'cm',
    'axes.unicode_minus': False
}
plt.rcParams.update(config)
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
    metric_keys = ['lin_vel_err', 'ang_vel_err', 'orientation_stability', 'dof_limits', 'torque_smoothness', 'dof_power']
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
            print(f"[ERROR] File not found: {path}")
            continue
        with open(path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        raw_path = content.get('model_path', 'Unknown_Model')
        model_name = os.path.basename(raw_path).replace('.pt', '')

        values = []
        for k in metric_keys:
            if k in content:
                raw_val = content[k]['mean@50']
                values.append(parse_value_string(raw_val))
            else:
                values.append(0.0)
        all_data.append({'name': model_name, 'values': values})
        
    return all_data, [labels_map[k] for k in metric_keys]

def plot_radar(data_list, labels, output_file=None, r_range=(0, 1.05)):
    """绘制雷达图"""
    if not data_list:
        return

    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]
    
    colors = plt.cm.get_cmap("tab10", len(data_list))
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
    plt.subplots_adjust(left=0.05, right=0.75, top=0.9, bottom=0.1)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    plt.xticks(angles[:-1], labels, color='#444444', size=11)
    
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        if angle in (0, np.pi): label.set_horizontalalignment('center')
        elif 0 < angle < np.pi: label.set_horizontalalignment('left')
        else: label.set_horizontalalignment('right')

    r_min, r_max = r_range
    ax.set_ylim(r_min, r_max)
    
    ticks = np.linspace(r_min, r_max, 5)
    plt.yticks(ticks, [f"{t:.2f}" for t in ticks], color="grey", size=10)
    
    ax.set_rlabel_position(180)
    ax.grid(True, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
    ax.spines['polar'].set_visible(False)

    linewidth = 2.5 
    for idx, item in enumerate(data_list):
        values_closed = item['values'] + [item['values'][0]]
        color = colors(idx)
        ax.plot(angles, values_closed, linewidth=linewidth, label=item['name'], color=color)
        ax.fill(angles, values_closed, color=color, alpha=0.15)

    plt.legend(loc='lower left', bbox_to_anchor=(0.82, 0.0), title="Models", frameon=False)
    plt.title('Performance Comparison (Radar)', size=16, y=1.06)
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Radar plot saved to {output_file}")

def plot_bar(data_list, labels, output_file=None, h_range=(0, 1.05)):
    """绘制柱状图"""
    if not data_list:
        return

    num_models = len(data_list)
    num_metrics = len(labels)
    
    # 设置柱状图参数
    x = np.arange(num_metrics)
    width = 0.8 / num_models  # 自动计算柱子宽度
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.get_cmap("tab10", num_models)
    
    for idx, item in enumerate(data_list):
        # 计算每个模型柱子的偏移量
        offset = (idx - (num_models - 1) / 2) * width
        ax.bar(x + offset, item['values'], width, label=item['name'], color=colors(idx), alpha=0.8)

    ax.set_ylabel('Score / Value')
    ax.set_title('Performance Comparison (Bar)', size=16)
    ax.set_xticks(x)
    # 将标签中的换行符去掉或处理，使其在柱状图中更美观
    clean_labels = [l.replace('\n', ' ') for l in labels]
    ax.set_xticklabels(clean_labels, rotation=15, ha='right')
    ax.legend(title="Models", bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    if h_range:
        ax.set_ylim(h_range)

    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Bar plot saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files_or_dir', metavar='F', type=str, nargs='+', help='YAML files or directory')
    parser.add_argument('--out', type=str, help='Base name for output files')
    parser.add_argument('--range', type=float, nargs=2, default=[0.0, 1.0], help='Axis range for radar and bar plots')
    args = parser.parse_args()
    
    # 获取文件列表
    files = args.files_or_dir
    if Path(args.files_or_dir[0]).is_dir():
        dir_path = Path(args.files_or_dir[0])
        files = [str(p) for p in dir_path.glob('*.yaml')]
    
    data, metrics_labels = load_data(files)

    # 处理输出文件名
    radar_out, bar_out = None, None
    if args.out:
        out_path = Path(args.out)
        radar_out = str(out_path.with_name(f"{out_path.stem}_radar{out_path.suffix}"))
        bar_out = str(out_path.with_name(f"{out_path.stem}_bar{out_path.suffix}"))

    # 分别调用绘图函数
    plot_radar(data, metrics_labels, output_file=radar_out, r_range=args.range)
    plot_bar(data, metrics_labels, output_file=bar_out, h_range=args.range)
    plt.show()
