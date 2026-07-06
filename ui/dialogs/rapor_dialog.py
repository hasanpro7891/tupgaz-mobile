import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar

class RaporDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.title("Raporlar")
        self.geometry("700x600")
        self.app = app
        self.rapor_service = app.rapor_service
        self.donem_secim = tk.StringVar(value="gunluk")
        self._setup_ui()

    def _setup_ui(self):
        ttk.Label(self, text="📊 Raporlar", font=("Arial", 14, "bold"),
                 foreground="#8B0000").pack(pady=(10, 5))

        donem_frame = ttk.Frame(self)
        donem_frame.pack(pady=5)
        for text, val in [("Günlük", "gunluk"), ("Aylık", "aylik"), ("Yıllık", "yillik")]:
            ttk.Radiobutton(donem_frame, text=text, variable=self.donem_secim,
                           value=val, command=self._refresh).pack(side=tk.LEFT, padx=10)

        tarih_frame = ttk.Frame(self)
        tarih_frame.pack(pady=5)
        ttk.Label(tarih_frame, text="Tarih:").pack(side=tk.LEFT)
        self.ent_tarih = ttk.Entry(tarih_frame, width=15)
        self.ent_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.ent_tarih.pack(side=tk.LEFT, padx=5)
        ttk.Button(tarih_frame, text="Yenile", command=self._refresh).pack(side=tk.LEFT, padx=5)

        self.text_rapor = tk.Text(self, font=("Courier", 9), wrap=tk.NONE, bg="#FFF8DC")
        self.text_rapor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scroll_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text_rapor.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_rapor.configure(yscrollcommand=scroll_y.set)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="🖨️ Yazdır", command=self._yazdir).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Kapat", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        self._refresh()

    def _refresh(self):
        self.text_rapor.delete("1.0", tk.END)
        try:
            donem = self.donem_secim.get()
            if donem == "gunluk":
                tarih = self.ent_tarih.get()
                rapor = self.rapor_service.gunluk_rapor(tarih)
                self._goster_gunluk(rapor)
            elif donem == "aylik":
                try:
                    gun, ay, yil = self.ent_tarih.get().split(".")
                    rapor = self.rapor_service.aylik_rapor(int(yil), int(ay))
                    self._goster_donem(rapor, "AYLIK RAPOR")
                except (ValueError, IndexError):
                    self.text_rapor.insert(tk.END, "HATA: Tarih formatı GG.AA.YYYY olmalıdır!")
            else:
                try:
                    gun, ay, yil = self.ent_tarih.get().split(".")
                    rapor = self.rapor_service.yillik_rapor(int(yil))
                    self._goster_donem(rapor, "YILLIK RAPOR")
                except (ValueError, IndexError):
                    self.text_rapor.insert(tk.END, "HATA: Tarih formatı GG.AA.YYYY olmalıdır!")
        except Exception as e:
            self.text_rapor.insert(tk.END, f"HATA: {e}")

    def _goster_gunluk(self, r):
        t = self.text_rapor
        t.insert(tk.END, f"========== GÜNLÜK RAPOR ==========\n")
        t.insert(tk.END, f"Tarih: {r['tarih']}\n")
        t.insert(tk.END, f"{'='*40}\n\n")

        t.insert(tk.END, "── GELİRLER ──\n")
        t.insert(tk.END, f"Tüp Satışları:      {r['tup_satislari']['toplam']:>10,.2f} TL\n")
        for s in r['tup_satislari']['detay']:
            t.insert(tk.END, f"  ├─ {s['urun']}: {s['toplam']:>10,.2f} TL ({s['adet']} adet)\n")
        t.insert(tk.END, f"İndirimli Satışlar: {r['indirimli_satislari']['toplam']:>10,.2f} TL\n")
        for s in r['indirimli_satislari']['detay']:
            t.insert(tk.END, f"  ├─ {s['urun']}: {s['toplam']:>10,.2f} TL ({s['adet']} adet)\n")
        t.insert(tk.END, f"Su Satışları:       {r['su_satislari']['toplam']:>10,.2f} TL\n")
        for s in r['su_satislari']['detay']:
            t.insert(tk.END, f"  ├─ {s['urun']}: {s['toplam']:>10,.2f} TL ({s['adet']} adet)\n")
        t.insert(tk.END, f"Peşin Satışlar:     {r['pesin_satislari']['toplam']:>10,.2f} TL\n")
        for s in r['pesin_satislari']['detay']:
            t.insert(tk.END, f"  ├─ {s['urun']}: {s['toplam']:>10,.2f} TL ({s['adet']} adet)\n")
        t.insert(tk.END, f"{'-'*40}\n")
        t.insert(tk.END, f"BRÜT GELİR:         {r['brut_gelir']:>10,.2f} TL\n\n")
        t.insert(tk.END, f"Tahsilat (Borç Düş): {r['toplam_tahsilat']:>10,.2f} TL\n\n")

        t.insert(tk.END, "── GİDERLER ──\n")
        if r['gider_detay']:
            for g in r['gider_detay']:
                t.insert(tk.END, f"  {g['kategori']}: {g['toplam']:>10,.2f} TL\n")
        else:
            t.insert(tk.END, "  (gider yok)\n")
        t.insert(tk.END, f"{'-'*40}\n")
        t.insert(tk.END, f"TOPLAM GİDER:       {r['toplam_gider']:>10,.2f} TL\n\n")

        t.insert(tk.END, "── KAR/ZARAR ──\n")
        t.insert(tk.END, f"Net Kar/Zarar:      {r['net_kar']:>10,.2f} TL")
        durum = r['kar_durumu']
        t.insert(tk.END, f"  ({'✅ KAR' if durum == 'kar' else '❌ ZARAR' if durum == 'zarar' else '⚖️ BAŞABAŞ'})\n")
        t.insert(tk.END, f"Kar Marjı:          {r['kar_marji']:>9.2f}%\n")
        t.insert(tk.END, f"Yeni Abone:         {r['yeni_abone']:>10}\n")

    def _goster_donem(self, r, baslik):
        t = self.text_rapor
        t.insert(tk.END, f"========== {baslik} ==========\n")
        t.insert(tk.END, f"Dönem: {r['donem']}\n")
        t.insert(tk.END, f"{'='*40}\n\n")
        t.insert(tk.END, f"Tüp Satışları:       {r['tup_satis']:>10,.2f} TL\n")
        t.insert(tk.END, f"İndirimli Satışlar:  {r['indirimli_satis']:>10,.2f} TL\n")
        t.insert(tk.END, f"Su Satışları:        {r['su_satis']:>10,.2f} TL\n")
        t.insert(tk.END, f"Peşin Satışlar:      {r['pesin_satis']:>10,.2f} TL\n")
        t.insert(tk.END, f"{'-'*40}\n")
        t.insert(tk.END, f"BRÜT GELİR:          {r['brut_gelir']:>10,.2f} TL\n")
        t.insert(tk.END, f"Tahsilat:            {r['toplam_tahsilat']:>10,.2f} TL\n")
        t.insert(tk.END, f"Toplam Gider:        {r['toplam_gider']:>10,.2f} TL\n")
        t.insert(tk.END, f"{'-'*40}\n")
        t.insert(tk.END, f"NET KAR:             {r['net_kar']:>10,.2f} TL\n")
        t.insert(tk.END, f"Yeni Abone:          {r['yeni_abone']:>10}\n")

        if 'en_karli_ay' in r:
            t.insert(tk.END, f"\nEn Karlı Ay:        {r['en_karli_ay']}\n")
            t.insert(tk.END, f"En Zararlı Ay:      {r['en_zararli_ay']}\n")

    def _yazdir(self):
        try:
            self.text_rapor.tag_add("sel", "1.0", tk.END)
            self.text_rapor.edit_separator()
            self.text_rapor.tag_remove("sel", "1.0", tk.END)
            self.text_rapor.event_generate("<<Copy>>")
            messagebox.showinfo("Yazdır", "Rapor panoya kopyalandı. Bir metin belgesine yapıştırabilirsiniz.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))
