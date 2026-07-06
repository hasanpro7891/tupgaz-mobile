import sqlite3
import os
from datetime import datetime

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aboneler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abone_no TEXT NOT NULL,
        kayit_tarihi TEXT NOT NULL DEFAULT (strftime('%d.%m.%Y', 'now', 'localtime')),
        son_siparis_tarihi TEXT DEFAULT '',
        ad TEXT NOT NULL,
        soyad TEXT NOT NULL DEFAULT '',
        servis_elemani TEXT DEFAULT '',
        abone_tipi TEXT DEFAULT 'Ev Abonesi'
            CHECK(abone_tipi IN ('Ev Abonesi', 'İş Yeri', 'Tali Bayii')),
        ek_adres TEXT DEFAULT '',
        mahalle TEXT DEFAULT '',
        sokak TEXT DEFAULT '',
        bina_no TEXT DEFAULT '',
        kat TEXT DEFAULT '',
        daire TEXT DEFAULT '',
        notlar TEXT DEFAULT '',
        aktif INTEGER DEFAULT 1,
        silindi INTEGER DEFAULT 0,
        silinme_tarihi TEXT,
        olusturma_tarihi TEXT DEFAULT (datetime('now', 'localtime')),
        guncelleme_tarihi TEXT DEFAULT (datetime('now', 'localtime')),
        UNIQUE(abone_no, silindi)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telefonlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abone_id INTEGER NOT NULL,
        tel_tipi TEXT NOT NULL CHECK(tel_tipi IN ('Ev', 'İş', 'Cep-1', 'Cep-2', 'Cep-3')),
        numara TEXT NOT NULL,
        FOREIGN KEY(abone_id) REFERENCES aboneler(id) ON DELETE CASCADE
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS borclar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abone_id INTEGER NOT NULL,
        tarih TEXT NOT NULL,
        tutar REAL NOT NULL CHECK(tutar != 0),
        aciklama TEXT DEFAULT '',
        islem_turu TEXT NOT NULL CHECK(islem_turu IN ('Borç', 'Borç Düşme')),
        urun_adi TEXT DEFAULT '',
        adet INTEGER DEFAULT 0 CHECK(adet >= 0),
        duzeltildi INTEGER DEFAULT 0,
        duzeltme_tarihi TEXT,
        duzeltme_aciklama TEXT,
        FOREIGN KEY(abone_id) REFERENCES aboneler(id) ON DELETE CASCADE
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emanet_hareketleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abone_id INTEGER NOT NULL,
        tup_tipi TEXT NOT NULL CHECK(tup_tipi IN (
            '2 KG', '12 KG', 'İndirimli 12 KG', '24 KG', '45 KG',
            'Hayat 19 LT', 'Berrak 19 LT'
        )),
        adet INTEGER NOT NULL CHECK(adet > 0),
        islem_turu TEXT NOT NULL CHECK(islem_turu IN ('Verildi', 'Alındı')),
        tarih TEXT NOT NULL,
        aciklama TEXT DEFAULT '',
        FOREIGN KEY(abone_id) REFERENCES aboneler(id) ON DELETE CASCADE
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emanet_bakiyesi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abone_id INTEGER NOT NULL UNIQUE,
        tup_2kg INTEGER DEFAULT 0 CHECK(tup_2kg >= 0),
        tup_12kg INTEGER DEFAULT 0 CHECK(tup_12kg >= 0),
        indirimli_12kg INTEGER DEFAULT 0 CHECK(indirimli_12kg >= 0),
        tup_24kg INTEGER DEFAULT 0 CHECK(tup_24kg >= 0),
        tup_45kg INTEGER DEFAULT 0 CHECK(tup_45kg >= 0),
        hayat_19lt INTEGER DEFAULT 0 CHECK(hayat_19lt >= 0),
        berrak_19lt INTEGER DEFAULT 0 CHECK(berrak_19lt >= 0),
        FOREIGN KEY(abone_id) REFERENCES aboneler(id) ON DELETE CASCADE
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS depo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        urun_adi TEXT NOT NULL UNIQUE CHECK(urun_adi IN (
            '2 KG Tüp', '12 KG Tüp', 'İndirimli 12 KG Tüp',
            '24 KG Tüp', '45 KG Tüp', 'Hayat 19 LT', 'Berrak 19 LT'
        )),
        dolu_adet INTEGER DEFAULT 0 CHECK(dolu_adet >= 0),
        bos_adet INTEGER DEFAULT 0 CHECK(bos_adet >= 0),
        guncelleme_tarihi TEXT DEFAULT (datetime('now', 'localtime'))
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fiyatlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        urun_adi TEXT NOT NULL UNIQUE,
        fiyat REAL NOT NULL DEFAULT 0 CHECK(fiyat >= 0),
        guncelleme_tarihi TEXT DEFAULT (datetime('now', 'localtime'))
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS giderler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih TEXT NOT NULL,
        tutar REAL NOT NULL CHECK(tutar > 0),
        kategori TEXT NOT NULL CHECK(kategori IN (
            'Kira', 'Elektrik', 'Su', 'Personel', 'Nakliye', 'Bakım', 'Vergi', 'Diğer'
        )),
        aciklama TEXT DEFAULT '',
        eklenme_tarihi TEXT DEFAULT (datetime('now', 'localtime'))
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS yedek_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        dosya_adi TEXT NOT NULL,
        dosya_boyutu INTEGER,
        durum TEXT DEFAULT 'Başarılı' CHECK(durum IN ('Başarılı', 'Başarısız')),
        hata_mesaji TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uygulama_ayarlari (
        anahtar TEXT PRIMARY KEY,
        deger TEXT NOT NULL,
        guncelleme_tarihi TEXT DEFAULT (datetime('now', 'localtime'))
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pesin_satislar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih TEXT NOT NULL,
        musteri_adi TEXT DEFAULT 'Yürüyen Müşteri',
        urun_adi TEXT NOT NULL,
        adet INTEGER NOT NULL CHECK(adet > 0),
        birim_fiyat REAL NOT NULL CHECK(birim_fiyat >= 0),
        toplam_tutar REAL NOT NULL CHECK(toplam_tutar >= 0),
        odeme_turu TEXT DEFAULT 'Nakit' CHECK(odeme_turu IN ('Nakit', 'Kart', 'Havale/EFT')),
        aciklama TEXT DEFAULT '',
        eklenme_tarihi TEXT DEFAULT (datetime('now', 'localtime'))
    )""")

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_emanet_hareketi_bakiye
    AFTER INSERT ON emanet_hareketleri
    BEGIN
        UPDATE emanet_bakiyesi SET
            tup_2kg = CASE WHEN NEW.tup_tipi = '2 KG' THEN
                tup_2kg + CASE WHEN NEW.islem_turu = 'Verildi' THEN NEW.adet ELSE -NEW.adet END
                ELSE tup_2kg END,
            tup_12kg = CASE WHEN NEW.tup_tipi = '12 KG' THEN
                tup_12kg + CASE WHEN NEW.islem_turu = 'Verildi' THEN NEW.adet ELSE -NEW.adet END
                ELSE tup_12kg END,
            indirimli_12kg = CASE WHEN NEW.tup_tipi = 'İndirimli 12 KG' THEN
                indirimli_12kg + CASE WHEN NEW.islem_turu = 'Verildi' THEN NEW.adet ELSE -NEW.adet END
                ELSE indirimli_12kg END,
            tup_24kg = CASE WHEN NEW.tup_tipi = '24 KG' THEN
                tup_24kg + CASE WHEN NEW.islem_turu = 'Verildi' THEN NEW.adet ELSE -NEW.adet END
                ELSE tup_24kg END,
            tup_45kg = CASE WHEN NEW.tup_tipi = '45 KG' THEN
                tup_45kg + CASE WHEN NEW.islem_turu = 'Verildi' THEN NEW.adet ELSE -NEW.adet END
                ELSE tup_45kg END,
            hayat_19lt = CASE WHEN NEW.tup_tipi = 'Hayat 19 LT' THEN
                hayat_19lt + CASE WHEN NEW.islem_turu = 'Verildi' THEN NEW.adet ELSE -NEW.adet END
                ELSE hayat_19lt END,
            berrak_19lt = CASE WHEN NEW.tup_tipi = 'Berrak 19 LT' THEN
                berrak_19lt + CASE WHEN NEW.islem_turu = 'Verildi' THEN NEW.adet ELSE -NEW.adet END
                ELSE berrak_19lt END
        WHERE abone_id = NEW.abone_id;
    END""")

    for table in ['aboneler', 'telefonlar', 'borclar', 'emanet_hareketleri',
                  'emanet_bakiyesi', 'giderler']:
        if table == 'aboneler':
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_aktif ON {table}(aktif, silindi)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_ad ON {table}(ad)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_soyad ON {table}(soyad)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_no ON {table}(abone_no)")
        elif table == 'telefonlar':
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_abone ON {table}(abone_id)")
        elif table == 'borclar':
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_abone ON {table}(abone_id)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_tarih ON {table}(tarih)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_tur ON {table}(islem_turu)")
        elif table in ('emanet_hareketleri',):
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_abone ON {table}(abone_id)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_tarih ON {table}(tarih)")
        elif table in ('emanet_bakiyesi',):
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_abone ON {table}(abone_id)")
        elif table == 'giderler':
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_tarih ON {table}(tarih)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_kategori ON {table}(kategori)")

    initial_prices = [
        ('2 KG Tüp', 0.0),
        ('12 KG Tüp', 0.0),
        ('İndirimli 12 KG Tüp', 0.0),
        ('24 KG Tüp', 0.0),
        ('45 KG Tüp', 0.0),
        ('Hayat 19 LT', 0.0),
        ('Berrak 19 LT', 0.0),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO fiyatlar (urun_adi, fiyat, guncelleme_tarihi) VALUES (?, ?, ?)",
        [(u, f, datetime.now().strftime("%d.%m.%Y")) for u, f in initial_prices]
    )

    initial_stock = [
        ('2 KG Tüp', 0, 0),
        ('12 KG Tüp', 0, 0),
        ('İndirimli 12 KG Tüp', 0, 0),
        ('24 KG Tüp', 0, 0),
        ('45 KG Tüp', 0, 0),
        ('Hayat 19 LT', 0, 0),
        ('Berrak 19 LT', 0, 0),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO depo (urun_adi, dolu_adet, bos_adet) VALUES (?, ?, ?)",
        initial_stock
    )

    cursor.execute(
        "INSERT OR IGNORE INTO uygulama_ayarlari (anahtar, deger) VALUES (?, ?)",
        ('son_yedek_tarihi', '')
    )

    conn.commit()
    conn.close()
