"""Repository context loading for coding agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


IGNORED_DIRS = {".git", "__pycache__", "node_modules", ".next", ".venv", "dist", "build"}
IGNORED_FILES = {".env", ".env.local", ".env.production"}
SUPPORTED_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".sql", ".css", ".toml", ".yaml", ".yml"}


@dataclass(frozen=True)
class RepositoryContext:
    root: Path
    files: dict[str, str] = field(default_factory=dict)
    detected_stack: list[str] = field(default_factory=list)


class RepositoryContextLoader:
    def __init__(self, root: str | Path, max_file_bytes: int = 20000):
        self.root = Path(root)
        self.max_file_bytes = max_file_bytes

    def load(self) -> RepositoryContext:
        files: dict[str, str] = {}
        for path in self.root.rglob("*"):
            if not path.is_file() or self._ignored(path):
                continue
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            rel = path.relative_to(self.root).as_posix()
            files[rel] = path.read_text(encoding="utf-8", errors="ignore")[: self.max_file_bytes]
        return RepositoryContext(root=self.root, files=files, detected_stack=self._detect_stack(files))

    def _ignored(self, path: Path) -> bool:
        if path.name in IGNORED_FILES:
            return True
        return any(part in IGNORED_DIRS for part in path.parts)

    @staticmethod
    def _detect_stack(files: dict[str, str]) -> list[str]:
        combined = "\n".join([*files.keys(), *files.values()]).lower()
        stack = []
        signals = {
            "Next.js": ["next.config", "next/", "app/page.tsx", "pages/"],
            "React": ["react", ".tsx", ".jsx"],
            "Tailwind": ["tailwind", "@tailwind"],
            "FastAPI": ["fastapi", "from fastapi import"],
            "PostgreSQL": ["postgres", "psycopg", "pgvector"],
            "Supabase": ["supabase"],
        }
        for name, patterns in signals.items():
            if any(pattern in combined for pattern in patterns):
                stack.append(name)
        return stack
