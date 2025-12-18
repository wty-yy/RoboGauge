# Single Run
```bash
python robogauge/scripts/run.py \
    --task go2_moe_flat \
    --model-path /home/xfy/Coding/robot_gauge/mytest/models/kaiwu/kaiwu_script_v6-2_124004.pt \
    --experiment-name debug \
    --headless
```

# Multi Run
```bash
python robogauge/scripts/run.py \
    --task go2_moe_flat \
    --model-path /home/xfy/Coding/robot_gauge/mytest/models/kaiwu/kaiwu_script_v6-2_124004.pt \
    --experiment-name debug \
    --multi \
    --num-processes 1 \
    --headless

python robogauge/scripts/run.py \
    --task go2_moe_flat \
    --model-path /home/xfy/Coding/robot_gauge/mytest/models/kaiwu/kaiwu_script_v6-2_102003.pt \
    --experiment-name debug \
    --multi \
    --num-processes 1 \
    --headless
```