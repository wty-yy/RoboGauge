# CMD for RoboGauge

- [Single Pipeline](#single-pipeline): Evaluate metrics in a single run
- [Multi Pipeline](#multi-pipeline): Evaluate metrics in multiple runs with different seeds and environment parameters
- [Level Pipeline](#level-pipeline): Evaluate metrics across different terrain levels to find the maximum level the policy can handle
- [Stress Pipeline](#stress-pipeline): Evaluate metrics across different terrain types and environment parameters to test policy robustness
- [Radar/Bar Plot](#radarbar-plot): Plot Multi Run results in Radar and Bar charts
- [Terrain Levels Plot](#terrain-levels-plot): Plot terrain levels analysis

# Single Pipeline
Evaluate metrics in a single run

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
Evaluate metrics in multiple runs with different seeds and environment parameters

```bash
python robogauge/scripts/run.py \
    --task go2_moe.flat \
    --experiment-name debug \
    --multi \
    --num-processes 5 \
    --seeds 0 1 2 \
    --frictions 0.2 0.4 0.6 0.8 1.0 \
    --compress-logs \
    --headless

# Terrain with Level, need specify goals (default is target_pos)
python robogauge/scripts/run.py \
    --task go2_moe.stairs_bd \
    --experiment-name debug \
    --multi \
    --num-processes 5 \
    --seeds 0 1 2 \
    --frictions 0.8 \
    --level 10 \
    --spawn-type level_eval \
    --goals max_velocity diagonal_velocity\
    --compress-logs \
    --headless
```

# Level Pipeline
Evaluate metrics across different terrain levels to find the maximum level the policy can handle

```bash
# Must specify single frictions for LevelPipeline!
python robogauge/scripts/run.py \
    --task go2_moe.slope \
    --experiment-name debug \
    --search-max-level \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.4 \
    --compress-logs \
    --headless
```

# Stress Pipeline
Evaluate metrics across different terrain types and environment parameters to test policy robustness

```bash
python robogauge/scripts/run.py \
    --task go2_moe \
    --experiment-name debug \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 50 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
    --compress-logs \
    --headless
```

# Radar/Bar Plot
Plot Multi Run results in Radar and Bar charts
```bash
# Optional: --out to save to image
python robogauge/utils/visualize/plot_radar_and_bar.py \
    aggregated_results_1.yaml \
    aggregated_results_2.yaml \
    --out logs/1.jpg

# plot all results in a directory, range for radar and bar y-axis
python robogauge/utils/visualize/plot_radar_and_bar.py \
    /home/xfy/Coding/robot_gauge/mytest/results \
    --range 0.35 1.0 \
    --out logs/1.jpg
```

# Terrain Levels Plot
```bash
# plot 5 types of terrains with varying levels and friction coefficients
python robogauge/utils/visualize/plot_terrain_levels.py \
    aggregated_results_1.yaml \
    aggregated_results_2.yaml \
    --out logs/terrain_analysis.jpg
```
