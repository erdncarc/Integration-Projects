import laspy
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import Point
from pyproj import Transformer, CRS
from laspy.vlrs.known import GeoKeyDirectoryVlr, WktCoordinateSystemVlr

# Pafta dosyalarının dizinlerini tutar.
dizinler = {
	5253: 'lib/pafta/TM_27.shp',
	5254: 'lib/pafta/TM_30.shp',
	5255: 'lib/pafta/TM_33.shp',
	5256: 'lib/pafta/TM_36.shp',
	5257: 'lib/pafta/TM_39.shp',
	5258: 'lib/pafta/TM_42.shp',
	5259: 'lib/pafta/TM_45.shp'
}


# SHP dosyalarındaki tüm pafta geometrilerini tek bir GeoDataFrame'e yükler.
def get_pafta_gdf():
	pafta_list = []  # Paftaları depolamak için bir liste.

	# Dizindeki her bir EPSG ve ona karşılık gelen dosya yolunu döngüyle okur.
	for epsg, dizin in dizinler.items():
		gdf = gpd.read_file(dizin)  # SHP dosyasını GeoDataFrame formatında okur.
		gdf['id'] = epsg  # Her paftaya o paftanın EPSG kodunu içeren bir 'id' sütunu ekler.
		pafta_list.append(gdf)
	return pd.concat(pafta_list)  # "pd.concat" ile tüm gdf'leri tek bir gdf'de birleştirir.


# Verilen bilgileri kullanarak yeni LAS dosyası oluşturur.
def create_las(las, index, suanki_epsg, donusturulecek_epsg, las_isim):
	yeni_las = laspy.LasData(header=las.header)  # Yeni LAS dosyasının header'ını, mevcut LAS verisinden kopyalar.
	yeni_las.points = las.points[index]  # İlgili noktaları yeni LAS dosyasına ekle.

	for vlr in yeni_las.header.vlrs:  # LAS dosyasının header kısmında bulunan VLR'leri dolaşır.
		if isinstance(vlr, GeoKeyDirectoryVlr):  # Eğer VLR, EPSG kodunu içeren GeoKeyDirectoryVlr ise,
			for key in vlr.geo_keys:  # içerisindeki geo_key'lere bakar.
				if key.id == 3072:
					key.value_offset = donusturulecek_epsg  # EPSG kodunu günceller.
					break

	# Koordinat sistemi dönüşüm aracı oluşturur.
	donusturucu = Transformer.from_crs(CRS.from_epsg(suanki_epsg), CRS.from_epsg(donusturulecek_epsg), always_xy=True)

	# Tüm nokta koordinatları, suanki_epsg'den epsg'ye dönüştürür.
	donusmus_noktalar = np.array(donusturucu.transform(yeni_las.x, yeni_las.y))

	# Dönüştürülmüş x ve y koordinatlarını LAS dosyasına yazar.
	yeni_las.x = donusmus_noktalar[0]
	yeni_las.y = donusmus_noktalar[1]

	for i, vlr in enumerate(yeni_las.header.vlrs):  # LAS dosyasının header kısmında bulunan VLR'leri dolaşır.
		if isinstance(vlr, WktCoordinateSystemVlr):  # Eğer VLR WktCoordinateSystemVlr türündeyse, yeni WKT'yi yükleyip günceller.
			with open(f'lib/wkt/{donusturulecek_epsg}.wkt', 'r') as dosya:  # Yeni EPSG'ye uygun WKT dosyasını açar.
				wkt = dosya.read()
				yeni_las.header.vlrs[i] = WktCoordinateSystemVlr(wkt)

	# Yeni LAS dosyası ismini oluşturur ve dosyayı yazar.
	isim = 'lib/' + las_isim[:-4] + f'_{donusturulecek_epsg}.las'
	yeni_las.write(isim)


def main():
	las_isim = '.las'  # LAS dosyasının adı.
	las = laspy.read(las_isim)  # LAS dosyasını okur.

	# Mevcut EPSG kodunu alır.
	suanki_epsg = None
	for vlr in las.header.vlrs:  # LAS dosyasının header kısmında bulunan VLR'leri dolaşır.
		if isinstance(vlr, GeoKeyDirectoryVlr):  # Eğer VLR, EPSG kodunu içeren GeoKeyDirectoryVlr ise,
			for key in vlr.geo_keys:  # içerisindeki geo_key'lere bakar.
				if key.id == 3072:
					suanki_epsg = key.value_offset  # Mevcut EPSG kodunu alır.
					break

	# Koordinat sistemi dönüşüm aracı oluşturur.
	donusturucu = Transformer.from_crs(CRS.from_epsg(suanki_epsg), CRS.from_epsg(4326), always_xy=True)

	# Tüm nokta koordinatları, suanki_epsg'den 4326'ya dönüştürür.
	donusmus_noktalar = np.array(donusturucu.transform(las.x, las.y))

	noktalar = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(donusmus_noktalar[0], donusmus_noktalar[1])], crs="EPSG:4326")  # Dönüşen noktaları gdf formatına dönüştürür.
	alanlar = get_pafta_gdf()  # Paftaları gdf olarak alır.

	# Noktaları paftalarla kesişimlerine göre topluca eşler.
	eslesmeler = noktalar.sjoin(alanlar[['geometry', 'id']], predicate='intersects')

	# Eşleşmelere göre create_las fonksiyonunu çağırır ve LAS dosyalarını oluşturur.
	for epsg, grup in eslesmeler.groupby('id'):
		create_las(las, grup.index.to_list(), suanki_epsg, int(epsg), las_isim)


main()
