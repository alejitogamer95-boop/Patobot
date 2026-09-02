threading.Thread(target=run_flask_server, daemon=True).start()
try:
    gui.root.after(1000, gui.actualizar_dispositivos_spotify)
except Exception:
    pass

if __name__ == "__main__":
    gui.root.mainloop()
