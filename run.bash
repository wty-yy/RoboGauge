#!/bin/bash

source /root/Programs/miniforge3/bin/activate robot

python robogauge/scripts/run.py \
    --task-name go2_moe \
    --experiment-name debug \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 62 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_hard_terrain_141k.pt \
    --experiment-name debug \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 62 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2 \
    --model-path /root/Coding/RoboGauge/mytest/go2_cts_hard_terrain_141k.pt \
    --experiment-name debug \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 62 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2 \
    --experiment-name debug \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 62 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_hard_terrain_100k.pt \
    --experiment-name debug \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 62 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2 \
    --model-path /root/Coding/RoboGauge/mytest/go2_cts_hard_terrain_100k.pt \
    --experiment-name debug \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 62 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 \
    --compress-logs \
    --headless
