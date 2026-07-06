import tkinter as tk
from tkinter import ttk

class RightPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10, width=380, relief="ridge")
        self.app = app
        self.pack(side=tk.RIGHT, fill=tk.Y)
        self.pack_propagate(False)

        self.search_kriter = tk.StringVar(value="tumu")

        search_frame = ttk.LabelFrame(self, text="Abone Ara")
        search_frame.pack(fill=tk.X, pady=(0, 5))

        self.ent_search = ttk.Entry(search_frame, style="Search.TEntry")
        self.ent_search.pack(fill=tk.X, padx=5, pady=(5, 2))
        self.ent_search.bind("<KeyRelease>", lambda e: self._on_search())

        kriter_frame = ttk.Frame(search_frame)
        kriter_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        for i, (text, val) in enumerate([("Tümü", "tumu"), ("Abone No", "abone_no"),
                                          ("Ad", "ad"), ("Soyad", "soyad")]):
            rb = ttk.Radiobutton(kriter_frame, text=text, variable=self.search_kriter,
                                 value=val, command=self._on_search)
            rb.grid(row=0, column=i, padx=3)

        self.tree = ttk.Treeview(self, columns=("no", "ad", "soyad", "borc"),
                                 show="headings", height=15)
        self.tree.heading("no", text="Ab.No")
        self.tree.heading("ad", text="Adı")
        self.tree.heading("soyad", text="Soyadı")
        self.tree.heading("borc", text="Borç (TL)")
        self.tree.column("no", width=65, anchor=tk.CENTER)
        self.tree.column("ad", width=95)
        self.tree.column("soyad", width=95)
        self.tree.column("borc", width=85, anchor=tk.E)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(relx=1, rely=0.5, relheight=0.6, anchor=tk.E)

        self.lbl_count = ttk.Label(self, text="Toplam: 0 abone", font=("Arial", 8))
        self.lbl_count.pack(anchor=tk.W)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        islem_frame = ttk.LabelFrame(self, text="Son İşlemler")
        islem_frame.pack(fill=tk.BOTH, expand=True)

        self.list_islemler = tk.Listbox(islem_frame, height=6, font=("Arial", 8),
                                        fg="#333", selectbackground="#FFD700")
        self.list_islemler.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.islem_kuyrugu = []

    def _on_search(self):
        self.refresh_list()

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        abone_id = int(selection[0])
        details = self.app.db.get_abone_details(abone_id)
        if details:
            self.app.left_panel.form_doldur(details)
            self.app.state_manager.set_state(self.app.state_manager.ABONE_SECILI)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        query = self.ent_search.get()
        kriter = self.search_kriter.get()
        aboneler = self.app.db.get_all_aboneler(query if query else None, kriter)
        for ab in aboneler:
            tag = 'borclu' if ab.get('bakiye', 0) > 0 else 'temiz'
            self.tree.insert("", tk.END, iid=str(ab['id']),
                             values=(ab['abone_no'], ab['ad'], ab['soyad'],
                                     f"{ab.get('bakiye', 0):.2f}"),
                             tags=(tag,))
            if ab.get('bakiye', 0) > 0:
                self.tree.tag_configure('borclu', foreground='#CC0000')
            else:
                self.tree.tag_configure('temiz', foreground='#006600')
        self.lbl_count.config(text=f"Toplam: {len(aboneler)} abone")

    def son_islem_ekle(self, mesaj):
        from datetime import datetime
        saat = datetime.now().strftime("%H:%M")
        metin = f"[{saat}] {mesaj}"
        self.islem_kuyrugu.insert(0, metin)
        if len(self.islem_kuyrugu) > 20:
            self.islem_kuyrugu = self.islem_kuyrugu[:20]
        self.list_islemler.delete(0, tk.END)
        for m in self.islem_kuyrugu:
            self.list_islemler.insert(tk.END, m)
