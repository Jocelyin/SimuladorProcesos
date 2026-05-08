class GestorRecursos:
	def __init__(self) -> None:
		self.cpu_libre = True
		self.memoria_total = 4096
		self.memoria_disponible = 4096
		self.pid_en_cpu = None

	def solicitar_cpu(self, pid) -> bool:
		if not self.cpu_libre:
			return False
		self.cpu_libre = False
		self.pid_en_cpu = pid
		return True

	def liberar_cpu(self) -> None:
		self.cpu_libre = True
		self.pid_en_cpu = None

	def solicitar_memoria(self, pid, cantidad) -> bool:
		if cantidad > self.memoria_disponible:
			return False
		self.memoria_disponible -= cantidad
		return True

	def liberar_memoria(self, cantidad) -> None:
		self.memoria_disponible = min(self.memoria_total, self.memoria_disponible + cantidad)

	def estado(self) -> dict:
		return {
			"cpu_libre": self.cpu_libre,
			"memoria_total": self.memoria_total,
			"memoria_disponible": self.memoria_disponible,
			"pid_en_cpu": self.pid_en_cpu,
		}
