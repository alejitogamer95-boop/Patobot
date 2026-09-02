def procesar_comandos_musica(comentario, username, user_obj):
    global cancion_actual, VOTOS_SKIP, ULTIMO_SKIP_TIEMPO, SPOTIFY_CURRENT_REQUEST
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
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} sin permisos para usar !play")
            return True
        if not arg:
            return True
        
        arg_normalizado = arg.strip().lower()
        
        if cancion_actual and arg_normalizado in cancion_actual.lower():
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} intentó añadir una canción que ya se está reproduciendo.")
            return True

        ya_en_cola = any(x.get("query", "").strip().lower() == arg_normalizado for x in cola_musica)
        if ya_en_cola:
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} la canción '{arg}' ya se encuentra en la cola.")
            return True

        try:
            track=spotify_buscar(arg)
            if not track: raise RuntimeError(f"No encontré '{arg}' en Spotify.")
            cola_musica.append({"query":arg,"user":nombre_user,**track})
            gui.actualizar_lista_musica_ui()
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} añadió: {track['title']} — {track['artist']}")
            if not SPOTIFY_CURRENT_REQUEST and not gui.musica_pausada: spotify_reproducir_siguiente()
        except Exception as e:
            gui.agregar_log(f"[SPOTIFY] @{nombre_user}: {e}")
        return True

    elif comando in cmds_skip:
        if not tiene_permiso_comando(user_obj, "skip"):
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} sin permisos para usar !skip")
            return True

        tiempo_actual = time.time()
        
        if tiempo_actual - ULTIMO_SKIP_TIEMPO < COOLDOWN_SKIP_SEGUNDOS:
            gui.agregar_log(f"[SPOTIFY] Espera unos segundos antes de pedir otro !skip.")
            return True

        if not spotify.access_token or not cancion_actual:
            gui.agregar_log("[SPOTIFY] No hay canción en reproducción para saltar.")
            return True

        es_mod_o_dj = es_moderador(user_obj) or (user_id_raw in gui.obtener_usuarios_djs())
        if es_mod_o_dj:
            gui.musica_pausada = False
            SPOTIFY_CURRENT_REQUEST = None
            if cola_musica:
                spotify_reproducir_siguiente()
            else:
                spotify.next()
            VOTOS_SKIP.clear()
            ULTIMO_SKIP_TIEMPO = tiempo_actual
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} (Mod/DJ) saltó la canción.")
            return True

        if user_id_raw in VOTOS_SKIP:
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} ya votó para saltar esta canción.")
            return True

        VOTOS_SKIP.add(user_id_raw)
        conteo_votos = len(VOTOS_SKIP)
        gui.agregar_log(f"[SPOTIFY] @{nombre_user} votó !skip ({conteo_votos}/{UMBRAL_VOTOS_SKIP})")

        if conteo_votos >= UMBRAL_VOTOS_SKIP:
            gui.musica_pausada = False
            SPOTIFY_CURRENT_REQUEST = None
            if cola_musica:
                spotify_reproducir_siguiente()
            else:
                spotify.next()
            VOTOS_SKIP.clear()
            ULTIMO_SKIP_TIEMPO = tiempo_actual
            gui.agregar_log("[SPOTIFY] ¡Meta de votos alcanzada! Canción saltada.")
            
        return True
    elif comando in cmds_pause:
        if not tiene_permiso_comando(user_obj, "pause"):
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} sin permisos para usar !pause")
            return True
        spotify.pause()
        gui.musica_pausada = True
        gui.agregar_log(f"[SPOTIFY] @{nombre_user} pausó la música")
        return True
    elif comando in cmds_resume:
        if not tiene_permiso_comando(user_obj, "resume"):
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} sin permisos para usar !resume")
            return True
        spotify.resume()
        gui.musica_pausada = False
        gui.agregar_log(f"[SPOTIFY] @{nombre_user} reanudó la música")
        return True

    elif comando in cmds_vol:
        if not tiene_permiso_comando(user_obj, "vol"):
            gui.agregar_log(f"[SPOTIFY] @{nombre_user} sin permisos para cambiar volumen")
            return True
        try:
            val = float(arg) / 100.0 if float(arg) > 1.0 else float(arg)
            val = max(0.0, min(1.0, val))
            gui.slider_volumen_musica.set(val)
            spotify.volume(val * 100)
            gui.agregar_log(f"[SPOTIFY] Volumen cambiado a {int(val*100)}%")
        except ValueError:
            pass
        return True

    return False
