#!/usr/bin/env python3
import sys
from datetime import datetime

DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    parts = line.split(",")
    if parts[0] == "id" or len(parts) < 8:
        continue

    try:
        fecha_str = parts[1]
        cantidad = int(parts[5])
        metodo_pago = parts[7].strip()

        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        dia_semana = DIAS[dt.weekday()]

        print(f"{metodo_pago}\t{dia_semana}\t{cantidad}")
    except (ValueError, IndexError):
        continue