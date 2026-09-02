class PanelControl:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TikTok Live Bot - Multiplataforma")
        self.root.geometry("760x980")
        self.root.configure(bg="#1e1e2e")
        self.root.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        self.proceso_actual = psutil.Process(os.getpid())
        self.tiempo_conexion_inicio = None

        self.audio_pausado = False
        self.musica_pausada = False
        self.restringir_subs = tk.BooleanVar(value=config["restringir_subs"])
        self.restringir_mods = tk.BooleanVar(value=config["restringir_mods"])
        self.restringir_lista = tk.BooleanVar(value=config["restringir_lista"])
        
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
        self.tab_widgets = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_principal, text=" Dashboard ")
        self.notebook.add(self.tab_musica, text=" Música y Comandos ")
        self.notebook.add(self.tab_tts, text=" Voz y TTS ")
        self.notebook.add(self.tab_filtros, text=" Filtros y Fuente ")
        self.notebook.add(self.tab_alertas, text=" Alertas ")
        self.notebook.add(self.tab_widgets, text=" Widgets / Overlay ")

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

        # Tab Widgets: cada widget usa su propia personalización.
        # No existe un tema/estilo global que se herede entre widgets.
        frame_widget_info = ttk.LabelFrame(self.tab_widgets, text=" Personalización de Widgets ")
        frame_widget_info.pack(fill="x", padx=10, pady=5)
        ttk.Label(
            frame_widget_info,
            text="Cada widget tiene sus propios ajustes independientes. Usa ⚙ Personalizar para modificarlo.",
            foreground="#a6e3a1"
        ).pack(fill="x", padx=8, pady=7)

        frame_urls = ttk.LabelFrame(self.tab_widgets, text=" Configuración Individual y URLs de Overlay ")
        frame_urls.pack(fill="both", expand=True, padx=10, pady=5)

        self.widget_configs = {}
        designs_saved = config.get("widget_designs", {})

        def _crear_widget_row_custom(parent, title_label, endpoint):
            f_box = ttk.LabelFrame(parent, text=f" {title_label} ")
            f_box.pack(fill="x", padx=5, pady=4)

            f_top = ttk.Frame(f_box)
            f_top.pack(fill="x", padx=5, pady=2)

            ttk.Label(f_top, text="Título:").pack(side="left")
            e_title = tk.Entry(f_top, bg="#11111b", fg="#cdd6f4", font=(self.fuente_actual, 8), width=18, relief="flat")
            e_title.insert(0, designs_saved.get(endpoint, {}).get("title", title_label))
            e_title.pack(side="left", padx=5)

            ttk.Label(f_top, text="Diseño:").pack(side="left", padx=(10, 0))
            c_design = ttk.Combobox(
                f_top,
                values=["standard", "toplikes_custom", "goal", "songrequests", "myactions"],
                state="readonly", width=14
            )
            c_design.set(designs_saved.get(endpoint, {}).get(
                "design",
                {"topliker":"toplikes_custom","myactions":"myactions","goal":"goal",
                 "songrequests":"songrequests"}.get(endpoint, "standard")
            ))
            c_design.pack(side="left", padx=5)

            ttk.Label(f_top, text="Max Usr:").pack(side="left", padx=(10, 0))
            e_max = tk.Entry(f_top, bg="#11111b", fg="#cdd6f4", font=(self.fuente_actual, 8), width=4, relief="flat")
            e_max.insert(0, str(designs_saved.get(endpoint, {}).get("max", 5)))
            e_max.pack(side="left", padx=5)

            custom_saved = designs_saved.get(endpoint, {}).get("custom", {}) or {}
            custom_state = tk.StringVar(value="✓ Personalización")
            btn_custom = tk.Button(
                f_top, textvariable=custom_state, bg="#313244", fg="#cdd6f4",
                relief="flat", font=(self.fuente_actual, 8, "bold"),
                command=lambda ep=endpoint: self.abrir_personalizacion_widget(ep)
            )
            btn_custom.pack(side="right", padx=5)

            f_bot = ttk.Frame(f_box)
            f_bot.pack(fill="x", padx=5, pady=2)

            entry_url = tk.Entry(f_bot, bg="#11111b", fg="#cdd6f4", font=(self.fuente_actual, 8), relief="flat")
            entry_url.pack(side="left", fill="x", expand=True, padx=(0, 5))

            btn_copy = tk.Button(
                f_bot, text="Copiar", bg="#89b4fa", fg="#11111b", relief="flat",
                command=lambda: self.copiar_al_portapapeles(entry_url.get()),
                font=(self.fuente_actual, 8, "bold")
            )
            btn_copy.pack(side="right")

            self.widget_configs[endpoint] = {
                "title_entry": e_title,
                "design_combo": c_design,
                "max_entry": e_max,
                "url_entry": entry_url,
                "custom": custom_saved,
                "custom_state": custom_state,
                "custom_button": btn_custom
            }

        _crear_widget_row_custom(frame_urls, "Top Likes", "topliker")
        _crear_widget_row_custom(frame_urls, "Mis Acciones", "myactions")
        _crear_widget_row_custom(frame_urls, "Último Follower", "lastfollower")
        _crear_widget_row_custom(frame_urls, "Meta / Goal", "goal")
        _crear_widget_row_custom(frame_urls, "Solicitudes de Canciones", "songrequests")

        ttk.Label(
            frame_urls,
            text="💡 Los ajustes de cada widget son independientes y no dependen de estilos globales.",
            foreground="#a6e3a1"
        ).pack(fill="x", padx=8, pady=(2, 5))

        btn_regen_urls = tk.Button(
            frame_urls, text="Generar y Guardar URLs de Widgets",
            bg="#a6e3a1", fg="#11111b", relief="flat",
            command=self.actualizar_urls_widgets, font=(self.fuente_actual, 8, "bold")
        )
        btn_regen_urls.pack(pady=5)

        self.actualizar_urls_widgets()

        # Tab Spotify
        # Toda la reproducción musical usa exclusivamente Spotify.
        frame_spotify = ttk.LabelFrame(self.tab_musica, text=" Spotify ")
        frame_spotify.pack(fill="x", padx=10, pady=5)
        f_sp = ttk.Frame(frame_spotify); f_sp.pack(fill="x", padx=8, pady=7)
        ttk.Label(f_sp, text="Dispositivo:").pack(side="left")
        self.combo_spotify_device = ttk.Combobox(f_sp, state="readonly", width=30)
        self.combo_spotify_device.pack(side="left", fill="x", expand=True, padx=6)
        self.btn_spotify_connect = tk.Button(f_sp, text="Conectar dispositivos", bg="#a6e3a1", fg="#11111b", relief="flat", command=self.conectar_dispositivos_spotify, font=(self.fuente_actual,8,"bold"))
        self.btn_spotify_connect.pack(side="left", padx=2)
        self.btn_spotify_refresh = tk.Button(f_sp, text="↻", bg="#89b4fa", fg="#11111b", relief="flat", command=self.actualizar_dispositivos_spotify, font=(self.fuente_actual,9,"bold"), width=3)
        self.btn_spotify_refresh.pack(side="left", padx=2)
        self.btn_spotify_disconnect = tk.Button(f_sp, text="Desconectar", bg="#f38ba8", fg="#11111b", relief="flat", command=self.desconectar_spotify, font=(self.fuente_actual,8,"bold"))
        self.btn_spotify_disconnect.pack(side="left", padx=2)
        self.lbl_spotify_status = ttk.Label(frame_spotify, text="Spotify: desconectado")
        self.lbl_spotify_status.pack(anchor="w", padx=8, pady=(0,7))

        # Barra de búsqueda manual: permite añadir canciones directamente desde el Dashboard.
        frame_busqueda_musica = ttk.LabelFrame(self.tab_musica, text=" Buscar en Spotify ")
        frame_busqueda_musica.pack(fill="x", padx=10, pady=5)

        f_busqueda = ttk.Frame(frame_busqueda_musica)
        f_busqueda.pack(fill="x", padx=8, pady=8)

        ttk.Label(f_busqueda, text="🔎").pack(side="left", padx=(0, 5))
        self.entry_busqueda_musica = tk.Entry(
            f_busqueda, bg="#11111b", fg="#cdd6f4",
            insertbackground="white", font=(self.fuente_actual, 9),
            relief="flat"
        )
        self.entry_busqueda_musica.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_busqueda_musica.bind("<Return>", lambda event: self.buscar_cancion_desde_ui())

        self.btn_buscar_musica = tk.Button(
            f_busqueda, text="Buscar / Añadir", bg="#89b4fa",
            fg="#11111b", relief="flat",
            command=self.buscar_cancion_desde_ui,
            font=(self.fuente_actual, 8, "bold")
        )
        self.btn_buscar_musica.pack(side="right")

        frame_rep_actual = ttk.LabelFrame(self.tab_musica, text=" Reproducción Spotify ")
        frame_rep_actual.pack(fill="x", padx=10, pady=5)
        self.lbl_now_playing = tk.Label(frame_rep_actual, text="Sonando: Ninguna", fg="#a6e3a1", bg="#1e1e2e", font=(self.fuente_actual, 9, "bold"), anchor="w", justify="left")
        self.lbl_now_playing.pack(fill="x", padx=10, pady=5)

        frame_vol_musica = ttk.LabelFrame(self.tab_musica, text=" Volumen Spotify ")
        frame_vol_musica.pack(fill="x", padx=10, pady=5)
        f_vol_m = ttk.Frame(frame_vol_musica)
        f_vol_m.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_vol_m, text="Volumen Música:").pack(side="left")
        self.slider_volumen_musica = ttk.Scale(f_vol_m, from_=0.0, to=1.0, value=VOLUMEN_MUSICA, command=self.cambiar_volumen_musica)
        self.slider_volumen_musica.pack(side="left", fill="x", expand=True, padx=10)

        frame_perm_musica = ttk.LabelFrame(self.tab_musica, text=" Permisos de comandos Spotify ")
        frame_perm_musica.pack(fill="x", padx=10, pady=5)

        f_djs = ttk.Frame(frame_perm_musica)
        f_djs.pack(fill="x", padx=5, pady=2)
        ttk.Label(f_djs, text="Lista DJs (separados por coma):").pack(side="left")
        self.entry_djs = tk.Entry(f_djs, bg="#11111b", fg="#cdd6f4", insertbackground="white", font=(self.fuente_actual, 8), relief="flat")
        self.entry_djs.insert(0, config.get("lista_djs", ""))
        self.entry_djs.pack(side="left", fill="x", expand=True, padx=5)

        f_grid_hdr = ttk.Frame(frame_perm_musica)
        f_grid_hdr.pack(fill="x", padx=5, pady=2)
        ttk.Label(f_grid_hdr, text="Rol", width=12, font=(self.fuente_actual, 8, "bold")).pack(side="left")
        for h in ["Play", "Skip", "Pause", "Resume", "Vol"]:
            ttk.Label(f_grid_hdr, text=h, width=7, anchor="center", font=(self.fuente_actual, 8, "bold")).pack(side="left", expand=True)

        f_row_sub = ttk.Frame(frame_perm_musica)
        f_row_sub.pack(fill="x", padx=5, pady=1)
        ttk.Label(f_row_sub, text="Suscriptores:", width=12).pack(side="left")
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_play).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_skip).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_pause).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_resume).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_vol).pack(side="left", expand=True)

        f_row_mod = ttk.Frame(frame_perm_musica)
        f_row_mod.pack(fill="x", padx=5, pady=1)
        ttk.Label(f_row_mod, text="Moderadores:", width=12).pack(side="left")
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_play).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_skip).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_pause).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_resume).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_vol).pack(side="left", expand=True)

        f_row_dj = ttk.Frame(frame_perm_musica)
        f_row_dj.pack(fill="x", padx=5, pady=1)
        ttk.Label(f_row_dj, text="DJs:", width=12).pack(side="left")
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_play).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_skip).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_pause).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_resume).pack(side="left", expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_vol).pack(side="left", expand=True)
        frame_lista_musica = ttk.LabelFrame(self.tab_musica, text=" Cola de Spotify ")
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
        frame_goal_follows = ttk.LabelFrame(self.tab_alertas, text=" Meta de Follows / Seguidores ")
        frame_goal_follows.pack(fill="x", padx=10, pady=5)
        f_goal_cfg = ttk.Frame(frame_goal_follows); f_goal_cfg.pack(fill="x", padx=5, pady=3)
        ttk.Label(f_goal_cfg, text="Meta:").pack(side="left")
        self.entry_meta_follows = tk.Entry(f_goal_cfg, bg="#11111b", fg="#cdd6f4", insertbackground="white", width=7, relief="flat")
        self.entry_meta_follows.insert(0, str(config.get("meta_follows", 100))); self.entry_meta_follows.pack(side="left", padx=6)
        self.repetir_meta_follows = tk.BooleanVar(value=config.get("repetir_meta_follows", False))
        ttk.Checkbutton(f_goal_cfg, text="Reiniciar al alcanzar", variable=self.repetir_meta_follows).pack(side="left", padx=8)

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


    def abrir_personalizacion_widget(self, endpoint):
        """Abre el panel avanzado exclusivo del widget seleccionado."""
        cfg = self.widget_configs.get(endpoint)
        if not cfg:
            return

        nombres = {
            "topliker": "Top Likes",
            "myactions": "Mis Acciones",
            "lastfollower": "Último Follower",
            "goal": "Meta / Goal",
            "songrequests": "Solicitudes de Canciones",
        }
        schemas = {
            "topliker": [
                ("Dimensiones", [
                    ("width", "Ancho", "340"), ("font_size", "Nombre (px)", "14"),
                    ("title_font_size", "Título (px)", "16"), ("avatar_size", "Avatar (px)", "52"),
                    ("gap", "Espaciado (px)", "12"), ("padding", "Padding (px)", "8"),
                ]),
                ("Apariencia", [
                    ("bg", "Fondo contenedor", "rgba(30, 30, 46, 0.9)"),
                    ("card_bg", "Fondo tarjeta", "rgba(0, 0, 0, 0.4)"),
                    ("text", "Color texto", "#cdd6f4"), ("accent", "Color acento", "#89b4fa"),
                    ("border", "Color borde", "rgba(49, 50, 68, 0.8)"),
                    ("shadow", "Color sombra", "rgba(0, 0, 0, 0.8)"),
                    ("shadow_blur", "Blur sombra", "10"), ("glow", "Brillo", "8"),
                    ("radius", "Radio tarjeta", "50"), ("card_blur", "Blur tarjeta", "4"),
                    ("border_width", "Grosor borde", "0"), ("avatar_radius", "Avatar %", "50"),
                ]),
                ("Elementos", [
                    ("heart_size", "❤️ Tamaño", "14"), ("crown_size", "👑 Tamaño", "16"),
                    ("crown_top", "👑 Posición Y", "-14"), ("rank_color", "Color posición", "#89b4fa"),
                    ("crown", "Mostrar corona (1/0)", "1"), ("show_rank", "Mostrar posición (1/0)", "0"),
                    ("show_badges", "Mostrar medallas (1/0)", "0"), ("heart_anim", "Animación corazón", "heartbeat"),
                ]),
            ],
            "myactions": [
                ("Tamaño y texto", [
                    ("width", "Ancho", "380"), ("avatar_size", "Avatar (px)", "100"),
                    ("name_size", "Nombre (px)", "42"), ("message_size", "Mensaje (px)", "24"),
                ]),
                ("Colores y efectos", [
                    ("action_bg", "Fondo tarjeta", "transparent"), ("text", "Color texto", "#ffffff"),
                    ("accent", "Color acento", "#38d9c5"), ("shadow", "Color sombra", "rgba(0,0,0,.85)"),
                    ("shadow_blur", "Blur sombra", "10"), ("glow", "Brillo", "12"),
                ]),
            ],
            "lastfollower": [
                ("Tamaño", [
                    ("width", "Ancho", "340"), ("font_size", "Texto (px)", "14"),
                    ("title_font_size", "Título (px)", "16"),
                ]),
                ("Colores", [
                    ("bg", "Fondo", "rgba(30,30,46,.9)"), ("card_bg", "Fondo tarjeta", "rgba(0,0,0,.4)"),
                    ("text", "Color texto", "#cdd6f4"), ("accent", "Color acento", "#89b4fa"),
                    ("border", "Borde", "rgba(49,50,68,.8)"), ("shadow", "Sombra", "rgba(0,0,0,.8)"),
                ]),
            ],
            "goal": [
                ("Barra de meta", [
                    ("width", "Ancho", "1460"), ("track", "Color fondo barra", "#ffffff"),
                    ("fill", "Color progreso", "#16d9d2"), ("percent", "Color porcentaje", "#238f8b"),
                    ("pct_size", "Porcentaje (px)", "30"), ("sub_size", "Texto meta (px)", "22"),
                ]),
                ("Efectos", [
                    ("shadow", "Sombra", "transparent"), ("glow", "Brillo", "0"),
                ]),
            ],
            "songrequests": [
                ("Tamaño", [
                    ("width", "Ancho", "520"), ("title_font_size", "Título (px)", "20"),
                    ("font_size", "Nombre (px)", "20"), ("sub_size", "Meta (px)", "14"),
                    ("max", "Canciones visibles", "5"),
                ]),
                ("Colores", [
                    ("bg", "Fondo", "rgba(30,30,46,.9)"), ("border", "Borde", "rgba(49,50,68,.8)"),
                    ("shadow", "Sombra", "rgba(0,0,0,.8)"), ("accent", "Acento", "#89b4fa"),
                    ("track", "Barra progreso", "rgba(255,255,255,.14)"), ("text", "Color texto", "#ffffff"),
                ]),
            ],
        }
        schema = schemas.get(endpoint, schemas["lastfollower"])
        defaults_now = {key: default for _, fields in schema for key, _, default in fields}
        saved = dict(cfg.get("custom", {}) or {})

        win = tk.Toplevel(self.root)
        win.title(f"⚙ Personalización avanzada — {nombres.get(endpoint, endpoint)}")
        win.geometry("590x680")
        win.minsize(520, 560)
        win.configure(bg="#1e1e2e")
        win.transient(self.root)
        win.grab_set()

        header = tk.Frame(win, bg="#1e1e2e")
        header.pack(fill="x", padx=14, pady=(12, 5))
        tk.Label(
            header, text=f"⚙ {nombres.get(endpoint, endpoint)}",
            bg="#1e1e2e", fg="#cdd6f4",
            font=(self.fuente_actual, 14, "bold")
        ).pack(side="left")
        tk.Label(
            header, text="Ajustes independientes del resto de widgets",
            bg="#1e1e2e", fg="#a6adc8",
            font=(self.fuente_actual, 8)
        ).pack(side="left", padx=12)

        body = ttk.Frame(win)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(body, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=550)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        vars_map = {}
        for section_name, fields in schema:
            lf = ttk.LabelFrame(inner, text=f" {section_name} ")
            lf.pack(fill="x", padx=4, pady=5)
            for key, label, default in fields:
                row = ttk.Frame(lf)
                row.pack(fill="x", padx=8, pady=3)
                ttk.Label(row, text=label, width=25).pack(side="left")
                current = saved.get(key, defaults_now.get(key, default))
                if key in ("crown", "show_rank", "show_badges"):
                    var = tk.BooleanVar(value=str(current) in ("1", "True", "true"))
                    ttk.Checkbutton(row, text="Activado", variable=var).pack(side="left")
                elif key == "heart_anim":
                    var = tk.StringVar(value=str(current))
                    combo = ttk.Combobox(row, textvariable=var, values=["heartbeat", "pop"], state="readonly", width=18)
                    combo.pack(side="left")
                else:
                    var = tk.StringVar(value=str(current))
                    ent = tk.Entry(row, textvariable=var, bg="#11111b", fg="#cdd6f4",
                                   insertbackground="white", relief="flat", font=(self.fuente_actual, 8))
                    ent.pack(side="left", fill="x", expand=True)
                vars_map[key] = var

        help_lbl = tk.Label(
            inner,
            text="Estos valores pertenecen únicamente a este widget.",
            bg="#1e1e2e", fg="#a6adc1", justify="left", wraplength=530,
            font=(self.fuente_actual, 8)
        )
        help_lbl.pack(fill="x", padx=8, pady=5)

        footer = tk.Frame(win, bg="#1e1e2e")
        footer.pack(fill="x", padx=12, pady=10)

        def guardar():
            custom = {"enabled": True}
            for key, var in vars_map.items():
                value = var.get()
                if isinstance(var, tk.BooleanVar):
                    value = "1" if var.get() else "0"
                custom[key] = str(value)
            cfg["custom"] = custom
            if custom["enabled"]:
                cfg["custom_state"].set("✓ Personalización")
            self.actualizar_urls_widgets()
            win.destroy()

        def reset():
            cfg["custom"] = {}
            cfg["custom_state"].set("✓ Personalización")
            self.actualizar_urls_widgets()
            win.destroy()

        tk.Button(
            footer, text="Restablecer valores", bg="#f38ba8", fg="#11111b",
            relief="flat", command=reset, font=(self.fuente_actual, 8, "bold")
        ).pack(side="left")
        tk.Button(
            footer, text="Cancelar", bg="#45475a", fg="#cdd6f4",
            relief="flat", command=win.destroy, font=(self.fuente_actual, 8, "bold")
        ).pack(side="right", padx=(5, 0))
        tk.Button(
            footer, text="✓ Guardar personalización", bg="#a6e3a1", fg="#11111b",
            relief="flat", command=guardar, font=(self.fuente_actual, 8, "bold")
        ).pack(side="right")

    def actualizar_urls_widgets(self):
        """Regenera las URLs usando únicamente los ajustes propios de cada widget."""
        widget_defaults = {
            "topliker": {
                "bg": "rgba(30, 30, 46, 0.9)", "card_bg": "rgba(0, 0, 0, 0.4)",
                "text": "#cdd6f4", "accent": "#89b4fa",
                "border": "rgba(49, 50, 68, 0.8)", "shadow": "rgba(0, 0, 0, 0.8)",
                "font": self.fuente_actual, "font_size": "14", "title_font_size": "16",
                "avatar_size": "52", "gap": "12", "padding": "8", "width": "340",
                "shadow_blur": "10", "glow": "8", "radius": "50", "card_blur": "4",
                "border_width": "0", "avatar_radius": "50", "heart_size": "14",
                "crown_size": "16", "crown_top": "-14", "rank_color": "#89b4fa",
                "crown": "1", "show_rank": "0", "show_badges": "0", "heart_anim": "heartbeat",
                "action_bg": "transparent", "name_size": "42", "message_size": "24",
                "track": "#ffffff", "fill": "#16d9d2", "percent": "#238f8b",
                "pct_size": "30", "sub_size": "22"
            },
            "myactions": {
                "bg": "transparent", "card_bg": "transparent", "text": "#ffffff",
                "accent": "#38d9c5", "border": "transparent", "shadow": "rgba(0,0,0,.85)",
                "font": self.fuente_actual, "width": "380", "avatar_size": "100",
                "name_size": "42", "message_size": "24", "shadow_blur": "10", "glow": "12",
                "action_bg": "transparent"
            },
            "lastfollower": {
                "bg": "rgba(30,30,46,.9)", "card_bg": "rgba(0,0,0,.4)",
                "text": "#cdd6f4", "accent": "#89b4fa",
                "border": "rgba(49,50,68,.8)", "shadow": "rgba(0,0,0,.8)",
                "font": self.fuente_actual, "width": "340", "font_size": "14",
                "title_font_size": "16", "avatar_size": "52", "gap": "12", "padding": "8",
                "shadow_blur": "10", "glow": "8"
            },
            "goal": {
                "bg": "transparent", "card_bg": "transparent", "text": "#ffffff",
                "accent": "#7b3f91", "border": "transparent", "shadow": "transparent",
                "font": self.fuente_actual, "width": "1460", "track": "#ffffff",
                "fill": "#16d9d2", "percent": "#238f8b", "pct_size": "30", "sub_size": "22",
                "glow": "0"
            },
            "songrequests": {
                "bg": "rgba(30,30,46,.9)", "card_bg": "rgba(30,30,46,.9)",
                "text": "#ffffff", "accent": "#89b4fa",
                "border": "rgba(49,50,68,.8)", "shadow": "rgba(0,0,0,.8)",
                "font": self.fuente_actual, "width": "520", "title_font_size": "20",
                "font_size": "20", "sub_size": "14", "track": "rgba(255,255,255,.14)"
            }
        }

        for endpoint, cfg in self.widget_configs.items():
            title_val = cfg["title_entry"].get().strip()
            design_val = cfg["design_combo"].get().strip()
            max_val = cfg["max_entry"].get().strip()

            defaults = widget_defaults.get(endpoint, {})
            custom = cfg.get("custom", {}) or {}

            def val(key, fallback=None):
                return custom.get(key, defaults.get(key, fallback))

            def q(value):
                return urllib.parse.quote(str(value))

            query = {
                "bg": val("bg", "transparent"),
                "card_bg": val("card_bg", "transparent"),
                "text": val("text", "#ffffff"),
                "accent": val("accent", "#89b4fa"),
                "border": val("border", "transparent"),
                "shadow": val("shadow", "transparent"),
                "font": val("font", self.fuente_actual),
                "title": title_val,
                "design": design_val,
                "max": max_val,
                "font_size": val("font_size", "14"),
                "title_font_size": val("title_font_size", "16"),
                "avatar_size": val("avatar_size", "52"),
                "gap": val("gap", "12"),
                "padding": val("padding", "8"),
                "width": val("width", "340"),
                "shadow_blur": val("shadow_blur", "10"),
                "glow": val("glow", "8"),
                "radius": val("radius", "50"),
                "card_blur": val("card_blur", "4"),
                "border_width": val("border_width", "0"),
                "avatar_radius": val("avatar_radius", "50"),
                "heart_size": val("heart_size", "14"),
                "crown_size": val("crown_size", "16"),
                "crown_top": val("crown_top", "-14"),
                "rank_color": val("rank_color", "#89b4fa"),
                "crown": val("crown", "1"),
                "show_rank": val("show_rank", "0"),
                "show_badges": val("show_badges", "0"),
                "heart_anim": val("heart_anim", "heartbeat"),
                "action_bg": val("action_bg", "transparent"),
                "name_size": val("name_size", "42"),
                "message_size": val("message_size", "24")
            }

            if endpoint == "goal":
                query.update({
                    "goal": "follows",
                    "target": self.obtener_meta_follows(),
                    "goal_width": val("width", "1460"),
                    "track": val("track", "#ffffff"),
                    "fill": val("fill", "#16d9d2"),
                    "frame": "transparent",
                    "label_bg": "transparent",
                    "percent": val("percent", "#238f8b"),
                    "pct_size": val("pct_size", "30"),
                    "sub_size": val("sub_size", "22"),
                })
            elif endpoint == "songrequests":
                query.update({
                    "title_size": val("title_font_size", "20"),
                    "name_size": val("font_size", "20"),
                    "meta_size": val("sub_size", "14"),
                    "track": val("track", "rgba(255,255,255,.14)")
                })

            query_str = "?" + "&".join(f"{key}={q(value)}" for key, value in query.items())
            full_url = f"http://localhost:5000/widget/{endpoint}{query_str}"

            cfg["url_entry"].delete(0, tk.END)
            cfg["url_entry"].insert(0, full_url)

    def copiar_al_portapapeles(self, texto):
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.agregar_log(f"[WIDGETS] URL copiada al portapapeles: {texto}")

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
        self.actualizar_urls_widgets()
        self.agregar_log(f"[GUI] Tipografía cambiada a: {nueva_fuente}")

    def cambiar_volumen_musica(self, val):
        try: spotify.volume(float(val)*100)
        except Exception: pass

    def alternar_pausa_musica(self):
        try:
            if self.musica_pausada:
                spotify.resume(); self.musica_pausada=False; self.agregar_log("[SPOTIFY] Música reanudada.")
            else:
                spotify.pause(); self.musica_pausada=True; self.agregar_log("[SPOTIFY] Música pausada.")
        except Exception as e: self.agregar_log(f"[SPOTIFY] {e}")

    def saltar_cancion_manual(self):
        global VOTOS_SKIP, SPOTIFY_CURRENT_REQUEST
        try:
            self.musica_pausada=False
            if cola_musica:
                SPOTIFY_CURRENT_REQUEST=None; spotify_reproducir_siguiente()
            else: spotify.next(); SPOTIFY_CURRENT_REQUEST=None
            VOTOS_SKIP.clear(); self.agregar_log("[SPOTIFY] Canción saltada.")
        except Exception as e: self.agregar_log(f"[SPOTIFY] {e}")

    def conectar_dispositivos_spotify(self):
        try:
            if not spotify.access_token:
                spotify.start_auth()
                self.lbl_spotify_status.config(text="Spotify: autoriza la cuenta en el navegador…")
                self.agregar_log("[SPOTIFY] Abriendo autorización.")
                return
            self.actualizar_dispositivos_spotify()
        except Exception as e: self.agregar_log(f"[SPOTIFY] {e}")

    def actualizar_dispositivos_spotify(self):
        try:
            devices=spotify.devices()
            names=[]; selected=0
            for d in devices:
                if d.get("is_restricted"): continue
                label=f"{d.get('name','Dispositivo')} · {d.get('type','')}"
                names.append(label)
                if d.get("id")==spotify.device_id: selected=len(names)-1
            self._spotify_device_map=devices
            self.combo_spotify_device["values"]=names
            if names:
                self.combo_spotify_device.current(min(selected,len(names)-1))
                self.lbl_spotify_status.config(text=f"Spotify: conectado · {names[selected if selected < len(names) else 0]}")
            else:
                self.combo_spotify_device.set("")
                self.lbl_spotify_status.config(text="Spotify: conectado · abre Spotify en un dispositivo")
            self.combo_spotify_device.bind("<<ComboboxSelected>>", self.seleccionar_dispositivo_spotify)
        except Exception as e: self.lbl_spotify_status.config(text=f"Spotify: {e}")

    def seleccionar_dispositivo_spotify(self, event=None):
        try:
            idx=self.combo_spotify_device.current()
            devices=[d for d in spotify.devices() if not d.get("is_restricted")]
            if idx<0 or idx>=len(devices): return
            d=spotify.choose_device(devices[idx].get("id"))
            self.lbl_spotify_status.config(text=f"Spotify: conectado · {d.get('name','Dispositivo')}")
            self.agregar_log(f"[SPOTIFY] Dispositivo seleccionado: {d.get('name','Dispositivo')}")
        except Exception as e: self.agregar_log(f"[SPOTIFY] {e}")

    def desconectar_spotify(self):
        global SPOTIFY_CURRENT_REQUEST
        spotify.access_token=""; spotify.refresh_token=""; spotify.expires_at=0; spotify.device_id=None; spotify.device_name=""; spotify.device_type=""; spotify._save()
        SPOTIFY_CURRENT_REQUEST=None
        self.combo_spotify_device["values"]=[]; self.combo_spotify_device.set("")
        self.lbl_spotify_status.config(text="Spotify: desconectado")
        self.agregar_log("[SPOTIFY] Sesión desconectada.")

    def buscar_cancion_desde_ui(self):
        query=self.entry_busqueda_musica.get().strip()
        if not query: return
        try:
            track=spotify_buscar(query)
            if not track: raise RuntimeError(f"No encontré '{query}'.")
            cola_musica.append({"query":query,"user":"Dashboard",**track})
            self.actualizar_lista_musica_ui(); self.entry_busqueda_musica.delete(0,tk.END)
            self.agregar_log(f"[SPOTIFY] Añadida: {track['title']} — {track['artist']}")
            if not SPOTIFY_CURRENT_REQUEST and not self.musica_pausada: spotify_reproducir_siguiente()
        except Exception as e: self.agregar_log(f"[SPOTIFY] {e}")

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
            for idx, item in enumerate(cola_musica, start=1):
                titulo=item.get("title", item.get("query", "Canción"))
                artista=item.get("artist", "")
                usuario=item.get("user", "Usuario")
                texto=f"{idx}. {titulo}"
                if artista: texto += f" — {artista}"
                self.listbox_musica.insert(tk.END, f"{texto} (por @{usuario})")
            
            if seleccion_previa and seleccion_previa[0] < len(cola_musica):
                self.listbox_musica.select_set(seleccion_previa[0])

        self.root.after(0, _update)
        broadcast_overlay_data()

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
                self.agregar_log(f"[SPOTIFY] Canción en índice {index+1} eliminada de la cola.")
        except Exception as e:
            self.agregar_log(f"[Error UI]: {e}")

    def vaciar_lista_musica(self):
        cola_musica.clear()
        self.actualizar_lista_musica_ui()
        self.agregar_log("[SPOTIFY] Lista de espera musical vaciada.")

    def obtener_meta_follows(self):
        try:
            val = int(self.entry_meta_follows.get().strip())
            return val if val > 0 else 100
        except (ValueError, AttributeError):
            return 100

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
        with cola_mensajes.mutex:
            cola_mensajes.queue.clear()
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

        designs_to_save = {}
        for k, v in self.widget_configs.items():
            try:
                m_val = int(v["max_entry"].get().strip())
            except ValueError:
                m_val = 5

            custom_saved = dict(v.get("custom", {}) or {})
            designs_to_save[k] = {
                "title": v["title_entry"].get().strip(),
                "design": v["design_combo"].get().strip(),
                "max": m_val,
                "custom": custom_saved,
            }

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
            "meta_follows": self.obtener_meta_follows(),
            "repetir_meta_follows": bool(self.repetir_meta_follows.get()),
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
            "fuente_interfaz": self.fuente_actual,
            "widget_designs": designs_to_save
        }
        guardar_configuracion(datos_guardar)
        self.root.destroy()

gui = PanelControl()
