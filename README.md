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
└── evidencias/            # Capturas y logs de ejecución
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

3. **Generar el dataset local (si no existe):**
   ```bash
   python generar_dataset.py 125053184
   ```
   *Nota: El dataset `ventas_125053184.csv` (~400 MB) debe colocarse o moverse a la ruta `data/output/` para ser consumido.*

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

## 3. Endpoints de la API (FastAPI)

Una vez desplegada, la API está disponible en `http://localhost:8000`:

* **`GET /resultados`**: Consulta todos los registros de la tabla datamart (`metodo_pago`, `dia_semana`, `unidades_vendidas`).
* **`GET /resultados/{metodo_pago}`**: Filtra los registros por un método de pago específico (ej. `/resultados/Tarjeta`).
* **`GET /resultados/{metodo_pago}/{dia_semana}`**: Filtra específicamente por combinación (ej. `/resultados/Tarjeta/Martes`).
* **`POST /resultados`**: Endpoint de escritura del CRUD para agregar o actualizar registros.
* **Documentación Swagger UI**: `http://localhost:8000/docs`

---

## 4. Comparativa de Rendimiento (MapReduce vs Secuencial)

- **Hadoop MapReduce Streaming:** ~32.4 segundos  
- **Script Secuencial en Python:** ~18.2 segundos  

### Explicación
Para un dataset de 400 MB (5 millones de registros), el script secuencial es más rápido debido al costo de sobrecarga (*overhead*) que implica Hadoop MapReduce al inicializar la Máquina Virtual de Java (JVM), distribuir los procesos de Map y Reduce, gestionar operaciones de I/O en disco para el ordenamiento (*shuffle & sort*) y coordinar la comunicación entre procesos. MapReduce comienza a superar el rendimiento del enfoque secuencial a partir de archivos en el orden de los *gigabytes* o *terabytes* procesados en clústeres multinodo, donde el paralelismo real justifica la sobrecarga de orquestación.

---

## 5. Parte E - Cuestionario Teórico

1. **Diferencia entre modos Standalone, Pseudo-distribuido y Totalmente distribuido:**  
   - **Standalone:** Ejecuta Hadoop en un solo proceso Java sin demonios corriendo ni HDFS (usa el sistema de archivos local).  
   - **Pseudo-distribuido:** Ejecuta todos los demonios de Hadoop (NameNode, DataNode, ResourceManager, NodeManager) como procesos independientes en una sola máquina; **sí utiliza HDFS**.  
   - **Totalmente distribuido:** Distribuye los demonios y el almacenamiento entre múltiples nodos físicos/virtuales en un clúster; **utiliza HDFS de forma distribuida**.

2. **¿Por qué el dataset se monta como volumen y no con `COPY` en el Dockerfile?**  
   - **Razón 1:** Evita inflar innecesariamente el tamaño de la imagen Docker en 400 MB+, haciendo la construcción y distribución de la imagen lenta e ineficiente.  
   - **Razón 2:** Permite la modificación o regeneración del dataset dinámicamente en el host sin necesidad de reconstruir la imagen de Docker cada vez.

3. **Diferencia entre `docker compose down` y `docker compose down -v`:**  
   - `docker compose down`: Detiene y elimina los contenedores, redes y elementos creados, pero **mantiene los volúmenes nombrados** (los datos en la base de datos persisten).  
   - `docker compose down -v`: Detiene todo y **elimina también los volúmenes nombrados**, borrando de forma permanente la base de datos y toda la información almacenada.

4. **¿Por qué MapReduce no siempre es más rápido que un script secuencial en 400 MB?**  
   - Por la sobrecarga (*overhead*) de inicialización del framework MapReduce (arranque de JVM, división de splits, fase de *Shuffle & Sort* escribiendo a disco). En volúmenes de datos pequeños (como 400 MB), la memoria RAM local y la ejecución secuencial leen y procesan el archivo directamente sin esa sobrecarga. Conviene usarlo cuando el volumen supera la capacidad de memoria de una sola máquina (múltiples GBs/TBs) y se requiere un clúster distribuido.

5. **Diferencias entre `CMD` vs `ENTRYPOINT` y `COPY` vs `ADD`:**  
   - **CMD vs ENTRYPOINT:** `ENTRYPOINT` establece el ejecutable principal e inmutable que se correrá al arrancar el contenedor, mientras que `CMD` provee los argumentos por defecto (o un comando sobreescribible desde la línea de comandos de Docker).  
   - **COPY vs ADD:** `COPY` copia archivos/directorios locales directamente al contenedor. `ADD` hace lo mismo pero además soporta la descarga de URLs remotas y la extracción automática de archivos comprimidos (`.tar.gz`, `.zip`).