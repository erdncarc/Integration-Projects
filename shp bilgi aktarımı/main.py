import geopandas as gpd

# Shapefile'ları okur.
gdf1 = gpd.read_file('.shp', encoding='utf-16')
gdf2 = gpd.read_file('.shp')

# En yakın noktaları bulmak için spatial join yapar.
en_yakin = gpd.sjoin_nearest(gdf1, gdf2, how="left", max_distance=None)

# Gerekli sütunları seçer.
yeni_shp = en_yakin[['geometry', 'hatadi', 'hat_id', 'engadi', 'direkserin']]

# Yeni GeoDataFrame'i bir Shapefile olarak kaydeder.
yeni_shp.to_file('lib/bırlestırılmıs.shp', driver='ESRI Shapefile')
