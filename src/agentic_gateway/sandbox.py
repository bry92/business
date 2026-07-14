"""Constrained Python execution for agent-generated snippets."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path


class SandboxViolation(RuntimeError):
    """Raised when sandboxed code is blocked or exceeds limits."""


@dataclass(frozen=True)
class PythonSandbox:
    """Run Python snippets in an isolated subprocess with restricted builtins."""

    timeout_seconds: float = 2.0
    max_output_bytes: int = 8_192

    def run(self, code: str) -> str:
        """Execute code and return captured stdout."""

        wrapper = self._wrap(code)
        with tempfile.TemporaryDirectory(prefix="agentic-gateway-") as workdir:
            script = Path(workdir) / "snippet.py"
            script.write_text(wrapper)
            proc = subprocess.run(
                [sys.executable, "-I", str(script)],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        stdout = proc.stdout[-self.max_output_bytes :]
        stderr = proc.stderr[-self.max_output_bytes :]
        if proc.returncode != 0:
            raise SandboxViolation(stderr or stdout or f"sandbox exited with {proc.returncode}")
        return stdout

    def _wrap(self, code: str) -> str:
        payload = json.dumps(code)
        return textwrap.dedent(
            f"""
            import builtins

            _ALLOWED_IMPORTS = {{"math", "statistics", "datetime", "decimal", "fractions", "random"}}
            _BLOCKED_BUILTINS = {{"open", "eval", "input", "breakpoint", "help"}}
            _original_import = builtins.__import__

            def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
                root = name.split(".")[0]
                if level == 0 and root not in _ALLOWED_IMPORTS and not root.startswith("_"):
                    raise ImportError(f"import '{{root}}' is not allowed in the sandbox")
                return _original_import(name, globals, locals, fromlist, level)

            builtins.__import__ = _guarded_import
            for _name in _BLOCKED_BUILTINS:
                if hasattr(builtins, _name):
                    setattr(builtins, _name, None)

            _code = {payload}
            exec(_code, {{"__builtins__": builtins.__dict__}}, {{}})
            """
        )
