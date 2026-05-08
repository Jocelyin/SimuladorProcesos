class BuzonMensajes:
    def __init__(self):
        self.buzones = {}

    def crear_buzon(self, pid):
        if pid not in self.buzones:
            self.buzones[pid] = []

    def enviar(self, origen, destino, texto):
        if destino not in self.buzones:
            self.crear_buzon(destino)
        
        self.buzones[destino].append({"de": origen, "texto": texto})
        return True

    def recibir(self, pid):
        if pid not in self.buzones:
            return []
        
        mensajes = self.buzones[pid]
        self.buzones[pid] = []
        return mensajes

    def hay_mensajes(self, pid):
        if pid not in self.buzones:
            return False
        return len(self.buzones[pid]) > 0
