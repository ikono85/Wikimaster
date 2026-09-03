"""Dashboard local (Flask) pour piloter le bot d'ouverture de paquets."""

from flask import Flask, jsonify, redirect, render_template, request, url_for

from . import browser, storage
from .config import STRATEGIES, load_config, save_config
from .scheduler import scheduler

app = Flask(__name__)


@app.route("/")
def index():
    cfg = load_config()
    return render_template(
        "index.html",
        cfg=cfg,
        strategies=STRATEGIES,
        running=scheduler.running,
        has_session=browser.has_saved_session(),
        packs_opened=storage.count_packs_opened(),
        logs=storage.get_recent_logs(limit=40),
    )


@app.route("/settings", methods=["POST"])
def update_settings():
    cfg = load_config()
    cfg.premium = "premium" in request.form
    cfg.max_stock = int(request.form.get("max_stock", cfg.max_stock))
    cfg.strategy = request.form.get("strategy", cfg.strategy)
    cfg.interval_minutes = float(request.form.get("interval_minutes", cfg.interval_minutes))
    cfg.headless = "headless" in request.form
    save_config(cfg)
    return redirect(url_for("index"))


@app.route("/bot/start", methods=["POST"])
def start_bot():
    cfg = load_config()
    cfg.bot_enabled = True
    save_config(cfg)
    scheduler.start(cfg)
    return redirect(url_for("index"))


@app.route("/bot/stop", methods=["POST"])
def stop_bot():
    cfg = load_config()
    cfg.bot_enabled = False
    save_config(cfg)
    scheduler.stop()
    return redirect(url_for("index"))


@app.route("/api/status")
def api_status():
    return jsonify({
        "running": scheduler.running,
        "packs_opened": storage.count_packs_opened(),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
