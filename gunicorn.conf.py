"""
Gunicorn — Production WSGI Server konfiguratsiyasi
===================================================
Ishga tushirish:
    gunicorn -c gunicorn.conf.py backend.wsgi:application
"""
import multiprocessing

# ── WORKERS ────────────────────────────────────────────────
# CPU yadrolari soni × 2 + 1 (klassik formula)
workers      = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'          # 'gevent' yoki 'uvicorn.workers.UvicornWorker' ham bo'lishi mumkin
threads      = 2               # Har bir worker uchun threadlar soni
worker_connections = 1000

# ── TIMEOUTS ────────────────────────────────────────────────
timeout            = 30        # Worker javob berish vaqti (sekund)
graceful_timeout   = 10        # Shutdown vaqti
keepalive          = 5         # Keep-alive ulanishlar

# ── BIND ───────────────────────────────────────────────────
bind = '0.0.0.0:8000'

# ── LOGGING ────────────────────────────────────────────────
accesslog  = 'logs/gunicorn_access.log'
errorlog   = 'logs/gunicorn_error.log'
loglevel   = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(f)s %(a)s %(D)sμs'

# ── PROCESS ────────────────────────────────────────────────
daemon      = False
pidfile     = 'gunicorn.pid'
proc_name   = 'pos_tizim'

# ── PRELOAD ────────────────────────────────────────────────
preload_app = True             # Xotira tejash uchun

# ── HOOKS ──────────────────────────────────────────────────
def on_starting(server):
    server.log.info("POS Tizim ishga tushmoqda...")

def on_exit(server):
    server.log.info("POS Tizim to'xtatildi.")

def worker_exit(server, worker):
    server.log.info(f"Worker {worker.pid} to'xtatildi.")
