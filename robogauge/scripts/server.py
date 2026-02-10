# -*- coding: utf-8 -*-
'''
@File    : server.py
@Time    : 2025/12/29 10:58:05
@Author  : wty-yy, Gemini3 Pro
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Asynchronous stress pipeline evaluation server
'''
import os

# Headless solution for mujoco
# For GPU
# os.environ['MUJOCO_GL'] = 'egl'
# For CPU (Slow)
# os.environ['MUJOCO_GL'] = 'osmesa'
# With a graphical user interface (GUI)
os.environ['MUJOCO_GL'] = 'glfw'

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import multiprocessing
import uvicorn
import queue
import time
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional
import argparse

from dataclasses import dataclass
from robogauge.utils.helpers import parse_args, class_to_dict
from robogauge.tasks.pipeline.stress_pipeline import StressPipeline
from pprint import pprint

default_args_list = [
    '--stress-benchmark',
    '--stress-terrain-names', 'flat', 'wave', 'slope_fd',  'slope_bd', 'stairs_fd', 'stairs_bd', 'obstacle',
    # '--stress-terrain-names', 'flat', 'wave',
    # '--num-processes', '30',  # Set in CLI
    '--seeds', '0', '1', '2',
    '--search-seeds', '0', '1', '2', '3', '4',
    '--frictions', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '1.0',
    '--compress-logs',
    '--headless',
]

@dataclass
class EvalTaskData:
    model_path: str
    step: int
    task_name: str
    experiment_name: str

class EvalRequest(BaseModel):
    model_path: str
    step: int
    task_name: str
    experiment_name: str

class ResponseStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    FINISHED = "finished"
    ERROR = "error"
    NOT_FOUND = "not_found"

def run_api_server(input_queue: multiprocessing.Queue, result_dict: dict, port=9973):
    """
    Running in a separate subprocess.
    I/O Process: submit requests -> put into queue -> return ID.
    """
    app = FastAPI()

    @app.post("/submit_eval")
    def submit_eval(req: EvalRequest):
        task_id = str(uuid.uuid4())
        task_data = EvalTaskData(
            model_path=req.model_path,
            step=req.step,
            task_name=req.task_name,
            experiment_name=req.experiment_name
        )
        input_queue.put((task_id, task_data))

        result_dict[task_id] = {"status": ResponseStatus.PENDING}
        return {"task_id": task_id, "message": "Queued"}

    @app.get("/get_result/{task_id}")
    def get_result(task_id: str):
        if task_id not in result_dict:
            return {"status": ResponseStatus.NOT_FOUND}
        result = result_dict[task_id]
        if result["status"] == ResponseStatus.FINISHED:
            result_dict.pop(task_id)
        return result

    print(f"📡 API Server listening on port {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9973, help='API server port')
    parser.add_argument('--num-processes', type=int, default=30, help='Number of parallel processes for StressPipeline')
    args_cli = parser.parse_args()
    print("🤖 RoboGauge Evaluation Server Starting...")
    ctx = multiprocessing.get_context('spawn')
    manager = ctx.Manager()
    task_queue = manager.Queue()
    results_store = manager.dict()

    api_p = ctx.Process(
        target=run_api_server, 
        args=(task_queue, results_store, args_cli.port),
        daemon=True
    )
    api_p.start()

    print("🚀 Main Process started. Waiting for tasks...")
    print("   (StressPipeline will run directly in this Main Process)")

    try:
        while True:
            try:
                task_data: EvalTaskData
                task_id, task_data = task_queue.get(timeout=1.0)
                
                print(f"\n🔄 [Main] Processing Task {task_id} (Step {task_data.step})...")
                results_store[task_id] = {"status": ResponseStatus.PROCESSING}
                
                args_list = default_args_list.copy()
                args_list += [
                    '--model-path', task_data.model_path,
                    '--task-name', task_data.task_name,
                    '--experiment-name', task_data.experiment_name,
                    '--num-processes', str(args_cli.num_processes),
                ]
                args = parse_args(args_list)

                print(f"📋 Running with args:")
                pprint(class_to_dict(args))
                
                pipeline = StressPipeline(args)
                stress_results = pipeline.run() 

                results_store[task_id] = {
                    "status": ResponseStatus.FINISHED,
                    "step": task_data.step,
                    "results": stress_results
                }
                print(f"✅ [Main] Task {task_id} Finished.")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ [Main] Error: {e}")
                import traceback
                traceback.print_exc()
                if 'task_id' in locals():
                    results_store[task_id] = {"status": ResponseStatus.ERROR, "error": str(e), "error_msg": traceback.format_exc()}

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        api_p.terminate()
        api_p.join()

if __name__ == "__main__":
    main()
