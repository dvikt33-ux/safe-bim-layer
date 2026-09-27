"""Tkinter UI for the Safe BIM controller; runtime remains a separate process."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk
from launcher import SingleInstance

from .client import ControllerConnectionError, RuntimeState, SafeBIMClient

POLL_MS = 750
STATUS_RU = {
    "RUNNING": "Выполняется", "WAITING_USER": "Ожидает пользователя",
    "UNKNOWN_OUTCOME": "Нужна проверка", "PAUSED": "Пауза", "FAILED": "Ошибка",
    "DONE": "Готово", "COMPLETED": "Завершено", "CANCELLED": "Остановлено",
    "PENDING": "Ожидает запуска",
}


def configure_logging() -> logging.Logger:
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = logging.getLogger("safe_bim_controller")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(log_dir / "controller.log", maxBytes=512 * 1024,
                                       backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


class ControllerApp:
    def __init__(self, root: tk.Tk, client: SafeBIMClient | None = None):
        self.root = root
        self.client = client or SafeBIMClient()
        self.log = configure_logging()
        self.job_id = "active"
        self.alive = True
        self.vars = {key: tk.StringVar(value="—") for key in
                     ("status", "enum", "job", "step", "progress", "floor", "readback", "message")}
        self.topmost = tk.BooleanVar(value=False)
        self.vars["status"].set("Подключение...")
        self.vars["enum"].set("CONNECTING")
        self.vars["message"].set("Подключаюсь к Safe BIM runtime...")
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.poll()

    def _build(self):
        self.root.title("Safe BIM Controller")
        self.root.geometry("340x330")
        self.root.minsize(300, 260)
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="SAFE BIM", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.vars["status"], font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.vars["enum"], foreground="#666").pack(anchor="w")
        details = (("Задание / Job", "job"), ("Шаг / Step", "step"), ("Прогресс", "progress"),
                   ("Этаж / Story", "floor"), ("Read-back", "readback"))
        for label, key in details:
            row = ttk.Frame(frame); row.pack(fill="x", pady=1)
            ttk.Label(row, text=label + ":", width=17).pack(side="left")
            ttk.Label(row, textvariable=self.vars[key]).pack(side="left", fill="x")
        ttk.Separator(frame).pack(fill="x", pady=8)
        ttk.Label(frame, textvariable=self.vars["message"], wraplength=310).pack(fill="x")
        self.history = ttk.Combobox(frame, state="readonly", width=42)
        self.history.pack(fill="x", pady=(6, 0))
        self.history.bind("<<ComboboxSelected>>", self.select_history)
        buttons = ttk.Frame(frame); buttons.pack(fill="x", pady=10)
        self.continue_button = ttk.Button(buttons, text="Продолжить / Continue", command=lambda: self.command("continue")); self.continue_button.pack(fill="x")
        self.pause_button = ttk.Button(buttons, text="Пауза / Pause", command=lambda: self.command("pause")); self.pause_button.pack(fill="x", pady=3)
        self.stop_button = ttk.Button(buttons, text="Стоп / Stop", command=lambda: self.command("stop")); self.stop_button.pack(fill="x")
        ttk.Checkbutton(frame, text="Поверх окон / Always on top", variable=self.topmost,
                        command=lambda: self.root.attributes("-topmost", self.topmost.get())).pack(anchor="w")

    def poll(self):
        if not self.alive: return
        threading.Thread(target=self._read_state, daemon=True).start()
        self.root.after(POLL_MS, self.poll)

    def _read_state(self):
        try:
            state = self.client.state(self.job_id)
        except Exception as exc:
            self.log.info("state unavailable: %s", exc)
            self.root.after(0, self.disconnected)
            return
        self.root.after(0, lambda: self.show_state(state))

    def disconnected(self):
        self.vars["status"].set("Нет связи")
        self.vars["enum"].set("DISCONNECTED")
        self.vars["message"].set("Runtime недоступен. Ожидаю восстановление связи.")

    def show_state(self, state: RuntimeState):
        self.vars["status"].set(STATUS_RU.get(state.status, state.status))
        self.vars["enum"].set(state.enum)
        for key, value in (("job", f"{state.task} / {state.job_id}"), ("step", state.step),
                           ("progress", state.progress), ("floor", state.floor if state.floor is not None else "—"),
                           ("readback", state.readback)):
            self.vars[key].set(str(value))
        if state.status in {"WAITING_USER", "UNKNOWN_OUTCOME"}:
            msg = "Закройте предупреждение Archicad вручную, затем нажмите «Продолжить»."
        elif state.status == "DISCONNECTED":
            msg = "Нет связи с runtime."
        elif not state.job_id:
            msg = "Runtime подключён. Активная задача отсутствует."
        else:
            msg = "Состояние получено от Safe BIM runtime."
        self.vars["message"].set(msg)
        history = state.history or ()
        self.history["values"] = [f"{item['job_id']} · {item['status']} · {item['task_name']}" for item in history]
        controls = state.controls or {}
        self.continue_button.configure(state="normal" if controls.get("continue", False) else "disabled")
        self.pause_button.configure(state="normal" if controls.get("pause", False) else "disabled")
        self.stop_button.configure(state="normal" if controls.get("stop", False) else "disabled")
        if state.selection == "history":
            self.vars["message"].set("История / History: отображается последний завершённый job.")

    def select_history(self, _event=None):
        value = self.history.get().split(" · ", 1)[0]
        if value:
            self.job_id = value
            self._read_state()

    def command(self, action: str):
        self.log.info("command requested: %s", action)
        try:
            self.client.command(action, self.job_id)
        except Exception as exc:
            self.log.warning("command failed: %s", exc)
            self.vars["message"].set("Команда не выполнена: нет связи с runtime.")

    def close(self):
        self.alive = False
        self.root.destroy()


def _run_controller():
    root = tk.Tk()
    ControllerApp(root)
    root.mainloop()


def main(use_lock: bool = True):
    """Run the controller, locking only for standalone launches.

    The unified launcher already owns the process-level lock and passes
    ``use_lock=False`` so the same process does not self-lock.
    """
    if not use_lock:
        return _run_controller()
    with SingleInstance(Path(__file__).resolve().parent.parent / "logs" / "safe_bim_controller.lock"):
        return _run_controller()


if __name__ == "__main__":
    from launcher import LaunchAlreadyRunning

    try:
        main()
    except LaunchAlreadyRunning as exc:
        print(f"Safe BIM: {exc}")
        raise SystemExit(2)
