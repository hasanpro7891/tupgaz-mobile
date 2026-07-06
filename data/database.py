import sqlite3
import datetime
import os
from contextlib import contextmanager
from config import DB_PATH, emanet_tipi_to_kolon

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @contextmanager
    def transaction(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ==================== ABONE METODLARI ====================

    def add_abone(self, data):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO aboneler (abone_no, kayit_tarihi, ad, soyad, servis_elemani,
                    abone_tipi, ek_adres, mahalle, sokak, bina_no, kat, daire, notlar)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['abone_no'], data.get('kayit_tarihi', datetime.datetime.now().strftime("%d.%m.%Y")),
                data['ad'], data.get('soyad', ''), data.get('servis_elemani', ''),
                data.get('abone_tipi', 'Ev Abonesi'), data.get('ek_adres', ''),
                data.get('mahalle', ''), data.get('sokak', ''), data.get('bina_no', ''),
                data.get('kat', ''), data.get('daire', ''), data.get('notlar', '')
            ))
            abone_id = cursor.lastrowid
            tels = data.get('tels', {})
            for tel_tipi, numara in tels.items():
                if numara and numara.strip():
                    cursor.execute("INSERT INTO telefonlar (abone_id, tel_tipi, numara) VALUES (?, ?, ?)",
                                   (abone_id, tel_tipi, numara.strip()))
            conn.commit()
            return abone_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def update_abone(self, abone_id, data):
        with self.transaction() as cursor:
            cursor.execute("""
                UPDATE aboneler SET ad=?, soyad=?, servis_elemani=?, abone_tipi=?,
                    ek_adres=?, mahalle=?, sokak=?, bina_no=?, kat=?, daire=?, notlar=?,
                    guncelleme_tarihi=datetime('now','localtime')
                WHERE id=?
            """, (data['ad'], data.get('soyad', ''), data.get('servis_elemani', ''),
                  data.get('abone_tipi', 'Ev Abonesi'), data.get('ek_adres', ''),
                  data.get('mahalle', ''), data.get('sokak', ''), data.get('bina_no', ''),
                  data.get('kat', ''), data.get('daire', ''), data.get('notlar', ''),
                  abone_id))
            cursor.execute("DELETE FROM telefonlar WHERE abone_id=?", (abone_id,))
            tels = data.get('tels', {})
            for tel_tipi, numara in tels.items():
                if numara and numara.strip():
                    cursor.execute("INSERT INTO telefonlar (abone_id, tel_tipi, numara) VALUES (?, ?, ?)",
                                   (abone_id, tel_tipi, numara.strip()))

    def soft_delete_abone(self, abone_id):
        with self.transaction() as cursor:
            cursor.execute("UPDATE aboneler SET silindi=1, silinme_tarihi=datetime('now','localtime') WHERE id=?", (abone_id,))

    def abone_no_var_mi(self, abone_no):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM aboneler WHERE abone_no=? AND silindi=0", (abone_no,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def get_all_aboneler(self, search_query=None, kriter='tumu'):
        conn = self._get_conn()
        cursor = conn.cursor()
        if search_query:
            q = f'%{search_query}%'
            if kriter == 'tumu':
                cursor.execute("""
                    SELECT a.id, a.abone_no, a.ad, a.soyad,
                        COALESCE((SELECT SUM(CASE WHEN b.islem_turu='Borç' THEN b.tutar ELSE 0 END) -
                            SUM(CASE WHEN b.islem_turu='Borç Düşme' THEN b.tutar ELSE 0 END)
                            FROM borclar b WHERE b.abone_id=a.id), 0) as bakiye
                    FROM aboneler a WHERE a.silindi=0 AND a.aktif=1
                    AND (a.abone_no LIKE ? OR a.ad LIKE ? OR a.soyad LIKE ?)
                    ORDER BY a.ad""", (q, q, q))
            elif kriter == 'abone_no':
                cursor.execute("""
                    SELECT a.id, a.abone_no, a.ad, a.soyad, COALESCE(
                        (SELECT SUM(CASE WHEN b.islem_turu='Borç' THEN b.tutar ELSE 0 END) -
                            SUM(CASE WHEN b.islem_turu='Borç Düşme' THEN b.tutar ELSE 0 END)
                            FROM borclar b WHERE b.abone_id=a.id), 0) as bakiye
                    FROM aboneler a WHERE a.silindi=0 AND a.aktif=1 AND a.abone_no LIKE ?
                    ORDER BY a.abone_no""", (q,))
            elif kriter == 'ad':
                cursor.execute("""
                    SELECT a.id, a.abone_no, a.ad, a.soyad, COALESCE(
                        (SELECT SUM(CASE WHEN b.islem_turu='Borç' THEN b.tutar ELSE 0 END) -
                            SUM(CASE WHEN b.islem_turu='Borç Düşme' THEN b.tutar ELSE 0 END)
                            FROM borclar b WHERE b.abone_id=a.id), 0) as bakiye
                    FROM aboneler a WHERE a.silindi=0 AND a.aktif=1 AND a.ad LIKE ?
                    ORDER BY a.ad""", (q,))
            elif kriter == 'soyad':
                cursor.execute("""
                    SELECT a.id, a.abone_no, a.ad, a.soyad, COALESCE(
                        (SELECT SUM(CASE WHEN b.islem_turu='Borç' THEN b.tutar ELSE 0 END) -
                            SUM(CASE WHEN b.islem_turu='Borç Düşme' THEN b.tutar ELSE 0 END)
                            FROM borclar b WHERE b.abone_id=a.id), 0) as bakiye
                    FROM aboneler a WHERE a.silindi=0 AND a.aktif=1 AND a.soyad LIKE ?
                    ORDER BY a.soyad""", (q,))
        else:
            cursor.execute("""
                SELECT a.id, a.abone_no, a.ad, a.soyad,
                    COALESCE((SELECT SUM(CASE WHEN b.islem_turu='Borç' THEN b.tutar ELSE 0 END) -
                        SUM(CASE WHEN b.islem_turu='Borç Düşme' THEN b.tutar ELSE 0 END)
                        FROM borclar b WHERE b.abone_id=a.id), 0) as bakiye
                FROM aboneler a WHERE a.silindi=0 AND a.aktif=1
                ORDER BY a.ad""")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows] if rows else []

    def get_abone_details(self, abone_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM aboneler WHERE id=?", (abone_id,))
        info = cursor.fetchone()
        if not info:
            conn.close()
            return None
        info = dict(info)
        cursor.execute("SELECT tel_tipi, numara FROM telefonlar WHERE abone_id=?", (abone_id,))
        tels = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM emanet_bakiyesi WHERE abone_id=?", (abone_id,))
        emanet = cursor.fetchone()
        emanet_dict = dict(emanet) if emanet else {}
        cursor.execute("SELECT COALESCE(SUM(tutar), 0) FROM borclar WHERE abone_id=? AND islem_turu='Borç'", (abone_id,))
        toplam_borc = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(tutar), 0) FROM borclar WHERE abone_id=? AND islem_turu='Borç Düşme'", (abone_id,))
        toplam_tahsilat = cursor.fetchone()[0]
        conn.close()
        return {
            'info': info,
            'tels': tels,
            'emanet': emanet_dict,
            'bakiye': toplam_borc - toplam_tahsilat
        }

    def get_abone_bakiye(self, abone_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(CASE WHEN islem_turu='Borç' THEN tutar ELSE 0 END), 0) - "
                       "COALESCE(SUM(CASE WHEN islem_turu='Borç Düşme' THEN tutar ELSE 0 END), 0) "
                       "FROM borclar WHERE abone_id=?", (abone_id,))
        bakiye = cursor.fetchone()[0]
        conn.close()
        return bakiye

    def init_emanet_bakiyesi(self, abone_id):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT OR IGNORE INTO emanet_bakiyesi
                    (abone_id, tup_2kg, tup_12kg, indirimli_12kg, tup_24kg, tup_45kg, hayat_19lt, berrak_19lt)
                VALUES (?, 0, 0, 0, 0, 0, 0, 0)
            """, (abone_id,))

    def get_toplam_abone_sayisi(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM aboneler WHERE silindi=0 AND aktif=1")
        sayi = cursor.fetchone()[0]
        conn.close()
        return sayi

    def get_toplam_alicak(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(CASE WHEN b.islem_turu='Borç' THEN b.tutar ELSE 0 END), 0) -
                   COALESCE(SUM(CASE WHEN b.islem_turu='Borç Düşme' THEN b.tutar ELSE 0 END), 0)
            FROM borclar b JOIN aboneler a ON b.abone_id=a.id
            WHERE a.silindi=0 AND a.aktif=1
        """)
        toplam = cursor.fetchone()[0]
        conn.close()
        return toplam

    # ==================== BORÇ METODLARI ====================

    def borc_ekle_transaction(self, abone_id, tarih, tutar, aciklama, urun_adi, adet):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO borclar (abone_id, tarih, tutar, aciklama, islem_turu, urun_adi, adet)
                VALUES (?, ?, ?, ?, 'Borç', ?, ?)
            """, (abone_id, tarih, tutar, aciklama, urun_adi, adet))
            cursor.execute("UPDATE aboneler SET son_siparis_tarihi=? WHERE id=?",
                           (tarih[:10] if tarih else datetime.datetime.now().strftime("%d.%m.%Y"), abone_id))
            depo_urun = urun_adi
            cursor.execute("UPDATE depo SET dolu_adet = MAX(dolu_adet - ?, 0), guncelleme_tarihi=datetime('now','localtime') WHERE urun_adi=?",
                           (adet, depo_urun))
            return cursor.lastrowid

    def add_islem(self, abone_id, tarih, tutar, aciklama, islem_turu):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO borclar (abone_id, tarih, tutar, aciklama, islem_turu)
                VALUES (?, ?, ?, ?, ?)
            """, (abone_id, tarih, tutar, aciklama, islem_turu))
            return cursor.lastrowid

    def get_islem(self, islem_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM borclar WHERE id=?", (islem_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_islem(self, islem_id, yeni_tutar, yeni_aciklama):
        with self.transaction() as cursor:
            cursor.execute("UPDATE borclar SET tutar=?, aciklama=? WHERE id=?",
                           (yeni_tutar, yeni_aciklama, islem_id))

    def mark_islem_duzeltildi(self, islem_id, tarih):
        with self.transaction() as cursor:
            cursor.execute("UPDATE borclar SET duzeltildi=1, duzeltme_tarihi=? WHERE id=?",
                           (tarih, islem_id))

    def get_islem_gecmisi(self, abone_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tarih, tutar, islem_turu, aciklama, urun_adi, adet, duzeltildi
            FROM borclar WHERE abone_id=? ORDER BY id DESC
        """, (abone_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ==================== EMANET METODLARI ====================

    def get_emanet_durumu(self, abone_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tup_2kg, tup_12kg, indirimli_12kg, tup_24kg, tup_45kg, hayat_19lt, berrak_19lt
            FROM emanet_bakiyesi WHERE abone_id=?
        """, (abone_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                '2 KG': row[0], '12 KG': row[1], 'İndirimli 12 KG': row[2],
                '24 KG': row[3], '45 KG': row[4],
                'Hayat 19 LT': row[5], 'Berrak 19 LT': row[6]
            }
        return {}

    def get_emanet_bakiye(self, abone_id, tup_tipi):
        kolon = emanet_tipi_to_kolon(tup_tipi)
        if not kolon:
            return 0
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {kolon} FROM emanet_bakiyesi WHERE abone_id=?", (abone_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def emanet_ekle_transaction(self, abone_id, tup_tipi, adet, islem_turu, tarih, aciklama):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO emanet_hareketleri (abone_id, tup_tipi, adet, islem_turu, tarih, aciklama)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (abone_id, tup_tipi, adet, islem_turu, tarih, aciklama))
            return cursor.lastrowid

    def emanet_al_transaction(self, abone_id, tup_tipi, adet, tarih, aciklama):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO emanet_hareketleri (abone_id, tup_tipi, adet, islem_turu, tarih, aciklama)
                VALUES (?, ?, ?, 'Alındı', ?, ?)
            """, (abone_id, tup_tipi, adet, tarih, aciklama))
            return cursor.lastrowid

    def get_emanet_hareketleri(self, abone_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tup_tipi, adet, islem_turu, tarih, aciklama
            FROM emanet_hareketleri WHERE abone_id=? ORDER BY id DESC
        """, (abone_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ==================== DEPO METODLARI ====================

    def get_depo_durumu(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT urun_adi, dolu_adet, bos_adet FROM depo ORDER BY urun_adi")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_depo_urun(self, urun_adi):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT dolu_adet, bos_adet FROM depo WHERE urun_adi=?", (urun_adi,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {'dolu_adet': 0, 'bos_adet': 0}

    def get_depo_toplam_dolu(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(dolu_adet), 0) FROM depo")
        sayi = cursor.fetchone()[0]
        conn.close()
        return sayi

    def update_stok(self, urun_adi, dolu, bos):
        with self.transaction() as cursor:
            cursor.execute("""
                UPDATE depo SET dolu_adet=?, bos_adet=?, guncelleme_tarihi=datetime('now','localtime')
                WHERE urun_adi=?
            """, (dolu, bos, urun_adi))

    def depo_stok_guncelle(self, urun_adi, dolu_delta, bos_delta):
        with self.transaction() as cursor:
            cursor.execute("""
                UPDATE depo SET dolu_adet = MAX(dolu_adet + ?, 0),
                    bos_adet = MAX(bos_adet + ?, 0),
                    guncelleme_tarihi=datetime('now','localtime')
                WHERE urun_adi=?
            """, (dolu_delta, bos_delta, urun_adi))

    # ==================== FİYAT METODLARI ====================

    def get_fiyatlar(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT urun_adi, fiyat FROM fiyatlar")
        return dict(cursor.fetchall())

    def get_fiyat(self, urun_adi):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT fiyat FROM fiyatlar WHERE urun_adi=?", (urun_adi,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0.0

    def get_fiyat_guncelleme_tarihi(self, urun_adi):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT guncelleme_tarihi FROM fiyatlar WHERE urun_adi=?", (urun_adi,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ''

    def update_fiyat(self, urun, yeni_fiyat):
        with self.transaction() as cursor:
            cursor.execute("""
                UPDATE fiyatlar SET fiyat=?, guncelleme_tarihi=? WHERE urun_adi=?
            """, (yeni_fiyat, datetime.datetime.now().strftime("%d.%m.%Y"), urun))

    # ==================== GİDER METODLARI ====================

    def add_gider(self, tarih, tutar, kategori, aciklama):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO giderler (tarih, tutar, kategori, aciklama)
                VALUES (?, ?, ?, ?)
            """, (tarih, tutar, kategori, aciklama))
            return cursor.lastrowid

    def get_gider_detay(self, tarih):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT kategori, COALESCE(SUM(tutar), 0) as toplam
            FROM giderler WHERE tarih=? GROUP BY kategori ORDER BY kategori
        """, (tarih,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_toplam_gider(self, tarih):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(tutar), 0) FROM giderler WHERE tarih=?", (tarih,))
        toplam = cursor.fetchone()[0]
        conn.close()
        return toplam

    # ==================== RAPOR METODLARI ====================

    def get_toplam_tutar(self, tarih, islem_turu):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) FROM borclar
            WHERE substr(tarih,1,10)=? AND islem_turu=?
        """, (tarih, islem_turu))
        toplam = cursor.fetchone()[0]
        conn.close()
        return toplam

    def get_gunluk_yeni_abone(self, tarih):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM aboneler WHERE kayit_tarihi=? AND silindi=0", (tarih,))
        sayi = cursor.fetchone()[0]
        conn.close()
        return sayi

    def get_aralik_tutari(self, ilk_gun, son_gun, islem_turu):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) FROM borclar
            WHERE substr(tarih,1,10)>=? AND substr(tarih,1,10)<=? AND islem_turu=?
        """, (ilk_gun, son_gun, islem_turu))
        toplam = cursor.fetchone()[0]
        conn.close()
        return toplam

    def get_aralik_gider(self, ilk_gun, son_gun):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) FROM giderler
            WHERE tarih>=? AND tarih<=?
        """, (ilk_gun, son_gun))
        toplam = cursor.fetchone()[0]
        conn.close()
        return toplam

    def get_aralik_yeni_abone(self, ilk_gun, son_gun):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM aboneler
            WHERE kayit_tarihi>=? AND kayit_tarihi<=? AND silindi=0
        """, (ilk_gun, son_gun))
        sayi = cursor.fetchone()[0]
        conn.close()
        return sayi

    def get_kategori_satis(self, tarih, islem_turu, kategori_filter):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT urun_adi, COALESCE(SUM(tutar), 0) as toplam, COALESCE(SUM(adet), 0) as adet
            FROM borclar WHERE substr(tarih,1,10)=? AND islem_turu=?
            GROUP BY urun_adi HAVING urun_adi != ''
        """, (tarih, islem_turu))
        rows = cursor.fetchall()
        conn.close()
        result = []
        for r in rows:
            if kategori_filter(r['urun_adi']):
                result.append({'urun': r['urun_adi'], 'toplam': r['toplam'], 'adet': r['adet']})
        return result

    def get_aralik_satis(self, ilk_gun, son_gun, islem_turu, kategori):
        conn = self._get_conn()
        cursor = conn.cursor()
        like_pattern = '%'
        if kategori == 'Tüp':
            like_pattern = '%Tüp'
        elif kategori == 'İndirimli':
            like_pattern = 'İndirimli%'
        elif kategori == 'Su':
            like_pattern = '%LT'
        cursor.execute("""
            SELECT COALESCE(SUM(tutar), 0) FROM borclar
            WHERE substr(tarih,1,10)>=? AND substr(tarih,1,10)<=?
            AND islem_turu=? AND urun_adi LIKE ?
        """, (ilk_gun, son_gun, islem_turu, like_pattern))
        toplam = cursor.fetchone()[0]
        conn.close()
        return toplam

    def get_gunluk_ozet(self, ilk_gun, son_gun):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT substr(tarih,1,10) as gun,
                COALESCE(SUM(CASE WHEN islem_turu='Borç' THEN tutar ELSE 0 END), 0) as satis,
                COALESCE(SUM(CASE WHEN islem_turu='Borç Düşme' THEN tutar ELSE 0 END), 0) as tahsilat
            FROM borclar WHERE substr(tarih,1,10)>=? AND substr(tarih,1,10)<=?
            GROUP BY gun ORDER BY gun
        """, (ilk_gun, son_gun))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ==================== PEŞİN SATIŞ METODLARI ====================

    def add_pesin_satis(self, tarih, musteri_adi, urun_adi, adet, birim_fiyat, toplam_tutar, odeme_turu, aciklama):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO pesin_satislar (tarih, musteri_adi, urun_adi, adet, birim_fiyat, toplam_tutar, odeme_turu, aciklama)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tarih, musteri_adi, urun_adi, adet, birim_fiyat, toplam_tutar, odeme_turu, aciklama))
            cursor.execute("""
                UPDATE depo SET dolu_adet = MAX(dolu_adet - ?, 0), guncelleme_tarihi=datetime('now','localtime')
                WHERE urun_adi=?
            """, (adet, urun_adi))
            return cursor.lastrowid

    def get_pesin_satislar(self, tarih=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        if tarih:
            cursor.execute("SELECT * FROM pesin_satislar WHERE tarih=? ORDER BY id DESC", (tarih,))
        else:
            cursor.execute("SELECT * FROM pesin_satislar ORDER BY id DESC LIMIT 100")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_pesin_satis_toplam(self, tarih=None, ilk_gun=None, son_gun=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        if tarih:
            cursor.execute("SELECT COALESCE(SUM(toplam_tutar), 0) FROM pesin_satislar WHERE tarih=?", (tarih,))
        elif ilk_gun and son_gun:
            cursor.execute("SELECT COALESCE(SUM(toplam_tutar), 0) FROM pesin_satislar WHERE tarih>=? AND tarih<=?", (ilk_gun, son_gun))
        else:
            cursor.execute("SELECT COALESCE(SUM(toplam_tutar), 0) FROM pesin_satislar")
        toplam = cursor.fetchone()[0]
        conn.close()
        return toplam

    def get_pesin_satis_detay(self, tarih):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT urun_adi, COALESCE(SUM(adet), 0) as adet, COALESCE(SUM(toplam_tutar), 0) as toplam
            FROM pesin_satislar WHERE tarih=? GROUP BY urun_adi ORDER BY urun_adi
        """, (tarih,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ==================== YEDEK METODLARI ====================

    def add_yedek_log(self, dosya_adi, dosya_boyutu, durum, hata_mesaji=''):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO yedek_log (dosya_adi, dosya_boyutu, durum, hata_mesaji)
                VALUES (?, ?, ?, ?)
            """, (dosya_adi, dosya_boyutu, durum, hata_mesaji))

    def get_yedek_gecmisi(self, limit=10):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM yedek_log ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ==================== AYAR METODLARI ====================

    def get_ayar(self, anahtar):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT deger FROM uygulama_ayarlari WHERE anahtar=?", (anahtar,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ''

    def set_ayar(self, anahtar, deger):
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO uygulama_ayarlari (anahtar, deger, guncelleme_tarihi)
                VALUES (?, ?, datetime('now','localtime'))
            """, (anahtar, deger))
