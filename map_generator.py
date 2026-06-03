# ============================================================
# MAP GENERATOR & GRAPH BUILDER
# Penanggung Jawab: Rahman
# Deskripsi:
# Membuat peta jalan secara prosedural, membentuk node dan edge,
# serta menentukan bobot antar-node berdasarkan jarak antar titik.
# Modul ini menjadi sumber data graph untuk algoritma Dijkstra.
# ============================================================

import random
import math

# Class untuk membangun peta, jalan, bangunan, node graph,
# adjacency list, dan edge berbobot.
class MapGenerator:
    def __init__(self):
        self.world_width = 3800
        self.world_height = 3400

        # Sistem Tema Peta
        self.daftar_tema = ["Pusat Kota"]
        self.tema_aktif = "Pusat Kota"

        self.GRID_ROWS = 4
        self.GRID_COLS = 4

        self.ruas_jalan = []
        self.objek_kota = []
        self.titik_simpang = []

        self.graph_nodes = []
        self.graph_adj = {}
        self.graph_edges = []

    def bezier_kubik(self, p0, p1, p2, p3, res=60):
        titik = []
        for i in range(res + 1):
            t = i / res
            u = 1 - t
            x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
            y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
            titik.append((x, y))
        return titik

    @staticmethod
    def _jarak(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _node_key(self, point):
        return (round(point[0], 1), round(point[1], 1))

    # Fungsi ini mengubah ruas jalan menjadi graph.
    # Setiap titik jalan menjadi node, dan hubungan antar titik menjadi edge.
    # Bobot edge dihitung dari jarak Euclidean antar-node.
    def _bangun_graf_jalan(self):
        self.graph_nodes = []
        self.graph_adj = {}
        self.graph_edges = []
        node_lookup = {}
        edge_seen = set()

        def add_node(point):
            key = self._node_key(point)
            if key not in node_lookup:
                idx = len(self.graph_nodes)
                node_lookup[key] = idx
                self.graph_nodes.append(point)
                self.graph_adj[idx] = []
            return node_lookup[key]

        def add_edge(a, b):
            if a == b: return
            edge_key = (min(a, b), max(a, b))
            if edge_key in edge_seen: return
            pa = self.graph_nodes[a]
            pb = self.graph_nodes[b]
            # Bobot edge ditentukan dari jarak antara node A dan node B.
            w = self._jarak(pa, pb)
            if w <= 0.1: return
            edge_seen.add(edge_key)
            self.graph_adj[a].append((b, w))
            self.graph_adj[b].append((a, w))
            self.graph_edges.append((a, b, w))

        for ruas in self.ruas_jalan:
            previous_idx = None
            for point in ruas["titik"]:
                idx = add_node(point)
                if previous_idx is not None:
                    add_edge(previous_idx, idx)
                previous_idx = idx

    def _bangun_objek_kota(self, cell_w, cell_h):
        """Generator bangunan random organik, tidak lagi mengikuti grid cell."""
        _ = (cell_w, cell_h)
        objek = []

        # ===== A. Elemen dasar lingkungan =====
        if self.tema_aktif == "Pesisir Pantai":
            objek.append({
                "jenis": "area",
                "rect": (0, self.world_height - 500, self.world_width, self.world_height + 500),
                "fill": "#1f618d",
                "nama": "Samudra"
            })
        elif self.tema_aktif == "Pusat Kota":
            mid_x, mid_y = self.world_width / 2, self.world_height / 2
            objek.append({
                "jenis": "lingkaran",
                "center": (mid_x, mid_y),
                "radius": 320,
                "fill": "#27ae60",
                "nama": "Taman Kota Sentral"
            })

        # ===== B. Konfigurasi bangunan berdasarkan tema =====
        if self.tema_aktif == "Pusat Kota":
            target_bangunan = random.randint(35, 45) # Dikurangi sedikit agar tidak terlalu padat overload
            ukuran_min, ukuran_max = 90, 160 # Ukuran dikecilkan agar muat di sela-sela kurva jalan
            warna_pool = ["#e74c3c", "#3498db", "#f1c40f", "#9b59b6", "#e67e22", "#1abc9c", "#95a5a6"]
        elif self.tema_aktif == "Kompleks Perumahan":
            target_bangunan = random.randint(55, 78)
            ukuran_min, ukuran_max = 60, 125
            warna_pool = ["#e67e22", "#3498db", "#9b59b6", "#16a085", "#f1c40f"]
        else:
            target_bangunan = random.randint(28, 42)
            ukuran_min, ukuran_max = 115, 195
            warna_pool = ["#f1c40f", "#ecf0f1", "#e74c3c", "#f5cba7"]

        pool_nama_bangunan = [
            "SEKOLAH", "RUMAH SAKIT", "POLISI", "PEMADAM", "BANK", 
            "HOTEL", "SUPERMARKET", "KANTOR POS", "KAMPUS", "MUSEUM",
            "APOTEK", "CAFE", "RESTORAN", "STASIUN", "PERPUSTAKAAN"
        ]
        random.shuffle(pool_nama_bangunan)
        indeks_nama = 0

        def rect_overlap(a, b, margin=0):
            ax1, ay1, ax2, ay2 = a
            bx1, by1, bx2, by2 = b
            return not (
                ax2 + margin < bx1 or ax1 - margin > bx2 or
                ay2 + margin < by1 or ay1 - margin > by2
            )

        def jarak_titik_ke_segmen(point, a, b):
            px, py = point
            ax, ay = a
            bx, by = b
            vx, vy = bx - ax, by - ay
            panjang2 = vx * vx + vy * vy
            if panjang2 <= 0.0001:
                return math.hypot(px - ax, py - ay)
            t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / panjang2))
            proj_x = ax + vx * t
            proj_y = ay + vy * t
            return math.hypot(px - proj_x, py - proj_y)

        def terlalu_dekat_jalan(rect):
            """Hindari bangunan menutup jalan utama/rute."""
            x1, y1, x2, y2 = rect
            center = ((x1 + x2) / 2, (y1 + y2) / 2)
            # radius bangunan + separuh lebar jalan + ruang napas
            radius = math.hypot(x2 - x1, y2 - y1) / 2 + 45
            for ruas in self.ruas_jalan:
                titik = ruas["titik"]
                for i in range(0, len(titik) - 1, 4):
                    if jarak_titik_ke_segmen(center, titik[i], titik[i + 1]) < radius:
                        return True
            return False

        def berada_di_area_terlarang(px, py, w=0, h=0):
            mid_x, mid_y = self.world_width / 2, self.world_height / 2
            jarak_ke_pusat = math.hypot(px - mid_x, py - mid_y)
            
            # Hitung jarak dari titik tengah bangunan ke ujung sudut kotaknya
            radius_bangunan = math.hypot(w / 2, h / 2)
            
            if self.tema_aktif == "Pusat Kota":
                # Batas Dalam: Jangan menembus bundaran tengah kota
                if jarak_ke_pusat - radius_bangunan < 390:
                    return True
                
                # Batas Luar: Seluruh badan bangunan harus berada di dalam sirkuit jalan (1250px)
                if jarak_ke_pusat + radius_bangunan > 1250:
                    return True
                    
            if self.tema_aktif == "Pesisir Pantai" and py > self.world_height - 950:
                return True
            return False

        jumlah_bangunan = 0
        percobaan = 0
        max_percobaan = target_bangunan * 100

        while jumlah_bangunan < target_bangunan and percobaan < max_percobaan:
            percobaan += 1
            w = random.uniform(ukuran_min, ukuran_max)
            h = random.uniform(ukuran_min, ukuran_max)

            mid_x, mid_y = self.world_width / 2, self.world_height / 2
            px = random.uniform(mid_x - 1300, mid_x + 1300)
            py = random.uniform(mid_y - 1300, mid_y + 1300)

            if berada_di_area_terlarang(px, py, w, h):
                continue

            kandidat = (px - w / 2, py - h / 2, px + w / 2, py + h / 2)

            if terlalu_dekat_jalan(kandidat):
                continue

            # Margin dinaikkan agar benar-benar terpisah dan rapi
            if any(o["jenis"] == "bangunan" and rect_overlap(kandidat, o["rect"], margin=50) for o in objek):
                continue

            nama_bgt = ""
            if indeks_nama < len(pool_nama_bangunan):
                nama_bgt = pool_nama_bangunan[indeks_nama]
                indeks_nama += 1
            else:
                nama_bgt = f"BLOK {chr(65 + (jumlah_bangunan % 6))}{jumlah_bangunan // 6 + 1}"

            objek.append({
                "jenis": "bangunan",
                "rect": kandidat,
                "fill": random.choice(warna_pool),
                "nama": nama_bgt
            })
            jumlah_bangunan += 1

        return objek
    
    def bangun_peta(self, mode_acak=False):
        self.ruas_jalan = []

        # Konfigurasi grid berdasarkan tema
        if self.tema_aktif == "Pusat Kota":
            self.GRID_ROWS, self.GRID_COLS = 5, 5
        elif self.tema_aktif == "Kompleks Perumahan":
            self.GRID_ROWS, self.GRID_COLS = 4, 4
        else:  # Pesisir Pantai
            self.GRID_ROWS, self.GRID_COLS = 4, 5

        cell_w = self.world_width  / (self.GRID_COLS + 1)
        cell_h = self.world_height / (self.GRID_ROWS + 1)

        # --- STEP 1: Tempatkan node grid dengan jitter KECIL ---
        NODE_JITTER = 0.10  
        nodes_grid = {}
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                base_x = (c + 1) * cell_w
                base_y = (r + 1) * cell_h
                if mode_acak:
                    cx = base_x + random.uniform(-cell_w * NODE_JITTER, cell_w * NODE_JITTER)
                    cy = base_y + random.uniform(-cell_h * NODE_JITTER, cell_h * NODE_JITTER)
                else:
                    cx, cy = base_x, base_y
                nodes_grid[(r, c)] = (cx, cy)

        # --- STEP 1B: INJEKSI BUNDARAN DI TENGAH ---
        mid_x, mid_y = self.world_width / 2, self.world_height / 2
        radius_bundaran = 350
        jumlah_node_bundaran = 8
        nodes_bundaran = []

        for i in range(jumlah_node_bundaran):
            theta = (i / jumlah_node_bundaran) * 2 * math.pi
            bx = mid_x + radius_bundaran * math.cos(theta)
            by = mid_y + radius_bundaran * math.sin(theta)
            nodes_bundaran.append((bx, by))

        id_jalan = 1
        KURVA_KUAT = 0.28   

        # --- STEP 2: Bangun jalan H, V, dan Diagonal ---
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                p0 = nodes_grid[(r, c)]

                # Ambil 4 node grid tengah yang mengurung pusat kota
                # untuk nanti dialihkan ke node bundaran terdekat
                is_node_tengah = (1 <= r <= 3) and (1 <= c <= 3)

                # -- Jalan Horizontal --
                if c < self.GRID_COLS - 1:
                    p3 = nodes_grid[(r, c + 1)]
                    
                    if r == 2 and c == 1: p3 = nodes_bundaran[4]
                    elif r == 2 and c == 2: p0 = nodes_bundaran[0]

                    dx, dy = p3[0] - p0[0], p3[1] - p0[1]
                    panjang = math.hypot(dx, dy) or 1
                    nx, ny = -dy / panjang, dx / panjang  
                    
                    amp = random.uniform(-KURVA_KUAT, KURVA_KUAT) * panjang if mode_acak else KURVA_KUAT * 0.5 * panjang * (1 if (r + c) % 2 == 0 else -1)
                    if (r == 2 and c == 1) or (r == 2 and c == 2): amp = 0
                    
                    cp1 = (p0[0] + dx * 0.33 + nx * amp, p0[1] + dy * 0.33 + ny * amp)
                    cp2 = (p0[0] + dx * 0.67 + nx * amp, p0[1] + dy * 0.67 + ny * amp)
                    self.ruas_jalan.append({
                        "nama": f"Jalan H-{id_jalan}",
                        "utama": r % 2 == 0,
                        "titik": self.bezier_kubik(p0, cp1, cp2, p3)
                    })
                    id_jalan += 1

                # -- Jalan Vertikal --
                if r < self.GRID_ROWS - 1:
                    p3 = nodes_grid[(r + 1, c)]
                    
                    if c == 2 and r == 1: p3 = nodes_bundaran[6]
                    elif c == 2 and r == 2: p0 = nodes_bundaran[2]

                    dx, dy = p3[0] - p0[0], p3[1] - p0[1]
                    panjang = math.hypot(dx, dy) or 1
                    nx, ny = -dy / panjang, dx / panjang
                    
                    amp = random.uniform(-KURVA_KUAT, KURVA_KUAT) * panjang if mode_acak else KURVA_KUAT * 0.5 * panjang * (1 if (r + c) % 2 == 0 else -1)
                    if (c == 2 and r == 1) or (c == 2 and r == 2): amp = 0

                    cp1 = (p0[0] + dx * 0.33 + nx * amp, p0[1] + dy * 0.33 + ny * amp)
                    cp2 = (p0[0] + dx * 0.67 + nx * amp, p0[1] + dy * 0.67 + ny * amp)
                    self.ruas_jalan.append({
                        "nama": f"Jalan V-{id_jalan}",
                        "utama": False,
                        "titik": self.bezier_kubik(p0, cp1, cp2, p3)
                    })
                    id_jalan += 1

                # -- Jalan Diagonal --
                if r < self.GRID_ROWS - 1 and c < self.GRID_COLS - 1:
                    if is_node_tengah: continue 
                    if random.random() < 0.35:
                        p3 = nodes_grid[(r + 1, c + 1)]
                        dx, dy = p3[0] - p0[0], p3[1] - p0[1]
                        panjang = math.hypot(dx, dy) or 1
                        nx, ny = -dy / panjang, dx / panjang
                        amp = random.uniform(-KURVA_KUAT * 0.5, KURVA_KUAT * 0.5) * panjang if mode_acak else 0
                        cp1 = (p0[0] + dx * 0.33 + nx * amp, p0[1] + dy * 0.33 + ny * amp)
                        cp2 = (p0[0] + dx * 0.67 + nx * amp, p0[1] + dy * 0.67 + ny * amp)
                        self.ruas_jalan.append({
                            "nama": f"Jalan D-{id_jalan}",
                            "utama": False,
                            "titik": self.bezier_kubik(p0, cp1, cp2, p3)
                        })
                        id_jalan += 1

        # --- STEP 2B: HUBUNGKAN JALAN LINGKAR BUNDARAN ---
        for i in range(jumlah_node_bundaran):
            p0 = nodes_bundaran[i]
            p3 = nodes_bundaran[(i + 1) % jumlah_node_bundaran] 
            
            dx, dy = p3[0] - p0[0], p3[1] - p0[1]
            panjang = math.hypot(dx, dy) or 1
            vx, vy = (p0[0] + p3[0])/2 - mid_x, (p0[1] + p3[1])/2 - mid_y
            v_len = math.hypot(vx, vy) or 1
            nx, ny = vx / v_len, vy / v_len
            
            amp = panjang * 0.15 
            cp1 = (p0[0] + dx * 0.33 + nx * amp, p0[1] + dy * 0.33 + ny * amp)
            cp2 = (p0[0] + dx * 0.67 + nx * amp, p0[1] + dy * 0.67 + ny * amp)
            
            self.ruas_jalan.append({
                "nama": f"Bundaran-{i+1}",
                "utama": True,
                "titik": self.bezier_kubik(p0, cp1, cp2, p3)
            })

        semua_nodes = list(nodes_grid.values()) + nodes_bundaran
        self.titik_simpang = semua_nodes

        self.objek_kota = self._bangun_objek_kota(cell_w, cell_h)
        self._bangun_graf_jalan()
        return self.graph_nodes
