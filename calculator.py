import tkinter as tk
import tkinter.font as tkfont

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("计算器")
        self.root.resizable(True, True)
        self.root.configure(bg="#ffffff")
        self.root.geometry("420x600")
        self.root.minsize(320, 480)

        self.expression = ""
        self.display_var = tk.StringVar(value="0")
        self.sub_display_var = tk.StringVar(value="")
        self.new_number = True
        self._is_fullscreen = False

        # Font objects (updated on resize)
        self.font_sub = tkfont.Font(family="Segoe UI", size=13)
        self.font_main = tkfont.Font(family="Segoe UI", size=40, weight="bold")
        self.font_btn = tkfont.Font(family="Segoe UI", size=15)

        self._build_ui()
        self.root.bind("<Key>", self._key_press)
        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<F11>", self._toggle_fullscreen)

    def _build_ui(self):
        # Root grid: 2 rows — display + buttons
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=4)
        self.root.grid_columnconfigure(0, weight=1)

        # --- Display area ---
        self.display_frame = tk.Frame(self.root, bg="#ffffff")
        self.display_frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=(12, 4))
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
        self.btn_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

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

    # ── Fullscreen & resize ──────────────────────────────────────────────────

    def _toggle_fullscreen(self, event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.root.attributes("-fullscreen", self._is_fullscreen)

    def _on_resize(self, event):
        if event.widget is not self.root:
            return
        w, h = event.width, event.height
        # Scale fonts proportionally to window size
        btn_size  = max(10, min(int(h / 28), int(w / 14)))
        main_size = max(18, min(int(h / 12), int(w / 7)))
        sub_size  = max(9,  min(int(h / 36), int(w / 20)))
        self.font_btn.configure(size=btn_size)
        self.font_main.configure(size=main_size)
        self.font_sub.configure(size=sub_size)

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


if __name__ == "__main__":
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()
