from __future__ import annotations


class Proceso:
	_contador_pid = 1

	ESTADOS_VALIDOS = {"listo", "ejecutando", "esperando", "suspendido", "terminado"}

	def __init__(
		self,
		nombre: str,
		prioridad: int,
		burst_time: int,
		memoria_req: int,
		tiempo_llegada: int = 0,
	) -> None:
		self.pid = Proceso._contador_pid
		Proceso._contador_pid += 1

		self.nombre = nombre
		self.estado = "listo"
		self.prioridad = prioridad
		self.burst_time = burst_time
		self.tiempo_restante = burst_time
		self.memoria_req = memoria_req
		self.recursos_asignados = {"cpu": False, "memoria": 0}
		self.causa_terminacion = None
		self.tiempo_llegada = tiempo_llegada

	def cambiar_estado(self, nuevo: str) -> None:
		if nuevo not in self.ESTADOS_VALIDOS:
			raise ValueError(f"Estado invalido: {nuevo}")
		self.estado = nuevo

	def asignar_recurso(self, tipo: str, val) -> None:
		if tipo == "cpu":
			self.recursos_asignados["cpu"] = bool(val)
		elif tipo == "memoria":
			self.recursos_asignados["memoria"] = int(val)
		else:
			self.recursos_asignados[tipo] = val

	def liberar_recursos(self) -> None:
		self.recursos_asignados = {"cpu": False, "memoria": 0}

	def to_dict(self) -> dict:
		return {
			"pid": self.pid,
			"nombre": self.nombre,
			"estado": self.estado,
			"prioridad": self.prioridad,
			"burst_time": self.burst_time,
			"tiempo_restante": self.tiempo_restante,
			"memoria_req": self.memoria_req,
			"recursos_asignados": dict(self.recursos_asignados),
			"causa_terminacion": self.causa_terminacion,
			"tiempo_llegada": self.tiempo_llegada,
		}
