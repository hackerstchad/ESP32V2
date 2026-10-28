#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 MicroPython IDE - hackers_tchad Edition
Auteur     : hackers_tchad
Date       : 2026
Licence    : MIT
Description:
    Interface graphique avancée tkinter permettant de détecter automatiquement
    un module ESP32 branché sur un port USB/Série, d'éditer du code MicroPython,
    de l'envoyer sur l'ESP32 et d'exécuter/interagir avec le REPL directement.
"""

from __future__ import annotations

import os
import sys
import time
import json
import serial
import serial.tools.list_ports
import threading
import subprocess
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog, colorchooser
from tkinter.font import Font
from typing import Optional, List, Dict, Callable, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import queue


# =============================================================================
# CONSTANTES GLOBALES
# =============================================================================
APP_NAME = "ESP32 MicroPython IDE"
APP_VERSION = "2026.1.0"
APP_AUTHOR = "hackers_tchad"
CONFIG_FILE = "esp32_ide_config.json"
ICON_DATA = None

ESP32_VID_PID_HINTS = [
    (0x10C4, 0xEA60),  # CP2102 / CP2104
    (0x1A86, 0x7523),  # CH340
    (0x0403, 0x6001),  # FT232
    (0x303A, 0x0002),  # ESP32-S2
    (0x303A, 0x0003),  # ESP32-S3
    (0x303A, 0x1001),  # Espressif USB/JTAG
]

DEFAULT_BAUDRATES = [9600, 19200, 38400, 57600, 74880, 115200, 230400, 460800, 921600]
DEFAULT_BAUD = 115200

THEMES = {
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#d4d4d4",
        "insert": "#ffffff",
        "select": "#264f78",
        "linenumber_bg": "#1e1e1e",
        "linenumber_fg": "#858585",
        "keyword": "#569cd6",
        "string": "#ce9178",
        "comment": "#6a9955",
        "number": "#b5cea8",
        "function": "#dcdcaa",
        "class": "#4ec9b0",
        "operator": "#d4d4d4",
        "builtin": "#4fc1ff",
        "status_bg": "#007acc",
        "status_fg": "#ffffff",
        "terminal_bg": "#0c0c0c",
        "terminal_fg": "#cccccc",
        "accent": "#007acc",
        "panel_bg": "#252526",
        "border": "#3e3e42",
    },
    "light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "insert": "#000000",
        "select": "#add6ff",
        "linenumber_bg": "#f0f0f0",
        "linenumber_fg": "#237893",
        "keyword": "#0000ff",
        "string": "#a31515",
        "comment": "#008000",
        "number": "#098658",
        "function": "#795e26",
        "class": "#267f99",
        "operator": "#000000",
        "builtin": "#001080",
        "status_bg": "#007acc",
        "status_fg": "#ffffff",
        "terminal_bg": "#ffffff",
        "terminal_fg": "#000000",
        "accent": "#007acc",
        "panel_bg": "#f3f3f3",
        "border": "#cccccc",
    },
    "hackers_tchad": {
        "bg": "#0a0a0f",
        "fg": "#00ff9d",
        "insert": "#00ff9d",
        "select": "#005533",
        "linenumber_bg": "#0d0d12",
        "linenumber_fg": "#00cc7d",
        "keyword": "#00d9ff",
        "string": "#ff6b6b",
        "comment": "#5c6b73",
        "number": "#ffd166",
        "function": "#00ff9d",
        "class": "#9b5de5",
        "operator": "#00ff9d",
        "builtin": "#00bbf9",
        "status_bg": "#00ff9d",
        "status_fg": "#000000",
        "terminal_bg": "#050505",
        "terminal_fg": "#00ff9d",
        "accent": "#00ff9d",
        "panel_bg": "#111118",
        "border": "#1f2833",
    },
}

PYTHON_KEYWORDS = [
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
]

PYTHON_BUILTINS = [
    "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable",
    "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir",
    "divmod", "enumerate", "eval", "exec", "filter", "float", "format",
    "frozenset", "getattr", "globals", "hasattr", "hash", "help", "hex",
    "id", "input", "int", "isinstance", "issubclass", "iter", "len", "list",
    "locals", "map", "max", "memoryview", "min", "next", "object", "oct",
    "open", "ord", "pow", "print", "property", "range", "repr", "reversed",
    "round", "set", "setattr", "slice", "sorted", "staticmethod", "str",
    "sum", "super", "tuple", "type", "vars", "zip",
]

MICROPYTHON_MODULES = [
    "machine", "network", "bluetooth", "ure", "ujson", "uos", "usocket",
    "ussl", "ustruct", "utime", "uzlib", "_thread", "btree", "cryptolib",
    "framebuf", "gc", "math", "micropython", "neopixel", "ntptime", "onewire",
    "random", "select", "socket", "ssl", "struct", "sys", "time", "zlib",
    "esp", "esp32", "flashbdev", "inisetup", "webrepl", "umqtt",
]


# =============================================================================
# CONFIGURATION
# =============================================================================
@dataclass
class AppConfig:
    theme: str = "dark"
    font_family: str = "Consolas"
    font_size: int = 11
    baudrate: int = DEFAULT_BAUD
    last_project: str = ""
    auto_connect: bool = True
    auto_detect: bool = True
    line_numbers: bool = True
    word_wrap: bool = False
    show_terminal: bool = True
    show_explorer: bool = True
    recent_files: List[str] = field(default_factory=list)
    editor_settings: Dict[str, Any] = field(default_factory=dict)
    custom_tags: Dict[str, str] = field(default_factory=dict)

    def save(self, path: str = CONFIG_FILE):
        data = {
            "theme": self.theme,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "baudrate": self.baudrate,
            "last_project": self.last_project,
            "auto_connect": self.auto_connect,
            "auto_detect": self.auto_detect,
            "line_numbers": self.line_numbers,
            "word_wrap": self.word_wrap,
            "show_terminal": self.show_terminal,
            "show_explorer": self.show_explorer,
            "recent_files": self.recent_files,
            "editor_settings": self.editor_settings,
            "custom_tags": self.custom_tags,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Erreur sauvegarde: {e}")

    @classmethod
    def load(cls, path: str = CONFIG_FILE) -> "AppConfig":
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = cls()
            for key, value in data.items():
                if hasattr(cfg, key):
                    setattr(cfg, key, value)
            return cfg
        except Exception as e:
            print(f"[Config] Erreur chargement: {e}")
            return cls()


# =============================================================================
# GESTION DU PORT SÉRIE / ESP32
# =============================================================================
class SerialManager:
    def __init__(self):
        self.port: Optional[serial.Serial] = None
        self.port_name: str = ""
        self.baudrate: int = DEFAULT_BAUD
        self.connected: bool = False
        self.lock = threading.Lock()
        self.read_thread: Optional[threading.Thread] = None
        self.running: bool = False
        self.callbacks: List[Callable[[str], None]] = []
        self.raw_callbacks: List[Callable[[bytes], None]] = []
        self.last_error: str = ""

    def list_ports(self) -> List[Dict[str, Any]]:
        ports = []
        for p in serial.tools.list_ports.comports():
            is_esp = self._is_likely_esp32(p)
            ports.append({
                "device": p.device,
                "description": p.description,
                "hwid": p.hwid,
                "vid": p.vid,
                "pid": p.pid,
                "is_esp32": is_esp,
            })
        return ports

    def _is_likely_esp32(self, p) -> bool:
        if p.vid is None or p.pid is None:
            return False
        return (p.vid, p.pid) in ESP32_VID_PID_HINTS

    def detect_esp32_port(self) -> Optional[str]:
        for port_info in self.list_ports():
            if port_info["is_esp32"]:
                return port_info["device"]
        # Fallback: chercher une description contenant ESP / CP210x / CH340
        for port_info in self.list_ports():
            desc = port_info["description"].upper()
            if any(h in desc for h in ["CP210", "CH340", "FT232", "ESP", "USB-SERIAL"]):
                return port_info["device"]
        return None

    def connect(self, port_name: str, baudrate: int = DEFAULT_BAUD) -> bool:
        self.disconnect()
        try:
            self.port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,
                write_timeout=2.0,
            )
            self.port_name = port_name
            self.baudrate = baudrate
            self.connected = True
            self.running = True
            self.read_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self.read_thread.start()
            return True
        except Exception as e:
            self.last_error = str(e)
            self.connected = False
            return False

    def disconnect(self):
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        if self.port and self.port.is_open:
            try:
                self.port.close()
            except Exception:
                pass
        self.port = None
        self.port_name = ""
        self.connected = False

    def _reader_loop(self):
        buffer = b""
        while self.running and self.port and self.port.is_open:
            try:
                data = self.port.read(self.port.in_waiting or 1)
                if data:
                    buffer += data
                    if b"\n" in buffer or b"\r" in buffer:
                        lines = buffer.splitlines(keepends=True)
                        for line in lines[:-1]:
                            self._emit(line)
                        buffer = lines[-1]
                else:
                    if buffer:
                        self._emit(buffer)
                        buffer = b""
            except serial.SerialException as e:
                self._emit(f"\n[SERIE] Déconnecté: {e}\n".encode("utf-8", "replace"))
                self.connected = False
                break
            except Exception as e:
                print(f"[SerialManager] Lecture erreur: {e}")
        if buffer:
            self._emit(buffer)

    def _emit(self, data: bytes):
        for cb in self.raw_callbacks:
            try:
                cb(data)
            except Exception as e:
                print(f"[SerialManager] raw callback error: {e}")
        try:
            text = data.decode("utf-8", "replace")
        except Exception:
            text = data.decode("latin-1", "replace")
        for cb in self.callbacks:
            try:
                cb(text)
            except Exception as e:
                print(f"[SerialManager] text callback error: {e}")

    def send(self, data: str or bytes, end: str = "\r\n") -> bool:
        if not self.connected or not self.port:
            return False
        try:
            with self.lock:
                if isinstance(data, str):
                    payload = (data + end).encode("utf-8")
                else:
                    payload = data
                    if end:
                        payload += end.encode("utf-8")
                self.port.write(payload)
                self.port.flush()
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def send_interrupt(self):
        if self.connected and self.port:
            try:
                self.port.write(b"\x03")
                self.port.flush()
            except Exception as e:
                print(f"[SerialManager] Interruption impossible: {e}")

    def send_reset(self):
        if self.connected and self.port:
            try:
                self.port.write(b"\x04")
                self.port.flush()
            except Exception as e:
                print(f"[SerialManager] Reset impossible: {e}")

    def soft_reset(self) -> bool:
        return self.send("\x04", end="")

    def enter_raw_repl(self) -> bool:
        if not self.connected:
            return False
        self.send_interrupt()
        time.sleep(0.2)
        self.send("\x01", end="")
        time.sleep(0.3)
        return True

    def exit_raw_repl(self) -> bool:
        return self.send("\x02", end="")

    def execute_on_device(self, code: str, timeout: float = 5.0) -> Tuple[bool, str]:
        if not self.connected:
            return False, "Non connecté à un ESP32."
        self.enter_raw_repl()
        time.sleep(0.5)
        self.send(code, end="\x04")
        start = time.time()
        output = ""
        while time.time() - start < timeout:
            if self.port and self.port.in_waiting:
                try:
                    chunk = self.port.read(self.port.in_waiting).decode("utf-8", "replace")
                    output += chunk
                    if "\x04" in chunk:
                        break
                except Exception:
                    pass
            time.sleep(0.05)
        self.exit_raw_repl()
        ok = "Traceback" not in output
        return ok, output

    def put_file(self, local_path: str, remote_name: str, timeout: float = 10.0) -> Tuple[bool, str]:
        if not self.connected:
            return False, "Non connecté."
        try:
            with open(local_path, "rb") as f:
                content = f.read()
        except Exception as e:
            return False, f"Lecture impossible: {e}"
        self.enter_raw_repl()
        time.sleep(0.3)
        cmd = (
            f"f=open('{remote_name}','wb')\n"
            f"f.write({content})\n"
            "f.close()\n"
        )
        self.send(cmd, end="\x04")
        start = time.time()
        output = ""
        while time.time() - start < timeout:
            if self.port and self.port.in_waiting:
                try:
                    chunk = self.port.read(self.port.in_waiting).decode("utf-8", "replace")
                    output += chunk
                    if "\x04" in chunk:
                        break
                except Exception:
                    pass
            time.sleep(0.05)
        self.exit_raw_repl()
        ok = "Traceback" not in output and "OK" in output
        return ok, output

    def list_device_files(self, timeout: float = 5.0) -> Tuple[bool, List[str]]:
        if not self.connected:
            return False, []
        ok, out = self.execute_on_device(
            "import uos\nprint(uos.listdir())\n",
            timeout=timeout,
        )
        if not ok:
            return False, []
        files = re.findall(r"'([^']+)'", out)
        return True, files

    def remove_device_file(self, filename: str, timeout: float = 5.0) -> Tuple[bool, str]:
        code = f"import uos\nuos.remove('{filename}')\nprint('OK')\n"
        ok, out = self.execute_on_device(code, timeout=timeout)
        return ok, out


# =============================================================================
# ÉDITEUR DE CODE AVEC NUMÉROS DE LIGNE
# =============================================================================
class LineNumberCanvas(tk.Canvas):
    def __init__(self, master, text_widget, theme, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.text_widget = text_widget
        self.theme = theme
        self.config(width=50, highlightthickness=0)
        self.bind("<Button-1>", self._on_click)
        self.text_widget.bind("<KeyRelease>", self._on_change)
        self.text_widget.bind("<MouseWheel>", self._on_change)
        self.text_widget.bind("<Configure>", self._on_change)
        self.text_widget.bind("<<Change>>", self._on_change)
        self._redraw()

    def set_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.config(bg=theme["linenumber_bg"])
        self._redraw()

    def _on_change(self, event=None):
        self.after(10, self._redraw)

    def _on_click(self, event):
        line = int(self.canvasy(event.y) / self._line_height()) + 1
        self.text_widget.tag_remove("sel", "1.0", tk.END)
        self.text_widget.tag_add("sel", f"{line}.0", f"{line + 1}.0")
        self.text_widget.mark_set(tk.INSERT, f"{line}.0")
        self.text_widget.focus_set()

    def _line_height(self) -> int:
        return self.text_widget.dlineinfo("1.0")[3] if self.text_widget.dlineinfo("1.0") else 17

    def _redraw(self):
        self.delete("all")
        bg = self.theme.get("linenumber_bg", "#1e1e1e")
        fg = self.theme.get("linenumber_fg", "#858585")
        self.config(bg=bg)
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(35, y, anchor="ne", text=linenum, fill=fg, font=self.text_widget.cget("font"))
            i = self.text_widget.index(f"{i}+1line")


class CodeEditor(tk.Frame):
    def __init__(self, master, theme: Dict[str, str], config: AppConfig, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.theme = theme
        self.config = config
        self.font = Font(family=config.font_family, size=config.font_size)
        self.bold_font = Font(family=config.font_family, size=config.font_size, weight="bold")
        self.filepath: Optional[str] = None
        self.filename = "sans_titre.py"
        self.modified = False
        self._highlight_after = None

        self.text = tk.Text(
            self,
            wrap=tk.NONE,
            font=self.font,
            bg=theme["bg"],
            fg=theme["fg"],
            insertbackground=theme["insert"],
            selectbackground=theme["select"],
            selectforeground=theme["fg"],
            undo=True,
            maxundo=-1,
            autoseparators=True,
            tabs=(self.font.measure("    "),),
            borderwidth=0,
            highlightthickness=0,
            padx=5,
            pady=5,
        )
        self.scroll_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.scroll_x = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.config(yscrollcommand=self._on_yscroll, xscrollcommand=self.scroll_x.set)

        self.line_numbers = LineNumberCanvas(self, self.text, theme)

        self.line_numbers.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.scroll_y.grid(row=0, column=2, sticky="ns")
        self.scroll_x.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._setup_tags()
        self._bind_events()
        self._setup_autocomplete()

    def _on_yscroll(self, first, last):
        self.scroll_y.set(first, last)
        self.line_numbers._redraw()

    def _setup_tags(self):
        t = self.theme
        self.text.tag_config("keyword", foreground=t["keyword"], font=self.bold_font)
        self.text.tag_config("string", foreground=t["string"])
        self.text.tag_config("comment", foreground=t["comment"], font=self.font)
        self.text.tag_config("number", foreground=t["number"])
        self.text.tag_config("function", foreground=t["function"])
        self.text.tag_config("class", foreground=t["class"])
        self.text.tag_config("operator", foreground=t["operator"])
        self.text.tag_config("builtin", foreground=t["builtin"])
        self.text.tag_config("mpmodule", foreground=t["class"])
        self.text.tag_config("current_line", background=t["panel_bg"])

    def _bind_events(self):
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<Tab>", self._on_tab)
        self.text.bind("<Return>", self._on_return)
        self.text.bind("<BackSpace>", self._on_backspace)
        self.text.bind("<Control-s>", lambda e: self.event_generate("<<SaveFile>>"))
        self.text.bind("<Control-S>", lambda e: self.event_generate("<<SaveFile>>"))
        self.text.bind("<Control-o>", lambda e: self.event_generate("<<OpenFile>>"))
        self.text.bind("<Control-n>", lambda e: self.event_generate("<<NewFile>>"))
        self.text.bind("<Control-f>", lambda e: self.event_generate("<<FindReplace>>"))
        self.text.bind("<Control-slash>", self._toggle_comment)
        self.text.bind("<Control-question>", self._toggle_comment)
        self.text.bind("<<Modified>>", self._on_modified)

    def _setup_autocomplete(self):
        self.autocomplete_words = set(PYTHON_KEYWORDS + PYTHON_BUILTINS + MICROPYTHON_MODULES)
        self.autocomplete_list = None

    def set_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.text.config(
            bg=theme["bg"],
            fg=theme["fg"],
            insertbackground=theme["insert"],
            selectbackground=theme["select"],
            selectforeground=theme["fg"],
        )
        self._setup_tags()
        self.line_numbers.set_theme(theme)
        self.highlight_syntax()

    def set_font(self, family: str, size: int):
        self.font.config(family=family, size=size)
        self.bold_font.config(family=family, size=size)
        self.text.config(font=self.font)
        self._setup_tags()

    def load_file(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.filepath = filepath
            self.filename = os.path.basename(filepath)
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.text.edit_modified(False)
            self.modified = False
            self.highlight_syntax()
            self.line_numbers._redraw()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir {filepath}:\n{e}")

    def save_file(self, filepath: Optional[str] = None) -> bool:
        if filepath:
            self.filepath = filepath
        if not self.filepath:
            return False
        try:
            content = self.text.get("1.0", tk.END)
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.filename = os.path.basename(self.filepath)
            self.text.edit_modified(False)
            self.modified = False
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder {self.filepath}:\n{e}")
            return False

    def get_content(self) -> str:
        return self.text.get("1.0", tk.END)

    def set_content(self, content: str):
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.highlight_syntax()

    def _on_key_release(self, event=None):
        if event and event.keysym in ("Up", "Down", "Left", "Right", "Control_L", "Control_R"):
            return
        self._schedule_highlight()

    def _schedule_highlight(self):
        if self._highlight_after:
            self.after_cancel(self._highlight_after)
        self._highlight_after = self.after(300, self.highlight_syntax)

    def _on_modified(self, event=None):
        flag = self.text.edit_modified()
        if flag:
            self.modified = True
            self.event_generate("<<FileModified>>")
        self.text.edit_modified(False)

    def _on_tab(self, event):
        sel = self.text.tag_ranges("sel")
        if sel:
            start, end = sel
            line_start = int(start.split(".")[0])
            line_end = int(end.split(".")[0])
            for line in range(line_start, line_end + 1):
                self.text.insert(f"{line}.0", "    ")
        else:
            self.text.insert(tk.INSERT, "    ")
        return "break"

    def _on_return(self, event):
        pos = self.text.index(tk.INSERT)
        line, col = map(int, pos.split("."))
        current = self.text.get(f"{line}.0", pos)
        indent = len(current) - len(current.lstrip())
        extra = ""
        stripped = current.strip()
        if stripped.endswith(":"):
            extra = "    "
        elif stripped.endswith("(") or stripped.endswith("[") or stripped.endswith("{"):
            extra = "    "
        self.text.insert(tk.INSERT, "\n" + " " * indent + extra)
        self._schedule_highlight()
        return "break"

    def _on_backspace(self, event):
        pos = self.text.index(tk.INSERT)
        line, col = map(int, pos.split("."))
        if col >= 4:
            segment = self.text.get(f"{line}.{col - 4}", pos)
            if segment == "    ":
                self.text.delete(f"{line}.{col - 4}", pos)
                return "break"
        return None

    def _toggle_comment(self, event):
        sel = self.text.tag_ranges("sel")
        if sel:
            start, end = sel
            line_start = int(start.split(".")[0])
            line_end = int(end.split(".")[0])
        else:
            line_start = line_end = int(self.text.index(tk.INSERT).split(".")[0])
        for line in range(line_start, line_end + 1):
            text_line = self.text.get(f"{line}.0", f"{line}.end")
            if text_line.strip().startswith("#"):
                new_line = text_line.replace("#", "", 1)
            else:
                new_line = "#" + text_line
            self.text.delete(f"{line}.0", f"{line}.end")
            self.text.insert(f"{line}.0", new_line)
        self._schedule_highlight()
        return "break"

    def highlight_syntax(self):
        content = self.text.get("1.0", tk.END)
        for tag in ("keyword", "string", "comment", "number", "function", "class", "operator", "builtin", "mpmodule"):
            self.text.tag_remove(tag, "1.0", tk.END)

        # Commentaires
        for match in re.finditer(r"#.*", content):
            start, end = match.span()
            self.text.tag_add("comment", f"1.0+{start}c", f"1.0+{end}c")

        # Chaînes
        for match in re.finditer(r"([rRfFuUbB]?['\"]{3}|['\"])(?:(?!\1).|\\.)*?\1", content, re.DOTALL):
            start, end = match.span()
            self.text.tag_add("string", f"1.0+{start}c", f"1.0+{end}c")

        # Mots-clés, builtins, modules
        for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", content):
            word = match.group(1)
            start, end = match.span()
            tag = None
            if word in PYTHON_KEYWORDS:
                tag = "keyword"
            elif word in PYTHON_BUILTINS:
                tag = "builtin"
            elif word in MICROPYTHON_MODULES:
                tag = "mpmodule"
            if tag:
                self.text.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

        # Nombres
        for match in re.finditer(r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b", content):
            start, end = match.span()
            self.text.tag_add("number", f"1.0+{start}c", f"1.0+{end}c")

        # Fonctions et classes
        for match in re.finditer(r"\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\b", content):
            start = match.start(2)
            end = match.end(2)
            tag = "function" if match.group(1) == "def" else "class"
            self.text.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

        # Opérateurs
        for match in re.finditer(r"[+\-*/%=<>!&|^~]+", content):
            start, end = match.span()
            self.text.tag_add("operator", f"1.0+{start}c", f"1.0+{end}c")


# =============================================================================
# TERMINAL SÉRIE
# =============================================================================
class SerialTerminal(tk.Frame):
    def __init__(self, master, theme: Dict[str, str], serial_manager: SerialManager, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.theme = theme
        self.serial = serial_manager
        self.font = Font(family="Consolas", size=10)
        self.queue: queue.Queue[str] = queue.Queue()
        self._after_id = None

        self.text = tk.Text(
            self,
            wrap=tk.CHAR,
            font=self.font,
            bg=theme["terminal_bg"],
            fg=theme["terminal_fg"],
            insertbackground=theme["terminal_fg"],
            state=tk.DISABLED,
            borderwidth=0,
            highlightthickness=0,
            padx=4,
            pady=4,
        )
        self.scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.config(yscrollcommand=self.scroll.set)

        self.entry = ttk.Entry(self, font=self.font)
        self.entry.bind("<Return>", self._send_command)
        self.entry.bind("<Up>", self._history_up)
        self.entry.bind("<Down>", self._history_down)

        self.text.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid(row=0, column=1, sticky="ns")
        self.entry.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.history: List[str] = []
        self.history_index = -1
        self.serial.callbacks.append(self._on_data)
        self._poll_queue()

    def set_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.text.config(
            bg=theme["terminal_bg"],
            fg=theme["terminal_fg"],
            insertbackground=theme["terminal_fg"],
        )

    def _on_data(self, text: str):
        self.queue.put(text)

    def _poll_queue(self):
        try:
            while True:
                text = self.queue.get_nowait()
                self._append(text)
        except queue.Empty:
            pass
        self._after_id = self.after(50, self._poll_queue)

    def _append(self, text: str):
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, text)
        self.text.see(tk.END)
        if self.text.index("end-1c").split(".")[0] != "1":
            max_lines = 1000
            current = int(self.text.index("end-1c").split(".")[0])
            if current > max_lines:
                self.text.delete("1.0", f"{current - max_lines}.0")
        self.text.config(state=tk.DISABLED)

    def _send_command(self, event):
        cmd = self.entry.get()
        if cmd:
            self.history.append(cmd)
            self.history_index = len(self.history)
            self.entry.delete(0, tk.END)
            self._append(f">>> {cmd}\n")
            self.serial.send(cmd)

    def _history_up(self, event):
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.history[self.history_index])
        return "break"

    def _history_down(self, event):
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.history[self.history_index])
        else:
            self.history_index = len(self.history)
            self.entry.delete(0, tk.END)
        return "break"

    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)

    def destroy(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        super().destroy()


# =============================================================================
# EXPLORATEUR DE FICHIERS
# =============================================================================
class FileExplorer(tk.Frame):
    def __init__(self, master, theme: Dict[str, str], on_open: Callable[[str], None], *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.theme = theme
        self.on_open = on_open
        self.root_path: Optional[str] = None

        self.tree = ttk.Treeview(self, show="tree", selectmode="browse")
        self.scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.config(yscrollcommand=self.scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)

    def set_theme(self, theme: Dict[str, str]):
        self.theme = theme

    def set_root(self, path: str):
        self.root_path = path
        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.root_path and os.path.isdir(self.root_path):
            self._populate(self.root_path, "")

    def _populate(self, path: str, parent: str):
        try:
            entries = sorted(os.listdir(path))
        except Exception:
            return
        for entry in entries:
            if entry.startswith("."):
                continue
            full = os.path.join(path, entry)
            node = self.tree.insert(parent, tk.END, text=entry, open=False)
            if os.path.isdir(full):
                self.tree.item(node, tags=("folder",))
                self._populate(full, node)
            else:
                self.tree.item(node, tags=("file",))

    def _on_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        path = self._item_path(item[0])
        if os.path.isfile(path):
            self.on_open(path)

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            path = self._item_path(item)
            menu.add_command(label="Ouvrir", command=lambda: self.on_open(path) if os.path.isfile(path) else None)
            menu.add_command(label="Actualiser", command=self.refresh)
            menu.add_command(label="Nouveau fichier", command=self._new_file)
            menu.add_command(label="Nouveau dossier", command=self._new_folder)
            if os.path.isfile(path):
                menu.add_command(label="Supprimer", command=lambda: self._delete(path))
            menu.tk_popup(event.x_root, event.y_root)

    def _item_path(self, item) -> str:
        parts = []
        while item:
            parts.append(self.tree.item(item, "text"))
            item = self.tree.parent(item)
        if not self.root_path:
            return ""
        return os.path.join(self.root_path, *reversed(parts))

    def _new_file(self):
        name = simpledialog.askstring("Nouveau fichier", "Nom:")
        if name and self.root_path:
            path = os.path.join(self.root_path, name)
            try:
                open(path, "w").close()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def _new_folder(self):
        name = simpledialog.askstring("Nouveau dossier", "Nom:")
        if name and self.root_path:
            path = os.path.join(self.root_path, name)
            try:
                os.makedirs(path, exist_ok=True)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def _delete(self, path: str):
        if messagebox.askyesno("Confirmer", f"Supprimer {path} ?"):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    os.rmdir(path)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))


# =============================================================================
# PANNEAU DE CONTRÔLE ESP32
# =============================================================================
class ESP32ControlPanel(tk.Frame):
    def __init__(self, master, theme: Dict[str, str], serial_manager: SerialManager, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.theme = theme
        self.serial = serial_manager
        self.on_status_change: Optional[Callable[[str], None]] = None

        self.config(bg=theme["panel_bg"], highlightbackground=theme["border"], highlightthickness=1)

        ttk.Label(self, text="Port ESP32:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(self, textvariable=self.port_var, state="readonly", width=30)
        self.port_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(self, text="Baud:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.baud_var = tk.IntVar(value=DEFAULT_BAUD)
        self.baud_combo = ttk.Combobox(self, textvariable=self.baud_var, values=DEFAULT_BAUDRATES, state="readonly", width=10)
        self.baud_combo.grid(row=0, column=3, sticky="w", padx=5, pady=2)

        btn_frame = tk.Frame(self, bg=theme["panel_bg"])
        btn_frame.grid(row=1, column=0, columnspan=5, sticky="ew", padx=5, pady=4)

        self.btn_refresh = tk.Button(btn_frame, text="↻ Actualiser", command=self.refresh_ports, bg=theme["panel_bg"], fg=theme["fg"])
        self.btn_refresh.pack(side=tk.LEFT, padx=2)
        self.btn_connect = tk.Button(btn_frame, text="⏻ Connecter", command=self.toggle_connect, bg=theme["panel_bg"], fg=theme["fg"])
        self.btn_connect.pack(side=tk.LEFT, padx=2)
        self.btn_run = tk.Button(btn_frame, text="▶ Exécuter", command=self.run_code, bg=theme["panel_bg"], fg=theme["fg"])
        self.btn_run.pack(side=tk.LEFT, padx=2)
        self.btn_upload = tk.Button(btn_frame, text="⬆ Envoyer", command=self.upload_file, bg=theme["panel_bg"], fg=theme["fg"])
        self.btn_upload.pack(side=tk.LEFT, padx=2)
        self.btn_reset = tk.Button(btn_frame, text="⟲ Reset", command=self.reset_device, bg=theme["panel_bg"], fg=theme["fg"])
        self.btn_reset.pack(side=tk.LEFT, padx=2)
        self.btn_files = tk.Button(btn_frame, text="📁 Fichiers", command=self.list_files, bg=theme["panel_bg"], fg=theme["fg"])
        self.btn_files.pack(side=tk.LEFT, padx=2)
        self.btn_erase = tk.Button(btn_frame, text="🗑 Effacer", command=self.erase_flash, bg=theme["panel_bg"], fg=theme["fg"])
        self.btn_erase.pack(side=tk.LEFT, padx=2)

        self.status_var = tk.StringVar(value="Déconnecté")
        self.status_label = tk.Label(self, textvariable=self.status_var, bg=theme["panel_bg"], fg=theme["fg"], anchor="w")
        self.status_label.grid(row=2, column=0, columnspan=5, sticky="ew", padx=5, pady=2)

        self.grid_columnconfigure(1, weight=1)

        self.refresh_ports()

    def set_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.config(bg=theme["panel_bg"], highlightbackground=theme["border"])
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg=theme["panel_bg"])
        self.status_label.config(bg=theme["panel_bg"], fg=theme["fg"])
        for btn in (self.btn_refresh, self.btn_connect, self.btn_run, self.btn_upload, self.btn_reset, self.btn_files, self.btn_erase):
            btn.config(bg=theme["panel_bg"], fg=theme["fg"])

    def refresh_ports(self):
        ports = self.serial.list_ports()
        values = [f"{p['device']} - {p['description']}" for p in ports]
        self.port_combo["values"] = values
        if values:
            esp = next((v for v, p in zip(values, ports) if p["is_esp32"]), values[0])
            self.port_var.set(esp)
        else:
            self.port_var.set("")
        if self.on_status_change:
            self.on_status_change(f"{len(ports)} port(s) détecté(s)")

    def get_selected_port(self) -> str:
        text = self.port_var.get()
        return text.split(" - ")[0] if " - " in text else text

    def toggle_connect(self):
        if self.serial.connected:
            self.serial.disconnect()
            self.btn_connect.config(text="⏻ Connecter")
            self.status_var.set("Déconnecté")
            if self.on_status_change:
                self.on_status_change("Déconnecté")
        else:
            port = self.get_selected_port()
            if not port:
                messagebox.showwarning("Avertissement", "Aucun port sélectionné.")
                return
            baud = self.baud_var.get()
            if self.serial.connect(port, baud):
                self.btn_connect.config(text="⏻ Déconnecter")
                self.status_var.set(f"Connecté à {port} @ {baud} bauds")
                if self.on_status_change:
                    self.on_status_change(f"Connecté à {port} @ {baud} bauds")
                self.serial.send("\r\n")
            else:
                messagebox.showerror("Erreur", f"Connexion impossible:\n{self.serial.last_error}")
                self.status_var.set("Échec connexion")

    def run_code(self):
        if not self.serial.connected:
            messagebox.showwarning("Avertissement", "Connectez d'abord l'ESP32.")
            return
        self.event_generate("<<RunOnDevice>>")

    def upload_file(self):
        if not self.serial.connected:
            messagebox.showwarning("Avertissement", "Connectez d'abord l'ESP32.")
            return
        self.event_generate("<<UploadToDevice>>")

    def reset_device(self):
        if not self.serial.connected:
            return
        self.serial.send_reset()
        self.status_var.set("Reset envoyé")
        if self.on_status_change:
            self.on_status_change("Reset envoyé")

    def list_files(self):
        if not self.serial.connected:
            messagebox.showwarning("Avertissement", "Connectez d'abord l'ESP32.")
            return
        ok, files = self.serial.list_device_files()
        if ok:
            messagebox.showinfo("Fichiers sur l'ESP32", "\n".join(files) or "(vide)")
        else:
            messagebox.showerror("Erreur", "Impossible de lister les fichiers.")

    def erase_flash(self):
        if not self.serial.connected:
            messagebox.showwarning("Avertissement", "Connectez d'abord l'ESP32.")
            return
        if messagebox.askyesno("Confirmer", "Effacer la flash ? Cela supprime tout le contenu."):
            try:
                import esptool
                port = self.serial.port_name
                self.serial.disconnect()
                esptool.main(["--port", port, "erase_flash"])
                messagebox.showinfo("Info", "Flash effacée.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur esptool: {e}")


# =============================================================================
# BARRE D'ÉTAT
# =============================================================================
class StatusBar(tk.Frame):
    def __init__(self, master, theme: Dict[str, str], *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.theme = theme
        self.config(bg=theme["status_bg"], highlightthickness=0)

        self.label_left = tk.Label(self, text="Prêt", bg=theme["status_bg"], fg=theme["status_fg"], anchor="w")
        self.label_left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        self.label_right = tk.Label(self, text="Ligne 1, Col 1", bg=theme["status_bg"], fg=theme["status_fg"], anchor="e")
        self.label_right.pack(side=tk.RIGHT, padx=6)

    def set_theme(self, theme: Dict[str, str]):
        self.config(bg=theme["status_bg"])
        self.label_left.config(bg=theme["status_bg"], fg=theme["status_fg"])
        self.label_right.config(bg=theme["status_bg"], fg=theme["status_fg"])

    def set_text(self, text: str):
        self.label_left.config(text=text)

    def set_position(self, line: int, col: int):
        self.label_right.config(text=f"Ligne {line}, Col {col}")


# =============================================================================
# BOÎTE DE DIALOGUE RECHERCHE/REMPLACER
# =============================================================================
class FindReplaceDialog(tk.Toplevel):
    def __init__(self, parent, text_widget: tk.Text, theme: Dict[str, str]):
        super().__init__(parent)
        self.text_widget = text_widget
        self.theme = theme
        self.title("Rechercher / Remplacer")
        self.transient(parent)
        self.resizable(False, False)
        self.geometry("450x180")

        tk.Label(self, text="Rechercher:", bg=theme["bg"], fg=theme["fg"]).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.find_var = tk.StringVar()
        self.find_entry = tk.Entry(self, textvariable=self.find_var, bg=theme["panel_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        self.find_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(self, text="Remplacer:", bg=theme["bg"], fg=theme["fg"]).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.replace_var = tk.StringVar()
        self.replace_entry = tk.Entry(self, textvariable=self.replace_var, bg=theme["panel_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        self.replace_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=theme["bg"])
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)

        tk.Button(btn_frame, text="Suivant", command=self.find_next, bg=theme["panel_bg"], fg=theme["fg"]).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Précédent", command=self.find_prev, bg=theme["panel_bg"], fg=theme["fg"]).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Remplacer", command=self.replace, bg=theme["panel_bg"], fg=theme["fg"]).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Tout remplacer", command=self.replace_all, bg=theme["panel_bg"], fg=theme["fg"]).pack(side=tk.LEFT, padx=3)

        self.config(bg=theme["bg"])
        self.grid_columnconfigure(1, weight=1)
        self.last_find_pos = "1.0"

    def find_next(self):
        term = self.find_var.get()
        if not term:
            return
        pos = self.text_widget.search(term, self.last_find_pos, stopindex=tk.END, nocase=True)
        if pos:
            end = f"{pos}+{len(term)}c"
            self.text_widget.tag_remove("sel", "1.0", tk.END)
            self.text_widget.tag_add("sel", pos, end)
            self.text_widget.mark_set(tk.INSERT, end)
            self.text_widget.see(pos)
            self.last_find_pos = end
        else:
            self.last_find_pos = "1.0"

    def find_prev(self):
        term = self.find_var.get()
        if not term:
            return
        pos = self.text_widget.search(term, tk.INSERT, stopindex="1.0", backwards=True, nocase=True)
        if pos:
            end = f"{pos}+{len(term)}c"
            self.text_widget.tag_remove("sel", "1.0", tk.END)
            self.text_widget.tag_add("sel", pos, end)
            self.text_widget.mark_set(tk.INSERT, pos)
            self.text_widget.see(pos)

    def replace(self):
        term = self.find_var.get()
        repl = self.replace_var.get()
        sel = self.text_widget.tag_ranges("sel")
        if sel:
            start, end = sel
            if self.text_widget.get(start, end) == term:
                self.text_widget.delete(start, end)
                self.text_widget.insert(start, repl)
        self.find_next()

    def replace_all(self):
        term = self.find_var.get()
        repl = self.replace_var.get()
        if not term:
            return
        count = 0
        pos = "1.0"
        while True:
            p = self.text_widget.search(term, pos, stopindex=tk.END, nocase=True)
            if not p:
                break
            end = f"{p}+{len(term)}c"
            self.text_widget.delete(p, end)
            self.text_widget.insert(p, repl)
            pos = f"{p}+{len(repl)}c"
            count += 1
        messagebox.showinfo("Info", f"{count} remplacement(s) effectué(s).")


# =============================================================================
# FENÊTRE PRINCIPALE
# =============================================================================
class ESP32IDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION} - {APP_AUTHOR}")
        self.geometry("1400x900")
        self.minsize(900, 600)

        self.config = AppConfig.load()
        self.theme = THEMES.get(self.config.theme, THEMES["dark"])
        self.serial = SerialManager()
        self.find_dialog: Optional[FindReplaceDialog] = None

        self._setup_style()
        self._build_menu()
        self._build_toolbar()
        self._build_layout()
        self._build_statusbar()
        self._bind_events()
        self._load_session()
        self._start_auto_detection()

    def _setup_style(self):
        self.configure(bg=self.theme["bg"])
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=self.theme["bg"])
        style.configure("TLabel", background=self.theme["bg"], foreground=self.theme["fg"])
        style.configure("TButton", background=self.theme["panel_bg"], foreground=self.theme["fg"])
        style.configure("TEntry", fieldbackground=self.theme["panel_bg"], foreground=self.theme["fg"])
        style.configure("TCombobox", fieldbackground=self.theme["panel_bg"], foreground=self.theme["fg"])
        style.map("TCombobox", fieldbackground=[("readonly", self.theme["panel_bg"])])
        style.configure("Treeview", background=self.theme["bg"], foreground=self.theme["fg"], fieldbackground=self.theme["bg"])
        style.configure("Treeview.Heading", background=self.theme["panel_bg"], foreground=self.theme["fg"])
        style.configure("TScrollbar", background=self.theme["panel_bg"], troughcolor=self.theme["bg"])

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(label="Nouveau (Ctrl+N)", command=self.new_file)
        menu_file.add_command(label="Ouvrir (Ctrl+O)", command=self.open_file)
        menu_file.add_command(label="Enregistrer (Ctrl+S)", command=self.save_file)
        menu_file.add_command(label="Enregistrer sous...", command=self.save_file_as)
        menu_file.add_separator()
        menu_file.add_command(label="Quitter", command=self.on_close)
        menubar.add_cascade(label="Fichier", menu=menu_file)

        menu_edit = tk.Menu(menubar, tearoff=0)
        menu_edit.add_command(label="Annuler", command=lambda: self.editor.text.edit_undo())
        menu_edit.add_command(label="Rétablir", command=lambda: self.editor.text.edit_redo())
        menu_edit.add_separator()
        menu_edit.add_command(label="Couper", command=lambda: self.editor.text.event_generate("<<Cut>>"))
        menu_edit.add_command(label="Copier", command=lambda: self.editor.text.event_generate("<<Copy>>"))
        menu_edit.add_command(label="Coller", command=lambda: self.editor.text.event_generate("<<Paste>>"))
        menu_edit.add_separator()
        menu_edit.add_command(label="Rechercher / Remplacer (Ctrl+F)", command=self.show_find_replace)
        menu_edit.add_command(label="Commenter / Décommenter (Ctrl+/)", command=lambda: self.editor._toggle_comment(None))
        menubar.add_cascade(label="Édition", menu=menu_edit)

        menu_view = tk.Menu(menubar, tearoff=0)
        self.var_line_numbers = tk.BooleanVar(value=self.config.line_numbers)
        self.var_word_wrap = tk.BooleanVar(value=self.config.word_wrap)
        self.var_show_terminal = tk.BooleanVar(value=self.config.show_terminal)
        self.var_show_explorer = tk.BooleanVar(value=self.config.show_explorer)
        menu_view.add_checkbutton(label="Numéros de ligne", variable=self.var_line_numbers, command=self.toggle_line_numbers)
        menu_view.add_checkbutton(label="Retour à la ligne", variable=self.var_word_wrap, command=self.toggle_word_wrap)
        menu_view.add_checkbutton(label="Afficher terminal", variable=self.var_show_terminal, command=self.toggle_terminal)
        menu_view.add_checkbutton(label="Afficher explorateur", variable=self.var_show_explorer, command=self.toggle_explorer)
        menu_view.add_separator()
        menu_theme = tk.Menu(menu_view, tearoff=0)
        for theme_name in THEMES.keys():
            menu_theme.add_command(label=theme_name.capitalize(), command=lambda t=theme_name: self.set_theme(t))
        menu_view.add_cascade(label="Thème", menu=menu_theme)
        menu_view.add_command(label="Police...", command=self.choose_font)
        menubar.add_cascade(label="Affichage", menu=menu_view)

        menu_esp = tk.Menu(menubar, tearoff=0)
        menu_esp.add_command(label="Actualiser ports", command=self.refresh_ports)
        menu_esp.add_command(label="Connecter/Déconnecter", command=self.toggle_connection)
        menu_esp.add_separator()
        menu_esp.add_command(label="Exécuter sur ESP32", command=self.run_on_device)
        menu_esp.add_command(label="Envoyer fichier sur ESP32", command=self.upload_to_device)
        menu_esp.add_command(label="Reset ESP32", command=self.reset_device)
        menu_esp.add_command(label="Lister fichiers ESP32", command=self.list_device_files)
        menu_esp.add_separator()
        menu_esp.add_command(label="Flasher firmware MicroPython...", command=self.flash_firmware)
        menubar.add_cascade(label="ESP32", menu=menu_esp)

        menu_help = tk.Menu(menubar, tearoff=0)
        menu_help.add_command(label="Documentation MicroPython", command=lambda: self.open_url("https://docs.micropython.org"))
        menu_help.add_command(label="À propos", command=self.show_about)
        menubar.add_cascade(label="Aide", menu=menu_help)

    def _build_toolbar(self):
        self.toolbar = tk.Frame(self, bg=self.theme["panel_bg"], height=40)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        buttons = [
            ("Nouveau", self.new_file),
            ("Ouvrir", self.open_file),
            ("Enregistrer", self.save_file),
            ("|", None),
            ("Couper", lambda: self.editor.text.event_generate("<<Cut>>")),
            ("Copier", lambda: self.editor.text.event_generate("<<Copy>>")),
            ("Coller", lambda: self.editor.text.event_generate("<<Paste>>")),
            ("|", None),
            ("Exécuter", self.run_on_device),
            ("Envoyer", self.upload_to_device),
            ("Stop", self.stop_execution),
            ("Reset", self.reset_device),
            ("|", None),
            ("Thème", self.cycle_theme),
        ]
        for label, cmd in buttons:
            if label == "|":
                ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
            else:
                btn = tk.Button(self.toolbar, text=label, command=cmd, bg=self.theme["panel_bg"], fg=self.theme["fg"],
                                activebackground=self.theme["accent"], activeforeground=self.theme["fg"], relief=tk.FLAT, padx=8)
                btn.pack(side=tk.LEFT, padx=1, pady=2)

    def _build_layout(self):
        self.main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.main_paned, bg=self.theme["bg"], width=250)
        self.explorer = FileExplorer(self.left_frame, self.theme, self.open_file_from_explorer)
        self.explorer.pack(fill=tk.BOTH, expand=True)

        self.center_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)

        self.top_frame = tk.Frame(self.center_paned, bg=self.theme["bg"])
        self.esp_panel = ESP32ControlPanel(self.top_frame, self.theme, self.serial)
        self.esp_panel.pack(fill=tk.X, side=tk.TOP)
        self.esp_panel.on_status_change = self.statusbar.set_text if hasattr(self, "statusbar") else None

        self.editor = CodeEditor(self.top_frame, self.theme, self.config)
        self.editor.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        self.bottom_frame = tk.Frame(self.center_paned, bg=self.theme["bg"], height=250)
        self.terminal = SerialTerminal(self.bottom_frame, self.theme, self.serial)
        self.terminal.pack(fill=tk.BOTH, expand=True)

        self.center_paned.add(self.top_frame, weight=3)
        self.center_paned.add(self.bottom_frame, weight=1)
        self.main_paned.add(self.left_frame, weight=1)
        self.main_paned.add(self.center_paned, weight=4)

        if not self.config.show_explorer:
            self.main_paned.forget(self.left_frame)
        if not self.config.show_terminal:
            self.center_paned.forget(self.bottom_frame)

    def _build_statusbar(self):
        self.statusbar = StatusBar(self, self.theme)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.esp_panel.on_status_change = self.statusbar.set_text
        self.editor.text.bind("<KeyRelease>", self._update_cursor_position)
        self.editor.text.bind("<Button-1>", self._update_cursor_position)

    def _bind_events(self):
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<<NewFile>>", lambda e: self.new_file())
        self.bind("<<OpenFile>>", lambda e: self.open_file())
        self.bind("<<SaveFile>>", lambda e: self.save_file())
        self.bind("<<FindReplace>>", lambda e: self.show_find_replace())
        self.bind("<<RunOnDevice>>", lambda e: self.run_on_device())
        self.bind("<<UploadToDevice>>", lambda e: self.upload_to_device())
        self.bind("<<FileModified>>", lambda e: self._update_title())

    def _load_session(self):
        if self.config.last_project and os.path.isdir(self.config.last_project):
            self.explorer.set_root(self.config.last_project)
            self.statusbar.set_text(f"Projet: {self.config.last_project}")
        if self.config.recent_files and os.path.exists(self.config.recent_files[-1]):
            self.open_file_from_explorer(self.config.recent_files[-1])

    def _start_auto_detection(self):
        if self.config.auto_detect:
            self._detect_and_maybe_connect()
        self._schedule_auto_detect()

    def _schedule_auto_detect(self):
        self._auto_detect_id = self.after(2000, self._auto_detect_tick)

    def _auto_detect_tick(self):
        self._detect_and_maybe_connect()
        self._schedule_auto_detect()

    def _detect_and_maybe_connect(self):
        if self.serial.connected:
            return
        port = self.serial.detect_esp32_port()
        if port:
            self.esp_panel.port_var.set(f"{port} - ESP32 détecté")
            if self.config.auto_connect:
                if self.serial.connect(port, self.config.baudrate):
                    self.esp_panel.btn_connect.config(text="⏻ Déconnecter")
                    self.esp_panel.status_var.set(f"Auto-connecté à {port}")
                    self.statusbar.set_text(f"ESP32 détecté et connecté sur {port}")
                    self.serial.send("\r\n")
        else:
            self.statusbar.set_text("ESP32 non détecté")

    def _update_cursor_position(self, event=None):
        pos = self.editor.text.index(tk.INSERT)
        line, col = pos.split(".")
        self.statusbar.set_position(int(line), int(col))

    def _update_title(self):
        mod = "*" if self.editor.modified else ""
        title = f"{mod}{self.editor.filename} - {APP_NAME} v{APP_VERSION} - {APP_AUTHOR}"
        self.title(title)

    def new_file(self):
        self.editor.filepath = None
        self.editor.filename = "sans_titre.py"
        self.editor.set_content("")
        self.editor.modified = False
        self._update_title()

    def open_file(self):
        path = filedialog.askopenfilename(
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("MicroPython", "*.mpy"), ("Tous", "*.*")],
        )
        if path:
            self.open_file_from_explorer(path)

    def open_file_from_explorer(self, path: str):
        if not os.path.isfile(path):
            return
        self.editor.load_file(path)
        self._add_recent_file(path)
        self._update_title()
        self.statusbar.set_text(f"Ouvert: {path}")

    def save_file(self):
        if not self.editor.filepath:
            return self.save_file_as()
        if self.editor.save_file(self.editor.filepath):
            self._update_title()
            self.statusbar.set_text(f"Enregistré: {self.editor.filepath}")
            return True
        return False

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("Tous", "*.*")],
        )
        if path:
            if self.editor.save_file(path):
                self._add_recent_file(path)
                self._update_title()
                self.statusbar.set_text(f"Enregistré sous: {path}")
                return True
        return False

    def _add_recent_file(self, path: str):
        if path in self.config.recent_files:
            self.config.recent_files.remove(path)
        self.config.recent_files.insert(0, path)
        self.config.recent_files = self.config.recent_files[:10]

    def show_find_replace(self):
        if self.find_dialog and self.find_dialog.winfo_exists():
            self.find_dialog.lift()
            return
        self.find_dialog = FindReplaceDialog(self, self.editor.text, self.theme)

    def toggle_line_numbers(self):
        self.config.line_numbers = self.var_line_numbers.get()
        if self.config.line_numbers:
            self.editor.line_numbers.grid()
        else:
            self.editor.line_numbers.grid_remove()

    def toggle_word_wrap(self):
        self.config.word_wrap = self.var_word_wrap.get()
        self.editor.text.config(wrap=tk.WORD if self.config.word_wrap else tk.NONE)

    def toggle_terminal(self):
        self.config.show_terminal = self.var_show_terminal.get()
        if self.config.show_terminal:
            self.center_paned.add(self.bottom_frame, weight=1)
        else:
            self.center_paned.forget(self.bottom_frame)

    def toggle_explorer(self):
        self.config.show_explorer = self.var_show_explorer.get()
        if self.config.show_explorer:
            self.main_paned.add(self.left_frame, weight=1)
        else:
            self.main_paned.forget(self.left_frame)

    def set_theme(self, theme_name: str):
        if theme_name not in THEMES:
            return
        self.config.theme = theme_name
        self.theme = THEMES[theme_name]
        self._setup_style()
        self.configure(bg=self.theme["bg"])
        self.toolbar.config(bg=self.theme["panel_bg"])
        for child in self.toolbar.winfo_children():
            if isinstance(child, tk.Button):
                child.config(bg=self.theme["panel_bg"], fg=self.theme["fg"],
                             activebackground=self.theme["accent"])
        self.editor.set_theme(self.theme)
        self.terminal.set_theme(self.theme)
        self.explorer.set_theme(self.theme)
        self.esp_panel.set_theme(self.theme)
        self.statusbar.set_theme(self.theme)

    def cycle_theme(self):
        names = list(THEMES.keys())
        idx = names.index(self.config.theme) if self.config.theme in names else 0
        self.set_theme(names[(idx + 1) % len(names)])

    def choose_font(self):
        from tkinter.font import families
        dialog = tk.Toplevel(self)
        dialog.title("Police")
        dialog.transient(self)
        dialog.config(bg=self.theme["bg"])
        tk.Label(dialog, text="Famille:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, padx=5, pady=5)
        family_var = tk.StringVar(value=self.config.font_family)
        family_combo = ttk.Combobox(dialog, textvariable=family_var, values=sorted(families()), state="readonly", width=30)
        family_combo.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(dialog, text="Taille:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=1, column=0, padx=5, pady=5)
        size_var = tk.IntVar(value=self.config.font_size)
        size_spin = tk.Spinbox(dialog, from_=6, to=72, textvariable=size_var, width=10)
        size_spin.grid(row=1, column=1, padx=5, pady=5)

        def apply():
            self.config.font_family = family_var.get()
            self.config.font_size = size_var.get()
            self.editor.set_font(self.config.font_family, self.config.font_size)
            dialog.destroy()

        tk.Button(dialog, text="Appliquer", command=apply, bg=self.theme["panel_bg"], fg=self.theme["fg"]).grid(row=2, column=0, columnspan=2, pady=10)

    def refresh_ports(self):
        self.esp_panel.refresh_ports()

    def toggle_connection(self):
        self.esp_panel.toggle_connect()

    def run_on_device(self):
        if not self.serial.connected:
            messagebox.showwarning("Avertissement", "Connectez d'abord l'ESP32.")
            return
        code = self.editor.get_content()
        if not code.strip():
            messagebox.showinfo("Info", "Le code est vide.")
            return
        self.terminal._append("\n--- Exécution sur ESP32 ---\n")

        def task():
            ok, out = self.serial.execute_on_device(code, timeout=15.0)
            self.after(0, lambda: self._execution_done(ok, out))

        threading.Thread(target=task, daemon=True).start()

    def _execution_done(self, ok: bool, output: str):
        self.terminal._append(output)
        self.terminal._append("--- Fin exécution ---\n")
        self.statusbar.set_text("Exécution terminée" if ok else "Erreur d'exécution")

    def upload_to_device(self):
        if not self.serial.connected:
            messagebox.showwarning("Avertissement", "Connectez d'abord l'ESP32.")
            return
        if not self.editor.filepath:
            if not self.save_file_as():
                return
        remote_name = simpledialog.askstring("Envoyer sur ESP32", "Nom distant:", initialvalue=self.editor.filename)
        if not remote_name:
            return
        self.terminal._append(f"\n--- Envoi de {self.editor.filename} vers {remote_name} ---\n")

        def task():
            ok, out = self.serial.put_file(self.editor.filepath, remote_name, timeout=20.0)
            self.after(0, lambda: self._upload_done(ok, out, remote_name))

        threading.Thread(target=task, daemon=True).start()

    def _upload_done(self, ok: bool, output: str, remote_name: str):
        self.terminal._append(output)
        self.terminal._append("--- Fin envoi ---\n")
        if ok:
            self.statusbar.set_text(f"{remote_name} envoyé avec succès")
        else:
            self.statusbar.set_text("Échec de l'envoi")

    def stop_execution(self):
        self.serial.send_interrupt()
        self.terminal._append("\n[INTERRUPTION]\n")

    def reset_device(self):
        self.serial.send_reset()
        self.terminal._append("\n[RESET]\n")

    def list_device_files(self):
        if not self.serial.connected:
            messagebox.showwarning("Avertissement", "Connectez d'abord l'ESP32.")
            return
        ok, files = self.serial.list_device_files()
        if ok:
            messagebox.showinfo("Fichiers sur l'ESP32", "\n".join(files) or "(vide)")
        else:
            messagebox.showerror("Erreur", "Impossible de lister les fichiers.")

    def flash_firmware(self):
        path = filedialog.askopenfilename(filetypes=[("Firmware", "*.bin")])
        if not path:
            return
        port = self.esp_panel.get_selected_port()
        if not port:
            messagebox.showerror("Erreur", "Aucun port sélectionné.")
            return
        if messagebox.askyesno("Confirmer", f"Flasher {path} sur {port} ?"):
            try:
                import esptool
                self.serial.disconnect()
                esptool.main(["--chip", "esp32", "--port", port, "write_flash", "-z", "0x1000", path])
                messagebox.showinfo("Info", "Flash terminée.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur flash: {e}")

    def open_url(self, url: str):
        import webbrowser
        webbrowser.open(url)

    def show_about(self):
        messagebox.showinfo(
            "À propos",
            f"{APP_NAME}\nVersion: {APP_VERSION}\nAuteur: {APP_AUTHOR}\nDate: 2026\n\n"
            "IDE graphique pour développement MicroPython sur ESP32.\n"
            "Détection automatique, édition, exécution et envoi de fichiers."
        )

    def on_close(self):
        if self.editor.modified:
            r = messagebox.askyesnocancel("Quitter", "Le fichier a été modifié. Voulez-vous l'enregistrer ?")
            if r is True:
                if not self.save_file():
                    return
            elif r is None:
                return
        if self._auto_detect_id:
            self.after_cancel(self._auto_detect_id)
        self.serial.disconnect()
        self.config.save()
        self.destroy()


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================
def main():
    if sys.platform.startswith("win"):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    app = ESP32IDE()
    app.mainloop()


if __name__ == "__main__":
    main()
