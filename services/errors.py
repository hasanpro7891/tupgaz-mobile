class TupcularKraliError(Exception):
    def __init__(self, mesaj, hata_kodu=None, alan=None):
        super().__init__(mesaj)
        self.hata_kodu = hata_kodu
        self.alan = alan
        self.mesaj = mesaj

class ValidasyonError(TupcularKraliError):
    pass

class VeritabaniError(TupcularKraliError):
    pass

class StokYetersizError(ValidasyonError):
    def __init__(self, urun, mevcut, istenen):
        super().__init__(
            f"Depoda yeterli {urun} stoku yok!\nMevcut: {mevcut} adet\nİstenen: {istenen} adet",
            hata_kodu='STOK_YETERSIZ',
            alan='urun'
        )
        self.urun = urun
        self.mevcut = mevcut
        self.istenen = istenen

class BorcYetersizError(ValidasyonError):
    def __init__(self, bakiye, tutar):
        super().__init__(
            f"Düşülecek tutar ({tutar:.2f} TL), güncel borçtan ({bakiye:.2f} TL) fazla olamaz!",
            hata_kodu='BORC_YETERSIZ',
            alan='tutar'
        )

class AboneSilmeError(ValidasyonError):
    def __init__(self, ad, bakiye):
        super().__init__(
            f"⚠ {ad} abonesinin {bakiye:.2f} TL borcu bulunuyor!\n"
            "Borcu olan aboneler silinemez!\nÖnce borcunu tahsil edin.",
            hata_kodu='ABONE_SILINEMEZ'
        )

class StateError(TupcularKraliError):
    pass
