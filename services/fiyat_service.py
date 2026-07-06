from services.errors import ValidasyonError

class FiyatService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def get_all(self):
        return self.db.get_fiyatlar()

    def update_all(self, fiyatlar):
        errors = []
        for urun, fiyat in fiyatlar.items():
            if fiyat < 0:
                errors.append(f"{urun}: Negatif fiyat girilemez!")
            elif fiyat > 999999:
                errors.append(f"{urun}: Fiyat çok yüksek!")
        if errors:
            raise ValidasyonError("\n".join(errors), 'FIYAT_HATA')
        for urun, fiyat in fiyatlar.items():
            self.db.update_fiyat(urun, fiyat)
        self.event_bus.publish('VERI_DEGISTI', {})

    def get_fiyat(self, urun_adi):
        return self.db.get_fiyat(urun_adi)

    def check_fiyatlar_girildi_mi(self):
        fiyatlar = self.get_all()
        return all(f > 0 for f in fiyatlar.values())

    def get_fiyat_girilmemis_urunler(self):
        return [u for u, f in self.get_all().items() if f == 0]
