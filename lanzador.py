import tkinter as tk
from tkinter import messagebox, scrolledtext, Toplevel
import subprocess
import os
import signal
import json
import sys

# --- CONFIGURACIÓN ---
INTERNAL_DEFAULT_IP = "162.244.53.174" # IP Puente Oficial
APP_TITLE = "Skate 3 Proxy | Linux Native v6.0 (Enhanced Replication)"

# Colores
COLOR_BG = "#1e1e1e"
COLOR_PANEL = "#252526"
COLOR_ACCENT = "#007acc"
COLOR_TEXT = "#ffffff"
COLOR_GRAY = "#888888"
COLOR_INFO = "#00bcd4"
COLOR_LOG_BG = "#000000"
COLOR_LOG_TEXT = "#00ff00"
COLOR_TOGGLE_BTN = "#2d2d30"

DEFAULT_LOGIN = {"Email": "", "Password": "", "PsnName": ""}
DEFAULT_SETTINGS = {
    "autoMinimize": False,
    "twoPlayerStableLobbies": False,
    "customIpEnabled": False,
    "customIp": INTERNAL_DEFAULT_IP
}

class SkateDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("700x380")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.process = None
        self.is_running = False
        self.rpcs3_detected = False
        self.logs_visible = False

        # Cargar settings iniciales para el IP Entry
        self.settings = self.load_json("appsettings.json", DEFAULT_SETTINGS)

        # --- HEADER ---
        self.header_frame = tk.Frame(root, bg=COLOR_BG)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(self.header_frame, text="SKATE 3 SERVER", font=("Impact", 24), fg=COLOR_TEXT, bg=COLOR_BG).pack(side="left")

        self.lbl_info = tk.Label(self.header_frame, text="READY TO START", font=("Arial", 11, "bold"), fg="#555", bg=COLOR_BG)
        self.lbl_info.pack(side="left", padx=20, expand=True)

        self.lbl_extra = tk.Label(root, text="SSL Patch & Hosts Redirection: ACTIVE", font=("Arial", 8), fg=COLOR_GRAY, bg=COLOR_BG)
        self.lbl_extra.place(x=20, y=55)

        self.status_frame = tk.Frame(self.header_frame, bg=COLOR_BG)
        self.status_frame.pack(side="right")
        self.status_canvas = tk.Canvas(self.status_frame, width=20, height=20, bg=COLOR_BG, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=5)
        self.status_light = self.status_canvas.create_oval(2, 2, 18, 18, fill="red", outline="")
        self.lbl_status = tk.Label(self.status_frame, text="DETENIDO", font=("Arial", 10, "bold"), fg="#ff5555", bg=COLOR_BG)
        self.lbl_status.pack(side="left")

        # --- PANEL ---
        self.panel = tk.Frame(root, bg=COLOR_PANEL, bd=1, relief="flat")
        self.panel.pack(fill="x", padx=20, pady=10)

        self.mode_var = tk.StringVar(value="local")
        tk.Label(self.panel, text="MODO DE OPERACIÓN", font=("Arial", 9, "bold"), fg=COLOR_GRAY, bg=COLOR_PANEL).pack(anchor="w", padx=15, pady=(15, 5))

        self.rb_local = tk.Radiobutton(self.panel, text="HOST LOCAL (Servidor Privado)", variable=self.mode_var, value="local",
                                       bg=COLOR_PANEL, fg="white", selectcolor="#444", activebackground=COLOR_PANEL, activeforeground=COLOR_ACCENT, font=("Arial", 11))
        self.rb_local.pack(anchor="w", padx=20, pady=2)

        self.remote_frame = tk.Frame(self.panel, bg=COLOR_PANEL)
        self.remote_frame.pack(anchor="w", padx=20, pady=(2, 15))

        self.rb_remote = tk.Radiobutton(self.remote_frame, text="Custom Server", variable=self.mode_var, value="remote",
                                        bg=COLOR_PANEL, fg="white", selectcolor="#444", activebackground=COLOR_PANEL, activeforeground="#ff9900", font=("Arial", 11))
        self.rb_remote.pack(side="left")

        self.ip_entry_var = tk.StringVar(value=self.settings.get("customIp", INTERNAL_DEFAULT_IP))
        self.ip_entry = tk.Entry(self.remote_frame, textvariable=self.ip_entry_var, font=("Consolas", 10), 
                                 bg="#333", fg="white", insertbackground="white", relief="flat", width=18)
        self.ip_entry.pack(side="left", padx=10)

        # --- TOGGLE LOGS ---
        self.btn_toggle_logs = tk.Button(root, text="▼ MOSTRAR DETALLES / LOGS", bg=COLOR_TOGGLE_BTN, fg=COLOR_GRAY,
                                         relief="flat", font=("Arial", 8), command=self.toggle_logs, cursor="hand2")
        self.btn_toggle_logs.pack(fill="x", padx=20, pady=(5, 0))

        # --- LOG CONTAINER ---
        self.log_container = tk.Frame(root, bg=COLOR_BG)
        tk.Label(self.log_container, text="ESTADO DE EJECUCIÓN (TERMINAL MIRROR)", font=("Consolas", 9), fg=COLOR_GRAY, bg=COLOR_BG).pack(anchor="w", pady=(10, 0))
        self.log_box = scrolledtext.ScrolledText(self.log_container, height=10, bg=COLOR_LOG_BG, fg=COLOR_LOG_TEXT, font=("Consolas", 10), state='disabled', bd=0)
        self.log_box.pack(fill="both", pady=(5, 10), expand=True)
        self.log(">> MODO TERMINAL ACTIVO", "cyan")
        self.log(">> Los logs detallados salen por la terminal.", "white")

        # --- BOTONES ---
        self.btn_frame = tk.Frame(root, bg=COLOR_BG)
        self.btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")

        self.btn_settings = tk.Button(self.btn_frame, text="Settings", bg="#333", fg="white", relief="flat", command=self.modal_settings)
        self.btn_settings.pack(side="left", ipadx=10)
        self.btn_main = tk.Button(self.btn_frame, text="INICIAR SERVIDOR", font=("Arial", 11, "bold"),
                                  bg=COLOR_ACCENT, fg="white", relief="flat", command=self.toggle_process)
        self.btn_main.pack(side="right", ipadx=20, ipady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.monitor_rpcs3()
        self.check_process_alive()

    # --- LÓGICA UI ---
    def toggle_logs(self):
        if self.logs_visible:
            self.log_container.pack_forget()
            self.btn_toggle_logs.config(text="▼ MOSTRAR DETALLES / LOGS")
            self.root.geometry("700x380")
            self.logs_visible = False
        else:
            self.log_container.pack(fill="both", padx=20, expand=True, before=self.btn_frame)
            self.btn_toggle_logs.config(text="▲ OCULTAR DETALLES")
            self.root.geometry("700x600")
            self.logs_visible = True

    # --- MONITORES ---
    def monitor_rpcs3(self):
        if self.is_running:
            try:
                res = subprocess.run(["pgrep", "rpcs3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    if not self.rpcs3_detected:
                        self.rpcs3_detected = True
                        self.update_info("🎮 RPCS3 DETECTADO", COLOR_INFO)
                else:
                    if self.rpcs3_detected:
                        self.rpcs3_detected = False
                        self.update_info("ESPERANDO JUEGO...", COLOR_GRAY)
            except: pass
        self.root.after(2000, self.monitor_rpcs3)

    def check_process_alive(self):
        if self.is_running and self.process:
            if self.process.poll() is not None:
                self.set_status(False)
                self.log(">> El servidor se ha cerrado.", "red")
        self.root.after(1000, self.check_process_alive)

    def update_info(self, text, color):
        self.lbl_info.config(text=text, fg=color)

    # --- START SERVER (CON CAMBIO A CORE_SERVER.SH) ---
    def start_server(self):
        # Guardamos el IP actual antes de iniciar
        self.settings["customIp"] = self.ip_entry_var.get().strip()
        self.save_json("appsettings.json", self.settings)

        if self.settings.get("autoMinimize", False): self.root.iconify()

        mode = self.mode_var.get()
        target_ip = self.settings["customIp"]

        # [CAMBIO CRÍTICO] Ahora llamamos a core_server.sh
        script_path = self.get_path("core_server.sh")

        cmd = ["bash", script_path, "--mode", mode]
        if mode == "remote":
            cmd.extend(["--ip", target_ip])

        try:
            self.process = subprocess.Popen(cmd)
            self.set_status(True)
            self.log(f">> Iniciando modo {mode.upper()}...", "green")
            if mode == "remote":
                self.log(f">> Destino: {target_ip}", "gray")
        except Exception as e:
            self.log(f"Error lanzando core_server.sh: {e}", "red")

    def stop_server(self):
        if self.process:
            self.process.terminate()
            self.process = None
        # Limpieza (sudo es opcional aqui porque ya somos root, pero no daña)
        subprocess.run(["pkill", "-f", "socat"])
        subprocess.run(["pkill", "-f", "Skateboard3Server.Host"])
        self.set_status(False)

    def toggle_process(self):
        if self.is_running: self.stop_server()
        else: self.start_server()

    # --- MODAL SETTINGS ---
    def modal_settings(self):
        win = Toplevel(self.root)
        win.title("Settings")
        win.geometry("400x250")
        win.configure(bg=COLOR_PANEL)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="CONFIGURACIÓN", font=("Impact", 16), fg=COLOR_TEXT, bg=COLOR_PANEL).pack(pady=20)

        frame = tk.Frame(win, bg=COLOR_PANEL)
        frame.pack(fill="both", padx=30)

        # Opciones Generales
        tk.Label(frame, text="GENERAL", font=("Arial", 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_PANEL).pack(anchor="w", pady=(0,5))

        var_minimize = tk.BooleanVar(value=self.settings.get("autoMinimize", False))
        tk.Checkbutton(frame, text="Minimizar al iniciar", variable=var_minimize, bg=COLOR_PANEL, fg="white",
                       selectcolor="#444", activebackground=COLOR_PANEL, activeforeground="white").pack(anchor="w")

        var_stable = tk.BooleanVar(value=self.settings.get("twoPlayerStableLobbies", False))
        tk.Checkbutton(frame, text="Lobbies Estables (2 Player Mode)", variable=var_stable, bg=COLOR_PANEL, fg="white",
                       selectcolor="#444", activebackground=COLOR_PANEL, activeforeground="white").pack(anchor="w")

        def save():
            self.settings["autoMinimize"] = var_minimize.get()
            self.settings["twoPlayerStableLobbies"] = var_stable.get()
            self.save_json("appsettings.json", self.settings)
            messagebox.showinfo("Guardado", "Configuración actualizada.", parent=win)
            win.destroy()

        tk.Button(win, text="GUARDAR CAMBIOS", bg=COLOR_ACCENT, fg="white", relief="flat", command=save).pack(pady=20, ipadx=20)

    # --- UTILIDADES ---
    def get_path(self, f):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), f)

    def load_json(self, f, d):
        p = self.get_path(f)
        if not os.path.exists(p): return d.copy()
        try:
            with open(p, 'r') as file: return json.load(file)
        except: return d.copy()

    def save_json(self, f, d):
        try:
            with open(self.get_path(f), 'w') as file: json.dump(d, file, indent=4)
        except Exception as e: print(f"Error JSON: {e}")

    def log(self, msg, color=None):
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, msg + "\n")
        if color:
            line = int(self.log_box.index('end-1c').split('.')[0])
            self.log_box.tag_add(color, f"{line}.0", f"{line}.end")
            self.log_box.tag_config(color, foreground=color)
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

    def set_status(self, running):
        self.is_running = running
        if running:
            self.status_canvas.itemconfig(self.status_light, fill="#00ff00")
            self.lbl_status.config(text="EJECUTANDO", fg="#00ff00")
            self.btn_main.config(text="DETENER", bg="#d32f2f")
            self.update_info("MIRA LA TERMINAL", COLOR_TEXT)
        else:
            self.status_canvas.itemconfig(self.status_light, fill="red")
            self.lbl_status.config(text="DETENIDO", fg="#ff5555")
            self.btn_main.config(text="INICIAR SERVIDOR", bg=COLOR_ACCENT)
            self.update_info("READY TO START", "#555")

    def on_close(self):
        if self.is_running: self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SkateDashboard(root)
    root.mainloop()
