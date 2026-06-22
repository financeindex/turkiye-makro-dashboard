"""
EVDS Seri Kodu Bulucu
======================
config/series.json'da "kod": null olan göstergeler için doğru EVDS seri
kodunu bulmanıza yardımcı olur.

Kullanım:
    export EVDS_API_KEY=anahtariniz
    python scripts/find_series.py işsizlik
    python scripts/find_series.py "cari işlemler"
    python scripts/find_series.py            # girdi ister

Bulduğunuz kodu config/series.json içindeki ilgili göstergenin
"kod" alanına yapıştırın, örn: "kod": "TP.XXXXX"
"""

import os
import sys

try:
    import borsapy as bp
except ImportError:
    sys.exit("borsapy kurulu değil. Önce: pip install -r requirements.txt")


def main():
    api_key = os.environ.get("EVDS_API_KEY")
    if not api_key:
        api_key = input("EVDS API anahtarınızı girin: ").strip()
    bp.set_evds_key(api_key)

    kelimeler = sys.argv[1:]
    if not kelimeler:
        girilen = input("Aranacak anahtar kelime(ler) (virgülle ayırın): ").strip()
        kelimeler = [k.strip() for k in girilen.split(",") if k.strip()]

    if not kelimeler:
        print("Anahtar kelime girilmedi, çıkılıyor.")
        return

    for kelime in kelimeler:
        print(f"\n=== '{kelime}' için bulunan seriler ===")
        try:
            sonuclar = bp.evds_search(kelime)
            print(sonuclar)
        except Exception as e:  # noqa: BLE001
            print(f"Arama sırasında hata oluştu: {e}")
            print("Alternatif: https://evds3.tcmb.gov.tr adresinden manuel arama yapabilirsiniz.")


if __name__ == "__main__":
    main()
