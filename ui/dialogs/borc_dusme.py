import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from config import ODEME_TIPLERI

class BorcDusmeDialog(tk.Toplevel):
    def __init__(self, parent, app, abone_id, abone_ad):
        super().__init__(parent)
        self.title(f"Borç Düşme - {abone_ad}")
        self.geometry("400x320")
        self.resizable(False, False)
        self.app = app
        self.db = app.db
        self.borc_service = app.borc_service
        self.abone_id = abone_id
        self._setup_ui()

    def _setup_ui(self):
        bakiye = self.db.get_abone_bakiye(self.abone_id)

        ttk.Label(self, text="Güncel Borç:", font=("Arial", 10)).pack(pady=(15, 2))
        self.lbl_bakiye = ttk.Label(self, text=f"{bakiye:,.2f} TL",
                                     style="Red.TLabel")
        self.lbl_bakiye.pack()

        form = ttk.Frame(self)
        form.pack(pady=15, padx=20, fill=tk.X)

        ttk.Label(form, text="Düşülecek Tutar:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ent_tutar = ttk.Entry(form, width=15, font=("Arial", 11))
        self.ent_tutar.grid(row=0, column=1, padx=5, pady=5)
        self.ent_tutar.bind("<KeyRelease>", self._hesapla)

        ttk.Label(form, text="Açıklama:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ent_aciklama = ttk.Entry(form, width=25)
        self.ent_aciklama.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Ödeme Türü:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cmb_odeme = ttk.Combobox(form, values=ODEME_TIPLERI, width=12, state="readonly")
        self.cmb_odeme.set("Nakit")
        self.cmb_odeme.grid(row=2, column=1, padx=5, pady=5)

        self.lbl_kalan = ttk.Label(self, text="Kalan Borç: 0,00 TL",
                                    font=("Arial", 11, "bold"))
        self.lbl_kalan.pack(pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="İptal", command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Borç Düş →", command=self._kaydet,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    def _hesapla(self, event=None):
        bakiye = self.db.get_abone_bakiye(self.abone_id)
        try:
            tutar = float(self.ent_tutar.get().replace(',', '.') or 0)
            kalan = max(0, bakiye - tutar)
            self.lbl_kalan.config(text=f"Kalan Borç: {kalan:,.2f} TL",
                                  foreground="#CC0000" if kalan > 0 else "#006600")
        except ValueError:
            self.lbl_kalan.config(text="Kalan Borç: 0,00 TL")

    def _kaydet(self):
        try:
            tutar_str = self.ent_tutar.get().replace(',', '.')
            if not tutar_str:
                messagebox.showwarning("Uyarı", "Lütfen bir tutar giriniz!")
                return
            tutar = float(tutar_str)
            if tutar <= 0:
                messagebox.showwarning("Uyarı", "Tutar 0'dan büyük olmalıdır!")
                return
            bakiye = self.db.get_abone_bakiye(self.abone_id)
            if tutar > bakiye:
                messagebox.showwarning("Uyarı",
                    f"Düşülecek tutar ({tutar:.2f} TL), güncel borçtan ({bakiye:.2f} TL) fazla olamaz!")
                return

            aciklama = self.ent_aciklama.get()
            odeme = self.cmb_odeme.get()

            self.borc_service.borc_dus(
                abone_id=self.abone_id, tutar=tutar,
                aciklama=aciklama, odeme_turu=odeme)

            self.app.right_panel.son_islem_ekle(
                f"Borç Düşüldü: {self.app.left_panel.ent_ad.get()} - {tutar:,.2f} TL ({odeme})")

            messagebox.showinfo("Başarılı", f"{tutar:,.2f} TL borç düşüldü.")
            self.destroy()

        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir sayı giriniz!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))
