# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'patobot.py'
# Bytecode version: 3.10.b1 (3439)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

global CONTADOR_LIKES_GENERAL
global TIEMPO_INICIO
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
import colorsys
import urllib.request
import urllib.parse
import urllib.error
from collections import deque, defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, font
from flask import Flask, render_template_string, Response, request
import pygame
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, FollowEvent, LikeEvent, RoomUserSeqEvent
try:
    from TikTokLive.events import EmoteChatEvent
except ImportError:
    EmoteChatEvent = None
import edge_tts
import psutil
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
                        const avatarEl = document.getElementById(`avatar-${index}`);
                        avatarEl.onerror = () => {
                            avatarEl.onerror = null;
                            avatarEl.src = 'https://www.tiktok.com/favicon.ico';
                        };
                        avatarEl.src = item.avatar || 'https://www.tiktok.com/favicon.ico';
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
            } else if (widgetType === "topdonator") {
                const items = (data.topdonators || []).slice(0, maxUsers);
                if (content.children.length !== items.length) {
                    content.innerHTML = "";
                    items.forEach((item, index) => {
                        content.innerHTML += `
                        <div class="toplikes-card" id="donor-card-${index}">
                            <span class="rank-number" id="donor-rank-num-${index}"></span>
                            <span class="rank-badge" id="donor-rank-badge-${index}"></span>
                            <div class="avatar-box">
                                <div id="donor-crown-${index}"></div>
                                <img class="avatar-img" id="donor-avatar-${index}" src="">
                                <div class="frame" id="donor-frame-${index}"></div>
                            </div>
                            <div class="user-info">
                                <span class="user-name" id="donor-name-${index}"></span>
                                <span class="user-score"><span class="heart-icon">🪙</span> <span id="donor-score-${index}"></span></span>
                            </div>
                        </div>`;
                    });
                }
                items.forEach((item, index) => {
                    document.getElementById(`donor-rank-num-${index}`).innerText = index + 1;
                    document.getElementById(`donor-rank-badge-${index}`).innerText =
                        index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '⭐';
                    document.getElementById(`donor-card-${index}`).className =
                        `toplikes-card ${index === 0 ? 'top-one' : ''}`;
                    const frameClass = index === 0 ? "frame-gold" :
                        index === 1 ? "frame-silver" :
                        index === 2 ? "frame-bronze" : "frame-default";
                    document.getElementById(`donor-frame-${index}`).className = `frame ${frameClass}`;
                    document.getElementById(`donor-crown-${index}`).innerHTML =
                        index === 0 ? `<div class="crown">👑</div>` : "";
                    const avatarEl = document.getElementById(`donor-avatar-${index}`);
                    avatarEl.onerror = () => {
                        avatarEl.onerror = null;
                        avatarEl.src = 'https://www.tiktok.com/favicon.ico';
                    };
                    avatarEl.src = item.avatar || 'https://www.tiktok.com/favicon.ico';
                    document.getElementById(`donor-name-${index}`).innerText = item.name || "Usuario";
                    document.getElementById(`donor-score-${index}`).innerText =
                        Number(item.score || 0).toLocaleString('es-ES');
                });
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
    if (item.type === "like" && item.total_likes != null) {
        messageEl.textContent = `❤️ ${item.name || "Usuario"} lleva ${Number(item.total_likes).toLocaleString("es-ES")} likes en este Live`;
    } else {
        messageEl.textContent = item.message || "¡Gracias por apoyar el Live!";
    }
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
@app.route("/widget/topdonator")
def widget_topdonator():
    return render_custom_widget("topdonator", "Top Donadores")
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

def obtener_avatar_usuario(user):
    """Obtiene la URL de la foto de perfil desde distintos modelos/versiones de TikTokLive."""
    if user is None:
        return ""

    # Atributos directos que algunas versiones exponen.
    for attr in (
        "avatar_url", "avatar_thumb_url", "avatar_medium_url",
        "avatar_larger_url", "profile_picture_url", "profile_pic_url"
    ):
        try:
            value = getattr(user, attr, None)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
        except Exception:
            pass

    # Objetos de imagen de TikTokLive suelen contener url_list.
    for attr in ("avatar_thumb", "avatar_medium", "avatar_larger", "avatar"):
        try:
            obj = getattr(user, attr, None)
            if obj is None:
                continue

            urls = getattr(obj, "url_list", None)
            if urls:
                if isinstance(urls, (list, tuple)):
                    for url in urls:
                        if isinstance(url, str) and url.startswith(("http://", "https://")):
                            return url
                elif isinstance(urls, str) and urls.startswith(("http://", "https://")):
                    return urls

            # Por si la biblioteca devuelve directamente una URL.
            if isinstance(obj, str) and obj.startswith(("http://", "https://")):
                return obj
        except Exception:
            pass

    # Último intento: revisar diccionarios/objetos internos comunes.
    try:
        data = getattr(user, "__dict__", {}) or {}
        for key in ("avatar_url", "avatar_thumb_url", "avatar_medium_url",
                    "avatar_larger_url", "profile_picture_url", "profile_pic_url"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
        for key in ("avatar_thumb", "avatar_medium", "avatar_larger", "avatar"):
            obj = data.get(key)
            if isinstance(obj, dict):
                urls = obj.get("url_list") or obj.get("urlList")
                if isinstance(urls, (list, tuple)):
                    for url in urls:
                        if isinstance(url, str) and url.startswith(("http://", "https://")):
                            return url
    except Exception:
        pass

    return ""


def obtener_nombre_usuario(user):
    """Devuelve el nombre visible de TikTok (nickname), no el @username/unique_id."""
    if user is None:
        return 'Usuario'
    username = str(getattr(user, 'unique_id', getattr(user, 'unique_id_str', '')) or '').lower()
    nickname = str(getattr(user, 'nickname', '') or '').strip()
    nombre = extraer_o_limpiar_emojis(nickname, max_emojis=1) if nickname else ''
    nombre = nombre.strip() if nombre else ''
    if username and nombre:
        NOMBRES_POR_USUARIO[username] = nombre
    return nombre or 'Usuario'

def broadcast_overlay_data():
    global ULTIMA_ACCION
    top_likers = sorted(LIKES_POR_USUARIO.items(), key=lambda x: x[1], reverse=True)[:15]
    formatted_likers = [
        {"name": NOMBRES_POR_USUARIO.get(k, k), "score": v, "progress": v, "goal_hits": 0,
         "goal_active": True, "avatar": AVATARES_POR_USUARIO.get(k, "")}
        for k, v in top_likers
    ]
    top_donators = sorted(DONACIONES_POR_USUARIO.items(), key=lambda x: x[1], reverse=True)[:15]
    formatted_donators = [
        {"name": NOMBRES_POR_USUARIO.get(k, k), "score": v, "progress": v, "goal_hits": 0,
         "goal_active": True, "avatar": AVATARES_POR_USUARIO.get(k, "")}
        for k, v in top_donators
    ]

    active_action = ULTIMA_ACCION
    if active_action:
        expires_at = float(active_action.get("expires_at", 0) or 0)
        if expires_at and time.time() >= expires_at:
            active_action = None
            ULTIMA_ACCION = None

    payload = {
        "toplikers": formatted_likers,
        "topdonators": formatted_donators,
        "last_gift": ULTIMO_REGALO,
        "last_follower": ULTIMO_SEGUIDOR,
        "last_action": active_action,
        "total_likes": STATS["likes_totales"],
        "follows_total": STATS["follows"],
        "last_like_goal": dict(ULTIMO_LIKE_META or {})
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
    'no_leer_usuario': False, 'no_leer_respuestas': False,
    'alerta_regalos': True, 'alerta_follows': True, 'alerta_likes_general': False,
    'meta_likes_general': 1000, 'repetir_likes_general': True,
    'alerta_likes_persona': True, 'meta_likes_persona': 50, 'repetir_likes_persona': True,
    'url_regalo': '', 'url_follow': '', 'url_like_general': '', 'url_like_persona': '',
    'alertas_regalos_personalizadas': [],  # Alertas independientes por regalo
    'alertas_emotes_personalizadas': [],   # Alertas independientes por emote
    'agradecer_regalos': True,

    'fuente_interfaz': 'Segoe UI',
    'widget_designs': {
        'topliker': {'design': 'toplikes_custom', 'max': 5, 'title': ''},
        'topdonator': {'design': 'toplikes_custom', 'max': 5, 'title': 'Top Donadores'},
        'myactions': {'design': 'myactions', 'max': 1, 'title': 'Mis Acciones'},
        'lastfollower': {'design': 'standard', 'max': 1, 'title': 'Último Seguidor'},
        'goal': {'design': 'goal', 'max': 1, 'title': 'Meta de Follows'},
    },
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
VELOCIDAD_AUDIO = config['velocidad']
VOZ_TTS = config['voz']
TONO_TTS = config.get('tono', '+0Hz')
HISTORIAL_RECIENTE = deque(maxlen=20)

# Anti-spam de alertas de regalos:
# evita reproducir repetidamente la misma alerta cuando TikTok entrega
# muchos eventos consecutivos del mismo regalo.
ANTISPAM_REGALOS_SEGUNDOS = 5.0
ULTIMAS_ALERTAS_REGALO = {}
ULTIMAS_ALERTAS_EMOTE = {}

TIEMPO_INICIO = time.time()
CONTADOR_LIKES_GENERAL = 0
LIKES_POR_USUARIO = defaultdict(int)          # Likes acumulados durante todo el Live
DONACIONES_POR_USUARIO = defaultdict(int)      # Monedas/coins aportadas mediante regalos durante el Live
LIKES_META_POR_USUARIO = defaultdict(int)      # Progreso independiente para la alerta por persona
AVATARES_POR_USUARIO = {}
NOMBRES_POR_USUARIO = {}
ULTIMO_REGALO = None
ULTIMO_SEGUIDOR = None
ULTIMA_ACCION = None
ULTIMO_LIKE_META = None
CANCION_ACTUAL_WIDGET = {"title": "", "user": "", "duration": 0, "started_at": 0, "cover": ""}
STATS = {'comentarios': 0, 'regalos': 0, 'follows': 0, 'likes_totales': 0, 'viewers': 0}
pygame.mixer.init()
cola_mensajes = queue.Queue(maxsize=50)

# Servidor local para overlays/widgets.
threading.Thread(target=run_flask_server, daemon=True).start()
def reproducir_sonido_url(origen):
    """Reproduce una alerta desde una URL HTTP/HTTPS o desde un archivo local."""
    origen = str(origen or '').strip().strip('"')
    if not origen:
        gui.agregar_log('[Alerta Audio]: No se indicó ningún audio.')
        return

    # También acepta rutas file://.
    if origen.lower().startswith('file://'):
        origen = urllib.parse.unquote(urllib.parse.urlparse(origen).path)
        if os.name == 'nt' and origen.startswith('/') and len(origen) > 2 and origen[2] == ':':
            origen = origen[1:]

    es_url = origen.lower().startswith(('http://', 'https://'))

    def _stream_and_play():
        audio_buffer = None
        try:
            if es_url:
                target_url = origen
                if 'myinstants.com' in target_url and not target_url.lower().endswith('.mp3'):
                    slug = target_url.rstrip('/').split('/')[-1]
                    target_url = f'https://www.myinstants.com/media/sounds/{slug}.mp3'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'audio/mpeg, audio/*;q=0.9, */*;q=0.8',
                    'Referer': 'https://www.myinstants.com/'
                }
                req = urllib.request.Request(target_url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    audio_bytes = response.read()
                if not audio_bytes:
                    gui.agregar_log('[Error Audio]: El archivo remoto está vacío.')
                    return
                audio_buffer = io.BytesIO(audio_bytes)
                sonido = pygame.mixer.Sound(audio_buffer)
            else:
                ruta = os.path.abspath(os.path.expanduser(origen))
                if not os.path.isfile(ruta):
                    gui.agregar_log(f'[Error Audio]: No existe el archivo local: {ruta}')
                    return
                sonido = pygame.mixer.Sound(ruta)

            canal = pygame.mixer.find_channel(True)
            if canal:
                volumen_alertas_real = float(gui.slider_volumen_alertas.get()) * 0.75
                canal.set_volume(volumen_alertas_real)
                canal.play(sonido)
            else:
                gui.agregar_log('[Error Audio]: Sin canales disponibles.')
        except Exception as e:
            gui.agregar_log(f'[Error Audio]: {e}')
        finally:
            if audio_buffer is not None:
                try:
                    audio_buffer.close()
                except Exception:
                    pass

    threading.Thread(target=_stream_and_play, daemon=True).start()


def seleccionar_audio_local(entry):
    """Selecciona un archivo local y coloca su ruta en el campo de audio."""
    try:
        ruta = filedialog.askopenfilename(
            title='Seleccionar sonido de alerta',
            filetypes=[
                ('Archivos de audio', '*.mp3 *.wav *.ogg *.oga *.flac'),
                ('MP3', '*.mp3'),
                ('WAV', '*.wav'),
                ('OGG', '*.ogg *.oga'),
                ('Todos los archivos', '*.*')
            ]
        )
        if ruta:
            entry.delete(0, tk.END)
            entry.insert(0, ruta)
    except Exception as e:
        gui.agregar_log(f'[Error Selector Audio]: {e}')

def extraer_catalogo_regalos_tiktok(client):
    """Extrae todos los regalos devueltos por TikTokLive."""
    encontrados = {}
    vistos = set()

    def recorrer(obj):
        if obj is None or isinstance(obj, (str, bytes, int, float, bool)):
            return
        try:
            oid = id(obj)
            if oid in vistos:
                return
            vistos.add(oid)
            if len(vistos) > 20000:
                return
        except Exception:
            pass

        if isinstance(obj, dict):
            nombre = (obj.get("name") or obj.get("gift_name") or obj.get("giftName")
                      or obj.get("gift_name_text") or obj.get("display_name"))
            gid = (obj.get("gift_id") or obj.get("giftId") or obj.get("id")
                   or obj.get("giftID"))
            if nombre:
                nombre = str(nombre).strip()
                if nombre:
                    gid = str(gid or nombre)
                    encontrados[gid] = {"id": gid, "name": nombre}
            for value in obj.values():
                recorrer(value)
            return

        if isinstance(obj, (list, tuple, set)):
            for item in obj:
                recorrer(item)
            return

        try:
            nombre = (getattr(obj, "name", None) or getattr(obj, "gift_name", None)
                      or getattr(obj, "giftName", None) or getattr(obj, "display_name", None))
            gid = (getattr(obj, "gift_id", None) or getattr(obj, "giftId", None)
                   or getattr(obj, "id", None))
            if nombre:
                nombre = str(nombre).strip()
                if nombre:
                    gid = str(gid or nombre)
                    encontrados[gid] = {"id": gid, "name": nombre}
        except Exception:
            pass

        for attr in ("gift", "info", "gift_info", "gifts", "available_gifts",
                     "gift_list", "giftList", "items", "data", "list", "gifts_info"):
            try:
                value = getattr(obj, attr, None)
                if value is not None:
                    recorrer(value)
            except Exception:
                pass

    try:
        recorrer(getattr(client, "gift_info", None))
    except Exception:
        pass

    for attr in ("available_gifts", "gifts", "gift_list"):
        try:
            recorrer(getattr(client, attr, None))
        except Exception:
            pass

    unicos = {}
    for item in encontrados.values():
        nombre = item["name"].strip()
        if nombre:
            unicos[nombre.casefold()] = {"id": item["id"], "name": nombre}
    return sorted(unicos.values(), key=lambda x: x["name"].casefold())

CATALOGO_REGALOS_INICIAL = [
    "Rose", "TikTok", "GG", "You're Awesome", "Ice Cream Cone",
    "Shining Starlight", "Creeper", "Birthday Cake", "Lucky Pig", "Pop",
    "Freestyle", "Wink Wink", "Oldies", "Glow Stick", "Love You So...",
    "Okay", "Finger Heart", "Ice Cream", "Peach", "Hand Heart",
    "Overreact", "Name Shoutout", "Rosa", "Shamrock", "Friendship Necklace",
    "Slow Motion", "Drip Brewing", "Perfume", "Journey Pass", "Bravo!",
    "Little Kisses", "Doughnut", "Takoyaki", "Family", "Fireworks",
    "Exclusive Space", "Diamond", "Party Laser", "Wedding", "Chasing the Dream",
    "Future Encounter", "Racing Debut", "Shooting Stars", "Cooper Flies",
    "Jollie's Heartland", "Sage's Coinbot", "Wave Lights", "Stars Honor",
    "Motorcycle", "Pink Dream", "Ice Cream Truck", "Love in Sunset",
    "Party Bus", "Meteor Shower", "Hip-Hop Hen", "Private Jet",
    "Hero Space Ship", "Flying Jets", "Star Hero Stage", "Strong Finish",
    "Sports Car", "Interstellar", "Sunset Speedway", "Superstar",
    "TikTok Shuttle", "Phoenix", "Capybara"
]

def catalogo_regalos_inicial():
    return [{"id": nombre, "name": nombre} for nombre in sorted(set(CATALOGO_REGALOS_INICIAL), key=str.casefold)]

def nombre_regalo_normalizado(nombre):
    return re.sub(r"\s+"," ",str(nombre or "").strip()).casefold()

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
        self.restringir_subs = tk.BooleanVar(value=config['restringir_subs'])
        self.restringir_mods = tk.BooleanVar(value=config['restringir_mods'])
        self.restringir_lista = tk.BooleanVar(value=config['restringir_lista'])
        self.no_leer_usuario = tk.BooleanVar(value=config.get('no_leer_usuario', False))
        self.no_leer_respuestas = tk.BooleanVar(value=config.get('no_leer_respuestas', False))
        self.alerta_regalos = tk.BooleanVar(value=config.get('alerta_regalos', True))
        self.agradecer_regalos = tk.BooleanVar(value=config.get('agradecer_regalos', True))
        self.alerta_follows = tk.BooleanVar(value=config.get('alerta_follows', True))
        self.alerta_likes_general = tk.BooleanVar(value=config.get('alerta_likes_general', True))
        self.repetir_likes_general = tk.BooleanVar(value=config.get('repetir_likes_general', True))
        self.alerta_likes_persona = tk.BooleanVar(value=config.get('alerta_likes_persona', True))
        self.repetir_likes_persona = tk.BooleanVar(value=config.get('repetir_likes_persona', True))
        self.client_tiktok = None
        self.conectado = False
        self.tiktok_stop_requested = False
        self.tiktok_connection_id = 0
        self._timer_regalos = None
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
        self.tab_tts = ttk.Frame(self.notebook)
        self.tab_filtros = ttk.Frame(self.notebook)
        self.tab_alertas = ttk.Frame(self.notebook)
        self.tab_widgets = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_principal, text=' Dashboard ')
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
        self.lbl_stat_viewers = ttk.Label(f_m, text='Viewers: 0')
        self.lbl_stat_viewers.pack(side='left', expand=True)
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
        self.combo_vel = ttk.Combobox(f_pitch_vel, values=['+0%', '+15%', '+30%', '+45%', '+60%', '+75%', '+90%', '+100%'], state='readonly', width=8)
        self.combo_vel.set(VELOCIDAD_AUDIO)
        self.combo_vel.pack(side='left', padx=5)
        ttk.Label(f_pitch_vel, text='Tono:').pack(side='left', padx=(15, 0))
        self.combo_tono = ttk.Combobox(f_pitch_vel, values=['-50Hz', '-45Hz', '-40Hz', '-35Hz', '-30Hz', '-25Hz', '-20Hz', '-15Hz', '-10Hz', '-5Hz', '+0Hz', '+5Hz', '+10Hz', '+15Hz', '+20Hz', '+25Hz', '+30Hz', '+35Hz', '+40Hz', '+45Hz', '+50Hz'], state='readonly', width=8)
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
        
        #Voz_Chat
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
        ttk.Checkbutton(f_chk, text='Suscritores/SupeFans', variable=self.restringir_subs).pack(side='left')
        ttk.Label(f_chk, text='Niv.').pack(side='left', padx=(10, 2))
        self.entry_nivel_sub = tk.Entry(f_chk, bg='#11111b', fg='#cdd6f4', insertbackground='white', width=4, relief='flat')
        self.entry_nivel_sub.insert(0, str(config.get('nivel_sub_minimo', 2)))
        self.entry_nivel_sub.pack(side='left', padx=(0, 15))
        ttk.Checkbutton(f_chk, text='Moderadores  ', variable=self.restringir_mods).pack(side='left', expand=True)
        ttk.Checkbutton(f_chk, text='Lista Blanca', variable=self.restringir_lista).pack(side='left', expand=True)
        f_chk_lectura = ttk.Frame(frame_filtros)
        f_chk_lectura.pack(fill='x', padx=10, pady=(0, 5))
        ttk.Checkbutton(
            f_chk_lectura,
            text='No leer usuario',
            variable=self.no_leer_usuario
        ).pack(side='left', expand=True)
        ttk.Checkbutton(
            f_chk_lectura,
            text='No leer menciones',
            variable=self.no_leer_respuestas
        ).pack(side='left', expand=True)
        f_lista = ttk.Frame(frame_filtros)
        f_lista.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_lista, text=' Lista Blanca ').pack(anchor='w')
        self.entry_lista = tk.Entry(f_lista, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 9), relief='flat')
        self.entry_lista.insert(0, config.get('lista_blanca', ''))
        self.entry_lista.pack(fill='x', pady=3)
        ttk.Label(
        f_lista, text="Ejemplo: (Usuario1, Usuario2)", foreground="#6c7086").pack(fill='x', padx=0, pady=(2, 5))
        
        frame_censura = ttk.LabelFrame(self.tab_filtros, text=' Filtro de Palabras Prohibidas ')
        frame_censura.pack(fill='x', padx=10, pady=5)
        f_cen = ttk.Frame(frame_censura)
        f_cen.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_cen, text='Palabras a omitir/censurar:').pack(anchor='w')
        self.entry_censura = tk.Entry(f_cen, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 9), relief='flat')
        self.entry_censura.insert(0, config.get('palabras_censuradas', ''))
        self.entry_censura.pack(fill='x', pady=3)
        ttk.Label(
        f_cen, text="Ejemplo: (Prohibida1, Prohibida2)", foreground="#6c7086").pack(fill='x', padx=0, pady=(2.5))
        
        frame_reemplazos = ttk.LabelFrame(self.tab_filtros, text=' Diccionario de Reemplazos ')
        frame_reemplazos.pack(fill='x', padx=10, pady=5)
        f_rep = ttk.Frame(frame_reemplazos)
        f_rep.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_rep, text='Reemplazar (Formato orig:nuevo):').pack(anchor='w')
        self.entry_reemplazos = tk.Entry(f_rep, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 9), relief='flat')
        self.entry_reemplazos.insert(0, config.get('reemplazos', ''))
        self.entry_reemplazos.pack(fill='x', pady=3)
        ttk.Label(
        f_rep, text="Ejemplo: (gg:yiyi, tqm:te quiero mucho)", foreground="#6c7086").pack(fill='x', padx=0, pady=(2.5))
        
        #Alertas y Eventos
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
        
        ttk.Checkbutton(f_reg, text='Agradecer por el regalo', variable=self.agradecer_regalos).pack(side='left', padx=(10,0))

        frame_regalos_personalizados = ttk.LabelFrame(self.tab_alertas, text=' Alertas de regalos independientes ')
        frame_regalos_personalizados.pack(fill='x', padx=10, pady=5)
        f_regalos_head = ttk.Frame(frame_regalos_personalizados); f_regalos_head.pack(fill='x', padx=5, pady=(5,2))
        ttk.Label(f_regalos_head,text='Regalo').pack(side='left',padx=(5,4))
        ttk.Label(f_regalos_head,text='Sonido (URL o archivo local)').pack(side='left',padx=(80,4))
        self.frame_regalos_personalizados=ttk.Frame(frame_regalos_personalizados); self.frame_regalos_personalizados.pack(fill='x',padx=5,pady=2)
        f_regalos_buttons=ttk.Frame(frame_regalos_personalizados); f_regalos_buttons.pack(fill='x',padx=5,pady=(3,6))
        self.btn_agregar_alerta_regalo=tk.Button(f_regalos_buttons,text='＋ Agregar ',bg='#a6e3a1',fg='#11111b',relief='flat',font=(self.fuente_actual,9,'bold'),command=self.agregar_alerta_regalo); self.btn_agregar_alerta_regalo.pack(side='left',padx=2)
        self.btn_actualizar_regalos=tk.Button(f_regalos_buttons,text='↻ Actualizar',bg='#89b4fa',fg='#11111b',relief='flat',font=(self.fuente_actual,9,'bold'),command=self.actualizar_catalogo_desde_tiktok); self.btn_actualizar_regalos.pack(side='left',padx=4)
        self.lbl_catalogo_regalos=ttk.Label(f_regalos_buttons,text=' Cargando catálogo inicial...')
        self.lbl_catalogo_regalos.pack(side='left',padx=8)
        self.alertas_regalos_personalizadas=[]; self.catalogo_regalos=catalogo_regalos_inicial()
        self.actualizar_catalogo_regalos(self.catalogo_regalos)
        self.cargar_alertas_regalos_personalizadas()

        frame_emotes_personalizados = ttk.LabelFrame(self.tab_alertas, text=' Alertas de Stickers')
        frame_emotes_personalizados.pack(fill='x', padx=10, pady=5)
        f_emotes_head = ttk.Frame(frame_emotes_personalizados)
        f_emotes_head.pack(fill='x', padx=5, pady=(5,2))
        ttk.Label(f_emotes_head, text='Sticker').pack(side='left', padx=(5,4))
        ttk.Label(f_emotes_head, text='Nombre').pack(side='left', padx=(55,4))
        ttk.Label(f_emotes_head, text='Sonido (URL o archivo local)').pack(side='left', padx=(45,4))
        self.frame_emotes_personalizados = ttk.Frame(frame_emotes_personalizados)
        self.frame_emotes_personalizados.pack(fill='x', padx=5, pady=2)
        f_emotes_buttons = ttk.Frame(frame_emotes_personalizados)
        f_emotes_buttons.pack(fill='x', padx=5, pady=(3,6))
        self.btn_agregar_alerta_emote = tk.Button(f_emotes_buttons, text='＋ Agregar ', bg='#a6e3a1', fg='#11111b', relief='flat', font=(self.fuente_actual,9,'bold'), command=self.agregar_alerta_emote)
        self.btn_agregar_alerta_emote.pack(side='left', padx=2)
        self.lbl_catalogo_emotes = ttk.Label(f_emotes_buttons, text='Esperando Stickers del Live...')
        self.lbl_catalogo_emotes.pack(side='left', padx=8)
        self.alertas_emotes_personalizadas = []
        self.catalogo_emotes_personalizados = []
        self.cargar_alertas_emotes_personalizadas()

        f_fol = ttk.Frame(frame_alertas_audio)
        f_fol.pack(fill='x', padx=10, pady=5)
        ttk.Checkbutton(f_fol, text='Follows:', variable=self.alerta_follows).pack(side='left')
        self.entry_url_follow = tk.Entry(f_fol, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 8), relief='flat')
        self.entry_url_follow.insert(0, config.get('url_follow', ''))
        self.entry_url_follow.pack(side='left', fill='x', expand=True, padx=5)
        tk.Button(f_fol, text='Subir Local', width=3, bg='#89b4fa', fg='#11111b', relief='flat',
                  command=lambda e=self.entry_url_follow: seleccionar_audio_local(e)).pack(side='left', padx=2)
        tk.Button(f_fol, text='▶', width=3, bg='#89b4fa', fg='#11111b', relief='flat',
                  command=lambda e=self.entry_url_follow: reproducir_sonido_url(e.get().strip())).pack(side='left', padx=2)
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
        ttk.Label(f_lik_gen_url, text='Audio (URL/local):').pack(side='left')
        self.entry_url_like_general = tk.Entry(f_lik_gen_url, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 8), relief='flat')
        self.entry_url_like_general.insert(0, config.get('url_like_general', ''))
        self.entry_url_like_general.pack(side='left', fill='x', expand=True, padx=5)
        tk.Button(f_lik_gen_url, text='Subir Local', width=3, bg='#89b4fa', fg='#11111b', relief='flat',
                  command=lambda e=self.entry_url_like_general: seleccionar_audio_local(e)).pack(side='left', padx=2)
        tk.Button(f_lik_gen_url, text='▶', width=3, bg='#89b4fa', fg='#11111b', relief='flat',
                  command=lambda e=self.entry_url_like_general: reproducir_sonido_url(e.get().strip())).pack(side='left', padx=2)
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
        ttk.Label(f_lik_per_url, text='Audio (URL/local):').pack(side='left')
        self.entry_url_like_persona = tk.Entry(f_lik_per_url, bg='#11111b', fg='#cdd6f4', insertbackground='white', font=(self.fuente_actual, 8), relief='flat')
        self.entry_url_like_persona.insert(0, config.get('url_like_persona', ''))
        self.entry_url_like_persona.pack(side='left', fill='x', expand=True, padx=5)
        tk.Button(f_lik_per_url, text='Subir Local', width=3, bg='#89b4fa', fg='#11111b', relief='flat',
                  command=lambda e=self.entry_url_like_persona: seleccionar_audio_local(e)).pack(side='left', padx=2)
        tk.Button(f_lik_per_url, text='▶', width=3, bg='#89b4fa', fg='#11111b', relief='flat',
                  command=lambda e=self.entry_url_like_persona: reproducir_sonido_url(e.get().strip())).pack(side='left', padx=2)
        # Tab Widgets: cada widget usa su propia personalización.
        # No existe un tema/estilo global que se herede entre widgets.

        frame_urls = ttk.LabelFrame(self.tab_widgets, text="Configuracion De Los Overlays")
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
                values=["standard", "toplikes_custom", "goal", "myactions"],
                state="readonly", width=14
            )
            c_design.set(designs_saved.get(endpoint, {}).get(
                "design",
                {"topliker":"toplikes_custom","myactions":"myactions","goal":"goal"}.get(endpoint, "standard")
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
        _crear_widget_row_custom(frame_urls, "Top Donadores", "topdonator")
        _crear_widget_row_custom(frame_urls, "Mis Acciones", "myactions")
        _crear_widget_row_custom(frame_urls, "Último Follower", "lastfollower")
        _crear_widget_row_custom(frame_urls, "Meta / Goal", "goal")
        
        btn_regen_urls = tk.Button(
            frame_urls, text="Generar y Guardar URLs de Widgets",
            bg="#a6e3a1", fg="#11111b", relief="flat",
            command=self.actualizar_urls_widgets, font=(self.fuente_actual, 8, "bold")
        )
        btn_regen_urls.pack(pady=5)

        self.actualizar_urls_widgets()


        self.actualizar_monitoreo_ram()
        self.actualizar_cronometro_live()
    def _parse_widget_color(self, value):
        """Convierte HEX/RGB/RGBA a (r, g, b, alpha 0..1)."""
        value = str(value or "").strip()
        if value.lower() == "transparent":
            return 0, 0, 0, 0.0

        m = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([0-9.]+))?\s*\)", value, re.I)
        if m:
            r, g, b = [max(0, min(255, int(x))) for x in m.group(1, 2, 3)]
            a = float(m.group(4)) if m.group(4) is not None else 1.0
            return r, g, b, max(0.0, min(1.0, a))

        h = value.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6 and re.fullmatch(r"[0-9a-fA-F]{6}", h):
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0
        if len(h) == 8 and re.fullmatch(r"[0-9a-fA-F]{8}", h):
            return (
                int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16),
                int(h[6:8], 16) / 255.0
            )
        return 137, 180, 250, 1.0

    def _widget_rgba_text(self, r, g, b, a):
        return f"rgba({int(r)}, {int(g)}, {int(b)}, {a:.2f})"

    def abrir_selector_color_widget(self, variable, button, title="Selector de color"):
        """Selector visual RGBA para los colores de los widgets."""
        r, g, b, alpha = self._parse_widget_color(variable.get())
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

        win = tk.Toplevel(self.root)
        win.title(f"🎨 {title}")
        win.geometry("470x470")
        win.resizable(False, False)
        win.configure(bg="#1e1e2e")
        win.transient(self.root)
        win.grab_set()

        tk.Label(
            win, text="Selector de color RGBA",
            bg="#1e1e2e", fg="#cdd6f4",
            font=(self.fuente_actual, 13, "bold")
        ).pack(pady=(12, 2))
        tk.Label(
            win, text="Elige el color y la transparencia sin escribir HEX.",
            bg="#1e1e2e", fg="#a6adc8",
            font=(self.fuente_actual, 8)
        ).pack(pady=(0, 8))

        W, H = 400, 190
        sv = tk.Canvas(win, width=W, height=H, highlightthickness=0, bd=0)
        sv.pack(padx=15)

        hue = tk.Canvas(win, width=W, height=22, highlightthickness=0, bd=0)
        hue.pack(padx=15, pady=(8, 0))

        alpha_canvas = tk.Canvas(win, width=W, height=22, highlightthickness=0, bd=0)
        alpha_canvas.pack(padx=15, pady=(7, 0))

        # Entradas RGBA/HEX: sirven para ver el valor exacto, pero el usuario
        # ya no necesita escribir HEX para seleccionar el color.
        fields = tk.Frame(win, bg="#1e1e2e")
        fields.pack(fill="x", padx=15, pady=10)

        vars_rgb = [tk.StringVar(value=str(r)), tk.StringVar(value=str(g)),
                    tk.StringVar(value=str(b)), tk.StringVar(value=str(round(alpha * 100)))]
        labels = ["R", "G", "B", "A %"]
        entries = []

        for lab, var in zip(labels, vars_rgb):
            box = tk.Frame(fields, bg="#1e1e2e")
            box.pack(side="left", expand=True, padx=3)
            tk.Label(box, text=lab, bg="#1e1e2e", fg="#a6adc8",
                     font=(self.fuente_actual, 8, "bold")).pack()
            ent = tk.Entry(
                box, textvariable=var, width=7, justify="center",
                bg="#11111b", fg="#cdd6f4", insertbackground="white",
                relief="flat", font=(self.fuente_actual, 9)
            )
            ent.pack()
            entries.append(ent)

        hex_var = tk.StringVar(
            value=f"#{int(r):02X}{int(g):02X}{int(b):02X}"
        )
        hex_row = tk.Frame(win, bg="#1e1e2e")
        hex_row.pack(fill="x", padx=18, pady=(0, 6))
        tk.Label(hex_row, text="HEX", bg="#1e1e2e", fg="#a6adc8",
                 font=(self.fuente_actual, 8, "bold")).pack(side="left")
        hex_entry = tk.Entry(
            hex_row, textvariable=hex_var, width=12, justify="center",
            bg="#11111b", fg="#cdd6f4", insertbackground="white",
            relief="flat", font=(self.fuente_actual, 9)
        )
        hex_entry.pack(side="left", padx=8)

        preview = tk.Frame(
            hex_row, width=55, height=28, bg="#11111b",
            highlightthickness=1, highlightbackground="#585b70"
        )
        preview.pack(side="right")
        preview.pack_propagate(False)

        value_lbl = tk.Label(
            win, text="", bg="#1e1e2e", fg="#a6adc8",
            font=(self.fuente_actual, 8)
        )
        value_lbl.pack()

        updating = {"value": False}

        def clamp_int(text, default):
            try:
                return max(0, min(255, int(float(text))))
            except (TypeError, ValueError):
                return default

        def clamp_alpha(text, default):
            try:
                return max(0, min(100, int(float(text))))
            except (TypeError, ValueError):
                return default

        def draw_sv():
            sv.delete("all")
            steps_x, steps_y = 80, 38
            for ix in range(steps_x):
                sat = ix / (steps_x - 1)
                for iy in range(steps_y):
                    val = 1 - iy / (steps_y - 1)
                    rr, gg, bb = colorsys.hsv_to_rgb(h, sat, val)
                    color = "#{:02x}{:02x}{:02x}".format(
                        int(rr * 255), int(gg * 255), int(bb * 255)
                    )
                    x0 = ix * W / steps_x
                    y0 = iy * H / steps_y
                    sv.create_rectangle(
                        x0, y0, x0 + W / steps_x + 1,
                        y0 + H / steps_y + 1, fill=color, outline=color
                    )

            x = s * W
            y = (1 - v) * H
            sv.create_oval(x - 7, y - 7, x + 7, y + 7,
                           outline="white", width=2)
            sv.create_oval(x - 3, y - 3, x + 3, y + 3,
                           outline="black", width=1)

        def draw_hue():
            hue.delete("all")
            steps = 120
            for i in range(steps):
                hh = i / (steps - 1)
                rr, gg, bb = colorsys.hsv_to_rgb(hh, 1, 1)
                color = "#{:02x}{:02x}{:02x}".format(
                    int(rr * 255), int(gg * 255), int(bb * 255)
                )
                x0 = i * W / steps
                hue.create_rectangle(
                    x0, 0, x0 + W / steps + 1, 22,
                    fill=color, outline=color
                )
            x = h * W
            hue.create_rectangle(x - 3, 0, x + 3, 22,
                                 outline="white", width=2)

        def draw_alpha():
            alpha_canvas.delete("all")
            size = 16
            for ix in range(0, W, size):
                for iy in range(0, 22, size):
                    n = ((ix // size) + (iy // size)) % 2
                    c = "#d8d8d8" if n else "#9c9c9c"
                    alpha_canvas.create_rectangle(
                        ix, iy, ix + size, iy + size,
                        fill=c, outline=c
                    )

            base = "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))
            # Segmentos con distintos niveles de transparencia sobre el tablero.
            for i in range(100):
                a = i / 99
                mixed = tuple(
                    round(220 * (1 - a) + comp * a) for comp in (r, g, b)
                )
                color = "#{:02x}{:02x}{:02x}".format(*mixed)
                x0 = i * W / 100
                alpha_canvas.create_rectangle(
                    x0, 0, x0 + W / 100 + 1, 22,
                    fill=color, outline=color
                )
            x = alpha * W
            alpha_canvas.create_rectangle(x - 3, 0, x + 3, 22,
                                          outline="white", width=2)

        def update_button_live():
            # El botón que abrió este selector refleja inmediatamente el color
            # que se está seleccionando, sin esperar a cerrar el panel.
            display = "#%02x%02x%02x" % (int(r), int(g), int(b))
            # El alpha no puede representarse directamente en un botón Tkinter;
            # se conserva en el valor RGBA y el botón muestra el RGB seleccionado.
            luminance = (int(r) * 299 + int(g) * 587 + int(b) * 114) / 1000
            fg = "#11111b" if luminance >= 150 else "#ffffff"
            rgba_value = self._widget_rgba_text(r, g, b, alpha)
            button.config(
                text=f"  {rgba_value}  ",
                bg=display,
                fg=fg,
                activebackground=display,
                activeforeground=fg
            )

        def update_fields():
            updating["value"] = True
            vars_rgb[0].set(str(int(r)))
            vars_rgb[1].set(str(int(g)))
            vars_rgb[2].set(str(int(b)))
            vars_rgb[3].set(str(int(round(alpha * 100))))
            hex_var.set(f"#{int(r):02X}{int(g):02X}{int(b):02X}")
            value_lbl.config(text=self._widget_rgba_text(r, g, b, alpha))
            display = "#%02x%02x%02x" % (int(r), int(g), int(b))
            preview.config(bg=display)
            update_button_live()
            updating["value"] = False

        def from_rgb():
            nonlocal r, g, b, h, s, v, alpha
            r = clamp_int(vars_rgb[0].get(), r)
            g = clamp_int(vars_rgb[1].get(), g)
            b = clamp_int(vars_rgb[2].get(), b)
            alpha = clamp_alpha(vars_rgb[3].get(), int(alpha * 100)) / 100
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            draw_sv()
            draw_hue()
            draw_alpha()
            update_fields()

        def from_hex(event=None):
            nonlocal r, g, b, h, s, v
            value = hex_var.get().strip().lstrip("#")
            if len(value) == 3:
                value = "".join(c * 2 for c in value)
            if len(value) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", value):
                update_fields()
                return
            r, g, b = int(value[:2], 16), int(value[2:4], 16), int(value[4:6], 16)
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            draw_sv()
            draw_hue()
            draw_alpha()
            update_fields()

        def click_sv(event):
            nonlocal s, v, r, g, b
            s = max(0.0, min(1.0, event.x / W))
            v = max(0.0, min(1.0, 1 - event.y / H))
            rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
            r, g, b = [round(x * 255) for x in (rr, gg, bb)]
            update_fields()
            draw_sv()

        def click_hue(event):
            nonlocal h, r, g, b
            h = max(0.0, min(1.0, event.x / W))
            rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
            r, g, b = [round(x * 255) for x in (rr, gg, bb)]
            update_fields()
            draw_sv()
            draw_hue()

        def click_alpha(event):
            nonlocal alpha
            alpha = max(0.0, min(1.0, event.x / W))
            update_fields()
            draw_alpha()

        sv.bind("<Button-1>", click_sv)
        sv.bind("<B1-Motion>", click_sv)
        hue.bind("<Button-1>", click_hue)
        hue.bind("<B1-Motion>", click_hue)
        alpha_canvas.bind("<Button-1>", click_alpha)
        alpha_canvas.bind("<B1-Motion>", click_alpha)
        hex_entry.bind("<Return>", from_hex)

        def save_color():
            from_rgb()
            variable.set(self._widget_rgba_text(r, g, b, alpha))
            update_button_live()
            win.destroy()

        # Al pulsar la X del panel se conserva exactamente el último color
        # seleccionado, igual que al pulsar «Aplicar color».
        win.protocol("WM_DELETE_WINDOW", save_color)

        footer = tk.Frame(win, bg="#1e1e2e")
        footer.pack(fill="x", padx=15, pady=10)
        tk.Button(
            footer, text="Cancelar", bg="#45475a", fg="#cdd6f4",
            relief="flat", command=win.destroy,
            font=(self.fuente_actual, 8, "bold")
        ).pack(side="right", padx=(5, 0))
        tk.Button(
            footer, text="✓ Aplicar color", bg="#a6e3a1", fg="#11111b",
            relief="flat", command=save_color,
            font=(self.fuente_actual, 8, "bold")
        ).pack(side="right")

        draw_sv()
        draw_hue()
        draw_alpha()
        update_fields()

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
                    ("heart_size", "Tamaño Del Corazon", "14"), ("crown_size", "Tamaño De La Corona", "16"),
                    ("crown_top", "Corona Posición Y", "-14"), ("rank_color", "Color posición", "#89b4fa"),
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
        # Estos parámetros se seleccionan con el panel visual RGBA.
        color_keys = {
            "bg", "card_bg", "text", "accent", "border", "shadow",
            "rank_color", "action_bg", "track", "fill", "percent"
        }

        def actualizar_boton_color(button, value):
            rr, gg, bb, aa = self._parse_widget_color(value)
            display = "#%02x%02x%02x" % (rr, gg, bb)
            button.config(
                text=f"  {value}  ",
                bg=display,
                activebackground=display
            )

        for section_name, fields in schema:
            lf = ttk.LabelFrame(inner, text=f" {section_name} ")
            lf.pack(fill="x", padx=4, pady=5)
            for key, label, default in fields:
                row = ttk.Frame(lf)
                row.pack(fill="x", padx=8, pady=3)
                ttk.Label(row, text=label, width=25).pack(side="left")
                current = saved.get(key, defaults_now.get(key, default))

                if key in ( "crown", "show_rank", "show_badges"):
                    var = tk.BooleanVar(value=str(current) in ("1", "True", "true"))
                    ttk.Checkbutton(row, text="Activado", variable=var).pack(side="left")
                elif key == "heart_anim":
                    var = tk.StringVar(value=str(current))
                    combo = ttk.Combobox(
                        row, textvariable=var,
                        values=["heartbeat", "pop"], state="readonly", width=18
                    )
                    combo.pack(side="left")
                elif key in color_keys:
                    var = tk.StringVar(value=str(current))
                    rr, gg, bb, aa = self._parse_widget_color(current)
                    display = "#%02x%02x%02x" % (rr, gg, bb)
                    btn_color = tk.Button(
                        row,
                        text=f"  {current}  ",
                        bg=display,
                        fg="#11111b" if (rr + gg + bb) > 420 else "#ffffff",
                        activebackground=display,
                        relief="flat",
                        font=(self.fuente_actual, 8, "bold"),
                        cursor="hand2",
                        command=lambda v=var, b_ref=None, lbl=label: None
                    )
                    # Se asigna después de crear el botón para evitar referencias
                    # incorrectas dentro del lambda.
                    btn_color.config(
                        command=lambda v=var, b=btn_color, lbl=label:
                            self.abrir_selector_color_widget(v, b, lbl)
                    )
                    btn_color.pack(side="left", fill="x", expand=True)
                else:
                    var = tk.StringVar(value=str(current))
                    ent = tk.Entry(
                        row, textvariable=var, bg="#11111b", fg="#cdd6f4",
                        insertbackground="white", relief="flat",
                        font=(self.fuente_actual, 8)
                    )
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
            "topdonator": {
                "bg": "rgba(30, 30, 46, 0.9)", "card_bg": "rgba(0, 0, 0, 0.4)",
                "text": "#cdd6f4", "accent": "#ffd166",
                "border": "rgba(49, 50, 68, 0.8)", "shadow": "rgba(0, 0, 0, 0.8)",
                "font": self.fuente_actual, "font_size": "14", "title_font_size": "16",
                "avatar_size": "52", "gap": "12", "padding": "8", "width": "340",
                "shadow_blur": "10", "glow": "8", "radius": "50", "card_blur": "4",
                "border_width": "0", "avatar_radius": "50", "heart_size": "14",
                "crown_size": "16", "crown_top": "-14", "rank_color": "#ffd166",
                "crown": "1", "show_rank": "0", "show_badges": "0", "heart_anim": "heartbeat",
                "action_bg": "transparent", "name_size": "42", "message_size": "24",
                "track": "#ffffff", "fill": "#ffd166", "percent": "#d89b00",
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

            query_str = "?" + "&".join(f"{key}={q(value)}" for key, value in query.items())
            full_url = f"http://127.0.0.1:5000/widget/{endpoint}{query_str}"

            cfg["url_entry"].delete(0, tk.END)
            cfg["url_entry"].insert(0, full_url)

    def copiar_al_portapapeles(self, texto):
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.agregar_log(f"✍URL copiada al portapapeles")


    def aplicar_nueva_fuente(self):
        nueva_fuente = self.combo_fuente.get()
        self.fuente_actual = nueva_fuente
        style = ttk.Style()
        style.configure('TLabelframe.Label', font=(nueva_fuente, 9, 'bold'))
        style.configure('TLabel', font=(nueva_fuente, 9))
        style.configure('TCheckbutton', font=(nueva_fuente, 9))
        self.log_box.config(font=(nueva_fuente, 9))
        self.lbl_estado.config(font=(nueva_fuente, 10, 'bold'))
        self.lbl_tiempo_live.config(font=(nueva_fuente, 10, 'bold'))
        
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
        self.root.after(0, lambda: self.lbl_stat_viewers.config(text=f"Viewers: {STATS.get('viewers', 0)}"))
    def cambiar_volumen(self, val):
        return
    def conmutar_pausa(self):
        self.audio_pausado = not self.audio_pausado
        if self.audio_pausado:
            self.btn_pausa.config(text='Reanudar TTS', bg='#a6e3a1')
            self.agregar_log('၊၊||၊ BOTCHAT PAUSADO')
        else:
            self.btn_pausa.config(text='Pausar TTS', bg='#f9e2af')
            self.agregar_log('၊၊||၊ BOTCHAT REANUDADO')
    def probar_audio(self):
        enviar_a_voz('Prueba de sonido en proceso', forzar=True)
        url = self.entry_url_like_general.get().strip()
        reproducir_sonido_url(url)
    def vaciar_cola(self):
        with cola_mensajes.mutex:
            cola_mensajes.queue.clear()
        self.agregar_log('⌦ Cola de mensajes limpiada')
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
            self.agregar_log('ⓘ No hay registros para aguardar.')
            return
        else:
            filepath = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Archivos de texto', '*.txt'), ('Todos los archivos', '*.*')], title='Guardar Registro de Chat')
            if filepath:
                pass
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(contenido)
            self.agregar_log(f'⎙ Registro guardado en: {filepath}')
        except Exception as e:
            self.agregar_log(f'[Error Guardado]: {e}')
    def alternar_conexion(self):
        if not self.conectado:
            usuario = self.entry_user.get().strip()
            # TikTok acepta el unique_id sin @; eliminamos espacios internos/finales
            # para evitar fallos cuando el usuario viene pegado desde otro sitio.
            usuario = re.sub(r"\\s+", "", usuario).lstrip("@")
            if not usuario:
                self.agregar_log('[ALERTA] Ingresa un usuario válido')
                return

            self.entry_user.delete(0, tk.END)
            self.entry_user.insert(0, '@' + usuario)
            self.tiktok_stop_requested = False
            self.tiktok_connection_id += 1
            self.btn_conectar.config(text='Desconectar', bg='#f38ba8')
            self.entry_user.config(state='disabled')
            threading.Thread(
                target=iniciar_tiktok,
                args=(usuario, self.tiktok_connection_id),
                daemon=True
            ).start()
        else:
            self.tiktok_stop_requested = True
            self.tiktok_connection_id += 1
            self.conectado = False
            self.tiempo_conexion_inicio = None

            client = self.client_tiktok
            self.client_tiktok = None
            if client:
                try:
                    client.stop()
                except Exception:
                    pass

            self.vaciar_cola()
            self.btn_conectar.config(text='Conectar Live', bg='#a6e3a1')
            self.entry_user.config(state='normal')
            self.actualizar_estado('Desconectado', '#f38ba8')
            self.agregar_log('ⓘ Conexión finalizada')

    def cargar_alertas_regalos_personalizadas(self):
        guardadas=config.get('alertas_regalos_personalizadas',[]) or []
        if not isinstance(guardadas,list): guardadas=[]
        for alerta in guardadas:
            if isinstance(alerta,dict): self.agregar_alerta_regalo(alerta.get('regalo',''),alerta.get('sonido',''),alerta.get('activar',True))

    def agregar_alerta_regalo(self, regalo='', sonido='', activar=True):
        fila=ttk.Frame(self.frame_regalos_personalizados); fila.pack(fill='x',pady=2)
        activa_var=tk.BooleanVar(value=bool(activar)); ttk.Checkbutton(fila,text='ON',variable=activa_var).pack(side='left',padx=(0,4))
        nombres=[x['name'] for x in getattr(self,'catalogo_regalos',[])];
        if regalo and regalo not in nombres: nombres.append(regalo)
        combo=ttk.Combobox(fila,values=sorted(set(nombres),key=str.casefold),state='readonly',width=24); combo.set(regalo or (nombres[0] if nombres else '')); combo.pack(side='left',padx=2)
        entry=tk.Entry(fila,bg='#11111b',fg='#cdd6f4',insertbackground='white',font=(self.fuente_actual,8),relief='flat'); entry.insert(0,sonido); entry.pack(side='left',fill='x',expand=True,padx=4)
        tk.Button(fila,text='Subir Local',width=3,bg='#89b4fa',fg='#11111b',relief='flat',
                  font=(self.fuente_actual,8,'bold'),command=lambda e=entry: seleccionar_audio_local(e)).pack(side='left',padx=2)
        tk.Button(fila,text='▶',width=3,bg='#89b4fa',fg='#11111b',relief='flat',
                  font=(self.fuente_actual,8,'bold'),command=lambda e=entry: reproducir_sonido_url(e.get().strip())).pack(side='left',padx=2)
        registro={'frame':fila,'activar_var':activa_var,'combo':combo,'entry':entry}
        def eliminar():
            fila.destroy()
            try: self.alertas_regalos_personalizadas.remove(registro)
            except ValueError: pass
        tk.Button(fila,text='✕',width=3,bg='#f38ba8',fg='#11111b',relief='flat',font=(self.fuente_actual,8,'bold'),command=eliminar).pack(side='left',padx=2)
        self.alertas_regalos_personalizadas.append(registro)

    def actualizar_catalogo_regalos(self,catalogo):
        if not catalogo:
            self.agregar_log('⚠ TikTok no devolvió regalos en este momento.')
            return
        self.catalogo_regalos = catalogo
        nombres = sorted({x['name'] for x in catalogo if x.get('name')}, key=str.casefold)
        for registro in getattr(self, 'alertas_regalos_personalizadas', []):
            actual = registro['combo'].get().strip()
            valores = list(nombres)
            if actual and actual not in valores:
                valores.append(actual)
            registro['combo']['values'] = valores
        try:
            self.lbl_catalogo_regalos.config(text=f' {len(nombres)} regalos disponibles')
        except Exception:
            pass
        self.agregar_log(f'⟳Catálogo de regalos actualizado: {len(nombres)} regalos disponibles.')

    def actualizar_catalogo_desde_tiktok(self):
        """Descarga el catálogo completo de regalos sin bloquear la interfaz."""
        client = getattr(self, 'client_tiktok', None)
        if client is None:
            # Sin Live conectado usamos el catálogo inicial local.
            # Al conectar, TikTokLive lo reemplaza/actualiza con el catálogo real disponible.
            self.actualizar_catalogo_regalos(catalogo_regalos_inicial())
            self.agregar_log('Catálogo inicial cargado sin conectar al Live.')
            return

        def trabajador():
            try:
                loop = getattr(client, '_asyncio_loop', None)
                web_client = getattr(client, 'web', None)
                metodo = getattr(web_client, 'fetch_gift_list', None) if web_client else None
                catalogo = None

                if loop is not None and metodo is not None:
                    import asyncio as _asyncio
                    future = _asyncio.run_coroutine_threadsafe(metodo(), loop)
                    datos = future.result(timeout=15)

                    class Caja:
                        pass
                    caja = Caja()
                    caja.gift_info = datos
                    catalogo = extraer_catalogo_regalos_tiktok(caja)

                if not catalogo:
                    catalogo = extraer_catalogo_regalos_tiktok(client)

                self.root.after(0, lambda c=catalogo: self.actualizar_catalogo_regalos(c))
            except Exception as e:
                self.root.after(0, lambda err=e: self.agregar_log(f'⚠ Error al actualizar catálogo: {err}'))

        threading.Thread(target=trabajador, daemon=True).start()

    def programar_actualizacion_regalos(self):
        """Actualiza periódicamente el catálogo para detectar regalos nuevos."""
        try:
            if getattr(self, 'conectado', False) and getattr(self, 'client_tiktok', None):
                self.actualizar_catalogo_desde_tiktok()
        except Exception:
            pass
        try:
            self._timer_regalos = self.root.after(300000, self.programar_actualizacion_regalos)
        except Exception:
            pass

    def obtener_sonido_alerta_regalo(self,nombre_regalo):
        objetivo=nombre_regalo_normalizado(nombre_regalo)
        for registro in getattr(self,'alertas_regalos_personalizadas',[]):
            try:
                if registro['activar_var'].get() and nombre_regalo_normalizado(registro['combo'].get())==objetivo: return registro['entry'].get().strip()
            except Exception: pass
        return ''

    def obtener_datos_emote(self, emote):
        """Obtiene image.url_list[0] y emote_id del emote."""
        url, emote_id = '', ''
        try:
            image = getattr(emote, 'image', None)
            urls = getattr(image, 'url_list', None)
            if isinstance(urls, (list, tuple)) and urls:
                url = str(urls[0] or '').strip()
            elif isinstance(urls, str):
                url = urls.strip()
        except Exception: pass
        try: emote_id = str(getattr(emote, 'emote_id', '') or '').strip()
        except Exception: pass
        try:
            data = getattr(emote, '__dict__', {}) or {}
            if isinstance(data, dict):
                if not url and isinstance(data.get('image'), dict):
                    urls = data['image'].get('url_list') or data['image'].get('urlList') or []
                    if isinstance(urls, (list, tuple)) and urls: url = str(urls[0] or '').strip()
                if not emote_id: emote_id = str(data.get('emote_id') or data.get('emoteId') or '').strip()
        except Exception: pass
        return url, emote_id

    def registrar_emote_catalogo(self, emote):
        url, emote_id = self.obtener_datos_emote(emote)
        clave = url or emote_id
        if not clave: return None
        for item in self.catalogo_emotes_personalizados:
            if item.get('key') == clave: return item
        item = {'key': clave, 'id': emote_id, 'url': url, 'name': f'Emote {emote_id}' if emote_id else 'Emote personalizado'}
        self.catalogo_emotes_personalizados.append(item)
        self.actualizar_catalogo_emotes()
        return item

    def actualizar_catalogo_emotes(self):
        nombres = sorted({x['name'] for x in getattr(self,'catalogo_emotes_personalizados',[]) if x.get('name')}, key=str.casefold)
        for r in getattr(self,'alertas_emotes_personalizadas',[]):
            actual=r['combo'].get().strip(); valores=list(nombres)
            if actual and actual not in valores: valores.append(actual)
            r['combo']['values']=valores
        try: self.lbl_catalogo_emotes.config(text=f' {len(nombres)} emotes detectados' if nombres else ' Esperando emotes del Live...')
        except Exception: pass

    def cargar_alertas_emotes_personalizadas(self):
        guardadas=config.get('alertas_emotes_personalizadas',[]) or []
        if not isinstance(guardadas,list): guardadas=[]
        for a in guardadas:
            if isinstance(a,dict):
                self.agregar_alerta_emote(
                    a.get('emote',''),
                    a.get('url',''),
                    a.get('emote_id',''),
                    a.get('activar',True),
                    a.get('nombre','')
                )

    def agregar_alerta_emote(self, emote='', url='', emote_id='', activar=True, nombre=''):
        fila=ttk.Frame(self.frame_emotes_personalizados); fila.pack(fill='x',pady=2)
        activa_var=tk.BooleanVar(value=bool(activar))
        ttk.Checkbutton(fila,text='ON',variable=activa_var).pack(side='left',padx=(0,4))

        nombres=[x['name'] for x in getattr(self,'catalogo_emotes_personalizados',[]) if x.get('name')]
        if emote and emote not in nombres: nombres.append(emote)
        combo=ttk.Combobox(
            fila,
            values=sorted(set(nombres),key=str.casefold),
            state='readonly',
            width=20
        )
        combo.set(emote or (nombres[0] if nombres else ''))
        combo.pack(side='left',padx=2)

        # Nombre personalizado que verá el usuario en la configuración.
        entry_nombre=tk.Entry(
            fila,bg='#11111b',fg='#cdd6f4',insertbackground='white',
            font=(self.fuente_actual,8),relief='flat',width=16
        )
        entry_nombre.insert(0,nombre)
        entry_nombre.pack(side='left',padx=4)

        entry=tk.Entry(
            fila,bg='#11111b',fg='#cdd6f4',insertbackground='white',
            font=(self.fuente_actual,8),relief='flat'
        )
        entry.insert(0,url)
        entry.pack(side='left',fill='x',expand=True,padx=4)

        tk.Button(
            fila,text='Subir Local',width=3,bg='#89b4fa',fg='#11111b',relief='flat',
            font=(self.fuente_actual,8,'bold'),
            command=lambda e=entry: seleccionar_audio_local(e)
        ).pack(side='left',padx=2)
        tk.Button(
            fila,text='▶',width=3,bg='#89b4fa',fg='#11111b',relief='flat',
            font=(self.fuente_actual,8,'bold'),
            command=lambda e=entry: reproducir_sonido_url(e.get().strip())
        ).pack(side='left',padx=2)

        registro={
            'frame':fila,
            'activar_var':activa_var,
            'combo':combo,
            'nombre':entry_nombre,
            'entry':entry,
            'url':url,
            'emote_id':emote_id
        }

        def eliminar():
            fila.destroy()
            try: self.alertas_emotes_personalizadas.remove(registro)
            except ValueError: pass

        tk.Button(
            fila,text='✕',width=3,bg='#f38ba8',fg='#11111b',relief='flat',
            font=(self.fuente_actual,8,'bold'),command=eliminar
        ).pack(side='left',padx=2)
        self.alertas_emotes_personalizadas.append(registro)

    def obtener_alerta_emote(self, emote):
        url, emote_id = self.obtener_datos_emote(emote)
        url=str(url or '').strip()
        emote_id=str(emote_id or '').strip()
        for r in getattr(self,'alertas_emotes_personalizadas',[]):
            try:
                if not r['activar_var'].get(): continue

                # Primero comparamos directamente los datos guardados del emote.
                guardado_id=str(r.get('emote_id') or '').strip()
                guardado_url=str(r.get('url') or '').strip()
                if guardado_id and emote_id and guardado_id == emote_id:
                    return r['entry'].get().strip()
                if guardado_url and url and guardado_url == url:
                    return r['entry'].get().strip()

                # Compatibilidad con emotes descubiertos durante el Live.
                seleccionado=r['combo'].get().strip()
                item=next((x for x in self.catalogo_emotes_personalizados if x.get('name')==seleccionado),None)
                if item:
                    item_id=str(item.get('id') or '').strip()
                    item_url=str(item.get('url') or '').strip()
                    if (item_id and emote_id and item_id == emote_id) or (item_url and url and item_url == url):
                        return r['entry'].get().strip()
            except Exception: pass
        return ''

    def guardar_alertas_emotes_personalizadas(self):
        resultado=[]
        for r in getattr(self,'alertas_emotes_personalizadas',[]):
            try:
                seleccionado=r['combo'].get().strip()
                nombre=r['nombre'].get().strip()
                if not seleccionado and not r['emote_id'] and not r.get('url'): continue
                item=next((x for x in self.catalogo_emotes_personalizados if x.get('name')==seleccionado),{})
                resultado.append({
                    'emote':seleccionado,
                    'nombre':nombre,
                    'url':r['entry'].get().strip(),
                    'emote_id':str(item.get('id') or r.get('emote_id') or ''),
                    'emote_image_url':str(item.get('url') or r.get('url') or ''),
                    'activar':bool(r['activar_var'].get())
                })
            except Exception: pass
        return resultado

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
            'no_leer_usuario': self.no_leer_usuario.get(),
            'no_leer_respuestas': self.no_leer_respuestas.get(),
            'lista_blanca': self.entry_lista.get(),
            'alerta_regalos': self.alerta_regalos.get(),
            'agradecer_regalos': self.agradecer_regalos.get(),
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
            'alertas_regalos_personalizadas': [
                {'regalo': r['combo'].get().strip(), 'sonido': r['entry'].get().strip(), 'activar': bool(r['activar_var'].get())}
                for r in getattr(self,'alertas_regalos_personalizadas',[]) if r['combo'].get().strip()
            ],
            'alertas_emotes_personalizadas': self.guardar_alertas_emotes_personalizadas(),
            'fuente_interfaz': self.fuente_actual,
        }

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
        gui.agregar_log(f'➥ {mensaje}')
    except queue.Full:
        gui.agregar_log('⚠ Cola llena')
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
def es_respuesta_a_otro_usuario(event, comentario=""):
    """Detecta respuestas y comentarios dirigidos a otro usuario mediante @mencion.

    Además de los campos de respuesta de TikTokLive, se revisa el texto del comentario.
    Esto permite bloquear casos como: "@patobot hola" o "@usuario hola", aunque
    la versión de TikTokLive no exponga el dato de respuesta en el evento.
    """
    # Si el texto contiene una @mención, se considera un comentario dirigido a otro usuario.
    # Ejemplos: "@patobot hola", "hola @patobot".
    try:
        if comentario and re.search(r"(?:^|\s)@[\w.\-]+", str(comentario), re.UNICODE):
            return True
    except Exception:
        pass

    # Indicadores booleanos explícitos.
    for attr in ("is_reply", "is_reply_comment", "is_reply_to_comment"):
        try:
            value = getattr(event, attr, None)
            if value is True:
                return True
        except Exception:
            pass

    # Referencias directas al comentario/usuario padre.
    reply_attrs = (
        "reply_to", "reply_to_user", "reply_to_comment", "reply_to_message",
        "parent_comment", "parent_message", "parent", "reply", "reply_info",
        "reply_data", "reply_to_id", "reply_id", "parent_id"
    )
    for attr in reply_attrs:
        try:
            value = getattr(event, attr, None)
            if value not in (None, "", 0, False, [], {}, ()):
                return True
        except Exception:
            pass

    # Algunas versiones guardan la información dentro de diccionarios/objetos internos.
    try:
        data = getattr(event, "__dict__", {}) or {}
        for key, value in data.items():
            key_norm = str(key).lower()
            if any(term in key_norm for term in ("reply", "parent")):
                if value not in (None, "", 0, False, [], {}, ()):
                    return True
    except Exception:
        pass

    return False

def iniciar_tiktok(unique_id, connection_id):
    retry_delay = 2.0
    while True:
        if getattr(gui, 'tiktok_stop_requested', False) or connection_id != getattr(gui, 'tiktok_connection_id', connection_id):
            return
        try:
            clean_id = re.sub(r"\s+", "", str(unique_id or "")).lstrip("@").strip()
            if not clean_id:
                raise ValueError('Usuario de TikTok vacío')
            if getattr(gui, 'tiktok_stop_requested', False) or connection_id != getattr(gui, 'tiktok_connection_id', connection_id):
                return
            gui.actualizar_estado(f'Conectando a @{clean_id}...', '#f9e2af')
            gui.client_tiktok = TikTokLiveClient(unique_id=clean_id)
            @gui.client_tiktok.on(ConnectEvent)
            async def on_connect(event: ConnectEvent):
                global CONTADOR_LIKES_GENERAL
                global TIEMPO_INICIO
                if getattr(gui, 'tiktok_stop_requested', False) or connection_id != getattr(gui, 'tiktok_connection_id', connection_id):
                    return
                gui.conectado = True
                gui.tiempo_conexion_inicio = time.time()
                TIEMPO_INICIO = time.time()
                CONTADOR_LIKES_GENERAL = 0
                LIKES_POR_USUARIO.clear()
                DONACIONES_POR_USUARIO.clear()
                LIKES_META_POR_USUARIO.clear()
                AVATARES_POR_USUARIO.clear()
                NOMBRES_POR_USUARIO.clear()
                HISTORIAL_RECIENTE.clear()
                gui.actualizar_estado(f'Conectado a @{clean_id}', '#a6e3a1')
                gui.agregar_log(f'( •)< Conectado exitosamente al Live @{clean_id}')
                gui.root.after(500, gui.actualizar_catalogo_desde_tiktok)
                gui.root.after(2000, gui.actualizar_catalogo_desde_tiktok)
                gui.root.after(2500, gui.programar_actualizacion_regalos)
            @gui.client_tiktok.on(RoomUserSeqEvent)
            async def on_room_user_seq(event: RoomUserSeqEvent):
                if not gui.conectado:
                    return
                # TikTokLive puede cambiar el nombre del campo según la versión.
                viewers = (
                    getattr(event, 'viewer_count', None)
                    or getattr(event, 'total', None)
                    or getattr(event, 'total_user_count', None)
                    or getattr(event, 'user_count', None)
                    or getattr(event, 'online_user_count', None)
                    or getattr(event, 'member_count', None)
                )
                if viewers is None:
                    data = getattr(event, '__dict__', {}) or {}
                    for key in ('viewer_count', 'total', 'total_user_count', 'user_count', 'online_user_count', 'member_count'):
                        if data.get(key) is not None:
                            viewers = data.get(key)
                            break
                try:
                    STATS['viewers'] = max(0, int(viewers))
                    gui.actualizar_metricas_ui()
                except (ValueError, TypeError):
                    pass

            @gui.client_tiktok.on(CommentEvent)
            async def on_comment(event: CommentEvent):
                # Los emotes tambien pueden llegar dentro de CommentEvent.emotes.
                # Los procesamos aqui para que aparezcan en el ComboBox en cuanto
                # alguien envie un emote, incluso si TikTok no emite EmoteChatEvent.
                if gui.conectado and getattr(event, 'emotes', None):
                    try:
                        await procesar_emote_personalizado(event)
                    except Exception as e:
                        gui.agregar_log(f'[Error Emote en comentario]: {e}')
                # ***<module>.iniciar_tiktok.on_comment: Failure: Different control flow
                if not gui.conectado:
                    return
                else:
                    user = event.user
                    username = str(getattr(user, 'unique_id', getattr(user, 'unique_id_str', ''))).lower()
                    nickname = str(getattr(user, 'nickname', username))
                    nombre_visible = obtener_nombre_usuario(user)
                    comentario = event.comment.strip()
                    if gui.no_leer_respuestas.get() and es_respuesta_a_otro_usuario(event, comentario):
                        gui.agregar_log(f'[FILTRO] Respuesta de  {normalizar_texto(username)} omitida.')
                        return
                    if time.time() - TIEMPO_INICIO < 2:
                        return
                    else:
                        if comentario.startswith('!'):
                            if (comentario, nickname or username, user):
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
                            # ANTISPAM: elimina repeticiones consecutivas de la misma palabra.
                            # Ejemplo: "hola hola hola hola" -> "hola".
                            palabras = comentario.split()
                            reducidas = []
                            ultima_palabra = None
                            for palabra in palabras:
                                clave = palabra.casefold().strip('.,!?¿¡:;')
                                if clave != ultima_palabra:
                                    reducidas.append(palabra)
                                    ultima_palabra = clave
                            comentario = ' '.join(reducidas)

                            id_mensaje = f'{username}:{comentario}'
                            if id_mensaje in HISTORIAL_RECIENTE:
                                return
                            else:
                                HISTORIAL_RECIENTE.append(id_mensaje)
                                nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=0) or 'Usuario'
                                try:
                                    max_chars = int(gui.entry_limite.get())
                                except ValueError:
                                    max_chars = 100
                                comentario_recortado = comentario[:max_chars]
                                dicc_reemplazos = gui.obtener_diccionario_reemplazos()
                                comentario_procesado = aplicar_diccionario_reemplazos(comentario_recortado, dicc_reemplazos)
                                comentario_normalizado = extraer_o_limpiar_emojis(comentario_procesado, max_emojis=1)
                                STATS['comentarios'] += 1
                                gui.actualizar_metricas_ui()
                                if gui.no_leer_usuario.get():
                                    enviar_a_voz(comentario_normalizado)
                                else:
                                    enviar_a_voz(f'{nombre_limpio} dice: {comentario_normalizado}')
            async def procesar_emote_personalizado(event):
                if not gui.conectado: return
                user=getattr(event,'user',None)
                username=str(getattr(user,'unique_id',getattr(user,'unique_id_str','')) or '').lower().strip()
                nickname=str(getattr(user,'nickname',username) or username)
                nombre_limpio=extraer_o_limpiar_emojis(nickname,max_emojis=0) or 'Usuario'
                emotes=getattr(event,'emote_list',None) or getattr(event,'emotes',None) or getattr(event,'emote',None) or []
                if not isinstance(emotes,(list,tuple,set)): emotes=[emotes]
                vistos=set()
                for item in emotes:
                    try:
                        # En CommentEvent, TikTokLive entrega EmoteWithIndex;
                        # el emote real está dentro de item.emote.
                        emote=getattr(item,'emote',None) or item
                        url,emote_id=gui.obtener_datos_emote(emote); clave=url or emote_id
                        if not clave or clave in vistos: continue
                        vistos.add(clave); gui.registrar_emote_catalogo(emote)
                        sonido=gui.obtener_alerta_emote(emote)
                        if not sonido: continue
                        key=(username,clave); ahora=time.monotonic()
                        if ahora-ULTIMAS_ALERTAS_EMOTE.get(key,0.0)<5.0: continue
                        ULTIMAS_ALERTAS_EMOTE[key]=ahora
                        reproducir_sonido_url(sonido)
                        gui.agregar_log(f'Emote personalizado de {nombre_limpio} activado (ID: {emote_id or "sin ID"})')
                    except Exception as e: gui.agregar_log(f'[Error Emote]: {e}')

            if EmoteChatEvent is not None:
                @gui.client_tiktok.on(EmoteChatEvent)
                async def on_emote_chat(event: EmoteChatEvent):
                    await procesar_emote_personalizado(event)

            def permitir_alerta_regalo_antispam(username, regalo):
                """Permite una alerta por regalo/usuario dentro de una ventana corta.

                Los regalos siguen contabilizándose y apareciendo en el log;
                únicamente se evita reproducir repetidamente el sonido de alerta.
                """
                ahora = time.monotonic()
                clave = (
                    str(username or '').casefold().strip(),
                    nombre_regalo_normalizado(regalo)
                )

                ultimo = ULTIMAS_ALERTAS_REGALO.get(clave, 0.0)
                if ahora - ultimo < ANTISPAM_REGALOS_SEGUNDOS:
                    return False

                ULTIMAS_ALERTAS_REGALO[clave] = ahora

                # Limpieza ligera para que el diccionario no crezca durante Lives largos.
                if len(ULTIMAS_ALERTAS_REGALO) > 500:
                    limite = ahora - (ANTISPAM_REGALOS_SEGUNDOS * 4)
                    for k, t in list(ULTIMAS_ALERTAS_REGALO.items()):
                        if t < limite:
                            ULTIMAS_ALERTAS_REGALO.pop(k, None)

                return True

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
                        nombre_limpio = obtener_nombre_usuario(event.user)
                        if nombre_limpio == 'Usuario':
                            nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or 'Usuario'
                        avatar_url = obtener_avatar_usuario(event.user)
                        username = str(getattr(event.user, 'unique_id', getattr(event.user, 'unique_id_str', '')) or '').lower()
                        if avatar_url and username:
                            AVATARES_POR_USUARIO[username] = avatar_url
                        regalo = getattr(event.gift, 'name', 'un regalo')
                        try:
                            if regalo and not any(nombre_regalo_normalizado(x.get('name')) == nombre_regalo_normalizado(regalo) for x in getattr(gui,'catalogo_regalos',[])):
                                gui.catalogo_regalos.append({'id':str(getattr(event.gift,'id',regalo)),'name':regalo})
                                gui.root.after(0,lambda: gui.actualizar_catalogo_regalos(gui.catalogo_regalos))
                        except Exception: pass
                        cantidad = getattr(event, 'repeat_count', 1) or getattr(event.gift, 'count', 1)
                        try:
                            cantidad = max(1, int(cantidad))
                        except (TypeError, ValueError):
                            cantidad = 1

                        # Valor del regalo para el ranking de donadores.
                        # Se prueban los nombres usados por distintas versiones de TikTokLive.
                        valor_unitario = 0
                        for obj in (event.gift, event):
                            for attr in ('diamond_count', 'diamondCount', 'coins', 'coin_count', 'coinCount'):
                                try:
                                    valor = getattr(obj, attr, None)
                                    if valor is not None:
                                        valor_unitario = int(float(valor))
                                        if valor_unitario > 0:
                                            break
                                except (TypeError, ValueError):
                                    pass
                            if valor_unitario > 0:
                                break

                        monedas = max(0, valor_unitario * cantidad)
                        if username and monedas > 0:
                            DONACIONES_POR_USUARIO[username] += monedas

                        STATS['regalos'] += cantidad
                        ULTIMO_REGALO = {'user': nombre_limpio, 'gift': regalo, 'count': cantidad, 'coins': monedas}
                        ULTIMA_ACCION = {
                            'id': f'gift-{time.time_ns()}',
                            'type': 'gift',
                            'name': nombre_limpio,
                            'avatar': avatar_url or AVATARES_POR_USUARIO.get(username, ''),
                            'message': f'🎁 {nombre_limpio} envió x{cantidad} {regalo}',
                            'icon': '🎁',
                            'expires_at': time.time() + 5
                        }
                        gui.actualizar_metricas_ui()
                        broadcast_overlay_data()
                        gui.agregar_log(f'Ⰶ {nombre_limpio} envió x{cantidad} {regalo}')
                        # ANTISPAM DE ALERTAS DE REGALOS
                        # El regalo y sus estadísticas NO se bloquean. Solo se
                        # bloquea la reproducción repetida de la alerta sonora.
                        permitir_sonido = permitir_alerta_regalo_antispam(username, regalo)

                        if permitir_sonido:
                            if gui.alerta_regalos.get():
                                url = gui.entry_url_regalo.get().strip()
                                if url:
                                    reproducir_sonido_url(url)

                            sonido_regalo = gui.obtener_sonido_alerta_regalo(regalo)
                            if sonido_regalo:
                                reproducir_sonido_url(sonido_regalo)

                            # Agradecimiento por voz independiente de las alertas de sonido.
                            # ON: agradece; OFF: no dice el agradecimiento.
                            if gui.agradecer_regalos.get():
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
                    username = str(getattr(event.user, 'unique_id', getattr(event.user, 'unique_id_str', '')) or '').lower()
                    avatar_url = obtener_avatar_usuario(event.user)
                    if avatar_url and username:
                        AVATARES_POR_USUARIO[username] = avatar_url
                    nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or 'Usuario'
                    STATS['follows'] += 1
                    ULTIMO_SEGUIDOR = nombre_limpio
                    ULTIMA_ACCION = {
                        'id': f'follow-{time.time_ns()}',
                        'type': 'follow',
                        'name': nombre_limpio,
                        'avatar': avatar_url or AVATARES_POR_USUARIO.get(username, ''),
                        'message': f'💙 ¡Gracias {nombre_limpio} por seguir!',
                        'icon': '💙',
                        'expires_at': time.time() + 5
                    }
                    gui.actualizar_metricas_ui()
                    broadcast_overlay_data()
                    gui.agregar_log(f'{nombre_limpio} te ha seguido')
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
                    nombre_limpio = obtener_nombre_usuario(user)
                    if nombre_limpio == 'Usuario':
                        nombre_limpio = extraer_o_limpiar_emojis(nickname, max_emojis=1) or normalizar_texto(username) or 'Usuario'
                    avatar_url = obtener_avatar_usuario(user)
                    if avatar_url:
                        AVATARES_POR_USUARIO[username] = avatar_url
                    LIKES_POR_USUARIO[username] += likes_recibidos
                    gui.actualizar_metricas_ui()

                    # La acción de Likes se sincroniza con la meta individual:
                    # 50, 100, 150... según la meta configurada.
                    like_goal_reached = False
                    reached_milestone = 0

                    if gui.alerta_likes_persona.get():
                        meta_persona = max(1, gui.obtener_meta_likes_persona())
                        progreso_anterior = LIKES_META_POR_USUARIO[username]
                        progreso_nuevo = progreso_anterior + likes_recibidos

                        if gui.repetir_likes_persona.get():
                            metas_antes = progreso_anterior // meta_persona
                            metas_despues = progreso_nuevo // meta_persona
                            if metas_despues > metas_antes:
                                like_goal_reached = True
                                reached_milestone = metas_despues * meta_persona
                            LIKES_META_POR_USUARIO[username] = progreso_nuevo % meta_persona
                        elif progreso_nuevo >= meta_persona:
                            like_goal_reached = True
                            reached_milestone = meta_persona
                            LIKES_META_POR_USUARIO[username] = meta_persona
                        else:
                            LIKES_META_POR_USUARIO[username] = progreso_nuevo

                    # Mis Acciones solo muestra Likes cuando se alcanza la meta.
                    if like_goal_reached:
                        ULTIMA_ACCION = {
                            'id': f'like-goal-{time.time_ns()}',
                            'type': 'like',
                            'name': nombre_limpio,
                            'avatar': avatar_url,
                            'message': f'❤️ ¡{nombre_limpio} alcanzó {reached_milestone:,} likes!',
                            'icon': '❤️',
                            'likes_count': likes_recibidos,
                            'total_likes': LIKES_POR_USUARIO[username],
                            'goal_milestone': reached_milestone,
                            'expires_at': time.time() + 5
                        }

                    if gui.alerta_likes_general.get():
                        meta_general = gui.obtener_meta_likes_general()
                        CONTADOR_LIKES_GENERAL += likes_recibidos
                        if CONTADOR_LIKES_GENERAL >= meta_general:
                            gui.agregar_log(f'ᰔᩚ Meta alcanzada: {meta_general} likes!')
                            url_gen = gui.entry_url_like_general.get().strip()
                            if url_gen:
                                reproducir_sonido_url(url_gen)
                            if gui.repetir_likes_general.get():
                                CONTADOR_LIKES_GENERAL %= meta_general
                            else:
                                gui.alerta_likes_general.set(False)
                    if gui.alerta_likes_persona.get() and like_goal_reached:
                        gui.agregar_log(
                            f'♡ @{normalizar_texto(username)} alcanzó {reached_milestone} likes'
                        )
                        url_per = gui.entry_url_like_persona.get().strip()
                        if url_per:
                            reproducir_sonido_url(url_per)

                        if not gui.repetir_likes_persona.get():
                            gui.alerta_likes_persona.set(False)
                    meta_actual = max(1, gui.obtener_meta_likes_persona())
                    ULTIMO_LIKE_META = {
                        'name': nombre_limpio,
                        'progress': LIKES_META_POR_USUARIO[username],
                        'total': LIKES_POR_USUARIO[username],
                        'target': meta_actual,
                        'goal_reached': like_goal_reached,
                        'goal_milestone': reached_milestone
                    }
                    broadcast_overlay_data()
            gui.client_tiktok.run(fetch_gift_info=True)
            if getattr(gui, 'tiktok_stop_requested', False) or connection_id != getattr(gui, 'tiktok_connection_id', connection_id):
                return
            # Algunos cierres de websocket pueden terminar run() sin lanzar excepción.
            gui.conectado = False
            gui.tiempo_conexion_inicio = None
            gui.agregar_log('[TikTok] La conexión terminó; intentando reconectar...')
            gui.actualizar_estado('Reconectando...', '#f9e2af')
            gui.client_tiktok = None
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 20.0)
        except Exception as e:
            if getattr(gui, 'tiktok_stop_requested', False) or connection_id != getattr(gui, 'tiktok_connection_id', connection_id):
                return
            gui.conectado = False
            gui.tiempo_conexion_inicio = None
            gui.client_tiktok = None
            gui.agregar_log(f'[TikTok] Conexión perdida: {e}')
            gui.actualizar_estado('Reconectando...', '#f9e2af')
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 20.0)

gui.root.mainloop()