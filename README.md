# Türkiye Makro Bülten — Otomatik Veri Platformu

TCMB EVDS'den makroekonomik verileri haftalık olarak otomatik çeken, işleyen ve
canlı bir web dashboard'unda gösteren sistem.

## Nasıl çalışır

```
TCMB EVDS  →  scripts/collect_data.py  →  docs/data/*.json,csv  →  docs/index.html (GitHub Pages)
                      ↑
          GitHub Actions (her Pazartesi otomatik tetikler)
```

Veri çekme/işleme `docs/data/` klasörüne yazılır, dashboard da aynı klasördeki
JSON'u okuyup tabloyu oluşturur. GitHub Actions her hafta bu scripti otomatik
çalıştırıp sonucu repoya commit eder — siz hiçbir şey yapmazsınız.

## Kurulum (ilk seferlik)

### 1. Bu klasörü GitHub reponuza yükleyin
Bu dosyaları indirip oluşturduğunuz GitHub reposuna push edin (GitHub web
arayüzünden dosya yükleyerek de yapabilirsiniz — "Add file" > "Upload files").

### 2. EVDS API anahtarınızı repo secret'ı olarak ekleyin
1. Repo sayfasında **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `EVDS_API_KEY`
4. Value: TCMB EVDS'den aldığınız API anahtarı
5. **Add secret**

### 3. GitHub Pages'i etkinleştirin
1. Repo sayfasında **Settings** → **Pages**
2. "Build and deployment" → Source: **Deploy from a branch**
3. Branch: **main**, klasör: **/docs**
4. Save

Birkaç dakika içinde dashboard'unuz şu adreste yayında olacak:
`https://KULLANICI_ADINIZ.github.io/REPO_ADINIZ/`

### 4. İlk veri çekimini elle tetikleyin
1. Repo sayfasında **Actions** sekmesi
2. "Haftalık makro veri güncelleme" iş akışını seçin
3. **Run workflow** butonuna basın
4. ~1 dakika sonra `docs/data/latest.json` güncellenmiş olacak

Bundan sonra her Pazartesi 08:00 (TR saati) otomatik çalışır. Elle tetiklemek
istediğinizde de aynı "Run workflow" butonunu kullanabilirsiniz.

## Eksik göstergeleri tamamlama

`config/series.json` içinde `"kod": null` olan göstergeler henüz EVDS seri
koduna bağlanmamıştır (dashboard'da "EVDS seri kodu tanımlanmadı" olarak
görünür). Bunları tamamlamak için:

```bash
pip install -r requirements.txt
export EVDS_API_KEY=anahtariniz
python scripts/find_series.py işsizlik
python scripts/find_series.py "cari işlemler"
```

Çıkan sonuçlardan doğru seriyi bulup `config/series.json` içindeki ilgili
göstergenin `"kod"` alanına yapıştırın, değişikliği commit edip push edin.
Bir sonraki otomatik çalışmada (veya Actions'tan elle tetiklediğinizde) o
gösterge de dolacaktır.

## Yeni gösterge ekleme

`config/series.json` içine yeni bir nesne eklemeniz yeterli:

```json
{
  "id": "ornek_id",
  "ad": "Ekrandaki görünen ad",
  "frekans": "Aylık",
  "birim": "%",
  "tip": "seviye",
  "kaynak_turu": "series",
  "kod": "TP.XXXX"
}
```

`"tip"` alanı:
- `"seviye"` — seriyi olduğu gibi kullan (çoğu gösterge bu)
- `"yoy"` — yıllık % değişim TCMB EVDS'nin kendisi yerine script tarafından hesaplansın (TÜFE yıllık gibi)
- `"mom"` — aylık % değişim script tarafından hesaplansın

## Yol haritası (sırayla planlanan)

- [x] **Faz 1 — TCMB EVDS (Aylık + Çeyreklik göstergeler)** — bu teslimat
- [ ] **Faz 2 — Haftalık piyasa verileri** (petrol, altın, VIX, DXY, ABD 10Y, TR Borsa) — Yahoo Finance üzerinden
- [ ] **Faz 3 — CDS primi ve TR tahvil getirileri** — yöntem henüz belirlenmedi (manuel giriş veya mevcut bir terminal API'si)

## Sorun mu çıktı?

Bu kod sizin için internet erişimi olmayan bir ortamda yazıldığı için test
edilmeden teslim edildi. İlk çalıştırmada bir hata görürseniz (Actions
sekmesindeki log çıktısını) Claude'a yapıştırın, birlikte düzeltelim.
