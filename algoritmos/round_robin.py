def rr_tick(scheduler):
    # Round Robin: preemptivo con quantum
    if scheduler.proceso_actual is None:
        if scheduler.cola_listos:
            pid = scheduler.cola_listos.popleft()
            proceso = scheduler.todos_los_procesos[pid]
            
            if scheduler.recursos.solicitar_cpu(pid):
                proceso.cambiar_estado("ejecutando")
                scheduler.proceso_actual = proceso
                scheduler.ticks_en_cpu = 0
                scheduler._registrar_log(f"Proceso {pid} iniciado en CPU")
    
    if scheduler.proceso_actual is not None:
        scheduler.ticks_en_cpu += 1
        scheduler.proceso_actual.tiempo_restante -= 1
        
        if scheduler.proceso_actual.tiempo_restante <= 0:
            pid = scheduler.proceso_actual.pid
            scheduler.terminar(pid, causa="normal")
        elif scheduler.ticks_en_cpu >= scheduler.quantum:
            pid = scheduler.proceso_actual.pid
            scheduler.proceso_actual.cambiar_estado("listo")
            scheduler.cola_listos.append(pid)
            scheduler.recursos.liberar_cpu()
            scheduler.proceso_actual = None
            scheduler.ticks_en_cpu = 0
            scheduler._registrar_log(f"Proceso {pid} desalojado por quantum")
