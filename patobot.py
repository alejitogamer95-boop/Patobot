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
import webbrowser
import secrets
import base64
import hashlib
from collections import deque, defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, font
import pygame
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, FollowEvent, LikeEvent
import edge_tts
import psutil
import yt_dlp
from flask import Flask, render_template_string, Response, request

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

threading.Thread(target=run_flask_server, daemon=True).start()

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
canal_musica_ram = None
SPOTIFY_CURRENT_REQUEST = None
CANCION_ACTUAL_WIDGET = {"title":"", "artist":"", "user":"", "duration":0, "started_at":0, "cover":"", "spotify_url":"", "paused":False, "progress_ms":0}

SPOTIFY_AUTH_BASE = "https://accounts.spotify.com"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/spotify/callback"
SPOTIFY_SCOPES = "user-read-playback-state user-read-currently-playing user-modify-playback-state"

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

        # Tab Música
        # Spotify queda integrado sin mostrar credenciales ni "OAuth / Web API" al usuario.
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
        frame_busqueda_musica = ttk.LabelFrame(self.tab_musica, text=" Buscar canción ")
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

        frame_perm_musica = ttk.LabelFrame(self.tab_musica, text=" Permisos de Comandos por Rol ")
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
                self.agregar_log(f"[MÚSQUEDA] Canción en índice {index+1} eliminada de la cola.")
        except Exception as e:
            self.agregar_log(f"[Error UI]: {e}")

    def vaciar_lista_musica(self):
        cola_musica.clear()
        self.actualizar_lista_musica_ui()
        self.agregar_log("[MÚSQUEDA] Lista de espera musical vaciada.")

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
    global cancion_actual, VOTOS_SKIP, ULTIMO_SKIP_TIEMPO, canal_musica_ram, SPOTIFY_CURRENT_REQUEST
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

        ya_en_cola = any(x.get("query", "").strip().lower() == arg_normalizado for x in cola_musica)
        if ya_en_cola:
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} la canción '{arg}' ya se encuentra en la cola.")
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
            SPOTIFY_CURRENT_REQUEST = None
            if cola_musica:
                spotify_reproducir_siguiente()
            else:
                spotify.next()
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
            SPOTIFY_CURRENT_REQUEST = None
            if cola_musica:
                spotify_reproducir_siguiente()
            else:
                spotify.next()
            VOTOS_SKIP.clear()
            ULTIMO_SKIP_TIEMPO = tiempo_actual
            gui.agregar_log("[MÚSQUEDA] ¡Meta de votos alcanzada! Canción saltada.")
            
        return True
    elif comando in cmds_pause:
        if not tiene_permiso_comando(user_obj, "pause"):
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} sin permisos para usar !pause")
            return True
        spotify.pause()
        gui.musica_pausada = True
        gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} pausó la música")
        return True
    elif comando in cmds_resume:
        if not tiene_permiso_comando(user_obj, "resume"):
            gui.agregar_log(f"[MÚSQUEDA] @{nombre_user} sin permisos para usar !resume")
            return True
        spotify.resume()
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
            spotify.volume(val * 100)
            gui.agregar_log(f"[MÚSQUEDA] Volumen cambiado a {int(val*100)}%")
        except ValueError:
            pass
        return True

    return False

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

try:
    gui.root.after(1000, gui.actualizar_dispositivos_spotify)
except Exception:
    pass

if __name__ == "__main__":
    gui.root.mainloop()
