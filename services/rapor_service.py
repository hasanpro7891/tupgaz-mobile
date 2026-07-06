from datetime import datetime
import calendar

class RaporService:
    def __init__(self, db):
        self.db = db

    def gunluk_rapor(self, tarih=None):
        if not tarih:
            tarih = datetime.now().strftime("%d.%m.%Y")

        tup_detay = self.db.get_kategori_satis(tarih, 'Borç', lambda u: 'Tüp' in u and 'İndirimli' not in u)
        indirimli_detay = self.db.get_kategori_satis(tarih, 'Borç', lambda u: 'İndirimli' in u)
        su_detay = self.db.get_kategori_satis(tarih, 'Borç', lambda u: 'LT' in u)
        pesin_detay = self.db.get_pesin_satis_detay(tarih)

        toplam_tup = sum(s['toplam'] for s in tup_detay)
        toplam_indirimli = sum(s['toplam'] for s in indirimli_detay)
        toplam_su = sum(s['toplam'] for s in su_detay)
        toplam_pesin = sum(s['toplam'] for s in pesin_detay)

        toplam_tahsilat = self.db.get_toplam_tutar(tarih, 'Borç Düşme')
        toplam_gider = self.db.get_toplam_gider(tarih)
        yeni_abone = self.db.get_gunluk_yeni_abone(tarih)
        gider_detay = self.db.get_gider_detay(tarih)

        brut_gelir = toplam_tup + toplam_indirimli + toplam_su + toplam_pesin
        net_kar = toplam_tahsilat + toplam_pesin - toplam_gider
        kar_marji = (net_kar / brut_gelir * 100) if brut_gelir > 0 else 0

        return {
            'tarih': tarih,
            'tup_satislari': {'detay': tup_detay, 'toplam': toplam_tup},
            'indirimli_satislari': {'detay': indirimli_detay, 'toplam': toplam_indirimli},
            'su_satislari': {'detay': su_detay, 'toplam': toplam_su},
            'pesin_satislari': {'detay': pesin_detay, 'toplam': toplam_pesin},
            'brut_gelir': brut_gelir,
            'toplam_tahsilat': toplam_tahsilat,
            'toplam_gider': toplam_gider,
            'net_kar': net_kar,
            'kar_marji': kar_marji,
            'yeni_abone': yeni_abone,
            'gider_detay': gider_detay,
            'kar_durumu': 'kar' if net_kar > 0 else ('zarar' if net_kar < 0 else 'basabas')
        }

    def aylik_rapor(self, yil, ay):
        ilk_gun = f"01.{ay:02d}.{yil}"
        son_gun = f"{calendar.monthrange(yil, ay)[1]:02d}.{ay:02d}.{yil}"
        return self._donem_raporu(ilk_gun, son_gun, f"{ay:02d}.{yil}")

    def yillik_rapor(self, yil):
        ilk_gun = f"01.01.{yil}"
        son_gun = f"31.12.{yil}"
        aylik_detay = [self.aylik_rapor(yil, ay) for ay in range(1, 13)]
        ana_rapor = self._donem_raporu(ilk_gun, son_gun, str(yil))
        ana_rapor['aylik_detay'] = aylik_detay
        ana_rapor['en_karli_ay'] = max(aylik_detay, key=lambda x: x['net_kar'])['donem']
        ana_rapor['en_zararli_ay'] = min(aylik_detay, key=lambda x: x['net_kar'])['donem']
        return ana_rapor

    def _donem_raporu(self, ilk_gun, son_gun, donem_adi):
        tup_toplam = self.db.get_aralik_satis(ilk_gun, son_gun, 'Borç', 'Tüp')
        indirimli_toplam = self.db.get_aralik_satis(ilk_gun, son_gun, 'Borç', 'İndirimli')
        su_toplam = self.db.get_aralik_satis(ilk_gun, son_gun, 'Borç', 'Su')
        pesin_toplam = self.db.get_pesin_satis_toplam(ilk_gun=ilk_gun, son_gun=son_gun)
        toplam_tahsilat = self.db.get_aralik_tutari(ilk_gun, son_gun, 'Borç Düşme')
        toplam_gider = self.db.get_aralik_gider(ilk_gun, son_gun)
        yeni_abone = self.db.get_aralik_yeni_abone(ilk_gun, son_gun)
        brut_gelir = tup_toplam + indirimli_toplam + su_toplam + pesin_toplam
        net_kar = toplam_tahsilat + pesin_toplam - toplam_gider
        return {
            'donem': donem_adi,
            'tup_satis': tup_toplam,
            'indirimli_satis': indirimli_toplam,
            'su_satis': su_toplam,
            'pesin_satis': pesin_toplam,
            'brut_gelir': brut_gelir,
            'toplam_tahsilat': toplam_tahsilat,
            'toplam_gider': toplam_gider,
            'net_kar': net_kar,
            'yeni_abone': yeni_abone
        }
