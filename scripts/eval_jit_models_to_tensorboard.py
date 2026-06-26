#!/usr/bin/env python3
"""Batch-submit exported JIT checkpoints to RoboGauge and log scores to TensorBoard.

Overview:
    The script discovers policy_jit_<step>.pt files under rsl_rl experiment logs,
    submits checkpoints through robogauge/scripts/client.py, caches full
    RoboGauge results as YAML, and writes scores as RoboGauge/{key} TensorBoard
    scalars using the checkpoint id as global_step.

Quick Start:
    python scripts/eval_jit_models_to_tensorboard.py

Full Command:
    python scripts/eval_jit_models_to_tensorboard.py \
        --source-root /home/user/go2_rl_robotlab/logs/rsl_rl \
        --experiment-glob "go2_moe_cts_v3*" \
        --log-root logs/go2_lab \
        --task-name go2_lab \
        --server-url http://127.0.0.1:9973 \
        --reuse-source-results \
        --clear-tensorboard

Options:
    --source-root: Directory containing rsl_rl experiment logs.
    --experiment-glob: One or more experiment directory patterns under source root.
    --experiments: Explicit experiment names that override the glob.
    --log-root: TensorBoard and result-cache output root.
    --task-name: RoboGauge task name sent to the evaluation server.
    --server-url: RoboGauge server URL used by RoboGaugeClient.
    --request-timeout: HTTP request timeout for client calls.
    --retry-interval: Delay between server availability retries.
    --poll-interval: Delay between task status checks.
    --start-step: Minimum checkpoint step to include.
    --end-step: Maximum checkpoint step to include.
    --max-checkpoints: Limit the number of discovered checkpoints.
    --overwrite: Re-submit checkpoints even when output result YAML exists.
    --reuse-source-results: Reuse source-run result YAML before submitting.
    --clear-tensorboard: Delete existing output event files before writing.
    --keep-going: Continue after failed checkpoints.
    --dry-run: Print planned work without writing logs or contacting the server.

Notes:
    Start robogauge/scripts/server.py before running checkpoints that cannot be
    satisfied from cached YAML. Output event files are written under
    logs/go2_lab/<experiment>, and full results are cached under
    logs/go2_lab/<experiment>/robogauge_results.
"""

from __future__ import annotations

import argparse
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from torch.utils.tensorboard import SummaryWriter


DEFAULT_SOURCE_ROOT = "/home/user/go2_rl_robotlab/logs/rsl_rl"
DEFAULT_LOG_ROOT = "logs/go2_lab"
CHECKPOINT_RE = re.compile(r"policy_jit_(\d+)\.pt$")


@dataclass(frozen=True)
class Checkpoint:
    """Represent one exported JIT checkpoint and its source run context."""

    experiment_name: str
    run_dir: Path
    model_path: Path
    step: int

    @property
    def source_result_path(self) -> Path:
        """Return the source training run's expected RoboGauge result path.

        Returns:
            Path to the source results_<step>.yaml file.
        """
        return self.run_dir / "robogauge_results" / f"results_{self.step}.yaml"


def parse_args() -> argparse.Namespace:
    """Build and parse the command line interface for batch evaluation.

    Returns:
        Parsed CLI arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate exported policy_jit_*.pt files through robogauge/scripts/client.py "
            "and write scores with tags matching rsl_rl's RoboGauge/{key} TensorBoard logs."
        )
    )
    parser.add_argument("--source-root", type=Path, default=Path(DEFAULT_SOURCE_ROOT))
    parser.add_argument(
        "--experiment-glob",
        nargs="+",
        default=["go2_moe_cts_v3*"],
        help="One or more experiment directory glob patterns under --source-root.",
    )
    parser.add_argument(
        "--experiments",
        nargs="+",
        help="Explicit experiment directory names under --source-root. Overrides --experiment-glob.",
    )
    parser.add_argument("--log-root", type=Path, default=Path(DEFAULT_LOG_ROOT))
    parser.add_argument("--task-name", default="go2_lab")
    parser.add_argument("--server-url", default="http://127.0.0.1:9973")
    parser.add_argument("--request-timeout", type=float, default=5.0)
    parser.add_argument("--retry-interval", type=float, default=2.0)
    parser.add_argument("--poll-interval", type=float, default=60.0)
    parser.add_argument("--start-step", type=int)
    parser.add_argument("--end-step", type=int)
    parser.add_argument("--max-checkpoints", type=int)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-submit checkpoints even when logs/go2_lab/<experiment>/robogauge_results/results_<step>.yaml exists.",
    )
    parser.add_argument(
        "--reuse-source-results",
        action="store_true",
        help="Reuse existing results from the source training run's robogauge_results before submitting to the server.",
    )
    parser.add_argument(
        "--clear-tensorboard",
        action="store_true",
        help="Delete existing TensorBoard event files in each output experiment directory before writing scalars.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue with later checkpoints after a failed evaluation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print discovered checkpoints and planned actions without contacting the server or writing logs.",
    )
    return parser.parse_args()


def checkpoint_step(path: Path) -> int | None:
    """Extract the checkpoint step from a policy_jit_<step>.pt filename.

    Args:
        path: Checkpoint path whose filename should match the export pattern.

    Returns:
        Parsed checkpoint step, or None when the filename does not match.
    """
    match = CHECKPOINT_RE.match(path.name)
    if match is None:
        return None
    return int(match.group(1))


def discover_experiment_dirs(source_root: Path, experiment_globs: list[str], experiments: list[str] | None) -> list[Path]:
    """Discover experiment directories under the source root.

    Explicit experiment names take precedence over the glob. Missing explicit
    directories raise an error so typos do not silently skip evaluations.

    Args:
        source_root: Directory that contains rsl_rl experiment directories.
        experiment_globs: Glob patterns used when explicit experiments are absent.
        experiments: Optional experiment directory names to evaluate.

    Returns:
        Existing experiment directories to scan.
    """
    if experiments:
        dirs = [source_root / name for name in experiments]
    else:
        matched_dirs = {
            path
            for experiment_glob in experiment_globs
            for path in source_root.glob(experiment_glob)
            if path.is_dir()
        }
        dirs = sorted(matched_dirs)
    missing = [path for path in dirs if not path.is_dir()]
    if missing:
        names = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(f"Experiment directories not found:\n{names}")
    return dirs


def discover_checkpoints(args: argparse.Namespace) -> list[Checkpoint]:
    """Find exported policy JIT checkpoints that match CLI filters.

    The discovered checkpoints are sorted by experiment name, step, and path so
    repeated runs process checkpoints in a stable order.

    Args:
        args: Parsed CLI arguments containing discovery roots and filters.

    Returns:
        Ordered checkpoints selected for evaluation.
    """
    source_root = args.source_root.expanduser().resolve()
    experiment_dirs = discover_experiment_dirs(source_root, args.experiment_glob, args.experiments)
    checkpoints: list[Checkpoint] = []

    for experiment_dir in experiment_dirs:
        for model_path in sorted(experiment_dir.glob("*/jit_models/policy_jit_*.pt")):
            step = checkpoint_step(model_path)
            if step is None:
                continue
            if args.start_step is not None and step < args.start_step:
                continue
            if args.end_step is not None and step > args.end_step:
                continue
            checkpoints.append(
                Checkpoint(
                    experiment_name=experiment_dir.name,
                    run_dir=model_path.parents[1],
                    model_path=model_path.resolve(),
                    step=step,
                )
            )

    checkpoints.sort(key=lambda item: (item.experiment_name, item.step, str(item.model_path)))
    if args.max_checkpoints is not None:
        checkpoints = checkpoints[: args.max_checkpoints]
    return checkpoints


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping from disk.

    Args:
        path: YAML file to read.

    Returns:
        Parsed YAML mapping.
    """
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}, got {type(data).__name__}.")
    return data


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write a YAML mapping to disk.

    Args:
        path: Output YAML path.
        data: Mapping to serialize.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)


def result_scores(results: dict[str, Any], source: Path | str) -> dict[str, Any]:
    """Return the scores mapping from a RoboGauge result payload.

    Args:
        results: RoboGauge result payload.
        source: Human-readable origin used in validation errors.

    Returns:
        Mapping of score names to scalar values.
    """
    scores = results.get("scores")
    if not isinstance(scores, dict):
        raise ValueError(f"RoboGauge results from {source} do not contain a 'scores' mapping.")
    return scores


def log_scores(writer: SummaryWriter, results: dict[str, Any], step: int, source: Path | str) -> None:
    """Write RoboGauge score scalars to TensorBoard.

    Scores are logged as RoboGauge/{key}, matching the training runner's
    TensorBoard tag format.

    Args:
        writer: TensorBoard writer for the output experiment directory.
        results: RoboGauge result payload containing a scores mapping.
        step: TensorBoard global_step taken from the checkpoint id.
        source: Human-readable result origin used in validation errors.
    """
    for key, value in result_scores(results, source).items():
        writer.add_scalar(f"RoboGauge/{key}", value, step)
    writer.flush()


def clear_tensorboard_events(log_dir: Path) -> None:
    """Delete TensorBoard event files from an experiment output directory.

    Args:
        log_dir: Experiment output directory that may contain event files.
    """
    for event_file in log_dir.glob("events.out.tfevents*"):
        event_file.unlink()


def output_paths(log_root: Path, checkpoint: Checkpoint) -> tuple[Path, Path]:
    """Build output paths for an experiment and checkpoint result.

    Args:
        log_root: Root directory for TensorBoard logs and result caches.
        checkpoint: Checkpoint whose experiment and step define the paths.

    Returns:
        Experiment log directory and checkpoint result YAML path.
    """
    experiment_log_dir = log_root / checkpoint.experiment_name
    result_path = experiment_log_dir / "robogauge_results" / f"results_{checkpoint.step}.yaml"
    return experiment_log_dir, result_path


def write_cached_result(
    writer: SummaryWriter,
    results: dict[str, Any],
    step: int,
    result_path: Path,
    source: Path | str,
) -> None:
    """Persist a result payload and write its score scalars.

    Args:
        writer: TensorBoard writer for the output experiment directory.
        results: RoboGauge result payload to cache and log.
        step: TensorBoard global_step taken from the checkpoint id.
        result_path: Output YAML path for the cached payload.
        source: Human-readable result origin used in validation errors.
    """
    save_yaml(result_path, results)
    log_scores(writer, results, step, source)


def submit_and_wait(
    client: Any,
    checkpoint: Checkpoint,
    task_name: str,
    poll_interval: float,
    retry_interval: float,
) -> dict[str, Any]:
    """Submit one checkpoint through RoboGaugeClient and wait for results.

    The function polls the existing client until the submitted task returns a
    finished result, preserving one-checkpoint-at-a-time queueing for the batch.

    Args:
        client: RoboGaugeClient instance used for submission and monitoring.
        checkpoint: Checkpoint to evaluate.
        task_name: RoboGauge task name sent with the evaluation request.
        poll_interval: Seconds to sleep between task status checks.
        retry_interval: Seconds to sleep between server availability retries.

    Returns:
        RoboGauge result payload returned by the server.
    """
    task_id = client.submit_task(
        model_path=str(checkpoint.model_path),
        step=checkpoint.step,
        task_name=task_name,
        experiment_name=checkpoint.experiment_name,
        wait_for_server=True,
        retry_interval=retry_interval,
    )
    if task_id is None:
        raise RuntimeError(f"Failed to submit {checkpoint.model_path}.")

    while True:
        client.monitor_tasks(wait_for_server=True, retry_interval=retry_interval)
        response = client.response_data.pop(task_id, None)
        if response is not None:
            results = response.get("results")
            if not isinstance(results, dict):
                raise ValueError(f"Task {task_id} finished without a valid results mapping: {response}")
            response_step = int(response.get("step", checkpoint.step))
            if response_step != checkpoint.step:
                raise ValueError(
                    f"Task {task_id} returned step {response_step}, expected {checkpoint.step}."
                )
            return results

        if task_id not in client.processing_ids:
            raise RuntimeError(f"Task {task_id} ended without a finished result.")

        time.sleep(poll_interval)


def print_plan(checkpoints: list[Checkpoint], log_root: Path, overwrite: bool, reuse_source_results: bool) -> None:
    """Print a compact summary of the batch evaluation plan.

    Args:
        checkpoints: Checkpoints selected for this run.
        log_root: Output root for TensorBoard logs and result caches.
        overwrite: Whether cached output results will be ignored.
        reuse_source_results: Whether source-run result YAML can satisfy work.
    """
    counts: dict[str, int] = {}
    for checkpoint in checkpoints:
        counts[checkpoint.experiment_name] = counts.get(checkpoint.experiment_name, 0) + 1
    print("Discovered checkpoints:")
    for experiment_name in sorted(counts):
        print(f"  - {experiment_name}: {counts[experiment_name]}")
    print(f"Output TensorBoard root: {log_root}")
    print(f"Overwrite output results: {overwrite}")
    print(f"Reuse source results: {reuse_source_results}")


def main() -> None:
    """Run checkpoint discovery, evaluation, caching, and TensorBoard logging."""
    args = parse_args()
    log_root = args.log_root.expanduser().resolve()
    checkpoints = discover_checkpoints(args)
    print_plan(checkpoints, log_root, args.overwrite, args.reuse_source_results)

    if not checkpoints:
        print("No checkpoints matched the requested filters.")
        return

    if args.dry_run:
        for checkpoint in checkpoints[:20]:
            experiment_log_dir, result_path = output_paths(log_root, checkpoint)
            action = "evaluate"
            if result_path.exists() and not args.overwrite:
                action = "use-output-cache"
            elif args.reuse_source_results and checkpoint.source_result_path.exists():
                action = "reuse-source-result"
            print(f"{action}: step={checkpoint.step} model={checkpoint.model_path} tb={experiment_log_dir}")
        if len(checkpoints) > 20:
            print(f"... {len(checkpoints) - 20} more checkpoints omitted from dry-run preview.")
        return

    log_root.mkdir(parents=True, exist_ok=True)
    writers: dict[str, SummaryWriter] = {}
    cleared_experiments: set[str] = set()
    client: Any | None = None
    completed = 0
    failed = 0

    try:
        for index, checkpoint in enumerate(checkpoints, start=1):
            experiment_log_dir, result_path = output_paths(log_root, checkpoint)
            experiment_log_dir.mkdir(parents=True, exist_ok=True)
            if args.clear_tensorboard and checkpoint.experiment_name not in cleared_experiments:
                clear_tensorboard_events(experiment_log_dir)
                cleared_experiments.add(checkpoint.experiment_name)

            writer = writers.get(checkpoint.experiment_name)
            if writer is None:
                writer = SummaryWriter(str(experiment_log_dir))
                writers[checkpoint.experiment_name] = writer

            prefix = f"[{index}/{len(checkpoints)}] {checkpoint.experiment_name} step {checkpoint.step}"
            try:
                if result_path.exists() and not args.overwrite:
                    results = load_yaml(result_path)
                    log_scores(writer, results, checkpoint.step, result_path)
                    print(f"{prefix}: logged cached output result.")
                    completed += 1
                    continue

                if args.reuse_source_results and checkpoint.source_result_path.exists() and not args.overwrite:
                    results = load_yaml(checkpoint.source_result_path)
                    write_cached_result(writer, results, checkpoint.step, result_path, checkpoint.source_result_path)
                    print(f"{prefix}: reused source result and logged TensorBoard scalars.")
                    completed += 1
                    continue

                if client is None:
                    from robogauge.scripts.client import RoboGaugeClient

                    client = RoboGaugeClient(args.server_url, request_timeout=args.request_timeout)
                    client.wait_until_available(retry_interval=args.retry_interval)

                print(f"{prefix}: submitting {checkpoint.model_path}.")
                results = submit_and_wait(
                    client=client,
                    checkpoint=checkpoint,
                    task_name=args.task_name,
                    poll_interval=args.poll_interval,
                    retry_interval=args.retry_interval,
                )
                write_cached_result(writer, results, checkpoint.step, result_path, "server")
                print(f"{prefix}: evaluation finished and logged.")
                completed += 1

            except Exception as exc:
                failed += 1
                print(f"{prefix}: failed: {exc}")
                if not args.keep_going:
                    raise

    finally:
        for writer in writers.values():
            writer.close()

    print(f"Done. Completed: {completed}, failed: {failed}, output: {log_root}")


if __name__ == "__main__":
    main()
