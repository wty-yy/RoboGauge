# -*- coding: utf-8 -*-
'''
@File    : progress_monitor.py
@Time    : 2025/12/27 00:10:07
@Author  : wty-yy (with Gemini 3)
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Centralized progress monitoring with Dynamic Slot Management
'''
from tqdm import tqdm
import multiprocessing
from typing import Dict
from threading import Thread
from dataclasses import dataclass
import heapq

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
        self.active_bars: Dict[int, Dict] = {} 
        self.free_slots = []
        self.max_slot_used = 0 
        
    def _get_free_slot(self):
        """ Get a free screen display position """
        if self.free_slots:
            return heapq.heappop(self.free_slots)
        else:
            self.max_slot_used += 1
            return self.max_slot_used

    def _release_slot(self, slot):
        """ Release a screen display position """
        heapq.heappush(self.free_slots, slot)

    def listener_loop(self, queue):
        """
        Listener thread in the main process
        """
        # Create the main progress bar (Position 0)
        main_bar = tqdm(
            total=self.total_rows, 
            position=0, 
            desc="🚀 Total Progress", 
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [Done: {n_fmt}] [{elapsed}<{remaining}]",
            leave=True,
            smoothing=0.1  # Optional: set smoothing factor (0-1) to prevent drastic ETA fluctuations due to slow tasks
        )
        
        # Number of tasks still pending
        pending_tasks = self.total_rows
        
        while pending_tasks > 0:
            record = queue.get()
            if record is None: break
            
            task_id, msg_type, data = record
            
            # --- Dynamically create/get sub progress bars ---
            if task_id not in self.active_bars:
                # Only create bar when message received to avoid Pending screen flicker
                slot = self._get_free_slot()
                # leave=False is key: after task completion, clear the line for new task reuse
                bar = tqdm(
                    total=100,
                    position=slot,
                    desc=f"Task {task_id} Starting...",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                    leave=False 
                )
                self.active_bars[task_id] = {'bar': bar, 'slot': slot}
            
            bar_info = self.active_bars[task_id]
            bar = bar_info['bar']
            
            # --- Handle messages ---
            try:
                if msg_type == ProgressTypes.INIT:
                    total = data.get('total', 100)
                    desc = data.get('desc', '')
                    bar.reset(total=total)
                    bar.set_description(desc)
                    bar.refresh()
                    
                elif msg_type == ProgressTypes.UPDATE:
                    val = data.get('value', 1)
                    bar.update(val)
                    
                elif msg_type == ProgressTypes.DESC:
                    desc = data.get('desc')
                    if desc: bar.set_description(desc)
                        
                elif msg_type == ProgressTypes.RESET:
                    total = data.get('total', 100)
                    desc = data.get('desc', '')
                    bar.reset(total=total)
                    bar.set_description(desc)
                    bar.refresh()
                    
                elif msg_type == ProgressTypes.FINISH or msg_type == ProgressTypes.ERROR:
                    # Update sub progress bar status
                    desc = data.get('desc')
                    if desc: bar.set_description(desc)
                    bar.refresh()
                    
                    # Close sub progress bar and release slot
                    bar.close() # 因为 leave=False，这行会从屏幕消失
                    slot = bar_info['slot']
                    self._release_slot(slot)
                    del self.active_bars[task_id]
                    
                    # Update the main progress bar
                    main_bar.update(1)
                    main_bar.refresh()
                    
                    pending_tasks -= 1

            except Exception as e:
                pass # Prevent printing errors from disrupting layout

        # Close all remaining bars (theoretically should be empty except main_bar)
        main_bar.close()
        for info in self.active_bars.values():
            info['bar'].close()

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
