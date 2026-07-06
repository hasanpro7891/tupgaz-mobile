from datetime import datetime
from services.errors import ValidasyonError, AboneSilmeError
from config import URUN_LISTESI

class AboneService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def yeni_abone(self, data):
        self._validate_yeni_abone(data)
        abone_id = self.db.add_abone(data)
        self.db.init_emanet_bakiyesi(abone_id)
        self.event_bus.publish('ABONE_EKLENDI', {
            'abone_id': abone_id,
            'abone_no': data['abone_no'],
            'ad': f"{data['ad']} {data.get('soyad', '')}"
        })
        return abone_id

    def abone_guncelle(self, abone_id, data):
        self.db.update_abone(abone_id, data)
        self.event_bus.publish('ABONE_GUNCELLENDI', {'abone_id': abone_id})

    def abone_sil(self, abone_id):
        details = self.db.get_abone_details(abone_id)
        if not details:
            raise ValidasyonError("Abone bulunamadı!", 'ABONE_BULUNAMADI')
        if details['bakiye'] > 0:
            ad = f"{details['info'].get('ad', '')} {details['info'].get('soyad', '')}"
            raise AboneSilmeError(ad, details['bakiye'])
        self.db.soft_delete_abone(abone_id)
        self.event_bus.publish('ABONE_SILINDI', {'abone_id': abone_id})
        return True

    def abone_ara(self, query, kriter='tumu'):
        if not query or not query.strip():
            return self.db.get_all_aboneler()
        return self.db.get_all_aboneler(query.strip(), kriter)

    def abone_detay(self, abone_id):
        return self.db.get_abone_details(abone_id)

    def _validate_yeni_abone(self, data):
        abone_no = data.get('abone_no', '').strip()
        if not abone_no:
            raise ValidasyonError("Abone No boş bırakılamaz!", 'ABONE_NO_BOS', 'abone_no')
        if len(abone_no) > 20:
            raise ValidasyonError("Abone No 20 karakterden uzun olamaz!", 'ABONE_NO_UZUN', 'abone_no')
        if self.db.abone_no_var_mi(abone_no):
            raise ValidasyonError(f"{abone_no} numarası zaten kayıtlı!", 'ABONE_NO_DUPLICATE', 'abone_no')
        ad = data.get('ad', '').strip()
        if not ad or len(ad) < 2:
            raise ValidasyonError("Ad en az 2 karakter olmalıdır!", 'AD_GECERSIZ', 'ad')
        if len(ad) > 50:
            raise ValidasyonError("Ad 50 karakterden uzun olamaz!", 'AD_UZUN', 'ad')
        soyad = data.get('soyad', '').strip()
        if len(soyad) > 50:
            raise ValidasyonError("Soyad 50 karakterden uzun olamaz!", 'SOYAD_UZUN', 'soyad')
        abone_tipi = data.get('abone_tipi', '')
        if abone_tipi and abone_tipi not in ['Ev Abonesi', 'İş Yeri', 'Tali Bayii']:
            raise ValidasyonError("Geçersiz abone tipi!", 'TIP_GECERSIZ', 'abone_tipi')
        tels = data.get('tels', {})
        for tip, num in tels.items():
            if num and num.strip():
                digits = ''.join(c for c in num if c.isdigit())
                if len(digits) < 10 or len(digits) > 15:
                    raise ValidasyonError(f"{tip} telefon numarası geçersiz! (10-15 hane)", 'TELEFON_GECERSIZ', f'tel_{tip}')
