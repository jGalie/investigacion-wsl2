# Laboratorio 02 - Conectividad NAT y mirrored

**Objetivo:** comparar el acceso a Nginx dentro de WSL2 y desde una segunda computadora de la misma red.

**Instrumentos:** Nginx, terminal Ubuntu (`ip`, `curl`), PowerShell, configuración de WSL y mecanismos de firewall de Windows.

### NAT

- Se inspeccionaron dirección IPv4 y rutas de Ubuntu mediante `ip -4 addr` e `ip route`.
- Se comprobó HTTP local con Nginx (respuesta `200 OK`).
- El acceso desde otro equipo de la LAN no funcionó inicialmente; se habilitó mediante redirección TCP (`portproxy`) y regla de entrada del firewall de Windows.

### Mirrored

- Se habilitó `networkingMode=mirrored` en `.wslconfig` y se reinició WSL2.
- Se comparó la dirección IPv4 mostrada por Ubuntu con la de Windows.
- Para permitir acceso HTTP desde otro equipo fue necesaria una regla de entrada del **firewall de Hyper-V** para el puerto 80; no se utilizó `portproxy`.

**Conclusión de la prueba:** publicar un servicio dentro de WSL2 depende del modo de red y de las reglas de seguridad del anfitrión. `localhost` correcto **no prueba** acceso desde toda la LAN.

**Evidencias:** figuras 4 a 9 del informe. El trabajo describe el ensayo NAT con `portproxy`, aunque sin incluir capturas adicionales de esa configuración.

**Referencia:** [Microsoft: redes con WSL](https://learn.microsoft.com/es-es/windows/wsl/networking).
