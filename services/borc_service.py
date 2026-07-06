from datetime import datetime
from services.errors import ValidasyonError, StokYetersizError, BorcYetersizError
from config import get_kategori

class BorcService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def borc_ekle(self, abone_id, urun, adet, birim_fiyat, aciklama=''):
        if adet <= 0:
            raise ValidasyonError("Adet 0'dan büyük olmalıdır!", 'ADET_GECERSIZ', 'adet')
        if birim_fiyat <= 0:
            raise ValidasyonError("Birim fiyat 0'dan büyük olmalıdır!", 'FIYAT_GECERSIZ', 'fiyat')
        if not urun:
            raise ValidasyonError("Lütfen bir ürün seçin!", 'URUN_SECILMEDI', 'urun')

        stok = self.db.get_depo_urun(urun)
        if stok['dolu_adet'] < adet:
            raise StokYetersizError(urun, stok['dolu_adet'], adet)

        toplam = adet * birim_fiyat
        tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
        islem_id = self.db.borc_ekle_transaction(
            abone_id=abone_id, tarih=tarih, tutar=toplam,
            aciklama=aciklama or f"{adet} adet {urun}",
            urun_adi=urun, adet=adet)

        kategori = get_kategori(urun)
        self.event_bus.publish('BORC_EKLENDI', {
            'islem_id': islem_id, 'abone_id': abone_id,
            'tutar': toplam, 'urun': urun, 'adet': adet,
            'kategori': kategori, 'tarih': tarih
        })
        return islem_id

    def borc_dus(self, abone_id, tutar, aciklama='', odeme_turu='Nakit'):
        if tutar <= 0:
            raise ValidasyonError("Tutar 0'dan büyük olmalıdır!", 'TUTAR_GECERSIZ', 'tutar')
        bakiye = self.db.get_abone_bakiye(abone_id)
        if tutar > bakiye:
            raise BorcYetersizError(bakiye, tutar)

        tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
        aciklama_full = f"{aciklama} ({odeme_turu})" if aciklama else odeme_turu
        islem_id = self.db.add_islem(abone_id, tarih, tutar, aciklama_full, 'Borç Düşme')
        self.event_bus.publish('BORC_DUSULDU', {
            'islem_id': islem_id, 'abone_id': abone_id,
            'tutar': tutar, 'tarih': tarih
        })
        return islem_id

    def satis_duzelt(self, islem_id, yeni_tutar, yeni_aciklama):
        eski = self.db.get_islem(islem_id)
        if not eski:
            raise ValidasyonError("İşlem bulunamadı!", 'ISLEM_BULUNAMADI')
        try:
            eski_tarih = datetime.strptime(eski['tarih'], "%d.%m.%Y %H:%M")
        except ValueError:
            eski_tarih = datetime.strptime(eski['tarih'][:10], "%d.%m.%Y")
        if (datetime.now() - eski_tarih).days > 30:
            raise ValidasyonError("30 günden eski işlemler düzeltilemez!", 'ISLEM_COK_ESKI')
        if yeni_tutar <= 0:
            raise ValidasyonError("Yeni tutar 0'dan büyük olmalıdır!", 'TUTAR_GECERSIZ', 'tutar')
        fark = yeni_tutar - eski['tutar']
        self.db.update_islem(islem_id, yeni_tutar, yeni_aciklama)
        self.db.mark_islem_duzeltildi(islem_id, datetime.now().strftime("%d.%m.%Y %H:%M"))
        self.event_bus.publish('SATIS_DUZELTILDI', {
            'islem_id': islem_id, 'abone_id': eski['abone_id'],
            'eski_tutar': eski['tutar'], 'yeni_tutar': yeni_tutar, 'fark': fark
        })
        return {'islem_id': islem_id, 'eski_tutar': eski['tutar'],
                'yeni_tutar': yeni_tutar, 'fark': fark}

    def borc_defteri(self, abone_id):
        islemler = self.db.get_islem_gecmisi(abone_id)
        toplam_borc = sum(i['tutar'] for i in islemler if i['islem_turu'] == 'Borç')
        toplam_odenen = sum(i['tutar'] for i in islemler if i['islem_turu'] == 'Borç Düşme')
        return {
            'islemler': islemler,
            'toplam_borc': toplam_borc,
            'toplam_odenen': toplam_odenen,
            'guncel_bakiye': toplam_borc - toplam_odenen
        }

    def get_toplam_alicak(self):
        return self.db.get_toplam_alicak()
