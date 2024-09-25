import pandas as pd


# Excel dosyasını okur ve dosyada bulunan verileri array olarak döndürür.
def get_datas(dizin):
	df = pd.read_excel(dizin, engine='openpyxl')
	return [grup.values.tolist() for _, grup in df.groupby(df.columns[0])]  # Verileri ilk sütuna göre sıralar.


# Bir array'deki veriyi verilen dosya adına Excel formatında yazar.
def write_excel(veri, dizin):
	df = pd.DataFrame(veri, columns=["kablo_no", "direk_no", "seri_no", "uzunluk"])
	with pd.ExcelWriter(dizin, engine='openpyxl') as dosya:
		df.to_excel(dosya, index=False)


def main():
	veriler = get_datas(".xlsx")
	tek, cift, diger = [], [], []  # tek: 1 satırlık gruplar, cift: 2 satırlık gruplar, diger: 2'den fazla satırlık gruplar.

	# Verileri satır sayılarına göre sınıflandırır.
	for veri in veriler:
		(tek if len(veri) == 1 else
		 cift if len(veri) == 2 else
		 diger).extend(veri)

	ayristirilanlar = []  # Karşılaştırılarak seçilebilenler.
	harfliler = []  # Direk_sıralama sütununda harf içerdiğinden karşılaştırılarak seçilemeyenler.

	for i in range(0, len(cift), 2):
		try:
			bir = int(cift[i][1])  # İlk satırdaki direk numarası.
			iki = int(cift[i + 1][1])  # İkinci satırdaki direk numarası.

			# Direk numarası küçük olan satır 'ayristirilanlar' listesine eklenir.
			ayristirilanlar.append(cift[i + 1] if bir > iki else cift[i])

		except Exception:
			# Eğer direk numarası harf içeriyorsa üst kısım hata verir ve bu satırlar 'harfliler' listesine eklenir.
			harfliler.extend([cift[i], cift[i + 1]])

	# Sonuçları farklı Excel dosyalarına yazar.
	write_excel(tek, "lib/tek.xlsx")
	write_excel(diger, "lib/diger.xlsx")
	write_excel(ayristirilanlar, "lib/ayristirilanlar.xlsx")
	write_excel(harfliler, "lib/harfliler.xlsx")


main()
