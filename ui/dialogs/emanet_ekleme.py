import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from config import EMANET_TIPLERI, EMANET_UI_GRUPLARI

class EmanetEklemeDialog(tk.Toplevel):
    def __init__(self, parent, app, abone_id, abone_ad):
        super().__init__(parent)
        self.title(f"Emanet İşlemi - {abone_ad}")
        self.geometry("500x450")
        self.resizable(False, False)
        self.app = app
        self.db = app.db
        self.emanet_service = app.emanet_service
        self.abone_id = abone_id
        self._setup_ui()

    def _setup_ui(self):
        emanet_durum = self.db.get_emanet_durumu(self.abone_id)

        form = ttk.Frame(self)
        form.pack(pady=15, padx=20, fill=tk.X)

        ttk.Label(form, text="Ürün:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cmb_tur = ttk.Combobox(form, values=EMANET_TIPLERI, width=25, state="readonly")
        if EMANET_TIPLERI:
            self.cmb_tur.set(EMANET_TIPLERI[0])
        self.cmb_tur.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Adet:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ent_adet = ttk.Entry(form, width=10)
        self.ent_adet.insert(0, "1")
        self.ent_adet.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="İşlem Türü:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.islem_turu = tk.StringVar(value="Verildi")
        ttk.Radiobutton(form, text="Boş Verildi", variable=self.islem_turu,
                        value="Verildi").grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(form, text="Dolu Alındı", variable=self.islem_turu,
                        value="Alındı").grid(row=2, column=2, sticky=tk.W)

        ttk.Label(form, text="Tarih:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ent_tarih = ttk.Entry(form, width=15)
        self.ent_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.ent_tarih.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Açıklama:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.ent_aciklama = ttk.Entry(form, width=30)
        self.ent_aciklama.grid(row=4, column=1, padx=5, pady=5)

        durum_frame = ttk.LabelFrame(self, text="Mevcut Emanet Durumu")
        durum_frame.pack(fill=tk.X, padx=20, pady=10)
        for grup_adi, items in EMANET_UI_GRUPLARI:
            frame = ttk.Frame(durum_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(frame, text=f"{grup_adi}:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
            for label, key in items:
                val = emanet_durum.get(label if label in EMANET_TIPLERI else key, 0)
                ttk.Label(frame, text=f" {label}:{val}",
                         foreground="blue", font=("Arial", 8, "bold")).pack(side=tk.LEFT, padx=2)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="İptal", command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Kaydet →", command=self._kaydet,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    def _kaydet(self):
        try:
            tup_tipi = self.cmb_tur.get()
            adet_str = self.ent_adet.get()
            islem = self.islem_turu.get()
            tarih = self.ent_tarih.get()
            aciklama = self.ent_aciklama.get()

            if not tup_tipi:
                messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin!")
                return
            try:
                adet = int(adet_str)
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir adet giriniz!")
                return
            if adet <= 0:
                messagebox.showwarning("Uyarı", "Adet 0'dan büyük olmalıdır!")
                return

            if islem == "Verildi":
                self.emanet_service.emanet_ver(
                    abone_id=self.abone_id, tup_tipi=tup_tipi,
                    adet=adet, tarih=tarih, aciklama=aciklama)
                self.app.right_panel.son_islem_ekle(
                    f"Emanet Verildi: {self.app.left_panel.ent_ad.get()} - {adet} adet {tup_tipi}")
            else:
                bakiye = self.db.get_emanet_bakiye(self.abone_id, tup_tipi)
                if bakiye < adet:
                    messagebox.showwarning("Yetersiz Emanet",
                        f"Abonede {bakiye} adet {tup_tipi} emaneti bulunuyor. "
                        f"{adet} adet alınamaz!")
                    return
                self.emanet_service.emanet_al(
                    abone_id=self.abone_id, tup_tipi=tup_tipi,
                    adet=adet, tarih=tarih, aciklama=aciklama)
                self.app.right_panel.son_islem_ekle(
                    f"Emanet Alındı: {self.app.left_panel.ent_ad.get()} - {adet} adet {tup_tipi}")

            messagebox.showinfo("Başarılı", "Emanet işlemi kaydedildi.")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Hata", str(e))
