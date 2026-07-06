import tkinter as tk
from tkinter import ttk
from config import COLOR_HEADER_BG, COLOR_HEADER_FG, COLOR_WIDGET_BG

class HeaderPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Header.TFrame")
        self.app = app
        self.pack(fill=tk.X)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.columnconfigure(4, weight=0)
        self.columnconfigure(5, weight=0)

        lbl_title = ttk.Label(self, text="🏆 TÜPÇÜLER KRALI v2.0", style="Header.TLabel")
        lbl_title.grid(row=0, column=0, rowspan=2, padx=15, pady=8, sticky=tk.W)

        self.lbl_abone = self._create_widget(2, "Toplam Abone", "0", row=0)
        self.lbl_alicak = self._create_widget(3, "Toplam Alıcak", "0,00 TL", row=0)
        self.lbl_depo = self._create_widget(4, "Depo Stoğu", "0", row=0)

        btn_fiyat = ttk.Button(self, text="Fiyatları Düzenle",
                               command=self.app.open_fiyatlar, style="Accent.TButton")
        btn_fiyat.grid(row=0, column=5, rowspan=2, padx=(10, 15), pady=8, sticky=tk.E)

        self.grid_columnconfigure(5, weight=1)
        self.pack_propagate(False)

    def _create_widget(self, col, title, value, row):
        frame = tk.Frame(self, bg=COLOR_WIDGET_BG, padx=12, pady=4, relief="raised", bd=1)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky=tk.W)
        lbl_title = tk.Label(frame, text=title, bg=COLOR_WIDGET_BG,
                            fg="white", font=("Arial", 8))
        lbl_title.pack()
        lbl_value = tk.Label(frame, text=value, bg="white",
                            fg=COLOR_HEADER_BG, font=("Arial", 16, "bold"))
        lbl_value.pack(pady=(0, 2))
        setattr(self, f'val_{col}', lbl_value)
        return lbl_value

    def guncelle(self, data):
        self.val_2.config(text=str(data.get('toplam_abone', 0)))
        self.val_3.config(text=f"{data.get('toplam_alicak', 0):,.2f} TL")
        self.val_4.config(text=str(data.get('depo_stogu', 0)))

    def refresh_from_db(self):
        toplam_abone = self.app.db.get_toplam_abone_sayisi()
        toplam_alicak = self.app.db.get_toplam_alicak()
        depo_stogu = self.app.db.get_depo_toplam_dolu()
        self.guncelle({
            'toplam_abone': toplam_abone,
            'toplam_alicak': toplam_alicak,
            'depo_stogu': depo_stogu
        })
