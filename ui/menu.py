import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scheduler import Scheduler
from core.proceso import Proceso
from ipc.sincronizacion import ProductorConsumidor
from ipc.mensajes import BuzonMensajes
from ui.logger import Logger


class App:
    def __init__(self, root, algoritmo="FCFS", quantum=3):
        self.root = root
        self.root.title("Simulador de Gestor de Procesos")
        self.root.geometry("1400x800")
        
        self.scheduler = Scheduler(algoritmo=algoritmo, quantum=quantum)
        self.pc = ProductorConsumidor(capacidad=5)
        self.logger = Logger()
        self.buzon = BuzonMensajes()
        
        self.auto_running = False
        self.auto_speed = 600
        self.proceso_id_contador = 0
        self.hilo_auto = None
        self.pids_cache = []
        
        self.setup_styles()
        self.setup_ui()
        self.schedule_update()

    def setup_styles(self):
        self.root.configure(bg="#2b2b2b")

        style = ttk.Style()
        style.theme_use("clam")

        bg_dark = "#2b2b2b"
        bg_med = "#3c3c3c"
        bg_light = "#4a4a4a"
        fg = "#ffffff"

        style.configure("TFrame", background=bg_med)
        style.configure("TLabel", background=bg_med, foreground=fg)
        style.configure("TLabelframe", background=bg_dark, foreground=fg)
        style.configure("TLabelframe.Label", background=bg_dark, foreground=fg)
        style.configure("TButton", background=bg_med, foreground=fg, bordercolor=bg_light)
        style.map("TButton", background=[("active", bg_light)])
        style.configure("TEntry", fieldbackground=bg_dark, foreground=fg)
        style.configure("TScale", background=bg_med, troughcolor=bg_dark)
        style.configure("TNotebook", background=bg_dark, foreground=fg)
        style.configure("TNotebook.Tab", background=bg_med, foreground=fg)
        style.map("TNotebook.Tab", background=[("selected", bg_dark)])
        style.configure("Treeview", background=bg_med, foreground=fg, fieldbackground=bg_med)
        style.configure("Treeview.Heading", background=bg_dark, foreground=fg)
        style.map("Treeview", background=[("selected", bg_light)])
        style.configure("TMenubutton", background=bg_med, foreground=fg)

    def setup_ui(self):
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

    def setup_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="Algoritmo:").pack(side=tk.LEFT, padx=5)
        self.algo_var = tk.StringVar(value="FCFS")
        algo_menu = ttk.OptionMenu(toolbar, self.algo_var, "FCFS", "FCFS", "RoundRobin")
        algo_menu.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(toolbar, text="Quantum:").pack(side=tk.LEFT, padx=5)
        self.quantum_var = tk.StringVar(value="3")
        ttk.Entry(toolbar, textvariable=self.quantum_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Tick Manual", command=self.manual_tick).pack(side=tk.LEFT, padx=5)
        
        self.auto_button = ttk.Button(toolbar, text="Auto ON", command=self.toggle_auto)
        self.auto_button.pack(side=tk.LEFT, padx=5)
        


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
        
        for col in ("PID", "Nombre", "Estado", "Burst", "Restante"):
            self.tree.heading(col, text=col)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Suspender", command=self.suspender).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reanudar", command=self.reanudar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Terminar", command=self.terminar).pack(side=tk.LEFT, padx=5)

    def setup_center_panel(self, parent):
        state_frame = ttk.LabelFrame(parent, text="Estado CPU")
        state_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.cpu_label = tk.Label(state_frame, text="LIBRE", bg="green", fg="white", 
                                   font=("Arial", 12, "bold"), height=3)
        self.cpu_label.pack(fill=tk.X, padx=5, pady=5)
        
        mem_frame = ttk.LabelFrame(parent, text="Memoria")
        mem_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mem_canvas = tk.Canvas(mem_frame, height=30, bg="#3c3c3c")
        self.mem_canvas.pack(fill=tk.X, padx=5, pady=5)
        
        queue_frame = ttk.LabelFrame(parent, text="Cola de Listos")
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(queue_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.queue_text = tk.Text(queue_frame, height=15, width=30, yscrollcommand=scrollbar.set,
                                   bg="#3c3c3c", fg="#ffffff", insertbackground="#ffffff")
        self.queue_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.queue_text.yview)

    def setup_right_panel(self, parent):
        ttk.Button(parent, text="Limpiar Logs", command=self.limpiar_logs).pack(padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = scrolledtext.ScrolledText(parent, height=30, width=40, 
                                                   yscrollcommand=scrollbar.set, wrap=tk.WORD,
                                                   bg="#3c3c3c", fg="#ffffff", insertbackground="#ffffff")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text.tag_config("PROCESO", foreground="#4FC3F7")
        self.log_text.tag_config("RECURSO", foreground="#FFB74D")
        self.log_text.tag_config("ALGORITMO", foreground="#81C784")
        self.log_text.tag_config("IPC", foreground="#CE93D8")

    def setup_bottom_panel(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        pc_frame = ttk.Frame(notebook)
        notebook.add(pc_frame, text="Productor-Consumidor")
        
        buffer_frame = ttk.Frame(pc_frame)
        buffer_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(buffer_frame, text="Buffer:").pack()
        
        self.buffer_canvas = tk.Canvas(buffer_frame, width=300, height=50, bg="#3c3c3c")
        self.buffer_canvas.pack()
        
        control_frame = ttk.Frame(pc_frame)
        control_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(control_frame, text="Item:").pack(side=tk.LEFT, padx=5)
        self.item_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.item_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Producir", command=self.producir).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Consumir", command=self.consumir).pack(side=tk.LEFT, padx=5)
        
        self.pc_label = ttk.Label(pc_frame, text="", font=("Arial", 10))
        self.pc_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        msg_frame = ttk.Frame(notebook)
        notebook.add(msg_frame, text="Mensajes")
        
        ctrl_frame = ttk.Frame(msg_frame)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(ctrl_frame, text="De PID:").pack(side=tk.LEFT, padx=5)
        self.msg_from_var = tk.StringVar(value="1")
        self.msg_from_menu = tk.OptionMenu(ctrl_frame, self.msg_from_var, "1")
        self.msg_from_menu.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(ctrl_frame, text="A PID:").pack(side=tk.LEFT, padx=5)
        self.msg_to_var = tk.StringVar(value="1")
        self.msg_to_menu = tk.OptionMenu(ctrl_frame, self.msg_to_var, "1")
        self.msg_to_menu.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(ctrl_frame, text="Mensaje:").pack(side=tk.LEFT, padx=5)
        self.msg_text_var = tk.StringVar()
        ttk.Entry(ctrl_frame, textvariable=self.msg_text_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="Enviar", command=self.enviar_mensaje).pack(side=tk.LEFT, padx=5)
        
        display_frame = ttk.Frame(msg_frame)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(display_frame, text="Mensajes recibidos:").pack(anchor=tk.W)
        
        scrollbar = ttk.Scrollbar(display_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.msg_display = scrolledtext.ScrolledText(display_frame, height=8, width=80, 
                                                     yscrollcommand=scrollbar.set,
                                                     bg="#3c3c3c", fg="#ffffff", insertbackground="#ffffff")
        self.msg_display.pack(fill=tk.BOTH, expand=True)

    def crear_proceso(self):
        try:
            nombre = self.nombre_var.get() or f"P{self.proceso_id_contador}"
            burst = int(self.burst_var.get())
            prioridad = int(self.prioridad_var.get())
            memoria = int(self.memoria_var.get())
            
            proceso = Proceso(nombre=nombre, prioridad=prioridad, burst_time=burst, 
                            memoria_req=memoria, tiempo_llegada=self.scheduler.tick)
            if self.scheduler.agregar_proceso(proceso):
                self.buzon.crear_buzon(proceso.pid)
                self.logger.registrar(self.scheduler.tick, "PROCESO", f"Creado {nombre} (PID {proceso.pid})")
                self.proceso_id_contador += 1
                self.nombre_var.set("")
            else:
                self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error: memoria insuficiente para {nombre}")
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "PROCESO", f"Error: {e}")

    def suspender(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            pid = int(item["values"][0])
            self.scheduler.suspender(pid)

    def reanudar(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            pid = int(item["values"][0])
            self.scheduler.reanudar(pid)

    def terminar(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            pid = int(item["values"][0])
            self.scheduler.terminar(pid, causa="usuario")

    def manual_tick(self):
        try:
            quantum = int(self.quantum_var.get())
            self.scheduler.quantum = quantum
            algo = self.algo_var.get()
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
                algo = self.algo_var.get()
                self.scheduler.algoritmo = algo
                self.scheduler.tick_step()
            except Exception:
                pass
            
            time.sleep(self.auto_speed / 1000.0)

    def producir(self):
        try:
            item = self.item_var.get()
            if not item:
                item = f"item_{len(self.pc.buffer)}"
            
            result = self.pc.producir(pid=1, item=item)
            self.logger.registrar(self.scheduler.tick, "IPC", result["msg"])
            self.item_var.set("")
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "IPC", f"Error: {e}")
        
        self.refresh_ui()

    def consumir(self):
        try:
            result = self.pc.consumir(pid=1)
            self.logger.registrar(self.scheduler.tick, "IPC", result["msg"])
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "IPC", f"Error: {e}")
        
        self.refresh_ui()

    def enviar_mensaje(self):
        try:
            from_pid = int(self.msg_from_var.get())
            to_pid = int(self.msg_to_var.get())
            texto = self.msg_text_var.get()
            
            if not texto:
                self.logger.registrar(self.scheduler.tick, "IPC", "Mensaje vacío")
                return
            
            self.buzon.enviar(from_pid, to_pid, texto)
            self.logger.registrar(self.scheduler.tick, "IPC", f"Mensaje de {from_pid} a {to_pid}: {texto}")
            self.msg_text_var.set("")
        except Exception as e:
            self.logger.registrar(self.scheduler.tick, "IPC", f"Error al enviar: {e}")

    def limpiar_logs(self):
        self.logger.limpiar()
        self.log_text.delete("1.0", tk.END)

    def refresh_ui(self):
        pids_activos = [str(p["pid"]) for p in self.scheduler.obtener_todos()]
        
        if pids_activos != self.pids_cache:
            self.pids_cache = pids_activos
            self.msg_from_menu['menu'].delete(0, 'end')
            self.msg_to_menu['menu'].delete(0, 'end')
            for pid in pids_activos:
                self.msg_from_menu['menu'].add_command(label=pid, command=tk._setit(self.msg_from_var, pid))
                self.msg_to_menu['menu'].add_command(label=pid, command=tk._setit(self.msg_to_var, pid))
        
        self.tree.delete(*self.tree.get_children())
        for proc_dict in self.scheduler.obtener_todos():
            self.tree.insert("", tk.END, values=(
                proc_dict["pid"],
                proc_dict["nombre"],
                proc_dict["estado"],
                proc_dict["burst_time"],
                proc_dict["tiempo_restante"]
            ))
        
        if self.scheduler.proceso_actual:
            self.cpu_label.config(text=f"EN USO (PID {self.scheduler.proceso_actual.pid})", 
                                 bg="red")
        else:
            self.cpu_label.config(text="LIBRE", bg="green")
        
        self.mem_canvas.delete("all")
        estado_rec = self.scheduler.recursos.estado()
        mem_total = estado_rec["memoria_total"]
        mem_usado = mem_total - estado_rec["memoria_disponible"]
        ancho = self.mem_canvas.winfo_width()
        if ancho > 1:
            ratio = mem_usado / mem_total if mem_total > 0 else 0
            self.mem_canvas.create_rectangle(0, 0, ancho * ratio, 30, fill="blue")
            self.mem_canvas.create_text(ancho // 2, 15, text=f"{mem_usado}/{mem_total} MB", 
                                       fill="white", font=("Arial", 9))
        
        self.queue_text.delete("1.0", tk.END)
        queue_info = f"Procesos en cola: {len(self.scheduler.cola_listos)}\n"
        for pid in self.scheduler.cola_listos:
            proc = self.scheduler.todos_los_procesos[pid]
            queue_info += f"  PID {pid}: {proc.nombre} (restante: {proc.tiempo_restante})\n"
        self.queue_text.insert("1.0", queue_info)
        
        self.log_text.delete("1.0", tk.END)
        for evt in self.logger.obtener_todos()[-20:]:
            linea = f"[{evt['tick']}] {evt['tipo']}: {evt['msg']}\n"
            self.log_text.insert(tk.END, linea, evt["tipo"])
        
        self.buffer_canvas.delete("all")
        estado_pc = self.pc.estado()
        buffer_items = estado_pc["buffer"]
        for i in range(estado_pc["capacidad"]):
            x = 20 + i * 55
            color = "green" if i < len(buffer_items) else "lightgray"
            self.buffer_canvas.create_rectangle(x, 5, x + 50, 45, fill=color, outline="black")
            if i < len(buffer_items):
                self.buffer_canvas.create_text(x + 25, 25, text=buffer_items[i][:5], 
                                              font=("Arial", 8))
        
        self.pc_label.config(text=f"Buffer: {len(buffer_items)}/{estado_pc['capacidad']}")
        
        self.msg_display.delete("1.0", tk.END)
        for pid in [p["pid"] for p in self.scheduler.obtener_todos()]:
            mensajes = self.buzon.recibir(pid)
            if mensajes:
                msg_header = f"\n--- Proceso {pid} ---\n"
                self.msg_display.insert(tk.END, msg_header)
                for msg in mensajes:
                    linea = f"De {msg['de']}: {msg['texto']}\n"
                    self.msg_display.insert(tk.END, linea)

    def schedule_update(self):
        self.refresh_ui()
        self.root.after(100, self.schedule_update)

