import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon

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


# Belirli bir dizindeki shapefile'den poligon geometrilerini alır.
def get_pafta(dizin):
	return [list(geom.exterior.coords) for geom in gpd.read_file(dizin).geometry if geom.geom_type == 'Polygon']


# Verilen bir nokta bulutunun hangi EPSG kodlarına ait olduğunu belirler.
def get_epsg(nokta_bulutu, alanlar):
	epsg = [str(kod) for kod, alan in alanlar.items() if alan.intersects(nokta_bulutu)]  # Verilen nokta bulutunun kesiştiği EPSG kodlarını listeler.
	return '-'.join(epsg)  # EPSG kodlarını  onlarını '-' ile birleştirip string olarak döndürür,


def main():
	gdf = gpd.read_file('.shp')

	alanlar = {key: Polygon(get_pafta(dizin)[0]) for key, dizin in dizinler.items()}  # Her EPSG kodu için poligon geometrilerini hesaplar.
	gdf['epsg'] = gdf.geometry.apply(lambda geom: get_epsg(geom, alanlar))  # Her satır için EPSG kodlarını bulup, Excel'e yeni bir sütun ekler.
	gdf.to_excel('lib/tum_hatlar.xlsx', index=False)  # Tüm verileri tek bir Excel dosyasında tek bir sayfaya kaydeder.

	# Farklı EPSG kodlarına göre verileri ayırıp ayrı ayrı sayfalara kaydeder.
	with pd.ExcelWriter('lib/hatlar.xlsx') as dosya:
		for epsg in dizinler.keys():
			# EPSG kodları '-' ile birleştirilmiş string olduğundan, bu kodu içerenler satırları bulur.
			region_gdf = gdf[gdf['epsg'].str.contains(str(epsg), na=False)]
			# Bulunan verileri ilgili EPSG koduyla aynı isimde bir Excel sayfasına yazar.
			region_gdf.to_excel(dosya, sheet_name=str(epsg), index=False)


main()
