#!/bin/bash

source /data/user/wutianyang/Programs/miniforge3/bin/activate go2-gym

python robogauge/scripts/run.py \
    --task-name go2_moe \
    --model-path /data/user/wutianyang/Coding/go2_rl_gym/mytest_merge_data/rem_cts/go2_moe_cts_expert_goal_137000_0.6745/policies/policy.pt \
    --experiment-name go2_moe_cts_expert_goal_137000_0.6745 \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 70 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe \
    --model-path /data/user/wutianyang/Coding/go2_rl_gym/mytest_merge_data/cts_vanilla2/go2_cts_vanilla2_103.5k_0.5819/policies/policy.pt \
    --experiment-name go2_cts_vanilla2_103.5k_0.5819 \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 70 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2 \
    --model-path /data/user/wutianyang/Coding/go2_rl_gym/mytest_merge_data/him/go2_him_21k_0.5266/policies/policy.pt \
    --experiment-name go2_him_21k_0.5266 \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 70 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2 \
    --model-path /data/user/wutianyang/Coding/go2_rl_gym/mytest_merge_data/dwaq/go2_dwaq_119.5k_0.4691/policies/policy.pt \
    --experiment-name go2_dwaq_119.5k_0.4691 \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 70 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe \
    --model-path /data/user/wutianyang/Coding/go2_rl_gym/mytest_merge_data/moe_cts/go2_moe_cts_79k_0.6637/policies/policy.pt \
    --experiment-name go2_moe_cts_79k_0.6637 \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 70 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe \
    --model-path /data/user/wutianyang/Coding/go2_rl_gym/mytest_merge_data/ac_moe_cts/go2_ac_moe_cts_115k_0.6589/policies/policy.pt \
    --experiment-name go2_ac_moe_cts_115k_0.6589 \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 70 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
    --compress-logs \
    --headless

python robogauge/scripts/run.py \
    --task-name go2_moe \
    --model-path /data/user/wutianyang/Coding/go2_rl_gym/mytest_merge_data/mcp_cts/go2_mcp_cts_91k_0.6513/policies/policy.pt \
    --experiment-name go2_mcp_cts_91k_0.6513 \
    --stress-benchmark \
    --stress-terrain-names flat slope_fd slope_bd stairs_fd stairs_bd wave obstacle \
    --num-processes 70 \
    --seeds 0 1 2 \
    --search-seeds 0 1 2 3 4 \
    --frictions 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 \
    --compress-logs \
    --headless
