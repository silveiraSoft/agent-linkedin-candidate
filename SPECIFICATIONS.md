# Job Agent — Especificaciones Maestras
## Documento de referencia completo · v1.0 · 2026-06-16

> **Propósito**: Este documento es la fuente de verdad única del sistema.
> Un desarrollador o agente Claude que lea solo este archivo debe poder
> implementar, configurar y operar el Job Agent desde cero sin perder ningún
> contexto histórico ni ninguna regla de negocio.
>
> **Auto-actualización**: Este archivo se actualiza automáticamente con cada
> nuevo requisito, modificación de regla o decisión arquitectónica. No es
> necesario solicitarlo explícitamente.

---

## 1. Descripción General del Sistema

El **Job Agent Autónomo** es un sistema de búsqueda y aplicación de empleo
que corre en Cowork (Claude desktop) y se ejecuta automáticamente cada
miércoles a las 8:00 PM ET. Busca ofertas de trabajo en LinkedIn, Dice,
ZipRecruiter e Indeed, aplica automáticamente a las que tienen Easy Apply /
1-Click Apply, y genera un reporte semanal por email con los resultados.

### 1.1 Objetivo

Automatizar completamente el proceso de búsqueda y aplicación de trabajo para
el candidato Adalberto Silveira Napoles, Senior Java Full-Stack Engineer,
maximizando la cobertura de ofertas relevantes mientras minimiza el tiempo
manual requerido.

### 1.2 Stack tecnológico

| Componente | Tecnología |
|---|---|
| Orquestador | Cowork (Claude claude-sonnet-4-6) |
| Lenguaje agente | Python 3.x |
| Automatización browser | Claude in Chrome MCP extension |
| Email | Gmail MCP |
| Búsqueda de empleos | Dice MCP, Indeed MCP, ZipRecruiter MCP |
| Generación de resumes | Claude Haiku (via API) |
| Programación | Cowork Scheduled Tasks (cron) |
| Almacenamiento | Archivos JSON en disco local |

---

## 2. Perfil del Candidato

| Campo | Valor |
|---|---|
| Nombre | Adalberto Silveira Napoles |
| Email | adalbertosn1982@gmail.com |
| Teléfono | +1 (812) 901-8687 |
| Dirección | 6955 NW 186th St, Hialeah, Florida 33015 |
| LinkedIn | https://www.linkedin.com/in/adalbertosilveiranapoles/ |
| GitHub | https://github.com/silveiraSoft |
| Experiencia | 18+ años Senior Java Full-Stack Engineer |

### 2.1 Habilidades principales

**Backend**: Java 8/11/17/21/25, Spring Boot, Spring WebFlux, Spring MVC,
Spring Security, Spring Cloud, Spring Data JPA/Hibernate, Project Reactor,
REST APIs, gRPC, microservices

**Cloud/AWS**: Lambda, SNS/SQS, S3, API Gateway, RDS, DynamoDB, Cognito,
CloudWatch, Parameter Store, IAM

**Frontend**: ReactJS, Next.js, Remix, Angular, TypeScript, Node.js 22,
HTML5, CSS3

**Bases de datos**: PostgreSQL, MySQL, DynamoDB, Redis, SQL Server, Oracle

**DevOps**: Docker, Kubernetes, Jenkins CI/CD, SonarQube

**Seguridad**: OAuth 2.0, JWT, AES/RSA, Spring Security, Amazon Cognito,
Azure AD (MSAL)

**AI Tools**: Amazon Q, GitHub Copilot, Claude Code, Amazon Bedrock

**Arquitectura**: Clean Architecture, SOLID, DDD, CQRS, Event-Driven,
Microservices

### 2.2 Preferencias laborales

| Preferencia | Valor |
|---|---|
| Modalidad | Remote (USA) O on-site Miami FL (28mi de 33015) |
| Roles aceptados | Junior, Mid, Senior, Principal, Staff (IC únicamente) |
| Roles rechazados | Team Lead, Tech Lead, Manager, Director, VP, Head of, PM |
| Trabajo autorizado en USA | Sí (sin necesidad de sponsorship) |
| Reubicación | NO |
| Disponibilidad de viaje | 50% |
| Período de preaviso | 1 mes |

### 2.3 Rangos salariales por nivel

| Nivel | Rango |
|---|---|
| Principal / Fintech+Security | $160,000 – $195,000 |
| Senior | $145,000 – $170,000 |
| Mid | $120,000 – $145,000 |
| Junior | $90,000 – $115,000 |

### 2.4 Respuestas estándar para formularios

| Pregunta | Respuesta |
|---|---|
| Authorized to work in USA | YES |
| Require sponsorship | NO |
| Willing to relocate | NO |
| Years Java experience | 10 (usar este valor en formularios, no 18) |
| Years Spring Boot experience | 10 (usar este valor en formularios) |
| Notice period | 1 month |
| Travel availability | 50% |
| Race/ethnicity | Hispanic or Latino |
| Disability | No disability |
| Veteran/military | Not a veteran |

> **IMPORTANTE**: En formularios de Easy Apply usar Java=10 y Spring Boot=10
> (no 18). Esto es deliberado para estar dentro de rangos esperados.

---

## 3. Arquitectura del Sistema

### 3.1 Componentes principales

```
C:\Dev\agent-linkedin-candidate\
├── linkedin_agent.py           # Agente principal Python (v3, ~1233 líneas)
├── agent_logger.py             # Sistema de logs (3 streams por ejecución)
├── ats_updater.py              # Auto-actualiza técnicas ATS mensualmente
├── regenerate_resumes.py       # Utilidad: regenera resumes con nuevo formato
├── AGENT_TASK_PROMPT.md        # Prompt maestro del agente (fuente de verdad del workflow)
├── SPECIFICATIONS.md           # Este archivo — especificaciones completas
├── INSTRUCCIONES_OPERACION.md  # Guía operacional para el usuario
├── setup_github.ps1            # Script GitHub (requiere PAT con scope repo)
├── applications_log.json       # Log maestro de todas las aplicaciones (dedup key)
├── jobs_input.json             # Jobs encontrados por MCPs → input para el agente
├── ats_techniques_cache.json   # Cache ATS — se renueva automáticamente 2026-07-15
├── SilveiraNapoles-Adalberto-Resume-2026-ATS.docx  # Resume ATS base (~90-92 score)
├── resume-personalized/        # Resumes personalizados por trabajo
│   ├── {Company}-{Role}-{YYYY-MM-DD}.docx
│   └── {Company}-{Role}-{YYYY-MM-DD}-CoverLetter.txt
└── logs/
    ├── run_history.json            # Historial de runs (últimos 52)
    ├── mcp_health.json             # Último health check de MCPs
    ├── errors.log                  # Errores (rotating 5MB x 5)
    ├── applications_{mode}_{ts}.log
    ├── execution_{mode}.log        # Ejecución (rotating 10MB x 10)
    └── email_status.log
```

### 3.2 MCPs utilizados

| MCP | ID / Tool prefix | Propósito |
|---|---|---|
| Dice MCP | `mcp__1d6f6569-bc1f-4bf2-b6bd-beaaeec39f6d__search_jobs` | Búsqueda Dice |
| Indeed MCP | `mcp__417fd6dd-e777-492d-9686-027e59df064d__search_jobs` | Búsqueda Indeed |
| ZipRecruiter MCP | `mcp__dd608528-fb3f-4e97-946e-9fe062bd68b6__search_jobs` | Búsqueda ZipRecruiter |
| Gmail MCP | `mcp__f95e01a0-3e85-4964-87df-1670f71bc1ac__create_draft` | Crear borradores |
| Claude in Chrome MCP | `mcp__Claude_in_Chrome__navigate` etc. | Automatización browser |
| Scheduled Tasks MCP | `mcp__scheduled-tasks__*` | Gestión de schedule |

### 3.3 Flujo de datos

```
Scheduled Task (miércoles 8PM)
    → Claude lee AGENT_TASK_PROMPT.md
    → Phase 0: Pre-flight checks
    → Phase 1: MCP searches → jobs_input.json
    → Phase 2: python linkedin_agent.py → resume-personalized/ + applications_log.json
    → Phase 3: Chrome automation → Easy Apply por job → applications_log.json updated
    → Phase 4: Gmail MCP → Draft report email con resultados
```

### 3.4 applications_log.json — Schema

```json
{
  "job_id": "platform-uuid",
  "title": "Job Title",
  "company": "Company Name",
  "location": "Remote (USA) | City, ST",
  "url": "https://platform.com/job-detail/uuid",
  "source": "dice | linkedin | indeed | ziprecruiter",
  "priority_label": "Priority 1 - Backend Java (Spring Boot / Reactive)",
  "priority_score": 55,
  "match_score": 21,
  "description_snippet": "first 200 chars...",
  "resume_file": "Company-Title-YYYY-MM-DD.docx",
  "resume_path": "C:\\Dev\\agent-linkedin-candidate\\resume-personalized\\...",
  "cover_letter_file": "Company-Title-YYYY-MM-DD-CoverLetter.txt",
  "salary_submitted": "$145,000 - $170,000",
  "salary_offered": "USD 50.00 - 62.00 per hour",
  "status": "resume_ready | applied | failed | error",
  "easy_apply": true,
  "retry_count": 0,
  "run_id": "uuid-prefix",
  "applied_date": "YYYY-MM-DD",
  "status_updated": "ISO-datetime"
}
```

---

## 4. Configuración del Browser

| Parámetro | Valor |
|---|---|
| Browser | Google Chrome (NO Microsoft Edge) |
| Chrome device ID | `0c683dc5-8d98-4217-b9ce-3a0cb9ecdc18` |
| Google account | `adalbertosn1982@gmail.com` |

**Al iniciar cada sesión**:
1. Llamar `list_connected_browsers()` y seleccionar deviceId `0c683dc5-8d98-4217-b9ce-3a0cb9ecdc18`
2. Navegar a `https://myaccount.google.com` para verificar cuenta activa
3. Si la cuenta NO es `adalbertosn1982@gmail.com` → **STOP INMEDIATO** (ver Sección 7.2)

**Sesiones requeridas antes de iniciar**:

| Plataforma | URL de verificación | Señal de sesión activa |
|---|---|---|
| LinkedIn | https://www.linkedin.com/feed | Muestra feed / avatar de perfil |
| Dice | https://www.dice.com/dashboard | Muestra dashboard / perfil |
| ZipRecruiter | https://www.ziprecruiter.com/profile | Muestra nombre de perfil |
| Indeed | https://www.indeed.com/account | Muestra página de cuenta |

---

## 5. Requisitos Previos de Ejecución

| Requisito | Cómo verificar |
|---|---|
| Cowork app corriendo | Ícono en la bandeja del sistema (system tray) |
| Chrome abierto con Claude in Chrome extensión verde | Ícono de extensión verde en Chrome |
| LinkedIn — sesión activa | linkedin.com → muestra feed, no login |
| Dice — sesión activa | dice.com → muestra perfil, no login |
| ZipRecruiter — sesión activa | ziprecruiter.com → muestra perfil, no login |
| Indeed — sesión activa | indeed.com → muestra perfil, no login |

> No se necesita tener las pestañas abiertas — solo que las cookies de sesión
> estén activas. Verificar abriendo cada sitio una vez antes de la ejecución.

---

## 6. Workflow del Agente (4 Fases)

### Fase 0 — Pre-Flight

#### 0A. Validaciones de entorno

**Check 2b — CRITICAL HARD STOP — Validación de cuenta Google Chrome**

Navegar a `https://myaccount.google.com`. Si la cuenta activa NO es
`adalbertosn1982@gmail.com`:
- STOP INMEDIATO
- No ejecutar ninguna fase
- Crear borrador Gmail: `⛔ Agent BLOCKED — Wrong Chrome account detected — {date}`
- El borrador debe incluir: cuenta detectada, cuenta esperada, instrucción de cambio

Si la cuenta es correcta → continuar.

**Check 3 — Sesiones de plataformas**

Navegar a cada URL y verificar login. Para cada plataforma que falle:
- LinkedIn ❌ → Phase 3 Easy Apply omitida; resto continúa
- Dice ❌ → Dice Easy Apply omitido
- ZipRecruiter ❌ → ZipRecruiter apply omitido
- Indeed ❌ → Indeed apply omitido
- Todas 4 ❌ → CRITICAL STOP — email de fallo y salir

**Check 4 — MCP health probe**

Llamar cada MCP con búsqueda de 1 keyword. Log en `logs/mcp_health.json`.
Si todos fallan → CRITICAL STOP.

#### 0B. Python preflight

```bash
cd C:\Dev\agent-linkedin-candidate
python linkedin_agent.py --preflight --jobs-file jobs_input.json
```

Si `preflight_ok: false` → enviar email de fallo y STOP.

#### 0C. Email de fallo de preflight

Sujeto: `⚠️ Agent Pre-Flight FAILED — {date}`
Para: `adalbertosn1982@gmail.com`
Contiene: tabla de fallas críticas + tabla de estado de sesiones de las 4 plataformas.

#### 0D. Si preflight pasa

El email final (Phase 4) debe incluir el estado de sesión de las 4 plataformas
registrado al inicio.

---

### Fase 1 — Búsqueda y Filtrado → jobs_input.json

#### 1A. LinkedIn Direct Search via Chrome

LinkedIn no expone job IDs via MCP — se necesita navegar con Chrome para
obtener IDs nativos de LinkedIn (requeridos para Easy Apply en Phase 3).

URLs de búsqueda (ejecutar las 4):

```
# Remote + Hybrid — USA
https://www.linkedin.com/jobs/search/?keywords=Senior%20Java%20Spring%20Boot%20backend&f_AL=true&f_WT=2%2C1&location=United%20States&sortBy=R

# Fullstack remote
https://www.linkedin.com/jobs/search/?keywords=fullstack%20Java%20React%20Spring%20Boot&f_AL=true&f_WT=2&location=United%20States&sortBy=R

# On-site/Hybrid 28mi Miami
https://www.linkedin.com/jobs/search/?keywords=Java%20Spring%20Boot%20developer&f_AL=true&f_WT=3%2C1&location=Miami%2C%20FL&distance=28&sortBy=R

# 🌟 GOLDEN RULE — Spring Boot standalone (sin "Java" en keywords)
https://www.linkedin.com/jobs/search/?keywords=spring%20boot%20developer&f_AL=true&f_WT=2&location=United%20States&sortBy=R
```

Parámetros:
- `f_AL=true` = Easy Apply only (intencional — Easy Apply es requisito para auto-apply)
- `f_WT=2,1` = Remote + Hybrid
- `f_WT=3,1` = On-site + Hybrid
- `distance=28` = radio 28 millas

Para cada job encontrado: extraer job_id (número del URL), title, company, url.
Navegar al job URL y usar `get_page_text` para obtener descripción completa.

**NOTA sobre Easy Apply en LinkedIn**:
El modal de Easy Apply SOLO se abre desde el panel de resultados de búsqueda,
NO desde `/jobs/view/JOBID/`. Para Phase 3, navegar a:
`https://www.linkedin.com/jobs/search/?currentJobId=JOBID&f_AL=true&keywords=Java+Spring+Boot`

#### 1B. Búsquedas MCP

**Dice MCP** — `employment_types: ["FULLTIME", "CONTRACTS"]` SIEMPRE

Remote Easy Apply:
- "Senior Java Spring Boot backend engineer", Remote, FULLTIME+CONTRACTS, easy_apply:true, posted:SEVEN, 30 results
- "Java microservices AWS developer", Remote, FULLTIME+CONTRACTS, easy_apply:true, posted:SEVEN, 30 results
- "fullstack Java React Spring Boot developer", Remote, FULLTIME+CONTRACTS, easy_apply:true, posted:SEVEN, 30 results
- "Senior Java developer Spring Boot AWS", Remote, FULLTIME+CONTRACTS, posted:SEVEN, 30 results
- 🌟 "spring boot developer", Remote, FULLTIME+CONTRACTS, easy_apply:true, posted:SEVEN, 30 results
- 🌟 "spring boot microservices engineer", Remote, FULLTIME+CONTRACTS, easy_apply:true, posted:SEVEN, 30 results
- 🌟 "spring boot backend engineer", Remote, FULLTIME+CONTRACTS, easy_apply:true, posted:SEVEN, 30 results

Local Miami/Broward (28mi):
- "Java Spring Boot developer", Miami FL, radius:28mi, On-Site+Hybrid, FULLTIME+CONTRACTS, easy_apply:true, posted:SEVEN, 20 results
- "Senior software engineer Java", Miami FL, radius:28mi, On-Site+Hybrid, FULLTIME+CONTRACTS, easy_apply:true, posted:SEVEN, 20 results

**Indeed MCP** — Parámetros requeridos: `search`, `location`, `country_code` (todos)

Remote fulltime/contract:
- "Senior Java Spring Boot backend", remote, US, fulltime
- "Senior Java Spring Boot backend", remote, US, contract
- "backend engineer Java Spring Boot", remote, US, fulltime
- "software developer Java Spring Boot", remote, US, fulltime
- "software engineer Java Spring Boot microservices", remote, US, fulltime
- "fullstack Java React Spring Boot developer", remote, US, fulltime
- "Java AWS developer Spring Boot", remote, US, fulltime
- "Java microservices Spring Boot developer", remote, US, fulltime
- "AI software developer Java Spring Boot", remote, US, fulltime
- "web developer Java Spring Boot backend", remote, US, fulltime
- "API developer Java Spring Boot", remote, US, fulltime
- 🌟 "spring boot developer", remote, US, fulltime
- 🌟 "spring boot developer", remote, US, contract
- 🌟 "spring boot microservices engineer", remote, US, fulltime
- 🌟 "spring boot backend engineer", remote, US, fulltime
- 🌟 "spring boot developer", Miami FL, US, fulltime

Local Miami/Broward:
- "Java developer", Miami FL, US, fulltime
- "Java developer", Miami FL, US, contract
- "Java Spring Boot developer", Miami FL, US, fulltime
- "backend engineer Java", Miami FL, US, fulltime
- "software engineer Java Spring Boot", Fort Lauderdale FL, US, fulltime

Post-filtrar por ciudad: aceptar Miami, Hialeah, Doral, Coral Gables, Fort Lauderdale,
Sunrise, Plantation, Davie, Hollywood FL, Pembroke Pines, Miramar, Aventura,
Broward County. Rechazar: Orlando, Tampa, Jacksonville, Boca Raton.

**ZipRecruiter MCP** — `employment_types: ["FULL_TIME", "CONTRACT", "CONTRACT_TO_HIRE"]`

- "senior Java Spring Boot backend engineer", REMOTE, SENIOR, skills:["Java","Spring Boot","AWS","microservices"], max_posted:10080min
- "fullstack Java React Spring Boot developer", REMOTE, SENIOR+MID
- "senior Java microservices developer", REMOTE+HYBRID, SENIOR
- 🌟 "spring boot developer", REMOTE, FULL_TIME+CONTRACT+CONTRACT_TO_HIRE
- 🌟 "spring boot microservices engineer", REMOTE, FULL_TIME+CONTRACT+CONTRACT_TO_HIRE

#### 1C. Schema de jobs_input.json

```json
[{
  "id": "platform-uuid",
  "title": "Job Title",
  "company": "Company Name",
  "location": "City, ST or Remote (USA)",
  "url": "https://platform.com/job-detail/uuid",
  "description": "descripción completa — DEBE incluir keywords Java/Spring Boot",
  "source": "linkedin | dice | indeed | ziprecruiter",
  "salary": "offered salary string or null",
  "easy_apply": true
}]
```

Campos `id`, `title`, `company`, `url` son REQUERIDOS.

---

### Fase 2 — Generación de Resumes

```bash
cd C:\Dev\agent-linkedin-candidate
python linkedin_agent.py --jobs-file jobs_input.json
```

Capturar `run_id` del JSON output (ej: `"run_id": "8050718c-192"`).

Genera por cada job:
- Resume `.docx` personalizado en `resume-personalized/`
- Summary via Claude Haiku con keywords del JD
- Bullets STAR cuantificados
- Skills reordenados por relevancia
- Cover letter `.txt`
- Match Score 0-100

Registra todos como `resume_ready` en `applications_log.json`.
Limpia resumes > 90 días automáticamente.

**Resume a usar en formularios de plataformas**:
SIEMPRE `SilveiraNapoles-Adalberto-Resume-2026-ATS.docx` (raíz del proyecto).
NUNCA usar archivos de `resume-personalized/` para uploads en plataformas.

---

### Fase 3 — Automatización Easy Apply

**AUTORIZACIÓN**: El usuario ha autorizado el envío autónomo de aplicaciones
sin confirmación por oferta. Aplica a TODOS los jobs con Easy Apply / 1-Click.

#### ⚠️ REGLA UNIVERSAL — NINGÚN JOB SE DESCARTA SILENCIOSAMENTE

Cada job que pasó los filtros de Phase 1 DEBE aparecer en el email de Phase 4.
El resultado de cada job cae en exactamente uno de estos estados:

| Outcome | Email section |
|---|---|
| ✅ Easy Apply enviado exitosamente | Sección 1 — APLICACIONES AUTOMÁTICAS |
| ❌ Easy Apply intentado pero falló | Sección 1 con ❌ + razón + Sección 3 con link manual |
| 🔴 Sin Easy Apply disponible | Sección 3 — APLICAR MANUALMENTE |
| ⏳ Pendiente / no intentado | Sección 3 con link |
| ❌ Filtrado (no pasó Phase 1) | Sección 5 — FILTRADOS |

`easy_apply: false` NO es razón para omitir un job. Va a Sección 3.

#### Años de experiencia en formularios

- Java: **10 años**
- Spring Boot: **10 años**
- Otras tecnologías: años reales o el más cercano a 10

#### Detección de Easy Apply por plataforma

- **Dice**: botón "Easy Apply" detectado via Chrome
- **ZipRecruiter**: botón "1-Click Apply" o "Apply Now" detectado via Chrome
- **Indeed**: botón "Easily apply" o "Apply now (Easily apply)" detectado via Chrome
- **LinkedIn**: botón "Easy Apply" detectado en panel de resultados de búsqueda

#### Proceso por cada job

1. `mcp__Claude_in_Chrome__navigate(url=job["url"])`
2. Esperar 2-3 segundos
3. `read_page(filter="interactive")` para accessibility tree
4. Buscar botón de quick-apply por plataforma
5. Si botón encontrado → llenar formulario → subir resume ATS → submit → screenshot confirmación → `python linkedin_agent.py --update-status JOBID applied`
6. Si NO hay botón → agregar a `manual_apply_list` con URL directa. **NUNCA descartar.**

#### Platform-specific: LinkedIn Easy Apply

- Navegar a search results panel (NO a `/jobs/view/JOBID/`)
- URL: `https://www.linkedin.com/jobs/search/?currentJobId=JOBID&f_AL=true&keywords=Java+Spring+Boot`
- Click Easy Apply desde el panel derecho
- Si pregunta "Did you use AI tool?" → dismiss y marcar para manual apply

#### Platform-specific: Indeed

- "Easily Apply" navega a `smartapply.indeed.com` (React SPA)
- ⚠️ Limitación conocida: botones no responden a clicks automatizados
- Estrategia: intentar 2 veces máximo; si no avanza → `manual_apply_list`
- No reintentar más de 2 veces

#### Platform-specific: ZipRecruiter

- `job_redirect_url` del MCP → navegar para llegar al job real
- "1-Click Apply" verde → click → envía instantáneamente desde perfil
- No puede detectarse desde MCP results — requiere browser

#### Tracking durante Phase 3

**`auto_applied_list`** — jobs donde Easy Apply fue intentado:
```json
{"title": "...", "company": "...", "url": "...", "source": "...", "status": "applied|failed", "fail_reason": "..."}
```

**`manual_apply_list`** — jobs que requieren acción manual:
```json
{"title": "...", "company": "...", "url": "...", "source": "...", "reason": "Sin Easy Apply|Easy Apply falló: ...|Aggregator externo"}
```

---

### Fase 4 — Email de Reporte + Notificación

**SIEMPRE enviar a**: `adalbertosn1982@gmail.com` — NUNCA a otra dirección.

**Sujeto**: `🤖 Job Agent Report — {YYYY-MM-DD} | {N} aplicados · {N} pendientes · {N} por revisar`

#### Requisitos críticos del email

1. **CADA job que pasó Phase 1 DEBE aparecer en el email** — sin excepciones
2. **Cada fila DEBE incluir link directo** a la oferta (no página de búsqueda)
3. **Cada fila DEBE mostrar status**: ✅ Aplicado / ❌ Falló (razón) / 🔴 Manual / ⏳ Pendiente
4. **Sección de aplicados es OBLIGATORIA** — aunque sea solo 1 job
5. **Jobs sin Easy Apply DEBEN aparecer en Sección 3** con link directo para aplicar manualmente
6. **100% inline CSS** — Gmail elimina los `<style>` tags. Todo estilo debe ser `style="..."` en cada elemento

#### Estructura del email (en este orden)

**Header** — fecha, modelo, nombre candidato

**Quick summary bar** — Applied ✅ · Manual 🔴 · To review 🟡 · Filtered ❌

---

**Sección 1 — ✅❌ APLICACIONES AUTOMÁTICAS**

Para cada job donde Easy Apply fue INTENTADO (exitoso O fallido):

| # | Platform | Company | Position | Salary/Type | Estado | 🔗 Link oferta |

- ✅ **Aplicado** — formulario enviado exitosamente
- ❌ **Falló** — razón específica ("form timed out", "multi-step blocked", "session expired")

Agrupar por plataforma. DEBE aparecer aunque solo 1 job.

---

**Sección 2 — 💼 LINKEDIN — TODAS LAS OFERTAS ENCONTRADAS**

LinkedIn = navegación directa, por lo tanto el agente tiene visibilidad completa.
TODOS los jobs de LinkedIn deben aparecer con su estado individual.

| # | Empresa | Posición | Tipo | Salario | Estado | 🔗 Link |

Status values: ✅ Aplicado / 🔴 Apply manual (razón) / ⏳ Pendiente / ❌ Filtrado (razón)

No colapsar LinkedIn a una sola línea. Si LinkedIn retornó 12 resultados, mostrar 12.

---

**Sección 3 — 🔴 APLICAR MANUALMENTE**

TODOS los jobs de TODAS las plataformas que requieren acción manual:

| # | Platform | Company | Position | Salary/Type | Motivo | 👉 Link para aplicar |

- Motivo: "Sin Easy Apply", "Easy Apply falló: [razón]", "Aggregator externo"
- Link: URL directa al job (no página de búsqueda)
- Incluye jobs de Dice con `easy_apply:false`, FetchJobs.co, Greenhouse, Lever, Workday, etc.

---

**Sección 4 — 🟡 VERIFICAR TIPO DE APLICACIÓN** (Indeed + ZipRecruiter)

Jobs donde el MCP no expone el tipo de apply — verificar manualmente en el browser.

| # | Platform | Company | Position | Salary | 🔗 Link para verificar |

---

**Sección 5 — ❌ FILTRADOS / OMITIDOS**

Tabla completa — company, title, platform, razón del filtro. No colapsar.

---

**Sección 6 — 📊 Dashboard por plataforma**

| Platform | Found | ✅ Applied | 🔴 Manual | 🟡 Review | ❌ Filtered |
|---|---|---|---|---|---|
| LinkedIn | N | N | N | — | N |
| Dice | N | N | N | — | N |
| Indeed | N | N | N | N | N |
| ZipRecruiter | N | N | — | N | N |
| **TOTAL** | **N** | **N** | **N** | **N** | **N** |

**💰 Token Usage**:

| Metric | Value |
|---|---|
| Total input tokens | ~N,000 |
| Total output tokens | ~N,000 |
| Estimated cost | ~$N.NN |
| Run duration | ~N minutes |
| Next scheduled run | {date} at 8:00 PM ET |

---

**Sección 7 — 🔐 Estado de sesiones al inicio del run**

```
✅ LinkedIn — logged in as adalbertosn1982@gmail.com
✅ Dice — logged in
✅ ZipRecruiter — logged in
⚠️ Indeed — session expired (Indeed apply skipped this run)
```

---

**Segundo borrador — Notificación corta**

Sujeto: `✅ Job Agent Run Complete — {date}`
Cuerpo (plain text): Applied N · Manual N · Errors N · Full report in drafts

---

## 7. Reglas de Filtrado

### 7.1 Filtro de Ubicación

**ACEPTAR**:
- Remote (USA)
- On-site o Hybrid dentro de 28 millas de 6955 NW 186th St, Hialeah FL 33015

**Ciudades aceptadas** (on-site/hybrid):
Miami, Hialeah, Doral, Kendall, Coral Gables, Miami Lakes, Miami Gardens,
North Miami, Opa-locka, Sweetwater, Medley, Aventura, Pembroke Pines,
Miramar, Hollywood FL, Hallandale, Sunrise FL, Plantation FL, Davie FL,
Cooper City, **Fort Lauderdale** (~25mi — DENTRO del radio), Broward County,
Pompano Beach, Deerfield Beach, Lauderhill, Tamarac, North Lauderdale

**RECHAZAR**: Boca Raton, Orlando, Tampa, Jacksonville, cualquier otra ciudad

> Fort Lauderdale es ≈25mi al norte de Hialeah — ACEPTAR on-site/hybrid allí.

### 7.2 Filtro de Roles de Liderazgo

**RECHAZAR** si el título contiene (case-insensitive):
`team lead`, `tech lead`, `engineering manager`, `director`, `vp`, `head of`,
`program manager`, `project manager`, `delivery manager`, `lead developer`,
`lead architect`, `lead analyst`, `lead consultant`, `microservices lead`,
`services lead`, `java lead`, ` lead` (standalone precedido de espacio)

> El patrón ` lead` con espacio adelante captura "Java Microservices Lead",
> "Java Services Lead" que no serían capturados por "team lead" solo.

### 7.3 🌟 REGLA DE ORO 1 — Spring Boot en Título = SIEMPRE ACEPTAR

**Si el título del job contiene "spring boot" (case-insensitive) → ACEPTAR inmediatamente.**
No se aplican otros filtros de título.

Aplica INCLUSO si "Java" no aparece en el título.

Ejemplos que DEBEN ser aceptados:
- "Spring Boot Developer"
- "Senior Spring Boot Engineer"
- "Spring Boot Microservices Developer"
- "Backend Spring Boot Developer"
- "AWS Engineer Spring Boot"
- "Spring Boot React Full Stack"

Si no tiene Easy Apply → `manual_apply_list`. **Nunca descartar.**

### 7.4 🌟 REGLA DE ORO 2 — Spring Boot en Skills = Priority 1

Si "spring boot" aparece en la sección de required skills / requirements del JD:
→ ACEPTAR, aunque el título sea genérico
→ Score como Priority 1

### 7.5 Filtro de Títulos Genéricos

Se aplica SOLO cuando el título es genérico ("Software Engineer", "Backend Engineer",
"Software Developer") Y no tiene "Java" NI "Spring Boot".

→ Solo aceptar si Java AND Spring Boot aparecen explícitamente en la sección de
   required skills / requirements (no mencionados casualmente)
→ Rechazar si Java/Spring Boot ausentes

> Este filtro es SOBREESCRITO por las Reglas de Oro 1 y 2.

### 7.6 Prioridades de búsqueda

1. **Priority 1 — Backend Java**: Spring Boot, Spring WebFlux, Java 17/21, reactive
2. **Priority 2 — Fullstack**: React o Next.js + Spring Boot/Java backend
3. **Priority 3 — General match**: cualquier rol que coincida con el perfil

### 7.7 Deduplicación

- Comparar por URL normalizada
- Comparar por par company+title
- Saltar si job_id ya existe en `applications_log.json`

---

## 8. Reglas de Seguridad

### 8.1 Validación de cuenta Google Chrome

Al inicio de CADA sesión:
- Navegar a `https://myaccount.google.com`
- Verificar que la cuenta activa sea `adalbertosn1982@gmail.com`
- Si es otra cuenta (ej: `asilveira@3htp.com`) → **STOP INMEDIATO**

Razón: Usar la cuenta equivocada enviaría aplicaciones bajo identidad incorrecta
y los emails irían al inbox equivocado. Esto es un HARD STOP sin excepciones.

Email de bloqueo:
- Sujeto: `⛔ Agent BLOCKED — Wrong Chrome account detected — {date}`
- Cuerpo: cuenta detectada, cuenta esperada, instrucción de cambio de perfil Chrome

### 8.2 Destino de emails

TODOS los emails (reportes, fallos, notificaciones) van SIEMPRE a:
`adalbertosn1982@gmail.com`

Nunca enviar a otra dirección, aunque el Gmail MCP esté autenticado con otra.

---

## 9. Configuración de Schedule

| Parámetro | Valor |
|---|---|
| Scheduled Task ID | `weekly-job-agent-adalberto` |
| Cron expression | `0 20 * * 3` |
| Ejecución | Miércoles 8:00 PM ET |
| Estado | HABILITADO ✅ |

### 9.1 Frases para activar/pausar el schedule

| Acción | Frases aceptadas |
|---|---|
| **Activar** | "activa el agente programado", "activa la ejecución automática", "habilita el agente", "activa el schedule", "enciende el agente", "reactiva el agente" |
| **Pausar** | "pausa el agente", "desactiva el agente programado", "suspende el agente", "desactiva la ejecución automática", "deshabilita el agente", "apaga el agente" |

Usar `mcp__scheduled-tasks__update_scheduled_task` con taskId `weekly-job-agent-adalberto`.

> Estas frases controlan SOLO el schedule. No inician ni detienen una sesión activa.

---

## 10. Ejecución Manual

### Frases trigger (cualquiera de estas inicia el agente completo)

- "ejecuta el agente"
- "ejecuta el agente manualmente"
- "corre el agente"
- "inicia el agente"
- "run the agent"
- "ejecuta el job agent"
- "lanza el agente"
- "ejecuta el proceso"

**Acción**: Leer `AGENT_TASK_PROMPT.md` y ejecutar workflow completo
(Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4) sin pedir confirmación.

Prompt interno completo:
```
Ejecuta el job agent completo siguiendo las instrucciones en C:\Dev\agent-linkedin-candidate\AGENT_TASK_PROMPT.md
```

---

## 11. Comandos CLI del Agente Python

```bash
# Ejecutar pipeline completo con jobs reales:
python linkedin_agent.py --jobs-file jobs_input.json

# Actualizar status de un job específico:
python linkedin_agent.py --update-status "job_id" applied

# Generar email de reporte filtrado por run:
python linkedin_agent.py --build-email --run-id <run_id>

# Simular sin side effects:
python linkedin_agent.py --jobs-file jobs_input.json --dry-run

# Verificar entorno antes de run:
python linkedin_agent.py --preflight --jobs-file jobs_input.json

# Limpiar resumes viejos manualmente:
python linkedin_agent.py --cleanup --days 90
```

> ⚠️ `python linkedin_agent.py` SIN argumentos corre el modo DEMO con 2 trabajos de prueba.
> Usar solo para verificar que el script funciona.

---

## 12. Generación de Resumes

### 12.1 Reglas de versioning

- El resume base ATS es: `SilveiraNapoles-Adalberto-Resume-2026-ATS.docx` (raíz del proyecto)
- Los resumes personalizados tienen fecha en el nombre: `{Company}-{Role}-{YYYY-MM-DD}.docx`
- Verificar que el resume en cada plataforma sea la versión actual antes de aplicar
- Si el resume en Dice/ZipRecruiter/Indeed está desactualizado → actualizar perfil

### 12.2 Qué NO usar en plataformas

NUNCA usar archivos de `resume-personalized/` para uploads en plataformas.
Solo el resume ATS de la raíz del proyecto.

### 12.3 Limpieza automática

Resumes en `resume-personalized/` con más de 90 días se eliminan automáticamente
al inicio de cada run.

---

## 13. Reglas de Emails para Plataformas

### Dice MCP

- `employment_types: ["FULLTIME", "CONTRACTS"]` — SIEMPRE incluir contratos
- `easy_apply: true` en búsquedas remote para identificar one-click apply
- Jobs con `easy_apply: false` → Dice detectó que requiere apply externo → `manual_apply_list`

### ZipRecruiter MCP

- `employment_types: ["FULL_TIME", "CONTRACT", "CONTRACT_TO_HIRE"]` (enum diferente a Dice)
- "1-Click Apply" NO se expone en MCP results — detectar via browser en Phase 3
- `job_redirect_url` → navegar para llegar al job real

### Indeed MCP

- Parámetros requeridos: `search`, `location`, `country_code` — todos obligatorios
- Sin `location` → "No job results found" silenciosamente
- "Easily Apply" NO se expone en MCP results — detectar via browser
- Indeed Smart Apply (`smartapply.indeed.com`) es SPA React — botones no responden a clicks
- Estrategia: max 2 intentos; si no avanza → `manual_apply_list`

### LinkedIn (Chrome)

- Easy Apply modal SOLO desde panel de búsqueda, NO desde `/jobs/view/JOBID/`
- Resume a usar: `SilveiraNapoles-Adalberto-Resume-2026-ATS.docx` (subido 2026-06-15)
- Si pregunta "Did you use AI?" → dismiss y marcar para manual apply

---

## 14. Limitaciones Conocidas

| Limitación | Plataforma | Workaround |
|---|---|---|
| Smart Apply es SPA React — no responde a clicks | Indeed | Max 2 intentos → manual_apply_list |
| 1-Click Apply no detectable via MCP | ZipRecruiter | Navegar cada job en Chrome para verificar |
| Easy Apply modal no abre desde /jobs/view/ | LinkedIn | Usar URL de search results con currentJobId |
| Jobs de aggregators (FetchJobs.co, etc.) en Dice no tienen easy_apply nativo | Dice | Marcar como manual_apply, nunca descartar |

---

## 15. Observabilidad y Logging

| Archivo | Contenido |
|---|---|
| `logs/run_history.json` | Historial de los últimos 52 runs |
| `logs/mcp_health.json` | Último health check de MCPs |
| `logs/errors.log` | Errores (rotating 5MB x 5) |
| `logs/applications_{mode}_{ts}.log` | Log de aplicaciones por ejecución |
| `logs/execution_{mode}.log` | Ejecución completa (rotating 10MB x 10) |
| `logs/email_status.log` | Estado de envío de emails |

---

## 16. Mejoras Implementadas (14 de 14)

1. Validación de schema `jobs_input.json` — rechaza entradas inválidas con log
2. Deduplicación cross-MCP — normaliza URL + pair company+title
3. Run ID (UUID) — agrupa entradas del log por ejecución, midnight-safe
4. FileLock cross-platform — `os.O_EXCL` para writes atómicos en Windows+Linux
5. `--build-email --run-id` — email filtrado por run, no por fecha
6. MCP health check al inicio de cada run → `logs/mcp_health.json`
7. `logs/run_history.json` — historial de los últimos 52 runs
8. Cleanup automático de resumes > 90 días al inicio de cada run
9. FileLock en todos los writes de `applications_log.json`
10. `notifyOnCompletion` habilitado en el scheduled task
11. Dashboard Cowork artifact con Chart.js
12. `--dry-run` — simula pipeline completo sin side effects
13. Match% score (0-100) en email y tabla, ordenado descendente
14. Cover letter via Claude Haiku, guardada junto al resume

---

## 17. GitHub

- **Repo**: https://github.com/silveiraSoft/agent-linkedin-candidate
- **Script de publicación**: `setup_github.ps1` (requiere GitHub PAT con scope `repo`)

```powershell
cd C:\Dev\agent-linkedin-candidate
.\setup_github.ps1 -Token "ghp_TU_TOKEN"
```

Token: https://github.com/settings/tokens/new → scope: `repo`

---

## 18. Dashboard

Ver dashboard en tiempo real:
```
"Muéstrame el dashboard de empleos"
```

Contiene:
- Cards resumen: Total | Applied | Resume Ready | Errors
- Gráfico de barras: aplicaciones por fuente
- Gráfico de dona: distribución por prioridad
- Tabla completa con Match%, Source, status badges
- Lee `applications_log.json` en tiempo real

---

## 19. Reglas de Actualización de Este Documento

Este archivo (`SPECIFICATIONS.md`) se actualiza automáticamente:

- Con cada nuevo requisito funcional o no funcional
- Con cada modificación de regla de filtrado
- Con cada nueva decisión arquitectónica
- Con cada nuevo trigger phrase o configuración operacional

No es necesario solicitar la actualización — es parte del proceso estándar
de cualquier cambio en el sistema.

El objetivo es que este archivo sea suficiente para que un desarrollador o
agente Claude externo pueda implementar, configurar y operar el sistema
completo desde cero, sin necesitar acceso a ningún otro archivo de contexto.

---

## 20. Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-06-15 | v1: Sistema inicial — 14 mejoras implementadas, pipeline 4 fases |
| 2026-06-15 | Accion Labs (Spring Boot + Docusign) identificado via Dice MCP |
| 2026-06-15 | Keeper Security aplicado via LinkedIn Easy Apply (prueba en vivo) |
| 2026-06-15 | Chrome validation: bloquear si cuenta ≠ adalbertosn1982@gmail.com |
| 2026-06-15 | Phase 4 email: 100% inline CSS, links en todas las filas |
| 2026-06-15 | Sección LinkedIn "todas las ofertas encontradas" añadida al email |
| 2026-06-16 | 8 jobs aplicados en Dice Easy Apply automáticamente |
| 2026-06-16 | Indeed: 15 variantes de keyword, Fort Lauderdale añadido al radio |
| 2026-06-16 | LinkedIn Phase 1A: búsqueda directa via Chrome para IDs nativos |
| 2026-06-16 | Phrase triggers: "ejecuta el agente" → ejecutar AGENT_TASK_PROMPT.md |
| 2026-06-16 | 🌟 GOLDEN RULE: Spring Boot en título = ACEPTAR siempre (independiente de Java) |
| 2026-06-16 | 🌟 GOLDEN RULE 2: Spring Boot en skills = Priority 1 |
| 2026-06-16 | Spring Boot standalone search terms en Dice, Indeed, ZipRecruiter, LinkedIn |
| 2026-06-16 | No-Easy-Apply jobs → manual_apply_list, NUNCA descartar |
| 2026-06-16 | Schedule toggle: "pausa el agente" / "activa el agente programado" |
| 2026-06-16 | REGLA UNIVERSAL: todo job seleccionado aparece en email con status + link |
| 2026-06-16 | SPECIFICATIONS.md creado — documento maestro de especificaciones |

---

*Documento generado automáticamente por el Job Agent System.*
*Actualizar con cada cambio en AGENT_TASK_PROMPT.md, reglas de filtrado, o configuración.*
