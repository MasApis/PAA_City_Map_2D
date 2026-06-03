# ============================================================
# APP SIMULASI / INTEGRATOR PROGRAM
# Penanggung Jawab: Vito
# Deskripsi:
# Mengintegrasikan seluruh komponen program, seperti generator peta,
# algoritma pencarian rute, kamera, kendaraan, UI, tombol kontrol,
# rendering canvas, serta animasi simulasi.
# ============================================================

import tkinter as tk
import math

from map_generator import MapGenerator
from vehicle import Vehicle
from pathfinding import Pathfinding
from camera import Camera

# Class utama aplikasi yang mengatur UI, event mouse, tombol,
# proses render peta, perhitungan rute, dan animasi kendaraan.
class AppSimulasi:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#1a252f")

        self.canvas = tk.Canvas(root, width=1366, height=768, bg="#2c3e50", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.map_generator = MapGenerator()
        self.vehicle = Vehicle()
        self.pathfinding = Pathfinding()
        self.camera = Camera(self.canvas, self, self.map_generator.world_width, self.map_generator.world_height)

        self.canvas.bind("<ButtonPress-1>", self.on_press_kiri)
        self.canvas.bind("<B1-Motion>", self.on_drag_kiri)
        self.canvas.bind("<ButtonRelease-1>", self.on_release_kiri)
        self.canvas.bind("<ButtonPress-3>", self.on_press_kanan)
        self.canvas.bind("<B3-Motion>", self.on_drag_kanan)
        self.canvas.bind("<ButtonRelease-3>", self.on_release_kanan)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.pan_start_x = self.pan_start_y = 0
        self.is_panning = False

        self.start_pick = self.finish_pick = self.hover_snap = None
        self.show_route, self.show_nodes = True, False
        self.route_node_path, self.route_points, self.route_cumulative = [], [], []
        self.route_total_length = self.mobil_distance = 0.0
        self.mobil_speed = 9.0  
        self.is_running, self.animasi_id = False, None
        self.rute_mode_on = True 
        self.custom_waypoints = []

        self.panel_bawah = tk.Frame(root, bg="#1a252f", pady=10)
        self.panel_bawah.pack(fill="x", side="bottom")
        self.btn_rute_toggle = tk.Button(self.panel_bawah, text="🌐 RUTE: ON", command=self.toggle_mode_rute, bg="#1abc9c", fg="white", font=("Arial", 10, "bold"), width=12)
        self.btn_rute_toggle.pack(side="left", padx=5)

        self.lbl_status = tk.Label(self.panel_bawah, text="STATUS: STOP", font=("Courier", 12, "bold"), fg="#e74c3c", bg="#1a252f", width=20)
        self.lbl_status.pack(side="left", padx=10)

        self.btn_play = tk.Button(self.panel_bawah, text="▶ PLAY", command=self.toggle_play, bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), width=10)
        self.btn_play.pack(side="left", padx=5)

        tk.Button(self.panel_bawah, text="🎲 ACAK TATA KOTA", command=lambda: self.update_view(True), bg="#f39c12", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(self.panel_bawah, text="🎯 ACAK POSISI & OBJEK", command=self.acak_posisi, bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(self.panel_bawah, text="⤢ RESET KAMERA", command=self.camera.reset_camera, bg="#7f8c8d", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        tk.Label(self.panel_bawah, text="Klik Kiri/Kanan: Rute | Drag: Scroll", bg="#1a252f", fg="#bdc3c7", font=("Arial", 9)).pack(side="right", padx=10)
    
        self.update_view(True) 

    def pause_animasi(self, status="STATUS: PAUSE", warna="#f1c40f"):
        self.is_running = False
        if self.animasi_id: self.root.after_cancel(self.animasi_id); self.animasi_id = None
        self.btn_play.config(text="▶ PLAY", bg="#2ecc71")
        self.lbl_status.config(text=status, fg=warna)
    
    def toggle_mode_rute(self):
     self.rute_mode_on = not self.rute_mode_on
     self.start_pick = self.finish_pick = None
     self.custom_waypoints = []
     self.route_points = []
     self.route_total_length = 0.0
     if self.rute_mode_on:
         self.btn_rute_toggle.config(text="🌐 RUTE: ON", bg="#1abc9c")
     else:
         self.btn_rute_toggle.config(text="🔒 RUTE: OFF", bg="#e74c3c")
     self.render_semua()
    
    def haluskan_sudut_rute(self, points, interval=45, smoothing_passes=4):
        if len(points) < 3: 
            return points

        resampled = [points[0]]
        current_dist = 0.0
        
        for i in range(1, len(points)):
            p0 = points[i-1]
            p1 = points[i]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            dist = math.hypot(dx, dy)
            
            if dist < 0.001: 
                continue
            
            while current_dist + dist >= interval:
                sisa = interval - current_dist
                t = sisa / dist
                qx = p0[0] + dx * t
                qy = p0[1] + dy * t
                resampled.append((qx, qy))
                
                p0 = (qx, qy)
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]
                dist = math.hypot(dx, dy)
                current_dist = 0.0
                
            current_dist += dist
            
        resampled.append(points[-1])
        
        for _ in range(smoothing_passes):
            smoothed = [resampled[0]]
            for i in range(len(resampled) - 1):
                p0 = resampled[i]
                p1 = resampled[i+1]
                smoothed.append((0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1]))
                smoothed.append((0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1]))
            smoothed.append(resampled[-1])
            resampled = smoothed
            
        return resampled

    def hitung_route(self, reset_mobil=True):
        if self.rute_mode_on:
            if not self.start_pick or not self.finish_pick: return False
            self.route_node_path, self.route_points, self.route_total_length = self.pathfinding.route_virtual(
                self.map_generator.graph_nodes,
                self.map_generator.graph_adj,
                self.start_pick,
                self.finish_pick,
                tampilkan_analisis=True
            )
        else:
            if not self.start_pick or not self.finish_pick or len(self.custom_waypoints) < 2: return False
            
            gabungan_points = []
            total_node_path = []
            total_length = 0.0
            
            for i in range(len(self.custom_waypoints) - 1):
                pt_awal = self.custom_waypoints[i]
                pt_tujuan = self.custom_waypoints[i+1]
                
                path, pts, length = self.pathfinding.route_virtual(
                    self.map_generator.graph_nodes, self.map_generator.graph_adj, pt_awal, pt_tujuan
                )
                if len(pts) < 2: return False
                
                if i > 0 and len(gabungan_points) > 0:
                    gabungan_points.extend(pts[1:])
                else:
                    gabungan_points.extend(pts)
                total_node_path.extend(path)
                total_length += length
                
            self.route_points = gabungan_points
            self.route_node_path = total_node_path
            self.route_total_length = total_length

        if len(self.route_points) < 2: return False

        self.route_points = self.haluskan_sudut_rute(self.route_points, interval=45, smoothing_passes=4)

        self.route_cumulative = [0.0]
        for i in range(1, len(self.route_points)):
            self.route_cumulative.append(self.route_cumulative[-1] + self.pathfinding.jarak(self.route_points[i-1], self.route_points[i]))
        if reset_mobil: self.mobil_distance = 0.0
        return True

    def posisi_mobil_saat_ini(self):
        if not self.route_points: return (0, 0), (1, 0)
        d = max(0.0, min(self.mobil_distance, self.route_total_length))
        for i in range(1, len(self.route_cumulative)):
            if self.route_cumulative[i] >= d:
                t = (d - self.route_cumulative[i-1]) / max(self.route_cumulative[i] - self.route_cumulative[i-1], 0.0001)
                p0, p1 = self.route_points[i-1], self.route_points[i]
                return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t), p1
        return self.route_points[-1], self.route_points[-1]

    def on_press_kiri(self, event): self.camera.start_pan(event); self.pan_start_x, self.pan_start_y, self.is_panning = event.x, event.y, False
    def on_drag_kiri(self, event):
        if abs(event.x - self.pan_start_x) > 5 or abs(event.y - self.pan_start_y) > 5: self.is_panning = True; self.camera.do_pan(event)
    def on_release_kiri(self, event):
        if not self.is_panning and self.map_generator.graph_nodes:
            snap = self.pathfinding.cari_jalan_terdekat(self.map_generator.graph_nodes, self.map_generator.graph_edges, *self.camera.screen_to_world(event.x, event.y))
            if snap:
                if self.rute_mode_on:
                    self.start_pick = snap
                else:
                    if not self.start_pick:
                        self.start_pick = snap
                        self.custom_waypoints = [snap]
                    else:
                        if not self.finish_pick:
                            self.custom_waypoints.append(snap)
                self.hitung_route()
                self.render_semua()

    def on_press_kanan(self, event): self.camera.start_pan(event); self.pan_start_x, self.pan_start_y, self.is_panning = event.x, event.y, False
    def on_drag_kanan(self, event):
        if abs(event.x - self.pan_start_x) > 5 or abs(event.y - self.pan_start_y) > 5: self.is_panning = True; self.camera.do_pan(event)
    def on_release_kanan(self, event):
        if not self.is_panning and self.map_generator.graph_nodes:
            snap = self.pathfinding.cari_jalan_terdekat(self.map_generator.graph_nodes, self.map_generator.graph_edges, *self.camera.screen_to_world(event.x, event.y))
            if snap:
                self.finish_pick = snap
                if not self.rute_mode_on:
                    if len(self.custom_waypoints) > 0:
                        if len(self.custom_waypoints) == 1:
                            self.custom_waypoints.append(snap)
                        else:
                            self.custom_waypoints[-1] = snap
                self.hitung_route()
                self.render_semua()

    def on_mouse_move(self, event):
        if self.is_running or self.is_panning or not self.map_generator.graph_edges: return
        snap = self.pathfinding.cari_jalan_terdekat(self.map_generator.graph_nodes, self.map_generator.graph_edges, *self.camera.screen_to_world(event.x, event.y))
        if snap and (not self.hover_snap or self.pathfinding.jarak(self.hover_snap["point"], snap["point"]) > 10):
            self.hover_snap = snap; self.render_semua()

    def toggle_play(self):
        if self.is_running: self.pause_animasi()
        elif len(self.route_points) >= 2:
            if self.mobil_distance >= self.route_total_length: self.mobil_distance = 0.0
            self.is_running, self.btn_play["text"], self.btn_play["bg"] = True, "⏸ PAUSE", "#e67e22"
            self.lbl_status.config(text="STATUS: JALAN", fg="#2ecc71")
            self.animasi_loop()

    def acak_posisi(self):
        if not self.map_generator.graph_nodes: return
        if self.is_running: self.pause_animasi(status="STATUS: POSISI", warna="#3498db")
        self.vehicle.ganti_kendaraan_acak()
        hasil = self.pathfinding.random_placement_jalan(self.map_generator.graph_nodes, self.map_generator.graph_edges, self.map_generator.graph_adj)
        if hasil[0]:
            self.start_pick, self.finish_pick, self.route_node_path, self.route_points, self.route_total_length = hasil
            self.hitung_route()
        self.render_semua()

    def update_view(self, acak):
        if self.is_running: self.pause_animasi(status="STATUS: STOP", warna="#e74c3c")
        if acak: self.vehicle.ganti_kendaraan_acak()
        self.map_generator.bangun_peta(mode_acak=acak)
        hasil = self.pathfinding.random_placement_jalan(self.map_generator.graph_nodes, self.map_generator.graph_edges, self.map_generator.graph_adj)
        if hasil[0]:
            self.start_pick, self.finish_pick, self.route_node_path, self.route_points, self.route_total_length = hasil
            self.hitung_route()
        self.hover_snap = None
        self.render_semua()

    def render_semua(self):
        self.canvas.delete("all")
        c, cam = self.canvas, self.camera
        
        c.create_rectangle(0, 0, max(1, c.winfo_width()), max(1, c.winfo_height()), fill="#2c3e50", outline="")
        x1, y1, x2, y2 = cam.rect_world_to_screen((0, 0, self.map_generator.world_width, self.map_generator.world_height))
        c.create_rectangle(x1, y1, x2, y2, fill="#34495e", outline="")

        for obj in self.map_generator.objek_kota:
            if obj["jenis"] == "lingkaran":
                cx, cy = obj["center"]
                r = obj["radius"]
                sx1, sy1 = cam.world_to_screen(cx - r, cy - r)
                sx2, sy2 = cam.world_to_screen(cx + r, cy + r)
                c.create_oval(sx1, sy1, sx2, sy2, fill=obj["fill"], outline="#ecf0f1", width=cam.scaled(3, 1, 5))
                c.create_text((sx1+sx2)/2, (sy1+sy2)/2, text=obj["nama"], fill="white", font=("Arial", cam.scaled_font(16), "bold"))
            
            elif obj["jenis"] == "area":
                sx1, sy1, sx2, sy2 = cam.rect_world_to_screen(obj["rect"])
                c.create_rectangle(sx1, sy1, sx2, sy2, fill=obj["fill"], outline="#ecf0f1" if obj.get("nama") else "", width=cam.scaled(2, 1, 4))
                if obj.get("nama"):
                    c.create_text((sx1+sx2)/2, (sy1+sy2)/2, text=obj["nama"], fill="white", font=("Arial", cam.scaled_font(18), "bold"))
            
            else: 
                sx1, sy1, sx2, sy2 = cam.rect_world_to_screen(obj["rect"])
                
                # Shadow bangunan
                bayangan = cam.scaled(10, 2, 12)
                c.create_rectangle(sx1 + bayangan, sy1 + bayangan, sx2 + bayangan, sy2 + bayangan, fill="#1c2833", outline="")
                
                # Kotak Bangunan Utama
                c.create_rectangle(sx1, sy1, sx2, sy2, fill=obj["fill"], outline="#2c3e50", width=cam.scaled(2, 1, 3))
                
                # Hiasan Garis Atap Dalam (Membentuk border estetik)
                offset_atap = cam.scaled(8, 2, 12)
                if (sx2 - sx1) > offset_atap * 2 and (sy2 - sy1) > offset_atap * 2:
                    c.create_rectangle(sx1 + offset_atap, sy1 + offset_atap, sx2 - offset_atap, sy2 - offset_atap, outline="#ecf0f1", width=cam.scaled(1, 1, 2))
                
                # Tampilkan Label Nama Bangunan di Tengah Kotak
                if obj.get("nama") and cam.zoom_level > 0.45:
                    cx_bgt = (sx1 + sx2) / 2
                    cy_bgt = (sy1 + sy2) / 2
                    
                    warna_font = "white"
                    if obj["fill"] in ["#f1c40f", "#95a5a6"]:
                        warna_font = "#1a252f"
                        
                    # Kalkulasi ukuran font adaptif agar muat 1 baris
                    lebar_bangunan_world = obj["rect"][2] - obj["rect"][0]
                    panjang_huruf = len(obj["nama"])
                    
                    # Rumus: Lebar kotak dibagi (jumlah karakter * rasio spasi huruf)
                    ukuran_ideal = int((lebar_bangunan_world - 10) / (panjang_huruf * 0.7))
                    ukuran_font_final = max(4, min(9, ukuran_ideal)) # Batasi min font 4, max font 9
                        
                    c.create_text(
                        cx_bgt, cy_bgt, 
                        text=obj["nama"], 
                        fill=warna_font, 
                        font=("Arial", cam.scaled_font(ukuran_font_final), "bold")
                        # Parameter 'width' sengaja dihapus agar tidak melakukan wrap ke baris baru
                    )

        for ruas in self.map_generator.ruas_jalan:
            flat_coords = cam.daftar_world_to_screen(ruas["titik"])
            c.create_line(*flat_coords, fill="#6c7a89" if ruas["utama"] else "#5d6d7e", width=cam.scaled(60, 10), capstyle="round", joinstyle="round")
            c.create_line(*flat_coords, fill="#ecf0f1", width=cam.scaled(3, 1), dash=(15, 12), capstyle="round", joinstyle="round")

        if self.show_route and len(self.route_points) >= 2:
            route_coords = cam.daftar_world_to_screen(self.route_points)
            c.create_line(*route_coords, fill="#f1c40f", width=cam.scaled(14, 4), capstyle="round", joinstyle="round")

        if self.hover_snap and not self.is_running:
            cx, cy = cam.world_to_screen(*self.hover_snap["point"])
            c.create_oval(cx-10, cy-10, cx+10, cy+10, outline="#00e5ff", width=2)

        # Marka Start & Finish
        if self.start_pick and self.finish_pick:
            # PERBAIKAN: Jarak bendera (ofsx) diperlebar, tiang dipertinggi, lingkaran diperbesar
            for p, warna, ofsx in [(self.start_pick["point"], "#2ecc71", -25), (self.finish_pick["point"], "#e74c3c", 25)]:
                px, py = cam.world_to_screen(*p)
                
                # Lingkaran tapak bawah diperbesar dari radius 8 ke 14
                c.create_oval(px-14, py-14, px+14, py+14, fill=warna, outline="white", width=cam.scaled(2, 1, 3))
                
                # Tiang bendera dipertinggi dari 30px ke 55px, dan dibuat lebih tebal
                c.create_line(px, py, px, py-55, fill="#bdc3c7", width=cam.scaled(5, 2, 7))
                
                # Poligon kain bendera diperbesar ukurannya agar mencolok
                c.create_polygon(px, py-55, px+ofsx, py-40, px, py-25, fill=warna, outline="white", width=cam.scaled(1, 0, 2))

        if self.route_points:
            p_pos, p_target = self.posisi_mobil_saat_ini()
            polygon = self.vehicle.hitung_koordinat_world(p_pos, p_target)
            screen_polygon = cam.daftar_world_to_screen(polygon)
            warna = self.vehicle.warna_kendaraan[self.vehicle.jenis_aktif]
            
            # MODIFIKASI: Outline width disesuaikan secara dinamis agar tidak ketebalan saat zoom
            c.create_polygon(*screen_polygon, fill=warna, outline="#111111", width=cam.scaled(1.5, 1, 3))

            for detail in self.vehicle.hitung_detail_kendaraan_world(p_pos, p_target):
                detail_coords = cam.daftar_world_to_screen(detail["points"])
                c.create_polygon(
                    *detail_coords,
                    fill=detail.get("fill", ""),
                    outline=detail.get("outline", ""),
                    width=cam.scaled(1, 1, 2)
                )

        teks_1 = f"Objek Aktif: {self.vehicle.jenis_aktif.upper()}"
        teks_2 = f"Zoom: {self.camera.zoom_level:.2f}x | Grid Segments: {len(self.map_generator.graph_edges)}"
        teks_3 = f"Route Nodes: {len(self.route_node_path)} | Distance: {self.route_total_length:.0f}"
        c.create_rectangle(12, 12, 450, 88, fill="#1a252f", outline="#7f8c8d")
        c.create_text(24, 29, anchor="w", text=teks_1, fill="#00e5ff", font=("Courier", 10, "bold"))
        c.create_text(24, 50, anchor="w", text=teks_2, fill="#ecf0f1", font=("Courier", 10, "bold"))
        c.create_text(24, 71, anchor="w", text=teks_3, fill="#f1c40f", font=("Courier", 10, "bold"))

    def animasi_loop(self):
        if not self.is_running or not self.route_points: return
        self.mobil_distance = min(self.mobil_distance + self.mobil_speed, self.route_total_length)
        self.render_semua()
        if self.mobil_distance >= self.route_total_length:
            self.pause_animasi(status="STATUS: ARRIVED!", warna="#f39c12")
            return
        self.animasi_id = self.root.after(20, self.animasi_loop)
