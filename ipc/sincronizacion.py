class Semaforo:
    def __init__(self, valor):
        self.valor = valor
        self.bloqueados = []

    def wait(self, pid):
        if self.valor > 0:
            self.valor -= 1
            return True
        else:
            self.bloqueados.append(pid)
            return False

    def signal(self):
        if self.bloqueados:
            pid = self.bloqueados.pop(0)
            return pid
        else:
            self.valor += 1
            return None


class ProductorConsumidor:
    def __init__(self, capacidad=5):
        self.capacidad = capacidad
        self.buffer = []
        self.sem_llenos = Semaforo(0)
        self.sem_vacios = Semaforo(capacidad)
        self.mutex = Semaforo(1)

    def producir(self, pid, item):
        if not self.mutex.wait(pid):
            return {"ok": False, "buffer": self.buffer, "msg": f"Mutex bloqueado para PID {pid}"}
        
        if not self.sem_vacios.wait(pid):
            self.mutex.signal()
            return {"ok": False, "buffer": self.buffer, "msg": f"Buffer lleno, PID {pid} bloqueado"}
        
        self.buffer.append(item)
        self.sem_llenos.signal()
        self.mutex.signal()
        
        return {"ok": True, "buffer": list(self.buffer), "msg": f"Producido: {item}"}

    def consumir(self, pid):
        if not self.mutex.wait(pid):
            return {"ok": False, "item": None, "buffer": self.buffer, "msg": f"Mutex bloqueado para PID {pid}"}
        
        if not self.sem_llenos.wait(pid):
            self.mutex.signal()
            return {"ok": False, "item": None, "buffer": self.buffer, "msg": f"Buffer vacío, PID {pid} bloqueado"}
        
        item = self.buffer.pop(0)
        self.sem_vacios.signal()
        self.mutex.signal()
        
        return {"ok": True, "item": item, "buffer": list(self.buffer), "msg": f"Consumido: {item}"}

    def estado(self):
        return {
            "buffer": list(self.buffer),
            "capacidad": self.capacidad,
            "ocupados": len(self.buffer),
            "libres": self.capacidad - len(self.buffer),
        }
