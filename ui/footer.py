import tkinter as tk
from tkinter import ttk
from enum import Enum

class AppState(Enum):
    BOS = 'bos'
    ABONE_SECILI = 'abone_secili'
    YENI_ABONE = 'yeni_abone'
    DUZENLEME = 'duzenleme'
    DIALOG_ACIK = 'dialog_acik'

class FooterPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Footer.TFrame", padding=5)
        self.app = app
        self.pack(side=tk.BOTTOM, fill=tk.X)

        btn_frame = ttk.Frame(self, style="Footer.TFrame")
        btn_frame.pack(expand=True)

        self.buttons = {}

        btn_configs = [
            ("btn_ara", "🔍 Abone Ara", self._on_ara),
            ("btn_borc_ekle", "💰 Borç Ekleme (F1)", self._on_borc_ekle),
            ("btn_borc_defteri", "📋 Borç Defteri (F2)", self._on_borc_defteri),
            ("btn_borc_dus", "💳 Borç Düşme (F3)", self._on_borc_dus),
            ("btn_emanet", "📦 Emanet (F4)", self._on_emanet),
            ("btn_pesin", "🛒 Peşin Satış (F5)", self._on_pesin_satis),
            ("btn_satis_duzelt", "✏️ Satış Düzelt (F6)", self._on_satis_duzelt),
            ("btn_kaydet", "💾 Kaydet (Ctrl+S)", self._on_kaydet),
            ("btn_yeni_abone", "➕ Yeni Abone (Ctrl+N)", self._on_yeni_abone),
        ]

        for key, text, cmd in btn_configs:
            btn = ttk.Button(btn_frame, text=text, command=cmd, style="Accent.TButton")
            btn.pack(side=tk.LEFT, padx=3)
            self.buttons[key] = btn

        self._update_buttons(AppState.BOS)

    def _update_buttons(self, state):
        abone_gerekli = ['btn_borc_ekle', 'btn_borc_defteri', 'btn_borc_dus',
                         'btn_emanet', 'btn_satis_duzelt']
        for key in abone_gerekli:
            self.buttons[key].config(state=tk.NORMAL if state == AppState.ABONE_SECILI else tk.DISABLED)
        self.buttons['btn_kaydet'].config(state=tk.NORMAL if state in [AppState.ABONE_SECILI, AppState.YENI_ABONE] else tk.DISABLED)
        self.buttons['btn_yeni_abone'].config(state=tk.NORMAL if state != AppState.YENI_ABONE else tk.DISABLED)
        self.buttons['btn_ara'].config(state=tk.NORMAL)

    def on_state_change(self, data):
        state_str = data.get('yeni', 'bos')
        try:
            state = AppState(state_str)
            self._update_buttons(state)
        except ValueError:
            pass

    def _on_ara(self):
        self.app.right_panel.ent_search.focus_set()

    def _on_borc_ekle(self):
        self.app.open_borc_ekleme()

    def _on_borc_defteri(self):
        self.app.open_borc_defteri()

    def _on_borc_dus(self):
        self.app.open_borc_dusme()

    def _on_emanet(self):
        self.app.open_emanet_ekleme()

    def _on_pesin_satis(self):
        self.app.open_pesin_satis()

    def _on_satis_duzelt(self):
        self.app.open_satis_duzeltme()

    def _on_kaydet(self):
        self.app.save_abone()

    def _on_yeni_abone(self):
        self.app.clear_form()
        self.app.state_manager.set_state(AppState.YENI_ABONE)
