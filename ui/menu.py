import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import sys
import os
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scheduler import Scheduler
from core.proceso import Proceso
from ipc.sincronizacion import ProductorConsumidor
from ipc.mensajes import BuzonMensajes
from ui.logger import Logger


class ConfigDialog:
    def __init__(self, parent):
        self.parent = parent
        self.algoritmo = None
        self.quantum = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuración Inicial")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Algoritmo de Planificación:", font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 5))
        
        self.algo_var = tk.StringVar(value="FCFS")
        algo_menu = ttk.OptionMenu(frame, self.algo_var, "FCFS", "FCFS", "RoundRobin",
                       command=self.on_algo_change)
        algo_menu.pack(anchor=tk.W, fill=tk.X, pady=(0, 15))
        
        ttk.Label(frame, text="Quantum (solo para Round Robin):", font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 5))
        
        self.quantum_var = tk.StringVar(value="3")
        self.quantum_entry = ttk.Entry(frame, textvariable=self.quantum_var, width=10)
        self.quantum_entry.pack(anchor=tk.W, pady=(0, 20))
        self.quantum_entry.config(state=tk.DISABLED)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Iniciar Simulador", command=self.on_init).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
    
    def on_algo_change(self, value):
        if value == "RoundRobin":
            self.quantum_entry.config(state=tk.NORMAL)
        else:
            self.quantum_entry.config(state=tk.DISABLED)
    
    def on_init(self):
        try:
            self.algoritmo = self.algo_var.get()
            self.quantum = int(self.quantum_var.get())
            self.dialog.destroy()
        except ValueError:
            self.quantum_var.set("3")
    
    def on_cancel(self):
        self.dialog.destroy()
        self.parent.quit()


class App:
    def __init__(self, root, algoritmo="FCFS", quantum=3):
        self.root = root
        self.root.title("Simulador de Gestor de Procesos")
        self.root.geometry("1400x800")
        self.algoritmo_inicial = algoritmo
        self.quantum_inicial = quantum
        
        self.scheduler = Scheduler(algoritmo=algoritmo, quantum=quantum)
        self.pc = ProductorConsumidor(capacidad=5)
        if not hasattr(self.pc, "estado_actual"):
            self.pc.estado_actual = self.pc.estado
        self.logger = Logger()
        self.buzon = BuzonMensajes()
        self.scheduler.buzon = self.buzon
        self.scheduler.pc = self.pc
        
        self.auto_running = False
        self.auto_speed = 600
        self.proceso_id_contador = 0
        self.hilo_auto = None
        self.pids_cache = []
        self._ultimo_log_scheduler = 0
        self._ultimo_log_logger = 0
        
        self.setup_ui()
        # (no global debug bindings in production)
        self.schedule_update()

    def _debug_click(self, event):
        pass

    def setup_ui(self):
        self.tree_style = ttk.Style()
        self.tree_style.map(
            "Treeview",
            background=[("selected", "#2b6cb0")],
            foreground=[("selected", "white")],
        )

        self.setup_toolbar()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = ttk.LabelFrame(main_frame, text="PROCESOS")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        
        center_frame = ttk.LabelFrame(main_frame, text="RECURSOS")
        center_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        right_frame = ttk.LabelFrame(main_frame, text="LOGS")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=5)
        
        bottom_frame = ttk.LabelFrame(main_frame, text="PRODUCTOR-CONSUMIDOR")
        bottom_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)
        
        self.setup_left_panel(left_frame)
        self.setup_center_panel(center_frame)
        self.setup_right_panel(right_frame)
        self.setup_bottom_panel(bottom_frame)
        self._on_algoritmo_change()

    def setup_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="Algoritmo:").pack(side=tk.LEFT, padx=5)
        self.algoritmo_var = tk.StringVar(value=self.algoritmo_inicial)
        self.algoritmo_var.trace("w", self._on_algoritmo_change)
        algo_menu = ttk.OptionMenu(toolbar, self.algoritmo_var, self.algoritmo_inicial, "FCFS", "RoundRobin")
        algo_menu.pack(side=tk.LEFT, padx=5)
        
        self.label_quantum = ttk.Label(toolbar, text="Quantum:")
        self.label_quantum.pack(side=tk.LEFT, padx=5)
        self.quantum_var = tk.StringVar(value=str(self.quantum_inicial))
        self.entry_quantum = ttk.Entry(toolbar, textvariable=self.quantum_var, width=5)
        self.entry_quantum.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Tick Manual", command=self.manual_tick).pack(side=tk.LEFT, padx=5)
        
        self.auto_button = ttk.Button(toolbar, text="Auto ON", command=self.toggle_auto)
        self.auto_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(toolbar, text="Velocidad (lento a rápido):").pack(side=tk.LEFT, padx=5)
        self.speed_scale = ttk.Scale(toolbar, from_=2000, to=200, orient=tk.HORIZONTAL, 
                                      command=self.change_speed)
        self.speed_scale.set(600)
        self.speed_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    def _on_algoritmo_change(self, *args):
        if not hasattr(self, "entry_quantum") or not hasattr(self, "label_quantum"):
            return
        if self.algoritmo_var.get() == "RoundRobin":
            self.entry_quantum.config(state="normal")
            self.label_quantum.config(state="normal")
        else:
            self.entry_quantum.config(state="disabled")
            self.label_quantum.config(state="disabled")

    def change_speed(self, val):
        self.auto_speed = int(float(val))

    def setup_left_panel(self, parent):
        form_frame = ttk.LabelFrame(parent, text="Crear Proceso")
        form_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Nombre:").pack(side=tk.LEFT, padx=5)
        self.nombre_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.nombre_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(form_frame, text="Burst:").pack(side=tk.LEFT, padx=5)
        self.burst_var = tk.StringVar(value="5")
        ttk.Entry(form_frame, textvariable=self.burst_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(form_frame, text="Prioridad:").pack(side=tk.LEFT, padx=5)
        self.prioridad_var = tk.StringVar(value="5")
        ttk.Entry(form_frame, textvariable=self.prioridad_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(form_frame, text="Memoria:").pack(side=tk.LEFT, padx=5)
        self.memoria_var = tk.StringVar(value="512")
        ttk.Entry(form_frame, textvariable=self.memoria_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(form_frame, text="Crear", command=self.crear_proceso).pack(side=tk.LEFT, padx=5)
        
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, columns=("PID", "Nombre", "Estado", "Burst", "Restante"),
                                  show="headings", yscrollcommand=scrollbar.set)
        self.tree.column("PID", width=30)
        self.tree.column("Nombre", width=80)
        self.tree.column("Estado", width=80)
        self.tree.column("Burst", width=50)
        self.tree.column("Restante", width=50)
        self.tree.configure(selectmode="browse")
        
        for col in ("PID", "Nombre", "Estado", "Burst", "Restante"):
            self.tree.heading(col, text=col)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        # Track last clicked/focused tree item PID to allow button actions
        self._last_tree_pid = None
        self._selected_tree_pid = None
        try:
            self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
            self.tree.bind('<ButtonRelease-1>', self._on_tree_click)
        except Exception:
            pass
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.btn_suspender = ttk.Button(btn_frame, text="Suspender", command=self.suspender_proceso)
        self.btn_suspender.pack(side=tk.LEFT, padx=5)

        self.btn_reanudar = ttk.Button(btn_frame, text="Reanudar", command=self.reanudar_proceso)
        self.btn_reanudar.pack(side=tk.LEFT, padx=5)

        self.btn_terminar = ttk.Button(btn_frame, text="Terminar", command=self.terminar_proceso)
        self.btn_terminar.pack(side=tk.LEFT, padx=5)

        # Buttons created

    def setup_center_panel(self, parent):
        state_frame = ttk.LabelFrame(parent, text="Estado CPU")
        state_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.cpu_label = tk.Label(state_frame, text="LIBRE", bg="green", fg="white", 
                                   font=("Arial", 12, "bold"), height=3)
        self.cpu_label.pack(fill=tk.X, padx=5, pady=5)
        
        mem_frame = ttk.LabelFrame(parent, text="Memoria")
        mem_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mem_canvas = tk.Canvas(mem_frame, height=30, bg="white")
        self.mem_canvas.pack(fill=tk.X, padx=5, pady=5)
        
        queue_frame = ttk.LabelFrame(parent, text="Cola de Listos")
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(queue_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.queue_text = tk.Text(queue_frame, height=15, width=30, yscrollcommand=scrollbar.set)
        self.queue_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.queue_text.yview)

    def setup_right_panel(self, parent):
        ttk.Button(parent, text="Limpiar Logs", command=self.limpiar_logs).pack(padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = scrolledtext.ScrolledText(parent, height=30, width=40, 
                                                   yscrollcommand=scrollbar.set, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text.tag_config("PROCESO", foreground="blue")
        self.log_text.tag_config("RECURSO", foreground="orange")
        self.log_text.tag_config("ALGORITMO", foreground="green")
        self.log_text.tag_config("IPC", foreground="purple")

    def setup_bottom_panel(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        pc_frame = ttk.Frame(notebook)
        notebook.add(pc_frame, text="Productor-Consumidor")
        
        buffer_frame = ttk.Frame(pc_frame)
        buffer_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(buffer_frame, text="Buffer:").pack()
        
        self.buffer_canvas = tk.Canvas(buffer_frame, width=300, height=50, bg="white")
        self.buffer_canvas.pack()

        self.pc_label = ttk.Label(pc_frame, text="Ocupación: 0/5", font=("Arial", 10))
        self.pc_label.pack(side=tk.LEFT, padx=10, pady=10)
        
    def crear_proceso(self):
        try:
            nombre = self.nombre_var.get() or f"P{self.proceso_id_contador}"
            burst = int(self.burst_var.get())
            prioridad = int(self.prioridad_var.get())
            memoria = int(self.memoria_var.get())
            
            proceso = Proceso(nombre=nombre, prioridad=prioridad, burst_time=burst, 
                            memoria_req=memoria, tiempo_llegada=self.scheduler.tick)
            self.scheduler.agregar_proceso(proceso)
            self.buzon.crear_buzon(proceso.pid)
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Creado {nombre} (PID {proceso.pid})")
            
            self.proceso_id_contador += 1
            self.nombre_var.set("")
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error: {e}")

    def _on_tree_select(self, event):
        try:
            sel = self.tree.selection()
            if sel:
                item = self.tree.item(sel[0])
                vals = item.get("values") or []
                if vals:
                    try:
                        pid = int(vals[0])
                    except Exception:
                        pid = vals[0]
                    self._last_tree_pid = pid
                    self._selected_tree_pid = pid
        except Exception:
            pass

    def _on_tree_click(self, event):
        try:
            row = self.tree.identify_row(event.y)
            if row:
                # Ensure the tree selection is set when clicking a row
                try:
                    self.tree.selection_set(row)
                    self.tree.focus(row)
                    self.tree.see(row)
                    self.tree.focus_set()
                except Exception:
                    pass
                item = self.tree.item(row)
                vals = item.get("values") or []
                if vals:
                    try:
                        pid = int(vals[0])
                    except Exception:
                        pid = vals[0]
                    self._last_tree_pid = pid
                    self._selected_tree_pid = pid
        except Exception:
            pass

    def suspender_proceso(self):
        seleccion = self.tree.selection()
        if not seleccion:
            last_pid = getattr(self, '_last_tree_pid', None)
            if last_pid is None:
                self.logger.registrar(self.scheduler.tick, "PROCESO", "Suspender: sin selección en la tabla")
                return
            pid = int(last_pid)
        else:
            try:
                item = self.tree.item(seleccion[0])
                pid = int(item["values"][0])
            except Exception as e:
                last_pid = getattr(self, '_last_tree_pid', None)
                if last_pid is None:
                    self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error leyendo PID para suspender: {e}")
                    return
                pid = int(last_pid)

        try:
            self.scheduler.suspender(pid)
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Suspender pedido para PID {pid}")
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error al suspender PID {pid}: {e}")

        self.refresh_ui()

    def reanudar_proceso(self):
        seleccion = self.tree.selection()
        if not seleccion:
            last_pid = getattr(self, '_last_tree_pid', None)
            if last_pid is None:
                self.logger.registrar(self.scheduler.tick, "PROCESO", "Reanudar: sin selección en la tabla")
                return
            pid = int(last_pid)
        else:
            try:
                item = self.tree.item(seleccion[0])
                pid = int(item["values"][0])
            except Exception as e:
                last_pid = getattr(self, '_last_tree_pid', None)
                if last_pid is None:
                    self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error leyendo PID para reanudar: {e}")
                    return
                pid = int(last_pid)

        try:
            self.scheduler.reanudar(pid)
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Reanudar pedido para PID {pid}")
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error al reanudar PID {pid}: {e}")

        self.refresh_ui()

    def terminar_proceso(self):
        seleccion = self.tree.selection()
        if not seleccion:
            last_pid = getattr(self, '_last_tree_pid', None)
            if last_pid is None:
                self.logger.registrar(self.scheduler.tick, "PROCESO", "Terminar: sin selección en la tabla")
                return
            pid = int(last_pid)
        else:
            try:
                item = self.tree.item(seleccion[0])
                pid = int(item["values"][0])
            except Exception as e:
                last_pid = getattr(self, '_last_tree_pid', None)
                if last_pid is None:
                    self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error leyendo PID para terminar: {e}")
                    return
                pid = int(last_pid)

        try:
            self.scheduler.terminar(pid, causa="forzado")
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Terminar pedido para PID {pid} (forzado)")
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error al terminar PID {pid}: {e}")

        self.refresh_ui()

    def manual_tick(self):
        try:
            quantum = int(self.quantum_var.get())
            self.scheduler.quantum = quantum
            algo = self.algoritmo_var.get()
            self.scheduler.algoritmo = algo
            self.scheduler.tick_step()
            self.logger.registrar(self.scheduler.tick, "ALGORITMO", f"Tick manual ({algo})")
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "ALGORITMO", f"Error: {e}")
        
        self.refresh_ui()

    def toggle_auto(self):
        self.auto_running = not self.auto_running
        if self.auto_running:
            self.auto_button.config(text="Auto OFF")
            self.hilo_auto = threading.Thread(target=self._loop_auto, daemon=True)
            self.hilo_auto.start()
        else:
            self.auto_button.config(text="Auto ON")

    def _loop_auto(self):
        while self.auto_running:
            try:
                quantum = int(self.quantum_var.get())
                self.scheduler.quantum = quantum
                algo = self.algoritmo_var.get()
                self.scheduler.algoritmo = algo
                self.scheduler.tick_step()
            except Exception:
                pass

            time.sleep(self.auto_speed / 1000.0)

    def limpiar_logs(self):
        self.logger.limpiar()
        self.log_text.delete("1.0", tk.END)
        self._ultimo_log_logger = 0
        self._ultimo_log_scheduler = 0

    def refresh_ui(self):
        pids_activos = [str(p["pid"]) for p in self.scheduler.obtener_todos() if p["estado"] != "terminado"]
        
        self.tree.delete(*self.tree.get_children())
        selected_pid = getattr(self, "_selected_tree_pid", None)
        restored_item = None
        for proc_dict in self.scheduler.obtener_todos():
            item_id = self.tree.insert("", tk.END, values=(
                proc_dict["pid"],
                proc_dict["nombre"],
                proc_dict["estado"],
                proc_dict["burst_time"],
                proc_dict["tiempo_restante"]
            ))
            if selected_pid is not None and proc_dict["pid"] == selected_pid:
                restored_item = item_id

        if restored_item:
            try:
                self.tree.selection_set(restored_item)
                self.tree.focus(restored_item)
                self.tree.see(restored_item)
            except Exception:
                pass
        
        if self.scheduler.proceso_actual:
            self.cpu_label.config(text=f"EN USO (PID {self.scheduler.proceso_actual.pid})", 
                                 bg="red")
        else:
            self.cpu_label.config(text="LIBRE", bg="green")
        
        estado = self.scheduler.recursos.estado()
        usada = estado["memoria_total"] - estado["memoria_disponible"]
        total = estado["memoria_total"]
        porcentaje = usada / total if total > 0 else 0

        ancho_total = self.mem_canvas.winfo_width() or 300
        self.mem_canvas.delete("all")
        self.mem_canvas.create_rectangle(
            0, 0, ancho_total * porcentaje, 20, fill="orange")
        self.mem_canvas.create_text(
            ancho_total // 2, 10,
            text=f"{usada} MB / {total} MB", fill="black")
        
        self.queue_text.delete("1.0", tk.END)
        queue_info = f"Procesos en cola: {len(self.scheduler.cola_listos)}\n"
        for pid in self.scheduler.cola_listos:
            proc = self.scheduler.todos_los_procesos[pid]
            queue_info += f"  PID {pid}: {proc.nombre} (restante: {proc.tiempo_restante})\n"
        self.queue_text.insert("1.0", queue_info)
        
        nuevos_eventos_logger = self.logger.obtener_todos()[self._ultimo_log_logger:]
        for evt in nuevos_eventos_logger:
            linea = f"[{evt['tick']}] {evt['tipo']}: {evt['msg']}\n"
            self.log_text.insert(tk.END, linea, evt["tipo"])
        self._ultimo_log_logger = len(self.logger.obtener_todos())

        nuevos_logs_scheduler = self.scheduler.log[self._ultimo_log_scheduler:]
        for msg in nuevos_logs_scheduler:
            self.log_text.insert(tk.END, f"{msg}\n", "ALGORITMO")
        self._ultimo_log_scheduler = len(self.scheduler.log)
        
        self.buffer_canvas.delete("all")
        estado_pc = self.pc.estado_actual()
        buffer_items = estado_pc["buffer"]
        for i in range(estado_pc["capacidad"]):
            x = 20 + i * 55
            color = "green" if i < len(buffer_items) else "lightgray"
            self.buffer_canvas.create_rectangle(x, 5, x + 50, 45, fill=color, outline="black")
            if i < len(buffer_items):
                self.buffer_canvas.create_text(x + 25, 25, text=buffer_items[i][:5], 
                                              font=("Arial", 8))
        
        self.pc_label.config(text=f"Ocupación: {len(buffer_items)}/{estado_pc['capacidad']}")

    def schedule_update(self):
        self.refresh_ui()
        self.root.after(100, self.schedule_update)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
