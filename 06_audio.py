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
