#!/usr/bin/env python3
"""
Simulador de Gestor de Procesos
Interfaz principal de la aplicación
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.menu import App
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
