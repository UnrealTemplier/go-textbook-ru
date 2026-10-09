"""Тесты ядра: python -m unittest discover -s engine/tests -t .

Демо-книга (book.toml, demo-sources/) есть только в корне репозитория html-textbook-engine;
в книге, куда ядро пришло через engine.sync, тесты демо пропускаются.
"""
import os

DEMO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HAS_DEMO = os.path.isdir(os.path.join(DEMO_ROOT, "demo-sources")) and os.path.isfile(os.path.join(DEMO_ROOT, "book.toml"))
