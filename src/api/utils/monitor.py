from logging import ERROR, getLogger, basicConfig

basicConfig(level = ERROR, format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = getLogger("WebSocket")