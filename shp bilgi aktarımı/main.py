import geopandas as gpd

# Shapefile'ları okur.
koordinat = gpd.read_file('.shp', encoding='utf-16')
bilgi = gpd.read_file('.shp', encoding='utf-16')

# Bilgilerin alınacağı dosyadan, koordinat dosyasına en yakın noktaları bulur.
en_yakin = gpd.sjoin_nearest(koordinat, bilgi, how="left", max_distance=None)

# Bulunan noktalardaki bilgileri alarak koordinat dosyasındaki noktalara atar.
yeni_gdf = en_yakin[['geometry', 'hatadi', 'hat_id', 'engadi', 'direkserin']]

# Yeni GeoDataFrame'i bir shp olarak kaydeder.
yeni_gdf.to_file('lib/bırlestırılmıs.shp', driver='ESRI Shapefile')
