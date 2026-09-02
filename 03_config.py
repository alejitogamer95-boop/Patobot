CONFIG_FILE = "config.json"
CONFIG_DEFAULTS = {
    "usuario": "@",
    "volumen": 0.6,
    "volumen_alertas": 0.7,
    "volumen_musica": 0.2,
    "spotify_client_id": "94d6e0bbd91143c0b036fc3202dd0d70",
    "spotify_client_secret": "d32497e99b48436b89aaa8bee4947b32",
    "spotify_access_token": "",
    "spotify_refresh_token": "",
    "spotify_expires_at": 0,
    "spotify_device_id": "",
    "spotify_device_name": "",
    "spotify_device_type": "",
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
    "meta_follows": 100,
    "repetir_meta_follows": False,
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
    "fuente_interfaz": "Segoe UI",
    "widget_designs": {
        "topliker": {"design": "toplikes_custom", "max": 5, "title": ""},
        "myactions": {"design": "myactions", "max": 1, "title": "Mis Acciones"},
        "lastfollower": {"design": "standard", "max": 1, "title": "Último Seguidor"},
        "goal": {"design": "goal", "max": 1, "title": "New Followers"},
        "songrequests": {"design": "songrequests", "max": 5, "title": "Solicitudes de Canciones"}
    }
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

LIKES_POR_USUARIO = defaultdict(lambda: {"score": 0, "progress": 0, "goal_hits": 0, "goal_active": True, "avatar": ""})
DONACIONES_POR_USUARIO = defaultdict(int)
ULTIMO_REGALO = None
ULTIMO_SEGUIDOR = None
ULTIMA_ACCION = None
ULTIMO_LIKE_META = None
CANCION_ACTUAL_WIDGET = {"title": "", "user": "", "duration": 0, "started_at": 0, "cover": ""}

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
SPOTIFY_CURRENT_REQUEST = None
CANCION_ACTUAL_WIDGET = {"title":"", "artist":"", "user":"", "duration":0, "started_at":0, "cover":"", "spotify_url":"", "paused":False, "progress_ms":0}

SPOTIFY_AUTH_BASE = "https://accounts.spotify.com"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/spotify/callback"
SPOTIFY_SCOPES = "user-read-playback-state user-read-currently-playing user-modify-playback-state"
