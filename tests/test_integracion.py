import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_cli(args, cwd=ROOT):
    return subprocess.run(
        [sys.executable, "-m", "tileup.cli"] + args,
        capture_output=True, text=True, cwd=cwd,
    )


def test_integracion_busqueda(tmp_path):
    inst = tmp_path / "i.txt"
    inst.write_text("3 2\n4\n1 5\n1 7\n2 3\n2 4\n")
    sol = tmp_path / "sol.txt"

    r = _run_cli([
        "--instancia", str(inst),
        "--agente", "busqueda",
        "--semilla", "42",
        "--tiempo", "5",
        "--salida", str(sol),
    ])
    assert r.returncode == 0, r.stderr
    assert sol.exists()

    from tileup.motor import leer_instancia
    from tileup.validador import validar
    instancia = leer_instancia(str(inst))
    ok, msg, metrics = validar(instancia, str(sol))
    assert ok, msg
    assert metrics["colocadas"] == 4


def test_integracion_evolutivo(tmp_path):
    inst = tmp_path / "i.txt"
    inst.write_text("3 2\n4\n1 5\n1 7\n2 3\n2 4\n")
    sol = tmp_path / "sol.txt"

    r = _run_cli([
        "--instancia", str(inst),
        "--agente", "evolutivo",
        "--semilla", "7",
        "--tiempo", "5",
        "--salida", str(sol),
    ])
    assert r.returncode == 0, r.stderr
    assert sol.exists()

    from tileup.motor import leer_instancia
    from tileup.validador import validar
    instancia = leer_instancia(str(inst))
    ok, msg, metrics = validar(instancia, str(sol))
    assert ok, msg
    assert metrics["colocadas"] > 0