import tkinter as tk
from tkinter import ttk, messagebox
from config import TUP_LISTESI, SU_LISTESI, INDIRIMLI_LISTESI

class FiyatListesiDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.title("Fiyat Listesi Yönetimi")
        self.geometry("550x500")
        self.resizable(False, False)
        self.app = app
        self.db = app.db
        self.fiyat_service = app.fiyat_service
        self.fiyatlar = self.db.get_fiyatlar()
        self.entries = {}
        self._setup_ui()

    def _setup_ui(self):
        ttk.Label(self, text="📊 Fiyat Listesi Yönetimi",
                 font=("Arial", 14, "bold"), foreground="#8B0000").pack(pady=(10, 2))
        ttk.Label(self, text="Fiyatı 0 (sıfır) bırakırsanız, borç eklerken manuel girmeniz gerekir.",
                 font=("Arial", 8, "italic"), foreground="blue").pack(pady=(0, 10))

        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        kategoriler = [
            ("Tüpler", TUP_LISTESI),
            ("İndirimli Tüpler", INDIRIMLI_LISTESI),
            ("Sular (19 LT)", SU_LISTESI),
        ]

        row = 0
        for kat_baslik, urunler in kategoriler:
            if not urunler:
                continue
            header = ttk.Label(scroll_frame, text=f"── {kat_baslik} ──",
                              font=("Arial", 11, "bold"), foreground="#8B0000")
            header.grid(row=row, column=0, columnspan=4, sticky=tk.W, padx=10, pady=(10, 5))
            row += 1
            for urun in urunler:
                fiyat = self.fiyatlar.get(urun, 0.0)
                gncl = self.db.get_fiyat_guncelleme_tarihi(urun)
                ttk.Label(scroll_frame, text=urun).grid(
                    row=row, column=0, sticky=tk.W, padx=15, pady=3)
                ent = ttk.Entry(scroll_frame, width=12, justify=tk.RIGHT)
                ent.insert(0, f"{fiyat:.2f}")
                ent.grid(row=row, column=1, padx=5, pady=3)
                self.entries[urun] = ent
                ttk.Label(scroll_frame, text="TL").grid(row=row, column=2, sticky=tk.W, pady=3)
                ttk.Label(scroll_frame, text=f"(Son: {gncl})",
                         font=("Arial", 8), foreground="gray").grid(
                    row=row, column=3, sticky=tk.W, padx=5)
                row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="💾 Tüm Fiyatları Kaydet",
                  command=self._save_all, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="↺ Varsayılana Dön",
                  command=self._reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✖ Kapat", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.after(100, lambda: canvas.configure(scrollregion=canvas.bbox("all")))

    def _save_all(self):
        errors = []
        yeni_fiyatlar = {}
        for urun, ent in self.entries.items():
            try:
                fiyat = float(ent.get().replace(',', '.'))
                if fiyat < 0:
                    errors.append(f"{urun}: Negatif fiyat girilemez!")
                elif fiyat > 999999:
                    errors.append(f"{urun}: Fiyat çok yüksek!")
                else:
                    yeni_fiyatlar[urun] = fiyat
            except ValueError:
                errors.append(f"{urun}: Geçersiz sayısal değer!")
        if errors:
            messagebox.showerror("Hatalar", "\n".join(errors))
            return
        try:
            self.fiyat_service.update_all(yeni_fiyatlar)
            self.app.right_panel.son_islem_ekle("Fiyat listesi güncellendi")
            messagebox.showinfo("Başarılı", "Tüm fiyatlar güncellendi.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _reset(self):
        if messagebox.askyesno("Onay", "Tüm fiyatları sıfırlamak istediğinize emin misiniz?"):
            for ent in self.entries.values():
                ent.delete(0, tk.END)
                ent.insert(0, "0.00")
