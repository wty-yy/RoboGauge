#!/bin/bash

# Description: This script automates the evaluation of multiple models 
#              specified in default ./evaluate_models.txt file.
#
# Usage: ./run_scripts.sh [-n EXP_NAME] [-t TASK_NAME] [-s]
#   -n EXP_NAME     Experiment name (default: go2_moe_flat)
#   -t TASK_NAME    Task name (default: go2_moe_flat)
#   -s              Save video (default: false)
#   -h              Show this help message

### Find the directory of the script ###
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_FILE="$SCRIPT_DIR/evaluate_models.txt"
RUN_PY="$SCRIPT_DIR/run.py"

### Default Configure ###
EXP_NAME=""     # Experiment name [-n]
TASK_NAME="go2_moe_flat"    # Task name [-t]
SAVE_VIDEO=false            # Whether to save video [-s]

### Parse Arguments ###
usage() {
    echo "Usage: $0 [-n EXP_NAME] [-t TASK_NAME] [-s]"
    echo "  -n EXP_NAME     Experiment name (default: ${EXP_NAME})"
    echo "  -t TASK_NAME    Task name (default: ${TASK_NAME})"
    echo "  -s              Save video (default: ${SAVE_VIDEO})"
    echo "  -h              Show this help message"
    exit 1
}

while getopts "n:t:sh" opt; do
    case "${opt}" in
        n) EXP_NAME="$OPTARG" ;;    # Experiment name [-n]
        t) TASK_NAME="$OPTARG" ;;   # Task name [-t]
        s) SAVE_VIDEO=true ;;       # Whether to save video [-s]
        h) usage ;;                 # Print usage [-h]
        *) usage ;;                 # Print usage for invalid options
    esac
done

### Activate Conda Environment ###
eval "$(conda shell.bash hook)"
conda activate kaiwu

### Read Models from File ###
echo "Reading models from: $MODELS_FILE"
mapfile -t models_paths < <(grep -v -e '^[[:space:]]*$' -e '^[[:space:]]*#' "$MODELS_FILE")

if [ ${#models_paths[@]} -eq 0 ]; then
    echo "Error: $MODELS_FILE is empty or contains only blank lines."
    exit 1
fi

### Run Evaluation Scripts ###
base_args="--task $TASK_NAME --headless"

if [ "$SAVE_VIDEO" = true ]; then
    base_args="$base_args --save-video"
fi

if [ -n "$EXP_NAME" ]; then
    base_args="$base_args --exp-name $EXP_NAME"
fi

echo "================ Run Settings ================"
echo "Script Dir: $SCRIPT_DIR"
echo "Runner:     $RUN_PY"
echo "Task:       $TASK_NAME"
echo "Exp Name:   $EXP_NAME"
echo "Save Video: $SAVE_VIDEO"
echo "Models Qty: ${#models_paths[@]}"
echo "=============================================="

for model_path in "${models_paths[@]}"; do
    echo "🚀 Evaluating model: $model_path 🚀"
    python "$RUN_PY" $base_args --model-path "$model_path"
done
