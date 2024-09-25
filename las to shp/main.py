import laspy
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer, CRS
from laspy.vlrs.known import GeoKeyDirectoryVlr

las_isim = ".las"  # LAS dosyasının ismi.
shp_isim = las_isim[:-4] + ".shp"  # ".las" uzantısını çıkarıp yerine ".shp" ekleyerek SHP dosyası adı oluşturulur.

las = laspy.read(las_isim)  # laspy kullanılarak LAS dosyasındaki veriler okunur.
noktalar = las.xyz  # LAS dosyasındaki x, y, z koordinatları elde edilir.

donusecegi_epsg = 4326  # Kordinatların enlem-boylam şeklinde olduğu EPSG kodu.
suanki_epsg = None

for vlr in las.header.vlrs:  # LAS dosyasının header kısmında bulunan VLR'leri dolaşır.
	if isinstance(vlr, GeoKeyDirectoryVlr):  # Eğer VLR, EPSG kodunu içeren GeoKeyDirectoryVlr ise,
		for key in vlr.geo_keys:  # içerisindeki geo_key'lere bakar.
			if key.id == 3072:
				suanki_epsg = key.value_offset  # Mevcut EPSG kodunu bulur ve suanki_epsg değişkenine atar.
				break

# Koordinat sistemi dönüşüm aracı oluşturur.
donusturucu = Transformer.from_crs(CRS.from_epsg(suanki_epsg), CRS.from_epsg(donusecegi_epsg), always_xy=True)

# Tüm nokta koordinatları, LAS dosyasındaki EPSG'den 4326'ya dönüştürür.
donusmus_noktalar = [donusturucu.transform(x, y) for x, y, z in noktalar]

# x ve y koordinatlarını kullanarak geometrik noktalar oluşturulur.
geom = [Point(x, y) for x, y in donusmus_noktalar]

# 'geometry' sütununa geometrik noktalar eklenir ve WGS84, GeoDataFrame'in CRS'si olarak ayarlanır.
gdf = gpd.GeoDataFrame(geometry=geom, crs=CRS.from_epsg(donusecegi_epsg))

# GeoDataFrame'i SHP dosyasına kaydetme işlemi.
gdf.to_file(shp_isim)
