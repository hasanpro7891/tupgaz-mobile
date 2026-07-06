from datetime import datetime
from services.errors import ValidasyonError, StokYetersizError
from config import URUN_LISTESI, get_kategori

class PesinSatisService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def pesin_satis_yap(self, tarih, musteri_adi, urun_adi, adet, birim_fiyat, odeme_turu='Nakit', aciklama=''):
        if not urun_adi:
            raise ValidasyonError("Lütfen bir ürün seçin!", 'URUN_SECILMEDI', 'urun')
        if urun_adi not in URUN_LISTESI:
            raise ValidasyonError(f"Geçersiz ürün: {urun_adi}", 'URUN_GECERSIZ', 'urun')
        if adet <= 0:
            raise ValidasyonError("Adet 0'dan büyük olmalıdır!", 'ADET_GECERSIZ', 'adet')
        if birim_fiyat <= 0:
            raise ValidasyonError("Birim fiyat 0'dan büyük olmalıdır!", 'FIYAT_GECERSIZ', 'fiyat')
        if not musteri_adi or not musteri_adi.strip():
            musteri_adi = "Yürüyen Müşteri"
        if not tarih:
            tarih = datetime.now().strftime("%d.%m.%Y")

        stok = self.db.get_depo_urun(urun_adi)
        if stok['dolu_adet'] < adet:
            raise StokYetersizError(urun_adi, stok['dolu_adet'], adet)

        toplam_tutar = adet * birim_fiyat
        satis_id = self.db.add_pesin_satis(
            tarih=tarih,
            musteri_adi=musteri_adi.strip(),
            urun_adi=urun_adi,
            adet=adet,
            birim_fiyat=birim_fiyat,
            toplam_tutar=toplam_tutar,
            odeme_turu=odeme_turu,
            aciklama=aciklama
        )

        kategori = get_kategori(urun_adi)
        self.event_bus.publish('PESIN_SATIS_YAPILDI', {
            'satis_id': satis_id,
            'musteri_adi': musteri_adi.strip(),
            'urun': urun_adi,
            'adet': adet,
            'toplam_tutar': toplam_tutar,
            'kategori': kategori,
            'tarih': tarih
        })
        return satis_id

    def get_satislar(self, tarih=None):
        return self.db.get_pesin_satislar(tarih)

    def get_gunluk_toplam(self, tarih=None):
        if not tarih:
            tarih = datetime.now().strftime("%d.%m.%Y")
        return self.db.get_pesin_satis_toplam(tarih=tarih)
