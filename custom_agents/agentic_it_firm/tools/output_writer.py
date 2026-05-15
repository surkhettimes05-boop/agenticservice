"""Write workflow outputs to timestamped files."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


class OutputWriter:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, agent_id: str, task: str, content: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", task.lower()).strip("-")[:72] or "task"
        path = self.output_dir / f"{timestamp}-{agent_id}-{slug}.md"
        path.write_text(content, encoding="utf-8")
        return path
