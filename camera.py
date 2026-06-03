# ============================================================
# CAMERA / TRANSFORMASI KOORDINAT
# Penanggung Jawab: Adib
# Deskripsi:
# Mengatur transformasi koordinat world ke screen dan screen ke world,
# fitur zoom in/out, panning, scaling ukuran objek, dan pembatasan
# kamera agar tidak keluar dari area peta.
# ============================================================

# Class kamera yang menangani zoom, pan, dan konversi koordinat
# antara world coordinate dan screen coordinate.
class Camera:
    def __init__(self, canvas, app, world_width, world_height):
        self.canvas, self.app = canvas, app
        self.world_width, self.world_height = world_width, world_height
        self.zoom_level, self.min_zoom, self.max_zoom = 1.0, 0.32, 2.8
        self.offset_x, self.offset_y = 0.0, 0.0
        self._pan_start_screen = self._pan_start_offset = (0, 0)
        
        self.canvas.bind("<MouseWheel>", self.zoom_wheel)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.after(60, self.reset_camera)

    # Mengubah koordinat dunia/peta menjadi koordinat layar.
    def world_to_screen(self, x, y): return (x - self.offset_x) * self.zoom_level, (y - self.offset_y) * self.zoom_level
    # Mengubah koordinat layar menjadi koordinat dunia/peta.
    # Digunakan saat user klik mouse pada canvas.
    def screen_to_world(self, sx, sy): return sx / self.zoom_level + self.offset_x, sy / self.zoom_level + self.offset_y
    def daftar_world_to_screen(self, points):
        coords = []
        for x, y in points:
            sx, sy = self.world_to_screen(x, y)
            coords.extend([sx, sy])
        return coords
    def rect_world_to_screen(self, rect):
        sx1, sy1 = self.world_to_screen(rect[0], rect[1])
        sx2, sy2 = self.world_to_screen(rect[2], rect[3])
        return sx1, sy1, sx2, sy2
    def scaled(self, value, minimum=1, maximum=None):
        hasil = value * self.zoom_level
        return max(minimum, min(hasil, maximum) if maximum else hasil)
    def scaled_font(self, size, minimum=6, maximum=22): return int(max(minimum, min(maximum, size * self.zoom_level)))

    def zoom_wheel(self, event):
        factor = 1.12 if event.delta > 0 else 0.88
        wx, wy = self.screen_to_world(event.x, event.y)
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level * factor))
        self.offset_x, self.offset_y = wx - event.x / self.zoom_level, wy - event.y / self.zoom_level
        self.clamp_camera(); self.app.render_semua()

    def start_pan(self, event):
        self._pan_start_screen, self._pan_start_offset = (event.x, event.y), (self.offset_x, self.offset_y)

    def do_pan(self, event):
        dx, dy = event.x - self._pan_start_screen[0], event.y - self._pan_start_screen[1]
        self.offset_x = self._pan_start_offset[0] - dx / self.zoom_level
        self.offset_y = self._pan_start_offset[1] - dy / self.zoom_level
        self.clamp_camera(); self.app.render_semua()

    def reset_camera(self):
        self.zoom_level = 1.0  
        vw = max(1, self.canvas.winfo_width()) / self.zoom_level
        vh = max(1, self.canvas.winfo_height()) / self.zoom_level
        self.offset_x, self.offset_y = max(0.0, (self.world_width - vw) / 2), max(0.0, (self.world_height - vh) / 2)
        self.clamp_camera(); self.app.render_semua()

    def on_resize(self, event=None): self.clamp_camera(); self.app.render_semua()

    def clamp_camera(self):
        vw, vh = max(1, self.canvas.winfo_width()) / self.zoom_level, max(1, self.canvas.winfo_height()) / self.zoom_level
        mx, my = self.world_width - vw, self.world_height - vh
        self.offset_x = min(max(0.0, self.offset_x), mx) if mx >= 0 else mx / 2
        self.offset_y = min(max(0.0, self.offset_y), my) if my >= 0 else my / 2


