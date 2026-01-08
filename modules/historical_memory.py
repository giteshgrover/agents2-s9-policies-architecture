# modules/historical_memory.py

import json
import os
import time
from typing import List, Optional
from pydantic import BaseModel
import pdb

# Optional fallback logger
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

class HistoricalMemoryItem(BaseModel):
    """Represents a single tool call for a given intent and entities."""
    timestamp: float
    type: str  # tool_call for now
    intent: str
    entities: List[str] = []
    tool_name: str
    success: bool


class HistoricalMemoryManager:
    """Manages historical memory (read/write/append)."""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = memory_dir
        self.memory_path = os.path.join('memory', 'historical_conversation_store.json')
        self.items: List[HistoricalMemoryItem] = []

        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

        self.load()

    def load(self):
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self.items = [HistoricalMemoryItem(**item) for item in raw]
        else:
            self.items = []

    def save(self):
        # Before opening the file for writing
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        with open(self.memory_path, "w", encoding="utf-8") as f:
            raw = [item.dict() for item in self.items]
            json.dump(raw, f, indent=2)

    def add(self, item: HistoricalMemoryItem):
        self.items.append(item)
        self.save()

    def add_tool_call(
        self, tool_name: str, success: bool, intent: str, entities: List[str] = []
    ):
        item = HistoricalMemoryItem(
            timestamp=time.time(),
            type="tool_call",
            tool_name=tool_name,
            intent=intent,
            entities=entities,
            success=success
        )
        self.add(item)

    def find_recent_successes(self, intent: str, entities: List[str] = [], limit: int = 5) -> List[str]:
        """Find tool names which succeeded recently."""
        tool_successes = []
        pdb.set_trace()

        # Search from newest to oldest
        for item in reversed(self.items):
            if item.type == "tool_output" and item.success and item.intent == intent and item.entities == entities:
                if item.tool_name and item.tool_name not in tool_successes:
                    tool_successes.append(item.tool_name)
            if len(tool_successes) >= limit:
                break

        return tool_successes

    def add_tool_success(self, tool_name: str, success: bool):
        """Patch last tool call or output for a given tool with success=True/False."""

        # Search backwards for latest matching tool call/output
        for item in reversed(self.items):
            if item.tool_name == tool_name and item.type in {"tool_call", "tool_output"}:
                item.success = success
                log("historical memory", f"✅ Marked {tool_name} as success={success}")
                self.save()
                return

        log("historical memory", f"⚠️ Tried to mark {tool_name} as success={success} but no matching memory found.")

