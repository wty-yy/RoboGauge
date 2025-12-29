import requests
import time
import json
import sys
from typing import Dict, Any, Optional
from robogauge.scripts.server import ResponseStatus

class RoboGaugeClient:
    def __init__(self, base_url: str = "http://127.0.0.1:9973"):
        self.base_url = base_url
        self.processing_ids = []
        self.task_id2info = {}
        self.response_data = {}

    def submit_task(self, 
        model_path: str, 
        step: int, 
        task_name: str, 
        experiment_name: str, 
        wait_for_server: bool = True,
        retry_interval: int = 2
    ) -> Optional[str]:
        """ Submit stress pipeline evaluation
        Args:
            model_path (str): Torch script model path.
            step (int): Model training step.
            task_name (str): Registered task name.
            experiment_name (str): Experiment name for logging.
            wait_for_server (bool): If True, will keep retrying until the server is available.
            retry_interval (int): Seconds to wait before retrying connection.
        Returns:
            Optional[str]: Task ID if submission is successful, else None.
        """
        payload = {
            "model_path": model_path,
            "step": step,
            "task_name": task_name,
            "experiment_name": experiment_name
        }

        print(f"[RoboGaugeClient]📤 Preparing to submit task: {task_name}")

        while True:
            try:
                response = requests.post(f"{self.base_url}/submit_eval", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    task_id = data["task_id"]
                    print(f"[RoboGaugeClient]✅ Submission successful! Task ID: {task_id}")
                    self.processing_ids.append(task_id)
                    self.task_id2info[task_id] = f"{payload['task_name']}_step{payload['step']}_{payload['experiment_name']}_{task_id}"
                    return task_id
                else:
                    print(f"[RoboGaugeClient]❌ Server returned error: {response.text}")
                    return None

            except requests.exceptions.ConnectionError:
                if not wait_for_server:
                    print("[RoboGaugeClient]❌ Unable to connect to server (Connection Refused).")
                    return None
                
                print(f"[RoboGaugeClient]⏳ Server not responding, retrying in {retry_interval} seconds... (Make sure server.py is running)")
                time.sleep(retry_interval)
            except Exception as e:
                print(f"[RoboGaugeClient]❌ Unknown error: {e}")
                return None

    def monitor_tasks(self):
        print("[RoboGaugeClient]⏱️ Monitoring submitted tasks...")
        """ Monitor all submitted tasks until completion. """
        for task_id in reversed(self.processing_ids):
            respone = requests.get(f"{self.base_url}/get_result/{task_id}")
            if respone.status_code != 200:
                continue
            resp_data = respone.json()
            status = resp_data['status']
            
            if status in [ResponseStatus.PENDING, ResponseStatus.PROCESSING]:
                print(f"[RoboGaugeClient]⏳ Task {self.task_id2info[task_id]} is still {status}.")
                continue

            if status == ResponseStatus.FINISHED:
                self.response_data[task_id] = resp_data
                print(f"[RoboGaugeClient]🎉 Task {self.task_id2info[task_id]} finished successfully!")
            elif status == ResponseStatus.ERROR:
                print(f"[RoboGaugeClient]❌ Task {self.task_id2info[task_id]} encountered an error: {resp_data.get('error_msg')}")
            elif status == ResponseStatus.NOT_FOUND:
                print(f"[RoboGaugeClient]❓ Task {self.task_id2info[task_id]} not found on server.")
            self.processing_ids.remove(task_id)

if __name__ == "__main__":
    SERVER_URL = "http://127.0.0.1:9973"
    client = RoboGaugeClient(base_url=SERVER_URL)

    test_payload = {
        "model_path": "{ROBOGAUGE_ROOT_DIR}/resources/models/go2/go2_moe_cts_124k.pt",
        "step": 124000,
        "task_name": "go2_moe",
        "experiment_name": "client_debug_001"
    }

    print("="*40)
    print("   RoboGauge Client Demo")
    print("="*40)

    task_id = client.submit_task(
        model_path=test_payload["model_path"],
        step=test_payload["step"],
        task_name=test_payload["task_name"],
        experiment_name=test_payload["experiment_name"],
        wait_for_server=True
    )

    while True:
        client.monitor_tasks()
        for task_id, resp in client.response_data.items():
            scores = resp['results']['scores']
            print("[RoboGaugeClient]📊 Scores:")
            print(json.dumps(scores, indent=2, ensure_ascii=False))
        client.response_data.clear()
        time.sleep(5)
