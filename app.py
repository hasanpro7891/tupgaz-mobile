import tkinter as tk
from tkinter import ttk, messagebox
from config import APP_TITLE, DB_PATH, COLOR_HEADER_BG, COLOR_HEADER_FG
from data.database import Database
from data.db_init import init_db
from services.event_bus import EventBus
from services.abone_service import AboneService
from services.borc_service import BorcService
from services.depo_service import DepoService
from services.emanet_service import EmanetService
from services.fiyat_service import FiyatService
from services.rapor_service import RaporService
from services.gider_service import GiderService
from services.yedek_service import YedekService
from services.pesin_satis_service import PesinSatisService
from ui.styles import setup_styles
from ui.header import HeaderPanel
from ui.left_panel import LeftPanel
from ui.right_panel import RightPanel
from ui.footer import FooterPanel, AppState


class StateManager:
    BOS = 'bos'
    ABONE_SECILI = 'abone_secili'
    YENI_ABONE = 'yeni_abone'
    DUZENLEME = 'duzenleme'
    DIALOG_ACIK = 'dialog_acik'

    def __init__(self, event_bus):
        self.current = self.BOS
        self.event_bus = event_bus

    def set_state(self, new_state):
        old = self.current
        self.current = new_state
        self.event_bus.publish('STATE_CHANGED', {'eski': old, 'yeni': new_state})

    def get_state(self):
        return self.current


class TupcularKraliApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1200x850")
        self.root.minsize(1000, 700)

        init_db(DB_PATH)
        self.db = Database()

        self.event_bus = EventBus()
        self.state_manager = StateManager(self.event_bus)

        self.abone_service = AboneService(self.db, self.event_bus)
        self.borc_service = BorcService(self.db, self.event_bus)
        self.depo_service = DepoService(self.db, self.event_bus)
        self.emanet_service = EmanetService(self.db, self.event_bus)
        self.fiyat_service = FiyatService(self.db, self.event_bus)
        self.rapor_service = RaporService(self.db)
        self.gider_service = GiderService(self.db, self.event_bus)
        self.yedek_service = YedekService(self.db, self.event_bus)
        self.pesin_satis_service = PesinSatisService(self.db, self.event_bus)

        setup_styles()

        self._setup_menu()
        self._setup_ui()
        self._setup_events()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after_id = self.root.after(500, self._initial_checks)

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        dosya_menu = tk.Menu(menubar, tearoff=0)
        dosya_menu.add_command(label="Depo Stoğu", command=self.open_depo, accelerator="Ctrl+D")
        dosya_menu.add_command(label="Fiyat Listesi", command=self.open_fiyatlar, accelerator="Ctrl+F")
        dosya_menu.add_separator()
        dosya_menu.add_command(label="Gider Ekle", command=self.open_gider, accelerator="Ctrl+G")
        dosya_menu.add_command(label="Yedek Al", command=self.open_yedek, accelerator="Ctrl+B")
        dosya_menu.add_separator()
        dosya_menu.add_command(label="Çıkış", command=self._on_close, accelerator="Alt+F4")
        menubar.add_cascade(label="Dosya", menu=dosya_menu)

        islem_menu = tk.Menu(menubar, tearoff=0)
        islem_menu.add_command(label="Borç Ekleme", command=lambda: self._check_abone_and_open(self.open_borc_ekleme))
        islem_menu.add_command(label="Borç Düşme", command=lambda: self._check_abone_and_open(self.open_borc_dusme))
        islem_menu.add_command(label="Borç Defteri", command=lambda: self._check_abone_and_open(self.open_borc_defteri))
        islem_menu.add_command(label="Emanet İşlemi", command=lambda: self._check_abone_and_open(self.open_emanet_ekleme))
        islem_menu.add_command(label="Satış Düzeltme", command=self.open_satis_duzeltme)
        islem_menu.add_separator()
        islem_menu.add_command(label="Peşin Satış", command=self.open_pesin_satis)
        menubar.add_cascade(label="İşlemler", menu=islem_menu)

        menubar.add_command(label="Raporlar", command=self.open_rapor)
        menubar.add_command(label="Yardım", command=self._show_help)

    def _setup_ui(self):
        self.header = HeaderPanel(self.root, self)

        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.left_panel = LeftPanel(self.main_container, self)
        self.right_panel = RightPanel(self.main_container, self)

        self.footer = FooterPanel(self.root, self)

        self._setup_keyboard_shortcuts()
        self.header.refresh_from_db()
        self.right_panel.refresh_list()

    def _setup_events(self):
        self.event_bus.subscribe('STATE_CHANGED', self.footer.on_state_change)
        self.event_bus.subscribe('VERI_DEGISTI', lambda d: self.header.refresh_from_db())
        self.event_bus.subscribe('ABONE_EKLENDI', lambda d: self._on_veri_degisti(d))
        self.event_bus.subscribe('ABONE_SILINDI', lambda d: self._on_veri_degisti(d))
        self.event_bus.subscribe('ABONE_GUNCELLENDI', lambda d: self._on_veri_degisti(d))

    def _on_veri_degisti(self, data):
        self.header.refresh_from_db()
        self.right_panel.refresh_list()
        if self.left_panel.selected_abone_id:
            details = self.db.get_abone_details(self.left_panel.selected_abone_id)
            if details:
                self.left_panel.form_doldur(details)

    def _setup_keyboard_shortcuts(self):
        self.root.bind('<F1>', lambda e: self._check_abone_and_open(self.open_borc_ekleme))
        self.root.bind('<F2>', lambda e: self._check_abone_and_open(self.open_borc_defteri))
        self.root.bind('<F3>', lambda e: self._check_abone_and_open(self.open_borc_dusme))
        self.root.bind('<F4>', lambda e: self._check_abone_and_open(self.open_emanet_ekleme))
        self.root.bind('<F5>', lambda e: self.open_pesin_satis())
        self.root.bind('<F6>', lambda e: self.open_satis_duzeltme())
        self.root.bind('<Control-s>', lambda e: self.save_abone())
        self.root.bind('<Control-n>', lambda e: self.clear_form())
        self.root.bind('<Control-d>', lambda e: self.open_depo())
        self.root.bind('<Control-f>', lambda e: self.open_fiyatlar())
        self.root.bind('<Control-g>', lambda e: self.open_gider())
        self.root.bind('<Control-b>', lambda e: self.open_yedek())
        self.root.bind('<Escape>', lambda e: self._focus_search())

    def _focus_search(self):
        self.right_panel.ent_search.focus_set()

    def _check_abone_and_open(self, callback):
        if not self.left_panel.selected_abone_id:
            messagebox.showwarning("Uyarı", "Lütfen önce bir abone seçin!")
            self.right_panel.ent_search.focus_set()
            return
        callback()

    def _initial_checks(self):
        girilmemis = self.fiyat_service.get_fiyat_girilmemis_urunler()
        if girilmemis:
            if messagebox.askyesno("Fiyat Uyarısı",
                    f"Aşağıdaki ürünlerin fiyatı henüz girilmemiş:\n\n"
                    + "\n".join(f"  • {u}" for u in girilmemis) +
                    "\n\nBorç eklemeden önce fiyatları girmek ister misiniz?"):
                self.open_fiyatlar()
        self.yedek_service.otomatik_yedek_kontrol()

    def _on_close(self):
        if messagebox.askokcancel("Çıkış", "Programdan çıkmak istediğinize emin misiniz?"):
            if hasattr(self, 'after_id'):
                self.root.after_cancel(self.after_id)
            self.root.destroy()

    def _show_help(self):
        messagebox.showinfo("Yardım",
            "Tüpçüler Kralı v2.0\n\n"
            "Kısayollar:\n"
            "  F1  - Borç Ekleme\n"
            "  F2  - Borç Defteri\n"
            "  F3  - Borç Düşme\n"
            "  F4  - Emanet İşlemi\n"
            "  F5  - Peşin Satış\n"
            "  F6  - Satış Düzeltme\n"
            "  Ctrl+S - Kaydet\n"
            "  Ctrl+N - Yeni Abone\n"
            "  Ctrl+D - Depo Stoğu\n"
            "  Ctrl+F - Fiyat Listesi\n"
            "  Ctrl+G - Gider Ekle\n"
            "  Ctrl+B - Yedek Al\n"
            "  Esc - Aramaya odaklan\n\n"
            "Ürünler: 5 LPG Tüp + 2 Su (19 LT)\n"
            "Her işlemde stok otomatik güncellenir.")

    def save_abone(self):
        abone_id = self.left_panel.selected_abone_id
        data = self.left_panel.get_form_data()
        if not data['abone_no']:
            messagebox.showwarning("Uyarı", "Abone No boş bırakılamaz!")
            self.left_panel.ent_abone_no.focus_set()
            return
        if not data['ad'] or len(data['ad']) < 2:
            messagebox.showwarning("Uyarı", "Ad en az 2 karakter olmalıdır!")
            self.left_panel.ent_ad.focus_set()
            return
        if not data.get('kayit_tarihi'):
            from datetime import datetime
            data['kayit_tarihi'] = datetime.now().strftime("%d.%m.%Y")
        try:
            if abone_id:
                self.abone_service.abone_guncelle(abone_id, data)
                messagebox.showinfo("Başarılı", "Abone güncellendi.")
            else:
                if self.db.abone_no_var_mi(data['abone_no']):
                    messagebox.showwarning("Uyarı",
                        f"{data['abone_no']} numarası zaten kayıtlı!\nFarklı bir numara deneyin.")
                    self.left_panel.ent_abone_no.focus_set()
                    return
                yeni_id = self.abone_service.yeni_abone(data)
                self.left_panel.selected_abone_id = yeni_id
                messagebox.showinfo("Başarılı", "Yeni abone eklendi.")
            self.right_panel.refresh_list()
            detay = self.db.get_abone_details(self.left_panel.selected_abone_id)
            if detay:
                self.left_panel.form_doldur(detay)
            self.state_manager.set_state(AppState.ABONE_SECILI)
        except Exception as e:
            messagebox.showerror("Hata", f"Kayıt başarısız:\n{e}")

    def clear_form(self):
        self.left_panel.clear_form()
        self.state_manager.set_state(AppState.YENI_ABONE)
        self.right_panel.tree.selection_remove(self.right_panel.tree.selection())

    def open_borc_ekleme(self):
        abone_id = self.left_panel.selected_abone_id
        if not abone_id:
            return
        ad = f"{self.left_panel.ent_ad.get()} {self.left_panel.ent_soyad.get()}".strip()
        from ui.dialogs.borc_ekleme import BorcEklemeDialog
        BorcEklemeDialog(self.root, self, abone_id, ad or "Abone")

    def open_borc_defteri(self):
        abone_id = self.left_panel.selected_abone_id
        if not abone_id:
            return
        ad = f"{self.left_panel.ent_ad.get()} {self.left_panel.ent_soyad.get()}".strip()
        from ui.dialogs.borc_defteri import BorcDefteriDialog
        BorcDefteriDialog(self.root, self, abone_id, ad or "Abone")

    def open_borc_dusme(self):
        abone_id = self.left_panel.selected_abone_id
        if not abone_id:
            return
        ad = f"{self.left_panel.ent_ad.get()} {self.left_panel.ent_soyad.get()}".strip()
        from ui.dialogs.borc_dusme import BorcDusmeDialog
        BorcDusmeDialog(self.root, self, abone_id, ad or "Abone")

    def open_emanet_ekleme(self):
        abone_id = self.left_panel.selected_abone_id
        if not abone_id:
            return
        ad = f"{self.left_panel.ent_ad.get()} {self.left_panel.ent_soyad.get()}".strip()
        from ui.dialogs.emanet_ekleme import EmanetEklemeDialog
        EmanetEklemeDialog(self.root, self, abone_id, ad or "Abone")

    def open_pesin_satis(self):
        from ui.dialogs.pesin_satis_dialog import PesinSatisDialog
        PesinSatisDialog(self.root, self)

    def open_satis_duzeltme(self):
        from ui.dialogs.satis_duzeltme import SatisDuzeltmeDialog
        SatisDuzeltmeDialog(self.root, self)

    def open_depo(self):
        from ui.dialogs.depo_dialog import DepoDialog
        DepoDialog(self.root, self)

    def open_fiyatlar(self):
        from ui.dialogs.fiyat_dialog import FiyatListesiDialog
        FiyatListesiDialog(self.root, self)

    def open_gider(self):
        from ui.dialogs.gider_dialog import GiderDialog
        GiderDialog(self.root, self)

    def open_rapor(self):
        from ui.dialogs.rapor_dialog import RaporDialog
        RaporDialog(self.root, self)

    def open_yedek(self):
        from ui.dialogs.yedek_dialog import YedekDialog
        YedekDialog(self.root, self)
