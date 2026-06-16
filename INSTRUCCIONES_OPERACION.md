# Instrucciones de Operación — Job Agent Autónomo
## Adalberto Silveira Napoles — Cowork Job Agent
**Última actualización: 2026-06-15 | v3 — todas las mejoras implementadas**

---

## ✅ Estado del sistema (verificado 2026-06-15)

| Archivo | Líneas | Estado |
|---|---|---|
| `linkedin_agent.py` | 1233 | ✅ v3 — pipeline completo + 14 mejoras |
| `agent_logger.py` | 143 | ✅ OK |
| `ats_updater.py` | 152 | ✅ OK — próxima renovación 2026-07-15 |
| `applications_log.json` | — | ✅ OK — 7 entradas |
| `ats_techniques_cache.json` | — | ✅ OK |
| `SilveiraNapoles-Adalberto-Resume-2026-ATS.docx` | — | ✅ OK (~90-92 ATS score) |
| `AGENT_TASK_PROMPT.md` | — | ✅ OK — actualizado con flujo 3 fases |
| `logs/` | — | ✅ OK |
| `setup_github.ps1` | — | ✅ Listo para publicar en GitHub |

---

## ⏰ Ejecución automática — miércoles 8:00 PM

- **Scheduled Task ID:** `weekly-job-agent-adalberto`
- **Cron:** `0 20 * * 3`
- **Próxima ejecución:** miércoles 2026-06-18 a las 8:00 PM
- **Estado:** HABILITADO ✅

### ▶️⏸️ Activar o pausar la ejecución automática

Puedes controlar el schedule con frases simples en Cowork:

| Acción | Frase |
|---|---|
| **Activar** | "activa el agente programado" |
| **Activar** | "activa la ejecución automática" |
| **Activar** | "habilita el agente" |
| **Pausar** | "pausa el agente" |
| **Pausar** | "desactiva el agente programado" |
| **Pausar** | "suspende el agente" |

Claude actualizará el scheduled task y te confirmará el nuevo estado.
> ⚠️ Estas frases **solo controlan el schedule automático** — no inician ni detienen una ejecución activa.

> 💡 **¿Por qué miércoles 8pm?** El proceso consume muchos tokens y tiempo de procesamiento.
> Las 8pm minimiza interrupciones al usuario y el trabajo publicado durante el día ya está disponible.

### Lo que debes tener activo ANTES de la ejecución (automática o manual):

| Requisito | Cómo verificar |
|---|---|
| **Cowork app** corriendo en background | Ícono en la bandeja del sistema (system tray) |
| **Google Chrome** abierto con **Claude in Chrome** en verde | Ícono de extensión verde en Chrome |
| **LinkedIn** — sesión activa en Chrome | Abre linkedin.com → debe mostrar el feed, no login |
| **Dice** — sesión activa en Chrome | Abre dice.com → debe mostrar tu perfil, no login |
| **ZipRecruiter** — sesión activa en Chrome | Abre ziprecruiter.com → debe mostrar tu perfil, no login |
| **Indeed** — sesión activa en Chrome | Abre indeed.com → debe mostrar tu perfil, no login |

> ⚠️ **No necesitas tener las pestañas abiertas activamente** — solo que la sesión esté guardada
> (cookies activas). Verifica abriendo cada sitio una vez antes de la ejecución.

### Lo que NO necesitas:
- No necesitas estar frente a la computadora durante la ejecución automática
- No necesitas aprobar ninguna acción individual
- No necesitas abrir ninguna app durante la ejecución

---

## 🔄 Flujo de trabajo del agente (4 fases)

### Fase 1 — Pre-vuelo + Búsqueda
1. MCP health check → escribe `logs/mcp_health.json`
2. LinkedIn session check (Chrome navega a linkedin.com/feed)
3. Búsqueda en **Indeed**, **Dice**, **ZipRecruiter** con 5 search terms
4. Filtrado: ubicación 28mi, no liderazgo, no duplicados
5. Escribe resultados a `jobs_input.json`

### Fase 2 — Generación de resumes
```bash
python linkedin_agent.py --jobs-file jobs_input.json
```
Genera por cada trabajo:
- Resume `.docx` personalizado en `resume-personalized/`
- Summary via Claude Haiku con keywords del JD
- Bullets STAR cuantificados
- Skills reordenados por relevancia al JD
- Cover letter `.txt` via Claude Haiku
- Match Score 0-100 (skills del candidato encontrados en JD)
Registra todos como `resume_ready` en `applications_log.json`
Limpia resumes > 90 días al inicio de cada run
Devuelve `run_id` para las siguientes fases

### Fase 3 — LinkedIn Easy Apply
Para cada trabajo LinkedIn:
1. Chrome navega al URL de LinkedIn
2. Click "Easy Apply"
3. Llena formulario + sube resume personalizado
4. Actualiza status en log:
```bash
python linkedin_agent.py --update-status "job_id" applied
```

### Fase 4 — Email de resumen (DESPUÉS del Easy Apply)
```bash
python linkedin_agent.py --build-email --run-id <run_id>
```
Gmail MCP crea borrador con **dos secciones**:
- ✅ **Applied** (Easy Apply completado) — verde, ordenado por Match%
- 📋 **Resume Ready** (manual apply — Indeed/Dice/ZipRecruiter) — naranja
- Columnas: Empresa | Posición | Ubicación | Source | Match% | Salario | Status

---

## ▶️ Ejecución manual

### Opción A — Cowork (recomendado, flujo completo)

Abre una nueva conversación en Cowork y escribe simplemente:

```
ejecuta el agente
```

El sistema reconoce esta frase y automáticamente ejecuta el comando completo:

```
Ejecuta el job agent completo siguiendo las instrucciones en `C:\Dev\agent-linkedin-candidate\AGENT_TASK_PROMPT.md`
```

Claude leerá `AGENT_TASK_PROMPT.md` y ejecutará las 4 fases completas (pre-vuelo, búsqueda, Easy Apply, email).

**Otras frases que también funcionan:**
- "ejecuta el agente manualmente"
- "corre el agente"
- "inicia el agente"
- "ejecuta el job agent"
- "lanza el agente"

> **Para desarrolladores:** el prompt exacto que se ejecuta internamente es:
> `Ejecuta el job agent completo siguiendo las instrucciones en C:\Dev\agent-linkedin-candidate\AGENT_TASK_PROMPT.md`
> La lógica completa está en `AGENT_TASK_PROMPT.md` — ese archivo es la única fuente de verdad del comportamiento del agente.

### Opción B — Terminal (solo Python, sin Easy Apply)
```bash
# Primero pedirle a Claude que busque empleos y genere jobs_input.json
# Luego:
cd C:\Dev\agent-linkedin-candidate

# Generar resumes:
python linkedin_agent.py --jobs-file jobs_input.json

# Después de tu Easy Apply manual, actualizar status:
python linkedin_agent.py --update-status "job-id-aqui" applied

# Generar email con el run_id que devolvió el primer comando:
python linkedin_agent.py --build-email --run-id <run_id>

# Probar sin efectos reales:
python linkedin_agent.py --jobs-file jobs_input.json --dry-run

# Limpiar resumes viejos manualmente:
python linkedin_agent.py --cleanup --days 90
```

**⚠️ ADVERTENCIA:** Ejecutar `python linkedin_agent.py` SIN `--jobs-file` corre el modo DEMO
con 2 trabajos de prueba. Úsalo solo para verificar que el script funciona.

---

## ⚠️ Única acción manual requerida después de cada ejecución

**Enviar el email de resumen:**
1. Abre **Gmail** (adalbertosn1982@gmail.com)
2. Ve a **Borradores** (Drafts)
3. Abre el draft: `Weekly Job Applications — Week of {fecha}`
4. Click **Enviar**

El Gmail MCP solo puede crear borradores, no enviar directamente.

---

## 📁 Estructura de archivos

```
C:\Dev\agent-linkedin-candidate\
├── linkedin_agent.py           # Agente principal (1233 líneas, v3)
├── agent_logger.py             # Sistema de logs (3 streams por ejecución)
├── ats_updater.py              # Auto-actualiza técnicas ATS mensualmente
├── regenerate_resumes.py       # Utilidad: regenera resumes existentes con nuevo formato
├── AGENT_TASK_PROMPT.md        # Instrucciones del agente (filtros, workflow, autorización)
├── INSTRUCCIONES_OPERACION.md  # Este archivo — guía de operación
├── setup_github.ps1            # Script para publicar en GitHub (ejecutar una vez)
├── applications_log.json       # Log maestro de todas las aplicaciones (dedup key)
├── jobs_input.json             # Trabajos encontrados por MCPs → input para el agente
├── ats_techniques_cache.json   # Cache ATS — renueva automáticamente 2026-07-15
├── SilveiraNapoles-Adalberto-Resume-2026-ATS.docx  # Resume base ATS (~90-92 score)
├── resume-personalized/        # Resumes personalizados por trabajo
│   └── {Company}-{Role}-{YYYY-MM-DD}.docx
│   └── {Company}-{Role}-{YYYY-MM-DD}-CoverLetter.txt
└── logs/
    ├── run_history.json            # Historial de runs (últimos 52)
    ├── mcp_health.json             # Último health check de MCPs
    ├── errors.log                  # Errores (rotating 5MB x 5)
    ├── applications_{mode}_{ts}.log
    ├── execution_{mode}.log        # Ejecución (rotating 10MB x 10)
    └── email_status.log
```

---

## 📊 Dashboard — cómo verlo

El dashboard muestra aplicaciones en tiempo real con gráficos y tabla completa.

**Para ver/actualizar el dashboard:**
```
"Muéstrame el dashboard de empleos"
o
"Refresh my job agent dashboard"
```

Contiene:
- Cards resumen: Total | Applied | Resume Ready | Errors
- Gráfico de barras: aplicaciones por fuente (Indeed / Dice / ZipRecruiter / LinkedIn)
- Gráfico de dona: distribución por prioridad
- Tabla completa con Match%, Source, status badges
- Se actualiza leyendo `applications_log.json` en tiempo real

---

## 🐙 GitHub

- **Repo:** https://github.com/silveiraSoft/agent-linkedin-candidate
- **Script de publicación:** `setup_github.ps1` (requiere GitHub PAT con scope `repo`)
- **Commits preparados:** 4 conventional commits listos

Para publicar:
```powershell
cd C:\Dev\agent-linkedin-candidate
.\setup_github.ps1 -Token "ghp_TU_TOKEN"
```

Token: https://github.com/settings/tokens/new → scope: `repo`

---

## 🔍 Filtros activos

| Filtro | Configuración |
|---|---|
| Fuentes | Indeed, Dice, ZipRecruiter (MCPs) + LinkedIn Easy Apply (Chrome) |
| Radio | 28 millas desde 6955 NW 186th St, Hialeah FL 33015 |
| Ciudades | Miami, Hialeah, Doral, Kendall, Coral Gables, Miami Lakes, Miami Gardens, North Miami, Opa-locka, Aventura, Pembroke Pines, Miramar, Hollywood FL, Hallandale, Sunrise FL, Plantation FL, Davie FL, Cooper City |
| Remote | Cualquier estado USA |
| Liderazgo | Rechaza: Team Lead, Tech Lead, Engineering Manager, Director, VP, Head of, Program Manager |
| Salario | Principal $165-195k / Fintech+Security $160-185k / Senior $145-170k / Mid $120-145k / Junior $90-115k |

---

## 📍 Cambiar dirección base y radio de búsqueda

Abre `linkedin_agent.py` y edita el bloque `LOCATION_CONFIG` (línea ~219):

```python
LOCATION_CONFIG = {
    "base_address":      "6955 NW 186th St, Hialeah, FL 33015",  # ← cambia aquí
    "radius_miles":      28,                                       # ← cambia aquí
    "cities_in_radius": [
        # Agrega o elimina ciudades según el nuevo radio
        "miami", "hialeah", "doral", "kendall", ...
    ],
}
```

### Qué cambiar según el escenario:

| Escenario | Qué editar |
|---|---|
| Te mudaste a otra ciudad | `base_address` + actualiza `cities_in_radius` |
| Quieres cubrir más área | Aumenta `radius_miles` + agrega ciudades a `cities_in_radius` |
| Quieres área más pequeña | Reduce `radius_miles` + elimina ciudades de `cities_in_radius` |
| Solo remote | Deja `cities_in_radius` vacío `[]` |

> ⚠️ **Importante:** `cities_in_radius` es la lista que el agente usa para filtrar trabajos.
> Si cambias `radius_miles` pero no actualizas `cities_in_radius`, el filtro no cambia.
> Los dos deben mantenerse en sincronía.

---

## 🔧 Mejoras implementadas (14 de 14)

### Fase 1 — Críticas ✅
1. Validación de schema `jobs_input.json` — rechaza entradas inválidas con log
2. Deduplicación cross-MCP — normaliza URL + pair company+title
3. Run ID (UUID) — agrupa entradas del log por ejecución, midnight-safe
4. FileLock cross-platform — `os.O_EXCL` para writes atómicos en Windows+Linux
5. `--build-email --run-id` — email filtrado por run, no por fecha

### Fase 2 — Observabilidad ✅
6. MCP health check al inicio de cada run → `logs/mcp_health.json`
7. `logs/run_history.json` — historial de los últimos 52 runs
8. Cleanup automático de resumes > 90 días al inicio de cada run
9. FileLock en todos los writes de `applications_log.json`
10. `notifyOnCompletion` habilitado en el scheduled task

### Fase 3 — Calidad ✅
11. Dashboard Cowork artifact con Chart.js
12. `--dry-run` — simula pipeline completo sin side effects
13. Match% score (0-100) en email y tabla, ordenado descendente
14. Cover letter via Claude Haiku, guardada junto al resume

---

## ❗ Diagnósticos resueltos

### Easy Apply no aparecía en el email (RESUELTO)
El email se generaba antes de los Easy Apply. Fix: `--update-status` actualiza cada trabajo
después del apply, `--build-email` corre al final.

### Indeed no aparecía (RESUELTO)
El script usaba `sample_jobs` hardcodeados ignorando los MCPs. Fix: `--jobs-file` recibe
los trabajos reales que Claude encontró vía MCPs.

### LinkedIn session (MITIGADO)
El SKILL.md navega a `linkedin.com/feed` antes del Easy Apply para verificar sesión activa.
Si no hay sesión activa, el run falla en Fase 3 con log del error.

---

*Archivo de referencia central para operar el Job Agent. Mantener actualizado con cada cambio.*
