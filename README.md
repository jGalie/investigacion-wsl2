# Análisis experimental de WSL2

**Arquitectura, conectividad y limitaciones de Windows Subsystem for Linux 2 (WSL2)**

Trabajo de investigación para **Redes de Datos**, Facultad de Ciencias Exactas y Naturales y Agrimensura, **Universidad Nacional del Nordeste (UNNE)**.

**Integrantes:** Leonardo Oscar Canteros, Facundo Nicolás Fernandez, Julieta Itatí Gauna y Juan Agustín Ojeda.

## Pregunta de investigación

> ¿Hasta qué punto WSL2 permite trabajar con Linux desde Windows y qué funcionalidades dependen de la integración entre ambos sistemas?

El proyecto documenta cinco ámbitos experimentales: identificación de la arquitectura y del kernel, conectividad de red, integración de archivos, hardware/dispositivos y persistencia de servicios. Se diferencia entre **soporte configurado**, **recurso expuesto** y **operación funcional comprobada**; un error de diagnóstico no se interpreta automáticamente como una incompatibilidad de WSL2.

## Entorno principal de pruebas

| Componente | Configuración del artículo |
| --- | --- |
| Anfitrión | Windows 11 |
| WSL | 3.0.3.0; versión 2 de la distribución |
| Distribución | Ubuntu 22.04.5 LTS |
| Kernel | `6.18.54.1-microsoft-standard-WSL2` |
| Procesador | AMD Ryzen 5 5625U |
| Memoria RAM | 16 GB |
| Pruebas de red | Equipo anfitrión y segunda computadora en la misma LAN |

## Experimentos y hallazgos

| Laboratorio | Qué se verificó | Resultado acotado al entorno |
| --- | --- | --- |
| [01 - Arquitectura](laboratorios/01-arquitectura.md) | Versión de WSL, Ubuntu, kernel y PID 1 | Kernel Linux real y `systemd` como PID 1 |
| [02 - Conectividad](laboratorios/02-conectividad.md) | Nginx en NAT y mirrored, acceso desde la LAN | NAT requirió redirección y firewall; mirrored requirió permitir tráfico en firewall Hyper-V |
| [03 - Archivos](laboratorios/03-archivos.md) | Integridad, rendimiento de un CSV y permisos | SHA-256 coincidente; promedio 4,66 s en `/home` y 10,71 s en `/mnt/c` (5 ejecuciones por ubicación) |
| [04 - Hardware](laboratorios/04-hardware.md) | Kernel/`loop`, KVM y USB | `loop` asociado y leído correctamente; `/dev/kvm` ausente; dispositivo USB enumerado después de `usbipd-win` |
| [05 - Persistencia](laboratorios/05-persistencia.md) | Estado de Nginx y ciclo de vida de WSL | La distribución pasó a `Stopped` tras cerrar la última sesión pese a que Nginx estaba habilitado y activo previamente |

**Alcance:** estos son resultados del entorno estudiado. No se comparó Windows nativo contra Linux nativo ni se demostró una incapacidad general de WSL2 para utilizar KVM.

## Herramienta Python de diagnóstico

El grupo desarrolló [`diagnostico_wsl2_v6_1.py`](scripts/diagnostico_wsl2_v6_1.py), un programa de Python 3 que ejecuta **25 comprobaciones** sobre módulos, virtualización KVM y dispositivos USB. Consulta el estado del sistema sin cargar módulos ni conectar dispositivos; almacena un `resumen.csv`, `metadatos.json` y evidencia textual por comprobación en `~/resultados_wsl2/`.

Para usarla **en Ubuntu sobre WSL2**:

```bash
python3 scripts/diagnostico_wsl2_v6_1.py
```

Se requieren las herramientas consultadas por el script para obtener todos sus resultados (`lsmod`, `modinfo`, `modprobe`, `lscpu`, `lsusb`, entre otras). La ausencia de alguna utilidad se registra como tal; no equivale a una restricción de WSL2. El diagnóstico **no ejecuta** las pruebas manuales con `losetup`, `usbipd attach` ni `systemd`.

Véase [la explicación detallada del programa](scripts/README.md).

## Documentos y reproducibilidad

- [`docs/borradores/informe.pdf`](docs/borradores/informe.pdf): última copia disponible del artículo, **pendiente de confirmar como versión final**.
- [`docs/borradores/presentacion.pdf`](docs/borradores/presentacion.pdf): última presentación adjuntada, **pendiente de revisión**.
- [`laboratorios/`](laboratorios/): procedimientos y alcance de cada experimento.
- [`datos/README.md`](datos/README.md): metadatos del conjunto CSV y pendientes para reproducir el filtrado.
- [`evidencias/README.md`](evidencias/README.md): criterios para incorporar capturas y registros depurados.

**Pendientes para publicación definitiva:** confirmar el informe corregido y la presentación definitiva; incorporar el script original de filtrado de vuelos y el origen verificable del CSV, si el grupo los proporciona; revisar datos personales en las capturas. No se incluyen capturas aisladas ni datos brutos sin revisión.

## Fuentes de consulta

Documentación oficial de Microsoft: [Descripción de WSL](https://learn.microsoft.com/es-es/windows/wsl/about), [Comparación entre WSL1 y WSL2](https://learn.microsoft.com/es-es/windows/wsl/compare-versions), [Redes](https://learn.microsoft.com/es-es/windows/wsl/networking), [Sistemas de archivos](https://learn.microsoft.com/es-es/windows/wsl/filesystems), [Configuración](https://learn.microsoft.com/es-es/windows/wsl/wsl-config), [USB](https://learn.microsoft.com/es-es/windows/wsl/connect-usb) y [systemd](https://learn.microsoft.com/es-es/windows/wsl/systemd).

Reportes de comunidad que motivaron verificaciones específicas: [WSL #11170 (`loop` y particiones)](https://github.com/microsoft/WSL/issues/11170), [WSL #41917 (virtualización anidada)](https://github.com/microsoft/WSL/issues/41917) y [usbipd-win #882 (USB y mirrored)](https://github.com/dorssel/usbipd-win/issues/882). Son reportes de configuraciones particulares y no establecen restricciones universales.

## Publicación y licencia

Repositorio de destino previsto: `jGalie/investigacion-wsl2`, **público**. Los documentos dentro de `docs/borradores/` no deben presentarse como versiones definitivas. **No se asignó una licencia de software:** antes de publicarla, los integrantes deberían acordar los permisos de reutilización del código y los materiales.
