# Single Pipeline
```bash
python robogauge/scripts/run.py \
    --task go2_moe.flat \
    --experiment-name debug \
    --headless
```

# Multi Pipeline
```bash
python robogauge/scripts/run.py \
    --task go2_moe.flat \
    --experiment-name debug \
    --multi \
    --num-processes 5 \
    --seeds 0 1 2 3 4 \
    --frictions 0.5 1.0 1.5 2.0 2.5 \
    --compress-logs \
    --headless

# Terrain with Level, need specify goals (default is target_pos)
python robogauge/scripts/run.py \
    --task go2_moe.slope \
    --experiment-name debug \
    --multi \
    --num-processes 5 \
    --seeds 0 1 2 3 4 \
    --frictions 1.0 \
    --level 3 \
    --goals max_velocity diagonal_velocity\
    --compress-logs \
    --headless
```

# Level Pipeline
```bash
# Must specify single frictions for LevelPipeline!
python robogauge/scripts/run.py \
    --task go2_moe.slope \
    --experiment-name debug \
    --search-max-level \
    --seeds 0 1 2 3 4 \
    --frictions 1.0 \
    --compress-logs \
    --headless
```

# Stress Pipeline
```bash
python robogauge/scripts/run.py \
    --task go2_moe \
    --experiment-name debug \
    --stress-benchmark \
    --stress-terrain-names flat slope stairs_up stairs_down wave \
    --stress-num-processes 2 \
    --num-processes 3 \
    --seeds 0 1 2 3 4 \
    --frictions 0.5 1.0 1.5 2.0 2.5 \
    --compress-logs \
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