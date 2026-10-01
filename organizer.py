import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font as tkfont

try:  # crisp text on Windows high-DPI screens
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


# ============================================================
# CATEGORIES  (extensions + colour used everywhere in the UI)
# ============================================================

FILE_CATEGORIES = {
    "Images":       [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "Videos":       [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
    "Music":        [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "Documents":    [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx"],
    "Archives":     [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Applications": [".exe", ".msi"],
}

CATEGORY_COLORS = {
    "Images":       "#ec4899",
    "Videos":       "#f97316",
    "Music":        "#8b5cf6",
    "Documents":    "#3b82f6",
    "Archives":     "#eab308",
    "Applications": "#10b981",
    "Others":       "#94a3b8",
}

# ============================================================
# THEME
# ============================================================

SIDEBAR_BG = "#1b1f3b"
SIDEBAR_CARD = "#272c52"
SIDEBAR_TEXT = "#f1f2fa"
SIDEBAR_MUTED = "#9aa0c7"

BG = "#f1f3f8"
CARD = "#ffffff"
TEXT = "#1e2235"
MUTED = "#6b7190"
BORDER = "#e1e5ef"
ACCENT = "#4f46e5"
ACCENT_HOVER = "#4338ca"
SUCCESS = "#16a34a"
SUCCESS_HOVER = "#15803d"
NEUTRAL = "#e4e7f1"
NEUTRAL_HOVER = "#d5d9e8"


# ============================================================
# HELPERS
# ============================================================

def get_category(extension):
    for category, extensions in FILE_CATEGORIES.items():
        if extension.lower() in extensions:
            return category
    return "Others"


def format_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024


def scan_folder(folder):
    """Return [(filename, category, size)] for files directly inside folder."""
    items = []
    for name in sorted(os.listdir(folder), key=str.lower):
        path = os.path.join(folder, name)
        if os.path.isdir(path) or name.startswith("."):
            continue
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        items.append((name, get_category(os.path.splitext(name)[1]), size))
    return items


class FlatButton(tk.Label):
    """A flat button with hover and disabled states."""

    def __init__(self, parent, text, command, bg, hover, fg="white", **kw):
        super().__init__(parent, text=text, bg=bg, fg=fg, cursor="hand2",
                         padx=kw.pop("padx", 22), pady=kw.pop("pady", 10), **kw)
        self._bg, self._hover, self._fg, self._cmd = bg, hover, fg, command
        self._enabled = True
        self.bind("<Enter>", lambda e: self._enabled and self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self._enabled and self.config(bg=self._bg))
        self.bind("<Button-1>", lambda e: self._enabled and self._cmd())

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.config(
            bg=self._bg if enabled else NEUTRAL,
            fg=self._fg if enabled else "#a3a8c0",
            cursor="hand2" if enabled else "arrow",
        )


# ============================================================
# APPLICATION
# ============================================================

class FileOrganizerApp:

    def __init__(self, root):
        self.root = root
        self.preview = []             # [(name, category, size)]
        self.last_operation = []      # [{"original", "destination"}]
        self.created_dirs = set()     # category folders created by the last run
        self.folder = tk.StringVar()
        self.filter_text = tk.StringVar()
        self.filter_text.trace_add("write", lambda *_: self.fill_table())
        self.legend_counts = {}

        families = set(tkfont.families())
        self.font = next((f for f in ("Segoe UI", "SF Pro Text", "Inter", "Helvetica Neue", "Arial")
                          if f in families), "Helvetica")

        root.title("Smart File Organizer")
        root.geometry("1100x700")
        root.minsize(980, 620)
        root.configure(bg=BG)

        self.setup_styles()
        self.build_sidebar()
        self.build_main()

        root.bind("<Control-o>", lambda e: self.select_folder())
        root.bind("<Control-z>", lambda e: self.undo_last_organization())

    # --------------------------------------------------------
    # Styles
    # --------------------------------------------------------

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=CARD, foreground=TEXT, rowheight=36,
                        fieldbackground=CARD, borderwidth=0, font=(self.font, 10))
        style.configure("Treeview.Heading", font=(self.font, 9, "bold"), background=CARD,
                        foreground=MUTED, relief="flat", padding=(10, 10), borderwidth=0)
        style.map("Treeview", background=[("selected", "#e8e9fd")],
                  foreground=[("selected", TEXT)])
        style.map("Treeview.Heading", background=[("active", CARD)])
        style.configure("Accent.Horizontal.TProgressbar", troughcolor=NEUTRAL,
                        background=ACCENT, thickness=6, borderwidth=0)
        style.configure("Vertical.TScrollbar", background=NEUTRAL, troughcolor=CARD,
                        borderwidth=0, arrowsize=0)

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------

    def build_sidebar(self):
        side = tk.Frame(self.root, bg=SIDEBAR_BG, width=300)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        # Brand
        brand = tk.Frame(side, bg=SIDEBAR_BG)
        brand.pack(fill="x", padx=26, pady=(30, 4))
        logo = tk.Canvas(brand, width=34, height=34, bg=SIDEBAR_BG, highlightthickness=0)
        logo.pack(side="left")
        for i, color in enumerate(("#ec4899", "#8b5cf6", "#3b82f6")):
            logo.create_rectangle(2, 4 + i * 10, 32 - i * 7, 11 + i * 10, fill=color, outline="")
        tk.Label(brand, text="Smart File\nOrganizer", justify="left", bg=SIDEBAR_BG,
                 fg=SIDEBAR_TEXT, font=(self.font, 13, "bold")).pack(side="left", padx=12)

        # Folder
        tk.Label(side, text="Folder", bg=SIDEBAR_BG, fg=SIDEBAR_MUTED,
                 font=(self.font, 9, "bold")).pack(anchor="w", padx=26, pady=(34, 8))
        folder_card = tk.Frame(side, bg=SIDEBAR_CARD)
        folder_card.pack(fill="x", padx=26)
        self.folder_label = tk.Label(folder_card, text="No folder selected", bg=SIDEBAR_CARD,
                                     fg=SIDEBAR_TEXT, font=(self.font, 10), anchor="w",
                                     justify="left", wraplength=210)
        self.folder_label.pack(fill="x", padx=14, pady=(12, 12))
        FlatButton(side, "Choose folder", self.select_folder, ACCENT, ACCENT_HOVER,
                   font=(self.font, 10, "bold")).pack(fill="x", padx=26, pady=(10, 0))

        # Legend with live counts
        tk.Label(side, text="File types", bg=SIDEBAR_BG, fg=SIDEBAR_MUTED,
                 font=(self.font, 9, "bold")).pack(anchor="w", padx=26, pady=(34, 8))
        legend = tk.Frame(side, bg=SIDEBAR_BG)
        legend.pack(fill="x", padx=26)
        self.legend_labels = {}
        for category, color in CATEGORY_COLORS.items():
            row = tk.Frame(legend, bg=SIDEBAR_BG)
            row.pack(fill="x", pady=4)
            dot = tk.Canvas(row, width=12, height=12, bg=SIDEBAR_BG, highlightthickness=0)
            dot.create_oval(1, 1, 11, 11, fill=color, outline="")
            dot.pack(side="left")
            tk.Label(row, text=category, bg=SIDEBAR_BG, fg=SIDEBAR_TEXT,
                     font=(self.font, 10)).pack(side="left", padx=10)
            count = tk.Label(row, text="0", bg=SIDEBAR_BG, fg=SIDEBAR_MUTED,
                             font=(self.font, 10, "bold"))
            count.pack(side="right")
            self.legend_labels[category] = count

        tk.Label(side, text="Nothing moves until you press Organize.\nYou can undo the last run.",
                 bg=SIDEBAR_BG, fg=SIDEBAR_MUTED, font=(self.font, 9), justify="left"
                 ).pack(side="bottom", anchor="w", padx=26, pady=26)

    # --------------------------------------------------------
    # Main area
    # --------------------------------------------------------

    def build_main(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(side="left", fill="both", expand=True, padx=36, pady=30)

        # Header row
        head = tk.Frame(main, bg=BG)
        head.pack(fill="x")
        title_box = tk.Frame(head, bg=BG)
        title_box.pack(side="left")
        tk.Label(title_box, text="Organization preview", bg=BG, fg=TEXT,
                 font=(self.font, 20, "bold")).pack(anchor="w")
        self.count_label = tk.Label(title_box, text="Choose a folder to begin", bg=BG,
                                    fg=MUTED, font=(self.font, 10))
        self.count_label.pack(anchor="w", pady=(2, 0))

        search = tk.Frame(head, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        search.pack(side="right")
        tk.Label(search, text="Filter", bg=CARD, fg=MUTED,
                 font=(self.font, 9)).pack(side="left", padx=(12, 4))
        tk.Entry(search, textvariable=self.filter_text, relief="flat", bg=CARD, fg=TEXT,
                 insertbackground=TEXT, width=22, font=(self.font, 10)
                 ).pack(side="left", padx=(0, 10), ipady=7)

        # Breakdown bar: the whole folder at a glance
        self.bar = tk.Canvas(main, height=12, bg=BG, highlightthickness=0)
        self.bar.pack(fill="x", pady=(18, 18))
        self.bar.bind("<Configure>", lambda e: self.draw_bar())

        # Table
        table_card = tk.Frame(main, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        table_card.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_card, columns=("file", "size", "dest"),
                                  show="headings", selectmode="browse")
        self.table.heading("file", text="File", anchor="w")
        self.table.heading("size", text="Size", anchor="e")
        self.table.heading("dest", text="Moves to", anchor="w")
        self.table.column("file", width=380, anchor="w")
        self.table.column("size", width=90, anchor="e")
        self.table.column("dest", width=160, anchor="w")
        for category, color in CATEGORY_COLORS.items():
            self.table.tag_configure(category, foreground=color)
        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)

        self.empty_label = tk.Label(table_card, bg=CARD, fg=MUTED, font=(self.font, 11),
                                    text="Choose a folder to see where each file will go.")
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

        # Action bar
        actions = tk.Frame(main, bg=BG)
        actions.pack(fill="x", pady=(18, 0))
        left = tk.Frame(actions, bg=BG)
        left.pack(side="left", fill="x", expand=True)
        self.status_label = tk.Label(left, text="Ready", bg=BG, fg=MUTED,
                                     font=(self.font, 10), anchor="w")
        self.status_label.pack(fill="x")
        self.progress = ttk.Progressbar(left, style="Accent.Horizontal.TProgressbar",
                                        mode="determinate")
        self.progress.pack(fill="x", pady=(8, 0), padx=(0, 24))

        self.organize_button = FlatButton(actions, "Organize files", self.start_organization,
                                          SUCCESS, SUCCESS_HOVER, font=(self.font, 10, "bold"))
        self.organize_button.pack(side="right")
        self.undo_button = FlatButton(actions, "Undo last", self.undo_last_organization,
                                      NEUTRAL, NEUTRAL_HOVER, fg=TEXT, font=(self.font, 10, "bold"))
        self.undo_button.pack(side="right", padx=(0, 10))
        self.undo_button.set_enabled(False)
        self.organize_button.set_enabled(False)

    # --------------------------------------------------------
    # Display updates
    # --------------------------------------------------------

    def update_stats(self, stats):
        self.legend_counts = stats
        for category, label in self.legend_labels.items():
            label.config(text=str(stats.get(category, 0)))
        self.draw_bar()

    def draw_bar(self):
        self.bar.delete("all")
        width = self.bar.winfo_width()
        total = sum(self.legend_counts.values())
        if width <= 1:
            return
        if total == 0:
            self.bar.create_rectangle(0, 0, width, 12, fill=NEUTRAL, outline="")
            return
        x = 0
        for category, color in CATEGORY_COLORS.items():
            count = self.legend_counts.get(category, 0)
            if not count:
                continue
            end = x + width * count / total
            self.bar.create_rectangle(x, 0, end - 2, 12, fill=color, outline="")
            x = end

    def fill_table(self):
        for item in self.table.get_children():
            self.table.delete(item)
        query = self.filter_text.get().strip().lower()
        shown = 0
        for name, category, size in self.preview:
            if query and query not in name.lower() and query not in category.lower():
                continue
            self.table.insert("", tk.END, values=(name, format_size(size), f"●  {category}"),
                              tags=(category,))
            shown += 1
        if self.preview:
            self.empty_label.place_forget()
            suffix = f" (showing {shown})" if query else ""
            self.count_label.config(text=f"{len(self.preview)} files ready to organize{suffix}")
        else:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def set_status(self, text):
        self.status_label.config(text=text)

    # --------------------------------------------------------
    # Folder selection
    # --------------------------------------------------------

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select folder to organize")
        if not folder:
            return

        self.folder.set(folder)
        self.folder_label.config(text=folder)
        self.progress["value"] = 0
        self.filter_text.set("")

        try:
            self.preview = scan_folder(folder)
        except OSError as error:
            messagebox.showerror("Can't open folder", f"This folder couldn't be read.\n\n{error}")
            return

        stats = {}
        for _, category, _ in self.preview:
            stats[category] = stats.get(category, 0) + 1
        self.update_stats(stats)
        self.fill_table()
        self.organize_button.set_enabled(bool(self.preview))

        if not self.preview:
            self.count_label.config(text="No files to organize")
            self.set_status("This folder has no loose files")
        else:
            self.set_status("Preview ready. No files have been moved.")

    # --------------------------------------------------------
    # Organize
    # --------------------------------------------------------

    def unique_destination(self, folder, filename):
        destination = os.path.join(folder, filename)
        name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(destination):
            destination = os.path.join(folder, f"{name}_{counter}{ext}")
            counter += 1
        return destination

    def start_organization(self):
        folder = self.folder.get()
        if not folder or not self.preview:
            messagebox.showwarning("No files", "Choose a folder that contains files first.")
            return
        if not messagebox.askyesno("Organize files",
                                   f"Move {len(self.preview)} files into type folders?\n\n"
                                   "You can undo this afterwards."):
            return

        self.last_operation, self.created_dirs = [], set()
        stats, failed = {}, 0
        total = len(self.preview)
        self.progress.config(maximum=total, value=0)
        self.organize_button.set_enabled(False)

        for index, (filename, category, _) in enumerate(self.preview, start=1):
            source = os.path.join(folder, filename)
            category_folder = os.path.join(folder, category)
            try:
                if not os.path.exists(category_folder):
                    os.makedirs(category_folder)
                    self.created_dirs.add(category_folder)
                destination = self.unique_destination(category_folder, filename)
                shutil.move(source, destination)
                self.last_operation.append({"original": source, "destination": destination})
                stats[category] = stats.get(category, 0) + 1
            except OSError:
                failed += 1
            self.progress["value"] = index
            self.set_status(f"Organizing {index} of {total}…")
            self.root.update_idletasks()

        moved = len(self.last_operation)
        self.preview = []
        self.fill_table()
        self.update_stats(stats)
        self.undo_button.set_enabled(moved > 0)
        self.count_label.config(text=f"{moved} files organized")
        self.set_status(f"Organized {moved} files" + (f". {failed} couldn't be moved." if failed else ""))

        message = f"Organized {moved} file(s)."
        if failed:
            message += f"\n{failed} file(s) couldn't be moved. They may be open in another program."
        messagebox.showinfo("Organization complete", message)

    # --------------------------------------------------------
    # Undo
    # --------------------------------------------------------

    def undo_last_organization(self):
        if not self.last_operation:
            return
        if not messagebox.askyesno("Undo", "Move every file back to where it was?"):
            return

        restored = failed = 0
        for op in reversed(self.last_operation):
            original, destination = op["original"], op["destination"]
            try:
                if not os.path.exists(destination) or os.path.exists(original):
                    failed += 1
                    continue
                shutil.move(destination, original)
                restored += 1
            except OSError:
                failed += 1

        # Remove the type folders this run created, if they're now empty
        for folder in self.created_dirs:
            try:
                if os.path.isdir(folder) and not os.listdir(folder):
                    os.rmdir(folder)
            except OSError:
                pass

        self.last_operation, self.created_dirs = [], set()
        self.undo_button.set_enabled(False)
        self.progress["value"] = 0
        self.set_status(f"Restored {restored} files")

        folder = self.folder.get()
        if folder and os.path.isdir(folder):
            self.preview = scan_folder(folder)
            stats = {}
            for _, category, _ in self.preview:
                stats[category] = stats.get(category, 0) + 1
            self.update_stats(stats)
            self.fill_table()
            self.organize_button.set_enabled(bool(self.preview))

        message = f"Restored {restored} file(s)."
        if failed:
            message += f"\n{failed} file(s) couldn't be restored because they were moved, renamed or replaced."
        messagebox.showinfo("Undo complete", message)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    FileOrganizerApp(root)
    root.mainloop()