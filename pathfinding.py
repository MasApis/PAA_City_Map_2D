# ============================================================
# PATHFINDING / ALGORITMA DIJKSTRA
# Penanggung Jawab: Rahman
# Deskripsi:
# Menentukan titik start dan finish pada jalan, mencari jalan terdekat,
# membuat virtual node, dan menjalankan algoritma Dijkstra untuk
# menemukan rute terpendek berdasarkan bobot edge.
# ============================================================

import random
import math
import heapq
import time

# Class yang menangani pemilihan titik pada jalan,
# pencarian rute terpendek, dan implementasi algoritma Dijkstra.
class Pathfinding:
    @staticmethod
    def jarak(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

    @staticmethod
    def proyeksi_titik_ke_segmen(point, a, b):
        px, py = point
        ax, ay = a
        bx, by = b
        vx, vy = bx - ax, by - ay
        panjang2 = vx * vx + vy * vy
        if panjang2 <= 0.0001: return a, 0.0
        t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / panjang2))
        return (ax + vx * t, ay + vy * t), t

    def buat_pick_dari_edge(self, nodes, edge, t):
        a, b, _ = edge
        pa, pb = nodes[a], nodes[b]
        return {"point": (pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t), "edge": (a, b), "t": t, "edge_key": (min(a, b), max(a, b))}

    def cari_jalan_terdekat(self, nodes, edges, mouse_x_world, mouse_y_world):
        if not nodes: return None
        target = (mouse_x_world, mouse_y_world)
        best, best_dist = None, float("inf")
        for edge in edges:
            proyeksi, t = self.proyeksi_titik_ke_segmen(target, nodes[edge[0]], nodes[edge[1]])
            dist = self.jarak(target, proyeksi)
            if dist < best_dist:
                best_dist, best = dist, self.buat_pick_dari_edge(nodes, edge, t)
        return best

    # Implementasi algoritma Dijkstra.
    # graph_adj berisi adjacency list dengan format:
    # node: [(tetangga, bobot), ...]
    # Fungsi ini mengembalikan urutan node sebagai rute terpendek.
    def dijkstra(self, graph_adj, start, finish):
        if start == finish: return [start]
        jarak, asal, heap, visited = {start: 0.0}, {}, [(0.0, start)], set()
        while heap:
            dist_now, node = heapq.heappop(heap)
            if node in visited: continue
            visited.add(node)
            if node == finish: break
            for tetangga, bobot in graph_adj.get(node, []):
                if tetangga in visited: continue
                dist_baru = dist_now + bobot
                if dist_baru < jarak.get(tetangga, float("inf")):
                    jarak[tetangga], asal[tetangga] = dist_baru, node
                    heapq.heappush(heap, (dist_baru, tetangga))
        if finish not in jarak: return []
        path = [finish]
        while path[-1] != start: path.append(asal[path[-1]])
        path.reverse()
        return path

    def _hubungkan_pick_virtual(self, nodes, temp_adj, pick, virtual_idx):
        if not pick: return
        a, b = pick["edge"]
        da, db = self.jarak(pick["point"], nodes[a]), self.jarak(pick["point"], nodes[b])
        for k in (virtual_idx, a, b): temp_adj.setdefault(k, [])
        temp_adj[virtual_idx].extend([(a, da), (b, db)])
        temp_adj[a].append((virtual_idx, da))
        temp_adj[b].append((virtual_idx, db))

    # Membuat node virtual untuk titik start dan finish
    # karena user bisa memilih titik di tengah ruas jalan,
    # bukan selalu tepat pada node graph asli.
    def route_virtual(self, nodes, graph_adj, start_pick, finish_pick, tampilkan_analisis=False):
        if not nodes or not start_pick or not finish_pick: return [], [], 0.0
        start_virt, finish_virt = len(nodes), len(nodes) + 1
        temp_nodes = nodes + [start_pick["point"], finish_pick["point"]]
        temp_adj = {n: list(t) for n, t in graph_adj.items()}
        self._hubungkan_pick_virtual(nodes, temp_adj, start_pick, start_virt)
        self._hubungkan_pick_virtual(nodes, temp_adj, finish_pick, finish_virt)
        
        if start_pick["edge_key"] == finish_pick["edge_key"]:
            direct = self.jarak(start_pick["point"], finish_pick["point"])
            temp_adj[start_virt].append((finish_virt, direct))
            temp_adj[finish_virt].append((start_virt, direct))

        # Analisis kompleksitas harus memakai temp_adj, bukan graph_adj asli.
        # temp_adj sudah berisi virtual node start dan finish, sehingga
        # proses Dijkstra yang diukur sama dengan proses pencarian rute asli.
        if tampilkan_analisis:
            hasil_analisis = self.analisis_kompleksitas_dijkstra(temp_adj, start_virt, finish_virt)
            self.tampilkan_hasil_analisis(hasil_analisis)
            self.analisis_terakhir = hasil_analisis
            
        path = self.dijkstra(temp_adj, start_virt, finish_virt)
        if len(path) < 2: return [], [], 0.0
        route_points = [temp_nodes[idx] for idx in path]
        return path, route_points, sum(self.jarak(route_points[i-1], route_points[i]) for i in range(1, len(route_points)))

    def tampilkan_hasil_analisis(self, hasil_analisis):
        print("=== ANALISIS KOMPLEKSITAS DIJKSTRA ===")
        print(f"Jumlah Node (V): {hasil_analisis['jumlah_node']}")
        print(f"Jumlah Edge (E): {hasil_analisis['jumlah_edge']}")
        print(f"Node Dikunjungi: {hasil_analisis['node_dikunjungi']}")
        print(f"Operasi Pop Heap: {hasil_analisis['operasi_pop_heap']}")
        print(f"Operasi Push Heap: {hasil_analisis['operasi_push_heap']}")
        print(f"Operasi Relaksasi Edge: {hasil_analisis['operasi_relaksasi']}")
        print(f"Waktu Eksekusi: {hasil_analisis['waktu_eksekusi']:.8f} detik")
        print(f"Kompleksitas Waktu: {hasil_analisis['kompleksitas_waktu']}")
        print(f"Kompleksitas Ruang: {hasil_analisis['kompleksitas_ruang']}")

    def random_placement_jalan(self, nodes, edges, graph_adj, min_panjang=700, percobaan=150):
        if not nodes or not edges: return None, None, [], [], 0.0
        best, best_len = None, -1.0
        for _ in range(percobaan):
            sp = self.buat_pick_dari_edge(nodes, random.choice(edges), random.uniform(0.1, 0.9))
            fp = self.buat_pick_dari_edge(nodes, random.choice(edges), random.uniform(0.1, 0.9))
            if self.jarak(sp["point"], fp["point"]) < 300: continue
            path, rp, total = self.route_virtual(nodes, graph_adj, sp, fp)
            if len(path) > 1 and total > best_len:
                best, best_len = (sp, fp, path, rp, total), total
            if best_len >= min_panjang: return best
        return best if best else (None, None, [], [], 0.0)
    
    def analisis_kompleksitas_dijkstra(self, graph_adj, start, finish):
        waktu_mulai = time.perf_counter()

        jumlah_node = len(graph_adj)
        jumlah_edge = sum(len(tetangga) for tetangga in graph_adj.values()) // 2

        operasi_pop_heap = 0
        operasi_push_heap = 0
        operasi_relaksasi = 0
        node_dikunjungi = 0

        if start == finish:
            return {
                "jumlah_node": jumlah_node,
                "jumlah_edge": jumlah_edge,
                "node_dikunjungi": 1,
                "operasi_pop_heap": 0,
                "operasi_push_heap": 0,
                "operasi_relaksasi": 0,
                "waktu_eksekusi": 0,
                "kompleksitas_waktu": "O((V + E) log V)",
                "kompleksitas_ruang": "O(V + E)"
            }

        jarak = {start: 0.0}
        asal = {}
        heap = [(0.0, start)]
        visited = set()

        while heap:
            dist_now, node = heapq.heappop(heap)
            operasi_pop_heap += 1

            if node in visited:
                continue

            visited.add(node)
            node_dikunjungi += 1

            if node == finish:
                break

            for tetangga, bobot in graph_adj.get(node, []):
                operasi_relaksasi += 1

                if tetangga in visited:
                    continue

                dist_baru = dist_now + bobot

                if dist_baru < jarak.get(tetangga, float("inf")):
                    jarak[tetangga] = dist_baru
                    asal[tetangga] = node
                    heapq.heappush(heap, (dist_baru, tetangga))
                    operasi_push_heap += 1

        waktu_selesai = time.perf_counter()

        return {
            "jumlah_node": jumlah_node,
            "jumlah_edge": jumlah_edge,
            "node_dikunjungi": node_dikunjungi,
            "operasi_pop_heap": operasi_pop_heap,
            "operasi_push_heap": operasi_push_heap,
            "operasi_relaksasi": operasi_relaksasi,
            "waktu_eksekusi": waktu_selesai - waktu_mulai,
            "kompleksitas_waktu": "O((V + E) log V)",
            "kompleksitas_ruang": "O(V + E)"
        }
