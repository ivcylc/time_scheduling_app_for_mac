#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_planner.py — 个人日程提醒助手（适用于 macOS）
========================================================
- 零依赖安装，仅需 Python 和 terminal-notifier。
- 支持普通任务的提前提醒（60/30/15/5/2 分钟），支持特殊任务的每小时重复提醒。
- 默认界面展示未来 24 小时内的首个任务 + 今日特殊任务，并在启动时自动弹出汇总提醒。
"""

import json
import pathlib
import subprocess
import datetime as dt
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

# ────────── macOS 通知封装 ──────────
TN_BIN = pathlib.Path(
    "/Users/ivcylc_lca/Downloads/terminal-notifier-2.0.0/terminal-notifier.app/Contents/MacOS/terminal-notifier"
)

def push(title: str, message: str, sound: str | None = None):
    if not TN_BIN.exists():
        print(f"[WARN] terminal-notifier not found: {TN_BIN}")
        return
    cmd = [str(TN_BIN), "-title", title, "-message", message]
    if sound:
        cmd += ["-sound", sound]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print("[WARN] notification failed:", e)

# ────────── 常量 & 存储 ──────────
STORE = pathlib.Path.home() / ".daily_planner.json"
REMIND_BEFORE_MIN = [60, 30, 15, 5, 2]
HOURLY = 1
HALF_HOUR = dt.timedelta(minutes=30)
FIRST_OVERDUE_DELAY = dt.timedelta(minutes=5)

def load_tasks():
    return json.loads(STORE.read_text()) if STORE.exists() else []

def save_tasks(tasks):
    STORE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2))

# ────────── 调度器 ──────────
sched = BackgroundScheduler()

def schedule_notifications(task: dict):
    when_iso = task["when"]
    start_at = dt.datetime.fromisoformat(when_iso)
    if task.get("special"):
        first_start = max(start_at, dt.datetime.now())
        sched.add_job(push, IntervalTrigger(hours=HOURLY, start_date=first_start), id=f"spec_{when_iso}", args=["特殊项目提醒", task["title"]])
        return
    for m in REMIND_BEFORE_MIN:
        t = start_at - dt.timedelta(minutes=m)
        if t > dt.datetime.now():
            sched.add_job(push, DateTrigger(run_date=t), id=f"pre_{m}_{when_iso}", args=["日程提醒", f"{m} 分钟后：{task['title']}"])
    chk = start_at + FIRST_OVERDUE_DELAY
    if chk > dt.datetime.now():
        sched.add_job(overdue_prompt, DateTrigger(run_date=chk), id=f"od_{when_iso}", args=[when_iso])

def unschedule_all(task: dict):
    for job in sched.get_jobs():
        if task["when"] in job.id:
            job.remove()

# ────────── 过期询问 ──────────
def overdue_prompt(when_iso: str):
    tasks = load_tasks()
    task = next((t for t in tasks if t["when"] == when_iso), None)
    if not task or task.get("special"):
        return
    root = tk._get_default_root()
    keep = messagebox.askyesno("未完成日程", f"{task['title']} 已开始 5 分钟\n是否保留为特殊项目？", parent=root)
    if keep:
        task["special"] = True
        save_tasks(tasks)
        schedule_notifications(task)
    else:
        sched.add_job(overdue_prompt, DateTrigger(run_date=dt.datetime.now() + HALF_HOUR), id=f"repeat_{when_iso}", args=[when_iso])

# ────────── GUI ──────────
class PlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("日程助手")
        self.geometry("640x600")
        self.resizable(False, False)
        bar = tk.Frame(self); bar.pack(fill=tk.X, pady=4)
        tk.Button(bar, text="添加日程", command=self.add_task_dialog).pack(side=tk.LEFT, padx=(6, 4))
        self.show_all_var = tk.BooleanVar(value=False)
        tk.Checkbutton(bar, text="显示全部", variable=self.show_all_var, command=self.refresh_view).pack(side=tk.LEFT)
        cols = ("date", "time", "title")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=22)
        for col, w in zip(cols, (100, 80, 400)):
            self.tree.heading(col, text={"date": "日期", "time": "时间", "title": "事项"}[col])
            self.tree.column(col, width=w, anchor=(tk.CENTER if col != "title" else tk.W))
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.tree.tag_configure("today", background="#e6f2ff")
        self.tree.tag_configure("overdue", foreground="red")
        self.tree.tag_configure("future", background="#f0f0f0")
        ttk.Style().configure("Treeview", rowheight=24)
        for mod in ("<Command-", "<Control-"):
            self.bind_all(f"{mod}n>", lambda e: self.add_task_dialog())
            self.bind_all(f"{mod}d>", self.delete_selected)
            self.bind_all(f"{mod}a>", self.toggle_view)
        self._build_menu(); self.refresh_view()

    def _build_menu(self):
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="删除", command=self.delete_selected)
        self.tree.bind("<Button-3>", self._popup)

    def _popup(self, e):
        iid = self.tree.identify_row(e.y)
        if iid:
            self.tree.selection_set(iid); self.menu.post(e.x_root, e.y_root)

    def refresh_view(self):
        self.tree.delete(*self.tree.get_children())
        today, now = dt.date.today(), dt.datetime.now()
        limit = now + dt.timedelta(days=1)
        tasks = sorted(load_tasks(), key=lambda t: t["when"])
        shown = set()
        for task in tasks:
            when = dt.datetime.fromisoformat(task["when"])
            if not self.show_all_var.get():
                if task.get("special") and when.date() == today:
                    shown.add(when.isoformat())
                elif now <= when < limit:
                    shown.add(when.isoformat())
                elif when < now:
                    # 已过期任务也保留显示，直到被用户删除
                    shown.add(when.isoformat())
                else:
                    continue
            overdue = task.get("special") or when < now or when.date() < today
            if when.date() == today and not overdue:
                tag = "today"
            elif when >= limit:
                tag = "future"
            elif overdue:
                tag = "overdue"
            else:
                tag = ""
            self.tree.insert("", tk.END, values=(when.strftime("%Y-%m-%d"), when.strftime("%H:%M"), task["title"]), tags=(tag,))

    def toggle_view(self, *_):
        self.show_all_var.set(not self.show_all_var.get()); self.refresh_view()

    def add_task_dialog(self):
        date_str = simpledialog.askstring("日期", "请输入日期 (YYYY-MM-DD)，留空默认今天：", parent=self, initialvalue=dt.date.today().isoformat())
        if date_str:
            try:
                date_obj = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("格式错误", "日期格式应为 YYYY-MM-DD"); return
        else:
            date_obj = dt.date.today()
        time_str = simpledialog.askstring("开始时间", "请输入开始时间 (HH:MM)，回车留空创建特殊项目", parent=self)
        special = False
        if not time_str:
            special = True; start_dt = dt.datetime.combine(date_obj, dt.time(0, 0))
        else:
            try:
                hh, mm = map(int, time_str.split(":"))
                start_dt = dt.datetime.combine(date_obj, dt.time(hh, mm))
                if start_dt < dt.datetime.now(): raise ValueError
            except Exception:
                messagebox.showerror("格式错误", "时间格式应为 HH:MM，且需晚于当前时间"); return
        if special and start_dt < dt.datetime.now():
            start_dt = dt.datetime.now()
        title = simpledialog.askstring("事项描述", "请输入事项：", parent=self)
        if not title: return
        task = {"title": title, "when": start_dt.isoformat(), "special": special}
        tasks = load_tasks(); tasks.append(task); save_tasks(tasks)
        schedule_notifications(task); self.refresh_view()

    def delete_selected(self, *_):
        sel = self.tree.selection()
        if not sel:
            return
        if not messagebox.askyesno("确认删除", "确定删除选中的日程？"):
            return
        tasks = load_tasks()
        for iid in sel:
            d, t, title = self.tree.item(iid, "values")
            for task in tasks[:]:
                if task["title"] == title and task["when"].startswith(f"{d}T{t}"):
                    unschedule_all(task)
                    tasks.remove(task)
        save_tasks(tasks)
        self.refresh_view()

# ────────── main 入口 ──────────
def main():
    sched.start()
    tasks = load_tasks()
    if tasks:
        now = dt.datetime.now()
        today = dt.date.today()
        limit = now + dt.timedelta(days=1)
        upcoming = [t for t in tasks if not t.get("special") and now <= dt.datetime.fromisoformat(t["when"]) < limit]
        specials = [t for t in tasks if t.get("special") and dt.datetime.fromisoformat(t["when"]).date() == today]
        parts = []
        if upcoming:
            next_up = sorted(upcoming, key=lambda t: t["when"])[0]
            parts.append(f"24h 内任务：{next_up['title']} @ {dt.datetime.fromisoformat(next_up['when']).strftime('%H:%M')}")
        if specials:
            parts.append("今日特殊：" + ", ".join(t["title"] for t in specials))
        if parts:
            push("启动提醒", "\n".join(parts))
    for t in tasks:
        schedule_notifications(t)
    PlannerApp().mainloop()

if __name__ == '__main__':
    main()
