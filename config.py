import os
from enum import Enum

APP_NAME = "Tüpçüler Kralı"
APP_VERSION = "v2.0"
APP_TITLE = f"{APP_NAME} {APP_VERSION}"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "tupgaz.db")
YEDEK_KLASORU = os.path.join(BASE_DIR, "data", "yedek")

class UrunKategori(Enum):
    TUP = "Tüp"
    INDIRIMLI_TUP = "İndirimli Tüp"
    SU = "Su"

URUN_LISTESI = [
    "2 KG Tüp",
    "12 KG Tüp",
    "İndirimli 12 KG Tüp",
    "24 KG Tüp",
    "45 KG Tüp",
    "Hayat 19 LT",
    "Berrak 19 LT",
]

TUP_LISTESI = ["2 KG Tüp", "12 KG Tüp", "İndirimli 12 KG Tüp", "24 KG Tüp", "45 KG Tüp"]
SU_LISTESI = ["Hayat 19 LT", "Berrak 19 LT"]
INDIRIMLI_LISTESI = ["İndirimli 12 KG Tüp"]

DEPO_URUNLERI = URUN_LISTESI

EMANET_TIPLERI = [
    "2 KG", "12 KG", "İndirimli 12 KG", "24 KG", "45 KG",
    "Hayat 19 LT", "Berrak 19 LT",
]

EMANET_KOLONLARI = {
    "2 KG": "tup_2kg",
    "12 KG": "tup_12kg",
    "İndirimli 12 KG": "indirimli_12kg",
    "24 KG": "tup_24kg",
    "45 KG": "tup_45kg",
    "Hayat 19 LT": "hayat_19lt",
    "Berrak 19 LT": "berrak_19lt",
}

EMANET_UI_GRUPLARI = [
    ("Tüpler", [
        ("2 KG", "tup_2kg"),
        ("12 KG", "tup_12kg"),
        ("İnd.12KG", "indirimli_12kg"),
        ("24 KG", "tup_24kg"),
        ("45 KG", "tup_45kg"),
    ]),
    ("Sular (19 LT)", [
        ("Hayat", "hayat_19lt"),
        ("Berrak", "berrak_19lt"),
    ]),
]

GIDER_KATEGORILERI = ["Kira", "Elektrik", "Su", "Personel", "Nakliye", "Bakım", "Vergi", "Diğer"]
ODEME_TIPLERI = ["Nakit", "Kart", "Havale/EFT"]

COLOR_HEADER_BG = "#8B0000"
COLOR_HEADER_FG = "#FFD700"
COLOR_FOOTER_BG = "#2F2F2F"
COLOR_KRMIZI = "#CC0000"
COLOR_YESIL = "#006600"
COLOR_MAVI = "#003366"
COLOR_ALTIN = "#FFD700"
COLOR_KREM = "#FFF8DC"
COLOR_WIDGET_BG = "#A52A2A"

FONT_BASLIK = ("Arial", 16, "bold")
FONT_NORMAL = ("Arial", 10)
FONT_BUTON = ("Arial", 9, "bold")
FONT_KUCUK = ("Arial", 8)

def urun_kategori(urun_adi):
    if urun_adi in SU_LISTESI:
        return UrunKategori.SU
    if urun_adi in INDIRIMLI_LISTESI:
        return UrunKategori.INDIRIMLI_TUP
    return UrunKategori.TUP

def urun_adi_to_emanet_tipi(urun_adi):
    return urun_adi.replace(" Tüp", "")

def emanet_tipi_to_kolon(emanet_tipi):
    return EMANET_KOLONLARI.get(emanet_tipi, "")

def depo_urun_to_emanet_tipi(urun_adi):
    if "LT" in urun_adi:
        return urun_adi
    if urun_adi == "İndirimli 12 KG Tüp":
        return "İndirimli 12 KG"
    return urun_adi.replace(" Tüp", "")

def get_kategori(urun_adi):
    if "İndirimli" in urun_adi:
        return "İndirimli Tüp"
    if "LT" in urun_adi:
        return "Su"
    return "Tüp"
