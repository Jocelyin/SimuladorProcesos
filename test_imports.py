import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.scheduler import Scheduler
    print("✓ Scheduler importado")
    
    from core.proceso import Proceso
    print("✓ Proceso importado")
    
    from ipc.sincronizacion import ProductorConsumidor
    print("✓ ProductorConsumidor importado")
    
    from ui.logger import Logger
    print("✓ Logger importado")
    
    print("\n✓ Todos los módulos se importaron correctamente")
    
    # Test básico
    scheduler = Scheduler()
    print(f"✓ Scheduler instanciado (tick={scheduler.tick})")
    
    proceso = Proceso("test", 5, 10, 512)
    print(f"✓ Proceso creado (PID={proceso.pid})")
    
    scheduler.agregar_proceso(proceso)
    print(f"✓ Proceso agregado a scheduler")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()