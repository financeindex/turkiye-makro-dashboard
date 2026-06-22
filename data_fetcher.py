import os
import pandas as pd
import requests

def fetch_evds_data():
    # GitHub Secrets'a eklediğimiz API anahtarını sistemden okuyoruz
    api_key = os.getenv("EVDS_API_KEY")
    if not api_key:
        print("HATA: EVDS_API_KEY bulunamadı!")
        return None
        
    # image_6533c0.png tablonuzdaki örnek göstergeler ve EVDS kod eşleşmeleri
    # Not: Gerçek kodları veri yapınıza göre EVDS üzerinden güncelleyebilirsiniz.
    series_dict = {
        'TP.CP.01': 'TR Enflasyon Oranı (TÜFE)-Aylık',
        'TP.AB.A02': 'TCMB Brüt Döviz Rezervi-Milyar $',
        'TP.AP01': 'TCMB Politika Faiz Oranı %',
        'TP.DK.USD.A': 'Dolar Kuru (Alış)'
    }
    
    series_ids = "-".join(series_dict.keys())
    # Dinamik olarak son 1-2 haftalık/aylık veriyi çekmek için geniş bir tarih aralığı veriyoruz
    url = f"https://evds2.tcmb.gov.tr/service/evds/series={series_ids}&startdate=01-01-2026&enddate=22-06-2026&type=json&key={api_key}"
    
    try:
        response = requests.get(url)
        res_json = response.json()
        
        if 'items' not in res_json:
            print("EVDS'den geçersiz veri döndü:", res_json)
            return None
            
        df = pd.DataFrame(res_json['items'])
        # Boş satırları ve UNNAMED sütunları temizle
        df = df.dropna(subset=['Tarih'])
        
        # Sütun isimlerini Türkçeleştir
        df.rename(columns=series_dict, inplace=True)
        
        output_data = []
        for col in series_dict.values():
            if col in df.columns:
                # Veriyi sayısal tipe dönüştür (virgül/nokta temizliği)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                valid_series = df[['Tarih', col]].dropna()
                
                if len(valid_series) >= 2:
                    # En güncel veri (Son satır veya tarihe göre sıralanmış hali)
                    # EVDS verileri genelde eskiden yeniye sıralı gelir, sondakiler en günceldir.
                    current_row = valid_series.iloc[-1]
                    previous_row = valid_series.iloc[-2]
                    
                    guncel = float(current_row[col])
                    onceki = float(previous_row[col])
                    
                    # Değişim yüzdesi hesaplama
                    degisim = ((guncel - onceki) / onceki) * 100 if onceki != 0 else 0
                    
                    output_data.append({
                        'Tarih': current_row['Tarih'],
                        'Veri': col,
                        'Güncel': round(guncel, 2),
                        'Önceki': round(onceki, 2),
                        'Değişim': f"{round(degisim, 1)}%"
                    })
        
        return pd.DataFrame(output_data)
    except Exception as e:
        print("Veri çekme esnasında hata oluştu:", e)
        return None

if __name__ == "__main__":
    # Klasörlerin varlığını kontrol et, yoksa oluştur
    os.makedirs("data", exist_ok=True)
    
    print("EVDS verileri çekiliyor...")
    macro_df = fetch_evds_data()
    
    if macro_df is not None and not macro_df.empty:
        # Dashboard için JSON, yedek için CSV kaydediyoruz
        macro_df.to_json("data/macro_data.json", orient="records", force_ascii=False, indent=4)
        macro_df.to_csv("data/macro_data.csv", index=False, encoding="utf-8-sig")
        print("Veriler 'data/' klasörüne başarıyla kaydedildi!")
    else:
        print("Veri kaydedilemedi.")
