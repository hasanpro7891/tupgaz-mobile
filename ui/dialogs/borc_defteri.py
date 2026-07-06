import tkinter as tk
from tkinter import ttk, messagebox

class BorcDefteriDialog(tk.Toplevel):
    def __init__(self, parent, app, abone_id, abone_ad):
        super().__init__(parent)
        self.title(f"Borç Defteri - {abone_ad}")
        self.geometry("750x500")
        self.app = app
        self.db = app.db
        self.borc_service = app.borc_service
        self.abone_id = abone_id
        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        self.lbl_ozet = ttk.Label(self, text="", font=("Arial", 11, "bold"))
        self.lbl_ozet.pack(pady=10)

        columns = ("tarih", "tutar", "tur", "urun", "adet", "aciklama", "duzeltildi")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        self.tree.heading("tarih", text="Tarih")
        self.tree.heading("tutar", text="Tutar")
        self.tree.heading("tur", text="İşlem")
        self.tree.heading("urun", text="Ürün")
        self.tree.heading("adet", text="Adet")
        self.tree.heading("aciklama", text="Açıklama")
        self.tree.heading("duzeltildi", text="Düz.")
        self.tree.column("tarih", width=120)
        self.tree.column("tutar", width=90, anchor=tk.E)
        self.tree.column("tur", width=90, anchor=tk.CENTER)
        self.tree.column("urun", width=130)
        self.tree.column("adet", width=50, anchor=tk.CENTER)
        self.tree.column("aciklama", width=180)
        self.tree.column("duzeltildi", width=40, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="Borç Düşme", command=self._borc_dus).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Düzelt", command=self._duzelt).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Kapat", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        defter = self.borc_service.borc_defteri(self.abone_id)
        self.lbl_ozet.config(
            text=f"💰 Toplam Borç: {defter['toplam_borc']:,.2f} TL  |  "
                 f"Ödenen: {defter['toplam_odenen']:,.2f} TL  |  "
                 f"Kalan: {defter['guncel_bakiye']:,.2f} TL",
            foreground="#8B0000" if defter['guncel_bakiye'] > 0 else "#006600")
        for islem in defter['islemler']:
            tur = islem['islem_turu']
            tag = 'borc' if tur == 'Borç' else 'tahsilat'
            self.tree.insert("", tk.END, iid=str(islem['id']), values=(
                islem['tarih'], f"{islem['tutar']:,.2f}",
                tur, islem.get('urun_adi', ''),
                islem.get('adet', 0), islem.get('aciklama', ''),
                "✓" if islem.get('duzeltildi', 0) else ""), tags=(tag,))
        self.tree.tag_configure('borc', foreground='#CC0000')
        self.tree.tag_configure('tahsilat', foreground='#006600')

    def _borc_dus(self):
        from ui.dialogs.borc_dusme import BorcDusmeDialog
        BorcDusmeDialog(self, self.app, self.abone_id,
                        f"{self.app.left_panel.ent_ad.get()} {self.app.left_panel.ent_soyad.get()}")
        self._refresh()

    def _duzelt(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir işlem seçin!")
            return
        from ui.dialogs.satis_duzeltme import SatisDuzeltmeDialog
        islem_id = int(selection[0])
        SatisDuzeltmeDialog(self, self.app, islem_id)
        self._refresh()
