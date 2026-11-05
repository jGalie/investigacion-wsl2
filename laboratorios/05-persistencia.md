# Laboratorio 05 - Persistencia de servicios

**Objetivo:** evaluar si habilitar un servicio con `systemd` mantiene ejecutándose la distribución WSL2 después de cerrar la última sesión.

**En Ubuntu:** se comprobó el estado de Nginx mediante:

```bash
systemctl is-enabled nginx
systemctl is-active nginx
```

Se observó `enabled` y `active` **antes** de cerrar la sesión con `exit`.

**En PowerShell:** se consultó la distribución con `wsl --list --verbose` después del cierre. Una consulta mostró `Running` y otra, aproximadamente cuatro segundos después, `Stopped`.

**Conclusión:** habilitar Nginx con `systemd` no garantiza por sí solo que la instancia WSL2 permanezca ejecutándose sin sesiones interactivas. Los cuatro segundos fueron una observación puntual, no un tiempo universal de apagado.

**Evidencias:** figura 23 del informe.

**Referencia:** [Microsoft: systemd en WSL](https://learn.microsoft.com/es-es/windows/wsl/systemd).
