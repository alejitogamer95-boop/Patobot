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
