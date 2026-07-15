"""Frozen loopback-only Studio API sidecar for the native Mac shell."""

from __future__ import annotations

import argparse
import os
import signal
import threading
import time

import uvicorn


def _watch_parent(parent_pid: int) -> None:
    while True:
        try:
            os.kill(parent_pid, 0)
        except OSError:
            os.kill(os.getpid(), signal.SIGTERM)
            return
        time.sleep(0.5)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-pid", type=int, required=True)
    args = parser.parse_args()
    threading.Thread(target=_watch_parent, args=(args.parent_pid,), daemon=True).start()

    from main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8321,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
