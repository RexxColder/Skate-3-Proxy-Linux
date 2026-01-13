#!/bin/bash

# ==========================================
# SKATE 3 PROXY - MASTER LAUNCHER
# ==========================================

# --- Configuración de Colores ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 1. AUTO-ELEVACIÓN A SUDO
# Si el usuario no es root, el script se reinicia pidiendo contraseña.
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[SUDO] Se requieren permisos de administrador para configuración de red.${NC}"
    echo -e "       Por favor, introduce tu contraseña:"
    exec sudo "$0" "$@"
    exit
fi

# Detectar usuario real (para arreglar permisos luego)
REAL_USER=$SUDO_USER
if [ -z "$REAL_USER" ]; then REAL_USER=$(whoami); fi

# Asegurar directorio de trabajo
cd "$(dirname "$0")"
WORK_DIR=$(pwd)

# --- Encabezado ---
clear
echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}    🛹  SKATE 3 SERVER — LINUX NATIVE PORT      ${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# 2. Gestión de Dependencias (Auto-Instalación)
echo -e "${YELLOW}[INFO] Verificando entorno y dependencias...${NC}"

# Detectar Distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi

install_package() {
    local PKG=$1
    echo -e "${YELLOW}[DEP] Intentando instalar $PKG...${NC}"
    case $DISTRO in
        arch)
            pacman -S --noconfirm "$PKG" > /dev/null 2>&1
            ;;
        ubuntu|debian|pop|mint)
            apt-get update -y > /dev/null 2>&1
            apt-get install -y "$PKG" > /dev/null 2>&1
            ;;
        fedora)
            dnf install -y "$PKG" > /dev/null 2>&1
            ;;
    esac
}

# Verificamos Tkinter (libtk)
if ! python3 -c "import tkinter" &> /dev/null; then
    echo -e "${BLUE}[DEP] Tkinter no detectado.${NC}"
    case $DISTRO in
        arch) install_package "tk" ;;
        ubuntu|debian|pop|mint) install_package "python3-tk" ;;
        fedora) install_package "python3-tkinter" ;;
        *) echo -e "${RED}[ERROR] No se pudo instalar Tkinter automáticamente en $DISTRO. Instálalo manualmente.${NC}" ;;
    esac
fi

# Verificamos otros esenciales
MISSING_DEPS=()
command -v socat &> /dev/null || MISSING_DEPS+=("socat")
command -v curl &> /dev/null || MISSING_DEPS+=("curl")

for dep in "${MISSING_DEPS[@]}"; do
    echo -e "${BLUE}[DEP] Instalando dependencia faltante: $dep...${NC}"
    install_package "$dep"
done

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 no está instalado. Instálalo para continuar.${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Entorno listo.${NC}"

# Asegurar permisos de ejecución en los binarios
chmod +x Skateboard3Server.Host lanzador.py core_server.sh

# 3. CONFIGURACIÓN DE FIREWALL
echo -e "${YELLOW}[FIREWALL] Analizando reglas de red...${NC}"
configure_firewall() {
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        echo -e "${BLUE}   -> Firewall detectado: UFW${NC}"
        ufw allow 80/tcp > /dev/null; ufw allow 443/tcp > /dev/null
        echo -e "${GREEN}[OK] Reglas añadidas a UFW.${NC}"
    elif command -v firewall-cmd &> /dev/null && firewall-cmd --state &> /dev/null; then
        echo -e "${BLUE}   -> Firewall detectado: Firewalld${NC}"
        firewall-cmd --zone=public --add-port=80/tcp --permanent > /dev/null
        firewall-cmd --zone=public --add-port=443/tcp --permanent > /dev/null
        firewall-cmd --reload > /dev/null
        echo -e "${GREEN}[OK] Reglas añadidas a Firewalld.${NC}"
    elif command -v iptables &> /dev/null; then
        echo -e "${BLUE}   -> Firewall detectado: Iptables (Genérico)${NC}"
        # Solo agrega si no existen
        iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 443 -j ACCEPT
        echo -e "${GREEN}[OK] Reglas inyectadas en Iptables.${NC}"
    else
        echo -e "${YELLOW}[INFO] No se detectó firewall activo.${NC}"
    fi
}
configure_firewall

# 3.5 REDIRECCIÓN DE DOMINIOS (REPLICACIÓN DE WINDOWS)
# Esto redirige el tráfico de EA al proxy local sin necesidad de inyectar en memoria.
DOMAINS=(
    "downloads.skate.online.ea.com"
    "skate-ps3-01.skate.online.ea.com"
    "gosredir.ea.com"
    "gosiadprod-qos01.ea.com"
    "gosgvaprod-qos01.ea.com"
    "gossjcprod-qos01.ea.com"
)

apply_redirection() {
    echo -e "${YELLOW}[NETWORK] Redirigiendo dominios de EA a localhost...${NC}"
    cp /etc/hosts /etc/hosts.skate.bak
    for domain in "${DOMAINS[@]}"; do
        if ! grep -q "$domain" /etc/hosts; then
            echo "127.0.0.1 $domain" >> /etc/hosts
        fi
    done
    echo -e "${GREEN}[OK] Redirección aplicada.${NC}"
}

cleanup_redirection() {
    if [ -f /etc/hosts.skate.bak ]; then
        echo -e "${YELLOW}[CLEANUP] Restaurando /etc/hosts...${NC}"
        mv /etc/hosts.skate.bak /etc/hosts
        echo -e "${GREEN}[OK] Red de sistema normalizada.${NC}"
    fi
}

# Asegurar limpieza al salir (Ctrl+C, errores, o cierre normal)
trap cleanup_redirection EXIT

apply_redirection

# 4. Gestión de Librería SQLite (Fix común)
if [ ! -f "libe_sqlite3.so" ]; then
    echo -e "${YELLOW}[SETUP] Enlazando SQLite...${NC}"
    TARGET=$(ldconfig -p | grep libsqlite3.so.0 | head -n 1 | awk '{print $4}')
    if [ -z "$TARGET" ]; then
        # Búsqueda manual si ldconfig falla
        for path in /usr/lib /usr/lib64 /usr/lib/x86_64-linux-gnu /lib; do
            if [ -f "$path/libsqlite3.so.0" ]; then TARGET="$path/libsqlite3.so.0"; break; fi
        done
    fi
    if [ ! -z "$TARGET" ]; then 
        ln -s "$TARGET" libe_sqlite3.so
        echo -e "${GREEN}[OK] SQLite enlazado correctamente.${NC}"
    fi
fi

# 5. CREACIÓN DE ACCESO DIRECTO "SILENCIOSO"
if [ "$REAL_USER" = "root" ]; then USER_HOME="/root"; else USER_HOME="/home/$REAL_USER"; fi
SHORTCUT_PATH="$USER_HOME/.local/share/applications/SkateServer.desktop"

# Solo creamos el acceso directo si no existe o si queremos forzar actualización
if [ ! -f "$SHORTCUT_PATH" ]; then
    echo -e "${YELLOW}[SETUP] Creando acceso directo en el menú...${NC}"
    mkdir -p "$USER_HOME/.local/share/applications"
    
    # Obtenemos ruta absoluta al icono si existe, sino genérico
    ICON_PATH="$WORK_DIR/wwwroot/favicon.ico"
    if [ ! -f "$ICON_PATH" ]; then ICON_PATH="utilities-terminal"; fi

    cat <<EOF > "$SHORTCUT_PATH"
[Desktop Entry]
Name=Skate 3 Server
Comment=Linux Native Proxy Server
Exec=pkexec "$WORK_DIR/run.sh"
Icon=$ICON_PATH
Terminal=true
Type=Application
Categories=Game;Network;
EOF
    chown $REAL_USER:$REAL_USER "$SHORTCUT_PATH"
    chmod +x "$SHORTCUT_PATH"
    echo -e "${GREEN}[OK] Acceso directo creado.${NC}"
fi

# 6. LANZAMIENTO DEL GUI
echo ""
echo -e "${BLUE}>>> Iniciando Launcher (Python Tkinter)... 🛹${NC}"
echo -e "${YELLOW}[NOTA] No cierres esta terminal para ver los logs en tiempo real.${NC}"
echo ""

# Ejecutamos python.
# Pasamos las variables de entorno necesarias para que Root pueda mostrar GUI en la sesión del usuario
# Especialmente importante en Wayland
if [ -n "$SUDO_USER" ]; then
    xhost +SI:localuser:root > /dev/null 2>&1
fi

python3 lanzador.py

# 7. LIMPIEZA DE PERMISOS AL CERRAR
# Como corrimos como root, los JSON pueden haber quedado como propiedad de root.
# Los devolvemos al usuario real para evitar problemas futuros.
echo ""
echo -e "${YELLOW}[CLEANUP] Restaurando permisos de archivos...${NC}"
chown $REAL_USER:$REAL_USER *.json 2>/dev/null
echo -e "${GREEN}[OK] Finalizado. ¡Hasta luego!${NC}"
