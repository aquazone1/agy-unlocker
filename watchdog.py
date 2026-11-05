#!/usr/bin/env python3
"""Сторож agy-unlocker: держит живым прокси из подписки и сам Gemini.

1. proxy_manager.py ensure — если локальный прокси мёртв или Google через
   него не отвечает, менеджер сам выбирает лучший живой узел подписки.
2. check_patch.py — автообновление CLI могло испортить патченную копию;
   тогда патч пересоздаётся из текущего оригинала.
3. Реальная проба CLI (agy-google + gemini-3.8-flash-low) — если прокси жив,
   а Gemini отвечает ошибкой eligibility, форсируется смена узла
   (proxy_manager.py up).

Рассчитан на запуск из systemd user timer, без TTY (проба идёт через
`script` для псевдотерминала). Повторный запуск при занятом локе завершается
молча, не дожидаясь окончания предыдущего.
"""
import fcntl
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOME = Path.home()
MANAGER = HOME / "proxy" / "proxy_manager.py"
AGY_GOOGLE = HOME / ".local/bin" / "agy-google"
STATE_DIR = HOME / ".local/state"
LOCK = STATE_DIR / "agy-watchdog.lock"
LOG = STATE_DIR / "agy-watchdog.log"
MAX_LOG = 100_000
PROBE_MINUTES = 10  # чаще — только проверка прокси

PROBE_CMD = [
    "script", "-qec",
    "timeout -k 3s 100s {} --model gemini-3.8-flash-low "
    "--disable-slash-commands --print-timeout 60s "
    "-p 'Не используй инструменты. Ответь только: GOOGLE_OK'".format(AGY_GOOGLE),
    "/dev/null",
]


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
    with LOG.open("a") as f:
        f.write(line)
    if LOG.stat().st_size > MAX_LOG:
        data = LOG.read_text()[-MAX_LOG // 2:]
        LOG.write_text(data)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300)


def probe_cli():
    r = subprocess.run(PROBE_CMD, capture_output=True, text=True, timeout=150)
    out = r.stdout + r.stderr
    return r.returncode == 0 and "GOOGLE_OK" in out, out.strip()[-300:]


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit(0)

        if not MANAGER.exists():
            sys.exit(f"нет {MANAGER}")

        r = run([sys.executable, str(MANAGER), "ensure"])
        if r.returncode != 0:
            log(f"ПРОКСИ НЕ ВОССТАНОВЛЕН: {(r.stdout + r.stderr).strip()[-300:]}")
            sys.exit(1)
        log(f"прокси: {r.stdout.strip().splitlines()[-1]}")

        r = run([sys.executable, str(REPO / "check_patch.py")])
        if r.returncode != 0:
            log("патч бит, пересоздаю")
            p = run([sys.executable, str(REPO / "patch.py")])
            if p.returncode != 0:
                log(f"ПАТЧ НЕ ВОССТАНОВЛЕН: {(p.stdout + p.stderr).strip()[-300:]}")
                sys.exit(1)
            log("патч пересоздан")

        stamp = STATE_DIR / "agy-watchdog.probe"
        if stamp.exists() and time.time() - stamp.stat().st_mtime < PROBE_MINUTES * 60:
            return
        ok, tail = probe_cli()
        stamp.touch()
        if ok:
            log("gemini: GOOGLE_OK")
            return
        log(f"gemini молчит, смена узла: {tail}")
        r = run([sys.executable, str(MANAGER), "up"])
        if r.returncode != 0:
            log(f"СМЕНА УЗЛА НЕ УДАЛАСЬ: {(r.stdout + r.stderr).strip()[-300:]}")
            sys.exit(1)
        log(f"узел сменён: {r.stdout.strip().splitlines()[-1]}")


if __name__ == "__main__":
    main()
