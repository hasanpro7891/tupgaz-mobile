import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from config import YEDEK_KLASORU

class YedekDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.title("Yedek Alma")
        self.geometry("550x400")
        self.resizable(False, False)
        self.app = app
        self.yedek_service = app.yedek_service
        self._setup_ui()

    def _setup_ui(self):
        ttk.Label(self, text="💾 Yedek Alma", font=("Arial", 14, "bold"),
                 foreground="#8B0000").pack(pady=(10, 5))

        info_frame = ttk.LabelFrame(self, text="Veritabanı Bilgisi")
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        db_path = self.yedek_service.db.db_path
        boyut = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        ttk.Label(info_frame, text=f"Dosya: {db_path}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(info_frame, text=f"Boyut: {boyut:,} bytes ({boyut/1024:.1f} KB)").pack(anchor=tk.W, padx=10, pady=2)

        path_frame = ttk.LabelFrame(self, text="Hedef Klasör")
        path_frame.pack(fill=tk.X, padx=20, pady=10)

        self.ent_klasor = ttk.Entry(path_frame, width=50)
        self.ent_klasor.insert(0, YEDEK_KLASORU)
        self.ent_klasor.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="📁 Gözat", command=self._gözat).pack(side=tk.RIGHT, padx=5)

        ttk.Button(self, text="💾 Yedek Al", command=self._yedek_al,
                  style="Accent.TButton").pack(pady=10)

        gecmis_frame = ttk.LabelFrame(self, text="Son Yedekler")
        gecmis_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.list_gecmis = tk.Listbox(gecmis_frame, height=6, font=("Arial", 8))
        self.list_gecmis.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._gecmis_yukle()

    def _gözat(self):
        klasor = filedialog.askdirectory(initialdir=YEDEK_KLASORU)
        if klasor:
            self.ent_klasor.delete(0, tk.END)
            self.ent_klasor.insert(0, klasor)

    def _yedek_al(self):
        try:
            hedef = self.ent_klasor.get()
            yedek_yolu = self.yedek_service.yedek_al(hedef_klasor=hedef)
            self.app.right_panel.son_islem_ekle(f"Yedek alındı: {os.path.basename(yedek_yolu)}")
            messagebox.showinfo("Başarılı", f"Yedek başarıyla alındı:\n{yedek_yolu}")
            self._gecmis_yukle()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _gecmis_yukle(self):
        self.list_gecmis.delete(0, tk.END)
        try:
            gecmis = self.yedek_service.get_gecmis(10)
            for g in gecmis:
                durum = "✅" if g['durum'] == 'Başarılı' else "❌"
                self.list_gecmis.insert(tk.END,
                    f"{durum} {g['tarih']} - {g['dosya_adi']} ({g['dosya_boyutu']//1024} KB)")
        except Exception:
            self.list_gecmis.insert(tk.END, "(yedek geçmişi bulunamadı)")
