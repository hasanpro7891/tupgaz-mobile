import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from config import TUP_LISTESI, SU_LISTESI

class BorcEklemeDialog(tk.Toplevel):
    def __init__(self, parent, app, abone_id, abone_ad):
        super().__init__(parent)
        self.title(f"Borç Ekleme - {abone_ad}")
        self.geometry("520x480")
        self.resizable(False, False)
        self.app = app
        self.db = app.db
        self.borc_service = app.borc_service
        self.abone_id = abone_id
        self.fiyatlar = self.db.get_fiyatlar()

        self.kat_secim = tk.StringVar(value="tup")
        self._setup_ui()

    def _setup_ui(self):
        ttk.Label(self, text="Ürün Kategorisi:", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        kat_frame = ttk.Frame(self)
        kat_frame.pack()
        ttk.Radiobutton(kat_frame, text="Tüpler", variable=self.kat_secim,
                        value="tup", command=self._kategori_degisti).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(kat_frame, text="Sular (19 LT)", variable=self.kat_secim,
                        value="su", command=self._kategori_degisti).pack(side=tk.LEFT, padx=10)

        form = ttk.Frame(self)
        form.pack(pady=10, padx=20, fill=tk.X)

        ttk.Label(form, text="Ürün:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cmb_urun = ttk.Combobox(form, width=30, state="readonly")
        self.cmb_urun.grid(row=0, column=1, padx=5, pady=5)
        self.cmb_urun.bind("<<ComboboxSelected>>", self._urun_secildi)

        ttk.Label(form, text="Adet:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ent_adet = ttk.Entry(form, width=10)
        self.ent_adet.insert(0, "1")
        self.ent_adet.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.ent_adet.bind("<KeyRelease>", self._hesapla)

        ttk.Label(form, text="Birim Fiyat:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ent_fiyat = ttk.Entry(form, width=12)
        self.ent_fiyat.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        self.ent_fiyat.bind("<KeyRelease>", self._hesapla)

        ttk.Label(form, text="Açıklama:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ent_aciklama = ttk.Entry(form, width=30)
        self.ent_aciklama.grid(row=3, column=1, padx=5, pady=5)

        self.lbl_toplam = ttk.Label(self, text="Toplam: 0,00 TL",
                                     font=("Arial", 16, "bold"), foreground="#8B0000")
        self.lbl_toplam.pack(pady=10)

        self.lbl_stok = ttk.Label(self, text="", font=("Arial", 9))
        self.lbl_stok.pack()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="İptal", command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Borca Ekle →", command=self._kaydet,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

        self._kategori_degisti()

    def _kategori_degisti(self):
        urunler = TUP_LISTESI if self.kat_secim.get() == "tup" else SU_LISTESI
        self.cmb_urun['values'] = urunler
        if urunler:
            self.cmb_urun.set(urunler[0])
            self._urun_secildi()

    def _urun_secildi(self, event=None):
        urun = self.cmb_urun.get()
        fiyat = self.fiyatlar.get(urun, 0.0)
        self.ent_fiyat.delete(0, tk.END)
        if fiyat > 0:
            self.ent_fiyat.insert(0, f"{fiyat:.2f}")
        else:
            self.ent_fiyat.insert(0, "")
            self.lbl_stok.config(text=f"⚠ {urun} fiyatı girilmemiş! Lütfen manuel giriniz.",
                                foreground="orange")
        self._stok_kontrol()
        self._hesapla()

    def _stok_kontrol(self):
        urun = self.cmb_urun.get()
        if urun:
            stok = self.db.get_depo_urun(urun)
            if stok:
                self.lbl_stok.config(
                    text=f"📦 Stok: {stok['dolu_adet']} dolu / {stok['bos_adet']} boş",
                    foreground="green" if stok['dolu_adet'] > 0 else "red")

    def _hesapla(self, event=None):
        try:
            adet = int(self.ent_adet.get() or 0)
            fiyat = float(self.ent_fiyat.get().replace(',', '.') or 0)
            toplam = adet * fiyat
            self.lbl_toplam.config(text=f"Toplam: {toplam:,.2f} TL")
        except ValueError:
            self.lbl_toplam.config(text="Toplam: 0,00 TL")

    def _kaydet(self):
        try:
            urun = self.cmb_urun.get()
            adet_str = self.ent_adet.get()
            fiyat_str = self.ent_fiyat.get().replace(',', '.')
            aciklama = self.ent_aciklama.get()

            if not urun:
                messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin!")
                return
            try:
                adet = int(adet_str)
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir adet giriniz!")
                self.ent_adet.focus_set()
                return
            try:
                fiyat = float(fiyat_str)
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir fiyat giriniz!")
                self.ent_fiyat.focus_set()
                return
            if adet <= 0:
                messagebox.showwarning("Uyarı", "Adet 0'dan büyük olmalıdır!")
                return
            if fiyat <= 0:
                messagebox.showwarning("Uyarı", "Birim fiyat 0'dan büyük olmalıdır!")
                return

            stok = self.db.get_depo_urun(urun)
            if stok['dolu_adet'] < adet:
                messagebox.showwarning("Stok Yetersiz",
                    f"Depoda yeterli {urun} stoku yok!\n"
                    f"Mevcut: {stok['dolu_adet']} adet\nİstenen: {adet} adet")
                return

            self.borc_service.borc_ekle(
                abone_id=self.abone_id, urun=urun, adet=adet,
                birim_fiyat=fiyat, aciklama=aciklama)

            toplam = adet * fiyat
            self.app.right_panel.son_islem_ekle(
                f"Borç Eklendi: {self.app.left_panel.ent_ad.get()} - {toplam:,.2f} TL ({adet}x{urun})")

            messagebox.showinfo("Başarılı", f"{toplam:,.2f} TL borç eklendi.")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Hata", str(e))
