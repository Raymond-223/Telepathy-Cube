from __future__ import annotations

import heapq
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Tuple


@dataclass(order=True)
class Task:
    priority: int
    created_at: float
    fn: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)


class PriorityTaskQueue:
    def __init__(self) -> None:
        self._heap: List[Task] = []
        self._lock = threading.Lock()

    def push(self, priority: int, fn: Callable, *args, **kwargs) -> None:
        # smaller number => higher priority
        task = Task(priority=priority, created_at=time.time(), fn=fn, args=args, kwargs=kwargs)
        with self._lock:
            heapq.heappush(self._heap, task)

    def pop(self) -> Task | None:
        with self._lock:
            if not self._heap:
                return None
            return heapq.heappop(self._heap)


class WorkerLoop:
    def __init__(self, queue: PriorityTaskQueue) -> None:
        self.queue = queue
        self.running = False
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _run(self) -> None:
        while self.running:
            task = self.queue.pop()
            if task is None:
                time.sleep(0.05)
                continue
            task.fn(*task.args, **task.kwargs)

