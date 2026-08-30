"""
rat.main — Primary entry point for rat (GUI & CLI).
"""

from __future__ import annotations

import logging
import sys

from rat.cli import main as cli_main
from rat.os.app import run_resident_app
from rat.os.daemon import install_launch_agent, uninstall_launch_agent
from rat.os.shell_integration import generate_shell_init_script, install_to_user_zshrc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
)


def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("search", "index", "status", "ask", "dedup", "--help", "-h"):
            cli_main()
            return
        elif cmd in ("init-shell", "shell"):
            print(generate_shell_init_script())
            return
        elif cmd == "install-shell":
            ok = install_to_user_zshrc()
            print("✓ Đã cài đặt tích hợp lệnh 'rat' vào ~/.zshrc!" if ok else "⚠️ Không thể ghi vào ~/.zshrc")
            return
        elif cmd in ("install-daemon", "install-service"):
            ok = install_launch_agent()
            print("✓ Đã cài đặt LaunchAgent tự động khởi động cùng macOS!" if ok else "⚠️ Cài đặt LaunchAgent thất bại")
            return
        elif cmd in ("uninstall-daemon", "uninstall-service"):
            ok = uninstall_launch_agent()
            print("✓ Đã gỡ bỏ LaunchAgent khỏi macOS!" if ok else "⚠️ Gỡ bỏ LaunchAgent thất bại")
            return
        elif cmd in ("--daemon", "-d"):
            run_resident_app(mode="daemon")
            return
        elif cmd == "spotlight":
            run_resident_app(mode="spotlight")
            return

    # Default: launch resident app with full AI Finder window
    run_resident_app(mode="finder")


if __name__ == "__main__":
    main()
