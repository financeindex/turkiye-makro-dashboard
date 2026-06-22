"""
Türkiye Makro Bülten - Veri Toplama Scripti
=============================================
Bu script config/series.json'da tanımlı göstergeleri TCMB EVDS'den
(borsapy kütüphanesi üzerinden) çeker, Güncel/Önceki/Değişim hesaplar
ve docs/data/ klasörüne (dashboard'un okuduğu yer) kaydeder.

Çalıştırma:
    EVDS_API_KEY=xxxx python scripts/collect_data.py

GitHub Actions üzerinde bu script haftalık otomatik çalışır
(bkz. .github/workflows/update.yml) ve EVDS_API_KEY repo secret'ından gelir.
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone

try:
    import borsapy as bp
except ImportError:
    sys.exit(
        "borsapy kurulu değil. Çalıştırmadan önce: pip install -r requirements.txt"
    )

CONFIG_PATH = os.path.join("config", "series.json")
OUTPUT_LATEST = os.path.join("docs", "data", "latest.json")
OUTPUT_HISTORY = os.path.join("docs", "data", "history.csv")


def api_anahtarini_yukle():
    key = os.environ.get("EVDS_API_KEY")
    if not key:
        sys.exit(
            "EVDS_API_KEY ortam değişkeni bulunamadı.\n"
            "Yerelde çalıştırmak için: export EVDS_API_KEY=anahtariniz\n"
            "GitHub Actions'da: repo Settings > Secrets > Actions > EVDS_API_KEY"
        )
    return key


def yuzde_degisim(guncel, onceki):
    if onceki in (None, 0):
        return None
    try:
        return round((guncel - onceki) / abs(onceki) * 100, 2)
    except (TypeError, ZeroDivisionError):
        return None


def donusum_uygula(seri, tip):
    """Ham seviye serisine yıllık/aylık % değişim dönüşümü uygular."""
    if tip == "yoy":
        return (seri / seri.shift(12) - 1) * 100
    if tip == "mom":
        return (seri / seri.shift(1) - 1) * 100
    return seri  # "seviye" -> dönüşüm yok


def gosterge_isle(ind, periyot_aylik="3y", periyot_ceyreklik="5y"):
    kaynak_turu = ind.get("kaynak_turu", "series")
    tip = ind.get("tip", "seviye")

    try:
        # --- Özel kaynak: TCMB politika faizi (doğrudan borsapy wrapper) ---
        if kaynak_turu == "policy_rate":
            tcmb = bp.TCMB()
            guncel = float(tcmb.policy_rate)
            return {
                "durum": "kismi",
                "not": "Sadece güncel değer mevcut; önceki değer geçmiş kayıtlardan birikecek.",
                "guncel": round(guncel, 2),
                "onceki": None,
                "degisim": None,
                "tarih": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            }

        # --- Standart kaynak: EVDS seri kodu ---
        kod = ind.get("kod")
        if not kod:
            return {"durum": "kod_gerekli"}

        periyot = periyot_ceyreklik if ind.get("frekans") == "Çeyreklik" else periyot_aylik
        df = bp.evds_series(kod, period=periyot)
        df = df.dropna()
        if df.empty:
            return {"durum": "veri_yok"}

        seri = df.iloc[:, -1]
        seri = donusum_uygula(seri, tip).dropna()

        if len(seri) < 2:
            return {"durum": "veri_yetersiz"}

        onceki = float(seri.iloc[-2])
        guncel = float(seri.iloc[-1])
        tarih = str(seri.index[-1])[:10]

        return {
            "durum": "ok",
            "guncel": round(guncel, 2),
            "onceki": round(onceki, 2),
            "degisim": yuzde_degisim(guncel, onceki),
            "tarih": tarih,
        }
    except Exception as e:  # noqa: BLE001 - tek göstergedeki hata diğerlerini durdurmamalı
        return {"durum": "hata", "mesaj": str(e)}


def main():
    api_key = api_anahtarini_yukle()
    bp.set_evds_key(api_key)

    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    calisma_zamani = datetime.now(timezone.utc).isoformat()
    sonuc = {"olusturulma_zamani": calisma_zamani, "veriler": []}

    ok_sayisi = 0
    for ind in config["gostergeler"]:
        sonuc_ind = gosterge_isle(ind)
        kayit = {**ind, **sonuc_ind}
        sonuc["veriler"].append(kayit)
        durum = sonuc_ind.get("durum")
        print(f"  [{durum:12s}] {ind['ad']}")
        if durum in ("ok", "kismi"):
            ok_sayisi += 1

    os.makedirs(os.path.dirname(OUTPUT_LATEST), exist_ok=True)
    with open(OUTPUT_LATEST, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)

    dosya_var = os.path.exists(OUTPUT_HISTORY)
    with open(OUTPUT_HISTORY, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if not dosya_var:
            w.writerow(["calisma_tarihi", "id", "guncel", "onceki", "degisim"])
        for k in sonuc["veriler"]:
            w.writerow(
                [calisma_zamani[:10], k["id"], k.get("guncel"), k.get("onceki"), k.get("degisim")]
            )

    print(f"\nToplam {len(sonuc['veriler'])} gösterge işlendi, {ok_sayisi} tanesi başarılı.")
    if ok_sayisi < len(sonuc["veriler"]):
        print("Eksik kalanlar için: python scripts/find_series.py <anahtar kelime>")


if __name__ == "__main__":
    main()
