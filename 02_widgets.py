app = Flask(__name__)
overlay_subscribers = []

HTML_BASE_WIDGET = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: '{{ font_family }}', 'Segoe UI', sans-serif; 
            background: transparent; 
            color: {{ text_color }}; 
            margin: 0; 
            padding: 10px; 
        }
        
        /* DISEÑO ESTÁNDAR */
        .card-standard { 
            background: {{ bg_color }}; 
            border-radius: 12px; 
            padding: 12px; 
            width: 320px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
            border: 1px solid {{ border_color }}; 
        }
        .card-standard .title { 
            font-size: 14px; 
            font-weight: bold; 
            color: {{ accent_color }}; 
            text-transform: uppercase; 
            margin-bottom: 10px; 
            text-align: center; 
        }
        .card-standard .item { display: flex; align-items: center; margin-bottom: 8px; font-size: 14px; font-weight: 600; }
        .card-standard .rank { width: 25px; text-align: center; font-weight: bold; }
        .card-standard .name { flex-grow: 1; padding: 0 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .card-standard .score { color: {{ accent_color }}; font-weight: bold; display: flex; align-items: center; gap: 4px; }
        .card-standard .single-box { text-align: center; font-size: 16px; font-weight: bold; padding: 10px; }

        /* DISEÑO ESPECIAL TOP LIKES TRANSPARENTE / CUSTOM */
        .toplikes-container {
            background: transparent;
            width: {{ card_width }}px;
            display: flex;
            flex-direction: column;
            gap: {{ gap_size }}px;
        }
        .toplikes-title {
            font-size: {{ title_font_size }}px;
            font-weight: 900;
            color: {{ accent_color }};
            text-shadow: 0 2px {{ glow_intensity }}px {{ shadow_color }};
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: {{ padding_size }}px;
        }
        .toplikes-card {
            display: flex;
            align-items: center;
            background: {{ card_bg }};
            backdrop-filter: blur({{ card_blur }}px);
            -webkit-backdrop-filter: blur({{ card_blur }}px);
            padding: {{ padding_size }}px 12px;
            border-radius: {{ card_radius }}px;
            gap: {{ gap_size }}px;
            border: {{ card_border_width }}px solid {{ border_color }};
            box-shadow: 0 4px {{ shadow_blur }}px {{ shadow_color }};
        }
        .avatar-box {
            position: relative;
            width: {{ avatar_size }}px;
            height: {{ avatar_size }}px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .avatar-img {
            width: calc({{ avatar_size }}px - 8px);
            height: calc({{ avatar_size }}px - 8px);
            border-radius: {{ avatar_radius }}%;
            object-fit: cover;
        }
        .frame {
            position: absolute;
            top: 0;
            left: 0;
            width: {{ avatar_size }}px;
            height: {{ avatar_size }}px;
            border-radius: {{ avatar_radius }}%;
            box-sizing: border-box;
        }
        .frame-gold { border: 3px solid #ffd700; box-shadow: 0 0 {{ glow_intensity }}px #ffd700; }
        .frame-silver { border: 3px solid #c0c0c0; box-shadow: 0 0 {{ glow_intensity }}px #c0c0c0; }
        .frame-bronze { border: 3px solid #cd7f32; box-shadow: 0 0 {{ glow_intensity }}px #cd7f32; }
        .frame-default { border: 2px solid {{ border_color }}; }
        .crown {
            position: absolute;
            top: {{ crown_top }}px;
            font-size: {{ crown_size }}px;
            filter: drop-shadow(0 2px 3px {{ shadow_color }});
            display: {{ crown_display }};
            z-index: 3;
        }
        .user-name {
            font-size: {{ font_size }}px;
            font-weight: bold;
            color: {{ text_color }};
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-shadow: 0 1px {{ shadow_blur }}px {{ shadow_color }};
        }
        .user-score {
            font-size: calc({{ font_size }}px - 2px);
            font-weight: 800;
            color: {{ accent_color }};
            text-shadow: 0 1px {{ shadow_blur }}px {{ shadow_color }};
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .heart-icon {
            display: inline-block;
            font-size: {{ heart_size }}px;
            transform-origin: center;
        }
        .heart-icon.tap-beat {
            animation: heartTap .9s ease-in-out;
        }
        @keyframes heartTap {
            0%   { transform: scale(1); }
            45%  { transform: scale(1.38); }
            100% { transform: scale(1); }
        }
        .rank-number {
            min-width: 24px;
            text-align: center;
            font-weight: 900;
            color: {{ rank_color }};
            display: {{ rank_display }};
        }
        .rank-badge {
            display: {{ badge_display }};
            min-width: 24px;
            text-align: center;
        }
        .toplikes-card.top-one {
            background: {{ top1_bg }};
            border-color: #ffd700;
            box-shadow: 0 0 {{ glow_intensity }}px rgba(255,215,0,.35), 0 5px {{ shadow_blur }}px {{ shadow_color }};
        }
    </style>
</head>
<body>
    {% if design == "toplikes_custom" %}
    <div class="toplikes-container">
        <div id="content"></div>
    </div>
    {% else %}
    <div class="card-standard">
        <div class="title">{{ title }}</div>
        <div id="content"></div>
    </div>
    {% endif %}

    <script>
        const evtSource = new EventSource("/stream");
        const widgetType = "{{ widget_type }}";
        const design = "{{ design }}";
        const maxUsers = {{ max_users }};
        let lastLikeEventId = "";
        // Seguimiento local de los puntos del Top Likes.
        // Esto hace que el corazón palpite aunque ULTIMA_ACCION sea
        // reemplazada por otra acción (por ejemplo, una meta general).
        const previousLikeScores = new Map();
        const initializedLikeScores = new Set();

        function pulseHeart(target, taps) {
            if (!target) return;
            const amount = Math.max(1, Math.min(Number(taps) || 1, 20));
            let current = Number(target.dataset.pendingTaps || 0);
            target.dataset.pendingTaps = current + amount;

            if (target.dataset.animating === "true") return;
            target.dataset.animating = "true";

            const beatOne = () => {
                let pending = Number(target.dataset.pendingTaps || 0);
                if (pending <= 0) {
                    target.dataset.animating = "false";
                    return;
                }
                target.dataset.pendingTaps = pending - 1;
                target.classList.remove("tap-beat");
                void target.offsetWidth;
                target.classList.add("tap-beat");
                setTimeout(beatOne, 920);
            };
            beatOne();
        }

        evtSource.onmessage = function(e) {
            const data = JSON.parse(e.data);
            const content = document.getElementById("content");

            if (widgetType === "topliker") {
                const items = (data.toplikers || []).slice(0, maxUsers);

                if (design === "toplikes_custom") {
                    if (content.children.length !== items.length) {
                        content.innerHTML = "";
                        items.forEach((item, index) => {
                            content.innerHTML += `
                            <div class="toplikes-card" id="user-card-${index}">
                                <span class="rank-number" id="rank-num-${index}"></span>
                                <span class="rank-badge" id="rank-badge-${index}"></span>
                                <div class="avatar-box">
                                    <div id="crown-${index}"></div>
                                    <img class="avatar-img" id="avatar-${index}" src="">
                                    <div class="frame" id="frame-${index}"></div>
                                </div>
                                <div class="user-info">
                                    <span class="user-name" id="name-${index}"></span>
                                    <span class="user-score"><span class="heart-icon" id="heart-${index}" data-user="">❤️</span> <span id="score-${index}"></span></span>
                                </div>
                            </div>`;
                        });
                    }

                    items.forEach((item, index) => {
                        const itemName = String(item.name || "");
                        const newScore = Number(item.score || 0);
                        const previousScore = previousLikeScores.get(itemName);
                        const heart = document.getElementById(`heart-${index}`);
                        document.getElementById(`rank-num-${index}`).innerText = index + 1;
                        document.getElementById(`rank-badge-${index}`).innerText = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '⭐';
                        document.getElementById(`user-card-${index}`).className = `toplikes-card ${index === 0 ? 'top-one' : ''}`;
                        const frameClass = index === 0 ? "frame-gold" : index === 1 ? "frame-silver" : index === 2 ? "frame-bronze" : "frame-default";
                        document.getElementById(`frame-${index}`).className = `frame ${frameClass}`;
                        document.getElementById(`crown-${index}`).innerHTML = index === 0 ? `<div class="crown">👑</div>` : "";
                        document.getElementById(`avatar-${index}`).src = item.avatar || 'https://www.tiktok.com/favicon.ico';
                        document.getElementById(`name-${index}`).innerText = item.name;
                        document.getElementById(`score-${index}`).innerText = item.score;
                        heart.dataset.user = itemName;
                        heart.dataset.score = String(newScore);
                        if (initializedLikeScores.has(itemName) && previousScore !== undefined && newScore > previousScore) {
                            pulseHeart(heart, newScore - previousScore);
                        }
                        previousLikeScores.set(itemName, newScore);
                        initializedLikeScores.add(itemName);
                    });

                } else {
                    if (content.children.length !== items.length) {
                        content.innerHTML = "";
                        items.forEach((item, index) => {
                            content.innerHTML += `<div class="item" id="std-card-${index}">
                                <span class="rank" id="std-rank-${index}"></span>
                                <span class="name" id="std-name-${index}"></span>
                                <span class="score"><span class="heart-icon" id="std-heart-${index}" data-user="">❤️</span> <span id="std-score-${index}"></span></span>
                            </div>`;
                        });
                    }
                    items.forEach((item, index) => {
                        const itemName = String(item.name || "");
                        const newScore = Number(item.score || 0);
                        const previousScore = previousLikeScores.get(itemName);
                        const heart = document.getElementById(`std-heart-${index}`);
                        let badge = (index === 0) ? '🥇' : (index === 1) ? '🥈' : (index === 2) ? '🥉' : (index + 1) + '.';
                        document.getElementById(`std-rank-${index}`).innerText = badge;
                        document.getElementById(`std-name-${index}`).innerText = item.name;
                        document.getElementById(`std-score-${index}`).innerText = item.score;
                        heart.dataset.user = itemName;
                        heart.dataset.score = String(newScore);
                        if (initializedLikeScores.has(itemName) && previousScore !== undefined && newScore > previousScore) {
                            pulseHeart(heart, newScore - previousScore);
                        }
                        previousLikeScores.set(itemName, newScore);
                        initializedLikeScores.add(itemName);
                    });
                }
            } else if (widgetType === "lastfollower") {
                if (data.last_follower) {
                    content.innerHTML = `<div class="single-box">👤 ${data.last_follower}</div>`;
                } else {
                    content.innerHTML = `<div class="single-box">Sin seguidores aún</div>`;
                }
            }

            // Compatibilidad con el evento explícito de Like.
            // El pulso principal ya se dispara por el cambio real del Top.
            const action = data.last_action;
            if (action && action.type === "like" && action.id !== lastLikeEventId) {
                lastLikeEventId = action.id;
                const targetName = String(action.name || "");
                const target = Array.from(document.querySelectorAll('.heart-icon'))
                    .find(h => h.dataset.user === targetName);
                if (target && !initializedLikeScores.has(targetName)) {
                    pulseHeart(target, action.likes_count || 1);
                }
            }
        };
    </script>
</body>
</html>
"""



HTML_MY_ACTIONS_WIDGET = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
    html, body {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: transparent;
        font-family: '{{ font_family }}', 'Segoe UI', sans-serif;
    }

    .stage {
        position: relative;
        width: 100%;
        min-height: 360px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: {{ text_color }};
    }

    .action {
        position: relative;
        z-index: 5;
        width: min({{ card_width }}px, 90vw);
        min-height: 300px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 18px 20px;
        box-sizing: border-box;
        background: {{ action_bg }};
        border-radius: 28px;
        opacity: 0;
        visibility: hidden;
        transform: translateY(16px) scale(.94);
    }

    .action.show {
        visibility: visible;
        animation: actionIn .45s ease both;
    }

    .action.hide {
        visibility: visible;
        animation: actionOut .35s ease forwards;
    }

    .avatar-wrap {
        position: relative;
        width: {{ avatar_size }}px;
        height: {{ avatar_size }}px;
        margin-bottom: 12px;
    }

    .avatar {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 50%;
        display: block;
        border: 3px solid {{ accent_color }};
        box-shadow: 0 0 {{ glow_intensity }}px {{ accent_color }};
    }

    .name {
        max-width: 100%;
        font-size: {{ name_size }}px;
        line-height: 1.05;
        font-weight: 900;
        color: {{ accent_color }};
        text-shadow: 0 2px {{ shadow_blur }}px {{ shadow_color }};
        margin-bottom: 10px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .message {
        max-width: 100%;
        font-size: {{ message_size }}px;
        line-height: 1.15;
        font-weight: 800;
        color: {{ text_color }};
        text-shadow: 0 2px {{ shadow_blur }}px {{ shadow_color }};
    }

    .particles {
        position: absolute;
        inset: 0;
        overflow: hidden;
        pointer-events: none;
        z-index: 2;
    }

    .particle {
        position: absolute;
        left: var(--x);
        bottom: -45px;
        font-size: var(--size);
        opacity: 0;
        animation: floatUp var(--duration) ease-out forwards;
        animation-delay: var(--delay);
        filter: drop-shadow(0 2px 4px {{ shadow_color }});
    }

    @keyframes floatUp {
        0%   { transform: translate3d(0, 0, 0) scale(.65) rotate(0deg); opacity: 0; }
        12%  { opacity: 1; }
        70%  { opacity: 1; }
        100% { transform: translate3d(var(--drift), -390px, 0) scale(1.15) rotate(var(--rot)); opacity: 0; }
    }

    @keyframes actionIn {
        from { opacity: 0; transform: translateY(16px) scale(.94); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes actionOut {
        from { opacity: 1; transform: translateY(0) scale(1); }
        to   { opacity: 0; transform: translateY(-10px) scale(.97); }
    }

    .event-badge {
        position: absolute;
        top: -8px;
        right: -8px;
        font-size: 24px;
        filter: drop-shadow(0 2px 4px {{ shadow_color }});
    }
</style>
</head>
<body>
<div class="stage">
    <div class="particles" id="particles"></div>
    <div class="action" id="action">
        <div class="avatar-wrap">
            <img class="avatar" id="avatar" src="https://www.tiktok.com/favicon.ico">
            <div class="event-badge" id="badge">❤️</div>
        </div>
        <div class="name" id="name">TikTok</div>
        <div class="message" id="message">Esperando una interacción...</div>
    </div>
</div>

<script>
const source = new EventSource("/stream");
const avatar = document.getElementById("avatar");
const nameEl = document.getElementById("name");
const messageEl = document.getElementById("message");
const badge = document.getElementById("badge");
const action = document.getElementById("action");
const particles = document.getElementById("particles");

let lastActionId = "";
let hideTimer = null;
const ACTION_VISIBLE_MS = 5000;

function hideAction() {
    if (hideTimer) {
        clearTimeout(hideTimer);
        hideTimer = null;
    }
    action.className = "action hide";
    particles.innerHTML = "";
    setTimeout(() => {
        if (!action.classList.contains("show")) {
            action.className = "action";
        }
    }, 380);
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({
        "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
    }[c]));
}

function particleSet(type) {
    if (type === "gift") return ["🎁","✨","💎","🪙","⭐"];
    if (type === "follow") return ["💙","✨","⭐","👋","💫"];
    return ["👍","❤️","💖","💜","💙","💚"];
}

function spawnParticles(type) {
    particles.innerHTML = "";
    const icons = particleSet(type);

    for (let i = 0; i < 14; i++) {
        const p = document.createElement("span");
        p.className = "particle";
        p.textContent = icons[i % icons.length];
        p.style.setProperty("--x", (8 + Math.random() * 84) + "%");
        p.style.setProperty("--drift", ((Math.random() * 90) - 45) + "px");
        p.style.setProperty("--size", (18 + Math.random() * 18) + "px");
        p.style.setProperty("--duration", (2.2 + Math.random() * 1.7) + "s");
        p.style.setProperty("--delay", (Math.random() * .45) + "s");
        p.style.setProperty("--rot", ((Math.random() * 80) - 40) + "deg");
        particles.appendChild(p);
    }
}

function showAction(data) {
    const item = data.last_action;
    if (!item || item.id === lastActionId) return;

    const expiresAt = Number(item.expires_at || 0);
    if (expiresAt && Date.now() / 1000 >= expiresAt) return;

    lastActionId = item.id;

    if (hideTimer) {
        clearTimeout(hideTimer);
        hideTimer = null;
    }

    const fallbackAvatar = "https://www.tiktok.com/favicon.ico";
    avatar.src = item.avatar || fallbackAvatar;
    avatar.onerror = () => { avatar.src = fallbackAvatar; };

    nameEl.textContent = item.name || "Usuario";
    messageEl.textContent = item.message || "¡Gracias por apoyar el Live!";
    badge.textContent = item.icon || "❤️";

    action.className = "action";
    void action.offsetWidth;
    action.className = "action show";
    spawnParticles(item.type || "like");

    const remaining = expiresAt
        ? Math.max(500, Math.min(ACTION_VISIBLE_MS, (expiresAt * 1000) - Date.now()))
        : ACTION_VISIBLE_MS;
    hideTimer = setTimeout(hideAction, remaining);
}

source.onmessage = function(e) {
    try {
        showAction(JSON.parse(e.data));
    } catch (_) {}
};
</script>
</body>
</html>
"""

HTML_GOAL_WIDGET = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><style>
html,body{
    margin:0;
    padding:0;
    background:transparent;
    color:{{ text_color }};
    font-family:'{{ font_family }}','Segoe UI',sans-serif;
    overflow:hidden;
}
.goal{
    width:min({{ width }}px,96vw);
    box-sizing:border-box;
    padding:0;
    background:transparent;
}
.goal-bar-frame{
    position:relative;
    width:100%;
    height:66px;
    padding:7px 9px;
    box-sizing:border-box;
    background:transparent;
    clip-path:polygon(1.8% 0,100% 0,98.2% 100%,0 100%);
}
.goal-bar-track{
    position:relative;
    width:100%;
    height:100%;
    box-sizing:border-box;
    background:{{ track }};
    clip-path:polygon(1.2% 0,100% 0,98.8% 100%,0 100%);
    overflow:hidden;
}
.goal-bar-fill{
    position:absolute;
    left:0;
    top:0;
    bottom:0;
    width:0;
    background:{{ fill }};
    transition:width .35s ease;
}
.goal-percent{
    position:absolute;
    inset:0;
    display:flex;
    align-items:center;
    justify-content:center;
    z-index:2;
    font-size:{{ pct_size }}px;
    line-height:1;
    font-weight:900;
    color:{{ percent_color }};
    text-shadow:0 2px 4px rgba(0,0,0,.20);
    pointer-events:none;
}
.goal-label{
    width:min(430px,58%);
    min-height:45px;
    margin-top:0;
    padding:5px 18px 7px 30px;
    box-sizing:border-box;
    display:flex;
    align-items:center;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
    background:transparent;
    clip-path:polygon(5% 0,100% 0,96% 100%,0 100%);
    font-size:{{ sub_size }}px;
    line-height:1.05;
    font-weight:800;
    letter-spacing:.4px;
    text-transform:uppercase;
    color:{{ fill }};
    text-shadow:0 2px 5px rgba(0,0,0,.55);
}
.goal-label-text{
    overflow:hidden;
    text-overflow:ellipsis;
    white-space:nowrap;
}
</style></head><body><div class="goal">
    <div class="goal-bar-frame">
        <div class="goal-bar-track">
            <div class="goal-bar-fill" id="fill"></div>
            <div class="goal-percent" id="pct">0%</div>
        </div>
    </div>
    <div class="goal-label"><div class="goal-label-text" id="label">META - 0 / {{ target }} FOLLOWS</div></div>
</div>
<script>
const es=new EventSource('/stream');
const goalType='{{ goal_type }}';
const target={{ target }};
const fillEl=document.getElementById('fill');
const pctEl=document.getElementById('pct');
const labelEl=document.getElementById('label');

function update(d){
    let value=0,targetLocal=target,label='META',unit='FOLLOWS';

    if(goalType==='likes'){
        value=d.total_likes||0;
        unit='LIKES';
    }else if(goalType==='likes_persona'){
        const x=d.last_like_goal||{};
        value=x.progress||0;
        targetLocal=x.target||target;
        label=x.name ? 'META - @'+x.name : 'META';
        unit='LIKES';
    }else{
        value=d.follows_total||0;
        unit='FOLLOWS';
    }

    const t=Math.max(1,targetLocal);
    const shown=Math.min(value,t);
    const pct=Math.round(shown/t*100);

    fillEl.style.width=pct+'%';
    pctEl.textContent=pct+'%';

    if(goalType==='likes_persona' && label!=='META'){
        labelEl.textContent=label+' - '+shown+' / '+t+' '+unit;
    }else{
        labelEl.textContent='META - '+shown+' / '+t+' '+unit;
    }
}

es.onmessage=e=>{
    try{update(JSON.parse(e.data))}catch(_){}
};
</script></body></html>
"""


HTML_SONGREQUESTS_WIDGET = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><style>
html,body{margin:0;padding:0;background:transparent;color:{{ text_color }};font-family:'{{ font_family }}','Segoe UI',sans-serif;overflow:hidden}.wrap{width:min({{ width }}px,95vw);background:{{ bg }};border:1px solid {{ border }};border-radius:14px;padding:10px;box-sizing:border-box;box-shadow:0 5px 20px {{ shadow }}}.title{color:{{ accent }};font-size:{{ title_size }}px;font-weight:900;margin:2px 4px 10px}.song{display:flex;gap:10px;align-items:center;padding:8px 4px;border-top:1px solid {{ border }}}.cover{width:64px;height:64px;border-radius:8px;object-fit:cover;background:#111}.info{min-width:0;flex:1}.name{font-size:{{ name_size }}px;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.meta{font-size:{{ meta_size }}px;opacity:.8;margin-top:4px}.status{font-size:{{ meta_size }}px;color:{{ accent }};margin-top:4px}.empty{padding:14px 4px;opacity:.75}.progress{height:6px;background:{{ track }};border-radius:5px;overflow:hidden;margin-top:5px}.progress i{display:block;height:100%;width:0;background:{{ accent }}}
</style></head><body><div class="wrap"><div class="title">{{ title }}</div><div id="content"></div></div>
<script>
const es=new EventSource('/stream'),content=document.getElementById('content'),fallback='https://www.tiktok.com/favicon.ico';function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))}function fmt(sec){sec=Math.max(0,Math.floor(sec));return Math.floor(sec/60)+':'+String(sec%60).padStart(2,'0')}
function render(d){let html='';const cur=d.current_song;if(cur&&cur.title){html+=`<div class="song"><img class="cover" src="${esc(cur.cover||fallback)}" onerror="this.src='${fallback}'"><div class="info"><div class="name">${esc(cur.title)}</div><div class="meta">Pedida por @${esc(cur.user||'Usuario')}</div><div class="status" id="now">Sonando ${fmt(cur.elapsed||0)} / ${fmt(cur.duration||0)}</div><div class="progress"><i id="bar"></i></div></div></div>`}else{html+='<div class="empty">Ninguna canción reproduciéndose</div>'}const q=d.song_queue||[];q.slice(0,{{ max_users }}).forEach((x,i)=>{html+=`<div class="song"><img class="cover" src="${esc(x.cover||fallback)}" onerror="this.src='${fallback}'"><div class="info"><div class="name">${i+1}. ${esc(x.title||x.query||'Canción')}</div><div class="meta">En cola · por @${esc(x.user||'Usuario')}</div><div class="status">En espera</div></div></div>`});if(!cur&&!q.length)html='<div class="empty">La cola está vacía</div>';content.innerHTML=html;window.__cur=cur}
function tick(){const cur=window.__cur;if(!cur||!cur.started_at||!cur.duration)return;const elapsed=Math.min(cur.duration,Math.max(0,Date.now()/1000-cur.started_at));const now=document.getElementById('now'),bar=document.getElementById('bar');if(now)now.textContent='Sonando '+fmt(elapsed)+' / '+fmt(cur.duration);if(bar)bar.style.width=Math.min(100,elapsed/cur.duration*100)+'%'}es.onmessage=e=>{try{render(JSON.parse(e.data))}catch(_){}};setInterval(tick,1000);
</script></body></html>
"""

@app.route("/widget/myactions")
def widget_myactions():
    def qint(name, default):
        try:
            return int(request.args.get(name, default))
        except (TypeError, ValueError):
            return default

    return render_template_string(
        HTML_MY_ACTIONS_WIDGET,
        font_family=request.args.get("font", "Segoe UI"),
        text_color=request.args.get("text", "#ffffff"),
        accent_color=request.args.get("accent", "#38d9c5"),
        shadow_color=request.args.get("shadow", "rgba(0,0,0,.85)"),
        action_bg=request.args.get("action_bg", "transparent"),
        card_width=qint("width", 380),
        avatar_size=qint("avatar_size", 100),
        name_size=qint("name_size", 42),
        message_size=qint("message_size", 24),
        shadow_blur=qint("shadow_blur", 10),
        glow_intensity=qint("glow", 12)
    )

@app.route("/widget/goal")
def widget_goal():
    def qi(name, default):
        try: return max(1, int(request.args.get(name, default)))
        except (TypeError, ValueError): return default
    return render_template_string(HTML_GOAL_WIDGET,
        font_family=request.args.get("font", "Segoe UI"), text_color=request.args.get("text", "#ffffff"),
        accent=request.args.get("accent", "#7b3f91"), bg=request.args.get("bg", "transparent"),
        border=request.args.get("border", "transparent"), shadow=request.args.get("shadow", "transparent"),
        track=request.args.get("track", "#55b4d6"), fill=request.args.get("fill", "#55b4d6"),
        frame_color=request.args.get("frame", "transparent"), label_bg=request.args.get("label_bg", "transparent"), percent_color=request.args.get("percent", "#238f8b"),
        width=qi("goal_width", qi("width", 1460)), title_size=qi("title_size", 20), count_size=qi("count_size", 24), pct_size=qi("pct_size", 30), sub_size=qi("sub_size", 22), glow=qi("glow", 0),
        title=request.args.get("title", "New Followers"), target=qi("target", config.get("meta_follows",100)), goal_type=request.args.get("goal", "follows"))

@app.route("/widget/songrequests")
def widget_songrequests():
    def qi(name, default):
        try: return max(1, int(request.args.get(name, default)))
        except (TypeError, ValueError): return default
    return render_template_string(HTML_SONGREQUESTS_WIDGET,
        font_family=request.args.get("font", "Segoe UI"), text_color=request.args.get("text", "#ffffff"),
        accent=request.args.get("accent", "#89b4fa"), bg=request.args.get("bg", "rgba(30,30,46,.9)"),
        border=request.args.get("border", "rgba(49,50,68,.8)"), shadow=request.args.get("shadow", "rgba(0,0,0,.8)"),
        track=request.args.get("track", "rgba(255,255,255,.14)"), width=qi("width", 520), title_size=qi("title_size", 20), name_size=qi("name_size", 20), meta_size=qi("meta_size", 14),
        max_users=qi("max", 5), title=request.args.get("title", "Solicitudes de Canciones"))

def render_custom_widget(widget_type, default_title):
    bg_color = request.args.get("bg", "rgba(30, 30, 46, 0.9)")
    card_bg = request.args.get("card_bg", "rgba(0, 0, 0, 0.4)")
    text_color = request.args.get("text", "#cdd6f4")
    accent_color = request.args.get("accent", "#89b4fa")
    border_color = request.args.get("border", "rgba(49, 50, 68, 0.8)")
    shadow_color = request.args.get("shadow", "rgba(0, 0, 0, 0.8)")
    font_family = request.args.get("font", "Segoe UI")
    title = request.args.get("title", default_title)
    design = request.args.get("design", "standard")
    
    try: max_users = int(request.args.get("max", 5))
    except ValueError: max_users = 5

    try: font_size = int(request.args.get("font_size", 14))
    except ValueError: font_size = 14

    try: title_font_size = int(request.args.get("title_font_size", 16))
    except ValueError: title_font_size = 16

    try: avatar_size = int(request.args.get("avatar_size", 52))
    except ValueError: avatar_size = 52

    try: gap_size = int(request.args.get("gap", 12))
    except ValueError: gap_size = 12

    try: padding_size = int(request.args.get("padding", 8))
    except ValueError: padding_size = 8

    try: card_width = int(request.args.get("width", 340))
    except ValueError: card_width = 340

    try: shadow_blur = int(request.args.get("shadow_blur", 10))
    except ValueError: shadow_blur = 10

    try: glow_intensity = int(request.args.get("glow", 8))
    except ValueError: glow_intensity = 8

    # Controles avanzados exclusivos del Top Likes
    def qint(name, default):
        try: return int(request.args.get(name, default))
        except (TypeError, ValueError): return default
    card_radius = qint("radius", 50)
    card_blur = qint("card_blur", 4)
    card_border_width = qint("border_width", 0)
    avatar_radius = max(0, min(50, qint("avatar_radius", 50)))
    heart_size = qint("heart_size", max(12, font_size))
    crown_size = qint("crown_size", 16)
    crown_top = qint("crown_top", -14)
    crown_display = "block" if request.args.get("crown", "1") == "1" else "none"
    heart_animation = "heartPop" if request.args.get("heart_anim", "heartbeat") == "pop" else "heartbeat"
    rank_display = "block" if request.args.get("show_rank", "0") == "1" else "none"
    badge_display = "block" if request.args.get("show_badges", "0") == "1" else "none"
    rank_color = request.args.get("rank_color", accent_color)
    top1_bg = request.args.get("top1_bg", card_bg)

    return render_template_string(
        HTML_BASE_WIDGET,
        widget_type=widget_type,
        title=title,
        bg_color=bg_color,
        card_bg=card_bg,
        text_color=text_color,
        accent_color=accent_color,
        border_color=border_color,
        shadow_color=shadow_color,
        font_family=font_family,
        design=design,
        max_users=max_users,
        font_size=font_size,
        title_font_size=title_font_size,
        avatar_size=avatar_size,
        gap_size=gap_size,
        padding_size=padding_size,
        card_width=card_width,
        shadow_blur=shadow_blur,
        glow_intensity=glow_intensity,
        card_radius=card_radius,
        card_blur=card_blur,
        card_border_width=card_border_width,
        avatar_radius=avatar_radius,
        heart_size=heart_size,
        heart_animation=heart_animation,
        crown_size=crown_size,
        crown_top=crown_top,
        crown_display=crown_display,
        rank_display=rank_display,
        badge_display=badge_display,
        rank_color=rank_color,
        top1_bg=top1_bg
    )

@app.route("/widget/topliker")
def widget_topliker():
    return render_custom_widget("topliker", "")
@app.route("/widget/lastfollower")
def widget_lastfollower():
    return render_custom_widget("lastfollower", "Último Seguidor")

@app.route("/stream")
def stream():
    def event_stream():
        q = queue.Queue()
        overlay_subscribers.append(q)
        try:
            broadcast_overlay_data()
            while True:
                data = q.get()
                yield f"data: {json.dumps(data)}\n\n"
        except GeneratorExit:
            overlay_subscribers.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")

def broadcast_overlay_data():
    top_likers = sorted(LIKES_POR_USUARIO.items(), key=lambda x: x[1]["score"], reverse=True)[:15]
    formatted_likers = [{"name": k, "score": v["score"], "progress": v.get("progress", 0), "goal_hits": v.get("goal_hits", 0), "goal_active": v.get("goal_active", True), "avatar": v["avatar"]} for k, v in top_likers]
    top_donators = sorted(DONACIONES_POR_USUARIO.items(), key=lambda x: x[1], reverse=True)[:15]
    formatted_donators = [{"name": k, "score": v} for k, v in top_donators]
    queue_payload = [{"query": q, "title": q, "user": u, "cover": ""} for q, u in list(cola_musica)]
    current = dict(CANCION_ACTUAL_WIDGET)
    if current.get("started_at") and current.get("duration"):
        current["elapsed"] = max(0, time.time() - current["started_at"])
    active_action = ULTIMA_ACCION
    if active_action:
        expires_at = float(active_action.get("expires_at", 0) or 0)
        if expires_at and time.time() >= expires_at:
            active_action = None

    payload = {
        "toplikers": formatted_likers, "topdonators": formatted_donators,
        "last_gift": ULTIMO_REGALO, "last_follower": ULTIMO_SEGUIDOR,
        "last_action": active_action, "total_likes": STATS["likes_totales"],
        "follows_total": STATS["follows"], "last_like_goal": dict(ULTIMO_LIKE_META or {}),
        "current_song": current if current.get("title") else None, "song_queue": queue_payload
    }
    for q in list(overlay_subscribers):
        try: q.put(payload)
        except Exception: pass

def run_flask_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

