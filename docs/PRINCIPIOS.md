# Los 7 principios ISTQB aplicados al proyecto

| # | Principio | Práctica del proyecto que lo aplica |
|---|---|---|
| 1 | **Las pruebas muestran la presencia de defectos, no su ausencia** | Que la suite pase no demuestra que no haya errores. Por eso medimos la efectividad de las pruebas con los mutantes del Saboteador y registramos cada hallazgo como DEF en `REPORTE_DEFECTOS.md`. |
| 2 | **Las pruebas exhaustivas son imposibles** | No probamos todos los tiempos de respuesta posibles: usamos **valores límite** (justo en el límite y una milésima después) y **análisis de impacto** para decidir qué re-ejecutar (`scripts/regresion_por_impacto.py`). |
| 3 | **Probar pronto ahorra tiempo y dinero (shift-left)** | SonarQube for IDE mientras se programa, pre-commit con Ruff antes de cada commit y CI en cada push. Cada función va seguida de su prueba en el commit siguiente. |
| 4 | **Los defectos se agrupan** | El puntaje concentra la lógica más riesgosa (tiempo, racha, bono); allí ponemos más pruebas de valores límite y la mayoría de los mutantes. |
| 5 | **Las pruebas se desgastan (paradoja del pesticida)** | Repetir las mismas pruebas deja de encontrar defectos nuevos. Los **mutantes del Saboteador** obligan a comprobar que las pruebas siguen detectando fallos; si uno sobrevive se escribe una prueba nueva. |
| 6 | **Las pruebas dependen del contexto** | Es un juego en vivo en clase: priorizamos tiempos de respuesta, equidad del ranking y que nadie sin token pueda sabotear, no las reglas de un sistema bancario. |
| 7 | **La ausencia de defectos es una falacia** | Un sistema sin defectos conocidos puede no servirle al usuario: por eso hay **pruebas de aceptación** basadas en historias de usuario y **sesiones exploratorias** manuales. |
