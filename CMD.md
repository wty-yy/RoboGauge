# Single Pipeline
```bash
python robogauge/scripts/run.py \
    --task go2_moe_flat \
    --experiment-name debug \
    --headless
```

# Multi Pipeline
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

# Level Pipeline
```bash
python robogauge/scripts/run.py \
    --task go2_slope \
    --experiment-name debug \
    --seed 0 \
    --headless \
    --search-max-level --seeds 0 1 2 --frictions 1
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