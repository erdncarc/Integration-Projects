import os
import json
import pandas as pd

# 'hat_id' ve 'epsg' sütunlarını Excel dosyasından alır.
excel_verisi = pd.read_excel('.xlsx', usecols=['hat_id', 'epsg'], engine='openpyxl')

# 'hat_id' ve 'epsg' sütunları bir sözlük yapısına dönüştürülür. Böylece her hat_id için epsg kodu hızlıca alınabilir.
hat_epsg = dict(zip(excel_verisi['hat_id'], excel_verisi['epsg']))

for dosya_adi in os.listdir('lib/excel'):  # 'lib/excel' dizinindeki tüm dosyalar taranıyor.
	if dosya_adi.endswith('.xlsx'):  # Sadece .xlsx uzantılı dosyalar ile işlem yapılıyor
		isim = dosya_adi[:-5]  # Dosya isminin uzantısı çıkarılarak (hat_id) kısmı elde ediliyor
		epsg = hat_epsg[isim].split('-')  # Dosyanın adı sözlükte aranır ve o hattın hangi paftalarda bulunduğu elde edilir.

		# Dosyanın 'plscadd_staking table' adlı sayfasından belirtilen sütunlar okunur.
		df = pd.read_excel(os.path.join('lib/excel', dosya_adi), sheet_name='plscadd_staking table', usecols=['Structure  Number', 'X  Easting   (m)', 'Y  Northing   (m)', 'Centerline Z  Elevation   (m)', 'Structure  Description'], engine='openpyxl')

		# X, Y ve Z koordinatları boş olmayan satırları seçer.
		df = df.dropna(subset=['X  Easting   (m)', 'Y  Northing   (m)', 'Centerline Z  Elevation   (m)'])

		veri1, isim1, veri2, isim2 = [], isim, [], ''
		onceki_x, ana_veri = abs(df.iloc[0]['X  Easting   (m)']), veri1

		for i in range(len(df)):
			# Eğer mevcut X koordinatı ile önceki X koordinatı arasındaki fark 100,000'den büyükse pafta değişikliği var demektir.
			if abs(df.iloc[i]['X  Easting   (m)'] - onceki_x) > 100_000:
				# Verilerin aktarıldığı liste değiştriilir.
				ana_veri = veri2
				# Yeni dosya isimleri EPSG kodlarına göre oluşturulur.
				isim1, isim2 = (f"{isim}_{epsg[1]}", f"{isim}_{epsg[0]}") if df.iloc[i]['X  Easting   (m)'] > onceki_x else (f"{isim}_{epsg[0]}", f"{isim}_{epsg[1]}")

			# Mevcut satırdaki veriler JSON yapısına dönüştürülerek listeye eklenir.
			ana_veri.append({
				"x": str(df.iloc[i]['X  Easting   (m)']),
				"y": str(df.iloc[i]['Y  Northing   (m)']),
				"z": str(df.iloc[i]['Centerline Z  Elevation   (m)']),
				"title": str(df.iloc[i]['Structure  Number']),
				"description": str(df.iloc[i]['Structure  Description'])
			})

			# Önceki X değeri güncellenir, böylece bir sonraki karşılaştırmada kullanılır.
			onceki_x = df.iloc[i]['X  Easting   (m)']

		# 'veri1' listesindeki veriler JSON formatında bir dosyaya yazılır.
		with open(os.path.join('lib/json', f"{isim1}.json"), 'w') as dosya:
			dosya.write(json.dumps(veri1, indent=4))

		# Eğer 'veri2' boş değilse, bu veriler de başka bir JSON dosyasına kaydedilir.
		if len(veri2) > 0:
			with open(os.path.join('lib/json', f"{isim2}.json"), 'w') as dosya:
				dosya.write(json.dumps(veri2, indent=4))
