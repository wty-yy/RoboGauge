# -*- coding: utf-8 -*-
'''
@File    : progress_monitor.py
@Time    : 2025/12/27 00:10:07
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Centralized progress monitoring for multiprocessing tasks using tqdm
'''
from tqdm import tqdm
import multiprocessing
from typing import Dict
from threading import Thread
from dataclasses import dataclass

class ProgressTypes:
    INIT = 'init'       # Init progress (set total, desc)
    UPDATE = 'update'   # Update progress value (set value)
    DESC = 'desc'       # Update description text only (set desc)
    RESET = 'reset'     # Reset progress bar (set total, desc)
    FINISH = 'finish'   # Mark completion (set desc)
    ERROR = 'error'     # Mark error (set desc)

@dataclass
class ProgressData:
    progress_queue: multiprocessing.Queue
    task_id: int = 0
    msg_prefix: str = ''

def report_progress(progress_data: ProgressData, msg_type, value=None, desc=None, total=None):
    """
    Assistant function to report progress to the main process.
    Args:
        queue: multiprocessing.Queue
        task_id: int, line number of the task
        msg_type: ProgressTypes
        value: int, value to update (for UPDATE type)
        desc: str, description text (for DESC, INIT, FINISH types)
        total: int, total value (for INIT, RESET types)
    """
    if progress_data is None:
        return
    queue = progress_data.progress_queue
    task_id = progress_data.task_id
    msg_prefix = progress_data.msg_prefix
    if desc is not None:
        desc = msg_prefix + desc
    queue.put((task_id, msg_type, {'value': value, 'desc': desc, 'total': total}))

class ProgressMonitor:
    def __init__(self, total_rows):
        self.total_rows = total_rows
        self.bars: Dict[int, tqdm] = {}
        
    def listener_loop(self, queue):
        """
        Run in a separate thread in the main process to consume the Queue and update tqdm.
        """
        # print(f"Monitor started for {self.total_rows} tasks...")
        for i in range(self.total_rows):
            self.bars[i] = tqdm(
                total=100, 
                position=i, 
                desc=f"Task {i} Pending...", 
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
                leave=True
            )
        
        active_tasks = self.total_rows
        
        while active_tasks > 0:
            record = queue.get()
            if record is None:  # Poison pill signal
                break
            
            task_id, msg_type, data = record
            if task_id not in self.bars:
                continue
                
            bar = self.bars[task_id]
            
            if msg_type == ProgressTypes.INIT:
                total = data['total']
                desc = data['desc']
                bar.reset(total=total)
                bar.set_description(desc)
                bar.refresh()
                
            elif msg_type == ProgressTypes.UPDATE:
                val = data['value']
                bar.update(val)
                
            elif msg_type == ProgressTypes.DESC:
                desc = data['desc']
                if desc:
                    bar.set_description(desc)
                    
            elif msg_type == ProgressTypes.RESET:
                # Scenario: Level search finished, starting MultiPipeline, reset progress bar
                total = data['total']
                desc = data['desc']
                bar.reset(total=total)
                bar.set_description(desc)
                bar.refresh()
                
            elif msg_type == ProgressTypes.FINISH:
                desc = data['desc']
                if desc:
                    bar.set_description(desc)
                bar.refresh()
                # Note: We do not close the bar here to keep it displayed until all tasks are finished and closed together.
                active_tasks -= 1
                
            elif msg_type == ProgressTypes.ERROR:
                desc = data['desc']
                bar.set_description(desc)
                bar.refresh()
                active_tasks -= 1

        # After all tasks are finished, close all bars
        for bar in self.bars.values():
            bar.close()

def start_progress_monitor_thread(total_rows):
    """
    Create and start a ProgressMonitor thread. Queue is returned for reporting progress.
    Args:
        total_rows: int, number of tasks to monitor
    Returns:
        queue: multiprocessing.Queue
        monitor_thread: threading.Thread
    """
    queue = multiprocessing.Manager().Queue()
    monitor = ProgressMonitor(total_rows)
    monitor_thread = Thread(target=monitor.listener_loop, args=(queue,))
    monitor_thread.start()
    return queue, monitor_thread
