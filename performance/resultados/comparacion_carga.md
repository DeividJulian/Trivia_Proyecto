| Escenario | Peticiones REST | p95 REST (ms) | Mediana (ms) | Fallos (%) | Peticiones/s | CPU Locust máx. (%) | CPU servidor máx. (%) | WS conexiones (fallidas) | WS mensajes (por s) | WS difusión p50 / p95 (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REST · uvicorn local | 4914 | 56 | 6 | 0.00 | 41.3 | 38 | 20 | — | — | — |
| REST+WS · uvicorn local | 5015 | 38 | 6 | 0.00 | 42.1 | 43 | 24 | 48 (0) | 17081 (257) | 14 / 36 |
| REST · contenedor Alpine | 4978 | 14 | 6 | 0.00 | 41.9 | 37 | 56 | — | — | — |
| REST+WS · contenedor Alpine | 4701 | 79 | 9 | 0.00 | 39.6 | 48 | 59 | 48 (0) | 18896 (266) | 22 / 624 |
