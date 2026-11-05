# Laboratorio 04 - Kernel, `loop`, KVM y USB

**Objetivo:** distinguir soporte configurado, recursos disponibles y operaciones que funcionan realmente. La selección de estos puntos se apoyó en reportes puntuales de usuarios de WSL/usbipd-win, **no** en la suposición de incompatibilidades generales.

## Herramienta de diagnóstico

El script [`diagnostico_wsl2_v6_1.py`](../scripts/diagnostico_wsl2_v6_1.py) realiza 25 comprobaciones automatizadas de módulos, KVM y USB, y guarda evidencia en CSV/JSON/TXT. **No carga módulos, no adjunta USB ni prueba la lectura `loop`**.

## `loop`

1. `modinfo loop` devolvió `Module loop not found`.
2. `CONFIG_BLK_DEV_LOOP=y`, recuperado desde `/proc/config.gz`, indicó soporte integrado en el kernel.
3. Se probó manualmente una asociación de un archivo temporal de 16 MiB con un dispositivo `loop` y una lectura de 1 MiB:

```bash
IMG=$(mktemp "$HOME/prueba_loop_XXXXXX.img")
truncate -s 16M "$IMG"
DEVICE=$(sudo losetup --find --show "$IMG")
echo "Dispositivo asignado: $DEVICE"
sudo losetup -j "$IMG"
sudo dd if="$DEVICE" of=/dev/null bs=1M count=1 status=none && echo "LECTURA_LOOP_OK"
# Limpiar después de guardar evidencia:
sudo losetup -d "$DEVICE"
rm -- "$IMG"
```

**Resultado:** asociación con `/dev/loop0` y lectura exitosa para las operaciones evaluadas. No se probó aquí el montaje de un sistema de archivos ni la exposición de particiones.

## KVM

- Se observaron `CONFIG_KVM=m`, `CONFIG_KVM_AMD=m` y la existencia de archivos de módulos.
- No se observaron módulos KVM cargados ni la extensión `svm`; `/dev/kvm` estaba ausente.
- `modprobe -n -v kvm_amd` fue una **simulación**; no se intentó una carga real ni ejecutar una máquina virtual anidada.

**Resultado:** KVM no estaba expuesto como dispositivo en el equipo AMD examinado. No se determinó la causa y no puede generalizarse a todas las instalaciones de WSL2.

## USB

- El anfitrión detectó un dispositivo USB físico, pero Ubuntu no lo enumeraba inicialmente.
- En una prueba manual anterior, se utilizó `usbipd bind`, `usbipd attach --wsl` y `usbipd detach`; Ubuntu pudo enumerar el identificador `0930:6545` después de adjuntarlo.
- El script Python **solo consultó** el estado; no ejecutó operaciones de conexión.

**Resultado:** conexión, enumeración y desconexión comprobadas mediante `usbipd-win`; no se evaluó lectura/escritura del pendrive.

**Fuentes de antecedentes:** [WSL #11170](https://github.com/microsoft/WSL/issues/11170), [WSL #41917](https://github.com/microsoft/WSL/issues/41917), [usbipd-win #882](https://github.com/dorssel/usbipd-win/issues/882). Problemas reportados por terceros en configuraciones específicas.

**Evidencias:** figuras 14 a 22 del informe; las capturas originales separadas están pendientes de revisión.
