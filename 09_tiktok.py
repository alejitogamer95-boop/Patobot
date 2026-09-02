def extraer_urls_de_objeto(obj):
    if not obj:
        return []
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, list):
        res = []
        for item in obj:
            res.extend(extraer_urls_de_objeto(item))
        return res
    if isinstance(obj, dict):
        urls = obj.get("url_list") or obj.get("urls") or obj.get("url") or []
        return extraer_urls_de_objeto(urls)
    
    for attr in ["url_list", "urls", "url"]:
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if val:
                return extraer_urls_de_objeto(val)
    return []

def obtener_avatar_usuario(user):
    for attr in ["avatar_thumb", "avatar_medium", "avatar_large", "avatar"]:
        avatar_obj = getattr(user, attr, None)
        if avatar_obj:
            urls = extraer_urls_de_objeto(avatar_obj)
            if urls:
                return urls[0]
    return "https://www.tiktok.com/favicon.ico"

def iniciar_tiktok(unique_id):
    global TIEMPO_INICIO, CONTADOR_LIKES_GENERAL, ULTIMO_REGALO, ULTIMO_SEGUIDOR, ULTIMA_ACCION
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
            DONACIONES_POR_USUARIO.clear()
            HISTORIAL_RECIENTE.clear()
            ULTIMA_ACCION = None
            ULTIMO_LIKE_META = None
            VOTOS_SKIP.clear()
            gui.actualizar_estado(f"Conectado a @{event.unique_id}", "#a6e3a1")
            gui.agregar_log(f"[SISTEMA] Conectado exitosamente al Live de {event.unique_id}")
            broadcast_overlay_data()

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
                    gui.agregar_log(f"[CENSURADO] Comentario de @{normalizar_texto(nickname or username)} omitido.")
                    return

            if gui.restringir_subs.get() and not es_suscriptor_nivel_minimo(user, gui.obtener_nivel_minimo_sub()):
                return

            if gui.restringir_mods.get() and not es_moderador(user):
                return

            if gui.restringir_lista.get():
                lista = gui.obtener_usuarios_lista_blanca()
                if username not in lista:
                    return

            diccionario = gui.obtener_diccionario_reemplazos()
            comentario_procesado = aplicar_diccionario_reemplazos(comentario, diccionario)

            limite = int(gui.entry_limite.get())
            if len(comentario_procesado) > limite:
                comentario_procesado = comentario_procesado[:limite]

            texto_para_voz = f"{normalizar_texto(nickname or username)} dice: {comentario_procesado}"
            enviar_a_voz(texto_para_voz)
            
            STATS["comentarios"] += 1
            gui.actualizar_metricas_ui()

        @gui.client_tiktok.on(LikeEvent)
        async def on_like(event: LikeEvent):
            global CONTADOR_LIKES_GENERAL
            if not gui.conectado:
                return

            user = event.user
            username = str(getattr(user, "unique_id", getattr(user, "unique_id_str", "Anonimo"))).lower()
            nickname = str(getattr(user, "nickname", username))
            nombre_limpio = normalizar_texto(nickname or username) or "Usuario"
            cantidad = getattr(event, "count", 1)
            avatar_url = obtener_avatar_usuario(user)

            STATS["likes_totales"] += cantidad
            CONTADOR_LIKES_GENERAL += cantidad

            like_data = LIKES_POR_USUARIO[nombre_limpio]
            like_data["score"] += cantidad
            like_data["progress"] += cantidad
            if avatar_url and avatar_url != "https://www.tiktok.com/favicon.ico":
                like_data["avatar"] = avatar_url

            global ULTIMA_ACCION, ULTIMO_LIKE_META
            meta_per = gui.obtener_meta_likes_persona()
            goal_triggered = False
            if gui.alerta_likes_persona.get() and meta_per > 0 and like_data.get("goal_active", True) and like_data["progress"] >= meta_per:
                hits = like_data["progress"] // meta_per
                like_data["goal_hits"] += hits
                goal_triggered = True
                if gui.repetir_likes_persona.get():
                    like_data["progress"] %= meta_per
                    for _ in range(hits):
                        reproducir_sonido_url(gui.entry_url_like_persona.get().strip())
                else:
                    like_data["progress"] = meta_per
                    like_data["goal_active"] = False
                    reproducir_sonido_url(gui.entry_url_like_persona.get().strip())

            ULTIMO_LIKE_META = {"name": nombre_limpio, "avatar": avatar_url, "progress": like_data["progress"], "total": like_data["score"], "target": meta_per, "goal_hits": like_data["goal_hits"], "active": like_data.get("goal_active", True), "triggered": goal_triggered}

            # "Mis Acciones" solo se actualiza cuando la persona alcanza
            # la meta de likes. Los likes normales no cambian este widget.
            if goal_triggered:
                meta_text = f"{meta_per} Likes"
                if hits > 1:
                    meta_text = f"{hits} metas de {meta_per} Likes"
                ULTIMA_ACCION = {
                    "id": f"like-goal-{time.time_ns()}",
                    "type": "like_goal",
                    "name": nombre_limpio,
                    "avatar": avatar_url,
                    "message": f"🎯 ¡Meta alcanzada! {meta_text} · Total {like_data['score']}",
                    "icon": "🎯",
                    "likes": like_data["progress"],
                    "likes_total": like_data["score"],
                    "goal": meta_per,
                    "goal_triggered": True,
                    "goal_hits": hits,
                    "likes_count": cantidad,
                    "expires_at": time.time() + 5
                }

            # Alerta de Likes General
            if gui.alerta_likes_general.get():
                meta_gen = gui.obtener_meta_likes_general()
                if CONTADOR_LIKES_GENERAL >= meta_gen:
                    hits_general = CONTADOR_LIKES_GENERAL // meta_gen
                    if gui.repetir_likes_general.get():
                        CONTADOR_LIKES_GENERAL %= meta_gen
                    else:
                        gui.alerta_likes_general.set(False)
                        CONTADOR_LIKES_GENERAL = meta_gen

                    # Mis Acciones también muestra la animación de la meta general.
                    ULTIMA_ACCION = {
                        "id": f"like-general-{time.time_ns()}",
                        "type": "like_goal",
                        "name": nombre_limpio,
                        "avatar": avatar_url,
                        "message": f"🎯 ¡Meta general alcanzada! {meta_gen} Likes" + (f" ×{hits_general}" if hits_general > 1 else ""),
                        "icon": "🎯",
                        "likes_total": STATS["likes_totales"],
                        "goal": meta_gen,
                        "goal_triggered": True,
                        "goal_hits": hits_general,
                        "likes_count": cantidad,
                        "expires_at": time.time() + 5
                    }
                    reproducir_sonido_url(gui.entry_url_like_general.get().strip())

            gui.actualizar_metricas_ui()
            broadcast_overlay_data()

        @gui.client_tiktok.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            global ULTIMO_REGALO
            if not gui.conectado:
                return

            user = event.user
            username = str(getattr(user, "unique_id", getattr(user, "unique_id_str", "Anonimo"))).lower()
            nickname = str(getattr(user, "nickname", username))
            nombre_limpio = normalizar_texto(nickname or username) or "Usuario"
            gift_name = getattr(event.gift, "name", "Regalo")
            repeat_count = getattr(event, "repeat_count", 1)
            diamond_count = getattr(event.gift, "diamond_count", 1) * repeat_count

            DONACIONES_POR_USUARIO[nombre_limpio] += diamond_count
            ULTIMO_REGALO = {"user": nombre_limpio, "gift": gift_name, "count": repeat_count}

            global ULTIMA_ACCION

            STATS["regalos"] += repeat_count

            # Mis Acciones se activa solamente cuando la alerta de regalos está activa.
            if gui.alerta_regalos.get():
                ULTIMA_ACCION = {
                    "id": f"gift-{time.time_ns()}",
                    "type": "gift",
                    "name": nombre_limpio,
                    "avatar": obtener_avatar_usuario(user),
                    "message": f"¡Gracias por x{repeat_count} {gift_name}!",
                    "icon": "🎁",
                    "expires_at": time.time() + 5
                }
                url_reg = gui.entry_url_regalo.get().strip()
                reproducir_sonido_url(url_reg)

            gui.actualizar_metricas_ui()
            broadcast_overlay_data()

        @gui.client_tiktok.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            global ULTIMO_SEGUIDOR
            if not gui.conectado:
                return

            user = event.user
            username = str(getattr(user, "unique_id", getattr(user, "unique_id_str", "Anonimo"))).lower()
            nickname = str(getattr(user, "nickname", username))
            nombre_limpio = normalizar_texto(nickname or username) or "Usuario"

            ULTIMO_SEGUIDOR = nombre_limpio

            global ULTIMA_ACCION

            STATS["follows"] += 1

            # Mis Acciones se activa solamente cuando la alerta de follows está activa.
            if gui.alerta_follows.get():
                ULTIMA_ACCION = {
                    "id": f"follow-{time.time_ns()}",
                    "type": "follow",
                    "name": nombre_limpio,
                    "avatar": obtener_avatar_usuario(user),
                    "message": "¡Gracias por seguirme!",
                    "icon": "💙",
                    "expires_at": time.time() + 5
                }
                url_fol = gui.entry_url_follow.get().strip()
                reproducir_sonido_url(url_fol)

            gui.actualizar_metricas_ui()
            broadcast_overlay_data()

            meta_follow = gui.obtener_meta_follows()
            if STATS["follows"] >= meta_follow and gui.repetir_meta_follows.get():
                STATS["follows"] %= meta_follow

        gui.client_tiktok.run()

    except Exception as e:
        gui.agregar_log(f"[Error Live]: {e}")
        gui.actualizar_estado("Error al conectar", "#f38ba8")
        gui.conectado = False
