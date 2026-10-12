import os
import sys
import subprocess
import platform
import venv
from pathlib import Path

# ------------------------------------------------------------
# Configuración
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()
os.chdir(PROJECT_ROOT)  # siempre trabaja desde la raíz del proyecto

VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
INSTANCIAS_DIR = PROJECT_ROOT / "instancias"
RESULTADOS_DIR = PROJECT_ROOT / "resultados"
IS_WINDOWS = platform.system() == "Windows"
PYTHON = sys.executable

# ------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------
def run(cmd, cwd=None):
    """Ejecuta un comando mostrando la salida en tiempo real."""
    print(f"\n> {' '.join(cmd)}\n")
    try:
        subprocess.run(cmd, check=True, cwd=cwd or PROJECT_ROOT)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[!] El comando terminó con código {e.returncode}")
        return False

def get_venv_python():
    """Ruta al intérprete dentro del venv (o el Python actual si no hay venv)."""
    if IS_WINDOWS:
        p = VENV_DIR / "Scripts" / "python.exe"
    else:
        p = VENV_DIR / "bin" / "python"
    return str(p) if p.exists() else PYTHON

def listar_instancias():
    """Devuelve la lista de archivos .txt en instancias/ (recursivo)."""
    if not INSTANCIAS_DIR.exists():
        return []
    return sorted([f for f in INSTANCIAS_DIR.rglob("*.txt") if f.is_file()])

def elegir_instancia():
    """Muestra las instancias disponibles y devuelve la ruta elegida."""
    instancias = listar_instancias()
    if not instancias:
        print("\n[!] No hay instancias en instancias/. Genera una primero (opción 5).")
        return None

    print("\nInstancias disponibles:")
    for i, f in enumerate(instancias, 1):
        try:
            rel = f.relative_to(INSTANCIAS_DIR)
        except ValueError:
            rel = f.name
        print(f"  {i:>2}. {rel}")

    entrada = input("\nElige el número (o escribe una ruta manual): ").strip()
    if not entrada:
        return None
    if entrada.isdigit():
        idx = int(entrada) - 1
        if 0 <= idx < len(instancias):
            return instancias[idx]
        print("[!] Número fuera de rango.")
        return None
    p = Path(entrada)
    if not p.is_absolute():
        if (PROJECT_ROOT / p).exists():
            p = PROJECT_ROOT / p
        elif (INSTANCIAS_DIR / p).exists():
            p = INSTANCIAS_DIR / p
    return p if p.exists() else None

def asegurar_carpeta_resultados():
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

def nombre_salida_sugerido(instancia: Path, agente: str) -> str:
    """Genera una ruta ABSOLUTA en resultados/ y garantiza que la carpeta exista."""
    asegurar_carpeta_resultados()
    base = instancia.stem
    destino = (RESULTADOS_DIR / f"sol_{agente}_{base}.txt").resolve()
    return str(destino)

# ------------------------------------------------------------
# Instalación
# ------------------------------------------------------------
def create_venv():
    if VENV_DIR.exists():
        print(f"[OK] El entorno virtual ya existe en {VENV_DIR}")
        return True
    print(f"Creando entorno virtual en {VENV_DIR} ...")
    try:
        venv.create(VENV_DIR, with_pip=True)
        print("[OK] Entorno virtual creado.")
        return True
    except Exception as e:
        print(f"[!] Error al crear el entorno virtual: {e}")
        return False

def install_dependencies():
    if not REQUIREMENTS.exists():
        print(f"[!] No se encontró {REQUIREMENTS}.")
        return False
    venv_python = get_venv_python()
    print("Instalando dependencias (pytest, matplotlib) ...")
    ok = run([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
    ok = run([venv_python, "-m", "pip", "install", "-r", str(REQUIREMENTS)]) and ok
    return ok

def setup_all():
    print("=== INSTALACIÓN DE TILEUP ===")
    return create_venv() and install_dependencies()

# ------------------------------------------------------------
# Comandos del CLI
# ------------------------------------------------------------
def cmd_run_agent():
    print("\n--- EJECUTAR AGENTE ---")
    instancia = elegir_instancia()
    if not instancia:
        return
    instancia = instancia.resolve()

    agente = (input("Agente [busqueda/evolutivo] (def. busqueda): ").strip().lower()
              or "busqueda")
    if agente not in ("busqueda", "evolutivo"):
        print("[!] Agente inválido.")
        return

    semilla = input("Semilla (def. 1): ").strip() or "1"
    tiempo = input("Tiempo límite en segundos (def. 10): ").strip() or "10"

    salida_default = nombre_salida_sugerido(instancia, agente)
    print(f"\nLa solución se guardará en:\n  {salida_default}")
    salida = input("Archivo de salida (Enter para usar el de arriba): ").strip()
    if not salida:
        salida = salida_default
    else:
        p = Path(salida)
        if p.parent == Path(".") or not p.is_absolute():
            asegurar_carpeta_resultados()
            salida = str((RESULTADOS_DIR / p.name).resolve())
            print(f"[i] Se interpretará como: {salida}")

    cmd = [get_venv_python(), "-m", "tileup.cli",
           "--instancia", str(instancia),
           "--agente", agente,
           "--semilla", semilla,
           "--tiempo", tiempo,
           "--salida", salida]

    if agente == "busqueda":
        w = input("Ancho del beam --w (def. 50): ").strip()
        if w:
            cmd += ["--w", w]
        beta = input("Peso lookahead --beta (def. 1.0): ").strip()
        if beta:
            cmd += ["--beta", beta]
    elif agente == "evolutivo":
        poblacion = input("Población --poblacion (def. 100): ").strip()
        if poblacion:
            cmd += ["--poblacion", poblacion]
        generaciones = input("Generaciones --generaciones (def. 400): ").strip()
        if generaciones:
            cmd += ["--generaciones", generaciones]

    run(cmd)

    destino = Path(salida)
    if destino.exists():
        print(f"\n[OK] Solución guardada en: {destino}")
    else:
        print(f"\n[!] No se encontró {destino}")
        alterno = PROJECT_ROOT / destino.name
        if alterno.exists():
            print(f"[i] Se encontró en {alterno}, moviendo a resultados/ ...")
            asegurar_carpeta_resultados()
            nuevo = RESULTADOS_DIR / destino.name
            alterno.replace(nuevo)
            print(f"[OK] Movido a: {nuevo}")
        else:
            print("[!] El CLI no generó ningún archivo. Revisa el error de arriba.")

def cmd_full():
    """Corre ambos agentes sobre la instancia y luego la batería experimental."""
    print("\n--- AMBOS AGENTES Y COMPARADOR (--full) ---")
    instancia = elegir_instancia()
    if not instancia:
        return
    instancia = instancia.resolve()

    semilla = input("Semilla (def. 1): ").strip() or "1"
    tiempo = input("Tiempo límite en segundos (def. 10): ").strip() or "10"

    print("\n[i] Se ejecutará en este orden:")
    print("    1. Agente de búsqueda sobre la instancia elegida")
    print("    2. Agente evolutivo sobre la misma instancia")
    print("    3. Comparación lado a lado de la instancia")
    print("    4. Batería experimental completa (comparacion_experimental)")
    print()
    confirmar = input("¿Continuar? (s/n, def. s): ").strip().lower() or "s"
    if confirmar != "s":
        print("[i] Cancelado.")
        return

    # --salida la usa el modo --full para los archivos sol_busqueda_*.txt
    # y sol_evolutivo_*.txt. La ponemos en resultados/.
    asegurar_carpeta_resultados()
    salida_base = str((RESULTADOS_DIR / "solucion").resolve())

    cmd = [get_venv_python(), "-m", "tileup.cli",
           "--instancia", str(instancia),
           "--full",
           "--semilla", semilla,
           "--tiempo", tiempo,
           "--salida", salida_base]

    run(cmd)

def cmd_validate():
    print("\n--- VALIDAR SOLUCIÓN ---")
    instancia = elegir_instancia()
    if not instancia:
        return

    soluciones = sorted(RESULTADOS_DIR.glob("*.txt")) if RESULTADOS_DIR.exists() else []
    if soluciones:
        print("\nSoluciones disponibles en resultados/:")
        for i, s in enumerate(soluciones, 1):
            print(f"  {i:>2}. {s.name}")
        print("  (o escribe una ruta manual)")

    entrada = input("Solución a validar: ").strip()
    if not entrada:
        return
    if entrada.isdigit():
        idx = int(entrada) - 1
        if 0 <= idx < len(soluciones):
            solucion = soluciones[idx]
        else:
            print("[!] Número fuera de rango.")
            return
    else:
        solucion = Path(entrada)
        if not solucion.is_absolute():
            if (PROJECT_ROOT / solucion).exists():
                solucion = PROJECT_ROOT / solucion
            elif (RESULTADOS_DIR / solucion).exists():
                solucion = RESULTADOS_DIR / solucion

    run([get_venv_python(), "-m", "tileup.validador", str(instancia), str(solucion)])

def cmd_generate_instance():
    print("\n--- GENERAR INSTANCIA ---")
    n = input("Tamaño del tablero N (def. 6): ").strip() or "6"
    k = input("Cantidad de colores K (def. 4): ").strip() or "4"
    m = input("Cantidad de fichas M (def. 60): ").strip() or "60"
    semilla = input("Semilla (def. 7): ").strip() or "7"
    nombre = input("Nombre del archivo (def. mi_instancia.txt): ").strip() or "mi_instancia.txt"
    if not nombre.endswith(".txt"):
        nombre += ".txt"
    INSTANCIAS_DIR.mkdir(parents=True, exist_ok=True)
    salida = INSTANCIAS_DIR / nombre

    code = (
        f"from tileup.generador_instancias import escribir_instancia; "
        f"escribir_instancia(r'{salida}', n={n}, k={k}, m={m}, semilla={semilla})"
    )
    if run([get_venv_python(), "-c", code]):
        if salida.exists():
            print(f"\n[OK] Instancia creada en: {salida}")
        else:
            print(f"\n[!] No se encontró {salida}. Revisa el error de arriba.")

def cmd_ver_soluciones():
    print("\n--- SOLUCIONES EN resultados/ ---")
    asegurar_carpeta_resultados()
    soluciones = sorted(RESULTADOS_DIR.glob("*.txt"))
    if not soluciones:
        print("No hay soluciones todavía.")
        sueltas = [f for f in PROJECT_ROOT.glob("sol*.txt") if f.is_file()]
        if sueltas:
            print("\n[i] Encontré soluciones en la raíz del proyecto:")
            for f in sueltas:
                print(f"    {f.name}")
            resp = input("¿Moverlas a resultados/? (s/n): ").strip().lower()
            if resp == "s":
                for f in sueltas:
                    f.replace(RESULTADOS_DIR / f.name)
                print("[OK] Movidas.")
        return

    for i, s in enumerate(soluciones, 1):
        tam = s.stat().st_size
        print(f"  {i:>2}. {s.name}  ({tam} bytes)")

    print("\nElige un número para VALIDAR (o 'v' para ver contenido, Enter para salir):")
    entrada = input("> ").strip().lower()
    if entrada == "v":
        for s in soluciones:
            print(f"\n--- {s.name} ---")
            print(s.read_text(encoding="utf-8"))
        return
    if not entrada.isdigit():
        return
    idx = int(entrada) - 1
    if not (0 <= idx < len(soluciones)):
        print("[!] Número fuera de rango.")
        return

    sol = soluciones[idx]
    partes = sol.stem.split("_", 2)
    base = partes[2] if len(partes) >= 3 else sol.stem
    candidato = INSTANCIAS_DIR / f"{base}.txt"
    if not candidato.exists():
        print(f"[!] No se encontró la instancia {candidato}. Elígela manualmente.")
        instancia = elegir_instancia()
        if not instancia:
            return
    else:
        instancia = candidato
    run([get_venv_python(), "-m", "tileup.validador", str(instancia), str(sol)])

# ------------------------------------------------------------
# Pruebas automatizadas
# ------------------------------------------------------------
def cmd_run_all_tests():
    print("\n--- TODAS LAS PRUEBAS (verbose) ---")
    run([get_venv_python(), "-m", "pytest", "-v"])

def cmd_run_all_tests_quiet():
    print("\n--- TODAS LAS PRUEBAS (resumen) ---")
    run([get_venv_python(), "-m", "pytest", "-q"])

def cmd_run_unit_tests():
    print("\n--- PRUEBAS UNITARIAS (motor, validador) ---")
    run([get_venv_python(), "-m", "pytest", "tests/test_motor.py", "tests/test_validador.py", "-v"])

def cmd_run_integration_tests():
    print("\n--- PRUEBAS DE INTEGRACIÓN ---")
    run([get_venv_python(), "-m", "pytest", "tests/test_integracion.py", "-v"])

def cmd_run_agentes_tests():
    print("\n--- PRUEBAS DE AGENTES ---")
    run([get_venv_python(), "-m", "pytest", "tests/test_agentes.py", "-v"])

def cmd_run_specific_test():
    print("\n--- PRUEBA ESPECÍFICA ---")
    opciones = [
        "tests/test_motor.py",
        "tests/test_validador.py",
        "tests/test_agentes.py",
        "tests/test_integracion.py",
    ]
    for i, o in enumerate(opciones, 1):
        print(f"  {i}. {o}")
    print("  m. escribir ruta manual")
    entrada = input("Elige (1-4 o m): ").strip().lower()
    if entrada == "m":
        archivo = input("Ruta del archivo de prueba: ").strip()
    elif entrada.isdigit() and 1 <= int(entrada) <= len(opciones):
        archivo = opciones[int(entrada) - 1]
    else:
        print("[!] Opción inválida.")
        return
    if archivo:
        run([get_venv_python(), "-m", "pytest", archivo, "-v"])

def cmd_run_by_name():
    print("\n--- BUSCAR PRUEBA POR NOMBRE ---")
    patron = input("Parte del nombre del test (ej. fusion, derrota, semilla): ").strip()
    if patron:
        run([get_venv_python(), "-m", "pytest", "-v", "-k", patron])

# ------------------------------------------------------------
# Menú interactivo
# ------------------------------------------------------------
def show_menu():
    print("\n" + "=" * 56)
    print("  MENÚ TILEUP")
    print("=" * 56)
    print("  --- Instalación ---")
    print("   1. Instalar todo (entorno + dependencias)")
    print()
    print("  --- Agentes ---")
    print("   2. Ejecutar agente (búsqueda / evolutivo)")
    print("   3. Ambos agentes y comparador (--full)")
    print("   4. Validar una solución")
    print("   5. Generar instancia")
    print("   6. Ver y validar soluciones en resultados/")
    print()
    print("  --- Pruebas automatizadas ---")
    print("   7. Todas las pruebas (verbose, línea por test)")
    print("   8. Todas las pruebas (resumen)")
    print("   9. Pruebas unitarias (motor + validador)")
    print("  10. Pruebas de integración")
    print("  11. Pruebas de agentes")
    print("  12. Elegir archivo de prueba específico")
    print("  13. Buscar prueba por nombre (-k)")
    print()
    print("   0. Salir")
    print("-" * 56)

def menu_loop():
    while True:
        show_menu()
        opcion = input("Elige una opción: ").strip()

        if opcion == "1":
            setup_all()
        elif opcion == "2":
            cmd_run_agent()
        elif opcion == "3":
            cmd_full()
        elif opcion == "4":
            cmd_validate()
        elif opcion == "5":
            cmd_generate_instance()
        elif opcion == "6":
            cmd_ver_soluciones()
        elif opcion == "7":
            cmd_run_all_tests()
        elif opcion == "8":
            cmd_run_all_tests_quiet()
        elif opcion == "9":
            cmd_run_unit_tests()
        elif opcion == "10":
            cmd_run_integration_tests()
        elif opcion == "11":
            cmd_run_agentes_tests()
        elif opcion == "12":
            cmd_run_specific_test()
        elif opcion == "13":
            cmd_run_by_name()
        elif opcion == "0":
            print("Saliendo...")
            break
        else:
            print("[!] Opción no válida.")

# ------------------------------------------------------------
# Punto de entrada
# ------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        sys.exit(0 if setup_all() else 1)
    else:
        if not VENV_DIR.exists():
            print("[!] No se ha detectado un entorno virtual.")
            resp = input("¿Quieres ejecutar la instalación ahora? (s/n): ").strip().lower()
            if resp == "s":
                setup_all()
        menu_loop()