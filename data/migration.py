import sqlite3
import shutil
import os
from datetime import datetime

def eski_db_var_mi(eski_yol):
    return os.path.exists(eski_yol)

def migrate(eski_yol, yeni_yol):
    if not eski_db_var_mi(eski_yol):
        return False

    yedek_yol = eski_yol + ".yedek." + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(eski_yol, yedek_yol)

    eski_conn = sqlite3.connect(eski_yol)
    eski_cursor = eski_conn.cursor()

    eski_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    eski_tablolar = {r[0] for r in eski_cursor.fetchall()}

    if 'aboneler' not in eski_tablolar:
        eski_conn.close()
        return False

    from data.db_init import init_db
    init_db(yeni_yol)

    yeni_conn = sqlite3.connect(yeni_yol)
    yeni_cursor = yeni_conn.cursor()

    eski_cursor.execute("PRAGMA table_info(aboneler)")
    eski_kolonlar = {r[1] for r in eski_cursor.fetchall()}

    abone_no_col = 'abone_no' if 'abone_no' in eski_kolonlar else 'abone_no' if 'no' in eski_kolonlar else None

    eski_cursor.execute("SELECT * FROM aboneler")
    eski_aboneler = eski_cursor.fetchall()
    eski_kolon_isimleri = [d[1] for d in eski_cursor.description]

    for row in eski_aboneler:
        row_dict = dict(zip(eski_kolon_isimleri, row))
        abone_no = str(row_dict.get('abone_no', row_dict.get('no', '')))
        if not abone_no:
            continue

        yeni_cursor.execute("""
            INSERT INTO aboneler (abone_no, kayit_tarihi, ad, soyad, servis_elemani,
                abone_tipi, ek_adres, mahalle, sokak, bina_no, kat, daire, notlar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row_dict.get('abone_no', '')),
            str(row_dict.get('kayit_tarihi', row_dict.get('kayit_tar', datetime.now().strftime("%d.%m.%Y")))),
            str(row_dict.get('ad', '')),
            str(row_dict.get('soyad', row_dict.get('soyadi', ''))),
            str(row_dict.get('servis_elemani', '')),
            str(row_dict.get('abone_tipi', row_dict.get('tip', 'Ev Abonesi'))),
            str(row_dict.get('ek_adres', '')),
            str(row_dict.get('mahalle', '')),
            str(row_dict.get('sokak', '')),
            str(row_dict.get('bina_no', row_dict.get('bina', ''))),
            str(row_dict.get('kat', '')),
            str(row_dict.get('daire', '')),
            str(row_dict.get('notlar', ''))
        ))
        yeni_abone_id = yeni_cursor.lastrowid

        if 'telefonlar' in eski_tablolar:
            try:
                eski_cursor.execute("SELECT * FROM telefonlar WHERE abone_id=?", (row_dict.get('id'),))
                for tel_row in eski_cursor.fetchall():
                    tel_dict = dict(zip([d[1] for d in eski_cursor.description], tel_row))
                    yeni_cursor.execute("""
                        INSERT INTO telefonlar (abone_id, tel_tipi, numara) VALUES (?, ?, ?)
                    """, (yeni_abone_id, tel_dict.get('tel_tipi', 'Cep-1'), str(tel_dict.get('numara', ''))))
            except Exception:
                tels = {}
                for key, tip in [('tel_ev', 'Ev'), ('tel_is', 'İş'), ('tel_cep1', 'Cep-1'),
                                  ('tel_cep2', 'Cep-2'), ('tel_cep3', 'Cep-3')]:
                    val = row_dict.get(key, '')
                    if val and str(val).strip():
                        tels[tip] = str(val).strip()
                for tip, num in tels.items():
                    yeni_cursor.execute("""
                        INSERT INTO telefonlar (abone_id, tel_tipi, numara) VALUES (?, ?, ?)
                    """, (yeni_abone_id, tip, num))

        yeni_cursor.execute("""
            INSERT OR IGNORE INTO emanet_bakiyesi
                (abone_id, tup_2kg, tup_12kg, indirimli_12kg, tup_24kg, tup_45kg, hayat_19lt, berrak_19lt)
            VALUES (?, 0, 0, 0, 0, 0, 0, 0)
        """, (yeni_abone_id,))

        if 'emanetler' in eski_tablolar:
            try:
                eski_cursor.execute("SELECT * FROM emanetler WHERE abone_id=?", (row_dict.get('id'),))
                emanet_row = eski_cursor.fetchone()
                if emanet_row:
                    e_dict = dict(zip([d[1] for d in eski_cursor.description], emanet_row))
                    tup_2kg = int(e_dict.get('tup_2kg', 0))
                    tup_12kg = int(e_dict.get('tup_12kg', 0))
                    tup_24kg = int(e_dict.get('tup_24kg', 0))
                    tup_45kg = int(e_dict.get('tup_45kg', 0))
                    su = int(e_dict.get('su', 0))
                    yeni_cursor.execute("""
                        UPDATE emanet_bakiyesi SET tup_2kg=?, tup_12kg=?, tup_24kg=?, tup_45kg=?, hayat_19lt=?
                        WHERE abone_id=?
                    """, (tup_2kg, tup_12kg, tup_24kg, tup_45kg, su, yeni_abone_id))
            except Exception:
                pass

    if 'borclar' in eski_tablolar:
        eski_cursor.execute("SELECT * FROM borclar ORDER BY id")
        eski_islemler = eski_cursor.fetchall()
        islem_kolonlari = [d[1] for d in eski_cursor.description]
        for row in eski_islemler:
            row_dict = dict(zip(islem_kolonlari, row))
            eski_abone_id = row_dict.get('abone_id')
            try:
                eski_abone_no = None
                orig_cursor = eski_conn.cursor()
                orig_cursor.execute("SELECT abone_no FROM aboneler WHERE id=?", (eski_abone_id,))
                orig_row = orig_cursor.fetchone()
                if orig_row:
                    eski_abone_no = str(orig_row[0])
                orig_cursor.close()
                if not eski_abone_no:
                    continue
                yeni_cursor.execute("SELECT id FROM aboneler WHERE abone_no=? AND silindi=0",
                                    (eski_abone_no,))
                yeni_abone = yeni_cursor.fetchone()
                if not yeni_abone:
                    continue
                yeni_abone_id = yeni_abone[0]

                eski_tutar = float(row_dict.get('tutar', 0))
                eski_tur = str(row_dict.get('islem_turu', 'Borç'))
                eski_tarih = str(row_dict.get('tarih', datetime.now().strftime("%d.%m.%Y %H:%M")))
                eski_aciklama = str(row_dict.get('aciklama', ''))
                eski_urun = str(row_dict.get('urun_adi', ''))
                eski_adet = int(row_dict.get('adet', 0))

                yeni_tur = 'Borç' if eski_tur in ('Borç', 'Sipariş', 'Satış') else 'Borç Düşme'

                if eski_urun and eski_urun in ('Su', 'Su 19 LT', 'Damacana'):
                    eski_urun = 'Hayat 19 LT'

                yeni_cursor.execute("""
                    INSERT INTO borclar (abone_id, tarih, tutar, aciklama, islem_turu, urun_adi, adet)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (yeni_abone_id, eski_tarih, eski_tutar, eski_aciklama, yeni_tur, eski_urun, eski_adet))
            except Exception:
                pass

    if 'fiyatlar' in eski_tablolar:
        try:
            eski_cursor.execute("SELECT urun_adi, fiyat FROM fiyatlar")
            for u, f in eski_cursor.fetchall():
                u = str(u)
                if u in ('Su', 'Su 19 LT'):
                    u = 'Hayat 19 LT'
                yeni_cursor.execute("UPDATE fiyatlar SET fiyat=? WHERE urun_adi=?", (float(f), u))
        except Exception:
            pass

    if 'depo' in eski_tablolar:
        try:
            eski_cursor.execute("SELECT urun_adi, dolu_adet, bos_adet FROM depo")
            for u, d, b in eski_cursor.fetchall():
                u = str(u)
                if u in ('Su', 'Su 19 LT'):
                    u = 'Hayat 19 LT'
                yeni_cursor.execute("UPDATE depo SET dolu_adet=?, bos_adet=? WHERE urun_adi=?",
                                    (int(d), int(b), u))
        except Exception:
            pass

    if 'giderler' in eski_tablolar:
        try:
            eski_cursor.execute("SELECT * FROM giderler")
            gider_kolonlari = [d[1] for d in eski_cursor.description]
            for row in eski_cursor.fetchall():
                row_dict = dict(zip(gider_kolonlari, row))
                yeni_cursor.execute("""
                    INSERT INTO giderler (tarih, tutar, kategori, aciklama) VALUES (?, ?, ?, ?)
                """, (str(row_dict.get('tarih', '')), float(row_dict.get('tutar', 0)),
                      str(row_dict.get('kategori', 'Diğer')), str(row_dict.get('aciklama', ''))))
        except Exception:
            pass

    yeni_conn.commit()
    yeni_conn.close()
    eski_conn.close()
    return True


def run_migration():
    from config import BASE_DIR, DB_PATH
    eski_yol = os.path.join(BASE_DIR, "data", "tupgaz.db")
    alt_eski_yol = os.path.join(BASE_DIR, "tupgaz.db")

    if os.path.exists(eski_yol) and os.path.getsize(eski_yol) > 0:
        from data.db_init import init_db
        yeni_yol = eski_yol + ".new"
        sonuc = migrate(eski_yol, yeni_yol)
        if sonuc:
            os.replace(yeni_yol, eski_yol)
            return True
    elif os.path.exists(alt_eski_yol) and os.path.getsize(alt_eski_yol) > 0:
        from data.db_init import init_db
        yeni_yol = eski_yol + ".new"
        sonuc = migrate(alt_eski_yol, yeni_yol)
        if sonuc:
            os.replace(yeni_yol, eski_yol)
            return True

    return False


if __name__ == "__main__":
    sonuc = run_migration()
    print("Migrasyon başarılı." if sonuc else "Migrasyon gerekmedi veya başarısız.")
