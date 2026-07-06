import tkinter as tk
from tkinter import ttk, messagebox
from config import TUP_LISTESI, SU_LISTESI

class DepoDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.title("Depo Stoğu Yönetimi")
        self.geometry("700x500")
        self.app = app
        self.db = app.db
        self.depo_service = app.depo_service

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tup_frame = ttk.Frame(notebook)
        notebook.add(tup_frame, text="Tüpler")
        self.tree_tup = self._setup_tree(tup_frame, TUP_LISTESI)

        su_frame = ttk.Frame(notebook)
        notebook.add(su_frame, text="Sular (19 LT)")
        self.tree_su = self._setup_tree(su_frame, SU_LISTESI)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="Seçili Ürünü Düzenle",
                  command=self._duzelt).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Tüm Stokları Sıfırla",
                  command=self._sifirla).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Kapat", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        self._refresh()

    def _setup_tree(self, parent, urunler):
        columns = ("urun", "dolu", "bos", "toplam")
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        tree.heading("urun", text="Ürün Adı")
        tree.heading("dolu", text="Dolu Stok")
        tree.heading("bos", text="Boş Stok")
        tree.heading("toplam", text="Toplam")
        tree.column("urun", width=200)
        tree.column("dolu", width=100, anchor=tk.CENTER)
        tree.column("bos", width=100, anchor=tk.CENTER)
        tree.column("toplam", width=100, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True)
        tree.urunler = urunler
        return tree

    def _refresh(self):
        durum = self.db.get_depo_durumu()
        for tree in [self.tree_tup, self.tree_su]:
            for item in tree.get_children():
                tree.delete(item)
        for urun in durum:
            if urun['urun_adi'] in TUP_LISTESI:
                tree = self.tree_tup
            else:
                tree = self.tree_su
            tree.insert("", tk.END, values=(
                urun['urun_adi'], urun['dolu_adet'], urun['bos_adet'],
                urun['dolu_adet'] + urun['bos_adet']))

    def _duzelt(self):
        notebook = self.tree_tup.master.master
        current_tab = notebook.index(notebook.select())
        tree = self.tree_tup if current_tab == 0 else self.tree_su
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin!")
            return
        item = tree.item(sel[0])['values']
        urun = item[0]
        dialog = tk.Toplevel(self)
        dialog.title(f"Stok Güncelle - {urun}")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        ttk.Label(dialog, text=f"Ürün: {urun}", font=("Arial", 10, "bold")).pack(pady=10)
        ttk.Label(dialog, text="Dolu Adet:").pack()
        ent_dolu = ttk.Entry(dialog)
        ent_dolu.insert(0, str(item[1]))
        ent_dolu.pack(pady=5)
        ttk.Label(dialog, text="Boş Adet:").pack()
        ent_bos = ttk.Entry(dialog)
        ent_bos.insert(0, str(item[2]))
        ent_bos.pack(pady=5)

        def save():
            try:
                d = int(ent_dolu.get())
                b = int(ent_bos.get())
                if d < 0 or b < 0:
                    messagebox.showwarning("Uyarı", "Negatif değer girilemez!")
                    return
                self.db.update_stok(urun, d, b)
                self.app.right_panel.son_islem_ekle(f"Stok güncellendi: {urun} ({d}/{b})")
                self._refresh()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz sayı!")
        ttk.Button(dialog, text="Kaydet", command=save).pack(pady=15)
        dialog.transient(self)
        dialog.grab_set()

    def _sifirla(self):
        if messagebox.askyesno("Onay", "Tüm stokları sıfırlamak istediğinize emin misiniz?\nBu işlem geri alınamaz!"):
            self.depo_service.stok_sifirla()
            self._refresh()
            self.app.right_panel.son_islem_ekle("Tüm stoklar sıfırlandı")
            messagebox.showinfo("Başarılı", "Tüm stoklar sıfırlandı.")
