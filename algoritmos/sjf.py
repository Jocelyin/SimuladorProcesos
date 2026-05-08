def sjf_tick(scheduler):
    # SJF: selecciona proceso con menor tiempo_restante, no preemptivo
    if scheduler.proceso_actual is None:
        if scheduler.cola_listos:
            lista_pids = list(scheduler.cola_listos)
            lista_pids.sort(key=lambda p: scheduler.todos_los_procesos[p].tiempo_restante)
            
            scheduler.cola_listos.clear()
            for p in lista_pids:
                scheduler.cola_listos.append(p)
            
            pid = scheduler.cola_listos.popleft()
            proceso = scheduler.todos_los_procesos[pid]
            
            if scheduler.recursos.solicitar_cpu(pid):
                proceso.cambiar_estado("ejecutando")
                scheduler.proceso_actual = proceso
                scheduler.ticks_en_cpu = 0
                scheduler._registrar_log(f"Proceso {pid} iniciado en CPU (tiempo={proceso.tiempo_restante})")
    
    if scheduler.proceso_actual is not None:
        scheduler.ticks_en_cpu += 1
        scheduler.proceso_actual.tiempo_restante -= 1
        
        if scheduler.proceso_actual.tiempo_restante <= 0:
            pid = scheduler.proceso_actual.pid
            scheduler.terminar(pid, causa="normal")
