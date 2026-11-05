# Herramientas y scripts

## `diagnostico_wsl2_v6_1.py`

Versión **6.1** del script original utilizado por el grupo. Ejecuta 25 comprobaciones de **diagnóstico**, no 25 pruebas funcionales independientes.

### Ejecución

Desde la raíz del repositorio, en Ubuntu sobre WSL2:

```bash
python3 scripts/diagnostico_wsl2_v6_1.py
```

La salida se crea en `~/resultados_wsl2/AAAAmmdd_HHMMSS/` y contiene archivos `.txt`, `resumen.csv` y `metadatos.json`.

### Cómo interpretar el resultado

- `CONFIG_BLK_DEV_LOOP=y`: soporte de `loop` integrado en el kernel. La operación con `losetup` se probó **manualmente** por separado.
- `modinfo loop` sin un `.ko`: no demuestra por sí solo ausencia de `loop`.
- `/dev/kvm` ausente: dispositivo no expuesto al momento de la consulta; no se identifica la causa raíz.
- `modprobe -n -v`: **simulación de carga**, no carga efectiva del módulo.
- USB: la enumeración en Linux y la lista de Windows no equivalen a transferencia, montaje ni acceso a todos los dispositivos. El uso de `usbipd-win` se documentó manualmente.

El código de la versión adjuntada hace consultas **específicas de `kvm_amd`** en sus pruebas modulares. No generalizar esas comprobaciones a Intel sin adaptarlas.

### Alcance y seguridad

No utiliza `sudo`, no carga módulos, no monta dispositivos ni ejecuta `usbipd attach`. **Sí escribe archivos de evidencia** en el directorio personal del usuario. Revisar la salida antes de publicarla, porque podría incluir identificadores y detalles locales del sistema.

### Material pendiente

El script original usado para filtrar el CSV de vuelos todavía no está incluido; no se ha reconstruido ni sustituido por un programa inventado.
