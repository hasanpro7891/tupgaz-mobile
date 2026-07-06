import shutil
import os
from datetime import datetime
from config import BASE_DIR, YEDEK_KLASORU

class YedekService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def yedek_al(self, hedef_klasor=None):
        if not hedef_klasor:
            hedef_klasor = YEDEK_KLASORU
        os.makedirs(hedef_klasor, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        yedek_adi = f"tupgaz_{timestamp}.db"
        yedek_yolu = os.path.join(hedef_klasor, yedek_adi)
        try:
            shutil.copy2(self.db.db_path, yedek_yolu)
            boyut = os.path.getsize(yedek_yolu)
            self.db.add_yedek_log(yedek_adi, boyut, 'Başarılı')
            self.event_bus.publish('YEDEK_ALINDI', {
                'dosya_adi': yedek_adi,
                'dosya_boyutu': boyut,
                'tarih': datetime.now().strftime("%d.%m.%Y %H:%M")
            })
            return yedek_yolu
        except Exception as e:
            self.db.add_yedek_log(yedek_adi, 0, 'Başarısız', str(e))
            raise ValueError(f"Yedekleme başarısız: {e}")

    def get_gecmis(self, limit=10):
        return self.db.get_yedek_gecmisi(limit)

    def otomatik_yedek_kontrol(self):
        son_yedek = self.db.get_ayar('son_yedek_tarihi')
        if son_yedek:
            try:
                son_tarih = datetime.strptime(son_yedek, "%d.%m.%Y")
                if (datetime.now() - son_tarih).days < 1:
                    return
            except Exception:
                pass
        try:
            self.yedek_al()
            self.db.set_ayar('son_yedek_tarihi', datetime.now().strftime("%d.%m.%Y"))
        except Exception:
            pass
