import laspy
import numpy as np
import geopandas as gpd
from scipy.spatial import KDTree

# LAS dosyasını okur ve X, Y, Z koordinatlarını alır.
las = laspy.read('.las')
bitki_noktalari = np.array(las.xyz)

# SHP dosyasından tel noktalarını okur.
tel_noktalari = gpd.read_file('.shp')

agac = KDTree(bitki_noktalari)  # Bitki noktaları için bir KDTree oluşturur.
yaricap = 5  # Tel noktaları etrafında bakılacak alanın uzunluğu.
ihlaller = set()  # İhlal edilen noktaları saklamak için bir set.

# Tel noktaları üzerinde iterasyon yaparak her bir noktanın yakınında bitki olup olmadığını kontrol eder.
for i, tel_noktasi in tel_noktalari.iterrows():
	# Her tel noktasının geometrisindeki tüm koordinatları kontrol et
	for nokta in tel_noktasi.geometry.coords:
		# KDTree'yi kullanarak bu tel noktasına belirli bir yarıçap içinde bulunan bitki noktalarını bul
		noktalar = agac.query_ball_point(np.array(nokta), yaricap)

		# Bulunan bitki noktaları ihlal edilmiş demektir
		for n in noktalar:
			ihlaller.add(tuple(bitki_noktalari[n]))

# İhlalleri bir dosyaya kaydet.
with open('lib/ihlaller.txt', 'w') as dosya:
	for nokta in ihlaller:
		dosya.write(f"{nokta[0]} {nokta[1]} {nokta[2]}\n")
