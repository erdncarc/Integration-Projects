import laspy
import numpy as np
from laspy.vlrs.known import GeoKeyDirectoryVlr, WktCoordinateSystemVlr
from pyproj import Transformer, CRS

las_isim = '.las'  # LAS dosyasının adı.
donusecegi_epsg = 5257  # Hedef EPSG kodu.

las = laspy.read(las_isim)  # LAS dosyasını okur.

# Mevcut EPSG kodunu alır.
suanki_epsg = None
for vlr in las.header.vlrs:  # LAS dosyasının header kısmında bulunan VLR'leri dolaşır.
	if isinstance(vlr, GeoKeyDirectoryVlr):  # Eğer VLR, EPSG kodunu içeren GeoKeyDirectoryVlr ise,
		for key in vlr.geo_keys:  # içerisindeki geo_key'lere bakar.
			if key.id == 3072:
				suanki_epsg = key.value_offset  # Mevcut EPSG kodunu alır.
				key.value_offset = donusecegi_epsg  # EPSG kodunu günceller.
				break

# Koordinat sistemi dönüşüm aracı oluşturur.
donusturucu = Transformer.from_crs(CRS.from_epsg(suanki_epsg), CRS.from_epsg(donusecegi_epsg), always_xy=True)

# Tüm nokta koordinatları, LAS dosyasındaki EPSG'den donusecegi_epsg'ye dönüştürür.
donusmus_noktalar = np.array(donusturucu.transform(las.x, las.y))

# Dönüştürülmüş x ve y koordinatlarını LAS dosyasına yazar.
las.x = donusmus_noktalar[0]
las.y = donusmus_noktalar[1]

for i, vlr in enumerate(las.header.vlrs):  # LAS dosyasının header kısmında bulunan VLR'leri dolaşır.
	if isinstance(vlr, WktCoordinateSystemVlr):  # Eğer VLR WktCoordinateSystemVlr türündeyse, yeni WKT'yi yükleyip günceller.
		with open(f'lib/wkt/{donusecegi_epsg}.wkt', 'r') as dosya:  # Yeni EPSG'ye uygun WKT dosyasını açar.
			wkt = dosya.read()
			las.header.vlrs[i] = WktCoordinateSystemVlr(wkt)

# Yeni LAS dosyası ismini oluşturur ve dosyayı yazar.
las_isim = 'lib/' + las_isim[:-4] + f'_{donusecegi_epsg}.las'
las.write(las_isim)
