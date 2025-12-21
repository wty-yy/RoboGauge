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

# Radar Plot
将Multi Run结果绘制在雷达图中
```bash
python robogauge/utils/radar_plot.py \
    aggregated_results_1.yaml \
    aggregated_results_2.yaml \
    --out logs/go2_flat_vs_moe_flat.png
```