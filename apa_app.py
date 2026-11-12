"""Windows interface for the same commands exposed by python -m apa."""

from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
from uuid import uuid4

from apa_release import read_release


ROOT = Path(__file__).resolve().parent
WORKFLOWS = {
    "Подготовить BIM-задание": (["plan"],
        [("Файл задания", "--intent", "file", "")], "план.json"),
    "Выполнить предконтроль оболочки в тестовой PLN": (["architecture-runtime", "preflight"],
        [("Каталог подготовленного задания оболочки", "--job", "directory", ""),
         ("Порт JSON API", "--port", "text", "19723")], None),
    "Проанализировать IFC, DXF или PDF": (["exchange"],
        [("Исходный файл", None, "file", ""), ("Страница PDF", "--page", "text", "1")], "обмен"),
    "Выполнить локальный граф": (["run-read-workflow"],
        [("Файл графа", "--graph", "file", "")], "результат-графа.json"),
    "Выпустить ведомости по снимку": (["documentation", "--all-dump-elements"],
        [("Снимок модели", "--native-dump", "file", ""), ("Номер этажа", "--story", "text", "0")], "документация"),
    "Проверить спецификации шаблона": (["template-check"], [], None),
    "Подготовить проектную библиотеку": (["library-pack"],
        [("Описание проекта", "--brief", "file", ""), ("Кандидат библиотеки", "--candidate", "file", "")], "библиотека.json"),
    "Найти сведения в реестре APA": (["knowledge-query"],
        [("Запрос или идентификатор задачи", "--query", "text", "")], "реестр.json"),
    "Подготовить задание на стену TDK": (["tdk-wall"],
        [("Задание Wall.Ensure", "--payload", "file", "")], "стена-tdk.json"),
    "Сверить стену TDK в открытой копии PLN": (["tdk-wall"],
        [("Задание Wall.Ensure", "--payload", "file", ""), ("Профиль чтения", "--profile", "file", ""),
         ("Журнал TDK (если есть)", "--journal", "optional-file", "")], "стена-tdk.json"),
    "Сформировать профиль чтения PLN": (["mailbox-profile"],
        [("Каталог с квитанцией reopened.json", "--state", "directory", ""),
         ("Порт JSON API", "--port", "text", "19723")], "профиль-apa.json"),
    "Проверить файлы профиля приёмника": (["mailbox", "--healthcheck"],
        [("Профиль чтения", "--package-profile", "file", "")], None),
    "Подготовить настройки бюро": (["bureau-profile"],
        [("Действующая конфигурация бюро", "--config", "file", ""),
         ("Профиль чтения APA", "--profile", "file", "")], "бюро.json"),
    "Посмотреть очередь бюро": (["bureau", "status"],
        [("Файл SQLite бюро", "--db", "file", "")], None),
    "Прочитать квитанцию Arena": (["arena-receipt"],
        [("Квитанция Arena", "--receipt", "file", "")], "arena.json"),
    "Сверить группу после открытия PLN": (["group-runtime", "verify-reopen"],
        [("Каталог состояния группы", "--state", "directory", ""),
         ("Порт JSON API", "--reopen-port", "text", "19723")], None),
}


class Application:
    def __init__(self, window):
        self.window = window
        self.release = read_release(ROOT)
        self.process = None
        self.job = None
        self.inputs = []
        window.title("APA · ArchiCAD Project Accelerator")
        window.geometry("930x650")
        window.minsize(740, 540)
        if "Inter" in font.families(window):
            font.nametofont("TkDefaultFont").configure(family="Inter", size=10)
        content = ttk.Frame(window, padding=20)
        content.pack(fill="both", expand=True)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(5, weight=1)
        ttk.Label(content, text="ArchiCAD Project Accelerator", font=("TkDefaultFont", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))

        ttk.Label(content, text="Действие").grid(row=1, column=0, sticky="w", padx=(0, 12))
        self.choice = ttk.Combobox(content, values=list(WORKFLOWS), state="readonly")
        self.choice.grid(row=1, column=1, columnspan=2, sticky="ew")
        self.choice.current(0)
        self.choice.bind("<<ComboboxSelected>>", lambda _: self.show_fields())

        self.form = ttk.Frame(content, padding=(0, 12))
        self.form.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.form.columnconfigure(1, weight=1)
        self.show_fields()

        self.workspace = tk.StringVar(value=str(Path.home() / "Documents" / "APA" / "Результаты"))
        ttk.Label(content, text="Папка результатов").grid(row=3, column=0, sticky="w", padx=(0, 12))
        ttk.Entry(content, textvariable=self.workspace).grid(row=3, column=1, sticky="ew")
        ttk.Button(content, text="Выбрать…", command=lambda: self.choose(self.workspace, "directory")).grid(
            row=3, column=2, padx=(8, 0))

        buttons = ttk.Frame(content, padding=(0, 12))
        buttons.grid(row=4, column=0, columnspan=3, sticky="ew")
        self.start = ttk.Button(buttons, text="Выполнить", command=self.run)
        self.start.pack(side="left")
        self.open = ttk.Button(buttons, text="Открыть результаты", state="disabled", command=self.open_results)
        self.open.pack(side="left", padx=(8, 0))
        self.status = tk.StringVar(value=f"Сборка {self.release['revision'][:8]}")
        ttk.Label(buttons, textvariable=self.status).pack(side="right")
        panel = ttk.Frame(content)
        panel.grid(row=5, column=0, columnspan=3, sticky="nsew")
        self.output = tk.Text(panel, wrap="word", state="disabled", padx=10, pady=10)
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        self.output.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    @staticmethod
    def choose(value, kind):
        selected = filedialog.askdirectory() if kind == "directory" else filedialog.askopenfilename()
        if selected:
            value.set(selected)

    def show_fields(self):
        for widget in self.form.winfo_children():
            widget.destroy()
        self.inputs = []
        for index, (label, option, kind, default) in enumerate(WORKFLOWS[self.choice.get()][1]):
            value = tk.StringVar(value=default)
            self.inputs.append((label, option, kind, value))
            ttk.Label(self.form, text=label).grid(row=index, column=0, sticky="w", padx=(0, 12), pady=3)
            ttk.Entry(self.form, textvariable=value).grid(row=index, column=1, sticky="ew", pady=3)
            if kind != "text":
                ttk.Button(self.form, text="Выбрать…", command=lambda v=value, k=kind: self.choose(v, k)).grid(
                    row=index, column=2, padx=(8, 0), pady=3)

    def show_output(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("end", text)
        self.output.configure(state="disabled")

    def run(self):
        if self.process:
            return
        try:
            command, _, output = WORKFLOWS[self.choice.get()]
            args = list(command)
            for label, option, kind, value in self.inputs:
                value = value.get().strip()
                if not value and kind == "optional-file":
                    continue
                if not value:
                    raise ValueError(f"Заполните поле «{label}»")
                if kind != "text":
                    value = str(Path(value).resolve(strict=True))
                if option:
                    args.append(option)
                args.append(value)
            if not self.workspace.get().strip():
                raise ValueError("Выберите папку результатов")
            workspace = Path(self.workspace.get().strip()).resolve()
            self.job = workspace / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:6])
            self.job.mkdir(parents=True)
            if output:
                args.extend(["--output", str(self.job / output)])
            if command[0] == "knowledge-query":
                args.extend(["--cache", str(workspace / ("Индекс-" + self.release["knowledgeRevision"][:10]))])
            python = Path(sys.executable).with_name("python.exe")
            with (self.job / "журнал.txt").open("xb") as log:
                self.process = subprocess.Popen([str(python), "-E", "-s", "-X", "utf8", "-m", "apa", *args],
                    cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW)
        except (OSError, ValueError) as exc:
            messagebox.showerror("APA", str(exc))
            return
        self.show_output("")
        self.status.set("Выполняется")
        self.start.configure(state="disabled")
        self.open.configure(state="normal")
        self.window.after(250, self.poll)

    def poll(self):
        code = self.process.poll()
        if code is None:
            self.window.after(250, self.poll)
            return
        self.process = None
        log = self.job / "журнал.txt"
        with log.open("rb") as stream:
            stream.seek(max(0, log.stat().st_size - 32000))
            self.show_output(stream.read().decode("utf-8", errors="replace"))
        self.start.configure(state="normal")
        self.status.set("Результаты сохранены" if code == 0 else f"Команда завершилась с кодом {code}")

    def open_results(self):
        os.startfile(self.job)


if __name__ == "__main__":
    app = tk.Tk()
    Application(app)
    app.mainloop()
