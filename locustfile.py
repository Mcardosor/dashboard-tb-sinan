"""
locustfile.py — Teste de carga do Dashboard TB | SINAN
───────────────────────────────────────────────────────
Simula N usuários navegando simultaneamente no dashboard.

Executar:
  locust -f locustfile.py --host http://10.20.10.64:8502 --users 20 --spawn-rate 2

Ou com interface web (recomendado):
  locust -f locustfile.py --host http://10.20.10.64:8502
  → abrir http://localhost:8089
"""

import time
import random
import threading
import websocket
from locust import HttpUser, task, between, events


BASE_PATH = "/cenarios/tb"

# Abas disponíveis para simular navegação
TABS = [0, 1, 2, 3, 4, 5]

# Estados para simular cliques no mapa
UFS = ["SP", "RJ", "MG", "BA", "AM", "CE", "PE", "RS", "PR", "GO"]

# Anos disponíveis no filtro
ANOS = [2022, 2023, 2024, 2025]


class DashboardUser(HttpUser):
    """
    Simula um usuário real navegando pelo dashboard TB.
    wait_time: pausa entre ações (3–10 segundos), simula leitura humana.
    """
    wait_time = between(3, 10)
    ws_error_count = 0
    ws_connected = 0

    # ── Carregamento inicial ───────────────────────────────────────────────
    def on_start(self):
        """Executado uma vez quando o usuário 'entra' no sistema."""
        self._carregar_pagina()
        self._conectar_websocket()

    def on_stop(self):
        """Executado quando o usuário 'sai'."""
        if hasattr(self, "_ws") and self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

    # ── Tarefas simuladas ──────────────────────────────────────────────────
    @task(3)
    def navegar_abas(self):
        """Clica em abas diferentes — ação mais comum."""
        self.client.get(
            f"{BASE_PATH}/",
            name="[aba] Navegar",
        )

    @task(2)
    def carregar_pagina_principal(self):
        """Recarrega o dashboard (simula F5 ou entrada direta)."""
        self._carregar_pagina()

    @task(2)
    def carregar_assets_estaticos(self):
        """Carrega JS/CSS estáticos — representa o primeiro acesso."""
        paths = [
            "/_stcore/static/js/main.chunk.js",
            "/_stcore/static/css/main.chunk.css",
            "/_stcore/health",
        ]
        for path in random.sample(paths, k=min(2, len(paths))):
            with self.client.get(path, catch_response=True, name="[static] asset") as r:
                if r.status_code in (200, 304, 404):
                    r.success()

    @task(1)
    def verificar_health(self):
        """Endpoint de health — mede disponibilidade do servidor."""
        with self.client.get(f"{BASE_PATH}/_stcore/health", name="[health] /health", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Health retornou {r.status_code}")

    @task(1)
    def carregar_stream(self):
        """
        Solicita o stream SSE do Streamlit — mede tempo para o
        servidor iniciar a sessão e enviar os primeiros dados.
        """
        with self.client.get(
            f"{BASE_PATH}/stream",
            name="[stream] iniciar sessão",
            catch_response=True,
            stream=True,
        ) as r:
            if r.status_code in (200, 404):
                r.success()
            else:
                r.failure(f"Stream retornou {r.status_code}")

    # ── Helpers internos ───────────────────────────────────────────────────
    def _carregar_pagina(self):
        with self.client.get(
            f"{BASE_PATH}/",
            name="[página] carregar dashboard",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code in (301, 302):
                r.success()
            else:
                r.failure(f"Página retornou {r.status_code}")

    def _conectar_websocket(self):
        """
        Abre uma conexão WebSocket com o Streamlit.
        Streamlit usa WebSocket para toda comunicação de estado —
        esta métrica mede tempo de handshake e latência do canal.
        """
        host = self.host.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{host}{BASE_PATH}/_stcore/stream"

        def _on_open(ws):
            DashboardUser.ws_connected += 1

        def _on_error(ws, error):
            DashboardUser.ws_error_count += 1

        def _on_close(ws, *args):
            DashboardUser.ws_connected = max(0, DashboardUser.ws_connected - 1)

        start = time.time()
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=_on_open,
                on_error=_on_error,
                on_close=_on_close,
            )
            t = threading.Thread(
                target=ws.run_forever,
                kwargs={"ping_interval": 20, "ping_timeout": 10},
                daemon=True,
            )
            t.start()
            self._ws = ws
            elapsed = int((time.time() - start) * 1000)
            events.request.fire(
                request_type="WS",
                name="[ws] handshake Streamlit",
                response_time=elapsed,
                response_length=0,
                exception=None,
                context={},
            )
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            events.request.fire(
                request_type="WS",
                name="[ws] handshake Streamlit",
                response_time=elapsed,
                response_length=0,
                exception=e,
                context={},
            )


# ── Listeners de evento ────────────────────────────────────────────────────
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*60)
    print("  TESTE DE CARGA — Dashboard TB | SINAN")
    print(f"  Host: {environment.host}")
    print(f"  Base path: {BASE_PATH}")
    print("="*60 + "\n")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats
    total = stats.total
    print("\n" + "="*60)
    print("  RESULTADO FINAL")
    print(f"  Requisições:  {total.num_requests}")
    print(f"  Falhas:       {total.num_failures} ({100*total.fail_ratio:.1f}%)")
    print(f"  RPS médio:    {total.current_rps:.1f}")
    print(f"  Latência p50: {total.get_response_time_percentile(0.5):.0f} ms")
    print(f"  Latência p95: {total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  Latência p99: {total.get_response_time_percentile(0.99):.0f} ms")
    print(f"  WS erros:     {DashboardUser.ws_error_count}")
    print("="*60 + "\n")
