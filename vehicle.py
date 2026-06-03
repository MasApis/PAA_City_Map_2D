# ============================================================
# VEHICLE / ANIMASI KENDARAAN
# Penanggung Jawab: Abdul Hafidz
# Deskripsi:
# Mengatur bentuk kendaraan, rotasi kendaraan, detail visual kendaraan,
# dan koordinat kendaraan agar dapat bergerak mengikuti rute hasil
# algoritma Dijkstra.
# ============================================================

import math

# Class yang menangani bentuk visual kendaraan dan rotasi kendaraan
# berdasarkan arah gerak dari titik saat ini menuju titik target.
class Vehicle:
    def __init__(self):
        # PERBAIKAN: Ukuran koordinat lokal F1 diperbesar agar proporsional di jalan raya
        self.bentuk_kendaraan = {
            "f1": [
                (-42, -6), (-36, -13), (-20, -15), (-4, -9),
                (16, -6), (34, -4), (46, 0), (34, 4),
                (16, 6), (-4, 9), (-20, 15), (-36, 13), (-42, 6)
            ]
        }
        self.warna_kendaraan = {
            "f1": "#dc143c"
        }
        self.jenis_aktif = "f1"

    def ganti_kendaraan_acak(self):
        # PERBAIKAN: Dikunci hanya untuk F1 saja sesuai permintaan
        self.jenis_aktif = "f1"

    @staticmethod
    def _rotasi_translate(points, origin, target):
        ox, oy = origin
        theta = math.atan2(target[1] - oy, target[0] - ox)
        cos_t, sin_t = math.pi, math.sin(theta)  # Menjaga kompatibilitas math
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        hasil = []
        for x, y in points:
            x_rot = x * cos_t - y * sin_t
            y_rot = x * sin_t + y * cos_t
            hasil.append((ox + x_rot, oy + y_rot))
        return hasil

    # Menghitung posisi kendaraan pada koordinat world
    # setelah dilakukan rotasi sesuai arah gerak kendaraan.
    def hitung_koordinat_world(self, p_sekarang, p_target):
        return self._rotasi_translate(self.bentuk_kendaraan[self.jenis_aktif], p_sekarang, p_target)

    def hitung_detail_kendaraan_world(self, p_sekarang, p_target):
        """Detail visual tambahan untuk F1 (Ukuran diselaraskan dengan bodi utama)."""
        if self.jenis_aktif != "f1":
            return []

        # Detailing berskala pas untuk bodi F1 yang baru
        stripe_kuning = [(36, -2), (16, -3), (-22, -3), (-30, 0), (-22, 3), (16, 3), (36, 2)]
        cockpit = [(-4, -5), (10, -5), (15, 0), (10, 5), (-4, 5), (-8, 0)]
        rear_wing = [(-46, -16), (-34, -16), (-34, 16), (-46, 16)]
        front_wing = [(30, -11), (43, -9), (43, 9), (30, 11)]

        return [
            {"points": self._rotasi_translate(rear_wing, p_sekarang, p_target), "fill": "#102a43", "outline": "#0b1620", "width": 1},
            {"points": self._rotasi_translate(front_wing, p_sekarang, p_target), "fill": "#102a43", "outline": "#0b1620", "width": 1},
            {"points": self._rotasi_translate(stripe_kuning, p_sekarang, p_target), "fill": "#f1c40f", "outline": "", "width": 1},
            {"points": self._rotasi_translate(cockpit, p_sekarang, p_target), "fill": "#17202a", "outline": "#ecf0f1", "width": 1},
        ]
