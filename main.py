import hashlib
import time
import json
import os
import open3d as o3d
import numpy as np


### --- Blockchain Bölümü --- ###

class Block:
    def __init__(self, index, timestamp, maintenance_data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.maintenance_data = maintenance_data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = str(self.index) + str(self.timestamp) + json.dumps(self.maintenance_data,
                                                                          sort_keys=True) + self.previous_hash
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), "Genesis Block", "0")
        self.chain.append(genesis_block)

    def add_block(self, maintenance_data):
        last_block = self.chain[-1]
        new_block = Block(len(self.chain), time.time(), maintenance_data, last_block.hash)
        self.chain.append(new_block)

    def display_chain(self):
        for block in self.chain:
            print(f"Block #{block.index}")
            print(f"Timestamp: {block.timestamp}")
            print(f"Maintenance Data: {block.maintenance_data}")
            print(f"Hash: {block.hash}")
            print(f"Previous Hash: {block.previous_hash}")
            print("-----------")


def add_maintenance_record(blockchain, vehicle_id, service_provider, maintenance_description):
    maintenance_data = {
        'vehicle_id': vehicle_id,
        'service_provider': service_provider,
        'maintenance_description': maintenance_description
    }
    blockchain.add_block(maintenance_data)


### --- Hasar Tespiti ve 3D Görselleştirme --- ###

renkler = {
    "ağır": [1.0, 0.0, 0.0],  # Kırmızı
    "orta": [1.0, 0.5, 0.0],  # Turuncu
    "hafif": [1.0, 1.0, 0.0],  # Sarı
    "": [0.8, 0.8, 0.8]  # Gri (varsayılan)
}


def yorumla_hasar(bakim_aciklamasi):
    bakim_aciklamasi = bakim_aciklamasi.lower()
    hasar_verisi = {}

    if "ön tampon" in bakim_aciklamasi or "ön çamurluk" in bakim_aciklamasi:
        hasar_verisi["ön"] = "ağır"
    if "arka far" in bakim_aciklamasi or "arka tampon" in bakim_aciklamasi:
        hasar_verisi["arka"] = "orta"
    if "kapı çizik" in bakim_aciklamasi or "sol kapı" in bakim_aciklamasi:
        hasar_verisi["sol"] = "hafif"
    if "sağ kapı" in bakim_aciklamasi or "sağ çamurluk" in bakim_aciklamasi:
        hasar_verisi["sağ"] = "hafif"
    if "tavan" in bakim_aciklamasi or "cam" in bakim_aciklamasi:
        hasar_verisi["üst"] = "orta"
    if "alt" in bakim_aciklamasi or "şasi" in bakim_aciklamasi:
        hasar_verisi["alt"] = "ağır"

    return hasar_verisi


def yukle_ve_boya_model(dosya_yolu, hasar_verisi):
    if not os.path.exists(dosya_yolu):
        raise FileNotFoundError(f"Model dosyası bulunamadı: {dosya_yolu}")

    mesh = o3d.io.read_triangle_mesh(dosya_yolu)
    mesh.compute_vertex_normals()

    renkler_listesi = np.tile(renkler[""], (np.asarray(mesh.vertices).shape[0], 1))
    noktalar = np.asarray(mesh.vertices)

    # Modelin sınırlarını belirle
    x_min, x_max = np.min(noktalar[:, 0]), np.max(noktalar[:, 0])
    y_min, y_max = np.min(noktalar[:, 1]), np.max(noktalar[:, 1])
    z_min, z_max = np.min(noktalar[:, 2]), np.max(noktalar[:, 2])

    # Bölge tanımlamaları için eşik değerleri belirle
    x_threshold = 0.2 * (x_max - x_min)
    y_threshold = 0.2 * (y_max - y_min)
    z_threshold = 0.2 * (z_max - z_min)

    for i, vertex in enumerate(noktalar):
        x, y, z = vertex
        renk = renkler[""]  # Varsayılan renk

        # Ön kısım (x minimuma yakın)
        if x < x_min + x_threshold:
            renk = renkler[hasar_verisi.get("ön", "")]
        # Arka kısım (x maksimuma yakın)
        elif x > x_max - x_threshold:
            renk = renkler[hasar_verisi.get("arka", "")]
        # Sol kısım (y minimuma yakın)
        elif y < y_min + y_threshold:
            renk = renkler[hasar_verisi.get("sol", "")]
        # Sağ kısım (y maksimuma yakın)
        elif y > y_max - y_threshold:
            renk = renkler[hasar_verisi.get("sağ", "")]
        # Alt kısım (z minimuma yakın)
        elif z < z_min + z_threshold:
            renk = renkler[hasar_verisi.get("alt", "")]
        # Üst kısım (z maksimuma yakın)
        elif z > z_max - z_threshold:
            renk = renkler[hasar_verisi.get("üst", "")]

        renkler_listesi[i] = renk

    mesh.vertex_colors = o3d.utility.Vector3dVector(renkler_listesi)
    return mesh


def gorsel_goster(mesh):
    o3d.visualization.draw_geometries([mesh])


### --- Ana Program --- ###

if __name__ == "__main__":
    # Blockchain başlat
    vehicle_blockchain = Blockchain()

    # Örnek bakım kayıtları ekle
    add_maintenance_record(vehicle_blockchain, "ABC123", "Servis A", "Ön tampon hasarı ve sol kapı çizik")
    add_maintenance_record(vehicle_blockchain, "ABC123", "Servis B", "Arka far değişimi")
    add_maintenance_record(vehicle_blockchain, "XYZ789", "Servis C", "Tavan hasarı ve şasi kontrolü")

    # Blockchain'i göster
    print("\nBlockchain Kayıtları:")
    vehicle_blockchain.display_chain()

    # Hasar verilerini blockchain'den topla
    hasar_durumu = {}
    for block in vehicle_blockchain.chain[1:]:  # Genesis bloğunu atla
        aciklama = block.maintenance_data["maintenance_description"]
        yorum = yorumla_hasar(aciklama)
        hasar_durumu.update(yorum)

    print("\nTespit Edilen Hasar Durumu:")
    print(hasar_durumu)

    # Model dosya yolunu al
    model_dosyasi = input("3D model dosya yolunu girin: ").strip()

    try:
        model = yukle_ve_boya_model(model_dosyasi, hasar_durumu)
        print("\n3D Model Hasar Görselleştirmesi:")
        gorsel_goster(model)
    except Exception as e:
        print(f"\nHata oluştu: {e}")