import webbrowser
from pathlib import Path

import webview  # pywebview

from app.backend import BackendManager

# Single global manager
backend = BackendManager()

class Api:
	def start(self):
		return backend.start_all()

	def stop(self):
		return backend.stop_all()

	def status(self):
		return backend.status()

	def open_docs(self):
		url = backend.open_docs_url()
		webbrowser.open(url)
		return {"opened": url}

	def open_config(self):
		url = backend.open_config_url()
		webbrowser.open(url)
		return {"opened": url}


def _index_html_path() -> str:
	here = Path(__file__).resolve().parent
	return str(here / "ui" / "index.html")


if __name__ == "__main__":
	# Auto-start on launch
	backend.start_all()

	api = Api()
	window = webview.create_window(
		title="Olympus Desktop",
		url=_index_html_path(),
		width=980,
		height=720,
		resizable=True,
		confirm_close=True,
	)
	webview.start(gui="qt", http_server=False, func=None, debug=False, private_mode=False, http_server_port=None, js_api=api)
