import tkinter as tk
from tkinter import ttk, messagebox

class SatisDuzeltmeDialog(tk.Toplevel):
    def __init__(self, parent, app, islem_id=None):
        super().__init__(parent)
        self.title("Satış Düzeltme")
        self.geometry("600x500")
        self.app = app
        self.db = app.db
        self.borc_service = app.borc_service
        self._setup_ui()
        if islem_id:
            self._yukle_islem(islem_id)

    def _setup_ui(self):
        ttk.Label(self, text="Abone Seçiniz:").pack(pady=(10, 2), padx=10, anchor=tk.W)
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10)
        self.ent_ara = ttk.Entry(search_frame)
        self.ent_ara.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(search_frame, text="Ara", command=self._ara).pack(side=tk.RIGHT)
        self.lbl_abone = ttk.Label(self, text="", font=("Arial", 10, "bold"))
        self.lbl_abone.pack(pady=5)

        columns = ("id", "tarih", "tutar", "tur", "urun", "adet")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=8)
        self.tree.heading("id", text="ID")
        self.tree.heading("tarih", text="Tarih")
        self.tree.heading("tutar", text="Tutar")
        self.tree.heading("tur", text="İşlem")
        self.tree.heading("urun", text="Ürün")
        self.tree.heading("adet", text="Adet")
        for col in columns:
            self.tree.column(col, width=80, anchor=tk.CENTER)
        self.tree.column("tarih", width=120)
        self.tree.column("urun", width=120)
        self.tree.column("tur", width=70)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._secim_yap)

        edit_frame = ttk.LabelFrame(self, text="Düzeltme")
        edit_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(edit_frame, text="Eski Tutar:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.lbl_eski = ttk.Label(edit_frame, text="0,00 TL")
        self.lbl_eski.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(edit_frame, text="Yeni Tutar:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.ent_yeni_tutar = ttk.Entry(edit_frame, width=15)
        self.ent_yeni_tutar.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(edit_frame, text="Yeni Açıklama:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.ent_yeni_aciklama = ttk.Entry(edit_frame, width=30)
        self.ent_yeni_aciklama.grid(row=2, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="İptal", command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Düzeltmeyi Kaydet", command=self._kaydet,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    def _yukle_islem(self, islem_id):
        islem = self.db.get_islem(islem_id)
        if islem:
            details = self.db.get_abone_details(islem['abone_id'])
            if details:
                ad = f"{details['info']['ad']} {details['info']['soyad']}"
                self.lbl_abone.config(text=f"Abone: {ad}")
                self._get_islemler(islem['abone_id'])
                self.tree.selection_set(str(islem_id))
                self._secim_yap()

    def _ara(self):
        query = self.ent_ara.get().strip()
        if not query:
            return
        aboneler = self.db.get_all_aboneler(query)
        if not aboneler:
            messagebox.showinfo("Bilgi", "Abone bulunamadı!")
            return
        if len(aboneler) == 1:
            ab = aboneler[0]
            self.lbl_abone.config(text=f"Abone: {ab['ad']} {ab['soyad']}")
            self.current_abone_id = ab['id']
            self._get_islemler(ab['id'])
        else:
            self._show_abone_list(aboneler)

    def _show_abone_list(self, aboneler):
        dialog = tk.Toplevel(self)
        dialog.title("Abone Seç")
        dialog.geometry("300x400")
        lb = tk.Listbox(dialog)
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for ab in aboneler:
            lb.insert(tk.END, f"{ab['abone_no']} - {ab['ad']} {ab['soyad']}")

        def sec():
            sel = lb.curselection()
            if sel:
                ab = aboneler[sel[0]]
                self.lbl_abone.config(text=f"Abone: {ab['ad']} {ab['soyad']}")
                self.current_abone_id = ab['id']
                self._get_islemler(ab['id'])
                dialog.destroy()

        ttk.Button(dialog, text="Seç", command=sec).pack(pady=10)

    def _get_islemler(self, abone_id):
        for item in self.tree.get_children():
            self.tree.delete(item)
        islemler = self.db.get_islem_gecmisi(abone_id)
        for islem in islemler:
            self.tree.insert("", tk.END, iid=str(islem['id']), values=(
                islem['id'], islem['tarih'], f"{islem['tutar']:,.2f}",
                islem['islem_turu'], islem.get('urun_adi', ''),
                islem.get('adet', 0)))

    def _secim_yap(self, event=None):
        sel = self.tree.selection()
        if sel:
            islem_id = int(sel[0])
            islem = self.db.get_islem(islem_id)
            if islem:
                self.selected_islem_id = islem_id
                self.lbl_eski.config(text=f"{islem['tutar']:,.2f} TL")
                self.ent_yeni_tutar.delete(0, tk.END)
                self.ent_yeni_tutar.insert(0, f"{islem['tutar']:,.2f}")
                self.ent_yeni_aciklama.delete(0, tk.END)
                self.ent_yeni_aciklama.insert(0, islem.get('aciklama', ''))

    def _kaydet(self):
        if not hasattr(self, 'selected_islem_id') or not self.selected_islem_id:
            messagebox.showwarning("Uyarı", "Lütfen bir işlem seçin!")
            return
        try:
            yeni_tutar = float(self.ent_yeni_tutar.get().replace(',', '.'))
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir tutar giriniz!")
            return
        yeni_aciklama = self.ent_yeni_aciklama.get()
        try:
            self.borc_service.satis_duzelt(self.selected_islem_id, yeni_tutar, yeni_aciklama)
            self.app.right_panel.son_islem_ekle("Satış düzeltildi (ID: {})".format(self.selected_islem_id))
            messagebox.showinfo("Başarılı", "İşlem düzeltildi.")
            self._get_islemler(self.current_abone_id)
            self.app.right_panel.refresh_list()
        except Exception as e:
            messagebox.showerror("Hata", str(e))
