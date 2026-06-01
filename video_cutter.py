#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Cutter / Trimmer / Uploader
=================================
Cut | Trim | Compress | Upload via FFmpeg

Customize "config.json" for upload endpoint and API key.
"""

import os, sys, subprocess, threading, time, json, requests
from tkinter import (
    Tk, Frame, Label, Button, Entry, Listbox, Scrollbar,
    Spinbox, filedialog, messagebox, StringVar, IntVar, BooleanVar,
    DISABLED, NORMAL, END, VERTICAL, RIGHT, LEFT, BOTH, X, Y,
    W, E, S, N, Radiobutton, Checkbutton, ttk
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
NO_WINDOW_FLAG = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


# ==================== Config ====================

def load_config():
    defaults = {"python_path": "", "api_base_url": "", "api_token": ""}
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
    except Exception:
        pass
    return defaults


def save_config(url, token):
    cfg = load_config()
    cfg["api_base_url"] = url
    cfg["api_token"] = token
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ==================== Utility ====================

def _find_exe(name):
    local = os.path.join(SCRIPT_DIR, name)
    if os.path.isfile(local):
        return local
    for p in os.environ.get("PATH", "").split(os.pathsep):
        c = os.path.join(p, name)
        if os.path.isfile(c):
            return c
    return name


def get_ffmpeg():
    return _find_exe("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")


def get_ffprobe():
    return _find_exe("ffprobe.exe" if sys.platform == "win32" else "ffprobe")


def video_duration(fp):
    try:
        r = subprocess.run([get_ffprobe(), "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", fp],
                           capture_output=True, text=True, timeout=30,
                           creationflags=NO_WINDOW_FLAG, encoding="utf-8", errors="replace")
        v = r.stdout.strip()
        return float(v) if v else None
    except Exception:
        return None


# ==================== App ====================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Cutter / Trimmer / Uploader")
        self.root.geometry("780x650")
        self.root.resizable(True, True)
        self.root.minsize(650, 520)

        cfg = load_config()

        self.video_files = []
        self.output_dir = StringVar(value=os.path.expanduser("~\\Videos\\VideoOutput"))
        self.running = False
        self.stop_requested = False
        self.mode = StringVar(value="cut")

        self.cut_minutes = IntVar(value=1)
        self.cut_seconds = IntVar(value=0)
        self.trim_type = StringVar(value="start")
        self.trim_dur_min = IntVar(value=0)
        self.trim_dur_sec = IntVar(value=30)
        self.trim_custom_s_min = IntVar(value=0)
        self.trim_custom_s_sec = IntVar(value=0)
        self.enable_compress = BooleanVar(value=False)
        self.target_size_mb = IntVar(value=50)

        # Upload (from config.json)
        self.api_base_url = StringVar(value=cfg.get("api_base_url", ""))
        self.api_token = StringVar(value=cfg.get("api_token", ""))
        self.upload_sequential = BooleanVar(value=True)
        self.upload_concurrent = BooleanVar(value=False)

        # Colors
        self.bg = "#f0f4f8"; self.card = "#ffffff"
        self.primary = "#4a90d9"; self.ph = "#357abd"
        self.danger = "#e74c3c"; self.dh = "#c0392b"
        self.success = "#27ae60"; self.tc = "#2c3e50"; self.st = "#7f8c8d"

        self.root.configure(bg=self.bg)
        self.build_ui()

    # ==================== UI ====================

    def build_ui(self):
        # Title
        tf = Frame(self.root, bg=self.bg)
        tf.pack(fill=X, padx=20, pady=(12, 6))
        Label(tf, text="Video Cutter / Trimmer / Uploader",
              font=("Microsoft YaHei UI", 16, "bold"), bg=self.bg, fg=self.tc).pack()
        Label(tf, text="Cut | Trim | Compress | Upload  ·  Requires FFmpeg",
              font=("Microsoft YaHei UI", 9), bg=self.bg, fg=self.st).pack()

        self._build_video_list()
        self._build_notebook()
        self._build_common()
        self._build_actions()

    def _build_video_list(self):
        card = Frame(self.root, bg=self.card, highlightbackground="#e0e6ed", highlightthickness=1, bd=0)
        card.pack(fill=X, padx=20, pady=(4, 4))
        hf = Frame(card, bg=self.card)
        hf.pack(fill=X, padx=15, pady=(10, 6))
        Label(hf, text="Video List", font=("Microsoft YaHei UI", 11, "bold"),
              bg=self.card, fg=self.tc).pack(side=LEFT)
        self.count_label = Label(hf, text="0 videos", font=("Microsoft YaHei UI", 9),
                                 bg=self.card, fg=self.st)
        self.count_label.pack(side=LEFT, padx=(10, 0))
        lf = Frame(card, bg=self.card)
        lf.pack(fill=BOTH, expand=True, padx=15, pady=(0, 8))
        sb = Scrollbar(lf, orient=VERTICAL)
        self.video_listbox = Listbox(lf, height=4, yscrollcommand=sb.set, font=("Consolas", 10),
                                     bg="#f8fafc", selectbackground=self.primary,
                                     selectforeground="white", activestyle="none",
                                     borderwidth=1, relief="solid", highlightbackground="#d0d7de")
        sb.config(command=self.video_listbox.yview)
        self.video_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        bf = Frame(card, bg=self.card)
        bf.pack(fill=X, padx=15, pady=(0, 10))
        self._btn(bf, "+ Add Videos", self.select_videos, self.primary).pack(side=LEFT)
        self._btn(bf, "x Remove", self.remove_selected, self.danger).pack(side=LEFT, padx=(8, 0))
        self._btn(bf, "Clear All", self.clear_all, "#95a5a6").pack(side=LEFT, padx=(8, 0))

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=X, padx=20, pady=(4, 4))

        self.tab_cut = Frame(self.notebook, bg=self.card)
        self.notebook.add(self.tab_cut, text="  Cut  ")
        self._build_cut_tab()

        self.tab_trim = Frame(self.notebook, bg=self.card)
        self.notebook.add(self.tab_trim, text="  Trim  ")
        self._build_trim_tab()

        self.tab_upload = Frame(self.notebook, bg=self.card)
        self.notebook.add(self.tab_upload, text="  Upload  ")
        self._build_upload_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _build_cut_tab(self):
        card = Frame(self.tab_cut, bg=self.card)
        card.pack(fill=X)
        inner = Frame(card, bg=self.card)
        inner.pack(fill=X, padx=15, pady=12)
        Label(inner, text="Split video into equal-length segments",
              bg=self.card, fg=self.st, font=("Microsoft YaHei UI", 9)).pack(anchor=W, pady=(0, 6))
        row = Frame(inner, bg=self.card)
        row.pack(fill=X)
        Label(row, text="Segment Length:", bg=self.card, fg=self.tc,
              font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        self.cut_min_spin = Spinbox(row, from_=0, to=120, increment=1, textvariable=self.cut_minutes,
                                    width=4, font=("Microsoft YaHei UI", 11), justify="center",
                                    state="readonly", readonlybackground="white", relief="solid", bd=1)
        self.cut_min_spin.pack(side=LEFT, padx=(5, 0))
        Label(row, text=" min ", bg=self.card, fg=self.tc, font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        self.cut_sec_spin = Spinbox(row, from_=0, to=59, increment=1, textvariable=self.cut_seconds,
                                    width=4, font=("Microsoft YaHei UI", 11), justify="center",
                                    state="readonly", readonlybackground="white", relief="solid", bd=1)
        self.cut_sec_spin.pack(side=LEFT, padx=(5, 0))
        Label(row, text=" sec", bg=self.card, fg=self.tc, font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        Label(inner, text="Example: 3min20s / 1min => 3x1min + 1x20s",
              bg=self.card, fg=self.st, font=("Microsoft YaHei UI", 8)).pack(anchor=W, pady=(6, 0))

    def _build_trim_tab(self):
        card = Frame(self.tab_trim, bg=self.card)
        card.pack(fill=X)
        inner = Frame(card, bg=self.card)
        inner.pack(fill=X, padx=15, pady=12)
        dur_f = Frame(inner, bg=self.card)
        dur_f.pack(fill=X, pady=(0, 10))
        Label(dur_f, text="Target Duration:", bg=self.card, fg=self.tc,
              font=("Microsoft YaHei UI", 11, "bold")).pack(side=LEFT)
        self.trim_dur_min_s = Spinbox(dur_f, from_=0, to=120, increment=1, textvariable=self.trim_dur_min,
                                      width=4, font=("Microsoft YaHei UI", 11), justify="center",
                                      state="normal", relief="solid", bd=1)
        self.trim_dur_min_s.pack(side=LEFT, padx=(5, 0))
        Label(dur_f, text=" min ", bg=self.card, fg=self.tc, font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        self.trim_dur_sec_s = Spinbox(dur_f, from_=0, to=59, increment=1, textvariable=self.trim_dur_sec,
                                      width=4, font=("Microsoft YaHei UI", 11), justify="center",
                                      state="normal", relief="solid", bd=1)
        self.trim_dur_sec_s.pack(side=LEFT, padx=(5, 0))
        Label(dur_f, text=" sec", bg=self.card, fg=self.tc, font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        region_f = Frame(inner, bg=self.card)
        region_f.pack(fill=X, pady=(0, 4))
        Label(region_f, text="Region:", bg=self.card, fg=self.tc,
              font=("Microsoft YaHei UI", 11, "bold")).pack(side=LEFT)
        for txt, val in [("Start", "start"), ("End", "end"), ("Custom", "custom")]:
            Radiobutton(region_f, text=txt, variable=self.trim_type, value=val,
                        bg=self.card, font=("Microsoft YaHei UI", 10),
                        activebackground=self.card, command=self._on_trim_type_change
                        ).pack(side=LEFT, padx=(10, 2))
        self.trim_frame_custom = Frame(inner, bg=self.card)
        row = Frame(self.trim_frame_custom, bg=self.card)
        row.pack(fill=X)
        Label(row, text="Start Time:", bg=self.card, fg=self.tc, font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        self.trim_custom_s_min_s = Spinbox(row, from_=0, to=120, increment=1, textvariable=self.trim_custom_s_min,
                                           width=4, font=("Microsoft YaHei UI", 11), justify="center",
                                           state="normal", relief="solid", bd=1)
        self.trim_custom_s_min_s.pack(side=LEFT, padx=(5, 0))
        Label(row, text=" min ", bg=self.card, fg=self.tc, font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        self.trim_custom_s_sec_s = Spinbox(row, from_=0, to=59, increment=1, textvariable=self.trim_custom_s_sec,
                                           width=4, font=("Microsoft YaHei UI", 11), justify="center",
                                           state="normal", relief="solid", bd=1)
        self.trim_custom_s_sec_s.pack(side=LEFT, padx=(5, 0))
        Label(row, text=" sec", bg=self.card, fg=self.tc, font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        self.trim_example = Label(inner, text="", bg=self.card, fg=self.st, font=("Microsoft YaHei UI", 8))
        self._on_trim_type_change()

    def _on_trim_type_change(self):
        t = self.trim_type.get()
        if t == "custom":
            self.trim_frame_custom.pack(fill=X, pady=(5, 0))
            self.trim_example.pack(anchor=W, pady=(8, 0))
            self.trim_example.config(text="Example: Start 1:30, Duration 1:00 => Clips 1:30 to 2:30")
        elif t == "start":
            self.trim_frame_custom.pack_forget()
            self.trim_example.pack(anchor=W, pady=(8, 0))
            self.trim_example.config(text="Example: 5min video, 1:30 duration => Keeps first 1:30")
        else:
            self.trim_frame_custom.pack_forget()
            self.trim_example.pack(anchor=W, pady=(8, 0))
            self.trim_example.config(text="Example: 5min video, 1:30 duration => Keeps last 1:30")

    def _build_upload_tab(self):
        """Upload tab: generic API config (no website-specific code)"""
        card = Frame(self.tab_upload, bg=self.card)
        card.pack(fill=X)
        inner = Frame(card, bg=self.card)
        inner.pack(fill=X, padx=12, pady=10)

        # API config
        c1 = Frame(inner, bg="#f0f4f8", highlightbackground="#d0d7de", highlightthickness=1, bd=0)
        c1.pack(fill=X, pady=(0, 4))
        r1 = Frame(c1, bg="#f0f4f8")
        r1.pack(fill=X, padx=8, pady=(6, 2))
        Label(r1, text="Base URL", bg="#f0f4f8", fg=self.tc, font=("Microsoft YaHei UI", 9), width=8, anchor=W).pack(side=LEFT)
        Entry(r1, textvariable=self.api_base_url, font=("Microsoft YaHei UI", 9), bg="white", relief="solid", bd=1).pack(side=LEFT, fill=X, expand=True)
        r2 = Frame(c1, bg="#f0f4f8")
        r2.pack(fill=X, padx=8, pady=(2, 6))
        Label(r2, text="API Key", bg="#f0f4f8", fg=self.tc, font=("Microsoft YaHei UI", 9), width=8, anchor=W).pack(side=LEFT)
        Entry(r2, textvariable=self.api_token, font=("Microsoft YaHei UI", 9), bg="white", relief="solid", bd=1, show="*").pack(side=LEFT, fill=X, expand=True)

        # Save button
        self._btn(inner, "Save Config", self._on_save_config, "#95a5a6", fs=9, pad=(6, 3)).pack(anchor=W, pady=(0, 6))

        # Upload button + serial/concurrent + status
        btn_f = Frame(inner, bg=self.card)
        btn_f.pack(fill=X, pady=(2, 0))
        self.upload_btn = self._btn(btn_f, "Upload All Videos", self._start_upload, self.success, fs=11, pad=(12, 6))
        self.upload_btn.pack(side=LEFT)
        self.upload_stop_btn = self._btn(btn_f, "Stop", self._stop_upload, self.danger, fs=11, pad=(12, 6))
        self.upload_stop_btn.pack(side=LEFT, padx=(6, 0))
        self.upload_stop_btn.config(state=DISABLED)

        mode_bar = Frame(btn_f, bg=self.card)
        mode_bar.pack(side=LEFT, padx=(10, 0))
        self.upload_seq_cb = Checkbutton(mode_bar, text="Sequential", variable=self.upload_sequential,
                                         bg=self.card, activebackground=self.card, command=self._on_seq_mode)
        self.upload_seq_cb.pack(side=LEFT)
        self.upload_conc_cb = Checkbutton(mode_bar, text="Concurrent", variable=self.upload_concurrent,
                                          bg=self.card, activebackground=self.card, command=self._on_conc_mode)
        self.upload_conc_cb.pack(side=LEFT, padx=(4, 0))

        self.upload_status = Label(btn_f, text="", bg=self.card, fg=self.st, font=("Microsoft YaHei UI", 8))
        self.upload_status.pack(side=LEFT, padx=(10, 0))

        # Upload log
        self.upload_log = Listbox(inner, height=5, font=("Consolas", 9), bg="#f8fafc",
                                  selectbackground=self.primary, selectforeground="white",
                                  relief="solid", bd=1, highlightbackground="#d0d7de")
        self.upload_log.pack(fill=X, pady=(6, 0))
        self.upload_stop = False

    def _on_seq_mode(self):
        self.upload_concurrent.set(False)

    def _on_conc_mode(self):
        self.upload_sequential.set(False)

    def _on_save_config(self):
        save_config(self.api_base_url.get(), self.api_token.get())
        self._ulog("Config saved to config.json")

    def _build_common(self):
        """Save path + compression"""
        self.common_card = Frame(self.root, bg=self.card, highlightbackground="#e0e6ed", highlightthickness=1, bd=0)
        self.common_card.pack(fill=X, padx=20, pady=(4, 6))
        inner = Frame(self.common_card, bg=self.card)
        inner.pack(fill=X, padx=15, pady=12)
        pr = Frame(inner, bg=self.card)
        pr.pack(fill=X)
        Label(pr, text="Save to:", bg=self.card, fg=self.tc, font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        self.path_entry = Entry(pr, textvariable=self.output_dir, font=("Microsoft YaHei UI", 9),
                                bg="#f8fafc", relief="solid", bd=1, highlightbackground="#d0d7de")
        self.path_entry.pack(side=LEFT, fill=X, expand=True, padx=(5, 5))
        self._btn(pr, "Browse...", self.choose_output_dir, "#7f8c8d").pack(side=RIGHT)
        comp_f = Frame(inner, bg=self.card)
        comp_f.pack(fill=X, pady=(10, 0))
        self.compress_cb = Checkbutton(comp_f, text="Enable Compression (limit file size)",
                                       variable=self.enable_compress, bg=self.card,
                                       font=("Microsoft YaHei UI", 10), activebackground=self.card,
                                       command=self._on_compress_toggle)
        self.compress_cb.pack(side=LEFT)
        self.compress_mb_spin = Spinbox(comp_f, from_=1, to=5000, increment=10, textvariable=self.target_size_mb,
                                        width=5, font=("Microsoft YaHei UI", 10), justify="center",
                                        state=DISABLED, readonlybackground="#e9ecef", relief="solid", bd=1)
        self.compress_mb_spin.pack(side=LEFT, padx=(10, 0))
        Label(comp_f, text="MB / file", bg=self.card, fg=self.st, font=("Microsoft YaHei UI", 9)).pack(side=LEFT, padx=(3, 0))
        Label(comp_f, text="(skip if source < target)", bg=self.card, fg=self.st, font=("Microsoft YaHei UI", 8)).pack(side=LEFT, padx=(8, 0))

    def _on_compress_toggle(self):
        self.compress_mb_spin.config(state="normal" if self.enable_compress.get() else DISABLED)

    def _build_actions(self):
        self.action_frame = Frame(self.root, bg=self.bg)
        self.action_frame.pack(fill=X, padx=20, pady=(8, 0))
        self.cut_btn = self._btn(self.action_frame, "Start Processing", self.start_processing,
                                 self.success, fs=13, pad=(20, 10))
        self.cut_btn.pack(side=LEFT)
        self.stop_btn = self._btn(self.action_frame, "Stop", self.stop_processing,
                                  self.danger, fs=13, pad=(20, 10))
        self.stop_btn.pack(side=LEFT, padx=(10, 0))
        self.stop_btn.config(state=DISABLED)

        self.progress_frame = Frame(self.root, bg=self.bg)
        self.progress_frame.pack(fill=X, padx=20, pady=(8, 5))
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="determinate")
        self.progress_bar.pack(fill=X)

        self.status_frame = Frame(self.root, bg=self.bg)
        self.status_frame.pack(fill=X, padx=30, pady=(2, 10))
        self.status_label = Label(self.status_frame, text="Ready - Select video files",
                                  font=("Microsoft YaHei UI", 9), bg=self.bg, fg=self.st, anchor=W)
        self.status_label.pack(fill=X)

    def _on_tab_change(self, event):
        try:
            idx = self.notebook.index("current")
            if idx in (0, 1):
                self.mode.set("cut" if idx == 0 else "trim")
                self.common_card.pack(fill=X, padx=20, pady=(4, 6))
                self.action_frame.pack(fill=X, padx=20, pady=(8, 0))
                self.progress_frame.pack(fill=X, padx=20, pady=(8, 5))
                self.status_frame.pack(fill=X, padx=30, pady=(2, 10))
            else:
                self.common_card.pack_forget()
                self.action_frame.pack_forget()
                self.progress_frame.pack_forget()
                self.status_frame.pack_forget()
        except Exception:
            pass

    # ==================== Button Helper ====================

    def _btn(self, parent, text, cmd, color, fs=10, pad=(10, 6)):
        b = Button(parent, text=text, command=cmd, font=("Microsoft YaHei UI", fs),
                   bg=color, fg="white", activebackground=color, activeforeground="white",
                   bd=0, cursor="hand2", padx=pad[0], pady=pad[1], relief="flat")
        hm = {self.primary: self.ph, self.danger: self.dh, self.success: "#219a52"}
        hc = hm.get(color, color)
        b.bind("<Enter>", lambda e, c=hc, w=b: w.config(bg=c))
        b.bind("<Leave>", lambda e, c=color, w=b: w.config(bg=c))
        return b

    # ==================== Video List ====================

    def select_videos(self):
        ft = [("Video Files", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.m4v *.ts *.mpg *.mpeg"), ("All", "*.*")]
        files = filedialog.askopenfilenames(title="Select Videos", filetypes=ft)
        if files:
            added = 0
            ex = {v[0] for v in self.video_files}
            for f in files:
                if f not in ex:
                    self.video_files.append((f, os.path.basename(f)))
                    self.video_listbox.insert(END, os.path.basename(f))
                    added += 1
            self._update_count()
            self._set_status(f"Added {added}, total {len(self.video_files)}")

    def remove_selected(self):
        sel = self.video_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a video first")
            return
        for idx in reversed(sel):
            self.video_listbox.delete(idx)
            del self.video_files[idx]
        self._update_count()

    def clear_all(self):
        if not self.video_files:
            return
        if messagebox.askyesno("Confirm", f"Clear all {len(self.video_files)}?"):
            self.video_listbox.delete(0, END)
            self.video_files.clear()
            self._update_count()

    def choose_output_dir(self):
        d = filedialog.askdirectory(title="Output Directory")
        if d:
            self.output_dir.set(d)

    # ==================== Processing ====================

    def _validate(self):
        if not self.video_files:
            return "Select videos first"
        if self.mode.get() == "cut":
            s = self.cut_minutes.get() * 60 + self.cut_seconds.get()
            if s <= 0:
                return "Segment length > 0"
        else:
            s = self.trim_dur_min.get() * 60 + self.trim_dur_sec.get()
            if s <= 0:
                return "Duration > 0"
        return "OK"

    def start_processing(self):
        if self.running:
            return
        err = self._validate()
        if err != "OK":
            messagebox.showwarning("Invalid", err)
            return
        out_dir = self.output_dir.get()
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create output dir:\n{e}")
            return
        if not self._check_ffmpeg():
            messagebox.showerror("Error", "FFmpeg not found!")
            return
        self.running = True
        self.stop_requested = False
        self._set_ui_state(True)
        threading.Thread(target=self._process, args=(out_dir,), daemon=True).start()

    def stop_processing(self):
        if messagebox.askyesno("Stop", "Stop? Completed files kept."):
            self.stop_requested = True
            self.stop_btn.config(state=DISABLED)

    def _set_ui_state(self, busy):
        sm = DISABLED if busy else NORMAL
        ss = DISABLED if busy else "readonly"
        sn = DISABLED if busy else NORMAL
        self.cut_btn.config(state=sm)
        self.stop_btn.config(state=NORMAL if busy else DISABLED)
        for i in range(self.notebook.index("end")):
            self.notebook.tab(i, state=sm)
        self.cut_min_spin.config(state=ss)
        self.cut_sec_spin.config(state=ss)
        self.trim_dur_min_s.config(state=sn)
        self.trim_dur_sec_s.config(state=sn)
        self.trim_custom_s_min_s.config(state=sn)
        self.trim_custom_s_sec_s.config(state=sn)
        self.compress_cb.config(state=sm)
        if self.enable_compress.get():
            self.compress_mb_spin.config(state="normal" if not busy else DISABLED)

    def _process(self, out_dir):
        if self.mode.get() == "cut":
            self._do_cut(out_dir)
        else:
            self._do_trim(out_dir)

    def _do_cut(self, out_dir):
        seg = self.cut_minutes.get() * 60 + self.cut_seconds.get()
        comp = self.enable_compress.get()
        tmb = self.target_size_mb.get() if comp else 0
        skipped = ok = done = 0
        errors = []
        jobs = []
        for idx, (fp, fn) in enumerate(self.video_files):
            if self.stop_requested:
                break
            d = video_duration(fp)
            if d is None:
                errors.append((fn, "Cannot read duration"))
                continue
            if d < seg:
                skipped += 1
                continue
            cnt = int(d // seg) + (1 if d % seg > 0 else 0)
            jobs.append((idx, fp, fn, d, cnt))
        total = sum(j[4] for j in jobs)
        self.root.after(0, lambda: self.progress_bar.config(maximum=total))
        for idx, fp, fn, d, cnt in jobs:
            if self.stop_requested:
                break
            self.root.after(0, lambda n=fn, i=idx: self._set_status(f"[Cut] [{i+1}/{len(jobs)}] {n}"))
            ne, ext = os.path.splitext(fn)
            for si in range(cnt):
                if self.stop_requested:
                    break
                start = si * seg
                td = min(seg, d - start)
                op = os.path.join(out_dir, f"{ne}_{si+1:03d}{ext}")
                if self._run_cut(fp, op, start, td):
                    if comp and not self._compress(op, tmb, td):
                        errors.append((fn, f"Seg {si+1} compression failed"))
                    done += 1
                else:
                    errors.append((fn, f"Seg {si+1} cut failed"))
                self.root.after(0, lambda c=done: self.progress_bar.config(value=c))
            ok += 1
        self.root.after(0, lambda: self._on_done(ok, done, errors, len(self.video_files), skipped, out_dir))

    def _do_trim(self, out_dir):
        ttype = self.trim_type.get()
        comp = self.enable_compress.get()
        tmb = self.target_size_mb.get() if comp else 0
        skipped = ok = done = 0
        errors = []
        jobs = []
        for idx, (fp, fn) in enumerate(self.video_files):
            if self.stop_requested:
                break
            d = video_duration(fp)
            if d is None:
                errors.append((fn, "Cannot read duration"))
                continue
            segs = self._trim_segs(d, ttype)
            if segs is None:
                skipped += 1
                continue
            jobs.append((idx, fp, fn, d, segs))
        total = sum(len(j[4]) for j in jobs)
        self.root.after(0, lambda: self.progress_bar.config(maximum=total))
        for idx, fp, fn, d, segs in jobs:
            if self.stop_requested:
                break
            self.root.after(0, lambda n=fn, i=idx: self._set_status(f"[Trim] [{i+1}/{len(jobs)}] {n}"))
            ne, ext = os.path.splitext(fn)
            for si, (ss, ee) in enumerate(segs):
                if self.stop_requested:
                    break
                td = ee - ss
                op = os.path.join(out_dir, f"{ne}_{si+1:03d}{ext}")
                if self._run_trim(fp, op, ss, td):
                    if comp and not self._compress(op, tmb, td):
                        errors.append((fn, f"Seg {si+1} compression failed"))
                    done += 1
                else:
                    errors.append((fn, f"Seg {si+1} trim failed"))
                self.root.after(0, lambda c=done: self.progress_bar.config(value=c))
            ok += 1
        self.root.after(0, lambda: self._on_done(ok, done, errors, len(self.video_files), skipped, out_dir))

    def _trim_segs(self, dur, ttype):
        target = self.trim_dur_min.get() * 60 + self.trim_dur_sec.get()
        if target <= 0 or dur < target:
            return None
        if ttype == "start":
            return [(0, target)]
        if ttype == "end":
            return [(dur - target, dur)]
        s = self.trim_custom_s_min.get() * 60 + self.trim_custom_s_sec.get()
        e = min(s + target, dur)
        return [(s, e)] if s < e else None

    # ==================== FFmpeg ====================

    def _check_ffmpeg(self):
        try:
            subprocess.run([get_ffmpeg(), "-version"], capture_output=True, timeout=5, creationflags=NO_WINDOW_FLAG)
            return True
        except Exception:
            return False

    def _run_cut(self, ip, op, start, dur):
        return self._ff(["-ss", str(start), "-i", ip, "-t", str(dur), "-c", "copy", "-avoid_negative_ts", "make_zero", "-y", op])

    def _run_trim(self, ip, op, start, dur):
        return self._run_cut(ip, op, start, dur)

    def _ff(self, args):
        try:
            if os.path.exists(args[-1]):
                os.remove(args[-1])
            cmd = [get_ffmpeg()] + args
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                               creationflags=NO_WINDOW_FLAG, encoding="utf-8", errors="replace")
            return r.returncode == 0
        except Exception as e:
            print(f"[FFmpeg] {e}")
            return False

    # ==================== Compression ====================

    def _compress(self, path, target_mb, duration):
        if not os.path.exists(path):
            return True
        if os.path.getsize(path) <= target_mb * 1024 * 1024:
            return True
        vb = max(int((target_mb * 1024 * 1024 * 8 - 128000 * duration) / duration), 100000)
        tmp = path + ".compressed.mp4"
        if os.path.exists(tmp):
            os.remove(tmp)
        ok = self._ff(["-i", path, "-c:v", "libx264", "-b:v", str(vb), "-maxrate", str(int(vb * 1.5)),
                        "-bufsize", str(int(vb * 2)), "-preset", "fast", "-c:a", "aac", "-b:a", "128k", "-y", tmp])
        if ok and os.path.exists(tmp):
            os.remove(path)
            os.rename(tmp, path)
        elif os.path.exists(tmp):
            os.remove(tmp)
        return ok

    # ==================== Upload ====================

    def _ulog(self, t):
        self.upload_log.insert(END, t)
        self.upload_log.see(END)

    def _start_upload(self):
        if not self.video_files:
            messagebox.showwarning("Info", "Add videos to the list first")
            return
        base = self.api_base_url.get().strip().rstrip("/")
        token = self.api_token.get().strip()
        if not base:
            messagebox.showwarning("Info", "Enter a Base URL")
            return
        files = [(fn, fp) for fp, fn in self.video_files]
        self.upload_log.delete(0, END)
        mode = "Concurrent" if self.upload_concurrent.get() else "Sequential"
        self._ulog(f"{len(files)} file(s) - {mode} mode")
        self._ulog(f"Upload to: {base}")
        self.upload_stop = False
        self.upload_btn.config(state=DISABLED)
        self.upload_stop_btn.config(state=NORMAL)
        self.upload_status.config(text="Uploading...")

        if self.upload_concurrent.get():
            for item in files:
                threading.Thread(target=self._upload_one, args=(item, base, token), daemon=True).start()
        else:
            threading.Thread(target=self._upload_seq, args=(files, base, token), daemon=True).start()

    def _upload_one(self, item, base, token):
        self._upload_seq([item], base, token, silent_btn=True)

    def _upload_seq(self, files, base, token, silent_btn=False):
        ok = fail = 0
        failed = []
        for idx, (fname, fpath) in enumerate(files):
            if self.upload_stop:
                self.root.after(0, lambda: self._ulog("Stopped"))
                break
            sz = os.path.getsize(fpath) / 1024 / 1024
            self.root.after(0, lambda n=fname, i=idx+1, t=len(files), s=sz:
                self._ulog(f"[{i}/{t}] {n} ({s:.1f}MB)"))
            try:
                with open(fpath, "rb") as f:
                    headers = {}
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                    r = requests.post(f"{base}/api/upload", files={"file": (fname, f, "video/mp4")},
                                      headers=headers, timeout=(30, 600))
                if r.status_code in (200, 201):
                    ok += 1
                    self.root.after(0, lambda n=fname: self._ulog(f"   OK: {n}"))
                else:
                    raise Exception(f"HTTP {r.status_code}: {r.text[:100]}")
            except Exception as e:
                fail += 1
                failed.append((fname, str(e)[:120]))
                self.root.after(0, lambda n=fname, err=str(e)[:80]: self._ulog(f"   FAIL: {err}"))
        if not silent_btn:
            self.root.after(0, lambda: self.upload_btn.config(state=NORMAL))
            self.root.after(0, lambda: self.upload_stop_btn.config(state=DISABLED))
        self._upload_summary(ok, fail, failed)

    def _upload_summary(self, ok, fail, failed):
        s = f"Done: {ok} ok / {fail} failed"
        if failed:
            s += "\nFailed files:"
            for fn, err in failed:
                s += f"\n  - {fn}: {err}"
        self.root.after(0, lambda t=s: self.upload_status.config(text=t))
        self.root.after(0, lambda: self._ulog(""))
        self.root.after(0, lambda: self._ulog(f"=== {s.split(chr(10))[0]} ==="))

    def _stop_upload(self):
        self.upload_stop = True
        self.upload_stop_btn.config(state=DISABLED)

    # ==================== Completion ====================

    def _on_done(self, ok_count, seg_done, errors, total, skipped, out_dir):
        self.running = False
        self._set_ui_state(False)
        self.progress_bar.config(value=0)
        mn = "Cut" if self.mode.get() == "cut" else "Trim"
        parts = [f"{mn} done!" if not self.stop_requested else f"{mn} stopped"]
        parts.append(f"Processed: {ok_count}/{total - skipped} videos")
        if skipped:
            parts.append(f"Skipped: {skipped} (too short)")
        parts.append(f"Output: {seg_done} segments")
        if errors:
            el = "\n".join([f"  o {n}: {r}" for n, r in errors[:8]])
            if len(errors) > 8:
                el += f"\n  ... +{len(errors)-8}"
            parts.append(f"Errors: {len(errors)}\n\n{el}")
        msg = "\n".join(parts) + f"\n\nSaved to: {out_dir}"
        self._set_status(f"{mn} done" if not errors else f"{mn} done (errors)")
        if ok_count > 0 and not self.stop_requested:
            if messagebox.askyesno("Done", msg + "\n\nOpen output directory?"):
                os.startfile(out_dir)
        else:
            messagebox.showinfo("Done", msg)

    def _update_count(self):
        self.count_label.config(text=f"{len(self.video_files)} videos")

    def _set_status(self, t):
        self.status_label.config(text=t)


# ==================== Entry ====================

def main():
    root = Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
