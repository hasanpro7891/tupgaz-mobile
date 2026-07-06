from datetime import datetime
from services.errors import ValidasyonError
from config import EMANET_TIPLERI, get_kategori

class EmanetService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def emanet_ver(self, abone_id, tup_tipi, adet, tarih=None, aciklama=''):
        if adet <= 0:
            raise ValidasyonError("Adet 0'dan büyük olmalıdır!", 'ADET_GECERSIZ', 'adet')
        if tup_tipi not in EMANET_TIPLERI:
            raise ValidasyonError(
                f"Geçersiz ürün tipi! Geçerli: {', '.join(EMANET_TIPLERI)}",
                'TUP_TIPI_GECERSIZ', 'tup_tipi')
        if not tarih:
            tarih = datetime.now().strftime("%d.%m.%Y")
        hareket_id = self.db.emanet_ekle_transaction(
            abone_id, tup_tipi, adet, 'Verildi', tarih, aciklama)
        kategori = get_kategori(tup_tipi)
        self.event_bus.publish('EMANET_VERILDI', {
            'hareket_id': hareket_id, 'abone_id': abone_id,
            'tup_tipi': tup_tipi, 'adet': adet, 'tarih': tarih, 'kategori': kategori
        })
        return hareket_id

    def emanet_al(self, abone_id, tup_tipi, adet, tarih=None, aciklama=''):
        if adet <= 0:
            raise ValidasyonError("Adet 0'dan büyük olmalıdır!", 'ADET_GECERSIZ', 'adet')
        if tup_tipi not in EMANET_TIPLERI:
            raise ValidasyonError(f"Geçersiz ürün tipi!", 'TUP_TIPI_GECERSIZ', 'tup_tipi')
        if not tarih:
            tarih = datetime.now().strftime("%d.%m.%Y")
        bakiye = self.db.get_emanet_bakiye(abone_id, tup_tipi)
        if bakiye < adet:
            raise ValidasyonError(
                f"Abonede {bakiye} adet {tup_tipi} emaneti bulunuyor. {adet} adet alınamaz!",
                'EMANET_YETERSIZ', 'adet')
        hareket_id = self.db.emanet_al_transaction(abone_id, tup_tipi, adet, tarih, aciklama)
        if tup_tipi == "İndirimli 12 KG":
            depo_urun = "İndirimli 12 KG Tüp"
        elif "LT" in tup_tipi:
            depo_urun = tup_tipi
        else:
            depo_urun = f"{tup_tipi} Tüp"
        self.db.depo_stok_guncelle(depo_urun, 0, adet)
        self.event_bus.publish('EMANET_ALINDI', {
            'hareket_id': hareket_id, 'abone_id': abone_id,
            'tup_tipi': tup_tipi, 'adet': adet, 'tarih': tarih
        })
        return hareket_id

    def get_emanet_durumu(self, abone_id):
        return self.db.get_emanet_durumu(abone_id)

    def get_emanet_gecmisi(self, abone_id):
        return self.db.get_emanet_hareketleri(abone_id)
