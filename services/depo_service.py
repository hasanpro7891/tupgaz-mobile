from services.errors import ValidasyonError
from config import DEPO_URUNLERI

class DepoService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def get_durum(self):
        return self.db.get_depo_durumu()

    def get_toplam_dolu(self):
        return self.db.get_depo_toplam_dolu()

    def stok_guncelle(self, urun_adi, dolu, bos):
        if urun_adi not in DEPO_URUNLERI:
            raise ValidasyonError(f"Geçersiz ürün: {urun_adi}", 'URUN_GECERSIZ')
        if dolu < 0 or bos < 0:
            raise ValidasyonError("Stok adedi negatif olamaz!", 'STOK_NEGATIF')
        self.db.update_stok(urun_adi, dolu, bos)
        self.event_bus.publish('VERI_DEGISTI', {})

    def stok_sifirla(self):
        for urun in DEPO_URUNLERI:
            self.db.update_stok(urun, 0, 0)
        self.event_bus.publish('VERI_DEGISTI', {})
