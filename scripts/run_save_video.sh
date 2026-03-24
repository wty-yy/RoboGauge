#!/bin/bash

MODEL_PATH="resources/models/go2/go2_moe_cts_137k_0.6739.pt"

python robogauge/scripts/run.py \
    --task-name go2_moe.flat \
    --model-path ${MODEL_PATH} \
    --experiment-name save-video \
    --seed 0 \
    --friction 0.6 \
    --goals max_velocity \
    --save-video \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.obstacle \
    --level 5 \
    --spawn-type level_eval \
    --model-path ${MODEL_PATH} \
    --experiment-name save-video \
    --seed 0 \
    --friction 0.6 \
    --goals max_velocity \
    --save-video \
    --headless

# python robogauge/scripts/run.py \
#     --task-name go2_moe.slope_bd \
#     --level 5 \
#     --spawn-type level_eval \
#     --model-path ${MODEL_PATH} \
#     --experiment-name save-video \
#     --seed 0 \
#     --friction 0.6 \
#     --goals max_velocity \
#     --save-video \
#     --headless

# python robogauge/scripts/run.py \
#     --task-name go2_moe.slope_fd \
#     --level 5 \
#     --spawn-type level_eval \
#     --model-path ${MODEL_PATH} \
#     --experiment-name save-video \
#     --seed 0 \
#     --friction 0.6 \
#     --goals max_velocity \
#     --save-video \
#     --headless

# python robogauge/scripts/run.py \
#     --task-name go2_moe.stairs_bd \
#     --level 5 \
#     --spawn-type level_eval \
#     --model-path ${MODEL_PATH} \
#     --experiment-name save-video \
#     --seed 0 \
#     --friction 0.6 \
#     --goals max_velocity \
#     --save-video \
#     --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.stairs_fd \
    --level 5 \
    --spawn-type level_eval \
    --model-path ${MODEL_PATH} \
    --experiment-name save-video \
    --seed 0 \
    --friction 0.6 \
    --goals max_velocity \
    --save-video \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe.wave \
    --level 5 \
    --spawn-type level_eval \
    --model-path ${MODEL_PATH} \
    --experiment-name save-video \
    --seed 0 \
    --friction 0.6 \
    --goals max_velocity \
    --save-video \
    --headless
