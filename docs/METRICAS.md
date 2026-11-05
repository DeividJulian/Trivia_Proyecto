# Métricas de calidad

Una métrica solo sirve si responde una pregunta y apoya una decisión.

| Métrica | Cómo se obtiene | Pregunta que responde | Decisión que apoya |
|---|---|---|---|
| Pruebas aprobadas por nivel | `pytest -m <nivel> --junitxml` | ¿Funciona cada nivel (componente, integración, sistema, aceptación)? | Una prueba fallida en cualquier nivel bloquea el despliegue |
| Cobertura de líneas y ramas | `pytest --cov=app --cov-report=xml` | ¿Qué parte del código ejecutan las pruebas? | Cobertura < 85 % (RNF-06) bloquea el despliegue y muestra dónde faltan pruebas |
| Mutantes detectados | `scripts/verificar_mutantes.py` | ¿Las pruebas detectan errores reales, o solo pasan? | Un mutante que sobrevive genera un DEF y una prueba nueva (RNF-07) |
| Defectos por módulo y severidad | `docs/REPORTE_DEFECTOS.md` | ¿Dónde se agrupan los defectos? | Más pruebas y revisión en los módulos con más defectos |
| Tiempo de corrección de un defecto | Fecha del DEF vs. commit `fix` | ¿Qué tan rápido reaccionamos? | Si crece, revisar el proceso o la complejidad del módulo |
| p95 del tiempo de respuesta | Locust + `verificar_umbrales.py` | ¿La app es rápida con 50 usuarios? | p95 ≥ 500 ms (RNF-01) es un defecto no funcional |
| % de fallos bajo carga | Locust + `verificar_umbrales.py` | ¿La app es fiable con 50 usuarios? | ≥ 1 % (RNF-02) es un defecto no funcional |
| Punto de quiebre (usuarios) | `performance/punto_quiebre.py` + `analizar_resultados.py` | ¿Cuántos usuarios soporta antes de fallar? | Dimensionar el servidor y priorizar mantenimiento perfectivo |
| Vulnerabilidades HIGH/CRITICAL | Trivy (fs, config e imagen) | ¿Desplegamos componentes con vulnerabilidades conocidas? | Cualquiera bloquea el despliegue (RNF-04) → mantenimiento adaptativo |
| Quality Gate, bugs, code smells y duplicación | SonarQube Cloud | ¿El código nuevo es mantenible y seguro? | Quality Gate en rojo bloquea el despliegue (RNF-05) |
| Pruebas afectadas por un cambio | `scripts/regresion_por_impacto.py` | ¿Qué hay que re-ejecutar tras un cambio? | Regresión selectiva rápida antes de la suite completa |
