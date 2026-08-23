import os
import re
import time
import threading
import queue
import asyncio
import io
from collections import deque
import tkinter as tk
from tkinter import ttk, scrolledtext
import pygame
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent
import edge_tts

# ==================== CONFIGURACIÓN INICIAL ====================
VOLUMEN = 0.5
USUARIOS_PERMITIDOS = {"bjiunjark", "otro_amigo"}
VELOCIDAD_AUDIO = "+30%"
VOZ_TTS = "es-MX-JorgeNeural"
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
        self.root.geometry("520x720")
        self.root.configure(bg="#1e1e2e")
        self.root.attributes('-topmost', True)

        # Variables de Control
        self.audio_pausado = False
        self.restringir_subs = tk.BooleanVar(value=False)
        self.restringir_mods = tk.BooleanVar(value=False)
        self.restringir_lista = tk.BooleanVar(value=False)
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
        self.entry_user.insert(0, "@aaron84_pk")
        self.entry_user.pack(side="left", fill="x", expand=True, padx=10)

        self.btn_conectar = tk.Button(f_user, text="🔗 Conectar Live", bg="#a6e3a1", fg="#11111b", relief="flat", command=self.alternar_conexion, font=("Segoe UI", 9, "bold"))
        self.btn_conectar.pack(side="right")

        # --- SECCIÓN: ESTADO ---
        frame_estado = ttk.Frame(self.root)
        frame_estado.pack(fill="x", padx=15, pady=2)

        self.lbl_estado = tk.Label(frame_estado, text="Estado: Desconectado", fg="#f38ba8", bg="#1e1e2e", font=("Segoe UI", 10, "bold"))
        self.lbl_estado.pack(side="left")

        self.lbl_cola = ttk.Label(frame_estado, text="En cola: 0/50")
        self.lbl_cola.pack(side="right")

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
        self.combo_vel = ttk.Combobox(f_voces, values=["+0%", "+15%", "+30%", "+45%", "+60%"], state="readonly", width=8)
        self.combo_vel.set(VELOCIDAD_AUDIO)
        self.combo_vel.pack(side="left", padx=5)

        f_botones = ttk.Frame(frame_audio)
        f_botones.pack(fill="x", padx=10, pady=8)

        self.btn_pausa = tk.Button(f_botones, text="⏸️ Pausar TTS", bg="#f9e2af", fg="#11111b", relief="flat", command=self.conmutar_pausa, font=("Segoe UI", 9, "bold"))
        self.btn_pausa.pack(side="left", fill="x", expand=True, padx=2)

        btn_test = tk.Button(f_botones, text="🔊 Probar Audio", bg="#89b4fa", fg="#11111b", relief="flat", command=self.probar_audio, font=("Segoe UI", 9, "bold"))
        btn_test.pack(side="left", fill="x", expand=True, padx=2)

        btn_limpiar = tk.Button(f_botones, text="🗑️ Vaciar Cola", bg="#f38ba8", fg="#11111b", relief="flat", command=self.vaciar_cola, font=("Segoe UI", 9, "bold"))
        btn_limpiar.pack(side="left", fill="x", expand=True, padx=2)

        # --- SECCIÓN: MODO RESTRICTIVO ---
        frame_filtros = ttk.LabelFrame(self.root, text=" Modo Restrictivo (Sin marcar = Lee a TODO EL CHAT) ")
        frame_filtros.pack(fill="x", padx=15, pady=5)

        f_chk = ttk.Frame(frame_filtros)
        f_chk.pack(fill="x", padx=10, pady=5)
        ttk.Checkbutton(f_chk, text="Solo Subs (Niv 2+)", variable=self.restringir_subs).pack(side="left", expand=True)
        ttk.Checkbutton(f_chk, text="Solo Mods", variable=self.restringir_mods).pack(side="left", expand=True)
        ttk.Checkbutton(f_chk, text="Solo Lista", variable=self.restringir_lista).pack(side="left", expand=True)

        # --- SECCIÓN: LOG ---
        frame_log = ttk.LabelFrame(self.root, text=" Registro de Comentarios ")
        frame_log.pack(fill="both", expand=True, padx=15, pady=5)

        self.log_box = scrolledtext.ScrolledText(
            frame_log, height=10, bg="#11111b", fg="#a6e3a1", 
            insertbackground="white", font=("Consolas", 9), relief="flat"
        )
        self.log_box.pack(padx=8, pady=8, fill="both", expand=True)

    def cambiar_volumen(self, val):
        pygame.mixer.music.set_volume(float(val))

    def conmutar_pausa(self):
        self.audio_pausado = not self.audio_pausado
        if self.audio_pausado:
            self.btn_pausa.config(text="▶️ Reanudar TTS", bg="#a6e3a1")
            self.agregar_log("⏸️ Audio Pausado")
        else:
            self.btn_pausa.config(text="⏸️ Pausar TTS", bg="#f9e2af")
            self.agregar_log("▶️ Audio Reanudado")

    def probar_audio(self):
        enviar_a_voz("Prueba de audio realizada con éxito")

    def vaciar_cola(self):
        with cola_mensajes.mutex:
            cola_mensajes.queue.clear()
        self.agregar_log("🗑️ Cola de mensajes limpiada")
        self.root.after(0, lambda: self.lbl_cola.config(text="En cola: 0/50"))

    def actualizar_estado(self, texto, color):
        self.root.after(0, lambda: self.lbl_estado.config(text=f"Estado: {texto}", fg=color))

    def agregar_log(self, mensaje):
        def _write():
            self.log_box.insert(tk.END, f"{mensaje}\n")
            self.log_box.see(tk.END)
            self.lbl_cola.config(text=f"En cola: {cola_mensajes.qsize()}/50")
        self.root.after(0, _write)

    def alternar_conexion(self):
        if not self.conectado:
            usuario = self.entry_user.get().strip()
            if not usuario:
                self.agregar_log("⚠️ Ingresa un usuario válido")
                return
            if not usuario.startswith("@"):
                usuario = f"@{usuario}"
                self.entry_user.delete(0, tk.END)
                self.entry_user.insert(0, usuario)

            self.conectado = True
            self.btn_conectar.config(text="❌ Desconectar", bg="#f38ba8")
            self.entry_user.config(state="disabled")
            threading.Thread(target=iniciar_tiktok, args=(usuario,), daemon=True).start()
        else:
            self.conectado = False
            if self.client_tiktok:
                try:
                    self.client_tiktok.stop()
                except Exception:
                    pass
            self.btn_conectar.config(text="🔗 Conectar Live", bg="#a6e3a1")
            self.entry_user.config(state="normal")
            self.actualizar_estado("Desconectado", "#f38ba8")
            self.agregar_log("🛑 Conexión finalizada")

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

def enviar_a_voz(mensaje):
    try:
        cola_mensajes.put(mensaje, timeout=0.2)
        gui.agregar_log(f"🔊 {mensaje}")
    except queue.Full:
        gui.agregar_log("⚠️ [Omitido] Cola llena")

# ==================== LÓGICA TIKTOK ====================
def es_suscriptor_nivel_2_o_superior(user) -> bool:
    badges = getattr(user, "badges", []) or []
    for badge in badges:
        scene_type = str(getattr(badge, "scene_type", ""))
        if any(x in scene_type for x in ["FANS", "SUBSCRIBER", "10", "4"]):
            priv_log = getattr(badge, "privilege_log_extra", None)
            if priv_log:
                try:
                    if int(getattr(priv_log, "level", 0)) >= 2:
                        return True
                except ValueError:
                    pass
    return False

def es_moderador(user) -> bool:
    if getattr(user, "is_moderator", False):
        return True
    badges = getattr(user, "badges", []) or []
    for badge in badges:
        badge_str = str(badge).lower()
        scene_type = str(getattr(badge, "scene_type", "")).lower()
        if "moderator" in badge_str or "admin" in scene_type or "moderator" in scene_type:
            return True
    return False

async def on_comment(event: CommentEvent) -> None:
    username = event.user.unique_id.lower()
    comentario = event.comment.strip()
    
    if time.time() - TIEMPO_INICIO < 2:
        return

    modo_sub = gui.restringir_subs.get()
    modo_mod = gui.restringir_mods.get()
    modo_lista = gui.restringir_lista.get()

    hay_restricciones = modo_sub or modo_mod or modo_lista

    if not hay_restricciones:
        permitido = True
    else:
        es_sub = modo_sub and es_suscriptor_nivel_2_o_superior(event.user)
        es_mod = modo_mod and es_moderador(event.user)
        esta_en_lista = modo_lista and (username in USUARIOS_PERMITIDOS)
        permitido = es_sub or es_mod or esta_en_lista

    if permitido:
        id_mensaje = f"{username}:{comentario}"
        if id_mensaje in HISTORIAL_RECIENTE:
            return
            
        HISTORIAL_RECIENTE.append(id_mensaje)
        nombre_limpio = limpiar_emojis(event.user.nickname) or "Usuario"
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
            TIEMPO_INICIO = time.time()
            HISTORIAL_RECIENTE.clear()
            gui.actualizar_estado(f"Conectado a @{event.unique_id}", "#a6e3a1")

        gui.client_tiktok.add_listener(CommentEvent, on_comment)
        gui.client_tiktok.run()
    except Exception as e:
        if gui.conectado:
            gui.actualizar_estado("Error de Conexión", "#f38ba8")
            gui.agregar_log(f"[Error TikTok]: {e}")
            gui.conectado = False
            gui.root.after(0, lambda: gui.btn_conectar.config(text="🔗 Conectar Live", bg="#a6e3a1"))
            gui.root.after(0, lambda: gui.entry_user.config(state="normal"))

gui.root.mainloop()
