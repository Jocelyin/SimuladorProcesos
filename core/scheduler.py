from collections import deque

from core.recursos import GestorRecursos


class Scheduler:
	def __init__(self, algoritmo: str = "FCFS", quantum: int = 3) -> None:
		self.cola_listos = deque()
		self.todos_los_procesos = {}
		self.proceso_actual = None
		self.algoritmo = algoritmo
		self.quantum = quantum
		self.ticks_en_cpu = 0
		self.tick = 0
		self.recursos = GestorRecursos()
		self.log = []

	def _registrar_log(self, mensaje: str) -> None:
		self.log.append(f"[Tick {self.tick}] {mensaje}")

	def agregar_proceso(self, proceso) -> bool:
		if not self.recursos.solicitar_memoria(proceso.pid, proceso.memoria_req):
			self._registrar_log(f"Memoria insuficiente para proceso {proceso.pid}")
			return False
		self.todos_los_procesos[proceso.pid] = proceso
		if proceso.estado != "listo":
			proceso.cambiar_estado("listo")
		if proceso.tiempo_llegada == 0:
			proceso.tiempo_llegada = self.tick
		self.cola_listos.append(proceso.pid)
		self._registrar_log(f"Proceso {proceso.pid} agregado a la cola de listos")
		return True

	def suspender(self, pid) -> None:
		proceso = self.todos_los_procesos.get(pid)
		if proceso is None:
			return
		proceso.cambiar_estado("suspendido")
		if self.proceso_actual is not None and self.proceso_actual.pid == pid:
			self.proceso_actual = None
			self.ticks_en_cpu = 0
			self.recursos.liberar_cpu()
		self._registrar_log(f"Proceso {pid} suspendido")

	def reanudar(self, pid) -> None:
		proceso = self.todos_los_procesos.get(pid)
		if proceso is None:
			return
		proceso.cambiar_estado("listo")
		self.cola_listos.append(pid)
		self._registrar_log(f"Proceso {pid} reanudado")

	def terminar(self, pid, causa="forzado") -> None:
		proceso = self.todos_los_procesos.get(pid)
		if proceso is None:
			return
		proceso.cambiar_estado("terminado")
		proceso.causa_terminacion = causa
		self.recursos.liberar_memoria(proceso.memoria_req)
		proceso.liberar_recursos()
		if self.proceso_actual is not None and self.proceso_actual.pid == pid:
			self.proceso_actual = None
			self.ticks_en_cpu = 0
			self.recursos.liberar_cpu()
		if hasattr(self, "buzon") and self.cola_listos:
			siguiente_pid = self.cola_listos[0] if self.cola_listos else None
			if siguiente_pid:
				self.buzon.enviar(pid, siguiente_pid, f"CPU liberada por PID {pid}, tu turno")
				self._registrar_log(f"IPC: PID {pid} notificó a PID {siguiente_pid}")
		self._registrar_log(f"Proceso {pid} terminado ({causa})")

	def tick_step(self) -> None:
		self.tick += 1
		algoritmo = self.algoritmo.lower()

		if algoritmo == "fcfs":
			from algoritmos.fcfs import fcfs_tick

			fcfs_tick(self)
		elif algoritmo == "roundrobin":
			from algoritmos.round_robin import rr_tick

			rr_tick(self)
		else:
			raise ValueError(f"Algoritmo no soportado: {self.algoritmo}")

		if hasattr(self, 'pc'):
			if self.tick % 4 == 0:
				pid_actual = self.proceso_actual.pid if self.proceso_actual else None
				if pid_actual is not None:
					estado_pc = self.pc.estado()
					ocupacion = len(estado_pc["buffer"])
					capacidad = estado_pc["capacidad"]

					if ocupacion < capacidad // 2:
						resultado = self.pc.producir(pid_actual, f"item-{self.tick}")
						if resultado["ok"]:
							self._registrar_log(
								f"PC: PID {pid_actual} produjo item-{self.tick}")
						else:
							self._registrar_log(
								f"PC: {resultado['msg']}")
					else:
						resultado = self.pc.consumir(pid_actual)
						if resultado["ok"]:
							self._registrar_log(
								f"PC: PID {pid_actual} consumió {resultado['item']}")
						else:
							self._registrar_log(
								f"PC: {resultado['msg']}")

			if self.proceso_actual is None and not self.cola_listos and len(self.pc.buffer) > 0:
				self.pc.vaciado()
				self._registrar_log("PC: Buffer vaciado (sin procesos activos)")

	def obtener_todos(self) -> list:
		return [proceso.to_dict() for proceso in self.todos_los_procesos.values()]
