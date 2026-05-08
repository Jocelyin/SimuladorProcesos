class Logger:
    def __init__(self):
        self.eventos = []

    def registrar(self, tick, tipo, msg):
        self.eventos.append({"tick": tick, "tipo": tipo, "msg": msg})

    def obtener_todos(self):
        return list(self.eventos)

    def limpiar(self):
        self.eventos = []

    def como_texto(self):
        lineas = []
        for evt in self.eventos:
            linea = f"[{evt['tick']:3d}] {evt['tipo']:10s} {evt['msg']}"
            lineas.append(linea)
        return "\n".join(lineas)
