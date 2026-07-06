import tkinter as tk
from tkinter import ttk
from config import COLOR_HEADER_BG, COLOR_HEADER_FG, COLOR_FOOTER_BG, COLOR_ALTIN, COLOR_WIDGET_BG

def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')

    style.configure("Header.TFrame", background=COLOR_HEADER_BG)
    style.configure("Header.TLabel", background=COLOR_HEADER_BG,
                    foreground=COLOR_HEADER_FG, font=("Arial", 16, "bold"))
    style.configure("Subheader.TLabel", background=COLOR_HEADER_BG,
                    foreground="white", font=("Arial", 9))

    style.configure("Footer.TFrame", background=COLOR_FOOTER_BG)

    style.configure("Card.TFrame", background="#FFFFFF", relief="ridge", borderwidth=1)
    style.configure("CardHeader.TLabel", background="#8B0000",
                    foreground="white", font=("Arial", 10, "bold"), padding=5)

    style.configure("Widget.TFrame", background=COLOR_WIDGET_BG, relief="raised")
    style.configure("Widget.TLabel", background=COLOR_WIDGET_BG,
                    foreground="white", font=("Arial", 8))
    style.configure("WidgetValue.TLabel", background="white",
                    foreground=COLOR_HEADER_BG, font=("Arial", 16, "bold"))

    style.configure("Accent.TButton", font=("Arial", 9, "bold"),
                    background=COLOR_HEADER_BG, foreground="white")
    style.map("Accent.TButton",
              background=[('active', '#A52A2A')],
              foreground=[('active', 'white')])

    style.configure("Green.TLabel", foreground="#006600", font=("Arial", 10, "bold"))
    style.configure("Red.TLabel", foreground="#CC0000", font=("Arial", 10, "bold"))
    style.configure("Gold.TLabel", foreground="#FFD700", font=("Arial", 12, "bold"))

    style.configure("Search.TEntry", fieldbackground="#FFF8DC")
    style.configure("Treeview", rowheight=28, font=("Arial", 9))
    style.configure("Treeview.Heading", font=("Arial", 9, "bold"))
    style.map("Treeview",
              background=[('selected', COLOR_ALTIN)],
              foreground=[('selected', 'black')])

    style.configure("StatusBar.TFrame", background="#2F2F2F")
    style.configure("StatusBar.TLabel", background="#2F2F2F",
                    foreground="white", font=("Arial", 8))
