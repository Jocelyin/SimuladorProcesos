def fcfs_tick(scheduler):
    # FCFS: procesa en orden FIFO sin preemption
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
