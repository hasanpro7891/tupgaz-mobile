import tkinter as tk
from tkinter import ttk
from config import EMANET_UI_GRUPLARI
from data.mahalleler import SERVIS_ELEMANLARI, get_mersin_mahalleleri, search_mahalle


class AutocompleteCombobox(ttk.Combobox):
    def __init__(self, parent, values, **kwargs):
        self._full_values = sorted(values) if values else []
        super().__init__(parent, values=self._full_values, **kwargs)
        self.bind('<KeyRelease>', self._on_keyrelease)

    def _on_keyrelease(self, event):
        if event.keysym in ('BackSpace', 'Left', 'Right', 'Up', 'Down', 'Tab', 'Return', 'Escape',
                            'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            return
        typed = self.get()
        if typed:
            filtered = [v for v in self._full_values if typed.lower() in v.lower()]
            self['values'] = filtered
        else:
            self['values'] = self._full_values

    def set_full_values(self, values):
        self._full_values = sorted(values) if values else []
        self['values'] = self._full_values


class DatePickerPopup(tk.Toplevel):
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.title("Tarih Seç")
        self.on_select = on_select
        self.resizable(False, False)
        self.grab_set()

        from datetime import date
        bugun = date.today()

        frame = ttk.Frame(self, padding=10)
        frame.pack()

        ttk.Label(frame, text="Gün:").grid(row=0, column=0, padx=3)
        self.spn_gun = tk.Spinbox(frame, from_=1, to=31, width=4, font=("Arial", 12),
                                  justify=tk.CENTER)
        self.spn_gun.grid(row=0, column=1, padx=3)
        self.spn_gun.delete(0, tk.END)
        self.spn_gun.insert(0, str(bugun.day))

        ttk.Label(frame, text="Ay:").grid(row=0, column=2, padx=3)
        self.spn_ay = tk.Spinbox(frame, from_=1, to=12, width=4, font=("Arial", 12),
                                 justify=tk.CENTER)
        self.spn_ay.grid(row=0, column=3, padx=3)
        self.spn_ay.delete(0, tk.END)
        self.spn_ay.insert(0, str(bugun.month))

        ttk.Label(frame, text="Yıl:").grid(row=0, column=4, padx=3)
        self.spn_yil = tk.Spinbox(frame, from_=2020, to=2035, width=6, font=("Arial", 12),
                                  justify=tk.CENTER)
        self.spn_yil.grid(row=0, column=5, padx=3)
        self.spn_yil.delete(0, tk.END)
        self.spn_yil.insert(0, str(bugun.year))

        btn_frame = ttk.Frame(self, padding=5)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Bugün", command=self._bugun).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Seç", command=self._sec).pack(side=tk.LEFT, padx=5)

    def _bugun(self):
        from datetime import date
        bugun = date.today()
        self.on_select(bugun.strftime("%d.%m.%Y"))
        self.destroy()

    def _sec(self):
        try:
            gun = int(self.spn_gun.get())
            ay = int(self.spn_ay.get())
            yil = int(self.spn_yil.get())
            from datetime import date
            secilen = date(yil, ay, gun)
            self.on_select(secilen.strftime("%d.%m.%Y"))
            self.destroy()
        except ValueError:
            pass


class LeftPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10, relief="ridge")
        self.app = app
        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.selected_abone_id = None
        self.emanet_labels = {}

        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header, text="Abone Kartı Bilgileri",
                  style="Header.TLabel").pack(side=tk.LEFT, padx=5)

        form = ttk.Frame(self)
        form.pack(fill=tk.X)

        r = 0
        ttk.Label(form, text="Abone No:").grid(row=r, column=0, sticky=tk.W, padx=5, pady=2)
        self.ent_abone_no = ttk.Entry(form, width=15)
        self.ent_abone_no.grid(row=r, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(form, text="Kayıt Tar:").grid(row=r, column=2, sticky=tk.W, padx=5, pady=2)
        tar_frame = ttk.Frame(form)
        tar_frame.grid(row=r, column=3, sticky=tk.W, padx=5, pady=2)
        self.ent_kayit_tar = ttk.Entry(tar_frame, width=12)
        self.ent_kayit_tar.pack(side=tk.LEFT)
        ttk.Button(tar_frame, text="📅", width=3,
                   command=lambda: DatePickerPopup(self.app.root, self._tarih_sec)).pack(side=tk.LEFT, padx=2)
        ttk.Label(form, text="Tip:").grid(row=r, column=4, sticky=tk.W, padx=5, pady=2)
        self.cmb_tip = ttk.Combobox(form, values=["Ev Abonesi", "İş Yeri", "Tali Bayii"], width=12)
        self.cmb_tip.grid(row=r, column=5, sticky=tk.W, padx=5, pady=2)
        self.cmb_tip.set("Ev Abonesi")

        r += 1
        ttk.Label(form, text="Adı:").grid(row=r, column=0, sticky=tk.W, padx=5, pady=2)
        self.ent_ad = ttk.Entry(form, width=25)
        self.ent_ad.grid(row=r, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)
        ttk.Label(form, text="Soyadı:").grid(row=r, column=3, sticky=tk.W, padx=5, pady=2)
        self.ent_soyad = ttk.Entry(form, width=25)
        self.ent_soyad.grid(row=r, column=4, columnspan=2, sticky=tk.W, padx=5, pady=2)

        r += 1
        ttk.Label(form, text="Servis Elemanı:").grid(row=r, column=0, sticky=tk.W, padx=5, pady=2)
        self.cmb_servis = ttk.Combobox(form, values=SERVIS_ELEMANLARI, width=22, state="normal")
        self.cmb_servis.grid(row=r, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)

        r += 1
        ttk.Label(form, text="Son Sipariş:").grid(row=r, column=0, sticky=tk.W, padx=5, pady=2)
        self.ent_son_siparis = ttk.Entry(form, width=15, state="readonly")
        self.ent_son_siparis.grid(row=r, column=1, sticky=tk.W, padx=5, pady=2)

        addr_frame = ttk.LabelFrame(self, text="Adres Bilgileri")
        addr_frame.pack(fill=tk.X, pady=5)

        ttk.Label(addr_frame, text="Mahalle:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.cmb_mah = AutocompleteCombobox(addr_frame, values=get_mersin_mahalleleri(), width=18)
        self.cmb_mah.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(addr_frame, text="Sokak:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.ent_sokak = ttk.Entry(addr_frame, width=20)
        self.ent_sokak.grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(addr_frame, text="Bina/Kat/Daire:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.ent_bina = ttk.Entry(addr_frame, width=10)
        self.ent_bina.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.ent_kat = ttk.Entry(addr_frame, width=5)
        self.ent_kat.grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.ent_daire = ttk.Entry(addr_frame, width=5)
        self.ent_daire.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        ttk.Label(addr_frame, text="Ek Adres:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.ent_ek_adres = ttk.Entry(addr_frame, width=50)
        self.ent_ek_adres.grid(row=2, column=1, columnspan=3, padx=5, pady=2)

        tel_frame = ttk.LabelFrame(self, text="Telefonlar")
        tel_frame.pack(fill=tk.X, pady=5)
        self.tels = {}
        labels = [("Ev", 0, 0), ("İş", 0, 2), ("Cep-1", 1, 0), ("Cep-2", 1, 2), ("Cep-3", 1, 4)]
        for label, r_tel, c in labels:
            ttk.Label(tel_frame, text=f"{label}:").grid(row=r_tel, column=c, padx=5)
            ent = ttk.Entry(tel_frame, width=15)
            ent.grid(row=r_tel, column=c+1, padx=5, pady=2)
            self.tels[label] = ent

        emanet_frame = ttk.LabelFrame(self, text="Emanet Durumu")
        emanet_frame.pack(fill=tk.X, pady=5)
        current_row = 0
        for grup_adi, items in EMANET_UI_GRUPLARI:
            ttk.Label(emanet_frame, text=f"{grup_adi}:",
                      font=("Arial", 9, "bold")).grid(
                row=current_row, column=0, columnspan=6, sticky=tk.W, padx=5, pady=(3, 0))
            current_row += 1
            for i, (label, key) in enumerate(items):
                ttk.Label(emanet_frame, text=f"{label}:").grid(
                    row=current_row, column=i*2, sticky=tk.W, padx=(5 if i==0 else 8), pady=2)
                lbl = ttk.Label(emanet_frame, text="0", foreground="blue",
                               font=("Arial", 9, "bold"))
                lbl.grid(row=current_row, column=i*2+1, sticky=tk.W, padx=2)
                self.emanet_labels[key] = lbl
            current_row += 1
        current_row += 1
        btn_emanet = ttk.Button(emanet_frame, text="Emanet Ekle/Düzenle",
                                command=lambda: self.app.open_emanet_ekleme())
        btn_emanet.grid(row=current_row, column=0, columnspan=6, pady=8)

        summary_frame = ttk.LabelFrame(self, text="Finansal Durum")
        summary_frame.pack(fill=tk.X, pady=5)
        ttk.Label(summary_frame, text="Toplam Borç:", font=("Arial", 10, "bold")).pack(pady=2)
        self.lbl_borc = ttk.Label(summary_frame, text="0,00 TL",
                                  style="Red.TLabel")
        self.lbl_borc.pack(pady=2)
        ttk.Label(summary_frame, text="Tüp Durumu:").pack(pady=(5, 0))
        self.progress_tup = ttk.Progressbar(summary_frame, orient=tk.HORIZONTAL,
                                            length=200, mode='determinate')
        self.progress_tup.pack(pady=2)
        self.lbl_tup_uyari = ttk.Label(summary_frame, text="", foreground="blue")
        self.lbl_tup_uyari.pack(pady=(0, 5))

        ttk.Label(self, text="Notlar:").pack(anchor=tk.W)
        self.txt_notlar = tk.Text(self, height=2, font=("Arial", 10))
        self.txt_notlar.pack(fill=tk.X, pady=5)

    def _tarih_sec(self, tarih):
        self.ent_kayit_tar.delete(0, tk.END)
        self.ent_kayit_tar.insert(0, tarih)

    def form_doldur(self, details):
        self.selected_abone_id = details['info']['id']
        self.clear_form(keep_selection=True)
        info = details['info']
        self.ent_abone_no.insert(0, info.get('abone_no', ''))
        self.ent_kayit_tar.insert(0, info.get('kayit_tarihi', ''))
        self.ent_ad.insert(0, info.get('ad', ''))
        self.ent_soyad.insert(0, info.get('soyad', ''))
        self.cmb_servis.set(info.get('servis_elemani', ''))
        self.cmb_tip.set(info.get('abone_tipi', 'Ev Abonesi'))
        self.ent_ek_adres.insert(0, info.get('ek_adres', ''))
        self.cmb_mah.set(info.get('mahalle', ''))
        self.ent_sokak.insert(0, info.get('sokak', ''))
        self.ent_bina.insert(0, info.get('bina_no', ''))
        self.ent_kat.insert(0, info.get('kat', ''))
        self.ent_daire.insert(0, info.get('daire', ''))
        self.ent_son_siparis.config(state="normal")
        self.ent_son_siparis.insert(0, info.get('son_siparis_tarihi', ''))
        self.ent_son_siparis.config(state="readonly")
        self.txt_notlar.insert("1.0", info.get('notlar', '') or '')
        for tel in details.get('tels', []):
            if tel['tel_tipi'] in self.tels:
                self.tels[tel['tel_tipi']].insert(0, tel['numara'])
        self.lbl_borc.config(text=f"{details['bakiye']:.2f} TL")
        self._tup_durumu_guncelle(info.get('son_siparis_tarihi', ''))

    def _tup_durumu_guncelle(self, son_siparis_tarihi):
        from datetime import datetime, date
        TUP_OMRU = 45
        if not son_siparis_tarihi or son_siparis_tarihi.strip() == '':
            self.progress_tup['value'] = 100
            self.lbl_tup_uyari.config(text="Yeni Abone - Tüp Dolu", foreground="green")
            return
        try:
            for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
                try:
                    siparis_tarih = datetime.strptime(son_siparis_tarihi[:10], fmt).date()
                    break
                except ValueError:
                    continue
            else:
                siparis_tarih = date.today()
            gun_gecen = (date.today() - siparis_tarih).days
        except Exception:
            gun_gecen = 0
        yuzde = max(0, 100 - (gun_gecen / TUP_OMRU * 100))
        self.progress_tup['value'] = yuzde
        if gun_gecen >= TUP_OMRU:
            self.lbl_tup_uyari.config(
                text=f"Tüp Bitmiştir! ({gun_gecen} gün)", foreground="red")
        elif gun_gecen >= TUP_OMRU * 0.67:
            self.lbl_tup_uyari.config(
                text=f"Tüp Azalıyor ({100 - int(yuzde)}% gitti)", foreground="orange")
        else:
            kalan_gun = TUP_OMRU - gun_gecen
            self.lbl_tup_uyari.config(
                text=f"Tüp Dolu (%{int(yuzde)} - {kalan_gun} gün kaldı)", foreground="green")
        emanet = details.get('emanet', {})
        for key, lbl in self.emanet_labels.items():
            lbl.config(text=str(emanet.get(key, 0)))

    def clear_form(self, keep_selection=False):
        if not keep_selection:
            self.selected_abone_id = None
        for ent in [self.ent_abone_no, self.ent_kayit_tar, self.ent_ad,
                     self.ent_soyad, self.ent_ek_adres,
                     self.ent_sokak, self.ent_bina,
                     self.ent_kat, self.ent_daire]:
            ent.delete(0, tk.END)
        self.cmb_servis.set('')
        self.cmb_mah.set('')
        self.ent_son_siparis.config(state="normal")
        self.ent_son_siparis.delete(0, tk.END)
        self.ent_son_siparis.config(state="readonly")
        self.txt_notlar.delete("1.0", tk.END)
        for ent in self.tels.values():
            ent.delete(0, tk.END)
        self.lbl_borc.config(text="0,00 TL")
        self.progress_tup['value'] = 0
        self.lbl_tup_uyari.config(text="")
        for lbl in self.emanet_labels.values():
            lbl.config(text="0")

    def get_form_data(self):
        return {
            'abone_no': self.ent_abone_no.get().strip(),
            'ad': self.ent_ad.get().strip(),
            'soyad': self.ent_soyad.get().strip(),
            'servis_elemani': self.cmb_servis.get().strip(),
            'abone_tipi': self.cmb_tip.get(),
            'kayit_tarihi': self.ent_kayit_tar.get().strip(),
            'ek_adres': self.ent_ek_adres.get().strip(),
            'mahalle': self.cmb_mah.get().strip(),
            'sokak': self.ent_sokak.get().strip(),
            'bina_no': self.ent_bina.get().strip(),
            'kat': self.ent_kat.get().strip(),
            'daire': self.ent_daire.get().strip(),
            'notlar': self.txt_notlar.get("1.0", tk.END).strip(),
            'tels': {k: v.get().strip() for k, v in self.tels.items()}
        }
