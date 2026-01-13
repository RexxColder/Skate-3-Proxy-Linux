                                    🛹 SKATE 3 PROXY PROJECT

<img width="2800" height="900" alt="image" src="https://github.com/user-attachments/assets/11a586a7-349f-465b-91bd-6d6fce1a30b0" />


                                     🛠️ Realizado por RexxColder
✨ Características Principales
🐧 Cero Emulación: El servidor .NET corre nativamente sobre el kernel de Linux.

🔗 Auto-Configuración: Script inteligente (run.sh) que detecta librerías y configura permisos.

🎨 GUI Integrada: Panel de control visual en Python (Tkinter).

⚡ Rendimiento: Menor uso de CPU y RAM al no depender de capas de compatibilidad.

🛠️ SQLite Fix: Incluye parche automático para la compatibilidad de bases de datos en distros modernas (Arch, Fedora, Ubuntu).


                                      📦 Instalación
No necesitas compilar nada. Simplemente descarga la Release, descomprime y juega.

                                       Requisitos Previos
Asegúrate de tener las librerías básicas instaladas en tu sistema:


Arch Linux / CachyOS / Manjaro: sudo pacman -S python tk sqlite


**Ubuntu / Debian / Mint: sudo apt update && sudo apt install python3 python3-tk sqlite3


Fedora: sudo dnf install python3 python3-tkinter sqlite


                                   
                                      Ejecución Rápida ⚡ 
Este paquete incluye un script maestro (run.sh) que se encarga de todo: permisos de red, enlaces de librerías y arranque.
Descarga y extrae la carpeta del proyecto. 
Abre una terminal dentro de la carpeta.

Ejecuta:sh run.sh

Nota: Se te pedirá tu contraseña de administrador (sudo) la primera vez. Esto es obligatorio y normal, ya que el servidor necesita escuchar en los puertos 80 y 443 (puertos privilegiados) para emular los servidores de EA.

                                   
                                      ⚙️ Configuración en RPCS3 Para que tu juego conecte a este servidor local:

Abre RPCS3 (Versión Linux). Ve a Configuration -> RPCN.Host: Skate 3 Server (Local)En la sección de IP/Hosts Switches.
pega lo siguiente: gosredirector.ea.com=127.0.0.1

                                 
                                      🐛 Solución de Problemas
ErrorSolución"Permission Denied" al arrancar
Asegúrate de lanzar el juego usando sh run.sh. No ejecutes el archivo Python directamente si no has configurado setcap manualmente.
SQLite Error / Database LockedBorra cualquier archivo .db en la carpeta y reinicia run.sh. El script regenerará la base de datos limpia.
Status: Stopped (Inmediato)Verifica que no tengas otro servicio web (Apache/Nginx) usando el puerto 80.


                                      ❤️ Créditos & Agradecimientos
RexxColder - Linux Porting, Python Wrapping & Scripting.
Hall of Meat Team - Creadores originales de la lógica del servidor y la ingeniería inversa.

"Skate or Die... natively." 🛹
