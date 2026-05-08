#!/usr/bin/env python3
"""
Simulador de Gestor de Procesos
Interfaz principal de la aplicación
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.menu import App, ConfigDialog
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    config = ConfigDialog(root)
    root.wait_window(config.dialog)
    
    if config.algoritmo and config.quantum:
        app = App(root, algoritmo=config.algoritmo, quantum=config.quantum)
        root.deiconify()
        root.mainloop()
    else:
        root.quit()
