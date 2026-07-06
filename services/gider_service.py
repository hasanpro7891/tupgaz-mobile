from datetime import datetime
from services.errors import ValidasyonError
from config import GIDER_KATEGORILERI

class GiderService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def gider_ekle(self, tarih, tutar, kategori, aciklama=''):
        if tutar <= 0:
            raise ValidasyonError("Gider tutarı 0'dan büyük olmalıdır!", 'GIDER_TUTAR', 'tutar')
        if not kategori or not kategori.strip():
            raise ValidasyonError("Kategori seçilmelidir!", 'KATEGORI_BOS', 'kategori')
        if not tarih:
            tarih = datetime.now().strftime("%d.%m.%Y")
        gider_id = self.db.add_gider(tarih, tutar, kategori.strip(), aciklama)
        self.event_bus.publish('GIDER_EKLENDI', {
            'gider_id': gider_id, 'tutar': tutar, 'kategori': kategori, 'tarih': tarih
        })
        return gider_id
