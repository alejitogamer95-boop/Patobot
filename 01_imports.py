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
from flask import Flask, render_template_string, Response, request
