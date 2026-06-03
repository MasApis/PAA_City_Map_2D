# ============================================================
# MAIN PROGRAM
# Penanggung Jawab: Vito
# Deskripsi:
# File utama untuk menjalankan aplikasi simulasi City Map 2D PAA.
# File ini memanggil AppSimulasi dan menjalankan Tkinter mainloop.
# ============================================================

import tkinter as tk

from app_simulasi import AppSimulasi


def main():
    root = tk.Tk()
    root.title("City Map 2D PAA - Smart Courier")
    root.geometry("1366x768")
    AppSimulasi(root)
    root.mainloop()


if __name__ == "__main__":
    main()

