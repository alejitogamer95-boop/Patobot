class SpotifyManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.client_id = config.get("spotify_client_id") or "94d6e0bbd91143c0b036fc3202dd0d70"
        self.client_secret = config.get("spotify_client_secret") or "d32497e99b48436b89aaa8bee4947b32"
        self.access_token = config.get("spotify_access_token", "")
        self.refresh_token = config.get("spotify_refresh_token", "")
        self.expires_at = float(config.get("spotify_expires_at", 0) or 0)
        self.device_id = config.get("spotify_device_id") or None
        self.device_name = config.get("spotify_device_name", "")
        self.device_type = config.get("spotify_device_type", "")
        self.state = None
        self.code_verifier = None
        self.last_error = ""

    def _save(self):
        config["spotify_client_id"] = self.client_id
        config["spotify_client_secret"] = self.client_secret
        config["spotify_access_token"] = self.access_token
        config["spotify_refresh_token"] = self.refresh_token
        config["spotify_expires_at"] = self.expires_at
        config["spotify_device_id"] = self.device_id or ""
        config["spotify_device_name"] = self.device_name
        config["spotify_device_type"] = self.device_type
        guardar_configuracion(config)

    def _basic(self):
        raw=f"{self.client_id}:{self.client_secret}".encode()
        return base64.b64encode(raw).decode()

    def _token_request(self, data, basic=False):
        req=urllib.request.Request(f"{SPOTIFY_AUTH_BASE}/api/token", data=urllib.parse.urlencode(data).encode(), method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        if basic: req.add_header("Authorization", f"Basic {self._basic()}")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail=e.read().decode(errors="replace")
            raise RuntimeError(f"Spotify OAuth HTTP {e.code}: {detail}") from e

    def start_auth(self):
        self.state=secrets.token_urlsafe(32)
        self.code_verifier=secrets.token_urlsafe(64)
        digest=hashlib.sha256(self.code_verifier.encode()).digest()
        challenge=base64.urlsafe_b64encode(digest).decode().rstrip("=")
        params=urllib.parse.urlencode({
            "client_id":self.client_id,"response_type":"code","redirect_uri":SPOTIFY_REDIRECT_URI,
            "scope":SPOTIFY_SCOPES,"state":self.state,"code_challenge_method":"S256","code_challenge":challenge,
            "show_dialog":"true"
        })
        url=f"{SPOTIFY_AUTH_BASE}/authorize?{params}"
        webbrowser.open(url)
        return url

    def finish_auth(self, code, state):
        if not code: raise RuntimeError("Spotify no devolvió el código.")
        if not self.state or state != self.state: raise RuntimeError("Estado OAuth inválido. Vuelve a conectar Spotify.")
        tokens=self._token_request({"client_id":self.client_id,"grant_type":"authorization_code","code":code,"redirect_uri":SPOTIFY_REDIRECT_URI,"code_verifier":self.code_verifier})
        with self.lock:
            self.access_token=tokens["access_token"]
            self.refresh_token=tokens.get("refresh_token", self.refresh_token)
            self.expires_at=time.time()+int(tokens.get("expires_in",3600))-60
            self.state=None; self.code_verifier=None; self.last_error=""
            self._save()

    def refresh(self):
        if not self.refresh_token: return False
        try:
            tokens=self._token_request({"client_id":self.client_id,"grant_type":"refresh_token","refresh_token":self.refresh_token})
            self.access_token=tokens["access_token"]
            if tokens.get("refresh_token"): self.refresh_token=tokens["refresh_token"]
            self.expires_at=time.time()+int(tokens.get("expires_in",3600))-60
            self._save(); return True
        except Exception as e:
            self.last_error=str(e); return False

    def _ensure(self):
        if not self.access_token: raise RuntimeError("Spotify no está conectado.")
        if time.time() >= self.expires_at and not self.refresh(): raise RuntimeError("La sesión de Spotify expiró.")

    def api(self, method, path, params=None, body=None, retry=True):
        self._ensure()
        url=SPOTIFY_API_BASE+path
        if params: url += "?"+urllib.parse.urlencode(params)
        headers={"Authorization":f"Bearer {self.access_token}"}
        data=None
        if body is not None:
            data=json.dumps(body).encode(); headers["Content-Type"]="application/json"
        req=urllib.request.Request(url,data=data,headers=headers,method=method.upper())
        try:
            with urllib.request.urlopen(req,timeout=15) as r:
                raw=r.read(); return json.loads(raw.decode()) if raw else None
        except urllib.error.HTTPError as e:
            if e.code==401 and retry and self.refresh(): return self.api(method,path,params,body,False)
            detail=e.read().decode(errors="replace")
            self.last_error=f"Spotify HTTP {e.code}: {detail}"
            raise RuntimeError(self.last_error) from e

    def devices(self): return (self.api("GET","/me/player/devices") or {}).get("devices",[])

    def choose_device(self, device_id):
        devices=self.devices()
        chosen=next((d for d in devices if d.get("id")==device_id),None)
        if not chosen: raise RuntimeError("El dispositivo seleccionado ya no está disponible.")
        if chosen.get("is_restricted"): raise RuntimeError("Spotify marcó ese dispositivo como restringido.")
        self.device_id=chosen.get("id"); self.device_name=chosen.get("name",""); self.device_type=chosen.get("type","")
        self._save(); return chosen

    def play(self, uri):
        if not self.device_id: raise RuntimeError("Selecciona un dispositivo Spotify primero.")
        self.api("PUT","/me/player/play",params={"device_id":self.device_id},body={"uris":[uri]})

    def pause(self): self.api("PUT","/me/player/pause",params={"device_id":self.device_id} if self.device_id else None)
    def resume(self): self.api("PUT","/me/player/play",params={"device_id":self.device_id} if self.device_id else None)
    def next(self): self.api("POST","/me/player/next",params={"device_id":self.device_id} if self.device_id else None)
    def volume(self, value): self.api("PUT","/me/player/volume",params={"volume_percent":max(0,min(100,int(value))),"device_id":self.device_id} if self.device_id else {"volume_percent":max(0,min(100,int(value)))})
    def playback(self): return self.api("GET","/me/player")

spotify=SpotifyManager()

@app.route("/spotify/login")
def spotify_login():
    try:
        url=spotify.start_auth()
        return f"<h2>Conectando Spotify…</h2><p>Si no se abrió el navegador, <a href='{url}'>pulsa aquí</a>.</p>"
    except Exception as e: return f"<h2>Error Spotify</h2><pre>{e}</pre>",400

@app.route("/spotify/callback")
def spotify_callback():
    if request.args.get("error"):
        return f"<h2>Spotify canceló la autorización</h2><p>{request.args.get('error')}</p>",400
    try:
        spotify.finish_auth(request.args.get("code",""),request.args.get("state",""))
        try: gui.root.after(0, gui.actualizar_dispositivos_spotify)
        except Exception: pass
        return "<h2>✓ Spotify conectado</h2><p>Vuelve a PatoBot. Ya puedes seleccionar el dispositivo.</p>"
    except Exception as e: return f"<h2>Error OAuth</h2><pre>{e}</pre>",400


def spotify_buscar(query):
    data=spotify.api("GET","/search",params={"q":query,"type":"track","limit":5})
    items=((data or {}).get("tracks") or {}).get("items") or []
    if not items: return None
    q=limpiar_busqueda(query)
    def score(x):
        cand=limpiar_busqueda(x.get("name","")+" "+" ".join(a.get("name","") for a in x.get("artists",[])))
        return len(set(q.split()) & set(cand.split()))*10 + (100 if q==cand else 0)
    t=max(items,key=score)
    return {"title":t.get("name",""),"artist":", ".join(a.get("name","") for a in t.get("artists",[])),"uri":t.get("uri",""),"cover":(((t.get("album") or {}).get("images") or [{}])[0].get("url","")),"duration":(t.get("duration_ms") or 0)/1000,"spotify_url":((t.get("external_urls") or {}).get("spotify",""))}


def spotify_reproducir_siguiente():
    global cancion_actual, SPOTIFY_CURRENT_REQUEST, CANCION_ACTUAL_WIDGET
    if not cola_musica: return False
    item=cola_musica.popleft()
    try:
        spotify.play(item["uri"])
    except Exception as e:
        cola_musica.appendleft(item); gui.agregar_log(f"[SPOTIFY] {e}"); return False
    SPOTIFY_CURRENT_REQUEST=item
    cancion_actual=f"{item['title']} — {item['artist']} (Pedida por @{item['user']})"
    CANCION_ACTUAL_WIDGET={"title":item["title"],"artist":item["artist"],"user":item["user"],"duration":item.get("duration",0),"started_at":time.time(),"cover":item.get("cover",""),"spotify_url":item.get("spotify_url",""),"paused":False,"progress_ms":0}
    gui.actualizar_lista_musica_ui(); gui.actualizar_cancion_actual_ui(cancion_actual); broadcast_overlay_data()
    gui.agregar_log(f"[SPOTIFY] Reproduciendo: {item['title']} — {item['artist']}")
    return True


def reproductor_musica_loop():
    global cancion_actual, SPOTIFY_CURRENT_REQUEST, CANCION_ACTUAL_WIDGET
    while True:
        try:
            if spotify.access_token and not getattr(gui,'musica_pausada',False):
                state=spotify.playback()
                item=(state or {}).get("item") if state else None
                playing=bool((state or {}).get("is_playing"))
                progress=int((state or {}).get("progress_ms") or 0)
                duration=int((item or {}).get("duration_ms") or 0)
                if item:
                    uri=item.get("uri","")
                    if SPOTIFY_CURRENT_REQUEST and uri==SPOTIFY_CURRENT_REQUEST.get("uri"):
                        CANCION_ACTUAL_WIDGET["progress_ms"]=progress; CANCION_ACTUAL_WIDGET["paused"]=not playing
                        CANCION_ACTUAL_WIDGET["started_at"]=time.time()-progress/1000
                    elif not SPOTIFY_CURRENT_REQUEST:
                        CANCION_ACTUAL_WIDGET={"title":item.get("name",""),"artist":", ".join(a.get("name","") for a in item.get("artists",[])),"user":"Spotify","duration":duration/1000,"started_at":time.time()-progress/1000,"cover":(((item.get("album") or {}).get("images") or [{}])[0].get("url","")),"spotify_url":((item.get("external_urls") or {}).get("spotify","")),"paused":not playing,"progress_ms":progress}
                        cancion_actual=f"{CANCION_ACTUAL_WIDGET['title']} — {CANCION_ACTUAL_WIDGET['artist']}"
                    if not playing and duration and progress >= duration-1500 and cola_musica:
                        SPOTIFY_CURRENT_REQUEST=None; spotify_reproducir_siguiente()
                elif cola_musica:
                    spotify_reproducir_siguiente()
                broadcast_overlay_data()
        except Exception as e:
            if spotify.access_token and "No hay" not in str(e):
                pass
        time.sleep(1.5)

threading.Thread(target=reproductor_musica_loop, daemon=True).start()
