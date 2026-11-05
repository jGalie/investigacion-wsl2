# Laboratorio 03 - Integración de sistemas de archivos

**Objetivo:** comparar integridad, tiempo de procesamiento y permisos de un mismo archivo cuando está en el sistema de archivos Linux (`/home`) y en la unidad Windows montada (`/mnt/c`).

**Datos empleados en el informe:** CSV de vuelos de enero de 2025, 243.177.378 bytes, 539.748 líneas incluido el encabezado. Se identificaron 8.327 vuelos con origen JFK.

**Método:**

1. Copiar el mismo CSV a ambas ubicaciones.
2. Calcular `sha256sum` de las dos copias y comprobar igualdad.
3. Ejecutar el mismo script Python de filtrado **cinco veces por ubicación** y registrar tiempos.
4. Examinar permisos y comparar el efecto observado de `chmod 600` sobre copias temporales.

**Resultado observado:** tiempos medios de 4,66 s en `/home` y 10,71 s en `/mnt/c`, aproximadamente 2,3 veces más en esta última ubicación **en el procesamiento ensayado**. En `/home` se observaron permisos `rw-------` después de `chmod 600`; en `/mnt/c` permanecieron `rwxrwxrwx` según la configuración de montaje utilizada.

**Alcance:** no es una comparación general de velocidad de Windows contra Linux. Ambas ejecuciones fueron dentro de Ubuntu/WSL2 y cambiaba la ubicación del archivo. No se documentó en este paquete el script original de filtrado ni el origen descargable del CSV; ver [`datos/README.md`](../datos/README.md).

**Evidencias:** figuras 10 a 13 del informe.

**Referencia:** [Microsoft: sistemas de archivos de WSL](https://learn.microsoft.com/es-es/windows/wsl/filesystems).
