# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'patobot.py'
# Bytecode version: 3.10.b1 (3439)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

global CONTADOR_LIKES_GENERAL
global TIEMPO_INICIO
global canal_musica_ram
global cancion_actual
global VOTOS_SKIP
global ULTIMO_SKIP_TIEMPO
# ***<module>: Failure: Compilation Error
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
import urllib.parse
import urllib.error
from collections import deque, defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, font
from flask import Flask, render_template_string, Response, request
import pygame
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, FollowEvent, LikeEvent
import edge_tts
import psutil
import yt_dlp
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
    global ULTIMA_ACCION
    top_likers = sorted(LIKES_POR_USUARIO.items(), key=lambda x: x[1], reverse=True)[:15]
    formatted_likers = [
        {"name": k, "score": v, "progress": v, "goal_hits": 0,
         "goal_active": True, "avatar": ""}
        for k, v in top_likers
    ]
    queue_payload = []
    for item in list(cola_musica):
        try:
            query, user = item
            queue_payload.append({"query": query, "title": query, "user": user, "cover": ""})
        except Exception:
            queue_payload.append({"query": str(item), "title": str(item), "user": "Usuario", "cover": ""})

    current = None
    if cancion_actual:
        current = {
            "title": str(cancion_actual),
            "user": "",
            "duration": 0,
            "started_at": 0,
            "cover": ""
        }

    active_action = ULTIMA_ACCION
    if active_action:
        expires_at = float(active_action.get("expires_at", 0) or 0)
        if expires_at and time.time() >= expires_at:
            active_action = None
            ULTIMA_ACCION = None

    payload = {
        "toplikers": formatted_likers,
        "topdonators": [],
        "last_gift": ULTIMO_REGALO,
        "last_follower": ULTIMO_SEGUIDOR,
        "last_action": active_action,
        "total_likes": STATS["likes_totales"],
        "follows_total": STATS["follows"],
        "last_like_goal": dict(ULTIMO_LIKE_META or {}),
        "current_song": current,
        "song_queue": queue_payload
    }
    for q in list(overlay_subscribers):
        try:
            q.put(payload)
        except Exception:
            pass

def run_flask_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

CONFIG_FILE = 'config.json'
CONFIG_DEFAULTS = {
    'usuario': '@', 'volumen': 0.6, 'volumen_alertas': 0.7, 'volumen_musica': 0.2,
    'voz': 'es-MX-JorgeNeural', 'velocidad': '+30%', 'tono': '+0Hz',
    'limite_caracteres': 100, 'palabras_censuradas': 'groseria1, groseria2',
    'reemplazos': 'gg:yiyi, xq:porque, q:que, k:que, 67:six seven, tbm:también',
    'restringir_subs': False, 'nivel_sub_minimo': 2, 'restringir_mods': False,
    'restringir_lista': False, 'lista_blanca': 'usuario, usuario', 'lista_djs': '',
    'alerta_regalos': True, 'alerta_follows': True, 'alerta_likes_general': False,
    'meta_likes_general': 1000, 'repetir_likes_general': True,
    'alerta_likes_persona': True, 'meta_likes_persona': 50, 'repetir_likes_persona': True,
    'url_regalo': '', 'url_follow': '', 'url_like_general': '', 'url_like_persona': '',
    'fuente_interfaz': 'Segoe UI',
    'widget_designs': {
        'topliker': {'design': 'toplikes_custom', 'max': 5, 'title': ''},
        'myactions': {'design': 'myactions', 'max': 1, 'title': 'Mis Acciones'},
        'lastfollower': {'design': 'standard', 'max': 1, 'title': 'Último Seguidor'},
        'goal': {'design': 'goal', 'max': 1, 'title': 'Meta de Follows'},
        'songrequests': {'design': 'songrequests', 'max': 5, 'title': 'Solicitudes de Canciones'}
    },
    'cmd_play': '!play', 'cmd_skip': '!skip', 'cmd_pause': '!pause',
    'cmd_resume': '!resume', 'cmd_volume': '!vol',
    'perm_sub_play': True, 'perm_sub_skip': False, 'perm_sub_pause': False,
    'perm_sub_resume': False, 'perm_sub_vol': False,
    'perm_mod_play': True, 'perm_mod_skip': True, 'perm_mod_pause': True,
    'perm_mod_resume': True, 'perm_mod_vol': True,
    'perm_dj_play': True, 'perm_dj_skip': True, 'perm_dj_pause': True,
    'perm_dj_resume': True, 'perm_dj_vol': True,
}

def cargar_configuracion():
    # irreducible cflow, using cdg fallback
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                return {**CONFIG_DEFAULTS, **datos}
        except Exception:
            return CONFIG_DEFAULTS
    else:
        return CONFIG_DEFAULTS
    return CONFIG_DEFAULTS
def guardar_configuracion(datos):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f'Error al guardar config: {e}')
config = cargar_configuracion()
VOLUMEN = config['volumen']
VOLUMEN_ALERTAS = config.get('volumen_alertas', 0.8)
VOLUMEN_MUSICA = config.get('volumen_musica', 0.4)
VELOCIDAD_AUDIO = config['velocidad']
VOZ_TTS = config['voz']
TONO_TTS = config.get('tono', '+0Hz')
HISTORIAL_RECIENTE = deque(maxlen=20)
TIEMPO_INICIO = time.time()
CONTADOR_LIKES_GENERAL = 0
LIKES_POR_USUARIO = defaultdict(int)
ULTIMO_REGALO = None
ULTIMO_SEGUIDOR = None
ULTIMA_ACCION = None
ULTIMO_LIKE_META = None
CANCION_ACTUAL_WIDGET = {"title": "", "user": "", "duration": 0, "started_at": 0, "cover": ""}
VOTOS_SKIP = set()
UMBRAL_VOTOS_SKIP = 3
ULTIMO_SKIP_TIEMPO = 0
COOLDOWN_SKIP_SEGUNDOS = 5
STATS = {'comentarios': 0, 'regalos': 0, 'follows': 0, 'likes_totales': 0}
pygame.mixer.init()
pygame.mixer.set_num_channels(16)
cola_mensajes = queue.Queue(maxsize=50)
cola_musica = deque()
cancion_actual = None

# Servidor local para overlays/widgets.
threading.Thread(target=run_flask_server, daemon=True).start()
canal_musica_ram = None
def reproducir_sonido_url(url):
    url = url.strip()
    if not url or not url.startswith('http'):
        gui.agregar_log('[Alerta Audio]: Ingresa una URL válida que empiece por http')
        return
    else:
        def _stream_and_play():
            try:
                target_url = url
                if 'myinstants.com' in target_url and (not target_url.endswith('.mp3')):
                        slug = target_url.rstrip('/').split('/')[(-1)]
                        target_url = f'https://www.myinstants.com/media/sounds/{slug}.mp3'
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'audio/mpeg, audio/*;q=0.9, */*;q=0.8', 'Referer': 'https://www.myinstants.com/'}
                req = urllib.request.Request(target_url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    audio_bytes = response.read()
                if not audio_bytes:
                    gui.agregar_log('[Error MyInstants]: Archivo vacío.')
                    return
                else:
                    audio_buffer = io.BytesIO(audio_bytes)
                    sonido = pygame.mixer.Sound(audio_buffer)
                    canal = pygame.mixer.find_channel(True)
                    if canal:
                        volumen_alertas_real = float(gui.slider_volumen_alertas.get()) * 0.75
                        canal.set_volume(volumen_alertas_real)
                        canal.play(sonido)
                    else:
                        gui.agregar_log('[Error Audio]: Sin canales disponibles.')
            except Exception as e:
                gui.agregar_log(f'[Error Audio]: {e}')
        threading.Thread(target=_stream_and_play, daemon=True).start()
def limpiar_busqueda(query):
    query = re.sub('[^\\w\\s]', ' ', query.lower())
    palabras_basura = {'audio', 'full', 'hd', 'letra', 'official', 'oficial', 'video', 'lyric', 'dj'}
    palabras = [p for p in query.split() if p not in palabras_basura]
    if palabras:
        return ' '.join(palabras)
    else:
        return query
def obtener_stream_audio(busqueda):
    if busqueda.startswith('http'):
        motores = [busqueda]
    else:
        busqueda_limpia = limpiar_busqueda(busqueda)
        motores = [
            f'scsearch1:{busqueda_limpia}',
            f'ytsearch1:{busqueda_limpia}',
            f'ytsearch1:{busqueda_limpia} topic',
        ]

    ydl_opts = {
        'format': 'bestaudio[protocol^=http][protocol!=m3u8]/bestaudio[ext=mp3]/bestaudio',
        'noplaylist': True, 'quiet': True, 'no_warnings': True,
        'nocheckcertificate': True, 'ignoreerrors': True, 'extract_flat': False,
        'max_filesize': 25000000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for motor in motores:
                try:
                    info = ydl.extract_info(motor, download=False)
                    if not info:
                        continue
                    if 'entries' in info:
                        entradas_validas = [e for e in info['entries'] if e is not None]
                        if not entradas_validas:
                            continue
                        info = entradas_validas[0]
                    if not isinstance(info, dict):
                        continue

                    duracion = info.get('duration') or 0
                    if duracion > 600:
                        gui.agregar_log(f"[BÚSQUEDA] Ignorada (>10 min): {info.get('title')}")
                        continue

                    stream_url = None
                    for fmt in info.get('formats', []):
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
                        titulo = info.get('title', 'Canción Desconocida')
                        uploader = info.get('uploader', '')
                        if uploader and uploader.lower() not in titulo.lower():
                            titulo = f'{uploader} - {titulo}'
                        return stream_url, titulo
                except Exception as e:
                    gui.agregar_log(f'[Error Búsqueda]: {e}')
    except Exception as e:
        gui.agregar_log(f'[Error yt-dlp]: {e}')
    return None, None

def reproductor_musica_loop():
    global cancion_actual
    global canal_musica_ram
    while True:
        esta_ocupado = canal_musica_ram and canal_musica_ram.get_busy()
        if cola_musica and (not esta_ocupado) and (not getattr(gui, 'musica_pausada', False)):
            query, usuario = cola_musica.popleft()
            gui.actualizar_lista_musica_ui()
            gui.agregar_log(f'[BÚSQUEDA] Buscando: {query}...')
            stream_url, titulo = obtener_stream_audio(query)
            if stream_url:
                try:
                    cancion_actual = f'{titulo} (Pedida por @{usuario})'
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
                            else:
                                buffer_ram.write(chunk)
                    buffer_ram.seek(0)
                    if len(buffer_ram.getvalue()) > 10000:
                        sonido_cancion = pygame.mixer.Sound(buffer_ram)
                        canal_musica_ram = pygame.mixer.Channel(0)
                        vol_val = float(gui.slider_volumen_musica.get()) if hasattr(gui, 'slider_volumen_musica') else VOLUMEN_MUSICA
                        canal_musica_ram.set_volume(vol_val * 0.25)
                        canal_musica_ram.play(sonido_cancion)
                        gui.agregar_log(f'[REPRODUCIENDO EN RAM] {cancion_actual}')
                        while canal_musica_ram.get_busy() or getattr(gui, 'musica_pausada', False):
                            time.sleep(1)
                        buffer_ram.close()
                        cancion_actual = None
                        VOTOS_SKIP.clear()
                        gui.actualizar_cancion_actual_ui('Ninguna')
                    else:
                        buffer_ram.close()
                        gui.agregar_log('[Error Reproducción]: Stream no compatible o vacío.')
                        cancion_actual = None
                        VOTOS_SKIP.clear()
                        gui.actualizar_cancion_actual_ui('Ninguna')
                except Exception as e:
                    gui.agregar_log(f'[Error Reproducción]: {e}')
                    cancion_actual = None
                    VOTOS_SKIP.clear()
                    gui.actualizar_cancion_actual_ui('Ninguna')
            else:
                gui.agregar_log(f'[MÚSQUEDA] No se encontró resultado válido para: {query}')
                cancion_actual = None
                VOTOS_SKIP.clear()
                gui.actualizar_cancion_actual_ui('Ninguna')
        time.sleep(1)
threading.Thread(target=reproductor_musica_loop, daemon=True).start()
class PanelControl:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('TikTok Live Bot - Multiplataforma')
        self.root.geometry('640x980')
        self.root.configure(bg='#1e1e2e')
        self.root.protocol('WM_DELETE_WINDOW', self.al_cerrar)
        self.proceso_actual = psutil.Process(os.getpid())
        self.tiempo_conexion_inicio = None
        self.audio_pausado = False
        self.musica_pausada = False
        self.restringir_subs = tk.BooleanVar(value=config['restringir_subs'])
        self.restringir_mods = tk.BooleanVar(value=config['restringir_mods'])
        self.restringir_lista = tk.BooleanVar(value=config['restringir_lista'])
        self.perm_sub_play = tk.BooleanVar(value=config.get('perm_sub_play', True))
        self.perm_sub_skip = tk.BooleanVar(value=config.get('perm_sub_skip', False))
        self.perm_sub_pause = tk.BooleanVar(value=config.get('perm_sub_pause', False))
        self.perm_sub_resume = tk.BooleanVar(value=config.get('perm_sub_resume', False))
        self.perm_sub_vol = tk.BooleanVar(value=config.get('perm_sub_vol', False))
        self.perm_mod_play = tk.BooleanVar(value=config.get('perm_mod_play', True))
        self.perm_mod_skip = tk.BooleanVar(value=config.get('perm_mod_skip', True))
        self.perm_mod_pause = tk.BooleanVar(value=config.get('perm_mod_pause', True))
        self.perm_mod_resume = tk.BooleanVar(value=config.get('perm_mod_resume', True))
        self.perm_mod_vol = tk.BooleanVar(value=config.get('perm_mod_vol', True))
        self.perm_dj_play = tk.BooleanVar(value=config.get('perm_dj_play', True))
        self.perm_dj_skip = tk.BooleanVar(value=config.get('perm_dj_skip', True))
        self.perm_dj_pause = tk.BooleanVar(value=config.get('perm_dj_pause', True))
        self.perm_dj_resume = tk.BooleanVar(value=config.get('perm_dj_resume', True))
        self.perm_dj_vol = tk.BooleanVar(value=config.get('perm_dj_vol', True))
        self.alerta_regalos = tk.BooleanVar(value=config.get('alerta_regalos', True))
        self.alerta_follows = tk.BooleanVar(value=config.get('alerta_follows', True))
        self.alerta_likes_general = tk.BooleanVar(value=config.get('alerta_likes_general', True))
        self.repetir_likes_general = tk.BooleanVar(value=config.get('repetir_likes_general', True))
        self.alerta_likes_persona = tk.BooleanVar(value=config.get('alerta_likes_persona', True))
        self.repetir_likes_persona = tk.BooleanVar(value=config.get('repetir_likes_persona', True))
        self.client_tiktok = None
        self.conectado = False
        self.fuente_actual = config.get('fuente_interfaz', 'Segoe UI')
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TFrame', background='#1e1e2e')
        style.configure('TLabelframe', background='#1e1e2e', foreground='#cdd6f4')
        style.configure('TLabelframe.Label', background='#1e1e2e', foreground='#cdd6f4', font=(self.fuente_actual, 9, 'bold'))
        style.configure('TLabel', background='#1e1e2e', foreground='#cdd6f4', font=(self.fuente_actual, 9))
        style.configure('TCheckbutton', background='#1e1e2e', foreground='#cdd6f4', font=(self.fuente_actual, 9))
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        self.tab_principal = ttk.Frame(self.notebook)
        self.tab_musica = ttk.Frame(self.notebook)
        self.tab_tts = ttk.Frame(self.notebook)
        self.tab_filtros = ttk.Frame(self.notebook)
        self.tab_alertas = ttk.Frame(self.notebook)
        self.tab_widgets = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_principal, text=' Dashboard ')
        self.notebook.add(self.tab_musica, text=' Música y Comandos ')
        self.notebook.add(self.tab_tts, text=' Voz y TTS ')
        self.notebook.add(self.tab_filtros, text=' Filtros y Fuente ')
        self.notebook.add(self.tab_alertas, text=' Alertas ')
        self.notebook.add(self.tab_widgets, text=' Widgets / Overlay ')
        frame_conexion = ttk.LabelFrame(self.tab_principal, text=' Conexión a Live ')
        frame_conexion.pack(fill='x', padx=10, pady=5)
        f_user = ttk.Frame(frame_conexion)
        f_user.pack(fill='x', padx=10, pady=8)
        ttk.Label(f_user, text='Usuario Live:').pack(side='left')
        self.entry_user = tk.Entry(f_user, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 10), relief='flat')
        self.entry_user.insert(0, config['usuario'])
        self.entry_user.pack(side='left', fill='x', expand=True, padx=10)
        self.btn_conectar = tk.Button(f_user, text='Conectar Live', bg='#a6e3a1', fg='#11111b', relief='flat', command=self.alternar_conexion, font=(self.fuente_actual, 9, 'bold'))
        self.btn_conectar.pack(side='right')
        frame_estado = ttk.Frame(self.tab_principal)
        frame_estado.pack(fill='x', padx=10, pady=2)
        self.lbl_estado = tk.Label(frame_estado, text='Estado: Desconectado', fg='#f38ba8', bg='#1e1e2e', font=(self.fuente_actual, 10, 'bold'))
        self.lbl_estado.pack(side='left')
        self.lbl_ram = ttk.Label(frame_estado, text='RAM: 0.0 MB')
        self.lbl_ram.pack(side='right', padx=(10, 0))
        self.lbl_cola = ttk.Label(frame_estado, text='En cola: 0/50')
        self.lbl_cola.pack(side='right')
        frame_tiempo = ttk.Frame(self.tab_principal)
        frame_tiempo.pack(fill='x', padx=10, pady=2)
        self.lbl_tiempo_live = tk.Label(frame_tiempo, text='Live activo: 00:00:00', fg='#89b4fa', bg='#1e1e2e', font=(self.fuente_actual, 10, 'bold'))
        self.lbl_tiempo_live.pack(side='left')
        frame_stats = ttk.LabelFrame(self.tab_principal, text=' Estadísticas del Stream ')
        frame_stats.pack(fill='x', padx=10, pady=5)
        f_m = ttk.Frame(frame_stats)
        f_m.pack(fill='x', padx=5, pady=5)
        self.lbl_stat_chat = ttk.Label(f_m, text='Leídos: 0')
        self.lbl_stat_chat.pack(side='left', expand=True)
        self.lbl_stat_gifts = ttk.Label(f_m, text='Regalos: 0')
        self.lbl_stat_gifts.pack(side='left', expand=True)
        self.lbl_stat_follows = ttk.Label(f_m, text='Follows: 0')
        self.lbl_stat_follows.pack(side='left', expand=True)
        self.lbl_stat_likes = ttk.Label(f_m, text='Likes: 0')
        self.lbl_stat_likes.pack(side='left', expand=True)
        frame_ctrl_dash = ttk.LabelFrame(self.tab_principal, text=' Control de Música ')
        frame_ctrl_dash.pack(fill='x', padx=10, pady=5)
        f_btn_dash = ttk.Frame(frame_ctrl_dash)
        f_btn_dash.pack(fill='x', padx=5, pady=5)
        self.btn_pause_musica = tk.Button(f_btn_dash, text='Pausar / Reanudar', bg='#f9e2af', fg='#11111b', relief='flat', command=self.alternar_pausa_musica, font=(self.fuente_actual, 9, 'bold'))
        self.btn_pause_musica.pack(side='left', fill='x', expand=True, padx=3)
        btn_next_musica = tk.Button(f_btn_dash, text='Siguiente (Next) ⏭', bg='#89b4fa', fg='#11111b', relief='flat', command=self.saltar_cancion_manual, font=(self.fuente_actual, 9, 'bold'))
        btn_next_musica.pack(side='left', fill='x', expand=True, padx=3)
        frame_log = ttk.LabelFrame(self.tab_principal, text=' Registro de Eventos y Chat ')
        frame_log.pack(fill='both', expand=True, padx=10, pady=5)
        self.log_box = scrolledtext.ScrolledText(frame_log, height=10, bg='#11111b', fg='#a6e3a1', insertbackground='white', font=(self.fuente_actual, 9), relief='flat')
        self.log_box.pack(padx=8, pady=5, fill='both', expand=True)
        f_log_acc = ttk.Frame(frame_log)
        f_log_acc.pack(fill='x', padx=8, pady=5)
        btn_guardar_log = tk.Button(f_log_acc, text='Guardar Registro (.txt)', bg='#89b4fa', fg='#11111b', relief='flat', command=self.exportar_log, font=(self.fuente_actual, 8, 'bold'))
        btn_guardar_log.pack(side='left', padx=2)
        btn_borrar_log = tk.Button(f_log_acc, text='Limpiar Cuadro', bg='#f38ba8', fg='#11111b', relief='flat', command=self.limpiar_cuadro_log, font=(self.fuente_actual, 8, 'bold'))
        btn_borrar_log.pack(side='right', padx=2)
        frame_rep_actual = ttk.LabelFrame(self.tab_musica, text=' Reproducción Actual ')
        frame_rep_actual.pack(fill='x', padx=10, pady=5)
        self.lbl_now_playing = tk.Label(frame_rep_actual, text='Sonando: Ninguna', fg='#a6e3a1', bg='#1e1e2e', font=(self.fuente_actual, 9, 'bold'), anchor='w', justify='left')
        self.lbl_now_playing.pack(fill='x', padx=10, pady=5)
        frame_vol_musica = ttk.LabelFrame(self.tab_musica, text=' Control de Volumen ')
        frame_vol_musica.pack(fill='x', padx=10, pady=5)
        f_vol_m = ttk.Frame(frame_vol_musica)
        f_vol_m.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_vol_m, text='Volumen Música:').pack(side='left')
        self.slider_volumen_musica = ttk.Scale(f_vol_m, from_=0.0, to=1.0, value=VOLUMEN_MUSICA, command=self.cambiar_volumen_musica)
        self.slider_volumen_musica.pack(side='left', fill='x', expand=True, padx=10)
        frame_perm_musica = ttk.LabelFrame(self.tab_musica, text=' Permisos de Comandos por Rol ')
        frame_perm_musica.pack(fill='x', padx=10, pady=5)
        f_djs = ttk.Frame(frame_perm_musica)
        f_djs.pack(fill='x', padx=5, pady=2)
        ttk.Label(f_djs, text='Lista DJs (separados por coma):').pack(side='left')
        self.entry_djs = tk.Entry(f_djs, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 8), relief='flat')
        self.entry_djs.insert(0, config.get('lista_djs', ''))
        self.entry_djs.pack(side='left', fill='x', expand=True, padx=5)
        f_grid_hdr = ttk.Frame(frame_perm_musica)
        f_grid_hdr.pack(fill='x', padx=5, pady=2)
        ttk.Label(f_grid_hdr, text='Rol', width=12, font=(self.fuente_actual, 8, 'bold')).pack(side='left')
        for h in ['Play', 'Skip', 'Pause', 'Resume', 'Vol']:
            ttk.Label(f_grid_hdr, text=h, width=7, anchor='center', font=(self.fuente_actual, 8, 'bold')).pack(side='left', expand=True)
        f_row_sub = ttk.Frame(frame_perm_musica)
        f_row_sub.pack(fill='x', padx=5, pady=1)
        ttk.Label(f_row_sub, text='Suscriptores:', width=12).pack(side='left')
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_play).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_skip).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_pause).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_resume).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_sub, variable=self.perm_sub_vol).pack(side='left', expand=True)
        f_row_mod = ttk.Frame(frame_perm_musica)
        f_row_mod.pack(fill='x', padx=5, pady=1)
        ttk.Label(f_row_mod, text='Moderadores:', width=12).pack(side='left')
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_play).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_skip).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_pause).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_resume).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_mod, variable=self.perm_mod_vol).pack(side='left', expand=True)
        f_row_dj = ttk.Frame(frame_perm_musica)
        f_row_dj.pack(fill='x', padx=5, pady=1)
        ttk.Label(f_row_dj, text='DJs:', width=12).pack(side='left')
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_play).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_skip).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_pause).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_resume).pack(side='left', expand=True)
        ttk.Checkbutton(f_row_dj, variable=self.perm_dj_vol).pack(side='left', expand=True)
        frame_lista_musica = ttk.LabelFrame(self.tab_musica, text=' Lista de Espera Musical ')
        frame_lista_musica.pack(fill='both', expand=True, padx=10, pady=5)
        self.listbox_musica = tk.Listbox(frame_lista_musica, bg='#11111b', fg='#cdd6f4', selectbackground='#45475a', font=(self.fuente_actual, 9), relief='flat')
        self.listbox_musica.pack(side='left', fill='both', expand=True, padx=(8, 0), pady=8)
        scrollbar_musica = ttk.Scrollbar(frame_lista_musica, orient='vertical', command=self.listbox_musica.yview)
        scrollbar_musica.pack(side='right', fill='y', padx=(0, 8), pady=8)
        self.listbox_musica.config(yscrollcommand=scrollbar_musica.set)
        f_btn_mus = ttk.Frame(self.tab_musica)
        f_btn_mus.pack(fill='x', padx=10, pady=5)
        btn_up_song = tk.Button(f_btn_mus, text='⬆ Arriba', bg='#89b4fa', fg='#11111b', relief='flat', command=self.mover_cancion_arriba, font=(self.fuente_actual, 8, 'bold'))
        btn_up_song.pack(side='left', padx=2)
        btn_down_song = tk.Button(f_btn_mus, text='⬇ Abajo', bg='#89b4fa', fg='#11111b', relief='flat', command=self.mover_cancion_abajo, font=(self.fuente_actual, 8, 'bold'))
        btn_down_song.pack(side='left', padx=2)
        btn_del_song = tk.Button(f_btn_mus, text='Eliminar', bg='#f38ba8', fg='#11111b', relief='flat', command=self.eliminar_cancion_lista, font=(self.fuente_actual, 8, 'bold'))
        btn_del_song.pack(side='left', padx=2)
        btn_clear_queue = tk.Button(f_btn_mus, text='Vaciar Lista', bg='#fab387', fg='#11111b', relief='flat', command=self.vaciar_lista_musica, font=(self.fuente_actual, 8, 'bold'))
        btn_clear_queue.pack(side='right', padx=2)
        frame_cmd_cfg = ttk.LabelFrame(self.tab_musica, text=' Comandos del Chat Configurables ')
        frame_cmd_cfg.pack(fill='x', padx=10, pady=5)
        def _crear_campo_cmd(parent, label_text, default_val):
            f = ttk.Frame(parent)
            f.pack(fill='x', padx=5, pady=2)
            ttk.Label(f, text=label_text, width=15, anchor='w').pack(side='left')
            entry = tk.Entry(f, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 9), relief='flat')
            entry.insert(0, config.get(default_val, ''))
            entry.pack(side='left', fill='x', expand=True, padx=5)
            return entry
        self.entry_cmd_play = _crear_campo_cmd(frame_cmd_cfg, 'Play:', 'cmd_play')
        self.entry_cmd_skip = _crear_campo_cmd(frame_cmd_cfg, 'Skip:', 'cmd_skip')
        self.entry_cmd_pause = _crear_campo_cmd(frame_cmd_cfg, 'Pausar:', 'cmd_pause')
        self.entry_cmd_resume = _crear_campo_cmd(frame_cmd_cfg, 'Reanudar:', 'cmd_resume')
        self.entry_cmd_vol = _crear_campo_cmd(frame_cmd_cfg, 'Volumen:', 'cmd_volume')
        frame_audio_cfg = ttk.LabelFrame(self.tab_tts, text=' Parámetros de Síntesis de Voz ')
        frame_audio_cfg.pack(fill='x', padx=10, pady=5)
        f_vol = ttk.Frame(frame_audio_cfg)
        f_vol.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_vol, text='Volumen TTS/General:').pack(side='left')
        self.slider_volumen = ttk.Scale(f_vol, from_=0.0, to=1.0, value=VOLUMEN, command=self.cambiar_volumen)
        self.slider_volumen.pack(side='left', fill='x', expand=True, padx=10)
        f_voces = ttk.Frame(frame_audio_cfg)
        f_voces.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_voces, text='Voz Seleccionada:').pack(side='left')
        self.combo_voz = ttk.Combobox(f_voces, values=['es-MX-JorgeNeural', 'es-MX-DaliaNeural', 'es-ES-ElviraNeural', 'es-ES-AlvaroNeural', 'es-AR-TomasNeural', 'es-CL-LorenzoNeural'], state='readonly', width=22)
        self.combo_voz.set(VOZ_TTS)
        self.combo_voz.pack(side='left', padx=(5, 10))
        f_pitch_vel = ttk.Frame(frame_audio_cfg)
        f_pitch_vel.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_pitch_vel, text='Velocidad:').pack(side='left')
        self.combo_vel = ttk.Combobox(f_pitch_vel, values=['+0%', '+15%', '+30%', '+45%', '+60%'], state='readonly', width=8)
        self.combo_vel.set(VELOCIDAD_AUDIO)
        self.combo_vel.pack(side='left', padx=5)
        ttk.Label(f_pitch_vel, text='Tono (Pitch):').pack(side='left', padx=(15, 0))
        self.combo_tono = ttk.Combobox(f_pitch_vel, values=['-10Hz', '-5Hz', '+0Hz', '+5Hz', '+10Hz'], state='readonly', width=8)
        self.combo_tono.set(TONO_TTS)
        self.combo_tono.pack(side='left', padx=5)
        f_limite = ttk.Frame(frame_audio_cfg)
        f_limite.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_limite, text='Máximo Caracteres por Mensaje:').pack(side='left')
        self.entry_limite = tk.Entry(f_limite, bg='#11111b', fg='#cdd6f4', insertbackground='white', width=8, relief='flat')
        self.entry_limite.insert(0, str(config.get('limite_caracteres', 100)))
        self.entry_limite.pack(side='left', padx=10)
        f_botones_tts = ttk.Frame(self.tab_tts)
        f_botones_tts.pack(fill='x', padx=10, pady=10)
        self.btn_pausa = tk.Button(f_botones_tts, text='Pausar TTS', bg='#f9e2af', fg='#11111b', relief='flat', command=self.conmutar_pausa, font=(self.fuente_actual, 9, 'bold'))
        self.btn_pausa.pack(side='left', fill='x', expand=True, padx=2)
        btn_test = tk.Button(f_botones_tts, text='Probar Audio', bg='#89b4fa', fg='#11111b', relief='flat', command=self.probar_audio, font=(self.fuente_actual, 9, 'bold'))
        btn_test.pack(side='left', fill='x', expand=True, padx=2)
        btn_limpiar = tk.Button(f_botones_tts, text='Vaciar Cola', bg='#f38ba8', fg='#11111b', relief='flat', command=self.vaciar_cola, font=(self.fuente_actual, 9, 'bold'))
        btn_limpiar.pack(side='left', fill='x', expand=True, padx=2)
        frame_tipografia = ttk.LabelFrame(self.tab_filtros, text=' Personalización de Fuente (GUI) ')
        frame_tipografia.pack(fill='x', padx=10, pady=5)
        f_font = ttk.Frame(frame_tipografia)
        f_font.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_font, text='Tipografía del sistema:').pack(side='left')
        fuentes_disponibles = sorted(font.families())
        self.combo_fuente = ttk.Combobox(f_font, values=fuentes_disponibles, state='readonly', width=22)
        self.combo_fuente.set(self.fuente_actual if self.fuente_actual in fuentes_disponibles else fuentes_disponibles[0])
        self.combo_fuente.pack(side='left', padx=10)
        btn_aplicar_fuente = tk.Button(f_font, text='Aplicar Fuente', bg='#89b4fa', fg='#11111b', relief='flat', command=self.aplicar_nueva_fuente, font=(self.fuente_actual, 8, 'bold'))
        btn_aplicar_fuente.pack(side='left')
        frame_filtros = ttk.LabelFrame(self.tab_filtros, text=' Restricciones de Lectura ')
        frame_filtros.pack(fill='x', padx=10, pady=5)
        f_chk = ttk.Frame(frame_filtros)
        f_chk.pack(fill='x', padx=10, pady=5)
        ttk.Checkbutton(f_chk, text='Solo Subs', variable=self.restringir_subs).pack(side='left')
        ttk.Label(f_chk, text='Nivel Mín:').pack(side='left', padx=(10, 2))
        self.entry_nivel_sub = tk.Entry(f_chk, bg='#11111b', fg='#cdd6f4', insertbackground='white', width=4, relief='flat')
        self.entry_nivel_sub.insert(0, str(config.get('nivel_sub_minimo', 2)))
        self.entry_nivel_sub.pack(side='left', padx=(0, 15))
        ttk.Checkbutton(f_chk, text='Solo Mods', variable=self.restringir_mods).pack(side='left', expand=True)
        ttk.Checkbutton(f_chk, text='Solo Lista Blanca', variable=self.restringir_lista).pack(side='left', expand=True)
        f_lista = ttk.Frame(frame_filtros)
        f_lista.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_lista, text='Lista Blanca (separados por coma):').pack(anchor='w')
        self.entry_lista = tk.Entry(f_lista, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 9), relief='flat')
        self.entry_lista.insert(0, config.get('lista_blanca', ''))
        self.entry_lista.pack(fill='x', pady=3)
        frame_censura = ttk.LabelFrame(self.tab_filtros, text=' Filtro de Palabras Prohibidas ')
        frame_censura.pack(fill='x', padx=10, pady=5)
        f_cen = ttk.Frame(frame_censura)
        f_cen.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_cen, text='Palabras a omitir/censurar:').pack(anchor='w')
        self.entry_censura = tk.Entry(f_cen, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 9), relief='flat')
        self.entry_censura.insert(0, config.get('palabras_censuradas', ''))
        self.entry_censura.pack(fill='x', pady=3)
        frame_reemplazos = ttk.LabelFrame(self.tab_filtros, text=' Diccionario de Reemplazos ')
        frame_reemplazos.pack(fill='x', padx=10, pady=5)
        f_rep = ttk.Frame(frame_reemplazos)
        f_rep.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_rep, text='Reemplazar (Formato orig:nuevo):').pack(anchor='w')
        self.entry_reemplazos = tk.Entry(f_rep, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 9), relief='flat')
        self.entry_reemplazos.insert(0, config.get('reemplazos', ''))
        self.entry_reemplazos.pack(fill='x', pady=3)
        frame_alertas_audio = ttk.LabelFrame(self.tab_alertas, text=' Control de Sonidos MyInstants ')
        frame_alertas_audio.pack(fill='x', padx=10, pady=5)
        f_vol_alt = ttk.Frame(frame_alertas_audio)
        f_vol_alt.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_vol_alt, text='Volumen Alertas:').pack(side='left')
        self.slider_volumen_alertas = ttk.Scale(f_vol_alt, from_=0.0, to=1.0, value=VOLUMEN_ALERTAS)
        self.slider_volumen_alertas.pack(side='left', fill='x', expand=True, padx=10)
        f_reg = ttk.Frame(frame_alertas_audio)
        f_reg.pack(fill='x', padx=10, pady=5)
        ttk.Checkbutton(f_reg, text='Regalos:', variable=self.alerta_regalos).pack(side='left')
        self.entry_url_regalo = tk.Entry(f_reg, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 8), relief='flat')
        self.entry_url_regalo.insert(0, config.get('url_regalo', ''))
        self.entry_url_regalo.pack(side='left', fill='x', expand=True, padx=5)
        f_fol = ttk.Frame(frame_alertas_audio)
        f_fol.pack(fill='x', padx=10, pady=5)
        ttk.Checkbutton(f_fol, text='Follows:', variable=self.alerta_follows).pack(side='left')
        self.entry_url_follow = tk.Entry(f_fol, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 8), relief='flat')
        self.entry_url_follow.insert(0, config.get('url_follow', ''))
        self.entry_url_follow.pack(side='left', fill='x', expand=True, padx=5)
        frame_likes_gen = ttk.LabelFrame(self.tab_alertas, text=' Meta de Likes General ')
        frame_likes_gen.pack(fill='x', padx=10, pady=5)
        f_lik_gen_cfg = ttk.Frame(frame_likes_gen)
        f_lik_gen_cfg.pack(fill='x', padx=5, pady=3)
        ttk.Checkbutton(f_lik_gen_cfg, text='Activar', variable=self.alerta_likes_general).pack(side='left')
        ttk.Label(f_lik_gen_cfg, text='Cada:').pack(side='left', padx=(10, 2))
        self.entry_meta_likes_general = tk.Entry(f_lik_gen_cfg, bg='#11111b', fg='#cdd6f4', insertbackground='white', width=6, relief='flat')
        self.entry_meta_likes_general.insert(0, str(config.get('meta_likes_general', 100)))
        self.entry_meta_likes_general.pack(side='left', padx=(0, 10))
        ttk.Checkbutton(f_lik_gen_cfg, text='Repetir infinitamente', variable=self.repetir_likes_general).pack(side='left')
        f_lik_gen_url = ttk.Frame(frame_likes_gen)
        f_lik_gen_url.pack(fill='x', padx=5, pady=3)
        ttk.Label(f_lik_gen_url, text='Audio URL:').pack(side='left')
        self.entry_url_like_general = tk.Entry(f_lik_gen_url, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 8), relief='flat')
        self.entry_url_like_general.insert(0, config.get('url_like_general', ''))
        self.entry_url_like_general.pack(side='left', fill='x', expand=True, padx=5)
        frame_likes_per = ttk.LabelFrame(self.tab_alertas, text=' Meta de Likes por Persona ')
        frame_likes_per.pack(fill='x', padx=10, pady=5)
        f_lik_per_cfg = ttk.Frame(frame_likes_per)
        f_lik_per_cfg.pack(fill='x', padx=5, pady=3)
        ttk.Checkbutton(f_lik_per_cfg, text='Activar', variable=self.alerta_likes_persona).pack(side='left')
        ttk.Label(f_lik_per_cfg, text='Cada:').pack(side='left', padx=(10, 2))
        self.entry_meta_likes_persona = tk.Entry(f_lik_per_cfg, bg='#11111b', fg='#cdd6f4', insertbackground='white', width=6, relief='flat')
        self.entry_meta_likes_persona.insert(0, str(config.get('meta_likes_persona', 50)))
        self.entry_meta_likes_persona.pack(side='left', padx=(0, 10))
        ttk.Checkbutton(f_lik_per_cfg, text='Repetir por usuario', variable=self.repetir_likes_persona).pack(side='left')
        f_lik_per_url = ttk.Frame(frame_likes_per)
        f_lik_per_url.pack(fill='x', padx=5, pady=3)
        ttk.Label(f_lik_per_url, text='Audio URL:').pack(side='left')
        self.entry_url_like_persona = tk.Entry(f_lik_per_url, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 8), relief='flat')
        self.entry_url_like_persona.insert(0, config.get('url_like_persona', ''))
        self.entry_url_like_persona.pack(side='left', fill='x', expand=True, padx=5)
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
                    "target": 100,
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
        style.configure('TLabelframe.Label', font=(nueva_fuente, 9, 'bold'))
        style.configure('TLabel', font=(nueva_fuente, 9))
        style.configure('TCheckbutton', font=(nueva_fuente, 9))
        self.log_box.config(font=(nueva_fuente, 9))
        self.listbox_musica.config(font=(nueva_fuente, 9))
        self.lbl_now_playing.config(font=(nueva_fuente, 9, 'bold'))
        self.lbl_estado.config(font=(nueva_fuente, 10, 'bold'))
        self.lbl_tiempo_live.config(font=(nueva_fuente, 10, 'bold'))
        self.agregar_log(f'[GUI] Tipografía cambiada a: {nueva_fuente}')
    def cambiar_volumen_musica(self, val):
        volumen_real = float(val) * 0.25
        if canal_musica_ram:
            canal_musica_ram.set_volume(volumen_real)
    def alternar_pausa_musica(self):
        if self.musica_pausada:
            if canal_musica_ram:
                canal_musica_ram.unpause()
            self.musica_pausada = False
            self.agregar_log('[MÚSQUEDA] Música reanudada manualmente.')
        else:
            if canal_musica_ram and canal_musica_ram.get_busy() or cancion_actual:
                if canal_musica_ram:
                    canal_musica_ram.pause()
                self.musica_pausada = True
                self.agregar_log('[MÚSQUEDA] Música pausada manualmente.')
    def saltar_cancion_manual(self):
        self.musica_pausada = False
        if canal_musica_ram and canal_musica_ram.get_busy() or cancion_actual:
            if canal_musica_ram:
                canal_musica_ram.stop()
            VOTOS_SKIP.clear()
            self.agregar_log('[MÚSQUEDA] Canción saltada desde el Dashboard.')
        else:
            self.agregar_log('[MÚSQUEDA] No hay canción activa para saltar.')
    def obtener_lista_comandos(self, entry_widget):
        raw = entry_widget.get().strip().lower()
        return [c.strip() for c in raw.split(',') if c.strip()]
    def obtener_usuarios_djs(self):
        raw_text = self.entry_djs.get()
        return {u.strip().lower().replace('@', '') for u in raw_text.split(',') if u.strip()}
    def actualizar_lista_musica_ui(self):
        def _update():
            # ***<module>.PanelControl.actualizar_lista_musica_ui._update: Failure: Different control flow
            seleccion_previa = self.listbox_musica.curselection()
            self.listbox_musica.delete(0, tk.END)
            for idx, (query, usuario) in enumerate(cola_musica, start=1):
                self.listbox_musica.insert(tk.END, f'{idx}. {query} (por @{usuario})')
            if not seleccion_previa or seleccion_previa[0] < len(cola_musica):
                    self.listbox_musica.select_set(seleccion_previa[0])
        self.root.after(0, _update)
        broadcast_overlay_data()
    def actualizar_cancion_actual_ui(self, texto):
        self.root.after(0, lambda: self.lbl_now_playing.config(text=f'Sonando: {texto}'))
        broadcast_overlay_data()
    def mover_cancion_arriba(self):
        try:
            seleccion = self.listbox_musica.curselection()
            if seleccion:
                index = seleccion[0]
                if index > 0:
                    cola_musica[index], cola_musica[index - 1] = (cola_musica[index - 1], cola_musica[index])
                    self.actualizar_lista_musica_ui()
                    self.listbox_musica.select_set(index - 1)
        except Exception as e:
            self.agregar_log(f'[Error UI]: {e}')
    def mover_cancion_abajo(self):
        try:
            seleccion = self.listbox_musica.curselection()
            if seleccion:
                index = seleccion[0]
                if index < len(cola_musica) - 1:
                    cola_musica[index], cola_musica[index + 1] = (cola_musica[index + 1], cola_musica[index])
                    self.actualizar_lista_musica_ui()
                    self.listbox_musica.select_set(index + 1)
        except Exception as e:
            self.agregar_log(f'[Error UI]: {e}')
    def eliminar_cancion_lista(self):
        try:
            seleccion = self.listbox_musica.curselection()
            if seleccion:
                index = seleccion[0]
                del cola_musica[index]
                self.actualizar_lista_musica_ui()
                self.agregar_log(f'[MÚSQUEDA] Canción en índice {index + 1} eliminada de la cola.')
        except Exception as e:
            self.agregar_log(f'[Error UI]: {e}')
    def vaciar_lista_musica(self):
        cola_musica.clear()
        self.actualizar_lista_musica_ui()
        self.agregar_log('[MÚSQUEDA] Lista de espera musical vaciada.')
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
        return {u.strip().lower().replace('@', '') for u in raw_text.split(',') if u.strip()}
    def obtener_palabras_censuradas(self):
        raw_text = self.entry_censura.get()
        return [p.strip().lower() for p in raw_text.split(',') if p.strip()]
    def obtener_diccionario_reemplazos(self):
        raw_text = self.entry_reemplazos.get()
        diccionario = {}
        items = raw_text.split(',')
        for item in items:
            if ':' in item:
                clave, valor = item.split(':', 1)
                if clave.strip():
                    diccionario[clave.strip().lower()] = valor.strip()
        return diccionario
    def actualizar_monitoreo_ram(self):
        try:
            ram_bytes = self.proceso_actual.memory_info().rss
            ram_mb = ram_bytes / 1048576
            self.lbl_ram.config(text=f'RAM: {ram_mb:.1f} MB')
        except Exception:
            pass
        self.root.after(2000, self.actualizar_monitoreo_ram)
    def actualizar_cronometro_live(self):
        if self.conectado and self.tiempo_conexion_inicio:
            transcurrido = int(time.time() - self.tiempo_conexion_inicio)
            horas = transcurrido // 3600
            minutos = transcurrido % 3600 // 60
            segundos = transcurrido % 60
            str_tiempo = f'{horas:02d}:{minutos:02d}:{segundos:02d}'
            self.lbl_tiempo_live.config(text=f'Live activo: {str_tiempo}', fg='#89b4fa')
        else:
            self.lbl_tiempo_live.config(text='Live activo: 00:00:00', fg='#6c7086')
        self.root.after(1000, self.actualizar_cronometro_live)
    def actualizar_metricas_ui(self):
        self.root.after(0, lambda: self.lbl_stat_chat.config(text=f"Leídos: {STATS['comentarios']}"))
        self.root.after(0, lambda: self.lbl_stat_gifts.config(text=f"Regalos: {STATS['regalos']}"))
        self.root.after(0, lambda: self.lbl_stat_follows.config(text=f"Follows: {STATS['follows']}"))
        self.root.after(0, lambda: self.lbl_stat_likes.config(text=f"Likes: {STATS['likes_totales']}"))
    def cambiar_volumen(self, val):
        return
    def conmutar_pausa(self):
        self.audio_pausado = not self.audio_pausado
        if self.audio_pausado:
            self.btn_pausa.config(text='Reanudar TTS', bg='#a6e3a1')
            self.agregar_log('[PAUSA] Audio Pausado')
        else:
            self.btn_pausa.config(text='Pausar TTS', bg='#f9e2af')
            self.agregar_log('[PLAY] Audio Reanudado')
    def probar_audio(self):
        enviar_a_voz('Prueba de sonido en proceso', forzar=True)
        url = self.entry_url_like_general.get().strip()
        reproducir_sonido_url(url)
    def vaciar_cola(self):
        with cola_mensajes.mutex:
            cola_mensajes.queue.clear()
        if canal_musica_ram:
            canal_musica_ram.stop()
        self.agregar_log('[INFO] Cola de mensajes limpiada')
        self.root.after(0, lambda: self.lbl_cola.config(text='En cola: 0/50'))
    def actualizar_estado(self, texto, color):
        self.root.after(0, lambda: self.lbl_estado.config(text=f'Estado: {texto}', fg=color))
    def agregar_log(self, mensaje):
        def _write():
            self.log_box.insert(tk.END, f'{mensaje}\n')
            self.log_box.see(tk.END)
            self.lbl_cola.config(text=f'En cola: {cola_mensajes.qsize()}/50')
        self.root.after(0, _write)
    def limpiar_cuadro_log(self):
        self.log_box.delete('1.0', tk.END)
    def exportar_log(self):
        # ***<module>.PanelControl.exportar_log: Failure: Different control flow
        contenido = self.log_box.get('1.0', tk.END).strip()
        if not contenido:
            self.agregar_log('[INFO] No hay registros.')
            return
        else:
            filepath = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Archivos de texto', '*.txt'), ('Todos los archivos', '*.*')], title='Guardar Registro de Chat')
            if filepath:
                pass
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(contenido)
            self.agregar_log(f'[INFO] Registro guardado en: {filepath}')
        except Exception as e:
            self.agregar_log(f'[Error Guardado]: {e}')
    def alternar_conexion(self):
        if not self.conectado:
            usuario = self.entry_user.get().strip()
            if not usuario:
                self.agregar_log('[ALERTA] Ingresa un usuario válido')
                return
            else:
                if not usuario.startswith('@'):
                    usuario = f'@{usuario}'
                    self.entry_user.delete(0, tk.END)
                    self.entry_user.insert(0, usuario)
                self.btn_conectar.config(text='Desconectar', bg='#f38ba8')
                self.entry_user.config(state='disabled')
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
            self.btn_conectar.config(text='Conectar Live', bg='#a6e3a1')
            self.entry_user.config(state='normal')
            self.actualizar_estado('Desconectado', '#f38ba8')
            self.agregar_log('[INFO] Conexión finalizada')
    def al_cerrar(self):
        try:
            limite_val = int(self.entry_limite.get())
        except ValueError:
            limite_val = 100
        try:
            nivel_sub_minimo = int(self.entry_nivel_sub.get())
        except ValueError:
            nivel_sub_minimo = 1

        datos_guardar = {
            'usuario': self.entry_user.get().strip(),
            'volumen': float(self.slider_volumen.get()),
            'volumen_alertas': float(self.slider_volumen_alertas.get()),
            'volumen_musica': float(self.slider_volumen_musica.get()),
            'voz': self.combo_voz.get(),
            'velocidad': self.combo_vel.get(),
            'tono': self.combo_tono.get(),
            'limite_caracteres': limite_val,
            'palabras_censuradas': self.entry_censura.get(),
            'reemplazos': self.entry_reemplazos.get(),
            'restringir_subs': self.restringir_subs.get(),
            'nivel_sub_minimo': nivel_sub_minimo,
            'restringir_mods': self.restringir_mods.get(),
            'restringir_lista': self.restringir_lista.get(),
            'lista_blanca': self.entry_lista.get(),
            'lista_djs': self.entry_djs.get(),
            'cmd_play': self.entry_cmd_play.get(),
            'cmd_skip': self.entry_cmd_skip.get(),
            'cmd_pause': self.entry_cmd_pause.get(),
            'cmd_resume': self.entry_cmd_resume.get(),
            'cmd_volume': self.entry_cmd_vol.get(),
            'alerta_regalos': self.alerta_regalos.get(),
            'alerta_follows': self.alerta_follows.get(),
            'alerta_likes_general': self.alerta_likes_general.get(),
            'meta_likes_general': self.obtener_meta_likes_general(),
            'repetir_likes_general': self.repetir_likes_general.get(),
            'alerta_likes_persona': self.alerta_likes_persona.get(),
            'meta_likes_persona': self.obtener_meta_likes_persona(),
            'repetir_likes_persona': self.repetir_likes_persona.get(),
            'url_regalo': self.entry_url_regalo.get(),
            'url_follow': self.entry_url_follow.get(),
            'url_like_general': self.entry_url_like_general.get(),
            'url_like_persona': self.entry_url_like_persona.get(),
            'fuente_interfaz': self.fuente_actual,
        }
        for nombre in (
            'perm_sub_play', 'perm_sub_skip', 'perm_sub_pause', 'perm_sub_resume', 'perm_sub_vol',
            'perm_mod_play', 'perm_mod_skip', 'perm_mod_pause', 'perm_mod_resume', 'perm_mod_vol',
            'perm_dj_play', 'perm_dj_skip', 'perm_dj_pause', 'perm_dj_resume', 'perm_dj_vol',
        ):
            datos_guardar[nombre] = getattr(self, nombre).get()

        designs_to_save = {}
        for endpoint, cfg in getattr(self, 'widget_configs', {}).items():
            designs_to_save[endpoint] = {
                'title': cfg['title_entry'].get().strip(),
                'design': cfg['design_combo'].get().strip(),
                'max': cfg['max_entry'].get().strip(),
                'custom': dict(cfg.get('custom', {}) or {})
            }
        datos_guardar['widget_designs'] = designs_to_save

        guardar_configuracion(datos_guardar)
        self.root.destroy()

gui = PanelControl()
def extraer_o_limpiar_emojis(texto, max_emojis):
    # ***<module>.extraer_o_limpiar_emojis: Failure: Different control flow
    texto_normalizado = unicodedata.normalize('NFKD', texto)
    texto_base = ''.join([c for c in texto_normalizado if not unicodedata.combining(c)])
    conteo = 0
    resultado = []
    for caracter in texto_base:
        codepoint = ord(caracter)
        es_emoji = 128512 <= codepoint <= 128591 or 127744 <= codepoint <= 128511 or (128640 <= codepoint <= 128767) or (129280 <= codepoint <= 129535) or (129648 <= codepoint <= 129791)
        if es_emoji:
            if conteo < max_emojis:
                resultado.append(caracter)
                conteo += 1
        else:
            resultado.append(caracter)
    texto_filtrado = ''.join(resultado)
    return re.sub('[^\\w\\s\\d@._\\-\\U00010000-\\U0010FFFF]', '', texto_filtrado).strip()
def normalizar_texto(texto):
    return extraer_o_limpiar_emojis(texto, max_emojis=0)
def aplicar_diccionario_reemplazos(texto, diccionario):
    for original, reemplazo in diccionario.items():
        patron = re.compile('\\b' + re.escape(original) + '\\b', re.IGNORECASE)
        texto = patron.sub(reemplazo, texto)
    return texto
async def generar_audio_bytes(texto, voz, velocidad, tono):
    # irreducible cflow, using cdg fallback
    communicate = edge_tts.Communicate(texto, voz, rate=velocidad, pitch=tono)
    data = bytearray()
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            data.extend(chunk['data'])
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
                audio_buffer = loop.run_until_complete(
                    generar_audio_bytes(texto, voz_actual, vel_actual, tono_actual)
                )
                sonido = pygame.mixer.Sound(audio_buffer)
                canal_tts = pygame.mixer.find_channel(True)
                if canal_tts:
                    volumen_tts_real = float(gui.slider_volumen.get()) * 0.6
                    canal_tts.set_volume(volumen_tts_real)
                    canal_tts.play(sonido)
                    while canal_tts.get_busy():
                        time.sleep(0.05)
                audio_buffer.close()
        except Exception as e:
            gui.agregar_log(f'[Error Audio TTS]: {e}')
        finally:
            cola_mensajes.task_done()
            gui.root.after(
                0,
                lambda: gui.lbl_cola.config(text=f'En cola: {cola_mensajes.qsize()}/50')
            )

threading.Thread(target=procesar_audio, daemon=True).start()
def enviar_a_voz(mensaje, forzar=False):
    if not gui.conectado and (not forzar):
            return
    try:
        cola_mensajes.put(mensaje, timeout=0.2)
        gui.agregar_log(f'[AUDIO] {mensaje}')
    except queue.Full:
        gui.agregar_log('[ALERTA] Cola llena')
def es_suscriptor_nivel_minimo(user, nivel_minimo: int) -> bool:
    is_sub = getattr(user, 'is_subscriber', False)
    badges = getattr(user, 'badges', []) or getattr(user, 'badge_list', []) or []
    for badge in badges:
        badge_str = str(badge).lower()
        if any((term in badge_str for term in ['subscriber', 'sub', 'sub_grade', 'fans', 'member'])):
            is_sub = True
            level = 0
            if isinstance(badge, dict):
                level = badge.get('level') or badge.get('sub_level') or 0
            else:
                priv_log = getattr(badge, 'privilege_log_extra', None)
                if priv_log:
                    level = getattr(priv_log, 'level', 0)
                else:
                    level = getattr(badge, 'level', getattr(badge, 'sub_level', 0))
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
    if getattr(user, 'is_moderator', False) or getattr(user, 'is_admin', False):
        return True
    else:
        user_str = str(user).lower()
        if 'moderator' in user_str or 'admin' in user_str:
            return True
        else:
            badges = getattr(user, 'badges', []) or getattr(user, 'badge_list', []) or []
            for badge in badges:
                badge_str = str(badge).lower()
                if 'moderator' in badge_str or 'admin' in badge_str:
                    return True
            return False
def tiene_permiso_comando(user, tipo_comando):
    username = str(getattr(user, 'unique_id', getattr(user, 'unique_id_str', ''))).lower()
    es_sub = es_suscriptor_nivel_minimo(user, gui.obtener_nivel_minimo_sub())
    es_mod = es_moderador(user)
    es_dj = username in gui.obtener_usuarios_djs()
    if es_dj and getattr(gui, f'perm_dj_{tipo_comando}').get():
            return True
    if es_mod and getattr(gui, f'perm_mod_{tipo_comando}').get():
            return True
    if es_sub and getattr(gui, f'perm_sub_{tipo_comando}').get():
            return True
    return False
def procesar_comandos_musica(comentario, username, user_obj):
    global ULTIMO_SKIP_TIEMPO
    partes = comentario.split(' ', 1)
    comando = partes[0].lower()
    arg = partes[1].strip() if len(partes) > 1 else ''
    nombre_user = normalizar_texto(username) or 'Usuario'
    user_id_raw = str(getattr(user_obj, 'unique_id', getattr(user_obj, 'unique_id_str', username))).lower()
    cmds_play = gui.obtener_lista_comandos(gui.entry_cmd_play)
    cmds_skip = gui.obtener_lista_comandos(gui.entry_cmd_skip)
    cmds_pause = gui.obtener_lista_comandos(gui.entry_cmd_pause)
    cmds_resume = gui.obtener_lista_comandos(gui.entry_cmd_resume)
    cmds_vol = gui.obtener_lista_comandos(gui.entry_cmd_vol)
    if comando in cmds_play:
        if not tiene_permiso_comando(user_obj, 'play'):
            gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} sin permisos para usar !play')
            return True
        else:
            if not arg:
                return True
            else:
                arg_normalizado = arg.strip().lower()
                if cancion_actual and arg_normalizado in cancion_actual.lower():
                    gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} intentó añadir una canción que ya se está reproduciendo.')
                    return True
                else:
                    ya_en_cola = any((q.strip().lower() == arg_normalizado for q, _ in cola_musica))
                    if ya_en_cola:
                        gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} la canción \'{arg}\' ya se encuentra en la cola.')
                        return True
                    else:
                        cola_musica.append((arg, nombre_user))
                        gui.actualizar_lista_musica_ui()
                        gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} añadió a la cola: {arg}')
                        return True
    else:
        if comando in cmds_skip:
            if not tiene_permiso_comando(user_obj, 'skip'):
                gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} sin permisos para usar !skip')
                return True
            else:
                tiempo_actual = time.time()
                if tiempo_actual - ULTIMO_SKIP_TIEMPO < COOLDOWN_SKIP_SEGUNDOS:
                    gui.agregar_log('[MÚSQUEDA] Espera unos segundos antes de pedir otro !skip.')
                    return True
                else:
                    esta_ocupado = canal_musica_ram and canal_musica_ram.get_busy()
                    if not esta_ocupado and (not cancion_actual):
                        gui.agregar_log('[MÚSQUEDA] No hay canción en reproducción para saltar.')
                        return True
                    else:
                        es_mod_o_dj = es_moderador(user_obj) or user_id_raw in gui.obtener_usuarios_djs()
                        if es_mod_o_dj:
                            gui.musica_pausada = False
                            if canal_musica_ram:
                                canal_musica_ram.stop()
                            VOTOS_SKIP.clear()
                            ULTIMO_SKIP_TIEMPO = tiempo_actual
                            gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} (Mod/DJ) saltó la canción.')
                            return True
                        else:
                            if user_id_raw in VOTOS_SKIP:
                                gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} ya votó para saltar esta canción.')
                                return True
                            else:
                                VOTOS_SKIP.add(user_id_raw)
                                conteo_votos = len(VOTOS_SKIP)
                                gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} votó !skip ({conteo_votos}/{UMBRAL_VOTOS_SKIP})')
                                if conteo_votos >= UMBRAL_VOTOS_SKIP:
                                    gui.musica_pausada = False
                                    if canal_musica_ram:
                                        canal_musica_ram.stop()
                                    VOTOS_SKIP.clear()
                                    ULTIMO_SKIP_TIEMPO = tiempo_actual
                                    gui.agregar_log('[MÚSQUEDA] ¡Meta de votos alcanzada! Canción saltada.')
                                return True
        else:
            if comando in cmds_pause:
                if not tiene_permiso_comando(user_obj, 'pause'):
                    gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} sin permisos para usar !pause')
                    return True
                else:
                    if canal_musica_ram:
                        canal_musica_ram.pause()
                    gui.musica_pausada = True
                    gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} pausó la música')
                    return True
            else:
                if comando in cmds_resume:
                    if not tiene_permiso_comando(user_obj, 'resume'):
                        gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} sin permisos para usar !resume')
                        return True
                    else:
                        if canal_musica_ram:
                            canal_musica_ram.unpause()
                        gui.musica_pausada = False
                        gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} reanudó la música')
                        return True
                else:
                    if comando in cmds_vol:
                        if not tiene_permiso_comando(user_obj, 'vol'):
                            gui.agregar_log(f'[MÚSQUEDA] @{nombre_user} sin permisos para cambiar volumen')
                            return True
                        else:
                            try:
                                val = float(arg) / 100.0 if float(arg) > 1.0 else float(arg)
                                val = max(0.0, min(1.0, val))
                                gui.slider_volumen_musica.set(val)
                                if canal_musica_ram:
                                    canal_musica_ram.set_volume(val * 0.25)
                                gui.agregar_log(f'[MÚSQUEDA] Volumen cambiado a {int(val * 100)}%')
                                return True
                            except ValueError:
                                return True
                    else:
                        return False
def iniciar_tiktok(unique_id):
    try:
        gui.actualizar_estado(f'Conectando a {unique_id}...', '#f9e2af')
        gui.client_tiktok = TikTokLiveClient(unique_id=unique_id)
        @gui.client_tiktok.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            global CONTADOR_LIKES_GENERAL
            global TIEMPO_INICIO
            gui.conectado = True
            gui.tiempo_conexion_inicio = time.time()
            TIEMPO_INICIO = time.time()
            CONTADOR_LIKES_GENERAL = 0
            LIKES_POR_USUARIO.clear()
            HISTORIAL_RECIENTE.clear()
            VOTOS_SKIP.clear()
            gui.actualizar_estado(f'Conectado a @{event.unique_id}', '#a6e3a1')
            gui.agregar_log(f'[SISTEMA] Conectado exitosamente al Live de {event.unique_id}')
        @gui.client_tiktok.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            # ***<module>.iniciar_tiktok.on_comment: Failure: Different control flow
            if not gui.conectado:
                return
            else:
                user = event.user
                username = str(getattr(user, 'unique_id', getattr(user, 'unique_id_str', ''))).lower()
                nickname = str(getattr(user, 'nickname', username))
                comentario = event.comment.strip()
                if time.time() - TIEMPO_INICIO < 2:
                    return
                else:
                    if comentario.startswith('!'):
                        if procesar_comandos_musica(comentario, nickname or username, user):
                            return
                    censuradas = gui.obtener_palabras_censuradas()
                    for palabra in censuradas:
                        if palabra in comentario.lower():
                            gui.agregar_log(f'[CENSURADO] Comentario de @{normalizar_texto(username)} omitido.')
                            return
                    modo_sub = bool(gui.restringir_subs.get())
                    modo_mod = bool(gui.restringir_mods.get())
                    modo_lista = bool(gui.restringir_lista.get())
                    hay_restricciones = modo_sub or modo_mod or modo_lista
                    nivel_minimo = gui.obtener_nivel_minimo_sub()
                    es_sub = es_suscriptor_nivel_minimo(user, nivel_minimo)
                    es_mod = es_moderador(user)
                    esta_en_lista = username in gui.obtener_usuarios_lista_blanca()
                    permitido = not hay_restricciones or (modo_sub and es_sub) or (modo_mod and es_mod) or (modo_lista and esta_en_lista)
                    if permitido:
                        id_mensaje = f'{username}:{comentario}'
                        if id_mensaje in HISTORIAL_RECIENTE:
                            return
                        else:
                            HISTORIAL_RECIENTE.append(id_mensaje)
                            nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or 'Usuario'
                            try:
                                max_chars = int(gui.entry_limite.get())
                            except ValueError:
                                max_chars = 100
                            comentario_recortado = comentario[:max_chars]
                            dicc_reemplazos = gui.obtener_diccionario_reemplazos()
                            comentario_procesado = aplicar_diccionario_reemplazos(comentario_recortado, dicc_reemplazos)
                            comentario_normalizado = extraer_o_limpiar_emojis(comentario_procesado, max_emojis=3)
                            STATS['comentarios'] += 1
                            gui.actualizar_metricas_ui()
                            enviar_a_voz(f'{nombre_limpio} dice: {comentario_normalizado}')
        @gui.client_tiktok.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            global ULTIMO_REGALO, ULTIMA_ACCION
            if not gui.conectado:
                return
            else:
                es_combo_activo = getattr(event, 'repeat_count', 1) > 1 and (not getattr(event, 'repeat_end', True))
                if es_combo_activo:
                    return
                else:
                    nickname = getattr(event.user, 'nickname', 'Alguien')
                    nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or 'Usuario'
                    regalo = getattr(event.gift, 'name', 'un regalo')
                    cantidad = getattr(event, 'repeat_count', 1) or getattr(event.gift, 'count', 1)
                    STATS['regalos'] += cantidad
                    ULTIMO_REGALO = {'user': nombre_limpio, 'gift': regalo, 'count': cantidad}
                    ULTIMA_ACCION = {
                        'id': f'gift-{time.time_ns()}',
                        'type': 'gift',
                        'name': nombre_limpio,
                        'avatar': '',
                        'message': f'🎁 {nombre_limpio} envió x{cantidad} {regalo}',
                        'icon': '🎁',
                        'expires_at': time.time() + 5
                    }
                    gui.actualizar_metricas_ui()
                    broadcast_overlay_data()
                    gui.agregar_log(f'[REGALO] {nombre_limpio} envió x{cantidad} {regalo}')
                    if gui.alerta_regalos.get():
                        url = gui.entry_url_regalo.get().strip()
                        if url:
                            reproducir_sonido_url(url)
                        if cantidad > 1:
                            enviar_a_voz(f'¡Gracias {nombre_limpio} por enviar {cantidad} {regalo}s!')
                        else:
                            enviar_a_voz(f'¡Gracias {nombre_limpio} por enviar {regalo}!')
        @gui.client_tiktok.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            global ULTIMO_SEGUIDOR, ULTIMA_ACCION
            if not gui.conectado:
                return
            else:
                nickname = getattr(event.user, 'nickname', 'Alguien')
                nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or 'Usuario'
                STATS['follows'] += 1
                ULTIMO_SEGUIDOR = nombre_limpio
                ULTIMA_ACCION = {
                    'id': f'follow-{time.time_ns()}',
                    'type': 'follow',
                    'name': nombre_limpio,
                    'avatar': '',
                    'message': f'💙 ¡Gracias {nombre_limpio} por seguir!',
                    'icon': '💙',
                    'expires_at': time.time() + 5
                }
                gui.actualizar_metricas_ui()
                broadcast_overlay_data()
                gui.agregar_log(f'[FOLLOW] {nombre_limpio} te ha seguido')
                if gui.alerta_follows.get():
                    url = gui.entry_url_follow.get().strip()
                    if url:
                        reproducir_sonido_url(url)
        @gui.client_tiktok.on(LikeEvent)
        async def on_like(event: LikeEvent):
            global CONTADOR_LIKES_GENERAL, ULTIMA_ACCION, ULTIMO_LIKE_META
            if not gui.conectado:
                return
            else:
                user = event.user
                username = str(getattr(user, 'unique_id', getattr(user, 'unique_id_str', 'anonimo'))).lower()
                likes_recibidos = getattr(event, 'likes', None) or getattr(event, 'count', None) or getattr(event, 'label', 1)
                try:
                    likes_recibidos = int(likes_recibidos)
                except (ValueError, TypeError):
                    likes_recibidos = 1
                STATS['likes_totales'] += likes_recibidos
                nickname = getattr(user, 'nickname', username)
                nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or normalizar_texto(username) or 'Usuario'
                LIKES_POR_USUARIO[username] += likes_recibidos
                gui.actualizar_metricas_ui()
                ULTIMA_ACCION = {
                    'id': f'like-{time.time_ns()}',
                    'type': 'like',
                    'name': nombre_limpio,
                    'avatar': '',
                    'message': f'❤️ {nombre_limpio} envió {likes_recibidos} like' + ('s' if likes_recibidos != 1 else ''),
                    'icon': '❤️',
                    'likes_count': likes_recibidos,
                    'expires_at': time.time() + 5
                }
                if gui.alerta_likes_general.get():
                    meta_general = gui.obtener_meta_likes_general()
                    CONTADOR_LIKES_GENERAL += likes_recibidos
                    if CONTADOR_LIKES_GENERAL >= meta_general:
                        gui.agregar_log(f'[LIKES GENERAL] Meta alcanzada: {meta_general} likes!')
                        url_gen = gui.entry_url_like_general.get().strip()
                        if url_gen:
                            reproducir_sonido_url(url_gen)
                        if gui.repetir_likes_general.get():
                            CONTADOR_LIKES_GENERAL %= meta_general
                        else:
                            gui.alerta_likes_general.set(False)
                if gui.alerta_likes_persona.get():
                    meta_persona = gui.obtener_meta_likes_persona()
                    if LIKES_POR_USUARIO[username] >= meta_persona:
                        gui.agregar_log(f'[LIKES PERSONA] @{normalizar_texto(username)} alcanzó {meta_persona} likes')
                        url_per = gui.entry_url_like_persona.get().strip()
                        if url_per:
                            reproducir_sonido_url(url_per)
                        if gui.repetir_likes_persona.get():
                            LIKES_POR_USUARIO[username] %= meta_persona
                        else:
                            LIKES_POR_USUARIO[username] = 0
                ULTIMO_LIKE_META = {
                    'name': nombre_limpio,
                    'progress': LIKES_POR_USUARIO[username] % max(gui.obtener_meta_likes_persona(), 1),
                    'total': LIKES_POR_USUARIO[username],
                    'target': gui.obtener_meta_likes_persona()
                }
                broadcast_overlay_data()
        gui.client_tiktok.run()
    except Exception as e:
        gui.conectado = False
        gui.tiempo_conexion_inicio = None
        gui.actualizar_estado('Error de Conexión', '#f38ba8')
        gui.agregar_log(f'[Error TikTok]: {e}')
        gui.root.after(0, lambda: gui.btn_conectar.config(text='Conectar Live', bg='#a6e3a1'))
        gui.root.after(0, lambda: gui.entry_user.config(state='normal'))
gui.root.mainloop()