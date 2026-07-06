import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from config import GIDER_KATEGORILERI

class GiderDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.title("Gider Ekle")
        self.geometry("400x300")
        self.resizable(False, False)
        self.app = app
        self.gider_service = app.gider_service
        self._setup_ui()

    def _setup_ui(self):
        ttk.Label(self, text="Gider Ekle", font=("Arial", 14, "bold"),
                 foreground="#CC0000").pack(pady=(10, 15))

        form = ttk.Frame(self)
        form.pack(padx=20, fill=tk.X)

        ttk.Label(form, text="Tarih:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ent_tarih = ttk.Entry(form, width=15)
        self.ent_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.ent_tarih.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Kategori:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cmb_kategori = ttk.Combobox(form, values=GIDER_KATEGORILERI, width=15, state="normal")
        self.cmb_kategori.set("Diğer")
        self.cmb_kategori.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Tutar:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ent_tutar = ttk.Entry(form, width=12)
        self.ent_tutar.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Açıklama:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ent_aciklama = ttk.Entry(form, width=30)
        self.ent_aciklama.grid(row=3, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="İptal", command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Gider Ekle →", command=self._kaydet,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    def _kaydet(self):
        try:
            tarih = self.ent_tarih.get()
            kategori = self.cmb_kategori.get()
            tutar_str = self.ent_tutar.get().replace(',', '.')
            aciklama = self.ent_aciklama.get()
            if not kategori:
                messagebox.showwarning("Uyarı", "Kategori seçilmelidir!")
                return
            try:
                tutar = float(tutar_str)
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir tutar giriniz!")
                return
            if tutar <= 0:
                messagebox.showwarning("Uyarı", "Gider tutarı 0'dan büyük olmalıdır!")
                return
            self.gider_service.gider_ekle(tarih, tutar, kategori, aciklama)
            self.app.right_panel.son_islem_ekle(
                f"Gider: {kategori} - {tutar:,.2f} TL")
            messagebox.showinfo("Başarılı", f"{tutar:,.2f} TL gider eklendi.\nKategori: {kategori}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Hata", str(e))
