# Examen Parcial 2 - Pipeline DataMart (Hadoop MapReduce, PostgreSQL & FastAPI)

**Matrícula:** `125053184`  
**Pregunta de negocio asignada (Dígito 4):** Unidades vendidas por método de pago y día de la semana.

---

## 1. Estructura del Repositorio

```text
examen-p2-125053184/
├── README.md              # Documentación completa y evidencias
├── .gitignore             # Ignora datasets *.csv y archivos temporales
├── .env.example           # Plantilla de variables de entorno
├── docker-compose.yml     # Orquestación de servicios
├── hadoop/
│   └── Dockerfile         # Imagen base Hadoop + SSH
├── mapreduce/
│   ├── mapper.py          # Mapper para parsing y agregación
│   ├── reducer.py          # Reducer para suma acumulada
│   └── secuencial.py     # Script secuencial de benchmark
├── api/
│   ├── Dockerfile         # Contenedor para FastAPI
│   ├── main.py            # Servidor FastAPI y endpoints CRUD
│   └── requirements.txt   # Dependencias de Python
├── scripts/
│   └── cargar_resultados.py # Carga masiva de part-00000 a PostgreSQL
└── evidencias/            # Capturas de pantalla
    ├── hadoop_version.png
    ├── ssh_conexion.png
    ├── salida_job.png
    └── api_respuesta.png
```

---

## 2. Pasos para Reproducir el Proyecto

### Requisitos previos
- Docker Desktop instalado y en ejecución.
- Git y PowerShell / Terminal.

### Despliegue de la Infraestructura
1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TU_USUARIO/examen-p2-125053184.git](https://github.com/TU_USUARIO/examen-p2-125053184.git)
   cd examen-p2-125053184
   ```

2. **Configurar variables de entorno:**
   ```bash
   cp .env.example .env
   ```

3. **Generar el dataset local:**
   ```bash
   python generar_dataset.py 125053184
   ```

4. **Levantar todo el entorno con un solo comando:**
   ```bash
   docker compose up --build -d
   ```

5. **Cargar los datos procesados en PostgreSQL:**
   ```bash
   docker cp .\data\output\resultado\part-00000 datamart-db:/tmp/part-00000
   docker exec -it datamart-db psql -U datamart_user -d datamart -c "TRUNCATE TABLE resultados_ventas; CREATE TEMP TABLE tmp (metodo_pago VARCHAR(50), dia_semana VARCHAR(20), unidades_vendidas INT); COPY tmp FROM '/tmp/part-00000' WITH (FORMAT csv, DELIMITER E'\t'); INSERT INTO resultados_ventas (metodo_pago, dia_semana, unidades_vendidas) SELECT metodo_pago, dia_semana, SUM(unidades_vendidas) FROM tmp GROUP BY metodo_pago, dia_semana ON CONFLICT (metodo_pago, dia_semana) DO UPDATE SET unidades_vendidas = EXCLUDED.unidades_vendidas;"
   ```

---

## 3. Evidencias de Funcionamiento

### A1. Validación de Hadoop Version
![Hadoop Version](evidencias/hadoop_version.png)

### B. Conexión SSH sin Contraseña
![SSH sin contraseña](evidencias/ssh_conexion.png)

### C1. Salida del Job MapReduce (`part-00000`)
![Salida MapReduce](evidencias/salida_job.png)

### D. Respuesta de la API (Endpoints GET y POST)
![Respuesta API](evidencias/api_respuesta.png)

---

## 4. Endpoints de la API (FastAPI)

Una vez desplegada, la API está disponible en `http://localhost:8000`:

* **`GET /resultados`**: Consulta todos los registros (`metodo_pago`, `dia_semana`, `unidades_vendidas`).
* **`GET /resultados/{metodo_pago}`**: Filtra por método de pago (ej. `/resultados/Tarjeta`).
* **`GET /resultados/{metodo_pago}/{dia_semana}`**: Filtra combinación específica (ej. `/resultados/Tarjeta/Martes`).
* **`POST /resultados`**: Endpoint de escritura para insertar/actualizar registros.
* **Swagger UI**: `http://localhost:8000/docs`

---

## 5. Comparativa de Rendimiento (Tiempos Medidos)

- **Hadoop MapReduce Streaming:** ~32.4 segundos  
- **Script Secuencial en Python:** ~18.2 segundos  

### Explicación
Para un dataset de 400 MB (5 millones de registros), el script secuencial en Python resulta más rápido debido a la sobrecarga (*overhead*) implícita en Hadoop MapReduce. Esta sobrecarga abarca la inicialización de la JVM, la asignación de contenedores, la distribución de procesos de Map y Reduce y las operaciones de lectura/escritura en disco durante la fase de *Shuffle & Sort*. MapReduce demuestra superioridad a partir de volúmenes en la escala de gigabytes o terabytes procesados en clústeres distribuídos.

---

## 6. Parte E - Cuestionario Teórico

1. **Diferencia entre modos Standalone, Pseudo-distribuido y Totalmente distribuido:**  
   - **Standalone:** Ejecuta Hadoop en un único proceso Java local sin demonios activos ni HDFS.  
   - **Pseudo-distribuido:** Ejecuta todos los demonios (NameNode, DataNode, ResourceManager) como procesos independientes en una sola máquina; **utiliza HDFS**.  
   - **Totalmente distribuido:** Distribuye los demonios y el almacenamiento entre un conjunto de nodos físicos o virtuales en clúster; **utiliza HDFS distribuido**.

2. **¿Por qué el dataset se monta como volumen y no con `COPY`?**  
   - **Razón 1:** Evita incrementar el tamaño de la imagen Docker en más de 400 MB, agilizando su construcción y distribución.  
   - **Razón 2:** Permite modificar o actualizar los datos de origen dinámicamente desde el host sin necesidad de reconstruir la imagen de Docker.

3. **Diferencia entre `docker compose down` y `docker compose down -v`:**  
   - `docker compose down`: Elimina contenedores y redes, **preservando los volúmenes nombrados** (los datos en la BD persisten).  
   - `docker compose down -v`: Elimina contenedores, redes y **destruye los volúmenes nombrados**, borrando la información en la base de datos de manera definitiva.

4. **¿Por qué MapReduce no siempre es más rápido que un script secuencial en 400 MB?**  
   - Por el costo de inicialización y orquestación del framework (inicio de JVM, división de splits, fase de *Shuffle & Sort* en disco). En volúmenes moderados (400 MB), la lectura secuencial directa en RAM procesa las líneas sin esa sobrecarga administrativa.

5. **Diferencias entre `CMD` vs `ENTRYPOINT` y `COPY` vs `ADD`:**  
   - **CMD vs ENTRYPOINT:** `ENTRYPOINT` fija el comando ejecutable base del contenedor, mientras que `CMD` provee argumentos por defecto que pueden ser anulados desde la CLI.  
   - **COPY vs ADD:** `COPY` transfiere archivos locales al contenedor. `ADD` añade capacidad para extraer automáticamente archivos comprimidos (`.tar.gz`, `.zip`) y descargar desde URLs remotas.
