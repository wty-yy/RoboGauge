# Single Pipeline
```bash
# Default goals: max_velocity, diagonal_velocity
python robogauge/scripts/run.py \
    --task go2_moe.flat \
    --experiment-name debug \
    --headless

# To evaluate metrics for level terrains, add `--goals` and `--spawn-type`
# level terrains: wave, slope_fb, slope_bd, stairs_fb, stairs_bd, obstacle (default is target_pos)
python robogauge/scripts/run.py \
    --task go2_moe.obstacle \
    --experiment-name debug \
    --level 10 \
    --friction 2 \
    --spawn-type level_eval \
    --goals max_velocity diagonal_velocity
```

# Multi Pipeline
```bash
python robogauge/scripts/run.py \
    --task go2_moe.flat \
    --experiment-name debug \
    --multi \
    --num-processes 5 \
    --seeds 0 1 2 \
    --frictions 0.5 1.0 1.5 2.0 2.5 \
    --compress-logs \
    --headless

# Terrain with Level, need specify goals (default is target_pos)
python robogauge/scripts/run.py \
    --task go2_moe.stairs_bd \
    --experiment-name debug \
    --multi \
    --num-processes 5 \
    --seeds 0 1 2 \
    --frictions 2.0 \
    --level 10 \
    --spawn-type level_eval \
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
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
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
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 50 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 \
    --compress-logs \
    --headless
```

# Radar/Bar Plot
将Multi Run结果绘制在雷达图中
```bash
# 可选--out保存到图片
python robogauge/utils/visualize/plot_radar_and_bar.py \
    aggregated_results_1.yaml \
    aggregated_results_2.yaml \
    --out logs/1.jpg

# 绘制下全部 *.yaml, 可选range控制radar, bar y轴显示范围
python robogauge/utils/visualize/plot_radar_and_bar.py \
    /home/xfy/Coding/robot_gauge/mytest/results \
    --range 0.35 1.0 \
    --out logs/1.jpg
```

# Terrain Levels Plot
```bash
# 绘制5种可变等级的地形与摩擦系数的关系图
python robogauge/utils/visualize/plot_terrain_levels.py \
    aggregated_results_1.yaml \
    aggregated_results_2.yaml \
    --out logs/terrain_analysis.jpg
```
