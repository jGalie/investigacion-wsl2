#!/usr/bin/env python3
"""Diagnóstico experimental no destructivo para Ubuntu en WSL2 (Python >=3.8)."""
import csv
import gzip
import datetime as dt
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys

MAX_OUTPUT = 120000
TIMEOUT = 12


def classify(returncode, stdout, stderr, missing=False, timeout=False):
    if missing:
        return 'COMANDO_AUSENTE', 'La utilidad no está instalada o no figura en PATH.'
    if timeout:
        return 'TIEMPO_AGOTADO', 'No se obtuvo respuesta dentro del plazo.'
    s = (stdout + '\n' + stderr).lower()
    if re.search(r'permission denied|operation not permitted|access denied|not permitted|permission error', s):
        return 'PERMISOS', 'Se detectó una denegación de acceso; no atribuir automáticamente a WSL2.'
    if returncode == 0:
        return 'CORRECTO', 'La operación finalizó correctamente; revisar el contenido de la salida.'
    if re.search(r'not supported|unsupported|not implemented|no such device|not available|invalid argument|unknown tracepoint', s):
        return 'RESTRICCION_POSIBLE', 'La operación o recurso no está disponible; requiere análisis de causa.'
    return 'ERROR_OTRO', 'El comando devolvió un error que requiere interpretación.'


def run_test(group, name, argv, outdir, records, interpretation='', timeout=TIMEOUT):
    number = len(records) + 1
    key = f'{number:02d}_{re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")}'
    cmd_path = shutil.which(argv[0])
    missing = cmd_path is None
    timed_out = False
    stdout, stderr, rc = '', '', None
    if not missing:
        try:
            cp = subprocess.run(argv, capture_output=True, text=True, errors='replace', timeout=timeout, check=False,
                                env={**os.environ, 'LC_ALL': 'C'})
            stdout, stderr, rc = cp.stdout, cp.stderr, cp.returncode
        except subprocess.TimeoutExpired as e:
            timed_out = True
            stdout = e.stdout.decode('utf-8', 'replace') if isinstance(e.stdout, bytes) else (e.stdout or '')
            stderr = e.stderr.decode('utf-8', 'replace') if isinstance(e.stderr, bytes) else (e.stderr or '')
        except OSError as e:
            stderr = str(e)
    status, detail = classify(rc, stdout, stderr, missing, timed_out)
    raw = (f'Prueba: {name}\nCategoría: {group}\nArgumentos: {argv!r}\n'
           f'Código de salida: {rc}\nEstado: {status}\n\nSTDOUT:\n{stdout[:MAX_OUTPUT]}\n\nSTDERR:\n{stderr[:MAX_OUTPUT]}\n')
    (outdir / (key + '.txt')).write_text(raw, encoding='utf-8')
    row = dict(categoria=group, prueba=name, comando=' '.join(argv), codigo_salida='' if rc is None else rc,
               estado=status, interpretacion=interpretation or detail, archivo_salida=key + '.txt')
    if name == 'Información módulo loop' and status == 'ERROR_OTRO' and 'Module loop not found' in stderr:
        try:
            with gzip.open('/proc/config.gz', 'rt', encoding='utf-8', errors='replace') as cfg:
                if any(line.strip() == 'CONFIG_BLK_DEV_LOOP=y' for line in cfg):
                    status = 'NO_MODULAR'
                    row['estado'] = status
                    row['interpretacion'] = 'loop está integrado en el kernel (CONFIG_BLK_DEV_LOOP=y); no necesita módulo .ko.'
                    raw = raw.replace('Estado: ERROR_OTRO', 'Estado: NO_MODULAR')
                    (outdir / (key + '.txt')).write_text(raw, encoding='utf-8')
        except OSError:
            pass
    records.append(row)
    mostrar(status, name, ' '.join(argv), interpretar(name, status, stdout, stderr))
    return row, stdout, stderr


def inspect_file(group, name, target, outdir, records, interpretation=''):
    p = Path(target)
    try:
        if not p.exists():
            raise FileNotFoundError(target)
        if p.is_char_device() or p.is_block_device():
            info = p.stat()
            content = f'Dispositivo especial; modo={stat.filemode(info.st_mode)}; uid={info.st_uid}; gid={info.st_gid}; lectura no realizada'
        elif p.is_dir():
            content = '\n'.join(sorted(x.name for x in p.iterdir())[:200])
        else:
            content = p.read_text(encoding='utf-8', errors='replace')[:MAX_OUTPUT]
        status, detail = 'CORRECTO', 'La ruta existe y es accesible.'
    except PermissionError as e:
        content, status, detail = str(e), 'PERMISOS', 'Acceso denegado.'
    except (FileNotFoundError, OSError) as e:
        content, status, detail = str(e), 'RECURSO_AUSENTE', 'La ruta no está disponible; no prueba por sí sola incompatibilidad.'
    number = len(records) + 1
    key = f'{number:02d}_{re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")}.txt'
    (outdir / key).write_text(f'Ruta: {target}\nEstado: {status}\n\n{content}\n', encoding='utf-8')
    records.append(dict(categoria=group, prueba=name, comando=f'lectura {target}', codigo_salida='', estado=status,
                        interpretacion=interpretation or detail, archivo_salida=key))
    mostrar(status, name, 'lectura ' + target, interpretar(name, status, evidencia=content))
    return status, content


def mostrar(estado, nombre, comando, hallazgo):
    """Salida compacta: estado, prueba, comando ejecutado y lectura del resultado."""
    etiquetas = {'RECURSO_AUSENTE': 'AUSENTE', 'ERROR_OTRO': 'ERROR',
                 'COMANDO_AUSENTE': 'SIN COMANDO', 'NO_EXPUESTO_ACTUALMENTE': 'NO EXPUESTO',
                 'INTEGRADO_KERNEL': 'INTEGRADO', 'NO_MODULAR': 'NO MODULAR', 'OBSERVACION_USB': 'OBSERVADO'}
    est = etiquetas.get(estado, estado)
    print(f'[{est:<13}] {nombre:<33} | {comando} -> {hallazgo}')


def interpretar(nombre, estado, stdout='', stderr='', evidencia=''):
    """Interpretaciones acotadas a la evidencia observada; sin inferir causas raíz."""
    data = (stdout + '\n' + evidencia).strip()
    if nombre == 'Versión del kernel':
        return f'Kernel {stdout.strip()}.' if stdout.strip() else 'No se obtuvo la versión del kernel.'
    if nombre == 'Módulos cargados':
        count = max(0, len(stdout.splitlines()) - 1) if estado == 'CORRECTO' else None
        return f'{count} módulos listados por lsmod.' if count is not None else 'No se pudo consultar los módulos.'
    if nombre == 'Información módulo dummy':
        return 'Módulo dummy disponible como archivo .ko.' if estado == 'CORRECTO' else 'No se pudo consultar el módulo dummy.'
    if nombre == 'Simulación modprobe dummy':
        return 'Dependencias localizadas; no se cargó ningún módulo.' if estado == 'CORRECTO' else 'No se pudo simular la carga.'
    if nombre == 'Módulos instalados para el kernel':
        return 'Directorio de módulos del kernel disponible.' if estado == 'CORRECTO' else 'No se encontró el directorio de módulos.'
    if nombre == 'Información CPU y virtualización':
        m = re.search(r'(?im)^Hypervisor vendor:\s*(.+)$', stdout)
        if m: return f'Hipervisor informado: {m.group(1).strip()}.'
        m = re.search(r'(?im)^Vendor ID:\s*(.+)$', stdout)
        return f'CPU: {m.group(1).strip()}; hipervisor no identificado.' if m else 'No se identificó el hipervisor en la salida.'
    if nombre == 'Dispositivo KVM':
        return 'No existe /dev/kvm; KVM no está expuesto ahora.' if estado == 'RECURSO_AUSENTE' else 'Dispositivo presente; uso no comprobado.'
    if nombre == 'Indicadores CPU':
        return 'svm/vmx visible' if re.search(r'(?<!\w)(svm|vmx)(?!\w)', data) else 'Sin svm/vmx visible; causa no determinada.'
    if nombre == 'Módulos KVM cargados':
        return 'Módulo KVM cargado.' if re.search(r'(?m)^(kvm|kvm_amd)\s+\d+', stdout) else 'No aparecen módulos KVM cargados.'
    if nombre == 'Información módulo loop':
        return ('No existe .ko independiente; soporte integrado (CONFIG=y).' if estado == 'NO_MODULAR' else 'modinfo no encuentra loop; revisar configuración del kernel.') if estado != 'CORRECTO' else 'Metadatos de loop disponibles.'
    if nombre == 'Interpretación de loop':
        return 'CONFIG=y: soporte integrado; no requiere archivo .ko.' if estado == 'INTEGRADO_KERNEL' else 'Revisar configuración del kernel.'
    if nombre.startswith('CONFIG_'):
        return evidencia.strip().replace('CONFIG_', '') + ' (y=integrado; m=módulo)'
    if nombre == 'Información módulo kvm_amd':
        return 'Archivo kvm-amd.ko disponible; no implica que esté cargado.' if estado == 'CORRECTO' else 'No se pudo consultar el módulo.'
    if nombre == 'Simulación carga kvm_amd':
        return 'Dependencias localizadas; simulación sin cargar módulos.' if estado == 'CORRECTO' else 'No se pudieron resolver las dependencias.'
    if nombre == 'Interpretación de disponibilidad KVM':
        return 'Sin /dev/kvm: KVM no expuesto; causa sin determinar.' if estado == 'NO_EXPUESTO_ACTUALMENTE' else 'Dispositivo presente; funcionamiento no probado.'
    if nombre == 'Bus USB en sysfs':
        return 'No se encontró bus USB visible.' if estado == 'RECURSO_AUSENTE' else 'Ruta USB accesible; verificar dispositivos.'
    if nombre in ('Enumeración lsusb', 'Controladores USB visibles'):
        if estado == 'CORRECTO':
            return 'Consulta completada; revisar dispositivos enumerados.'
        if estado == 'ERROR_OTRO' and not stdout.strip() and not stderr.strip():
            return 'Código de salida no cero, sin detalle; causa indeterminada.'
        return 'Consulta sin éxito; revisar salida original.'
    if nombre == 'Nodo USB device':
        return 'No existe /dev/bus/usb actualmente.' if estado == 'RECURSO_AUSENTE' else 'Nodos USB visibles; acceso no probado.'
    if nombre == 'Cliente usbip Linux':
        return 'Herramienta opcional no instalada.' if estado == 'COMANDO_AUSENTE' else 'Cliente usbip consultado.'
    if nombre == 'Dispositivos USB del anfitrión Windows':
        shared = len(re.findall(r'(?m)^\s*\d+-\d+\s+[0-9a-fA-F]{4}:[0-9a-fA-F]{4}.*?\sShared\s*$', stdout))
        attached = len(re.findall(r'(?m)^\s*\d+-\d+\s+[0-9a-fA-F]{4}:[0-9a-fA-F]{4}.*?\sAttached\s*$', stdout))
        return f'Windows: {shared} Shared, {attached} Attached; Shared no es Attached.' if estado == 'CORRECTO' else 'No se pudo consultar usbipd-win.'
    if nombre == 'Interpretación USB':
        return 'USB físico no se expone automáticamente; USB/IP es alternativa.'
    if estado == 'CORRECTO':
        return 'Consulta completada; detalles guardados.'
    if estado == 'COMANDO_AUSENTE':
        return 'Utilidad ausente; no equivale a restricción de WSL2.'
    if estado == 'RECURSO_AUSENTE':
        return 'Recurso no disponible en esta sesión.'
    return 'Resultado no concluyente; revisar salida guardada.'


def main():
    stamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    root = Path.home() / 'resultados_wsl2' / stamp
    root.mkdir(parents=True, exist_ok=False)
    records = []
    print('Diagnóstico WSL2 v6.1 | Pruebas agrupadas e interpretadas | Solo lectura')
    print('Resultados:', root)
    print('NO utiliza sudo ni modifica el sistema.\n')

    print('\n=== 1. MÓDULOS Y SOPORTE LOOP ===')
    run_test('Módulos', 'Versión del kernel', ['uname', '-r'], root, records)
    run_test('Módulos', 'Módulos cargados', ['lsmod'], root, records)
    run_test('Módulos', 'Información módulo dummy', ['modinfo', 'dummy'], root, records)
    run_test('Módulos', 'Simulación modprobe dummy', ['modprobe', '-n', '-v', 'dummy'], root, records)
    run_test('Módulos', 'Información módulo loop', ['modinfo', 'loop'], root, records)
    inspect_file('Módulos', 'Módulos instalados para el kernel', '/lib/modules/' + platform.release(), root, records)

    # Kernel: config efectiva, disponible como /proc/config.gz cuando está habilitada.
    def config_value(option):
        try:
            with gzip.open('/proc/config.gz', 'rt', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if line.startswith(option + '='):
                        return line.strip().split('=', 1)[1]
                    if line.strip() == '# ' + option + ' is not set':
                        return 'n'
        except OSError:
            return None
        return None

    def derived(group, name, status, explanation, evidence):
        number = len(records) + 1
        key = f'{number:02d}_{re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")}.txt'
        (root / key).write_text('Estado: ' + status + '\n' + explanation + '\n\n' + evidence + '\n', encoding='utf-8')
        records.append(dict(categoria=group, prueba=name, comando='evaluación de evidencias',
                            codigo_salida='', estado=status, interpretacion=explanation, archivo_salida=key))
        mostrar(status, name, 'evaluación', interpretar(name, status, evidencia=evidence))

    # Correlación: un fallo de modinfo NO significa ausencia de soporte si CONFIG_=y.
    loop_config = config_value('CONFIG_BLK_DEV_LOOP')
    kvm_config = config_value('CONFIG_KVM')
    amd_config = config_value('CONFIG_KVM_AMD')
    intel_config = config_value('CONFIG_KVM_INTEL')
    for name, value in [('CONFIG_BLK_DEV_LOOP', loop_config)]:
        status = 'CONFIGURACION_NO_DISPONIBLE' if value is None else 'CORRECTO'
        derived('Kernel', name, status, 'Valor observado en /proc/config.gz; y=integrado, m=módulo, n=deshabilitado.',
                f'{name}={value if value is not None else "NO_CONSULTABLE"}')
    if loop_config == 'y':
        derived('Módulos', 'Interpretación de loop', 'INTEGRADO_KERNEL',
                'loop está compilado dentro del kernel: modinfo loop puede fallar sin indicar incompatibilidad.',
                'CONFIG_BLK_DEV_LOOP=y')
    elif loop_config == 'm':
        derived('Módulos', 'Interpretación de loop', 'MODULO_CONFIGURADO',
                'loop se configura como módulo; comprobar archivo y carga por separado.',
                'CONFIG_BLK_DEV_LOOP=m')
    else:
        derived('Módulos', 'Interpretación de loop', 'INDETERMINADO',
                'No se puede concluir soporte operativo de loop a partir de modinfo solamente.',
                f'CONFIG_BLK_DEV_LOOP={loop_config}')

    print('\n=== 2. VIRTUALIZACIÓN ANIDADA Y KVM ===')
    # KVM: examina exposición de dispositivo y banderas; NO inicia hipervisores.
    inspect_file('KVM', 'Dispositivo KVM', '/dev/kvm', root, records,
                 'La existencia de /dev/kvm no demuestra por sí sola que KVM sea utilizable.')
    run_test('KVM', 'Información CPU y virtualización', ['lscpu'], root, records)
    inspect_file('KVM', 'Indicadores CPU', '/proc/cpuinfo', root, records,
                 'Buscar vmx/svm; la ausencia de banderas no demuestra por sí sola la causa.')
    run_test('KVM', 'Módulos KVM cargados', ['lsmod'], root, records)

    for name, value in [('CONFIG_KVM', kvm_config), ('CONFIG_KVM_AMD', amd_config), ('CONFIG_KVM_INTEL', intel_config)]:
        status = 'CONFIGURACION_NO_DISPONIBLE' if value is None else 'CORRECTO'
        derived('KVM', name, status, 'y=integrado, m=módulo, n=deshabilitado.',
                f'{name}={value if value is not None else "NO_CONSULTABLE"}')
    # KVM: pruebas adicionales no destructivas, sin cargar módulos.
    run_test('KVM', 'Información módulo kvm_amd', ['modinfo', 'kvm_amd'], root, records)
    run_test('KVM', 'Simulación carga kvm_amd', ['modprobe', '-n', '-v', 'kvm_amd'], root, records)
    try:
        cpuinfo = Path('/proc/cpuinfo').read_text(encoding='utf-8', errors='replace')
        flags = bool(re.search(r'(?<!\w)(svm|vmx)(?!\w)', cpuinfo))
    except OSError:
        flags = False
    kvm_device = Path('/dev/kvm').exists()
    derived('KVM', 'Interpretación de disponibilidad KVM',
            'DISPOSITIVO_PRESENTE' if kvm_device else 'NO_EXPUESTO_ACTUALMENTE',
            'La ausencia de /dev/kvm y de flags no identifica por sí sola la causa ni prueba imposibilidad de cargar módulos.',
            f'/dev/kvm={kvm_device}; svm_o_vmx_en_cpuinfo={flags}; CONFIG_KVM={kvm_config}; CONFIG_KVM_AMD={amd_config}')

    print('\n=== 3. ACCESO A DISPOSITIVOS USB ===')
    # USB: enumera y consulta. No ejecuta attach/detach, ni usbipd bind.
    inspect_file('USB', 'Bus USB en sysfs', '/sys/bus/usb/devices', root, records,
                 'Un directorio vacío no demuestra por sí solo una limitación general de USB.')
    run_test('USB', 'Enumeración lsusb', ['lsusb'], root, records,
             'Una salida vacía o sin dispositivos físicos no equivale a error de ejecución.')
    run_test('USB', 'Controladores USB visibles', ['lsusb', '-t'], root, records)
    inspect_file('USB', 'Nodo USB device', '/dev/bus/usb', root, records,
                 'La ausencia del nodo debe interpretarse junto con lsusb y sysfs.')
    run_test('USB', 'Cliente usbip Linux', ['usbip', 'version'], root, records,
             'La utilidad es opcional; comando ausente no significa que WSL2 no soporte USB/IP.')
    # Desde WSL, usbipd.exe puede estar disponible en PATH de Windows. Solo consulta.
    if shutil.which('usbipd.exe'):
        run_test('USB', 'Dispositivos USB del anfitrión Windows', ['usbipd.exe', 'list'], root, records,
                 'Lista dispositivos en Windows; no indica que estén adjuntos a WSL2.', timeout=18)
    else:
        derived('USB', 'Herramienta usbipd-win del anfitrión', 'HERRAMIENTA_NO_DETECTADA',
                'usbipd.exe no figura en el PATH visible desde WSL; puede no estar instalado o no estar expuesto.',
                'No se ejecutaron operaciones de conexión USB.')
    try:
        usb_devices = [x for x in Path('/sys/bus/usb/devices').iterdir() if (x / 'idVendor').exists()]
        usb_count = len(usb_devices)
    except OSError:
        usb_count = None
    derived('USB', 'Interpretación USB', 'OBSERVACION_USB',
            'La visibilidad USB en WSL2 no equivale a acceso nativo automático a todos los dispositivos del anfitrión; usbipd-win permite compartir dispositivos compatibles.',
            f'dispositivos_usb_con_idVendor_en_sysfs={usb_count}; sin attach ni detach')

    csv_path = root / 'resumen.csv'
    with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (root / 'metadatos.json').write_text(json.dumps({
        'fecha': dt.datetime.now().isoformat(timespec='seconds'),
        'plataforma': platform.platform(), 'python': sys.version,
        'usuario_root': os.geteuid() == 0, 'cantidad_pruebas': len(records),
        'version_script': '6.1', 'nota': 'Las clasificaciones son preliminares; no prueban por sí solas limitaciones inherentes a WSL2.'
    }, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nFinalizado: {len(records)} pruebas. CSV: {csv_path}')
    print('Nota: el programa no ejecuta pruebas de persistencia de servicios; se documentan manualmente en el artículo.')


if __name__ == '__main__':
    main()
