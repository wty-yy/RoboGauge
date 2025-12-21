# Single Run
```bash
python robogauge/scripts/run.py \
    --task go2_moe_flat \
    --experiment-name debug \
    --headless
```

# Multi Run
```bash
python robogauge/scripts/run.py \
    --task go2_moe_flat \
    --experiment-name debug \
    --multi \
    --num-processes 3 \
    --headless

python robogauge/scripts/run.py \
    --task go2_moe_flat \
    --experiment-name debug \
    --multi \
    --num-processes 3 \
    --headless
```

# Radar/Bar Plot
将Multi Run结果绘制在雷达图中
```bash
# 可选--out保存到图片
python robogauge/utils/visualize_results.py \
    aggregated_results_1.yaml \
    aggregated_results_2.yaml \
    --out logs/1.jpg

# 绘制下全部 *.yaml, 可选range控制radar, bar y轴显示范围
python robogauge/utils/visualize_results.py \
    /home/xfy/Coding/robot_gauge/mytest/results \
    --range 0.35 1.0 \
    --out logs/1.jpg
```