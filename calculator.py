import ctypes
import tkinter as tk
import tkinter.font as tkfont

# 声明 DPI 感知，解决 Windows 高分屏下模糊问题
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


def _get_dpi_scale(root):
    """获取系统 DPI 缩放倍数"""
    try:
        return root.winfo_fpixels('1i') / 72.0
    except Exception:
        return 1.0


class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("计算器")
        self.root.resizable(True, True)
        self.root.configure(bg="#ffffff")

        self._dpi_scale = _get_dpi_scale(root)
        # 用 DPI 缩放倍数调整初始窗口大小
        w = int(420 * self._dpi_scale)
        h = int(600 * self._dpi_scale)
        mw = int(320 * self._dpi_scale)
        mh = int(480 * self._dpi_scale)
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(mw, mh)

        self.expression = ""
        self.display_var = tk.StringVar(value="0")
        self.sub_display_var = tk.StringVar(value="")
        self.new_number = True
        self._is_fullscreen = False
        self._mode = "calc"  # "calc" or "base"

        # Font objects (updated on resize)
        self.font_sub = tkfont.Font(family="Segoe UI", size=11)
        self.font_main = tkfont.Font(family="Segoe UI", size=28, weight="bold")
        self.font_btn = tkfont.Font(family="Segoe UI", size=13)
        self.font_base_label = tkfont.Font(family="Segoe UI", size=10)
        self.font_base_value = tkfont.Font(family="Segoe UI", size=13, weight="bold")

        self._build_ui()
        self._build_base_ui()
        self.root.state("zoomed")
        self.root.bind("<Key>", self._key_press)
        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<F11>", self._toggle_fullscreen)

    def _build_ui(self):
        # Root grid: 3 rows — tab bar + display/panel + buttons
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=2)
        self.root.grid_rowconfigure(2, weight=5)
        self.root.grid_columnconfigure(0, weight=1)

        # --- Tab bar ---
        self.tab_frame = tk.Frame(self.root, bg="#e8e8e8")
        self.tab_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        self.tab_calc = tk.Button(
            self.tab_frame, text="计算器", font=self.font_sub,
            bg="#ffffff", fg="#1a73e8", relief="flat", cursor="hand2",
            command=lambda: self._switch_mode("calc"),
        )
        self.tab_calc.pack(side="left", padx=(4, 2), pady=4, ipadx=12, ipady=2)
        self.tab_base = tk.Button(
            self.tab_frame, text="进制转换", font=self.font_sub,
            bg="#e8e8e8", fg="#555555", relief="flat", cursor="hand2",
            command=lambda: self._switch_mode("base"),
        )
        self.tab_base.pack(side="left", padx=(2, 4), pady=4, ipadx=12, ipady=2)

        # --- Display area ---
        self.display_frame = tk.Frame(self.root, bg="#ffffff")
        self.display_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 4))
        self.display_frame.grid_rowconfigure(0, weight=1)
        self.display_frame.grid_rowconfigure(1, weight=2)
        self.display_frame.grid_columnconfigure(0, weight=1)

        self.sub_label = tk.Label(
            self.display_frame,
            textvariable=self.sub_display_var,
            font=self.font_sub,
            bg="#ffffff",
            fg="#999999",
            anchor="e",
        )
        self.sub_label.grid(row=0, column=0, sticky="sew")

        self.main_label = tk.Label(
            self.display_frame,
            textvariable=self.display_var,
            font=self.font_main,
            bg="#ffffff",
            fg="#1a1a1a",
            anchor="e",
        )
        self.main_label.grid(row=1, column=0, sticky="sew")

        # --- Button grid ---
        self.btn_frame = tk.Frame(self.root, bg="#ffffff")
        self.btn_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)

        COLS, ROWS = 4, 5
        for c in range(COLS):
            self.btn_frame.grid_columnconfigure(c, weight=1)
        for r in range(ROWS):
            self.btn_frame.grid_rowconfigure(r, weight=1)

        # (label, row, col, colspan, style)
        buttons = [
            ("CE",  0, 0, 1, "fn"),
            ("C",   0, 1, 1, "fn"),
            ("⌫",  0, 2, 2, "fn"),
            ("7",   1, 0, 1, "num"),
            ("8",   1, 1, 1, "num"),
            ("9",   1, 2, 1, "num"),
            ("×",   1, 3, 1, "op"),
            ("4",   2, 0, 1, "num"),
            ("5",   2, 1, 1, "num"),
            ("6",   2, 2, 1, "num"),
            ("−",   2, 3, 1, "op"),
            ("1",   3, 0, 1, "num"),
            ("2",   3, 1, 1, "num"),
            ("3",   3, 2, 1, "num"),
            ("+",   3, 3, 1, "op"),
            ("0",   4, 0, 2, "num"),
            (".",   4, 2, 1, "num"),
            ("=",   4, 3, 1, "eq"),
        ]

        self.styles = {
            "num": {"bg": "#f2f2f2", "fg": "#1a1a1a", "active_bg": "#e0e0e0"},
            "op":  {"bg": "#e8f0fe", "fg": "#1a73e8", "active_bg": "#d2e3fc"},
            "fn":  {"bg": "#ffffff", "fg": "#555555", "active_bg": "#f2f2f2"},
            "eq":  {"bg": "#1a73e8", "fg": "#ffffff", "active_bg": "#1558b0"},
        }

        self.buttons = {}
        for (label, row, col, colspan, style) in buttons:
            s = self.styles[style]
            btn = tk.Button(
                self.btn_frame,
                text=label,
                font=self.font_btn,
                bg=s["bg"],
                fg=s["fg"],
                activebackground=s["active_bg"],
                activeforeground=s["fg"],
                relief="flat",
                cursor="hand2",
                command=lambda l=label: self._on_button(l),
            )
            btn.grid(
                row=row, column=col, columnspan=colspan,
                padx=4, pady=4, sticky="nsew",
            )
            self.buttons[label] = btn

    def _build_base_ui(self):
        """构建进制转换界面"""
        # --- 进制转换主面板 ---
        self.base_frame = tk.Frame(self.root, bg="#ffffff")
        # 不立即 grid，切换模式时再显示

        self.base_frame.grid_columnconfigure(0, weight=1)

        # 当前输入进制选择
        self._base_input = tk.StringVar(value="10")
        self._base_input_str = tk.StringVar(value="0")

        bases = [("二进制", "2"), ("八进制", "8"), ("十进制", "10"), ("十六进制", "16")]

        select_frame = tk.Frame(self.base_frame, bg="#ffffff")
        select_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        tk.Label(select_frame, text="输入进制：", font=self.font_sub,
                 bg="#ffffff", fg="#555555").pack(side="left")
        for name, val in bases:
            rb = tk.Radiobutton(
                select_frame, text=name, variable=self._base_input, value=val,
                font=self.font_sub, bg="#ffffff", fg="#1a1a1a",
                activebackground="#ffffff", selectcolor="#ffffff",
                command=self._base_convert,
            )
            rb.pack(side="left", padx=6)

        # 输入框
        input_frame = tk.Frame(self.base_frame, bg="#ffffff")
        input_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        input_frame.grid_columnconfigure(0, weight=1)

        self.base_entry = tk.Label(
            input_frame, textvariable=self._base_input_str,
            font=self.font_base_value, bg="#f2f2f2", fg="#1a1a1a",
            anchor="e", padx=12, pady=8,
        )
        self.base_entry.grid(row=0, column=0, sticky="ew", ipady=4, padx=(0, 8))

        base_clear_btn = tk.Button(
            input_frame, text="C", font=self.font_sub,
            bg="#e8e8e8", fg="#555555", relief="flat", cursor="hand2",
            command=self._base_clear,
        )
        base_clear_btn.grid(row=0, column=1, ipadx=10, ipady=4)

        # 结果显示区域
        self._base_results = {}
        result_frame = tk.Frame(self.base_frame, bg="#ffffff")
        result_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(12, 8))
        result_frame.grid_columnconfigure(1, weight=1)
        self.base_frame.grid_rowconfigure(2, weight=1)

        labels = [("二进制 (BIN)", "2"), ("八进制 (OCT)", "8"),
                  ("十进制 (DEC)", "10"), ("十六进制 (HEX)", "16")]
        for i, (name, base) in enumerate(labels):
            tk.Label(result_frame, text=name, font=self.font_base_label,
                     bg="#ffffff", fg="#888888", anchor="w").grid(
                row=i, column=0, sticky="w", pady=6, padx=(0, 12))
            var = tk.StringVar(value="0")
            lbl = tk.Label(result_frame, textvariable=var, font=self.font_base_value,
                           bg="#f8f8f8", fg="#1a1a1a", anchor="e", relief="flat",
                           padx=12, pady=6)
            lbl.grid(row=i, column=1, sticky="ew", pady=6)
            self._base_results[base] = var

        # 进制转换的按钮键盘
        self.base_btn_frame = tk.Frame(self.root, bg="#ffffff")
        self.base_btn_frame.grid_columnconfigure(0, weight=1)
        self.base_btn_frame.grid_columnconfigure(1, weight=1)
        self.base_btn_frame.grid_columnconfigure(2, weight=1)
        self.base_btn_frame.grid_columnconfigure(3, weight=1)
        for r in range(5):
            self.base_btn_frame.grid_rowconfigure(r, weight=1)

        base_buttons = [
            ("D", 0, 0), ("E", 0, 1), ("F", 0, 2), ("⌫", 0, 3),
            ("A", 1, 0), ("B", 1, 1), ("C", 1, 2), ("清空", 1, 3),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2),
            ("0", 4, 3),
        ]
        for (label, row, col) in base_buttons:
            if label in "0123456789":
                style = "num"
            elif label in "ABCDEF":
                style = "op"
            else:
                style = "fn"
            s = self.styles[style]
            btn = tk.Button(
                self.base_btn_frame, text=label, font=self.font_btn,
                bg=s["bg"], fg=s["fg"], activebackground=s["active_bg"],
                activeforeground=s["fg"], relief="flat", cursor="hand2",
                command=lambda l=label: self._base_btn_press(l),
            )
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

    def _switch_mode(self, mode):
        if mode == self._mode:
            return
        self._mode = mode
        if mode == "calc":
            self.tab_calc.configure(bg="#ffffff", fg="#1a73e8")
            self.tab_base.configure(bg="#e8e8e8", fg="#555555")
            self.base_frame.grid_forget()
            self.base_btn_frame.grid_forget()
            self.display_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 4))
            self.btn_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        else:
            self.tab_calc.configure(bg="#e8e8e8", fg="#555555")
            self.tab_base.configure(bg="#ffffff", fg="#1a73e8")
            self.display_frame.grid_forget()
            self.btn_frame.grid_forget()
            self.base_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
            self.base_btn_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
            self._base_convert()

    def _base_clear(self):
        self._base_input_str.set("0")
        self._base_convert()

    def _base_btn_press(self, label):
        if label == "⌫":
            cur = self._base_input_str.get()
            if len(cur) > 1:
                self._base_input_str.set(cur[:-1])
            else:
                self._base_input_str.set("0")
        elif label == "清空":
            self._base_clear()
        else:
            ch = label.upper()
            cur = self._base_input_str.get()
            if cur == "0":
                self._base_input_str.set(ch)
            else:
                self._base_input_str.set(cur + ch)
        self._base_convert()

    def _base_convert(self):
        """根据输入的进制和值，转换并显示所有进制的结果"""
        text = self._base_input_str.get().strip().upper()
        base = int(self._base_input.get())
        try:
            if not text or text == "0":
                value = 0
            else:
                value = int(text, base)
            self._base_results["2"].set(bin(value)[2:])
            self._base_results["8"].set(oct(value)[2:])
            self._base_results["10"].set(str(value))
            self._base_results["16"].set(hex(value)[2:].upper())
        except ValueError:
            for v in self._base_results.values():
                v.set("无效输入")

    # ── Fullscreen & resize ──────────────────────────────────────────────────

    def _toggle_fullscreen(self, event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.root.attributes("-fullscreen", self._is_fullscreen)

    def _on_resize(self, event):
        if event.widget is not self.root:
            return
        # 归一化到逻辑像素（消除 DPI 影响）
        s = self._dpi_scale
        w = event.width / s
        h = event.height / s
        # Scale fonts proportionally to logical window size
        btn_size  = max(10, min(int(h / 28), int(w / 14)))
        main_size = max(18, min(int(h / 12), int(w / 7)))
        sub_size  = max(9,  min(int(h / 36), int(w / 20)))
        self.font_btn.configure(size=btn_size)
        self.font_main.configure(size=main_size)
        self.font_sub.configure(size=sub_size)
        base_label_size = max(9, min(int(h / 40), int(w / 24)))
        base_value_size = max(11, min(int(h / 30), int(w / 20)))
        self.font_base_label.configure(size=base_label_size)
        self.font_base_value.configure(size=base_value_size)

    # ── Logic ────────────────────────────────────────────────────────────────

    def _get_display(self):
        return self.display_var.get()

    def _set_display(self, val):
        s = str(val)
        if len(s) > 15:
            try:
                s = f"{float(s):.10g}"
            except Exception:
                s = s[:15]
        self.display_var.set(s)

    def _on_button(self, label):
        d = self._get_display()

        if label.isdigit():
            if self.new_number or d == "0":
                self._set_display(label)
                self.new_number = False
            else:
                if len(d.replace("-", "").replace(".", "")) < 15:
                    self._set_display(d + label)

        elif label == ".":
            if self.new_number:
                self._set_display("0.")
                self.new_number = False
            elif "." not in d:
                self._set_display(d + ".")

        elif label in ("+", "−", "×", "÷"):
            self._store_operation(label)

        elif label == "=":
            self._calculate()

        elif label == "C":
            self.expression = ""
            self._set_display("0")
            self.sub_display_var.set("")
            self.new_number = True

        elif label == "CE":
            self._set_display("0")
            self.new_number = True

        elif label == "⌫":
            if not self.new_number and len(d) > 1:
                self._set_display(d[:-1])
            else:
                self._set_display("0")
                self.new_number = True

    def _store_operation(self, op):
        d = self._get_display()
        op_map = {"÷": "/", "×": "*", "−": "-", "+": "+"}
        self.expression = d + op_map[op]
        self.sub_display_var.set(d + " " + op + " ")
        self.new_number = True

    def _calculate(self):
        if not self.expression:
            return
        d = self._get_display()
        self.sub_display_var.set(self.sub_display_var.get() + d + " =")
        try:
            result = eval(self.expression + d)
            self._set_display(self._fmt(result))
        except ZeroDivisionError:
            self._set_display("除数不能为零")
        except Exception:
            self._set_display("错误")
        self.expression = ""
        self.new_number = True

    def _fmt(self, val):
        if isinstance(val, float):
            if val == int(val) and abs(val) < 1e15:
                return str(int(val))
            return f"{val:.10g}"
        return str(val)

    def _key_press(self, event):
        if self._mode == "base":
            self._base_key_press(event)
            return
        key_map = {
            "/": "÷", "*": "×", "-": "−",
            "+": "+", "=": "=", "\r": "=",
            "\x08": "⌫",
        }
        key = event.char
        if key.isdigit() or key == ".":
            self._on_button(key)
        elif key in key_map:
            self._on_button(key_map[key])
        elif event.keysym == "Escape":
            if self._is_fullscreen:
                self._toggle_fullscreen()
            else:
                self._on_button("C")
        elif event.keysym == "Delete":
            self._on_button("CE")

    def _base_key_press(self, event):
        key = event.char.upper()
        if key in "0123456789ABCDEF":
            self._base_btn_press(key)
        elif event.char == "\x08":
            self._base_btn_press("⌫")
        elif event.keysym == "Escape":
            if self._is_fullscreen:
                self._toggle_fullscreen()
            else:
                self._base_clear()


if __name__ == "__main__":
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()
