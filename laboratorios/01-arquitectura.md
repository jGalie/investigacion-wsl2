# Laboratorio 01 - Arquitectura y kernel

**Objetivo:** identificar la versión de WSL, la distribución Linux, el kernel y el proceso de inicialización.

**Desde PowerShell:** `wsl --version`, `wsl --status`, `wsl --list --verbose`.

**Desde Ubuntu:**

```bash
cat /etc/os-release
uname -r
cat /proc/version
systemd-detect-virt
ps -p 1 -o pid,comm,args
```

**Resultado observado:** Ubuntu 22.04.5 LTS sobre WSL2, kernel `6.18.54.1-microsoft-standard-WSL2` y `systemd` como PID 1.

**Interpretación:** WSL2 ejecuta un kernel Linux real en una máquina virtual ligera gestionada por Windows. Esto no implica que todos los recursos físicos o capacidades de virtualización estén expuestos.

**Evidencias:** figuras 1 a 3 del informe. Las capturas individuales están pendientes de selección y revisión.
