import sys
import os
from datetime import datetime

os.environ['KIVY_NO_ARGS'] = '1'

import kivy

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.dropdown import DropDown

from data.mahalleler import SERVIS_ELEMANLARI, get_mersin_mahalleleri

Window.size = (420, 780) if platform != 'android' else Window.size

from config import (
    APP_TITLE, DB_PATH, URUN_LISTESI, TUP_LISTESI, SU_LISTESI,
    EMANET_TIPLERI, EMANET_UI_GRUPLARI, GIDER_KATEGORILERI, ODEME_TIPLERI,
    COLOR_HEADER_BG, COLOR_HEADER_FG, COLOR_KRMIZI, COLOR_YESIL, COLOR_ALTIN
)
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

class ColoredLabel(Label):
    def __init__(self, bg_color=(1,1,1,1), **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg_color)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self._update_rect, size=self._update_rect)
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class AutoCompleteInput(TextInput):
    def __init__(self, items, **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.dropdown = None
        self.bind(text=self._filter)
        self.bind(focus=self._on_focus)

    def _show_items(self, filtered):
        self._dismiss()
        if not filtered or not self.get_parent_window():
            return
        self.dropdown = DropDown()
        for item in filtered[:12]:
            btn = Button(text=item, size_hint_y=None, height=dp(38),
                        background_normal='', background_color=(0.25, 0.25, 0.25, 1))
            btn.bind(on_release=lambda btn, t=item: self._select(t))
            self.dropdown.add_widget(btn)
        Clock.schedule_once(lambda dt: self.dropdown.open(self), 0.05)

    def _on_focus(self, instance, value):
        if value and not self.text.strip():
            self._show_items(self.items)

    def _filter(self, instance, value):
        if not value.strip():
            self._dismiss()
            return
        self._dismiss()
        if not self.get_parent_window():
            return
        filtered = [i for i in self.items if value.lower() in i.lower()]
        if not filtered:
            return
        self._show_items(filtered)

    def _dismiss(self):
        if self.dropdown:
            self.dropdown.dismiss()
            self.dropdown = None

    def _select(self, text):
        self.text = text
        self._dismiss()
        self.focus = False


def baslik_btn(text, on_press, size_hint_y=None, height=None):
    btn = Button(
        text=text, size_hint_y=size_hint_y, height=height,
        font_size=sp(14), bold=True,
        background_color=(0.55, 0, 0, 1),
        color=(1, 0.85, 0, 1),
        background_normal=''
    )
    btn.bind(on_press=on_press)
    return btn

def normal_btn(text, on_press, width=None):
    btn = Button(
        text=text, font_size=sp(13), bold=True,
        size_hint_x=None if width else 1, width=width,
        background_color=(0.55, 0, 0, 1),
        color=(1, 1, 1, 1),
        background_normal=''
    )
    btn.bind(on_press=on_press)
    return btn

class BilgiPopup(Popup):
    def __init__(self, title, mesaj, **kwargs):
        super().__init__(title=title, size_hint=(0.85, 0.4), **kwargs)
        content = BoxLayout(orientation='vertical', padding=dp(10))
        content.add_widget(Label(text=mesaj, font_size=sp(14), halign='center'))
        btn = normal_btn('Tamam', lambda x: self.dismiss())
        content.add_widget(btn)
        self.content = content

class UyariPopup(Popup):
    def __init__(self, title, mesaj, on_ok=None, **kwargs):
        super().__init__(title=title, size_hint=(0.85, 0.35), **kwargs)
        content = BoxLayout(orientation='vertical', padding=dp(10))
        content.add_widget(Label(text=mesaj, font_size=sp(14), halign='center'))
        btn_box = BoxLayout(size_hint_y=0.4, spacing=dp(10))
        if on_ok:
            btn_ok = normal_btn('Evet', lambda x: [on_ok(), self.dismiss()])
            btn_box.add_widget(btn_ok)
        btn_no = normal_btn('Hayır', lambda x: self.dismiss())
        btn_box.add_widget(btn_no)
        content.add_widget(btn_box)
        self.content = content

class FormSatir(BoxLayout):
    def __init__(self, etiket, widget, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(42), spacing=dp(5), **kwargs)
        self.add_widget(Label(text=etiket, size_hint_x=0.35, font_size=sp(13), halign='left'))
        self.add_widget(widget)

class TarihSecPopup(Popup):
    def __init__(self, on_select, **kwargs):
        super().__init__(title='Tarih Seç', size_hint=(0.7, 0.35), **kwargs)
        self.on_select = on_select
        from datetime import date
        bugun = date.today()
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        row = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=None, height=dp(44))
        row.add_widget(Label(text='Gün:', font_size=sp(14)))
        self.spn_gun = Spinner(text=str(bugun.day), values=[str(i) for i in range(1, 32)],
                               size_hint_y=None, height=dp(40))
        row.add_widget(self.spn_gun)
        row.add_widget(Label(text='Ay:', font_size=sp(14)))
        self.spn_ay = Spinner(text=str(bugun.month), values=[str(i) for i in range(1, 13)],
                              size_hint_y=None, height=dp(40))
        row.add_widget(self.spn_ay)
        row.add_widget(Label(text='Yıl:', font_size=sp(14)))
        self.spn_yil = Spinner(text=str(bugun.year), values=[str(i) for i in range(2020, 2036)],
                               size_hint_y=None, height=dp(40))
        row.add_widget(self.spn_yil)
        content.add_widget(row)
        btn_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(48))
        btn_row.add_widget(normal_btn('Bugün', lambda x: self._sec(bugun)))
        btn_row.add_widget(normal_btn('Seç', lambda x: self._sec(date.today())))
        content.add_widget(btn_row)
        self.content = content
        self.bugun = bugun

    def _sec(self, secilen):
        try:
            from datetime import date
            d = date(int(self.spn_yil.text), int(self.spn_ay.text), int(self.spn_gun.text))
            self.on_select(d.strftime('%d.%m.%Y'))
            self.dismiss()
        except Exception:
            pass


class AnaEkran(Screen):
    pass

class AboneKartScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app
        self.selected_id = None
        self.emanet_labels = {}
        self._build_ui()

    def _build_ui(self):
        main = BoxLayout(orientation='vertical')
        scroll = ScrollView()
        form = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(8), spacing=dp(4))
        form.bind(minimum_height=form.setter('height'))

        header = ColoredLabel(text='ABONE KARTI', bg_color=(0.55, 0, 0, 1),
                             color=(1, 0.85, 0, 1), font_size=sp(16), bold=True,
                             size_hint_y=None, height=dp(36))
        form.add_widget(header)

        self.ent_abone_no = TextInput(text='', multiline=False, font_size=sp(14), size_hint_y=None, height=dp(36))
        form.add_widget(FormSatir('Abone No:', self.ent_abone_no))

        self.ent_kayit_tar = TextInput(text='', multiline=False, font_size=sp(14),
                                       size_hint_y=None, height=dp(36))
        tar_satir = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(42), spacing=dp(3))
        tar_satir.add_widget(Label(text='Kayıt Tar:', size_hint_x=0.35, font_size=sp(13), halign='left'))
        tar_satir.add_widget(self.ent_kayit_tar)
        tar_btn = Button(text='📅', size_hint_x=0.15, font_size=sp(16),
                        background_normal='', background_color=(0.4, 0.4, 0.4, 1))
        tar_btn.bind(on_press=lambda x: self._tarih_sec())
        tar_satir.add_widget(tar_btn)
        form.add_widget(tar_satir)

        self.ent_ad = TextInput(text='', multiline=False, font_size=sp(14), size_hint_y=None, height=dp(36))
        form.add_widget(FormSatir('Ad:', self.ent_ad))

        self.ent_soyad = TextInput(text='', multiline=False, font_size=sp(14), size_hint_y=None, height=dp(36))
        form.add_widget(FormSatir('Soyad:', self.ent_soyad))

        self.ent_servis = AutoCompleteInput(items=SERVIS_ELEMANLARI, text='',
                                            multiline=False, font_size=sp(14),
                                            size_hint_y=None, height=dp(36))
        form.add_widget(FormSatir('Servis:', self.ent_servis))

        self.ent_mah = AutoCompleteInput(items=get_mersin_mahalleleri(), text='',
                                         multiline=False, font_size=sp(14),
                                         size_hint_y=None, height=dp(36))
        form.add_widget(FormSatir('Mahalle:', self.ent_mah))

        self.ent_sokak = TextInput(text='', multiline=False, font_size=sp(14), size_hint_y=None, height=dp(36))
        form.add_widget(FormSatir('Sokak:', self.ent_sokak))

        self.ent_tel = TextInput(text='', multiline=False, font_size=sp(14), size_hint_y=None, height=dp(36))
        form.add_widget(FormSatir('Telefon:', self.ent_tel))

        self.ent_not = TextInput(text='', multiline=True, font_size=sp(13), size_hint_y=None, height=dp(60))
        form.add_widget(FormSatir('Notlar:', self.ent_not))

        form.add_widget(Label(text='', size_hint_y=None, height=dp(4)))

        self.lbl_borc = Label(text='Toplam Borç: 0,00 TL', font_size=sp(18), bold=True,
                             color=(0.8, 0, 0, 1), size_hint_y=None, height=dp(36))
        form.add_widget(self.lbl_borc)

        self.progress_tup = ProgressBar(max=100, value=100, size_hint_y=None, height=dp(16))
        form.add_widget(self.progress_tup)
        self.lbl_tup = Label(text='Tüp Dolu (%100)', font_size=sp(12), size_hint_y=None, height=dp(20))
        form.add_widget(self.lbl_tup)

        self.lbl_emanet = Label(text='Emanet: ---', font_size=sp(13), size_hint_y=None, height=dp(24))
        form.add_widget(self.lbl_emanet)

        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6), padding=(0, dp(6)))
        btn_box.add_widget(normal_btn('KAYDET', self._kaydet))
        btn_box.add_widget(normal_btn('BORÇ EKLE', lambda x: self.app_ref.open_borc_ekle(self.selected_id)))
        btn_box.add_widget(normal_btn('BORÇ DÜŞ', lambda x: self.app_ref.open_borc_dus(self.selected_id)))
        form.add_widget(btn_box)

        btn_box2 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6), padding=(0, dp(6)))
        btn_box2.add_widget(normal_btn('BORÇ DEFTERİ', lambda x: self.app_ref.open_borc_defteri(self.selected_id)))
        btn_box2.add_widget(normal_btn('EMANET', lambda x: self.app_ref.open_emanet(self.selected_id)))
        btn_box2.add_widget(normal_btn('PEŞİN SATIŞ', lambda x: self.app_ref.open_pesin_satis()))
        form.add_widget(btn_box2)

        scroll.add_widget(form)
        main.add_widget(scroll)
        self.add_widget(main)

    def _tarih_sec(self):
        def tarih_secildi(tarih):
            self.ent_kayit_tar.text = tarih
        TarihSecPopup(on_select=tarih_secildi).open()

    def form_doldur(self, details):
        if not details:
            return
        self.selected_id = details['info']['id']
        self.ent_abone_no.text = str(details['info'].get('abone_no', ''))
        self.ent_kayit_tar.text = str(details['info'].get('kayit_tarihi', ''))
        self.ent_ad.text = str(details['info'].get('ad', ''))
        self.ent_soyad.text = str(details['info'].get('soyad', ''))
        self.ent_servis.text = str(details['info'].get('servis_elemani', ''))
        self.ent_mah.text = str(details['info'].get('mahalle', ''))
        self.ent_sokak.text = str(details['info'].get('sokak', ''))
        tels = details.get('tels', [])
        tel_text = ', '.join(t['numara'] for t in tels) if tels else ''
        self.ent_tel.text = tel_text
        self.ent_not.text = str(details['info'].get('notlar', '') or '')
        self.lbl_borc.text = f"Toplam Borç: {details['bakiye']:,.2f} TL"
        self._tup_durumu_guncelle(str(details['info'].get('son_siparis_tarihi', '')))
        emanet = details.get('emanet', {})
        e_text = '  '.join(f"{k}:{v}" for k, v in emanet.items() if v)
        self.lbl_emanet.text = f"Emanet: {e_text}" if e_text else 'Emanet: (yok)'

    def _kaydet(self, instance):
        self.app_ref.save_abone_from_form(
            abone_id=self.selected_id,
            abone_no=self.ent_abone_no.text.strip(),
            ad=self.ent_ad.text.strip(),
            soyad=self.ent_soyad.text.strip(),
            servis=self.ent_servis.text.strip(),
            mahalle=self.ent_mah.text.strip(),
            sokak=self.ent_sokak.text.strip(),
            telefon=self.ent_tel.text.strip(),
            notlar=self.ent_not.text.strip(),
            kayit_tarihi=self.ent_kayit_tar.text.strip()
        )

    def _tup_durumu_guncelle(self, son_siparis_tarihi):
        from datetime import datetime, date
        TUP_OMRU = 45
        if not son_siparis_tarihi or son_siparis_tarihi.strip() == '':
            self.progress_tup.value = 100
            self.lbl_tup.text = 'Yeni Abone - Tüp Dolu'
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
        self.progress_tup.value = yuzde
        if gun_gecen >= TUP_OMRU:
            self.lbl_tup.text = f'Tüp Bitmiştir! ({gun_gecen} gün)'
        elif gun_gecen >= TUP_OMRU * 0.67:
            self.lbl_tup.text = f'Tüp Azalıyor (%{int(yuzde)} - {100 - int(yuzde)}% gitti)'
        else:
            kalan_gun = TUP_OMRU - gun_gecen
            self.lbl_tup.text = f'Tüp Dolu (%{int(yuzde)} - {kalan_gun} gün kaldı)'

    def temizle(self):
        self.selected_id = None
        for widget in [self.ent_abone_no, self.ent_kayit_tar, self.ent_ad, self.ent_soyad,
                       self.ent_sokak, self.ent_tel, self.ent_not]:
            widget.text = ''
        self.ent_servis.text = ''
        self.ent_mah.text = ''
        self.lbl_borc.text = 'Toplam Borç: 0,00 TL'
        self.progress_tup.value = 100
        self.lbl_tup.text = 'Tüp Dolu (%100)'
        self.lbl_emanet.text = 'Emanet: ---'

class AboneListScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app
        self._build_ui()

    def _build_ui(self):
        main = BoxLayout(orientation='vertical', padding=dp(6), spacing=dp(4))
        header = ColoredLabel(text='ABONE LİSTESİ', bg_color=(0.55, 0, 0, 1),
                             color=(1, 0.85, 0, 1), font_size=sp(16), bold=True,
                             size_hint_y=None, height=dp(36))
        main.add_widget(header)

        search_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        self.ent_ara = TextInput(text='', multiline=False, font_size=sp(14),
                                hint_text='Abone No / Ad / Soyad...')
        self.ent_ara.bind(text=self._ara)
        search_box.add_widget(self.ent_ara)
        main.add_widget(search_box)

        self.rv = RecycleView()
        self.data = []
        main.add_widget(self.rv)
        self.add_widget(main)

    def _ara(self, instance, value):
        self.app_ref.abone_ara(value)

    def listele(self, aboneler):
        self.data = []
        for ab in aboneler:
            self.data.append({
                'text': f"{ab['abone_no']} - {ab['ad']} {ab['soyad']} ({ab.get('bakiye', 0):.0f} TL)",
                'abone_id': ab['id']
            })
        self.rv.data = self.data

class BorcEklePopup(Popup):
    def __init__(self, app, abone_id, **kwargs):
        super().__init__(title='Borç Ekle', size_hint=(0.9, 0.7), **kwargs)
        self.app_ref = app
        self.abone_id = abone_id
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        self.cmb_kategori = Spinner(text='Tüpler', values=('Tüpler', 'Sular'), size_hint_y=None, height=dp(40))
        self.cmb_kategori.bind(text=self._kategori_degisti)
        content.add_widget(FormSatir('Kategori:', self.cmb_kategori))
        self.cmb_urun = Spinner(text=TUP_LISTESI[0] if TUP_LISTESI else '', values=TUP_LISTESI,
                                size_hint_y=None, height=dp(40))
        content.add_widget(FormSatir('Ürün:', self.cmb_urun))
        self.ent_adet = TextInput(text='1', multiline=False, font_size=sp(14),
                                  size_hint_y=None, height=dp(36))
        content.add_widget(FormSatir('Adet:', self.ent_adet))
        self.ent_fiyat = TextInput(text='', multiline=False, font_size=sp(14),
                                   size_hint_y=None, height=dp(36))
        content.add_widget(FormSatir('Fiyat:', self.ent_fiyat))
        self.ent_aciklama = TextInput(text='', multiline=False, font_size=sp(14),
                                      size_hint_y=None, height=dp(36))
        content.add_widget(FormSatir('Açıklama:', self.ent_aciklama))
        self.lbl_toplam = Label(text='Toplam: 0,00 TL', font_size=sp(18), bold=True,
                                color=(0.8, 0, 0, 1), size_hint_y=None, height=dp(36))
        content.add_widget(self.lbl_toplam)
        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        btn_box.add_widget(normal_btn('Ekle', self._kaydet))
        btn_box.add_widget(normal_btn('İptal', lambda x: self.dismiss()))
        content.add_widget(btn_box)
        self.content = content
        self._fiyat_yukle()

    def _kategori_degisti(self, instance, value):
        urunler = TUP_LISTESI if value == 'Tüpler' else SU_LISTESI
        self.cmb_urun.values = urunler
        if urunler:
            self.cmb_urun.text = urunler[0]
            self._fiyat_yukle()

    def _fiyat_yukle(self, instance=None):
        fiyatlar = self.app_ref.db.get_fiyatlar()
        fiyat = fiyatlar.get(self.cmb_urun.text, 0)
        self.ent_fiyat.text = f"{fiyat:.2f}" if fiyat > 0 else ''

    def _kaydet(self, instance):
        try:
            urun = self.cmb_urun.text
            adet = int(self.ent_adet.text)
            fiyat = float(self.ent_fiyat.text.replace(',', '.'))
            aciklama = self.ent_aciklama.text
            self.app_ref.borc_service.borc_ekle(self.abone_id, urun, adet, fiyat, aciklama)
            self.app_ref.veri_degisti()
            BilgiPopup('Başarılı', f"{adet*fiyat:,.2f} TL borç eklendi.").open()
            self.dismiss()
        except Exception as e:
            BilgiPopup('Hata', str(e)).open()

class BorcDusPopup(Popup):
    def __init__(self, app, abone_id, **kwargs):
        super().__init__(title='Borç Düş', size_hint=(0.85, 0.5), **kwargs)
        self.app_ref = app
        self.abone_id = abone_id
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        bakiye = app.db.get_abone_bakiye(abone_id)
        self.lbl_bakiye = Label(text=f"Güncel Borç: {bakiye:,.2f} TL",
                                font_size=sp(18), bold=True, color=(0.8, 0, 0, 1),
                                size_hint_y=None, height=dp(40))
        content.add_widget(self.lbl_bakiye)
        self.ent_tutar = TextInput(text='', multiline=False, font_size=sp(16),
                                   size_hint_y=None, height=dp(42))
        content.add_widget(FormSatir('Tutar:', self.ent_tutar))
        self.cmb_odeme = Spinner(text='Nakit', values=ODEME_TIPLERI,
                                 size_hint_y=None, height=dp(40))
        content.add_widget(FormSatir('Ödeme:', self.cmb_odeme))
        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        btn_box.add_widget(normal_btn('Düş', self._kaydet))
        btn_box.add_widget(normal_btn('İptal', lambda x: self.dismiss()))
        content.add_widget(btn_box)
        self.content = content

    def _kaydet(self, instance):
        try:
            tutar = float(self.ent_tutar.text.replace(',', '.'))
            odeme = self.cmb_odeme.text
            self.app_ref.borc_service.borc_dus(self.abone_id, tutar, odeme_turu=odeme)
            self.app_ref.veri_degisti()
            BilgiPopup('Başarılı', f"{tutar:,.2f} TL düşüldü.").open()
            self.dismiss()
        except Exception as e:
            BilgiPopup('Hata', str(e)).open()

class BorcDefteriPopup(Popup):
    def __init__(self, app, abone_id, **kwargs):
        super().__init__(title='Borç Defteri', size_hint=(0.9, 0.7), **kwargs)
        self.app_ref = app
        content = BoxLayout(orientation='vertical', padding=dp(6))
        defter = app.borc_service.borc_defteri(abone_id)
        ozet = Label(
            text=f"Toplam: {defter['toplam_borc']:,.2f} TL  |  Kalan: {defter['guncel_bakiye']:,.2f} TL",
            font_size=sp(13), bold=True, size_hint_y=None, height=dp(36))
        content.add_widget(ozet)
        scroll = ScrollView()
        liste = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        liste.bind(minimum_height=liste.setter('height'))
        for islem in defter['islemler'][:50]:
            renk = (0.8, 0, 0, 1) if islem['islem_turu'] == 'Borç' else (0, 0.4, 0, 1)
            lbl = Label(
                text=f"{islem['tarih'][:10]}  {islem['tutar']:>8,.2f} TL  {islem['islem_turu']}",
                font_size=sp(12), color=renk, size_hint_y=None, height=dp(24), halign='left')
            liste.add_widget(lbl)
        scroll.add_widget(liste)
        content.add_widget(scroll)
        btn = normal_btn('Kapat', lambda x: self.dismiss(), width=dp(120))
        btn.size_hint_y = None
        btn.height = dp(44)
        content.add_widget(btn)
        self.content = content

class EmanetPopup(Popup):
    def __init__(self, app, abone_id, **kwargs):
        super().__init__(title='Emanet İşlemi', size_hint=(0.9, 0.6), **kwargs)
        self.app_ref = app
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        self.cmb_tur = Spinner(text=EMANET_TIPLERI[0], values=EMANET_TIPLERI,
                               size_hint_y=None, height=dp(40))
        content.add_widget(FormSatir('Ürün:', self.cmb_tur))
        self.ent_adet = TextInput(text='1', multiline=False, font_size=sp(14),
                                  size_hint_y=None, height=dp(36))
        content.add_widget(FormSatir('Adet:', self.ent_adet))
        self.cmb_islem = Spinner(text='Verildi', values=('Verildi', 'Alındı'),
                                 size_hint_y=None, height=dp(40))
        content.add_widget(FormSatir('İşlem:', self.cmb_islem))
        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        btn_box.add_widget(normal_btn('Kaydet', self._kaydet))
        btn_box.add_widget(normal_btn('İptal', lambda x: self.dismiss()))
        content.add_widget(btn_box)
        self.content = content

    def _kaydet(self, instance):
        try:
            tur = self.cmb_tur.text
            adet = int(self.ent_adet.text)
            islem = self.cmb_islem.text
            if islem == 'Verildi':
                self.app_ref.emanet_service.emanet_ver(self.abone_id, tur, adet)
            else:
                self.app_ref.emanet_service.emanet_al(self.abone_id, tur, adet)
            self.app_ref.veri_degisti()
            BilgiPopup('Başarılı', f"Emanet {islem}: {adet} {tur}").open()
            self.dismiss()
        except Exception as e:
            BilgiPopup('Hata', str(e)).open()

class PesinSatisPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(title='Peşin Satış', size_hint=(0.9, 0.7), **kwargs)
        self.app_ref = app
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        self.ent_musteri = TextInput(text='Yürüyen Müşteri', multiline=False,
                                     font_size=sp(14), size_hint_y=None, height=dp(36))
        content.add_widget(FormSatir('Müşteri:', self.ent_musteri))
        self.cmb_kategori = Spinner(text='Tüpler', values=('Tüpler', 'Sular'),
                                     size_hint_y=None, height=dp(40))
        self.cmb_kategori.bind(text=self._kategori_degisti)
        content.add_widget(FormSatir('Kategori:', self.cmb_kategori))
        self.cmb_urun = Spinner(text=TUP_LISTESI[0], values=TUP_LISTESI,
                                size_hint_y=None, height=dp(40))
        content.add_widget(FormSatir('Ürün:', self.cmb_urun))
        self.ent_adet = TextInput(text='1', multiline=False, font_size=sp(14),
                                  size_hint_y=None, height=dp(36))
        content.add_widget(FormSatir('Adet:', self.ent_adet))
        self.ent_fiyat = TextInput(text='', multiline=False, font_size=sp(14),
                                   size_hint_y=None, height=dp(36))
        content.add_widget(FormSatir('Fiyat:', self.ent_fiyat))
        self.cmb_odeme = Spinner(text='Nakit', values=ODEME_TIPLERI,
                                 size_hint_y=None, height=dp(40))
        content.add_widget(FormSatir('Ödeme:', self.cmb_odeme))
        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        btn_box.add_widget(normal_btn('Satış Yap', self._kaydet))
        btn_box.add_widget(normal_btn('İptal', lambda x: self.dismiss()))
        content.add_widget(btn_box)
        self.content = content
        self._fiyat_yukle()

    def _kategori_degisti(self, instance, value):
        urunler = TUP_LISTESI if value == 'Tüpler' else SU_LISTESI
        self.cmb_urun.values = urunler
        if urunler:
            self.cmb_urun.text = urunler[0]
            self._fiyat_yukle()

    def _fiyat_yukle(self):
        fiyatlar = self.app_ref.db.get_fiyatlar()
        fiyat = fiyatlar.get(self.cmb_urun.text, 0)
        self.ent_fiyat.text = f"{fiyat:.2f}" if fiyat > 0 else ''

    def _kaydet(self, instance):
        try:
            musteri = self.ent_musteri.text
            urun = self.cmb_urun.text
            adet = int(self.ent_adet.text)
            fiyat = float(self.ent_fiyat.text.replace(',', '.'))
            odeme = self.cmb_odeme.text
            self.app_ref.pesin_satis_service.pesin_satis_yap(
                '', musteri, urun, adet, fiyat, odeme)
            self.app_ref.veri_degisti()
            BilgiPopup('Başarılı', f"Peşin satış: {musteri} - {adet*fiyat:,.2f} TL").open()
            self.dismiss()
        except Exception as e:
            BilgiPopup('Hata', str(e)).open()

class DepoPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(title='Depo Stoğu', size_hint=(0.9, 0.6), **kwargs)
        self.app_ref = app
        content = BoxLayout(orientation='vertical', padding=dp(6))
        scroll = ScrollView()
        liste = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        liste.bind(minimum_height=liste.setter('height'))
        durum = app.db.get_depo_durumu()
        for u in durum:
            lbl = Label(
                text=f"{u['urun_adi']}: {u['dolu_adet']} dolu / {u['bos_adet']} boş",
                font_size=sp(13), size_hint_y=None, height=dp(28), halign='left')
            liste.add_widget(lbl)
        scroll.add_widget(liste)
        content.add_widget(scroll)
        btn = normal_btn('Kapat', lambda x: self.dismiss(), width=dp(120))
        btn.size_hint_y = None
        btn.height = dp(44)
        content.add_widget(btn)
        self.content = content

class FiyatPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(title='Fiyat Listesi', size_hint=(0.9, 0.7), **kwargs)
        self.app_ref = app
        self.fiyatlar = app.db.get_fiyatlar()
        self.entries = {}
        content = BoxLayout(orientation='vertical', padding=dp(6))
        scroll = ScrollView()
        form = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        form.bind(minimum_height=form.setter('height'))
        for urun in URUN_LISTESI:
            f = self.fiyatlar.get(urun, 0)
            satir = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(4))
            satir.add_widget(Label(text=urun, font_size=sp(12), size_hint_x=0.5, halign='left'))
            ent = TextInput(text=f"{f:.2f}", multiline=False, font_size=sp(13),
                           size_hint_x=0.3, height=dp(32))
            satir.add_widget(ent)
            self.entries[urun] = ent
            form.add_widget(satir)
        scroll.add_widget(form)
        content.add_widget(scroll)
        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        btn_box.add_widget(normal_btn('Kaydet', self._kaydet))
        btn_box.add_widget(normal_btn('Kapat', lambda x: self.dismiss()))
        content.add_widget(btn_box)
        self.content = content

    def _kaydet(self, instance):
        try:
            yeni = {}
            for urun, ent in self.entries.items():
                f = float(ent.text.replace(',', '.'))
                if f < 0:
                    raise ValueError(f"{urun}: Negatif fiyat!")
                yeni[urun] = f
            self.app_ref.fiyat_service.update_all(yeni)
            BilgiPopup('Başarılı', 'Fiyatlar güncellendi.').open()
            self.dismiss()
        except Exception as e:
            BilgiPopup('Hata', str(e)).open()

class RaporPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(title='Rapor', size_hint=(0.9, 0.7), **kwargs)
        self.app_ref = app
        content = BoxLayout(orientation='vertical', padding=dp(6))
        btn_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        btn_box.add_widget(normal_btn('Günlük', lambda x: self._rapor_goster('gunluk')))
        btn_box.add_widget(normal_btn('Aylık', lambda x: self._rapor_goster('aylik')))
        btn_box.add_widget(normal_btn('Yıllık', lambda x: self._rapor_goster('yillik')))
        content.add_widget(btn_box)
        self.lbl_rapor = Label(text='', font_size=sp(11), halign='left', valign='top')
        self.lbl_rapor.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
        scroll = ScrollView()
        scroll.add_widget(self.lbl_rapor)
        content.add_widget(scroll)
        btn = normal_btn('Kapat', lambda x: self.dismiss(), width=dp(120))
        btn.size_hint_y = None
        btn.height = dp(44)
        content.add_widget(btn)
        self.content = content

    def _rapor_goster(self, tur):
        try:
            from datetime import datetime
            now = datetime.now()
            if tur == 'gunluk':
                r = self.app_ref.rapor_service.gunluk_rapor()
                txt = f"GÜNLÜK RAPOR - {r['tarih']}\n"
                txt += f"Tüp: {r['tup_satislari']['toplam']:,.2f} TL\n"
                txt += f"İndirimli: {r['indirimli_satislari']['toplam']:,.2f} TL\n"
                txt += f"Su: {r['su_satislari']['toplam']:,.2f} TL\n"
                txt += f"Peşin: {r['pesin_satislari']['toplam']:,.2f} TL\n"
                txt += f"Brüt: {r['brut_gelir']:,.2f} TL\n"
                txt += f"Tahsilat: {r['toplam_tahsilat']:,.2f} TL\n"
                txt += f"Gider: {r['toplam_gider']:,.2f} TL\n"
                txt += f"Net: {r['net_kar']:,.2f} TL\n"
            elif tur == 'aylik':
                r = self.app_ref.rapor_service.aylik_rapor(now.year, now.month)
                txt = f"AYLIK RAPOR - {r['donem']}\n"
                txt += f"Tüp: {r['tup_satis']:,.2f} TL\n"
                txt += f"İndirimli: {r['indirimli_satis']:,.2f} TL\n"
                txt += f"Su: {r['su_satis']:,.2f} TL\n"
                txt += f"Peşin: {r['pesin_satis']:,.2f} TL\n"
                txt += f"Brüt: {r['brut_gelir']:,.2f} TL\n"
                txt += f"Net: {r['net_kar']:,.2f} TL\n"
            else:
                r = self.app_ref.rapor_service.yillik_rapor(now.year)
                txt = f"YILLIK RAPOR - {r['donem']}\n"
                txt += f"Tüp: {r['tup_satis']:,.2f} TL\n"
                txt += f"Net: {r['net_kar']:,.2f} TL\n"
                if 'en_karli_ay' in r:
                    txt += f"En Karlı Ay: {r['en_karli_ay']}\n"
            self.lbl_rapor.text = txt
        except Exception as e:
            self.lbl_rapor.text = f"Hata: {e}"

class TupcularKraliKivyApp(App):
    def build(self):
        self.title = APP_TITLE
        init_db(DB_PATH)
        self.db = Database()
        self.event_bus = EventBus()
        self.abone_service = AboneService(self.db, self.event_bus)
        self.borc_service = BorcService(self.db, self.event_bus)
        self.depo_service = DepoService(self.db, self.event_bus)
        self.emanet_service = EmanetService(self.db, self.event_bus)
        self.fiyat_service = FiyatService(self.db, self.event_bus)
        self.rapor_service = RaporService(self.db)
        self.gider_service = GiderService(self.db, self.event_bus)
        self.yedek_service = YedekService(self.db, self.event_bus)
        self.pesin_satis_service = PesinSatisService(self.db, self.event_bus)

        sm = ScreenManager()
        self.ana_screen = Screen(name='ana')

        main = BoxLayout(orientation='vertical')
        header = ColoredLabel(text=APP_TITLE, bg_color=(0.55, 0, 0, 1),
                             color=(1, 0.85, 0, 1), font_size=sp(18), bold=True,
                             size_hint_y=None, height=dp(40))
        main.add_widget(header)

        tb = TabbedPanel(do_default_tab=False, tab_width=dp(200))
        th1 = TabbedPanelHeader(text='Abone Kartı')
        self.abone_kart = AboneKartScreen(self)
        th1.content = self.abone_kart
        tb.add_widget(th1)

        th2 = TabbedPanelHeader(text='Abone Listesi')
        self.abone_list = AboneListScreen(self)
        th2.content = self.abone_list
        tb.add_widget(th2)

        tb.default_tab = th2
        main.add_widget(tb)

        footer = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(3), padding=dp(3))
        footer.add_widget(normal_btn('LİSTE', lambda x: [setattr(tb, 'default_tab', th2), tb.switch_to(th2)]))
        footer.add_widget(normal_btn('YENİ', self._yeni_abone))
        footer.add_widget(normal_btn('DEPO', lambda x: DepoPopup(self).open()))
        footer.add_widget(normal_btn('FİYAT', lambda x: FiyatPopup(self).open()))
        footer.add_widget(normal_btn('RAPOR', lambda x: RaporPopup(self).open()))
        main.add_widget(footer)

        self.ana_screen.add_widget(main)
        sm.add_widget(self.ana_screen)

        self.abone_listesi = []
        Clock.schedule_once(lambda dt: self._ilk_yukle(), 0.5)

        return sm

    def _ilk_yukle(self):
        self.abone_ara('')

    def abone_ara(self, query):
        aboneler = self.db.get_all_aboneler(query if query else None)
        self.abone_listesi = aboneler
        if hasattr(self, 'abone_list'):
            self.abone_list.listele(aboneler)

    def veri_degisti(self):
        self.abone_ara('')

    def _yeni_abone(self, instance):
        self.abone_kart.temizle()
        sm = self.root
        sm.get_screen('ana').children[0].children[1].default_tab = \
            sm.get_screen('ana').children[0].children[1].tab_list[0]
        sm.get_screen('ana').children[0].children[1].switch_to(
            sm.get_screen('ana').children[0].children[1].tab_list[0])

    def save_abone_from_form(self, abone_id, abone_no, ad, soyad='',
                              servis='', mahalle='', sokak='',
                              telefon='', notlar='', kayit_tarihi=''):
        if not abone_no:
            BilgiPopup('Uyarı', 'Abone No boş bırakılamaz!').open()
            return
        if not ad or len(ad) < 2:
            BilgiPopup('Uyarı', 'Ad en az 2 karakter olmalıdır!').open()
            return
        try:
            data = {
                'abone_no': abone_no, 'ad': ad, 'soyad': soyad,
                'servis_elemani': servis, 'abone_tipi': 'Ev Abonesi',
                'kayit_tarihi': kayit_tarihi or datetime.now().strftime("%d.%m.%Y"),
                'ek_adres': '', 'mahalle': mahalle, 'sokak': sokak,
                'bina_no': '', 'kat': '', 'daire': '', 'notlar': notlar,
                'tels': {'Cep-1': telefon} if telefon else {}
            }
            if abone_id:
                self.abone_service.abone_guncelle(abone_id, data)
                BilgiPopup('Başarılı', 'Abone güncellendi.').open()
            else:
                if self.db.abone_no_var_mi(abone_no):
                    BilgiPopup('Uyarı', f'{abone_no} numarası zaten kayıtlı!').open()
                    return
                yeni_id = self.abone_service.yeni_abone(data)
                self.abone_kart.selected_id = yeni_id
                BilgiPopup('Başarılı', 'Yeni abone eklendi.').open()
            self.veri_degisti()
            detay = self.db.get_abone_details(self.abone_kart.selected_id or abone_id)
            if detay:
                self.abone_kart.form_doldur(detay)
        except Exception as e:
            BilgiPopup('Hata', f'Kayıt başarısız:\n{e}').open()

    def open_borc_ekle(self, abone_id):
        if not abone_id:
            BilgiPopup('Uyarı', 'Önce bir abone seçin!').open()
            return
        BorcEklePopup(self, abone_id).open()

    def open_borc_dus(self, abone_id):
        if not abone_id:
            BilgiPopup('Uyarı', 'Önce bir abone seçin!').open()
            return
        BorcDusPopup(self, abone_id).open()

    def open_borc_defteri(self, abone_id):
        if not abone_id:
            BilgiPopup('Uyarı', 'Önce bir abone seçin!').open()
            return
        BorcDefteriPopup(self, abone_id).open()

    def open_emanet(self, abone_id):
        if not abone_id:
            BilgiPopup('Uyarı', 'Önce bir abone seçin!').open()
            return
        EmanetPopup(self, abone_id).open()

    def open_pesin_satis(self):
        PesinSatisPopup(self).open()

if __name__ == '__main__':
    TupcularKraliKivyApp().run()
