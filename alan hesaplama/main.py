import geopandas as gpd
from shapely.ops import unary_union

# Shapefile dosyasından geometri verilerini okur.
gdf = gpd.read_file('.shp')

# Her bir geometrinin etrafına belirtilen uzunlukta(metre) bir buffer ekler.
buffer = gdf.geometry.buffer(0.25)

# Tüm geometrileri tek bir birleşik geometri haline getirir. Bu sayede geometriler kesişebilir veya birleşebilir.
birlesmis_buffer = unary_union(buffer)

# Geometrinin toplam alanını hesaplar.
toplam_alan = birlesmis_buffer.area

print(f"Alan: {toplam_alan} metrekare")
