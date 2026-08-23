import os
import re
import time
import json
import threading
import queue
import asyncio
import io
from collections import deque
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import pygame
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent
from TikTokLive.client.web.web_settings import WebDefaults
import edge_tts
import psutil

# OPCIONAL: Si tienes tu API Key personal de EulerStream, descomenta la siguiente línea:
# WebDefaults.tiktok_sign_api_key = "TU_API_KEY_AQUI"

# ==================== CONFIGURACIÓN Y ARCHIVO JSON ====================
CONFIG_FILE = "config.json"

CONFIG_DEFAULTS = {
    "usuario": "@",
    "volumen": 0.5,
    "voz": "es-MX-JorgeNeural",
    "velocidad": "+0%",
    "restringir_subs": False,
    "restringir_mods": False,
    "restringir_lista": False,
    "lista_blanca": "nombre1, nombre2"
}

def cargar_configuracion():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
                return {**CONFIG_DEFAULTS, **datos}
        except Exception:
            return CONFIG_DEFAULTS
    return CONFIG_DEFAULTS

def guardar_configuracion(datos):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error al guardar config: {e}")

config = cargar_configuracion()

VOLUMEN = config["volumen"]
VELOCIDAD_AUDIO = config["velocidad"]
VOZ_TTS = config["voz"]
HISTORIAL_RECIENTE = deque(maxlen=20)
TIEMPO_INICIO = time.time()

pygame.mixer.init()
pygame.mixer.music.set_volume(VOLUMEN)
cola_mensajes = queue.Queue(maxsize=50)
# ==================== PANEL VISUAL COMPLETO ====================
class PanelControl:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TikTok Live TTS - Panel de Control")
        self.root.geometry("560x880")
        self.root.configure(bg="#1e1e2e")
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        # Variables de tiempo y monitoreo
        self.proceso_actual = psutil.Process(os.getpid())
        self.tiempo_conexion_inicio = None

        # Variables de Control
        self.audio_pausado = False
        self.restringir_subs = tk.BooleanVar(value=config["restringir_subs"])
        self.restringir_mods = tk.BooleanVar(value=config["restringir_mods"])
        self.restringir_lista = tk.BooleanVar(value=config["restringir_lista"])
        self.client_tiktok = None
        self.conectado = False

        # Estilos
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabelframe", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("TLabelframe.Label", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 9, "bold"))
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 9))
        style.configure("TCheckbutton", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 9))

        # --- SECCIÓN: CONEXIÓN TIKTOK ---
        frame_conexion = ttk.LabelFrame(self.root, text=" Conexión a Live ")
        frame_conexion.pack(fill="x", padx=15, pady=5)

        f_user = ttk.Frame(frame_conexion)
        f_user.pack(fill="x", padx=10, pady=8)

        ttk.Label(f_user, text="Usuario Live:").pack(side="left")
        self.entry_user = tk.Entry(f_user, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=("Segoe UI", 10), relief="flat")
        self.entry_user.insert(0, config["usuario"])
        self.entry_user.pack(side="left", fill="x", expand=True, padx=10)

        self.btn_conectar = tk.Button(f_user, text="Conectar Live", bg="#a6e3a1", fg="#11111b", relief="flat", command=self.alternar_conexion, font=("Segoe UI", 9, "bold"))
        self.btn_conectar.pack(side="right")

        # --- SECCIÓN: ESTADO Y RECURSOS ---
        frame_estado = ttk.Frame(self.root)
        frame_estado.pack(fill="x", padx=15, pady=2)

        self.lbl_estado = tk.Label(frame_estado, text="Estado: Desconectado", fg="#f38ba8", bg="#1e1e2e", font=("Segoe UI", 10, "bold"))
        self.lbl_estado.pack(side="left")

        self.lbl_ram = ttk.Label(frame_estado, text="RAM: 0.0 MB")
        self.lbl_ram.pack(side="right", padx=(10, 0))

        self.lbl_cola = ttk.Label(frame_estado, text="En cola: 0/50")
        self.lbl_cola.pack(side="right")

        # --- SECCIÓN: TIEMPO EN VIVO ---
        frame_tiempo = ttk.Frame(self.root)
        frame_tiempo.pack(fill="x", padx=15, pady=2)

        self.lbl_tiempo_live = tk.Label(frame_tiempo, text="Live activo: 00:00:00", fg="#89b4fa", bg="#1e1e2e", font=("Segoe UI", 10, "bold"))
        self.lbl_tiempo_live.pack(side="left")

        # --- SECCIÓN: CONTROLES DE AUDIO ---
        frame_audio = ttk.LabelFrame(self.root, text=" Ajustes de Audio ")
        frame_audio.pack(fill="x", padx=15, pady=5)

        f_vol = ttk.Frame(frame_audio)
        f_vol.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_vol, text="Volumen:").pack(side="left")
        self.slider_volumen = ttk.Scale(f_vol, from_=0.0, to=1.0, value=VOLUMEN, command=self.cambiar_volumen)
        self.slider_volumen.pack(side="left", fill="x", expand=True, padx=10)

        f_voces = ttk.Frame(frame_audio)
        f_voces.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(f_voces, text="Voz:").pack(side="left")
        self.combo_voz = ttk.Combobox(f_voces, values=[
            "es-MX-JorgeNeural", 
            "es-MX-DaliaNeural", 
            "es-ES-ElviraNeural", 
            "es-ES-AlvaroNeural",
            "es-AR-TomasNeural"
        ], state="readonly", width=18)
        self.combo_voz.set(VOZ_TTS)
        self.combo_voz.pack(side="left", padx=(5, 15))

        ttk.Label(f_voces, text="Velocidad:").pack(side="left")
        self.combo_vel = ttk.Combobox(f_voces, values=["-30%", "-15%", "+0%", "+15%", "+30%", "+45%", "+60%"], state="readonly", width=8)
        self.combo_vel.set(VELOCIDAD_AUDIO)
        self.combo_vel.pack(side="left", padx=5)

        f_botones = ttk.Frame(frame_audio)
        f_botones.pack(fill="x", padx=10, pady=8)

        self.btn_pausa = tk.Button(f_botones, text="Pausar TTS", bg="#f9e2af", fg="#11111b", relief="flat", command=self.conmutar_pausa, font=("Segoe UI", 9, "bold"))
        self.btn_pausa.pack(side="left", fill="x", expand=True, padx=2)

        btn_test = tk.Button(f_botones, text="Probar Audio", bg="#89b4fa", fg="#11111b", relief="flat", command=self.probar_audio, font=("Segoe UI", 9, "bold"))
        btn_test.pack(side="left", fill="x", expand=True, padx=2)

        btn_limpiar = tk.Button(f_botones, text="Vaciar Cola", bg="#f38ba8", fg="#11111b", relief="flat", command=self.vaciar_cola, font=("Segoe UI", 9, "bold"))
        btn_limpiar.pack(side="left", fill="x", expand=True, padx=2)

        # --- SECCIÓN: MODO RESTRICTIVO Y LISTA BLANCA ---
        frame_filtros = ttk.LabelFrame(self.root, text=" Modo Restrictivo (Sin marcar = Lee a TODO EL CHAT) ")
        frame_filtros.pack(fill="x", padx=15, pady=5)

        f_chk = ttk.Frame(frame_filtros)
        f_chk.pack(fill="x", padx=10, pady=5)
        ttk.Checkbutton(f_chk, text="Solo Subs (Niv 2+)", variable=self.restringir_subs).pack(side="left", expand=True)
        ttk.Checkbutton(f_chk, text="Solo Mods", variable=self.restringir_mods).pack(side="left", expand=True)
        ttk.Checkbutton(f_chk, text="Solo Lista Blanca", variable=self.restringir_lista).pack(side="left", expand=True)

        f_lista = ttk.Frame(frame_filtros)
        f_lista.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_lista, text="Lista Blanca (separados por coma):").pack(anchor="w")
        
        self.entry_lista = tk.Entry(f_lista, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=("Segoe UI", 9), relief="flat")
        self.entry_lista.insert(0, config.get("lista_blanca", ""))
        self.entry_lista.pack(fill="x", pady=3)

        # --- SECCIÓN: LOG Y EXPORTACIÓN ---
        frame_log = ttk.LabelFrame(self.root, text=" Registro de Comentarios ")
        frame_log.pack(fill="both", expand=True, padx=15, pady=5)

        self.log_box = scrolledtext.ScrolledText(
            frame_log, height=8, bg="#11111b", fg="#a6e3a1", 
            insertbackground="white", font=("Consolas", 9), relief="flat"
        )
        self.log_box.pack(padx=8, pady=5, fill="both", expand=True)

        f_log_acc = ttk.Frame(frame_log)
        f_log_acc.pack(fill="x", padx=8, pady=5)

        btn_guardar_log = tk.Button(f_log_acc, text="Guardar Registro (.txt)", bg="#89b4fa", fg="#11111b", relief="flat", command=self.exportar_log, font=("Segoe UI", 8, "bold"))
        btn_guardar_log.pack(side="left", padx=2)

        btn_borrar_log = tk.Button(f_log_acc, text="Limpiar Cuadro", bg="#f38ba8", fg="#11111b", relief="flat", command=self.limpiar_cuadro_log, font=("Segoe UI", 8, "bold"))
        btn_borrar_log.pack(side="right", padx=2)

        # Iniciar ciclos de monitoreo
        self.actualizar_monitoreo_ram()
        self.actualizar_cronometro_live()

    def obtener_usuarios_lista_blanca(self):
        raw_text = self.entry_lista.get()
        return {u.strip().lower().replace("@", "") for u in raw_text.split(",") if u.strip()}

    def actualizar_monitoreo_ram(self):
        try:
            ram_bytes = self.proceso_actual.memory_info().rss
            ram_mb = ram_bytes / (1024 * 1024)
            self.lbl_ram.config(text=f"RAM: {ram_mb:.1f} MB")
        except Exception:
            pass
        self.root.after(2000, self.actualizar_monitoreo_ram)

    def actualizar_cronometro_live(self):
        if self.conectado and self.tiempo_conexion_inicio:
            transcurrido = int(time.time() - self.tiempo_conexion_inicio)
            horas = transcurrido // 3600
            minutos = (transcurrido % 3600) // 60
            segundos = transcurrido % 60
            str_tiempo = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            self.lbl_tiempo_live.config(text=f"Live activo: {str_tiempo}", fg="#89b4fa")
        else:
            self.lbl_tiempo_live.config(text="Live activo: 00:00:00", fg="#6c7086")
            
        self.root.after(1000, self.actualizar_cronometro_live)

    def cambiar_volumen(self, val):
        pygame.mixer.music.set_volume(float(val))

    def conmutar_pausa(self):
        self.audio_pausado = not self.audio_pausado
        if self.audio_pausado:
            self.btn_pausa.config(text="Reanudar TTS", bg="#a6e3a1")
            self.agregar_log("[PAUSA] Audio Pausado")
        else:
            self.btn_pausa.config(text="Pausar TTS", bg="#f9e2af")
            self.agregar_log("[PLAY] Audio Reanudado")

    def probar_audio(self):
        enviar_a_voz("Prueba de audio realizada con éxito", forzar=True)

    def vaciar_cola(self):
        with cola_mensajes.mutex:
            cola_mensajes.queue.clear()
        pygame.mixer.music.stop()
        self.agregar_log("[INFO] Cola de mensajes limpiada")
        self.root.after(0, lambda: self.lbl_cola.config(text="En cola: 0/50"))

    def actualizar_estado(self, texto, color):
        self.root.after(0, lambda: self.lbl_estado.config(text=f"Estado: {texto}", fg=color))

    def agregar_log(self, mensaje):
        def _write():
            self.log_box.insert(tk.END, f"{mensaje}\n")
            self.log_box.see(tk.END)
            self.lbl_cola.config(text=f"En cola: {cola_mensajes.qsize()}/50")
        self.root.after(0, _write)

    def limpiar_cuadro_log(self):
        self.log_box.delete('1.0', tk.END)

    def exportar_log(self):
        contenido = self.log_box.get("1.0", tk.END).strip()
        if not contenido:
            self.agregar_log("[INFO] No hay registros para guardar.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Guardar Registro de Chat"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(contenido)
                self.agregar_log(f"[INFO] Registro guardado en: {filepath}")
            except Exception as e:
                self.agregar_log(f"[Error Guardado]: {e}")

    def alternar_conexion(self):
        if not self.conectado:
            usuario = self.entry_user.get().strip()
            if not usuario:
                self.agregar_log("[ALERTA] Ingresa un usuario válido")
                return
            if not usuario.startswith("@"):
                usuario = f"@{usuario}"
                self.entry_user.delete(0, tk.END)
                self.entry_user.insert(0, usuario)

            self.btn_conectar.config(text="Desconectar", bg="#f38ba8")
            self.entry_user.config(state="disabled")
            threading.Thread(target=iniciar_tiktok, args=(usuario,), daemon=True).start()
        else:
            self.conectado = False
            self.tiempo_conexion_inicio = None
            if self.client_tiktok:
                try:
                    self.client_tiktok.stop()
                except Exception:
                    pass
            self.vaciar_cola()
            self.btn_conectar.config(text="Conectar Live", bg="#a6e3a1")
            self.entry_user.config(state="normal")
            self.actualizar_estado("Desconectado", "#f38ba8")
            self.agregar_log("[INFO] Conexión finalizada")

    def al_cerrar(self):
        datos_guardar = {
            "usuario": self.entry_user.get().strip(),
            "volumen": float(self.slider_volumen.get()),
            "voz": self.combo_voz.get(),
            "velocidad": self.combo_vel.get(),
            "restringir_subs": bool(self.restringir_subs.get()),
            "restringir_mods": bool(self.restringir_mods.get()),
            "restringir_lista": bool(self.restringir_lista.get()),
            "lista_blanca": self.entry_lista.get().strip()
        }
        guardar_configuracion(datos_guardar)
        self.root.destroy()

gui = PanelControl()
# ==================== PROCESAMIENTO DE AUDIO ====================
def limpiar_emojis(texto):
    patron_emojis = re.compile(
        "["
        "\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF"
        "]+", flags=re.UNICODE
    )
    return patron_emojis.sub(r'', texto).strip()

async def generar_audio_bytes(texto, voz, velocidad):
    communicate = edge_tts.Communicate(texto, voz, rate=velocidad)
    data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            data.extend(chunk["data"])
    return io.BytesIO(data)

def procesar_audio():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        texto = cola_mensajes.get()
        try:
            if not gui.audio_pausado:
                voz_actual = gui.combo_voz.get()
                vel_actual = gui.combo_vel.get()
                audio_buffer = loop.run_until_complete(generar_audio_bytes(texto, voz_actual, vel_actual))
                
                pygame.mixer.music.load(audio_buffer, "mp3")
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                    
                pygame.mixer.music.unload()
        except Exception as e:
            gui.agregar_log(f"[Error Audio]: {e}")
        finally:
            cola_mensajes.task_done()
            gui.root.after(0, lambda: gui.lbl_cola.config(text=f"En cola: {cola_mensajes.qsize()}/50"))

threading.Thread(target=procesar_audio, daemon=True).start()

def enviar_a_voz(mensaje, forzar=False):
    if not gui.conectado and not forzar:
        return
    try:
        cola_mensajes.put(mensaje, timeout=0.2)
        gui.agregar_log(f"[AUDIO] {mensaje}")
    except queue.Full:
        gui.agregar_log("[ALERTA] Cola llena")
# ==================== LÓGICA DE VERIFICACIÓN ROBUSTA ====================
def es_suscriptor_nivel_2_o_superior(user) -> bool:
    if getattr(user, "is_subscriber", False):
        return True

    user_str = str(user).lower()
    if any(k in user_str for k in ["subscriber", "sub_level", "sub_grade", "subscription"]):
        return True

    badges = getattr(user, "badges", []) or getattr(user, "badge_list", []) or []
    for badge in badges:
        badge_str = str(badge).lower()
        if any(term in badge_str for term in ["subscriber", "sub", "sub_grade", "fans", "member"]):
            level = 0
            if isinstance(badge, dict):
                level = badge.get("level") or badge.get("sub_level") or 0
            else:
                priv_log = getattr(badge, "privilege_log_extra", None)
                if priv_log:
                    level = getattr(priv_log, "level", 0)
                else:
                    level = getattr(badge, "level", getattr(badge, "sub_level", 0))

            try:
                level = int(level)
            except (ValueError, TypeError):
                level = 0

            if level >= 2 or level == 0 or "subscriber" in badge_str:
                return True

    return False

def es_moderador(user) -> bool:
    if getattr(user, "is_moderator", False) or getattr(user, "is_admin", False):
        return True

    user_str = str(user).lower()
    if "moderator" in user_str or "admin" in user_str:
        return True

    badges = getattr(user, "badges", []) or getattr(user, "badge_list", []) or []
    for badge in badges:
        badge_str = str(badge).lower()
        if "moderator" in badge_str or "admin" in badge_str:
            return True

    return False

async def on_comment(event: CommentEvent) -> None:
    if not gui.conectado:
        return

    user = event.user
    username = str(getattr(user, "unique_id", getattr(user, "unique_id_str", ""))).lower()
    nickname = str(getattr(user, "nickname", username))
    comentario = event.comment.strip()
    
    if time.time() - TIEMPO_INICIO < 2:
        return

    modo_sub = bool(gui.restringir_subs.get())
    modo_mod = bool(gui.restringir_mods.get())
    modo_lista = bool(gui.restringir_lista.get())

    hay_restricciones = modo_sub or modo_mod or modo_lista

    es_sub = es_suscriptor_nivel_2_o_superior(user)
    es_mod = es_moderador(user)
    
    usuarios_permitidos = gui.obtener_usuarios_lista_blanca()
    esta_en_lista = (username in usuarios_permitidos)

    print(f"[DEBUG USER] @{username} | Mod: {es_mod} | Sub: {es_sub} | Lista Blanca: {esta_en_lista}")

    if not hay_restricciones:
        permitido = True
    else:
        permitido = (
            (modo_sub and es_sub) or 
            (modo_mod and es_mod) or 
            (modo_lista and esta_en_lista)
        )

    if permitido:
        id_mensaje = f"{username}:{comentario}"
        if id_mensaje in HISTORIAL_RECIENTE:
            return
            
        HISTORIAL_RECIENTE.append(id_mensaje)
        nombre_limpio = limpiar_emojis(nickname) or "Usuario"
        mensaje_tts = f"{nombre_limpio} dice: {comentario[:100]}"
        
        enviar_a_voz(mensaje_tts)

def iniciar_tiktok(unique_id):
    global TIEMPO_INICIO
    try:
        gui.actualizar_estado(f"Conectando a {unique_id}...", "#f9e2af")
        gui.client_tiktok = TikTokLiveClient(unique_id=unique_id)

        @gui.client_tiktok.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            global TIEMPO_INICIO
            gui.conectado = True
            gui.tiempo_conexion_inicio = time.time()
            TIEMPO_INICIO = time.time()
            HISTORIAL_RECIENTE.clear()
            gui.actualizar_estado(f"Conectado a @{event.unique_id}", "#a6e3a1")

        gui.client_tiktok.add_listener(CommentEvent, on_comment)
        gui.client_tiktok.run()
    except Exception as e:
        gui.conectado = False
        gui.tiempo_conexion_inicio = None
        gui.actualizar_estado("Error de Conexión", "#f38ba8")
        gui.agregar_log(f"[Error TikTok]: {e}")
        gui.root.after(0, lambda: gui.btn_conectar.config(text="Conectar Live", bg="#a6e3a1"))
        gui.root.after(0, lambda: gui.entry_user.config(state="normal"))

gui.root.mainloop()
