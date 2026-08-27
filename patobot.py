import os
import re
import time
import json
import threading
import queue
import asyncio
import io
import unicodedata
import urllib.request
import urllib.error
from collections import deque, defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, font
import pygame
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, FollowEvent, LikeEvent
import edge_tts
import psutil
import yt_dlp

CONFIG_FILE = "config.json"

CONFIG_DEFAULTS = {
    "usuario": "@",
    "volumen": 0.6,
    "volumen_alertas": 0.7,
    "volumen_musica": 0.2,
    "voz": "es-MX-JorgeNeural",
    "velocidad": "+30%",
    "tono": "+0Hz",
    "limite_caracteres": 100,
    "palabras_censuradas": "groseria1, groseria2",
    "reemplazos": "gg:yiyi, xq:porque, q: que k:que, 67:six seven, tbm:también",
    "restringir_subs": False,
    "nivel_sub_minimo": 2,
    "restringir_mods": False,
    "restringir_lista": False,
    "lista_blanca": "usuario, usuario",
    "lista_djs": "usuario_dj1, usuario_dj2",
    "alerta_regalos": True,
    "alerta_follows": True,
    "alerta_likes_general": True,
    "meta_likes_general": 1000,
    "repetir_likes_general": True,
    "alerta_likes_persona": True,
    "meta_likes_persona": 100,
    "repetir_likes_persona": True,
    "url_regalo": "https://www.myinstants.com/media/sounds/coin.mp3",
    "url_follow": "https://www.myinstants.com/media/sounds/discord-notification.mp3",
    "url_like_general": "https://www.myinstants.com/media/sounds/coin_1_8F9fpWu.mp3",
    "url_like_persona": "https://www.myinstants.com/media/sounds/coin.mp3",
    "cmd_play": "!play, !p",
    "cmd_skip": "!skip",
    "cmd_pause": "!pause",
    "cmd_resume": "!resume",
    "cmd_volume": "!volume, !vol",
    "perm_sub_play": True,
    "perm_sub_skip": False,
    "perm_sub_pause": False,
    "perm_sub_resume": False,
    "perm_sub_vol": False,
    "perm_mod_play": True,
    "perm_mod_skip": True,
    "perm_mod_pause": True,
    "perm_mod_resume": True,
    "perm_mod_vol": True,
    "perm_dj_play": True,
    "perm_dj_skip": True,
    "perm_dj_pause": True,
    "perm_dj_resume": True,
    "perm_dj_vol": True,
    "fuente_interfaz": "Segoe UI"
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
VOLUMEN_ALERTAS = config.get("volumen_alertas", 0.8)
VOLUMEN_MUSICA = config.get("volumen_musica", 0.4)
VELOCIDAD_AUDIO = config["velocidad"]
VOZ_TTS = config["voz"]
TONO_TTS = config.get("tono", "+0Hz")
HISTORIAL_RECIENTE = deque(maxlen=20)
TIEMPO_INICIO = time.time()
CONTADOR_LIKES_GENERAL = 0
LIKES_POR_USUARIO = defaultdict(int)

# Estado de skip (votos y cooldown anti-spam)
VOTOS_SKIP = set()
UMBRAL_VOTOS_SKIP = 3
ULTIMO_SKIP_TIEMPO = 0
COOLDOWN_SKIP_SEGUNDOS = 5

STATS = {
    "comentarios": 0,
    "regalos": 0,
    "follows": 0,
    "likes_totales": 0
}

pygame.mixer.init()
pygame.mixer.set_num_channels(16)
cola_mensajes = queue.Queue(maxsize=50)
cola_musica = deque()
cancion_actual = None
canal_musica_ram = None

def reproducir_sonido_url(url):
    url = url.strip()
    if not url or not url.startswith("http"):
        gui.agregar_log("[Alerta Audio]: Ingresa una URL válida que empiece por http")
        return

    def _stream_and_play():
        try:
            target_url = url
            if "myinstants.com" in target_url and not target_url.endswith(".mp3"):
                slug = target_url.rstrip("/").split("/")[-1]
                target_url = f"https://www.myinstants.com/media/sounds/{slug}.mp3"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'audio/mpeg, audio/*;q=0.9, */*;q=0.8',
                'Referer': 'https://www.myinstants.com/'
            }
            
            req = urllib.request.Request(target_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                audio_bytes = response.read()

            if not audio_bytes:
                gui.agregar_log("[Error MyInstants]: Archivo vacío.")
                return

            audio_buffer = io.BytesIO(audio_bytes)
            sonido = pygame.mixer.Sound(audio_buffer)
            
            canal = pygame.mixer.find_channel(True)
            if canal:
                volumen_alertas_real = float(gui.slider_volumen_alertas.get()) * 0.75
                canal.set_volume(volumen_alertas_real)
                canal.play(sonido)
            else:
                gui.agregar_log("[Error Audio]: Sin canales disponibles.")

        except Exception as e:
            gui.agregar_log(f"[Error Audio]: {e}")

    threading.Thread(target=_stream_and_play, daemon=True).start()

def limpiar_busqueda(query):
    query = re.sub(r'[^\w\s]', ' ', query.lower())
    palabras_basura = {'video', 'oficial', 'official', 'lyric', 'letra', 'audio', 'full', 'dj',  'hd'}
    palabras = [p for p in query.split() if p not in palabras_basura]
    return " ".join(palabras) if palabras else query

def obtener_stream_audio(busqueda):
    if busqueda.startswith("http"):
        motores = [busqueda]
    else:
        busqueda_limpia = limpiar_busqueda(busqueda)
        motores = [
            f"scsearch1:{busqueda_limpia}",
            f"ytsearch1:{busqueda_limpia}",
            f"ytsearch1:{busqueda_limpia} topic"
        ]

    ydl_opts = {
        'format': 'bestaudio[protocol^=http][protocol!=m3u8]/bestaudio[ext=mp3]/bestaudio',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'extract_flat': False,
        'max_filesize': 25000000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for motor in motores:
            try:
                info = ydl.extract_info(motor, download=False)
                if not info:
                    continue
                    
                if 'entries' in info and info['entries']:
                    entradas_validas = [e for e in info['entries'] if e is not None]
                    if not entradas_validas:
                        continue
                    info = entradas_validas[0]

                if not isinstance(info, dict):
                    continue
                duracion = info.get('duration', 0)
                if duracion > 600:
                    gui.agregar_log(f"[BÚSQUEDA] Ignorada (>10 min): {info.get('title')}")
                    continue
                stream_url = None
                if 'formats' in info:
                    for fmt in info['formats']:
                        protocol = fmt.get('protocol', '')
                        url_fmt = fmt.get('url', '')
                        if url_fmt and 'm3u8' not in protocol and '.m3u8' not in url_fmt:
                            stream_url = url_fmt
                            break
                if not stream_url:
                    candidate_url = info.get('url', '')
                    if candidate_url and '.m3u8' not in candidate_url:
                        stream_url = candidate_url

                if stream_url:
                    titulo_cancion = info.get('title', 'Canción Desconocida')
                    uploader = info.get('uploader', '')
                    if uploader and uploader.lower() not in titulo_cancion.lower():
                        titulo_cancion = f"{uploader} - {titulo_cancion}"
                    return stream_url, titulo_cancion

            except Exception as e:
                gui.agregar_log(f"[Error Búsqueda]: {e}")
                continue

    return None, None

def reproductor_musica_loop():
    global cancion_actual, VOTOS_SKIP, canal_musica_ram

    while True:
        esta_ocupado = canal_musica_ram and canal_musica_ram.get_busy()
        if cola_musica and not esta_ocupado and not getattr(gui, 'musica_pausada', False):
            query, usuario = cola_musica.popleft()
            gui.actualizar_lista_musica_ui()
            gui.agregar_log(f"[BÚSQUEDA] Buscando: {query}...")
            
            stream_url, titulo = obtener_stream_audio(query)
            if stream_url:
                try:
                    cancion_actual = f"{titulo} (Pedida por @{usuario})"
                    VOTOS_SKIP.clear()
                    gui.actualizar_cancion_actual_ui(cancion_actual)
                    
                    if canal_musica_ram:
                        canal_musica_ram.stop()

                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    req = urllib.request.Request(stream_url, headers=headers)
                    
                    buffer_ram = io.BytesIO()
                    with urllib.request.urlopen(req, timeout=15) as response:
                        while True:
                            chunk = response.read(16384)
                            if not chunk:
                                break
                            buffer_ram.write(chunk)
                    
                    buffer_ram.seek(0)
                    
                    if len(buffer_ram.getvalue()) > 10000:
                        sonido_cancion = pygame.mixer.Sound(buffer_ram)
                        canal_musica_ram = pygame.mixer.Channel(0)
                        
                        vol_val = float(gui.slider_volumen_musica.get()) if hasattr(gui, 'slider_volumen_musica') else VOLUMEN_MUSICA
                        canal_musica_ram.set_volume(vol_val * 0.25)
                        canal_musica_ram.play(sonido_cancion)
                        
                        gui.agregar_log(f"[REPRODUCIENDO EN RAM] {cancion_actual}")
                        
                        while canal_musica_ram.get_busy() or getattr(gui, 'musica_pausada', False):
                            time.sleep(1)

                        buffer_ram.close()
                        cancion_actual = None
                        VOTOS_SKIP.clear()
                        gui.actualizar_cancion_actual_ui("Ninguna")
                    else:
                        buffer_ram.close()
                        gui.agregar_log("[Error Reproducción]: Stream no compatible o vacío.")
                        cancion_actual = None
                        VOTOS_SKIP.clear()
                        gui.actualizar_cancion_actual_ui("Ninguna")

                except Exception as e:
                    gui.agregar_log(f"[Error Reproducción]: {e}")
                    cancion_actual = None
                    VOTOS_SKIP.clear()
                    gui.actualizar_cancion_actual_ui("Ninguna")
            else:
                gui.agregar_log(f"[MÚSQUEDA] No se encontró resultado válido para: {query}")
                cancion_actual = None
                VOTOS_SKIP.clear()
                gui.actualizar_cancion_actual_ui("Ninguna")
        time.sleep(1)

threading.Thread(target=reproductor_musica_loop, daemon=True).start()

class PanelControl:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TikTok Live Bot - Multiplataforma")
        self.root.geometry("640x980")
        self.root.configure(bg="#1e1e2e")
        self.root.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        self.proceso_actual = psutil.Process(os.getpid())
        self.tiempo_conexion_inicio = None

        self.audio_pausado = False
        self.musica_pausada = False
        self.restringir_subs = tk.BooleanVar(value=config["restringir_subs"])
        self.restringir_mods = tk.BooleanVar(value=config["restringir_mods"])
        self.restringir_lista = tk.BooleanVar(value=config["restringir_lista"])
        
        # Variables de permisos por rol para música
        self.perm_sub_play = tk.BooleanVar(value=config.get("perm_sub_play", True))
        self.perm_sub_skip = tk.BooleanVar(value=config.get("perm_sub_skip", False))
        self.perm_sub_pause = tk.BooleanVar(value=config.get("perm_sub_pause", False))
        self.perm_sub_resume = tk.BooleanVar(value=config.get("perm_sub_resume", False))
        self.perm_sub_vol = tk.BooleanVar(value=config.get("perm_sub_vol", False))

        self.perm_mod_play = tk.BooleanVar(value=config.get("perm_mod_play", True))
        self.perm_mod_skip = tk.BooleanVar(value=config.get("perm_mod_skip", True))
        self.perm_mod_pause = tk.BooleanVar(value=config.get("perm_mod_pause", True))
        self.perm_mod_resume = tk.BooleanVar(value=config.get("perm_mod_resume", True))
        self.perm_mod_vol = tk.BooleanVar(value=config.get("perm_mod_vol", True))

        self.perm_dj_play = tk.BooleanVar(value=config.get("perm_dj_play", True))
        self.perm_dj_skip = tk.BooleanVar(value=config.get("perm_dj_skip", True))
        self.perm_dj_pause = tk.BooleanVar(value=config.get("perm_dj_pause", True))
        self.perm_dj_resume = tk.BooleanVar(value=config.get("perm_dj_resume", True))
        self.perm_dj_vol = tk.BooleanVar(value=config.get("perm_dj_vol", True))

        self.alerta_regalos = tk.BooleanVar(value=config.get("alerta_regalos", True))
        self.alerta_follows = tk.BooleanVar(value=config.get("alerta_follows", True))
        
        self.alerta_likes_general = tk.BooleanVar(value=config.get("alerta_likes_general", True))
        self.repetir_likes_general = tk.BooleanVar(value=config.get("repetir_likes_general", True))
        
        self.alerta_likes_persona = tk.BooleanVar(value=config.get("alerta_likes_persona", True))
        self.repetir_likes_persona = tk.BooleanVar(value=config.get("repetir_likes_persona", True))
        
        self.client_tiktok = None
        self.conectado = False

        self.fuente_actual = config.get("fuente_interfaz", "Segoe UI")

        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabelframe", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("TLabelframe.Label", background="#1e1e2e", foreground="#cdd6f4", font=(self.fuente_actual, 9, "bold"))
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=(self.fuente_actual, 9))
        style.configure("TCheckbutton", background="#1e1e2e", foreground="#cdd6f4", font=(self.fuente_actual, 9))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_principal = ttk.Frame(self.notebook)
        self.tab_musica = ttk.Frame(self.notebook)
        self.tab_tts = ttk.Frame(self.notebook)
        self.tab_filtros = ttk.Frame(self.notebook)
        self.tab_alertas = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_principal, text=" Dashboard ")
        self.notebook.add(self.tab_musica, text=" Música y Comandos ")
        self.notebook.add(self.tab_tts, text=" Voz y TTS ")
        self.notebook.add(self.tab_filtros, text=" Filtros y Fuente ")
        self.notebook.add(self.tab_alertas, text=" Alertas ")
        # Dashboard
        frame_conexion = ttk.LabelFrame(self.tab_principal, text=" Conexión a Live ")
        frame_conexion.pack(fill="x", padx=10, pady=5)

        f_user = ttk.Frame(frame_conexion)
        f_user.pack(fill="x", padx=10, pady=8)
        ttk.Label(f_user, text="Usuario Live:").pack(side="left")
        self.entry_user = tk.Entry(f_user, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 10), relief="flat")
        self.entry_user.insert(0, config["usuario"])
        self.entry_user.pack(side="left", fill="x", expand=True, padx=10)
        self.btn_conectar = tk.Button(f_user, text="Conectar Live", bg="#a6e3a1", fg="#11111b", relief="flat", command=self.alternar_conexion, font=(self.fuente_actual, 9, "bold"))
        self.btn_conectar.pack(side="right")
        frame_estado = ttk.Frame(self.tab_principal)
        frame_estado.pack(fill="x", padx=10, pady=2)
        self.lbl_estado = tk.Label(frame_estado, text="Estado: Desconectado", fg="#f38ba8", bg="#1e1e2e", font=(self.fuente_actual, 10, "bold"))
        self.lbl_estado.pack(side="left")
        self.lbl_ram = ttk.Label(frame_estado, text="RAM: 0.0 MB")
        self.lbl_ram.pack(side="right", padx=(10, 0))
        self.lbl_cola = ttk.Label(frame_estado, text="En cola: 0/50")
        self.lbl_cola.pack(side="right")

        frame_tiempo = ttk.Frame(self.tab_principal)
        frame_tiempo.pack(fill="x", padx=10, pady=2)
        self.lbl_tiempo_live = tk.Label(frame_tiempo, text="Live activo: 00:00:00", fg="#89b4fa", bg="#1e1e2e", font=(self.fuente_actual, 10, "bold"))
        self.lbl_tiempo_live.pack(side="left")

        frame_stats = ttk.LabelFrame(self.tab_principal, text=" Estadísticas del Stream ")
        frame_stats.pack(fill="x", padx=10, pady=5)
        f_m = ttk.Frame(frame_stats)
        f_m.pack(fill="x", padx=5, pady=5)
        self.lbl_stat_chat = ttk.Label(f_m, text="Leídos: 0")
        self.lbl_stat_chat.pack(side="left", expand=True)
        self.lbl_stat_gifts = ttk.Label(f_m, text="Regalos: 0")
        self.lbl_stat_gifts.pack(side="left", expand=True)
        self.lbl_stat_follows = ttk.Label(f_m, text="Follows: 0")
        self.lbl_stat_follows.pack(side="left", expand=True)
        self.lbl_stat_likes = ttk.Label(f_m, text="Likes: 0")
        self.lbl_stat_likes.pack(side="left", expand=True)
        frame_ctrl_dash = ttk.LabelFrame(self.tab_principal, text=" Control de Música ")
        frame_ctrl_dash.pack(fill="x", padx=10, pady=5)
        f_btn_dash = ttk.Frame(frame_ctrl_dash)
        f_btn_dash.pack(fill="x", padx=5, pady=5)
        self.btn_pause_musica = tk.Button(
            f_btn_dash, text="Pausar / Reanudar", bg="#f9e2af", fg="#11111b", 
            relief="flat", command=self.alternar_pausa_musica, font=(self.fuente_actual, 9, "bold")
        )
        self.btn_pause_musica.pack(side="left", fill="x", expand=True, padx=3)

        btn_next_musica = tk.Button(
            f_btn_dash, text="Siguiente (Next) ⏭", bg="#89b4fa", fg="#11111b", 
            relief="flat", command=self.saltar_cancion_manual, font=(self.fuente_actual, 9, "bold")
        )
        btn_next_musica.pack(side="left", fill="x", expand=True, padx=3)

        frame_log = ttk.LabelFrame(self.tab_principal, text=" Registro de Eventos y Chat ")
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_box = scrolledtext.ScrolledText(frame_log, height=10, bg="#11111b", fg="#a6e3a1", insertbackground="white", font=(self.fuente_actual, 9), relief="flat")
        self.log_box.pack(padx=8, pady=5, fill="both", expand=True)
        f_log_acc = ttk.Frame(frame_log)
        f_log_acc.pack(fill="x", padx=8, pady=5)
        btn_guardar_log = tk.Button(f_log_acc, text="Guardar Registro (.txt)", bg="#89b4fa", fg="#11111b", relief="flat", command=self.exportar_log, font=(self.fuente_actual, 8, "bold"))
        btn_guardar_log.pack(side="left", padx=2)
        btn_borrar_log = tk.Button(f_log_acc, text="Limpiar Cuadro", bg="#f38ba8", fg="#11111b", relief="flat", command=self.limpiar_cuadro_log, font=(self.fuente_actual, 8, "bold"))
        btn_borrar_log.pack(side="right", padx=2)
        # Tab Música
        frame_rep_actual = ttk.LabelFrame(self.tab_musica, text=" Reproducción Actual ")
        frame_rep_actual.pack(fill="x", padx=10, pady=5)
        self.lbl_now_playing = tk.Label(frame_rep_actual, text="Sonando: Ninguna", fg="#a6e3a1", bg="#1e1e2e", font=(self.fuente_actual, 9, "bold"), anchor="w", justify="left")
        self.lbl_now_playing.pack(fill="x", padx=10, pady=5)

        frame_vol_musica = ttk.LabelFrame(self.tab_musica, text=" Control de Volumen ")
        frame_vol_musica.pack(fill="x", padx=10, pady=5)
        f_vol_m = ttk.Frame(frame_vol_musica)
        f_vol_m.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_vol_m, text="Volumen Música:").pack(side="left")
        self.slider_volumen_musica = ttk.Scale(f_vol_m, from_=0.0, to=1.0, value=VOLUMEN_MUSICA, command=self.cambiar_volumen_musica)
        self.slider_volumen_musica.pack(side="left", fill="x", expand=True, padx=10)

        # Matriz de Permisos por Rol para Música
        frame_perm_musica = ttk.LabelFrame(self.tab_musica, text=" Permisos de Comandos por Rol ")
        frame_perm_musica.pack(fill="x", padx=10, pady=5)

        f_djs = ttk.Frame(frame_perm_musica)
        f_djs.pack(fill="x", padx=5, pady=2)
        ttk.Label(f_djs, text="Lista DJs (separados por coma):").pack(side="left")
        self.entry_djs = tk.Entry(f_djs, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 8), relief="flat")
        self.entry_djs.insert(0, config.get("lista_djs", ""))
        self.entry_djs.pack(side="left", fill="x", expand=True, padx=5)

        # Encabezados de la tabla de permisos
        f_grid_hdr = ttk.Frame(frame_perm_musica)
        f_grid_hdr.pack(fill="x", padx=5, pady=2)
        ttk.Label(f_grid_hdr, text="Rol", width=12, font=(self.fuente_actual, 8, "bold")).pack(side="left")
        for h in ["Play", "Skip", "Pause", "Resume", "Vol"]:
            ttk.Label(f_grid_hdr, text=h, width=7, anchor="center", font=(self.fuente_actual, 8, "bold")).pack(side="left", expand=True)

        # Fila Suscriptores
        f_row_sub = ttk.Frame(frame_perm_musica)
        f_row_sub.pack(fill="x", padx=5, pady=1)
        ttk.Label(f_row_sub, text="Suscriptores:", width=12).pack(side="left")
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_play).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_skip).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_pause).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_resume).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_vol).pack(side="left", expand=True)

        # Fila Moderadores
        f_row_mod = ttk.Frame(frame_perm_musica)
        f_row_mod.pack(fill="x", padx=5, pady=1)
        ttk.Label(f_row_mod, text="Moderadores:", width=12).pack(side="left")
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_play).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_skip).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_pause).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_resume).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_vol).pack(side="left", expand=True)

        # Fila DJs
        f_row_dj = ttk.Frame(frame_perm_musica)
        f_row_dj.pack(fill="x", padx=5, pady=1)
        ttk.Label(f_row_dj, text="DJs:", width=12).pack(side="left")
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_play).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_skip).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_pause).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_resume).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_vol).pack(side="left", expand=True)

        frame_lista_musica = ttk.LabelFrame(self.tab_musica, text=" Lista de Espera Musical ")
        frame_lista_musica.pack(fill="both", expand=True, padx=10, pady=5)

        self.listbox_musica = tk.Listbox(frame_lista_musica, bg="#11111b", fg="#cdd6f4", selectbackground="#45475a", font=(self.fuente_actual, 9), relief="flat")
        self.listbox_musica.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar_musica = ttk.Scrollbar(frame_lista_musica, orient="vertical", command=self.listbox_musica.yview)
        scrollbar_musica.pack(side="right", fill="y", padx=(0, 8), pady=8)
        self.listbox_musica.config(yscrollcommand=scrollbar_musica.set)

        f_btn_mus = ttk.Frame(self.tab_musica)
        f_btn_mus.pack(fill="x", padx=10, pady=5)
        btn_up_song = tk.Button(f_btn_mus, text="⬆ Arriba", bg="#89b4fa", fg="#11111b", relief="flat", command=self.mover_cancion_arriba, font=(self.fuente_actual, 8, "bold"))
        btn_up_song.pack(side="left", padx=2)
        btn_down_song = tk.Button(f_btn_mus, text="⬇ Abajo", bg="#89b4fa", fg="#11111b", relief="flat", command=self.mover_cancion_abajo, font=(self.fuente_actual, 8, "bold"))
        btn_down_song.pack(side="left", padx=2)
        btn_del_song = tk.Button(f_btn_mus, text="Eliminar", bg="#f38ba8", fg="#11111b", relief="flat", command=self.eliminar_cancion_lista, font=(self.fuente_actual, 8, "bold"))
        btn_del_song.pack(side="left", padx=2)
        btn_clear_queue = tk.Button(f_btn_mus, text="Vaciar Lista", bg="#fab387", fg="#11111b", relief="flat", command=self.vaciar_lista_musica, font=(self.fuente_actual, 8, "bold"))
        btn_clear_queue.pack(side="right", padx=2)

        frame_cmd_cfg = ttk.LabelFrame(self.tab_musica, text=" Comandos del Chat Configurables ")
        frame_cmd_cfg.pack(fill="x", padx=10, pady=5)

        def _crear_campo_cmd(parent, label_text, default_val):
            f = ttk.Frame(parent)
            f.pack(fill="x", padx=5, pady=2)
            ttk.Label(f, text=label_text, width=15, anchor="w").pack(side="left")
            entry = tk.Entry(f, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 9), relief="flat")
            entry.insert(0, config.get(default_val, ""))
            entry.pack(side="left", fill="x", expand=True, padx=5)
            return entry
            
        self.entry_cmd_play = _crear_campo_cmd(frame_cmd_cfg, "Play:", "cmd_play")
        self.entry_cmd_skip = _crear_campo_cmd(frame_cmd_cfg, "Skip:", "cmd_skip")
        self.entry_cmd_pause = _crear_campo_cmd(frame_cmd_cfg, "Pausar:", "cmd_pause")
        self.entry_cmd_resume = _crear_campo_cmd(frame_cmd_cfg, "Reanudar:", "cmd_resume")
        self.entry_cmd_vol = _crear_campo_cmd(frame_cmd_cfg, "Volumen:", "cmd_volume")
        # Voz y TTS
        frame_audio_cfg = ttk.LabelFrame(self.tab_tts, text=" Parámetros de Síntesis de Voz ")
        frame_audio_cfg.pack(fill="x", padx=10, pady=5)
        f_vol = ttk.Frame(frame_audio_cfg)
        f_vol.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_vol, text="Volumen TTS/General:").pack(side="left")
        self.slider_volumen = ttk.Scale(f_vol, from_=0.0, to=1.0, value=VOLUMEN, command=self.cambiar_volumen)
        self.slider_volumen.pack(side="left", fill="x", expand=True, padx=10)
        f_voces = ttk.Frame(frame_audio_cfg)
        f_voces.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_voces, text="Voz Seleccionada:").pack(side="left")
        self.combo_voz = ttk.Combobox(f_voces, values=[
            "es-MX-JorgeNeural", "es-MX-DaliaNeural", "es-ES-ElviraNeural", 
            "es-ES-AlvaroNeural", "es-AR-TomasNeural", "es-CL-LorenzoNeural"
        ], state="readonly", width=22)
        self.combo_voz.set(VOZ_TTS)
        self.combo_voz.pack(side="left", padx=(5, 10))

        f_pitch_vel = ttk.Frame(frame_audio_cfg)
        f_pitch_vel.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_pitch_vel, text="Velocidad:").pack(side="left")
        self.combo_vel = ttk.Combobox(f_pitch_vel, values=["+0%", "+15%", "+30%", "+45%", "+60%"], state="readonly", width=8)
        self.combo_vel.set(VELOCIDAD_AUDIO)
        self.combo_vel.pack(side="left", padx=5)

        ttk.Label(f_pitch_vel, text="Tono (Pitch):").pack(side="left", padx=(15, 0))
        self.combo_tono = ttk.Combobox(f_pitch_vel, values=["-10Hz", "-5Hz", "+0Hz", "+5Hz", "+10Hz"], state="readonly", width=8)
        self.combo_tono.set(TONO_TTS)
        self.combo_tono.pack(side="left", padx=5)
        f_limite = ttk.Frame(frame_audio_cfg)
        f_limite.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_limite, text="Máximo Caracteres por Mensaje:").pack(side="left")
        self.entry_limite = tk.Entry(f_limite, bg="#11111b", fg="#cdd6f4", insertbackground="white", width=8, relief="flat")
        self.entry_limite.insert(0, str(config.get("limite_caracteres", 100)))
        self.entry_limite.pack(side="left", padx=10)

        f_botones_tts = ttk.Frame(self.tab_tts)
        f_botones_tts.pack(fill="x", padx=10, pady=10)
        self.btn_pausa = tk.Button(f_botones_tts, text="Pausar TTS", bg="#f9e2af", fg="#11111b", relief="flat", command=self.conmutar_pausa, font=(self.fuente_actual, 9, "bold"))
        self.btn_pausa.pack(side="left", fill="x", expand=True, padx=2)
        btn_test = tk.Button(f_botones_tts, text="Probar Audio", bg="#89b4fa", fg="#11111b", relief="flat", command=self.probar_audio, font=(self.fuente_actual, 9, "bold"))
        btn_test.pack(side="left", fill="x", expand=True, padx=2)
        btn_limpiar = tk.Button(f_botones_tts, text="Vaciar Cola", bg="#f38ba8", fg="#11111b", relief="flat", command=self.vaciar_cola, font=(self.fuente_actual, 9, "bold"))
        btn_limpiar.pack(side="left", fill="x", expand=True, padx=2)

        # Filtros y Selección de Fuente
        frame_tipografia = ttk.LabelFrame(self.tab_filtros, text=" Personalización de Fuente (GUI) ")
        frame_tipografia.pack(fill="x", padx=10, pady=5)
        f_font = ttk.Frame(frame_tipografia)
        f_font.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_font, text="Tipografía del sistema:").pack(side="left")

        fuentes_disponibles = sorted(font.families())
        self.combo_fuente = ttk.Combobox(f_font, values=fuentes_disponibles, state="readonly", width=22)
        self.combo_fuente.set(self.fuente_actual if self.fuente_actual in fuentes_disponibles else fuentes_disponibles[0])
        self.combo_fuente.pack(side="left", padx=10)

        btn_aplicar_fuente = tk.Button(
            f_font, text="Aplicar Fuente", bg="#89b4fa", fg="#11111b", 
            relief="flat", command=self.aplicar_nueva_fuente, font=(self.fuente_actual, 8, "bold")
        )
        btn_aplicar_fuente.pack(side="left")

        frame_filtros = ttk.LabelFrame(self.tab_filtros, text=" Restricciones de Lectura ")
        frame_filtros.pack(fill="x", padx=10, pady=5)
        f_chk = ttk.Frame(frame_filtros)
        f_chk.pack(fill="x", padx=10, pady=5)
        ttk.Checkbutton(f_chk, text="Solo Subs", variable=self.restringir_subs).pack(side="left")
        ttk.Label(f_chk, text="Nivel Mín:").pack(side="left", padx=(10, 2))
        self.entry_nivel_sub = tk.Entry(f_chk, bg="#11111b", fg="#cdd6f4", insertbackground="white", width=4, relief="flat")
        self.entry_nivel_sub.insert(0, str(config.get("nivel_sub_minimo", 2)))
        self.entry_nivel_sub.pack(side="left", padx=(0, 15))
        ttk.Checkbutton(f_chk, text="Solo Mods", variable=self.restringir_mods).pack(side="left", expand=True)
        ttk.Checkbutton(f_chk, text="Solo Lista Blanca", variable=self.restringir_lista).pack(side="left", expand=True)

        f_lista = ttk.Frame(frame_filtros)
        f_lista.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_lista, text="Lista Blanca (separados por coma):").pack(anchor="w")
        self.entry_lista = tk.Entry(f_lista, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 9), relief="flat")
        self.entry_lista.insert(0, config.get("lista_blanca", ""))
        self.entry_lista.pack(fill="x", pady=3)
        frame_censura = ttk.LabelFrame(self.tab_filtros, text=" Filtro de Palabras Prohibidas ")
        frame_censura.pack(fill="x", padx=10, pady=5)
        f_cen = ttk.Frame(frame_censura)
        f_cen.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_cen, text="Palabras a omitir/censurar:").pack(anchor="w")
        self.entry_censura = tk.Entry(f_cen, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 9), relief="flat")
        self.entry_censura.insert(0, config.get("palabras_censuradas", ""))
        self.entry_censura.pack(fill="x", pady=3)
        frame_reemplazos = ttk.LabelFrame(self.tab_filtros, text=" Diccionario de Reemplazos ")
        frame_reemplazos.pack(fill="x", padx=10, pady=5)
        f_rep = ttk.Frame(frame_reemplazos)
        f_rep.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_rep, text="Reemplazar (Formato orig:nuevo):").pack(anchor="w")
        self.entry_reemplazos = tk.Entry(f_rep, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 9), relief="flat")
        self.entry_reemplazos.insert(0, config.get("reemplazos", ""))
        self.entry_reemplazos.pack(fill="x", pady=3)
        # Alertas
        frame_alertas_audio = ttk.LabelFrame(self.tab_alertas, text=" Control de Sonidos MyInstants ")
        frame_alertas_audio.pack(fill="x", padx=10, pady=5)
        f_vol_alt = ttk.Frame(frame_alertas_audio)
        f_vol_alt.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_vol_alt, text="Volumen Alertas:").pack(side="left")
        self.slider_volumen_alertas = ttk.Scale(f_vol_alt, from_=0.0, to=1.0, value=VOLUMEN_ALERTAS)
        self.slider_volumen_alertas.pack(side="left", fill="x", expand=True, padx=10)

        f_reg = ttk.Frame(frame_alertas_audio)
        f_reg.pack(fill="x", padx=10, pady=5)
        ttk.Checkbutton(f_reg, text="Regalos:", variable=self.alerta_regalos).pack(side="left")
        self.entry_url_regalo = tk.Entry(f_reg, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 8), relief="flat")
        self.entry_url_regalo.insert(0, config.get("url_regalo", ""))
        self.entry_url_regalo.pack(side="left", fill="x", expand=True, padx=5)

        f_fol = ttk.Frame(frame_alertas_audio)
        f_fol.pack(fill="x", padx=10, pady=5)
        ttk.Checkbutton(f_fol, text="Follows:", variable=self.alerta_follows).pack(side="left")
        self.entry_url_follow = tk.Entry(f_fol, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 8), relief="flat")
        self.entry_url_follow.insert(0, config.get("url_follow", ""))
        self.entry_url_follow.pack(side="left", fill="x", expand=True, padx=5)

        frame_likes_gen = ttk.LabelFrame(self.tab_alertas, text=" Meta de Likes General ")
        frame_likes_gen.pack(fill="x", padx=10, pady=5)
        f_lik_gen_cfg = ttk.Frame(frame_likes_gen)
        f_lik_gen_cfg.pack(fill="x", padx=5, pady=3)
        ttk.Checkbutton(f_lik_gen_cfg, text="Activar", variable=self.alerta_likes_general).pack(side="left")
        ttk.Label(f_lik_gen_cfg, text="Cada:").pack(side="left", padx=(10, 2))
        self.entry_meta_likes_general = tk.Entry(f_lik_gen_cfg, bg="#11111b", fg="#cdd6f4", insertbackground="white", width=6, relief="flat")
        self.entry_meta_likes_general.insert(0, str(config.get("meta_likes_general", 100)))
        self.entry_meta_likes_general.pack(side="left", padx=(0, 10))
        ttk.Checkbutton(f_lik_gen_cfg, text="Repetir infinitamente", variable=self.repetir_likes_general).pack(side="left")

        f_lik_gen_url = ttk.Frame(frame_likes_gen)
        f_lik_gen_url.pack(fill="x", padx=5, pady=3)
        ttk.Label(f_lik_gen_url, text="Audio URL:").pack(side="left")
        self.entry_url_like_general = tk.Entry(f_lik_gen_url, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 8), relief="flat")
        self.entry_url_like_general.insert(0, config.get("url_like_general", ""))
        self.entry_url_like_general.pack(side="left", fill="x", expand=True, padx=5)

        frame_likes_per = ttk.LabelFrame(self.tab_alertas, text=" Meta de Likes por Persona ")
        frame_likes_per.pack(fill="x", padx=10, pady=5)
        f_lik_per_cfg = ttk.Frame(frame_likes_per)
        f_lik_per_cfg.pack(fill="x", padx=5, pady=3)
        ttk.Checkbutton(f_lik_per_cfg, text="Activar", variable=self.alerta_likes_persona).pack(side="left")
        ttk.Label(f_lik_per_cfg, text="Cada:").pack(side="left", padx=(10, 2))
        self.entry_meta_likes_persona = tk.Entry(f_lik_per_cfg, bg="#11111b", fg="#cdd6f4", insertbackground="white", width=6, relief="flat")
        self.entry_meta_likes_persona.insert(0, str(config.get("meta_likes_persona", 50)))
        self.entry_meta_likes_persona.pack(side="left", padx=(0, 10))
        ttk.Checkbutton(f_lik_per_cfg, text="Repetir por usuario", variable=self.repetir_likes_persona).pack(side="left")

        f_lik_per_url = ttk.Frame(frame_likes_per)
        f_lik_per_url.pack(fill="x", padx=5, pady=3)
        ttk.Label(f_lik_per_url, text="Audio URL:").pack(side="left")
        self.entry_url_like_persona = tk.Entry(f_lik_per_url, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 8), relief="flat")
        self.entry_url_like_persona.insert(0, config.get("url_like_persona", ""))
        self.entry_url_like_persona.pack(side="left", fill="x", expand=True, padx=5)

        self.actualizar_monitoreo_ram()
        self.actualizar_cronometro_live()
    def aplicar_nueva_fuente(self):
        nueva_fuente = self.combo_fuente.get()
        self.fuente_actual = nueva_fuente
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=(nueva_fuente, 9, "bold"))
        style.configure("TLabel", font=(nueva_fuente, 9))
        style.configure("TCheckbutton", font=(nueva_fuente, 9))
        self.log_box.config(font=(nueva_fuente, 9))
        self.listbox_musica.config(font=(nueva_fuente, 9))
        self.lbl_now_playing.config(font=(nueva_fuente, 9, "bold"))
        self.lbl_estado.config(font=(nueva_fuente, 10, "bold"))
        self.lbl_tiempo_live.config(font=(nueva_fuente, 10, "bold"))
        self.agregar_log(f"[GUI] Tipografía cambiada a: {nueva_fuente}")

    def cambiar_volumen_musica(self, val):
        global canal_musica_ram
        volumen_real = float(val) * 0.25
        if canal_musica_ram:
            canal_musica_ram.set_volume(volumen_real)

    def alternar_pausa_musica(self):
        global cancion_actual, canal_musica_ram
        if self.musica_pausada:
            if canal_musica_ram:
                canal_musica_ram.unpause()
            self.musica_pausada = False
            self.agregar_log("[MÚSQUEDA] Música reanudada manualmente.")
        elif (canal_musica_ram and canal_musica_ram.get_busy()) or cancion_actual:
            if canal_musica_ram:
                canal_musica_ram.pause()
            self.musica_pausada = True
            self.agregar_log("[MÚSQUEDA] Música pausada manualmente.")
            
    def saltar_cancion_manual(self):
        global cancion_actual, VOTOS_SKIP, canal_musica_ram
        self.musica_pausada = False
        if (canal_musica_ram and canal_musica_ram.get_busy()) or cancion_actual:
            if canal_musica_ram:
                canal_musica_ram.stop()
            VOTOS_SKIP.clear()
            self.agregar_log("[MÚSQUEDA] Canción saltada desde el Dashboard.")
        else:
            self.agregar_log("[MÚSQUEDA] No hay canción activa para saltar.")

    def obtener_lista_comandos(self, entry_widget):
        raw = entry_widget.get().strip().lower()
        return [c.strip() for c in raw.split(",") if c.strip()]

    def obtener_usuarios_djs(self):
        raw_text = self.entry_djs.get()
        return {u.strip().lower().replace("@", "") for u in raw_text.split(",") if u.strip()}

    def actualizar_lista_musica_ui(self):
        def _update():
            seleccion_previa = self.listbox_musica.curselection()
            self.listbox_musica.delete(0, tk.END)
            for idx, (query, usuario) in enumerate(cola_musica, start=1):
                self.listbox_musica.insert(tk.END, f"{idx}. {query} (por @{usuario})")
            
            if seleccion_previa and seleccion_previa[0] < len(cola_musica):
                self.listbox_musica.select_set(seleccion_previa[0])

        self.root.after(0, _update)

    def actualizar_cancion_actual_ui(self, texto):
        self.root.after(0, lambda: self.lbl_now_playing.config(text=f"Sonando: {texto}"))

    def mover_cancion_arriba(self):
        try:
            seleccion = self.listbox_musica.curselection()
            if seleccion:
                index = seleccion[0]
                if index > 0:
                    cola_musica[index], cola_musica[index - 1] = cola_musica[index - 1], cola_musica[index]
                    self.actualizar_lista_musica_ui()
                    self.listbox_musica.select_set(index - 1)
        except Exception as e:
            self.agregar_log(f"[Error UI]: {e}")

    def mover_cancion_abajo(self):
        try:
            seleccion = self.listbox_musica.curselection()
            if seleccion:
                index = seleccion[0]
                if index < len(cola_musica) - 1:
                    cola_musica[index], cola_musica[index + 1] = cola_musica[index + 1], cola_musica[index]
                    self.actualizar_lista_musica_ui()
                    self.listbox_musica.select_set(index + 1)
        except Exception as e:
            self.agregar_log(f"[Error UI]: {e}")

    def eliminar_cancion_lista(self):
        try:
            seleccion = self.listbox_musica.curselection()
            if seleccion:
                index = seleccion[0]
                del cola_musica[index]
                self.actualizar_lista_musica_ui()
                self.agregar_log(f"[MÚSQUEDA] Canción en índice {index+1} eliminada de la cola.")
        except Exception as e:
            self.agregar_log(f"[Error UI]: {e}")

    def vaciar_lista_musica(self):
        cola_musica.clear()
        self.actualizar_lista_musica_ui()
        self.agregar_log("[MÚSQUEDA] Lista de espera musical vaciada.")

    def obtener_meta_likes_general(self):
        try:
            val = int(self.entry_meta_likes_general.get().strip())
            return val if val > 0 else 100
        except ValueError:
            return 100

    def obtener_meta_likes_persona(self):
        try:
            val = int(self.entry_meta_likes_persona.get().strip())
            return val if val > 0 else 50
        except ValueError:
            return 50

    def obtener_nivel_minimo_sub(self):
        try:
            return int(self.entry_nivel_sub.get().strip())
        except ValueError:
            return 1

    def obtener_usuarios_lista_blanca(self):
        raw_text = self.entry_lista.get()
        return {u.strip().lower().replace("@", "") for u in raw_text.split(",") if u.strip()}

    def obtener_palabras_censuradas(self):
        raw_text = self.entry_censura.get()
        return [p.strip().lower() for p in raw_text.split(",") if p.strip()]

    def obtener_diccionario_reemplazos(self):
        raw_text = self.entry_reemplazos.get()
        diccionario = {}
        items = raw_text.split(",")
        for item in items:
            if ":" in item:
                clave, valor = item.split(":", 1)
                if clave.strip():
                    diccionario[clave.strip().lower()] = valor.strip()
        return diccionario

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

    def actualizar_metricas_ui(self):
        self.root.after(0, lambda: self.lbl_stat_chat.config(text=f"Leídos: {STATS['comentarios']}"))
        self.root.after(0, lambda: self.lbl_stat_gifts.config(text=f"Regalos: {STATS['regalos']}"))
        self.root.after(0, lambda: self.lbl_stat_follows.config(text=f"Follows: {STATS['follows']}"))
        self.root.after(0, lambda: self.lbl_stat_likes.config(text=f"Likes: {STATS['likes_totales']}"))

    def cambiar_volumen(self, val):
        pass

    def conmutar_pausa(self):
        self.audio_pausado = not self.audio_pausado
        if self.audio_pausado:
            self.btn_pausa.config(text="Reanudar TTS", bg="#a6e3a1")
            self.agregar_log("[PAUSA] Audio Pausado")
        else:
            self.btn_pausa.config(text="Pausar TTS", bg="#f9e2af")
            self.agregar_log("[PLAY] Audio Reanudado")

    def probar_audio(self):
        enviar_a_voz("Prueba de sonido en proceso", forzar=True)
        url = self.entry_url_like_general.get().strip()
        reproducir_sonido_url(url)
    def vaciar_cola(self):
        global canal_musica_ram
        with cola_mensajes.mutex:
            cola_mensajes.queue.clear()
        if canal_musica_ram:
            canal_musica_ram.stop()
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
            self.agregar_log("[INFO] No hay registros.")
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
        try:
            limite_val = int(self.entry_limite.get())
        except ValueError:
            limite_val = 100

        datos_guardar = {
            "usuario": self.entry_user.get().strip(),
            "volumen": float(self.slider_volumen.get()),
            "volumen_alertas": float(self.slider_volumen_alertas.get()),
            "volumen_musica": float(self.slider_volumen_musica.get()),
            "voz": self.combo_voz.get(),
            "velocidad": self.combo_vel.get(),
            "tono": self.combo_tono.get(),
            "limite_caracteres": limite_val,
            "palabras_censuradas": self.entry_censura.get().strip(),
            "reemplazos": self.entry_reemplazos.get().strip(),
            "restringir_subs": bool(self.restringir_subs.get()),
            "nivel_sub_minimo": self.obtener_nivel_minimo_sub(),
            "restringir_mods": bool(self.restringir_mods.get()),
            "restringir_lista": bool(self.restringir_lista.get()),
            "lista_blanca": self.entry_lista.get().strip(),
            "lista_djs": self.entry_djs.get().strip(),
            "alerta_regalos": bool(self.alerta_regalos.get()),
            "alerta_follows": bool(self.alerta_follows.get()),
            "alerta_likes_general": bool(self.alerta_likes_general.get()),
            "meta_likes_general": self.obtener_meta_likes_general(),
            "repetir_likes_general": bool(self.repetir_likes_general.get()),
            "alerta_likes_persona": bool(self.alerta_likes_persona.get()),
            "meta_likes_persona": self.obtener_meta_likes_persona(),
            "repetir_likes_persona": bool(self.repetir_likes_persona.get()),
            "url_regalo": self.entry_url_regalo.get().strip(),
            "url_follow": self.entry_url_follow.get().strip(),
            "url_like_general": self.entry_url_like_general.get().strip(),
            "url_like_persona": self.entry_url_like_persona.get().strip(),
            "cmd_play": self.entry_cmd_play.get().strip(),
            "cmd_skip": self.entry_cmd_skip.get().strip(),
            "cmd_pause": self.entry_cmd_pause.get().strip(),
            "cmd_resume": self.entry_cmd_resume.get().strip(),
            "cmd_volume": self.entry_cmd_vol.get().strip(),
            "perm_sub_play": bool(self.perm_sub_play.get()),
            "perm_sub_skip": bool(self.perm_sub_skip.get()),
            "perm_sub_pause": bool(self.perm_sub_pause.get()),
            "perm_sub_resume": bool(self.perm_sub_resume.get()),
            "perm_sub_vol": bool(self.perm_sub_vol.get()),
            "perm_mod_play": bool(self.perm_mod_play.get()),
            "perm_mod_skip": bool(self.perm_mod_skip.get()),
            "perm_mod_pause": bool(self.perm_mod_pause.get()),
            "perm_mod_resume": bool(self.perm_mod_resume.get()),
            "perm_mod_vol": bool(self.perm_mod_vol.get()),
            "perm_dj_play": bool(self.perm_dj_play.get()),
            "perm_dj_skip": bool(self.perm_dj_skip.get()),
            "perm_dj_pause": bool(self.perm_dj_pause.get()),
            "perm_dj_resume": bool(self.perm_dj_resume.get()),
            "perm_dj_vol": bool(self.perm_dj_vol.get()),
            "fuente_interfaz": self.fuente_actual
        }
        guardar_configuracion(datos_guardar)
        self.root.destroy()

gui = PanelControl()

def extraer_o_limpiar_emojis(texto, max_emojis):
    texto_normalizado = unicodedata.normalize('NFKD', texto)
    texto_base = "".join([c for c in texto_normalizado if not unicodedata.combining(c)])

    conteo = 0
    resultado = []

    for caracter in texto_base:
        codepoint = ord(caracter)
        es_emoji = (
            0x1F600 <= codepoint <= 0x1F64F or
            0x1F300 <= codepoint <= 0x1F5FF or
            0x1F680 <= codepoint <= 0x1F6FF or
            0x1F1E0 <= codepoint <= 0x1F1FF or
            0x2600 <= codepoint <= 0x26FF or
            0x2700 <= codepoint <= 0x27BF or
            0x1F900 <= codepoint <= 0x1F9FF or
            0x1FA70 <= codepoint <= 0x1FAFF
        )

        if es_emoji:
            if conteo < max_emojis:
                resultado.append(caracter)
                conteo += 1
        else:
            resultado.append(caracter)

    texto_filtrado = "".join(resultado)
    return re.sub(r'[^\w\s\d@._\-\U00010000-\U0010FFFF]', '', texto_filtrado).strip()

def normalizar_texto(texto):
    return extraer_o_limpiar_emojis(texto, max_emojis=0)

def aplicar_diccionario_reemplazos(texto, diccionario):
    for original, reemplazo in diccionario.items():
        patron = re.compile(r'\b' + re.escape(original) + r'\b', re.IGNORECASE)
        texto = patron.sub(reemplazo, texto)
    return texto

async def generar_audio_bytes(texto, voz, velocidad, tono):
    communicate = edge_tts.Communicate(texto, voz, rate=velocidad, pitch=tono)
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
                tono_actual = gui.combo_tono.get()
                audio_buffer = loop.run_until_complete(generar_audio_bytes(texto, voz_actual, vel_actual, tono_actual))
                
                sonido = pygame.mixer.Sound(audio_buffer)
                canal_tts = pygame.mixer.find_channel(True)
                if canal_tts:
                    volumen_tts_real = float(gui.slider_volumen.get()) * 0.6
                    canal_tts.set_volume(volumen_tts_real)
                    canal_tts.play(sonido)
                    while canal_tts.get_busy():
                        time.sleep(0.05)
        except Exception as e:
            gui.agregar_log(f"[Error Audio TTS]: {e}")
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

def es_suscriptor_nivel_minimo(user, nivel_minimo: int) -> bool:
    is_sub = getattr(user, "is_subscriber", False)
    badges = getattr(user, "badges", []) or getattr(user, "badge_list", []) or []
    
    for badge in badges:
        badge_str = str(badge).lower()
        if any(term in badge_str for term in ["subscriber", "sub", "sub_grade", "fans", "member"]):
            is_sub = True
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

            if level >= nivel_minimo:
                return True

    if is_sub and nivel_minimo <= 1:
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

def tiene_permiso_comando(user, tipo_comando):
    username = str(getattr(user, "unique_id", getattr(user, "unique_id_str", ""))).lower()
    es_sub = es_suscriptor_nivel_minimo(user, gui.obtener_nivel_minimo_sub())
    es_mod = es_moderador(user)
    es_dj = username in gui.obtener_usuarios_djs()

    if es_dj and getattr(gui, f"perm_dj_{tipo_comando}").get():
        return True
    if es_mod and getattr(gui, f"perm_mod_{tipo_comando}").get():
        return True
    if es_sub and getattr(gui, f"perm_sub_{tipo_comando}").get():
        return True

    return False

def procesar_comandos_musica(comentario, username, user_obj):
    global cancion_actual, VOTOS_SKIP, ULTIMO_SKIP_TIEMPO, canal_musica_ram
    partes = comentario.split(" ", 1)
    comando = partes[0].lower()
    arg = partes[1].strip() if len(partes) > 1 else ""
    
    nombre_user = normalizar_texto(username) or "Usuario"
    user_id_raw = str(getattr(user_obj, "unique_id", getattr(user_obj, "unique_id_str", username))).lower()

    cmds_play = gui.obtener_lista_comandos(gui.entry_cmd_play)
    cmds_skip = gui.obtener_lista_comandos(gui.entry_cmd_skip)
    cmds_pause = gui.obtener_lista_comandos(gui.entry_cmd_pause)
    cmds_resume = gui.obtener_lista_comandos(gui.entry_cmd_resume)
    cmds_vol = gui.obtener_lista_comandos(gui.entry_cmd_vol)

    if comando in cmds_play:
        if not tiene_permiso_comando(user_obj, "play"):
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} sin permisos para usar !play")
            return True
        if not arg:
            return True
        
        arg_normalizado = arg.strip().lower()
        
        if cancion_actual and arg_normalizado in cancion_actual.lower():
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} intentó añadir una canción que ya se está reproduciendo.")
            return True

        ya_en_cola = any(q.strip().lower() == arg_normalizado for q, _ in cola_musica)
        if ya_en_cola:
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} la canción '{arg}' ya se encuentra en la cola.")
            return True

        cola_musica.append((arg, nombre_user))
        gui.actualizar_lista_musica_ui()
        gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} añadió a la cola: {arg}")
        return True

    elif comando in cmds_skip:
        if not tiene_permiso_comando(user_obj, "skip"):
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} sin permisos para usar !skip")
            return True

        tiempo_actual = time.time()
        
        if tiempo_actual - ULTIMO_SKIP_TIEMPO < COOLDOWN_SKIP_SEGUNDOS:
            gui.agregar_log(f"[MÚSQUEDA] Espera unos segundos antes de pedir otro !skip.")
            return True

        esta_ocupado = canal_musica_ram and canal_musica_ram.get_busy()
        if not esta_ocupado and not cancion_actual:
            gui.agregar_log("[MÚSQUEDA] No hay canción en reproducción para saltar.")
            return True

        es_mod_o_dj = es_moderador(user_obj) or (user_id_raw in gui.obtener_usuarios_djs())
        if es_mod_o_dj:
            gui.musica_pausada = False
            if canal_musica_ram:
                canal_musica_ram.stop()
            VOTOS_SKIP.clear()
            ULTIMO_SKIP_TIEMPO = tiempo_actual
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} (Mod/DJ) saltó la canción.")
            return True

        if user_id_raw in VOTOS_SKIP:
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} ya votó para saltar esta canción.")
            return True

        VOTOS_SKIP.add(user_id_raw)
        conteo_votos = len(VOTOS_SKIP)
        gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} votó !skip ({conteo_votos}/{UMBRAL_VOTOS_SKIP})")

        if conteo_votos >= UMBRAL_VOTOS_SKIP:
            gui.musica_pausada = False
            if canal_musica_ram:
                canal_musica_ram.stop()
            VOTOS_SKIP.clear()
            ULTIMO_SKIP_TIEMPO = tiempo_actual
            gui.agregar_log("[MÚSQUEDA] ¡Meta de votos alcanzada! Canción saltada.")
            
        return True

    elif comando in cmds_pause:
        if not tiene_permiso_comando(user_obj, "pause"):
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} sin permisos para usar !pause")
            return True
        if canal_musica_ram:
            canal_musica_ram.pause()
        gui.musica_pausada = True
        gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} pausó la música")
        return True
    elif comando in cmds_resume:
        if not tiene_permiso_comando(user_obj, "resume"):
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} sin permisos para usar !resume")
            return True
        if canal_musica_ram:
            canal_musica_ram.unpause()
        gui.musica_pausada = False
        gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} reanudó la música")
        return True

    elif comando in cmds_vol:
        if not tiene_permiso_comando(user_obj, "vol"):
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} sin permisos para cambiar volumen")
            return True
        try:
            val = float(arg) / 100.0 if float(arg) > 1.0 else float(arg)
            val = max(0.0, min(1.0, val))
            gui.slider_volumen_musica.set(val)
            if canal_musica_ram:
                canal_musica_ram.set_volume(val * 0.25)
            gui.agregar_log(f"[MÚSQUEDA] Volumen cambiado a {int(val*100)}%")
        except ValueError:
            pass
        return True

    return False

def iniciar_tiktok(unique_id):
    global TIEMPO_INICIO, CONTADOR_LIKES_GENERAL
    try:
        gui.actualizar_estado(f"Conectando a {unique_id}...", "#f9e2af")
        gui.client_tiktok = TikTokLiveClient(unique_id=unique_id)

        @gui.client_tiktok.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            global TIEMPO_INICIO, CONTADOR_LIKES_GENERAL, VOTOS_SKIP
            gui.conectado = True
            gui.tiempo_conexion_inicio = time.time()
            TIEMPO_INICIO = time.time()
            CONTADOR_LIKES_GENERAL = 0
            LIKES_POR_USUARIO.clear()
            HISTORIAL_RECIENTE.clear()
            VOTOS_SKIP.clear()
            gui.actualizar_estado(f"Conectado a @{event.unique_id}", "#a6e3a1")
            gui.agregar_log(f"[SISTEMA] Conectado exitosamente al Live de {event.unique_id}")

        @gui.client_tiktok.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            if not gui.conectado:
                return

            user = event.user
            username = str(getattr(user, "unique_id", getattr(user, "unique_id_str", ""))).lower()
            nickname = str(getattr(user, "nickname", username))
            comentario = event.comment.strip()
            
            if time.time() - TIEMPO_INICIO < 2:
                return

            if comentario.startswith("!"):
                if procesar_comandos_musica(comentario, nickname or username, user):
                    return

            censuradas = gui.obtener_palabras_censuradas()
            for palabra in censuradas:
                if palabra in comentario.lower():
                    gui.agregar_log(f"[CENSURADO] Comentario de @{normalizar_texto(username)} omitido.")
                    return

            modo_sub = bool(gui.restringir_subs.get())
            modo_mod = bool(gui.restringir_mods.get())
            modo_lista = bool(gui.restringir_lista.get())
            hay_restricciones = modo_sub or modo_mod or modo_lista

            nivel_minimo = gui.obtener_nivel_minimo_sub()
            es_sub = es_suscriptor_nivel_minimo(user, nivel_minimo)
            es_mod = es_moderador(user)
            esta_en_lista = (username in gui.obtener_usuarios_lista_blanca())
            permitido = not hay_restricciones or (
                (modo_sub and es_sub) or 
                (modo_mod and es_mod) or 
                (modo_lista and esta_en_lista)
            )

            if permitido:
                id_mensaje = f"{username}:{comentario}"
                if id_mensaje in HISTORIAL_RECIENTE:
                    return
                    
                HISTORIAL_RECIENTE.append(id_mensaje)

                nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or "Usuario"
                
                try:
                    max_chars = int(gui.entry_limite.get())
                except ValueError:
                    max_chars = 100

                comentario_recortado = comentario[:max_chars]
                dicc_reemplazos = gui.obtener_diccionario_reemplazos()
                comentario_procesado = aplicar_diccionario_reemplazos(comentario_recortado, dicc_reemplazos)
                comentario_normalizado = extraer_o_limpiar_emojis(comentario_procesado, max_emojis=3)
                
                STATS["comentarios"] += 1
                gui.actualizar_metricas_ui()
                enviar_a_voz(f"{nombre_limpio} dice: {comentario_normalizado}")

        @gui.client_tiktok.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            if not gui.conectado:
                return

            es_combo_activo = getattr(event, "repeat_count", 1) > 1 and not getattr(event, "repeat_end", True)
            if es_combo_activo:
                return

            nickname = getattr(event.user, "nickname", "Alguien")
            nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or "Usuario"
            regalo = getattr(event.gift, "name", "un regalo")
            cantidad = getattr(event, "repeat_count", 1) or getattr(event.gift, "count", 1)
            
            STATS["regalos"] += cantidad
            gui.actualizar_metricas_ui()
            gui.agregar_log(f"[REGALO] {nombre_limpio} envió x{cantidad} {regalo}")

            if gui.alerta_regalos.get():
                url = gui.entry_url_regalo.get().strip()
                if url:
                    reproducir_sonido_url(url)
                
                if cantidad > 1:
                    enviar_a_voz(f"¡Gracias {nombre_limpio} por enviar {cantidad} {regalo}s!")
                else:
                    enviar_a_voz(f"¡Gracias {nombre_limpio} por enviar {regalo}!")

        @gui.client_tiktok.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            if not gui.conectado:
                return

            nickname = getattr(event.user, "nickname", "Alguien")
            nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or "Usuario"
            STATS["follows"] += 1
            gui.actualizar_metricas_ui()
            gui.agregar_log(f"[FOLLOW] {nombre_limpio} te ha seguido")

            if gui.alerta_follows.get():
                url = gui.entry_url_follow.get().strip()
                if url:
                    reproducir_sonido_url(url)

        @gui.client_tiktok.on(LikeEvent)
        async def on_like(event: LikeEvent):
            global CONTADOR_LIKES_GENERAL
            if not gui.conectado:
                return

            user = event.user
            username = str(getattr(user, "unique_id", getattr(user, "unique_id_str", "anonimo"))).lower()

            likes_recibidos = (
                getattr(event, "likes", None) or 
                getattr(event, "count", None) or 
                getattr(event, "label", 1)
            )
            
            try:
                likes_recibidos = int(likes_recibidos)
            except (ValueError, TypeError):
                likes_recibidos = 1

            STATS["likes_totales"] += likes_recibidos
            gui.actualizar_metricas_ui()

            if gui.alerta_likes_general.get():
                meta_general = gui.obtener_meta_likes_general()
                CONTADOR_LIKES_GENERAL += likes_recibidos
                
                if CONTADOR_LIKES_GENERAL >= meta_general:
                    gui.agregar_log(f"[LIKES GENERAL] Meta alcanzada: {meta_general} likes!")
                    url_gen = gui.entry_url_like_general.get().strip()
                    if url_gen:
                        reproducir_sonido_url(url_gen)
                    
                    if gui.repetir_likes_general.get():
                        CONTADOR_LIKES_GENERAL %= meta_general
                    else:
                        gui.alerta_likes_general.set(False)

            if gui.alerta_likes_persona.get():
                meta_persona = gui.obtener_meta_likes_persona()
                LIKES_POR_USUARIO[username] += likes_recibidos
                
                if LIKES_POR_USUARIO[username] >= meta_persona:
                    gui.agregar_log(f"[LIKES PERSONA] @{normalizar_texto(username)} alcanzó {meta_persona} likes")
                    
                    url_per = gui.entry_url_like_persona.get().strip()
                    if url_per:
                        reproducir_sonido_url(url_per)

                    if gui.repetir_likes_persona.get():
                        LIKES_POR_USUARIO[username] %= meta_persona
                    else:
                        LIKES_POR_USUARIO[username] = 0

        gui.client_tiktok.run()

    except Exception as e:
        gui.conectado = False
        gui.tiempo_conexion_inicio = None
        gui.actualizar_estado("Error de Conexión", "#f38ba8")
        gui.agregar_log(f"[Error TikTok]: {e}")
        gui.root.after(0, lambda: gui.btn_conectar.config(text="Conectar Live", bg="#a6e3a1"))
        gui.root.after(0, lambda: gui.entry_user.config(state="normal"))

gui.root.mainloop()
