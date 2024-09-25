import math
import laspy
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import Polygon, Point, LineString
from scipy.interpolate import LinearNDInterpolator
from pandas.core.dtypes.inference import is_integer

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


# Verilen dizindeki Excel tablosundan, direk türüne göre direk uzunluğunu çeker.
def fill_distances(dizin):
	df = pd.read_excel(dizin)  # Excel dosyasını okur ve DataFrame'e yükler.
	uzunluklar = {}  # Uzunluk verilerini tutacak boş bir sözlük oluşturur.
	for i in df.index:
		uzunluklar[df.iloc[i, 0]] = df.iloc[i, 1]  # İlk sütundaki değeri anahtar, ikinci sütundaki değeri sözlükteki karşılık olarak atar
	return uzunluklar


# Belirli bir dizindeki SHP dosyasından poligon geometrilerini alır.
def get_pafta(dizin):
	return [list(geom.exterior.coords) for geom in gpd.read_file(dizin).geometry if geom.geom_type == 'Polygon']


# Verilen dizindeki excel tablosunu okuyarak tüm verileri bir sözlüğe atar.
def get_excel(dizin, alanlar, uzunluklar):
	# 'Sayfa1' adlı sayfayı Excel dosyasından okur ve eksik verileri olan satırları düşürür (X ve Y sütunları için).
	df1 = pd.read_excel(dizin, sheet_name='Sayfa1').dropna(subset=['X  Easting   (m)', 'Y  Northing   (m)'])

	# 'Sayfa2' adlı sayfayı Excel dosyasından okur ve eksik verileri olan satırları düşürür (Enlem ve Boylam sütunları için).
	df2 = pd.read_excel(dizin, sheet_name='Sayfa2').dropna(subset=['Longitude  (deg)', 'Latitude  (deg)'])

	# Sadece gerekli sütunları alır.
	veri1 = df1[['Row #', 'Orientation  Angle   (gr.)', 'X  Easting   (m)', 'Y  Northing   (m)', 'Structure  Description']]
	veri2 = df2[['Longitude  (deg)', 'Latitude  (deg)']]

	sonuc = {}
	epsg = 0

	for i in veri1.index:  # veri1 DataFrame'inin her bir satırında döner.
		for e, alan in alanlar.items():  # alanlar sözlüğündeki her bir epsg kodu ve alan üzerinde döner.
			if alan.intersects(Point(veri2.iloc[i]['Longitude  (deg)'], veri2.iloc[i]['Latitude  (deg)'])):  # Eğer enlem-boylam, alan ile kesişiyorsa,
				sonuc[str(int(veri1.iloc[i]['Row #']))] = {
					'point': {'x': veri2.iloc[i]['Longitude  (deg)'], 'y': veri2.iloc[i]['Latitude  (deg)']},
					'coordinates': {'x': veri1.iloc[i]['X  Easting   (m)'], 'y': veri1.iloc[i]['Y  Northing   (m)']},
					'distance': uzunluklar[veri1.iloc[i]['Structure  Description']],
					'EPSG': e,
					'orientation': veri1.iloc[i]['Orientation  Angle   (gr.)'] if is_integer(veri1.iloc[i]['Orientation  Angle   (gr.)']) else 0,
				}
				epsg = e
				break
	return sonuc, epsg


# İlk ve son direğin; semt açısı ve köşe kordinatlarının hesaplanması için sözlüğün başına ve sonuna, ilk ve son direğin hizasında ekstra bir direk ekler.
def create_extra(veriler):
	f1, f2, l1, l2 = list(veriler.keys())[:2][0], list(veriler.keys())[:2][1], list(veriler.keys())[-2:][0], list(veriler.keys())[-2:][1]
	dic1, dic2 = {}, {}
	dic1['first'] = {
		'coordinates': {
			'x': veriler[f1]['coordinates']['x'] - (veriler[f2]['coordinates']['x'] - veriler[f1]['coordinates']['x']),
			'y': veriler[f1]['coordinates']['y'] - (veriler[f2]['coordinates']['y'] - veriler[f1]['coordinates']['y'])
		},
		'distance': veriler[f1]['distance']
	}
	dic2['last'] = {
		'coordinates': {
			'x': veriler[l2]['coordinates']['x'] - (veriler[l1]['coordinates']['x'] - veriler[l2]['coordinates']['x']),
			'y': veriler[l2]['coordinates']['y'] - (veriler[l1]['coordinates']['y'] - veriler[l2]['coordinates']['y'])
		},
		'distance': veriler[f2]['distance']
	}
	return {**dic1, **veriler, **dic2}


# xy1'i merkez kabul eder ve xy2'yi merkeze göre aci kadar döndürür. Bunun sonucunda birim vektör elde edilir ve uzunluk kadar büyütülür.
def find_xy(xy1, xy2, aci, uzunluk):
	vektor1 = np.array([xy2[0] - xy1[0], xy2[1] - xy1[1]])  # xy1'den xy2'ye bir vektör oluşturur.
	birim_vektor1 = vektor1 / np.linalg.norm(vektor1)  # vektor1'in birim vektörünü hesaplar.

	# birim_vektor1'i, verilen açıya göre döndürür ve istediğimiz doğrultuda bir birim vektör elde etmemizi sağlar.
	birim_vektor2 = np.array([
		birim_vektor1[0] * math.cos(aci) - birim_vektor1[1] * math.sin(aci),
		birim_vektor1[0] * math.sin(aci) + birim_vektor1[1] * math.cos(aci)
	])

	vektor2 = birim_vektor2 * uzunluk  # Elde edilen birim vektörü, verilen uzunlukla çarparak yeni bir vektör elde eder.
	x, y = xy1[0] + vektor2[0], xy1[1] + vektor2[1]  # Yeni koordinatları hesaplar (xy1'den hareketle).

	return (x, y), (xy1[0] - (x - xy1[0]), xy1[1] - (y - xy1[1]))  # Hesaplanan yeni koordinatlar ve onun xy1'e göre simetriğini döndürür.


# Verilen verilerin direk ayaklarının x ve y kodinatlarını ve semt açısını hesaplar.
def find_angle_corner(veriler):
	hesaplanacak_uclu = []  # Hesaplamalar için gerekli 3 noktayı tutar.
	for key in veriler.keys():
		hesaplanacak_uclu.append(key)
		if len(hesaplanacak_uclu) != 3:   continue  # Eğer 3 nokta henüz seçilmediyse bir sonraki iterasyona geçer.

		xy1 = (veriler[hesaplanacak_uclu[0]]['coordinates']['x'], veriler[hesaplanacak_uclu[0]]['coordinates']['y'])
		xy2 = (veriler[hesaplanacak_uclu[1]]['coordinates']['x'], veriler[hesaplanacak_uclu[1]]['coordinates']['y'])
		xy3 = (veriler[hesaplanacak_uclu[2]]['coordinates']['x'], veriler[hesaplanacak_uclu[2]]['coordinates']['y'])

		# İki vektör oluşturulur: biri xy1'den xy2'ye, diğeri xy2'den xy3'e.
		v1 = np.array([xy2[0] - xy1[0], xy2[1] - xy1[1]])
		v2 = np.array([xy3[0] - xy2[0], xy3[1] - xy2[1]])

		theta = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))  # İki vektör arasındaki açıyı hesaplar.
		derece = np.degrees(theta) if np.cross(v1, v2) < 0 else -np.degrees(theta)  # Eğer çapraz çarpım negatifse açıyı negatif yap, değilse pozitif bırakır.
		derece = 0 if np.allclose(v1, v2, atol=1e-6) else derece  # Eğer vektörler neredeyse aynı ise dereceyi sıfır yapar.

		veriler[hesaplanacak_uclu[1]]['angle'] = derece * 10 / 9  # Açıyı 10/9 ile çarparak grad cinsine çevir ve verilerde saklar.

		# Köşelerin isimlendirmesi için gerekli yeni eksenleri oluşturur.
		y_ekseni = v1 / np.linalg.norm(v1)
		x_ekseni = np.array([-y_ekseni[1], y_ekseni[0]])

		# Açıortayların konumlarını hesaplar.
		d1, d2 = find_xy(xy2, xy3, math.radians(90 + derece / 2), veriler[hesaplanacak_uclu[1]]['distance'] / 2)

		# Köşe kordinatlarınu bulur.
		k1, k2 = find_xy(d1, xy2, math.radians(90), veriler[hesaplanacak_uclu[1]]['distance'] / 2)
		k3, k4 = find_xy(d2, xy2, math.radians(90), veriler[hesaplanacak_uclu[1]]['distance'] / 2)

		for i, nokta in enumerate([k1, k2, k3, k4], start=1):
			# Koordinatı, yeni x ve y eksenine göre dönüştürür (isimlendirmek için).
			yeni_kordinatlar = np.dot(np.array([x_ekseni, y_ekseni]).T, np.array([nokta[0] - xy2[0], nokta[1] - xy2[1]]))

			# Yeni koordinatlara göre noktayı isimlendirir.
			if yeni_kordinatlar[0] > 0 > yeni_kordinatlar[1]:
				isim = 'k1'
			elif yeni_kordinatlar[0] > 0 and yeni_kordinatlar[1] > 0:
				isim = 'k2'
			elif yeni_kordinatlar[0] < 0 < yeni_kordinatlar[1]:
				isim = 'k3'
			else:
				isim = 'k4'

			# Yeni noktayı orientation'a göre döndürür.
			yeni_nokta, _ = find_xy(xy2, nokta, math.radians(veriler[hesaplanacak_uclu[1]]['orientation'] * 9 / 10), np.linalg.norm(np.array([xy2[0] - nokta[0], xy2[1] - nokta[1]])))

			veriler[hesaplanacak_uclu[1]][isim] = {'x': yeni_nokta[0], 'y': yeni_nokta[1]}  # Verilere yeni noktayı kaydeder.

		# Üç noktanın ilk elemanını kaldırarak döngüye devam et.
		hesaplanacak_uclu.pop(0)

	# 'first' ve 'last' anahtarlarını verilerden sil.
	del veriler['first']
	del veriler['last']

	return veriler


# Verilen dosya yolundaki LAS dosyasına göre z değerlerini hesaplar.
def find_z(dizin, veriler):
	las = laspy.read(dizin)  # LAS dosyasını okur.

	# LAS dosyasındaki x ve y koordinatlarını kullanarak z değerlerini tahmin eden bir LinearNDInterpolator oluşturur.
	z_bulucu = LinearNDInterpolator(np.vstack((las.x, las.y)).T, las.z)

	for key in veriler.keys():
		# 'coordinates' için z değerini bulur ve ekler.
		veriler[key]['coordinates']['z'] = z_bulucu((veriler[key]['coordinates']['x'], veriler[key]['coordinates']['y']))

		# 'k1', 'k2', 'k3' ve 'k4' için z değerini bulur ve ekler.
		for i in range(1, 5):
			veriler[key][f'k{i}']['z'] = z_bulucu((veriler[key][f'k{i}']['x'], veriler[key][f'k{i}']['y']))
	return veriler


# Elde edilen değerleri Excel ve SHP formatında yazdırır.
def write_excel(veriler, epsg):
	# Excel'e yazılacak verilerin tutulacağı liste.
	excels = []

	# Poligonlar, noktalar, etiketler ve hatlar için listeler.
	polygons = []
	points = []
	labels = []
	line = []

	for key, value in veriler.items():
		# Her bir eleman için gerekli başlığı açarak sütunları oluşturur.
		excel = {
			'Struct_Num': key,
			'point_x': value['point']['x'],
			'point_y': value['point']['y'],
			'coordinates_x': value['coordinates']['x'],
			'coordinates_y': value['coordinates']['y'],
			'coordinates_z': value['coordinates']['z'],
			'EPSG': value['EPSG'],
			'distance': value['distance'],
			'angle': value['angle'],
			'k1_x': value['k1']['x'],
			'k1_y': value['k1']['y'],
			'k1_z': value['k1']['z'],
			'k1_diff': value['coordinates']['z'] - value['k1']['z'],
			'k2_x': value['k2']['x'],
			'k2_y': value['k2']['y'],
			'k2_z': value['k2']['z'],
			'k2_diff': value['coordinates']['z'] - value['k2']['z'],
			'k3_x': value['k3']['x'],
			'k3_y': value['k3']['y'],
			'k3_z': value['k3']['z'],
			'k3_diff': value['coordinates']['z'] - value['k3']['z'],
			'k4_x': value['k4']['x'],
			'k4_y': value['k4']['y'],
			'k4_z': value['k4']['z'],
			'k4_diff': value['coordinates']['z'] - value['k4']['z']
		}
		excels.append(excel)

		# Dört köşeyi kullanarak bir çokgen yapar.
		polygon = Polygon([
			(value['k1']['x'], value['k1']['y']),
			(value['k2']['x'], value['k2']['y']),
			(value['k3']['x'], value['k3']['y']),
			(value['k4']['x'], value['k4']['y'])
		])
		polygons.append(polygon)

		# k1, k2, k3 ve k4 noktalarını ve etiketlerini ekler.
		points.append(Point(value['k1']['x'], value['k1']['y']))
		labels.append('k1')
		points.append(Point(value['k2']['x'], value['k2']['y']))
		labels.append('k2')
		points.append(Point(value['k3']['x'], value['k3']['y']))
		labels.append('k3')
		points.append(Point(value['k4']['x'], value['k4']['y']))
		labels.append('k4')

		# Merkez noktaları kullanarak bir hat oluşturur.
		line.append((value['coordinates']['x'], value['coordinates']['y']))

	# Tüm verileri bir DataFrame'e çevirir ve kaydeder.
	df = pd.DataFrame(excels)
	df.to_excel('lib/tum_veriler.xlsx', index=False)

	# Alanları SHP dosyasına yazar.
	gdf = gpd.GeoDataFrame(geometry=polygons, crs=f'EPSG:{epsg}')
	gdf.to_file('lib/new_shp/alanlar.shp')

	# Köşeleri noktalar halinde SHP dosyasına yazar.
	gdf = gpd.GeoDataFrame({'label': labels, 'geometry': points}, crs=f'EPSG:{epsg}')
	gdf.to_file('lib/new_shp/koseler.shp')

	# Merkez noktalar arasındaki hattı SHP dosyasına kaydeder.
	line_gdf = gpd.GeoDataFrame(geometry=[LineString(line)], crs=f'EPSG:{epsg}')
	line_gdf.to_file('lib/new_shp/hat.shp')


def main():
	alanlar = {key: Polygon(get_pafta(dizin)[0]) for key, dizin in dizinler.items()}
	uzunluklar = fill_distances('.xlsx')
	veriler, epsg = get_excel('.xlsx', alanlar, uzunluklar)
	veriler = create_extra(veriler)
	veriler = find_angle_corner(veriler)
	veriler = find_z('.las', veriler)
	write_excel(veriler, epsg)


main()
