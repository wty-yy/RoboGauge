#!/bin/bash

# Change robogauge/tasks/robots/go2/go2_moe_config.py `save_additional_output = True`
# This 

source /root/Programs/miniforge3/bin/activate robot

# python robogauge/scripts/run.py \
#     --task-name go2_moe \
#     --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_111k_61.09%.pt \
#     --experiment-name debug \
#     --stress-benchmark \
#     --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
#     --num-processes 35 \
#     --seeds 0 1 2 \
#     --search-seeds 0 1 2 3 4 \
#     --frictions 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.25 2.5 \
#     --compress-logs \
#     --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.flat \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_111k_61.09%.pt \
    --experiment-name latent \
    --seed 0 \
    --friction 1.5 \
    --goals max_velocity \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.obstacle \
    --level 9 \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_111k_61.09%.pt \
    --experiment-name latent \
    --seed 0 \
    --friction 1.5 \
    --goals max_velocity \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.slope_bd \
    --level 6 \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_111k_61.09%.pt \
    --experiment-name latent \
    --seed 0 \
    --friction 1.5 \
    --goals max_velocity \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.slope_fd \
    --level 6 \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_111k_61.09%.pt \
    --experiment-name latent \
    --seed 0 \
    --friction 1.5 \
    --goals max_velocity \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.stairs_bd \
    --level 7 \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_111k_61.09%.pt \
    --experiment-name latent \
    --seed 0 \
    --friction 1.5 \
    --goals max_velocity \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.stairs_fd \
    --level 9 \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_111k_61.09%.pt \
    --experiment-name latent \
    --seed 0 \
    --friction 1.5 \
    --goals max_velocity \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.wave \
    --level 6 \
    --model-path /root/Coding/RoboGauge/mytest/go2_moe_cts_111k_61.09%.pt \
    --experiment-name latent \
    --seed 0 \
    --friction 1.5 \
    --goals max_velocity \
    --headless
