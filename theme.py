"""
theme.py

Provides a function to apply an Aqua-like theme to ttk widgets, imitating macOS Aqua appearance on any platform.
"""

def apply_aqua_theme(style):
    """
    Apply an Aqua-like theme to ttk widgets using the given ttk.Style instance.
    This imitates the macOS Aqua look with light backgrounds, blue highlights, and modern fonts.
    """
    style.theme_use("clam")  # Use a theme that allows full customization

    # Aqua-like color palette
    aqua_bg = "#f8f8f8"
    aqua_fg = "#222"
    aqua_entry_bg = "#ffffff"
    aqua_select_bg = "#007aff"  # macOS blue
    aqua_select_fg = "#fff"
    aqua_border = "#d1d1d6"

    # General widget styles
    style.configure("TFrame", background=aqua_bg)
    style.configure("TLabel", background=aqua_bg, foreground=aqua_fg, font=("Segoe UI", 13))
    style.configure("TButton", background=aqua_bg, foreground=aqua_fg, font=("Segoe UI", 13), borderwidth=1, focusthickness=2, focuscolor=aqua_border)
    style.map("TButton",
        background=[("active", "#e5e5ea")],
        relief=[("pressed", "sunken"), ("!pressed", "raised")]
    )
    style.configure("TEntry", fieldbackground=aqua_entry_bg, foreground=aqua_fg, bordercolor=aqua_border, font=("Segoe UI", 13))
    style.configure("Treeview", background=aqua_bg, foreground=aqua_fg, fieldbackground=aqua_bg, bordercolor=aqua_border, font=("Segoe UI", 13))
    style.map("Treeview",
        background=[("selected", aqua_select_bg)],
        foreground=[("selected", aqua_select_fg)]
    )
    style.configure("TScrollbar", background=aqua_bg, troughcolor="#e5e5ea", bordercolor=aqua_border)

    # Add padding for a more macOS feel
    style.configure(".", padding=8) 