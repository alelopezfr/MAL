#!/usr/bin/env python3
import sys

current_key = None
current_count = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    parts = line.split("\t")
    if len(parts) != 3:
        continue

    metodo_pago, dia_semana, cantidad_str = parts
    key = f"{metodo_pago}\t{dia_semana}"

    try:
        cantidad = int(cantidad_str)
    except ValueError:
        continue

    if current_key == key:
        current_count += cantidad
    else:
        if current_key:
            mp, ds = current_key.split("\t")
            print(f"{mp}\t{ds}\t{current_count}")
        current_key = key
        current_count = cantidad

if current_key:
    mp, ds = current_key.split("\t")
    print(f"{mp}\t{ds}\t{current_count}")