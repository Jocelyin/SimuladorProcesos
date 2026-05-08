# Simulador de Gestor de Procesos

Simulador educativo de un gestor de procesos de sistema operativo, implementado en Python con interfaz gráfica tkinter. Reproduce fielmente el comportamiento de un planificador de procesos real con algoritmos FCFS y Round Robin.

## Información Académica

**Materia:** Sistemas Operativos  
**Institución:** Universidad Autónoma de Tamaulipas, Facultad de Ingeniería Tampico  
**Semestre:** 6°  
**Profesor:** Dr. Dante Adolfo Muñoz Quintero

## Integrantes

- César Olvera Rodríguez
- Brian Satihs Hernandez Gonzalez
- Jocelyin Mateo Saldierna

## Requisitos

- Python 3.x
- tkinter (incluido por defecto en Python)

## Instalación y Ejecución

1. Clona el repositorio:
```bash
git clone https://github.com/Jocelyin/SimuladorProcesos.git
cd SimuladorProcesos
```

2. Ejecuta la aplicación desde la raíz del proyecto:
```bash
python main.py
```

## Estructura del Proyecto

```
SimuladorProcesos/
├── main.py                    # Punto de entrada principal
├── core/                      # Lógica del simulador
│   ├── __init__.py
│   ├── proceso.py            # Clase Proceso con PID, estado, recursos
│   ├── scheduler.py          # Orquestador central del sistema
│   └── recursos.py           # Gestor de CPU y memoria
├── algoritmos/               # Algoritmos de planificación
│   ├── __init__.py
│   ├── fcfs.py              # First Come First Served
│   └── round_robin.py       # Round Robin con quantum
├── ipc/                      # Comunicación entre procesos
│   ├── __init__.py
│   ├── sincronizacion.py    # Semáforos y Productor-Consumidor
│   └── mensajes.py          # Buzón de mensajes
├── ui/                       # Interfaz gráfica y logging
│   ├── __init__.py
│   ├── menu.py              # Aplicación tkinter principal
│   └── logger.py            # Sistema de eventos y logs
└── test_imports.py          # Script de validación de módulos
```

## Componentes Principales

### core/
Contiene la lógica fundamental del simulador:
- **Proceso:** Define cada proceso con PID autogenerado, estados (listo, ejecutando, terminado), burst time y recursos.
- **Scheduler:** Orquesta la ejecución, mantiene la cola de listos, registra eventos y delega la planificación.
- **GestorRecursos:** Controla acceso a CPU (1 núcleo) y memoria (4096 MB).

### algoritmos/
Implementa los tres algoritmos de planificación:
- **FCFS:** Procesa en orden FIFO sin preemption.
- **Round Robin:** Preemptivo con quantum configurable, alterna procesos equitativamente.

### ipc/
Sincronización e IPC:
- **Semáforo:** Controla acceso a recursos compartidos.
- **ProductorConsumidor:** Demuestra el problema clásico con buffer sincronizado.
- **BuzonMensajes:** Permite comunicación asincrónica entre procesos.

### ui/
Interfaz y logging:
- **Menu:** Aplicación tkinter con:
  - Formulario de creación de procesos
  - Selector de algoritmo y quantum
  - Simulación automática y manual
  - Visualización de CPU, memoria, cola de listos
  - Panel de Productor-Consumidor con buffer visual
  - Logs categorizados por color
- **Logger:** Registro de eventos (PROCESO, RECURSO, ALGORITMO, IPC).

## Funcionalidades

### Gestión de Procesos
- Crear procesos con nombre, burst time, prioridad y memoria
- Suspender, reanudar y terminar procesos en tiempo real
- Visualizar estado de todos los procesos en tabla interactiva

### Algoritmos de Planificación
- Seleccionar algoritmo dinámicamente (FCFS, Round Robin)
- Configurar quantum para Round Robin
- Ejecutar ticks manuales o simulación automática

### Visualización
- Indicador CPU (verde=libre, rojo=ocupado)
- Barra de memoria con uso en tiempo real
- Cola de procesos listos ordenada
- Logs con eventos categorizados

### IPC
- Panel Productor-Consumidor con buffer visual
- Demostración de sincronización con semáforos
- Visualización del estado del buffer

## Uso del Simulador

1. **Crear procesos:** Ingresa nombre, burst time, prioridad y memoria. Presiona "Crear".
2. **Elegir algoritmo:** Usa el selector en la barra superior (FCFS, RoundRobin).
3. **Configurar quantum:** Para Round Robin, ajusta el valor y presiona Tick.
4. **Ejecutar:** Presiona "Tick Manual" para avanzar un paso o "Auto ON" para simulación continua.
5. **Observar:** Mira cómo los procesos cambian de estado según el algoritmo seleccionado.

## Validación

Para validar que todos los módulos se importan correctamente, ejecuta:
```bash
python test_imports.py
```

## Notas Técnicas

- Solo usa librerías estándar de Python (tkinter, threading, collections).
- Los ticks representan unidades de tiempo de CPU.
- El PID se autogenera secuencialmente.
- La memoria es limitada (4096 MB total).
- Solo una CPU disponible (monoprocesador).
- Los procesos pueden suspenderse/reanudarse manualmente, pero la planificación es automática según el algoritmo.
