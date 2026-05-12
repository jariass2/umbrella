# Propuesta Comercial — Umbrella AI
## Plataforma Inteligente de Desarrollo para Laboratorio + Fabricante de Complementos Alimenticios

**Para:** Ümbrella Flavours & Functional Ingredients, S.L.  
**De:** Equipo Umbrella AI  
**Fecha:** Abril 2026  
**Confidencial**

---

## Resumen Ejecutivo

Ümbrella invierte 18-22 horas de trabajo técnico especializado en cada formulación: validación regulatoria, cálculo de claims, generación de dossiers. Con 100 formulaciones/año, eso supone más de 2.000 horas de técnico senior — más de 160.000 € anuales en tiempo técnico.

**Umbrella AI** es el sistema de 8 agentes de inteligencia artificial desarrollado internamente por Ümbrella que reduce ese proceso a 3-5 minutos: análisis normativo, ficha técnica, claims comerciales, plan de QC y Lista de Materiales — todo en paralelo, con trazabilidad completa hacia fuentes oficiales (EFSA, AESAN, BELFRIT, Reg. 432/2012).

El sistema ya está en uso interno. Esta propuesta es para implantarlo en producción para el equipo de Ümbrella, en fases validables. La inversión mínima (Fases 0+1+1b, 5 semanas) es de **20.500 €**. Con 100 formulaciones/año, el sistema se amortiza en menos de 2 meses.

---

## 1. Contexto: Ümbrella como laboratorio y fabricante

Ümbrella Flavours & Functional Ingredients opera en un modelo integrado: desarrolla fórmulas a medida (laboratorio) y las fabrica a escala (producción propia). Esto implica un doble ciclo de trabajo:

**Como laboratorio**, Ümbrella recibe peticiones de clientes ("Necesitamos un inmunológico en stick, sin alérgenos") y debe transformar esa necesidad en una formulación viable: validar ingredientes, verificar normativa, calcular dosis, diseñar formato.

**Como fabricante**, Ümbrella debe producir cada formulación de forma reproducible: Lista de Materiales precisa, plan de control de calidad, documentación para regulatory, trazabilidad de lote.

El cuello de botella no está en la producción — está en la transición de la idea a la formulación validada. Un técnico senior dedica 18-20 horas por formulación entre:

- Buscar cada ingrediente en la Directiva 2002/46/CE y listas BELFRIT/AESAN
- Verificar que la dosis no supera el UL de EFSA
- Calcular los claims autorizados (Reglamento 432/2012)
- Redactar la ficha técnica conforme a normativa AESAN
- Diseñar el plan de QC según farmacopea (Ph. Eur.)
- Generar la Lista de Materiales para producción

Cada cambio en la fórmula obliga a repetir todo el proceso.

---

## 2. La solución: Umbrella AI

Umbrella AI es el sistema que Ümbrella ha desarrollado internamente para resolver este cuello de botella. Un sistema de **8 agentes de inteligencia artificial especializados** que ejecutan todo el ciclo de desarrollo — desde la fórmula hasta la documentación lista para producción — en **3-5 minutos**.

El técnico introduce una fórmula:

```
Inmuno Complex Pro
- Vitamina C (ác. ascórbico): 120mg (150% VRN)
- Zinc (gluconato): 10mg (100% VRN)
- Vitamina D3 (colecalciferol): 15μg (300% VRN)
- Equinácea (extracto seco 4:1): 200mg
- Propóleo (extracto estandarizado): 150mg
```

Umbrella AI genera en paralelo todos los entregables:

| Agente | Entregable | Tiempo manual estimado |
|--------|------------|------------------|
| **KIC** | Clasificación funcional, biodisponibilidad, interacciones, sinergias | 3-4h |
| **Regulatorio** | Semáforo por ingrediente (✅⚠️❌), normativa aplicable, UL EFSA | 2-3h |
| **Ficha Técnica** | Dossier AESAN: composición, nutricional, alérgenos, modo de empleo | 3-4h |
| **Claims** | Claims autorizados UE 432/2012, selling points, advertencias legales | 2-3h |
| **Etiqueta** | Texto cara principal, secundaria, lateral (Reg. 1169/2011) | 2h |
| **Formatos** | Evaluación sticks/cápsulas/viales, reactividad, target | 1-2h |
| **Docs Internos** | Lista de Materiales, proceso de fabricación, mapa de reactividad | 2-3h |
| **QC** | Plan FTIR, granulometría, densidad, pH, estabilidad ICH | 2-3h |

**Tiempo manual total: 18-22 horas por formulación. Tiempo con Umbrella AI: 3-5 minutos.**

### ¿Cómo funciona?

Cada agente está especializado en una fase del desarrollo y puede consultar fuentes oficiales en tiempo real:

```
Fórmula de entrada
        │
        ▼
┌───────────────────────────────────────────────┐
│              Umbrella AI Pipeline               │
│                                                │
│   Batch 1 (paralelo)                           │
│   ├── Ag. KIC ──────────────────────┐         │
│   ├── Ag. Formatos                  │         │
│   ├── Ag. Docs Internos             │         │
│   └── Ag. QC                       │         │
│                                    ▼         │
│   Batch 2                           │         │
│   └── Ag. Regulatorio ─────────────┤         │
│                                    ▼         │
│   Batch 3 (paralelo)               │         │
│   ├── Ag. Ficha Técnica ───────────┤         │
│   └── Ag. Claims ─────────────────┤         │
│                                    ▼         │
│   Batch 4                           │         │
│   └── Ag. Etiqueta ───────────────┘         │
│                                                │
│   Informe Ejecutivo                          │
└───────────────────────────────────────────────┘
        │
        ├── Fuentes regulatorias
        │   (Dir. 2002/46/CE, Reg. 432/2012, BELFRIT/AESAN, NRV)
        │
        └── Navision / Business Central (Fase 2)
            (Catálogo, stock, LM, proveedores)
```

### Diferenciadores

**1. Agentes especializados con consulta a fuentes oficiales.** Cada agente está configurado con conocimiento normativo experto y consulta las fuentes relevantes para su ámbito:
- Ag. KIC: tablas NRV (Reg. 1169/2011), literatura científica
- Ag. Regulatory: Directiva 2002/46/CE, listas BELFRIT/AESAN, UL EFSA, Novel Foods
- Ag. Claims: Reglamento (UE) 432/2012
- Ag. QC: farmacopeas (Ph. Eur., USP), guías ICH

**2. Auditoría completa.** Cada output incluye las fuentes exactas consultadas — artículo, anexo, url si aplica. Trazabilidad completa para auditorías AESAN.

**3. Sistema validado internamente.** Umbrella AI ya está en uso dentro de Ümbrella para el desarrollo de fórmulas propias. Los agentes han sido probados con formulaciones reales del sector.

**4. Diseño laboratorio + fabricante.** Los agentes Docs Internos y QC generan documentación directamente usable en producción: LM estilo Navision, planes de control según Ph. Eur., no solo dossiers regulatorios.

**5. Arquitectura extensible.** Añadir un nuevo agente especializado (evaluación de costes, simulación de estabilidad, análisis de proveedores) es crear un archivo de configuración. No hay que tocar el resto del sistema. El pipeline está diseñado para crecer con las necesidades de Ümbrella.

---

## 3. Casos de uso para Ümbrella

### 3.1. Desarrollo rápido de fórmulas para clientes

Ümbrella recibe peticiones de fórmulas personalizadas con frecuencia. Cada petición requiere validar la viabilidad regulatoria, calcular dosis, y generar documentación.

**Sin Umbrella AI:** 18-22 horas de trabajo técnico por fórmula. Cuello de botella cuando hay 5-10 peticiones en paralelo.

**Con Umbrella AI:** El técnico introduce la fórmula. En 15 minutos tiene el análisis completo con semáforo regulatorio, claims disponibles, ficha técnica preliminar, y plan de QC. Puede evaluar 5-10 variantes en una mañana y presentar al cliente una recomendación fundamentada.

### 3.2. Escalado del catálogo de productos propios

Ümbrella tiene un catálogo de ingredientes funcionales propios ("OpenLabs", fórmulas a medida). Lanzar un nuevo producto requiere dossier completo para registro.

**Sin Umbrella AI:** El equipo técnico produce cada dossier desde cero. 20 horas por producto = cuello de botella para escalar.

**Con Umbrella AI:** El equipo introduce las fórmulas candidateadas. Umbrella AI genera los dossiers en paralelo. El tiempo se invierte en decidir qué producto lanzar, no en redactar documentación.

### 3.3. Evaluación de viabilidad de nuevas formulaciones

Antes de comprometer recursos en una formulación, Ümbrella quiere verificar que es viable: ingredientes permitidos, claims disponibles, formato posible.

**Sin Umbrella AI:** Requiere estudio previo de 2-3 días por un técnico regulatorio.

**Con Umbrella AI:** Análisis de viabilidad en 10 minutos. El semáforo regulatorio indica inmediatamente qué ingredientes son problemáticos y por qué. Decisión informada antes de invertir en desarrollo.

---

## 4. Arquitectura técnica

**Stack tecnológico:**
- Orquestación: Agno Framework (Python)
- Modelos de lenguaje: OpenAI GPT-4o / Claude (configurable por agente)
- Búsqueda regulatoria: EFSA Journal, BELFRIT, AESAN, PubMed (en tiempo real)
- Base de datos: PostgreSQL + pgvector (para base de conocimiento, ver sección 4.1)
- Integración ERP: Navision / Business Central vía API OData (Fase 2)

**Arquitectura del sistema:**

**Esquema del sistema:**

```
                    ┌──────────────────────────────────┐
                    │         UMBRELLA AI              │
                    └──────────────────────────────────┘
                                     │
                    ┌─────────────────┴─────────────────┐
                    │     Orquestador (Agno)              │
                    └─────────────────┬─────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Ag. KIC        │      │ Ag. Regulatory │      │ Ag. Ficha       │
│  Ag. Formatos   │      │                 │      │ Ag. Claims      │
│  Ag. Docs Int.  │      │                 │      │                 │
│  Ag. QC         │      │                 │      │                 │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌──────────────┴──────────────┐
                    │    Informe ejecutivo         │
                    └─────────────────────────────┘
```

```
                                  FUENTES DE DATOS
    ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
    │ Fuentes          │   │ Base de          │   │ Navision /       │
    │ regulatorias      │   │ conocimiento      │   │ Business Central  │
    │                  │   │ (pgvector)       │   │ (API OData)       │
    │ • EFSA           │   │                  │   │                   │
    │ • AESAN          │   │ • Fichas         │   │ • Catálogo        │
    │ • BELFRIT        │   │   proveedores    │   │ • Lista de        │
    │ • PubMed         │   │ • Estudios int.  │   │   materiales      │
    │ • Reg. 432/2012 │   │ • AFEPDI         │   │ • Proveedores     │
    └──────────────────┘   └──────────────────┘   └──────────────────┘
```

**Flujo de datos:**
1. Usuario introduce fórmula → Orquestador la distribuye a agentes
2. Agentes consultan fuentes regulatorias públicas según necesidad
3. Agentes consultan base de conocimiento propietaria (Fase 2+)
4. Agentes consultan Navision para datos de producto (Fase 2)
5. Orquestador compila outputs y genera informe ejecutivo

### 4.1 Base de conocimiento y RAG

La base de conocimiento de Ümbrella no ha sido estudiada aún. Phase 0 tiene como objetivo entender su naturaleza antes de diseñar la solución.

**¿Qué es RAG y por qué importa?**

RAG (Retrieval-Augmented Generation) es una arquitectura que permite a los agentes consultar documentos propietarios como si fueran una base de conocimiento consultable. En lugar de depender solo del conocimiento interno del modelo (que puede ser inexacto o hallucinar), el agente recupera fragmentos relevantes de documentos y los usa para fundamentar sus respuestas.

**Componentes de un sistema RAG:**

```
Documentos fuentes (fichas proveedores, AFEPDI, internas)
        │
        ▼
  Chunking / Segmentación
        │
        ▼
  Embedding (modelo de transformadores)
        │
        ▼
  Índice vectorial (pgvector)
        │
        ▼
  Retrieval (búsqueda por similitud)
        │
        ▼
  Contexto para el agente LLM
```

**Complejidad real de integrar RAG:**

| Aspecto | Complejidad | Detalle |
|---------|-------------|---------|
| **Naturaleza de los documentos** | Variable | No sabemos si son PDFs, Word, estructura heterogénea, calidad variable |
| **Chunking óptimo** | Media-Alta | Cómo segmentar afecta directamente la calidad de retrieval. No existe una regla universal — requiere experimentación |
| **Calidad de embeddings** | Alta | Elegir el modelo de embedding correcto (sentence-transformers, OpenAI embeddings) es crítico para la precisión |
| **Freshness** | Continua | La base de conocimiento se queda obsoleta. ¿Cómo se actualiza? ¿Cada cuánto? |
| **Retrieval** | Media | Búsqueda por similitud funciona bien para texto, peor para tablas, imágenes, datos numéricos |
| **Evaluación** | Crítica | ¿Cómo medimos que RAG mejora los outputs vs. solo el conocimiento interno del modelo? |
| **Coste operativo** | No trivial | pgvector, embeddings, storage, recompute de índices |

**¿Es necesario RAG para Ümbrella?**

Phase 0 determina esto. Las preguntas clave son:
- ¿Los agentes necesitan consultar documentación propietaria de Ümbrella (fichas técnicas de proveedores, estudios internos) para dar respuestas precisas?
- ¿El conocimiento interno de los agentes (entrenado con normativa pública) es suficiente?
- ¿La información propietaria está estructurada o es documentos sueltos?

**Resultado posible de Phase 0:**
- RAG sí tiene sentido → Se diseña arquitectura, se estima coste adicional
- RAG no tiene sentido → Los agentes funcionan solo con normativas públicas y búsqueda web

Esta es la razón por la que Phase 0 es esencial antes de estimar el coste total del proyecto.

---

## 5. Modelo de implantación progresiva

Para Ümbrella, recomendamos una **implantación por fases progresivas** que permite validar el valor en cada paso. Como el sistema ya está desarrollado, la fase de validación puede ejecutarse con formulaciones reales de Ümbrella.

### Prerrequisitos para iniciar la Fase 0

Antes de comenzar la Fase 0 (Validación), es necesario disponer de:

**1. Cuenta de proveedor de modelos de lenguaje**

Es necesario disponer de una cuenta activa en un proveedor de modelos de lenguaje (LLM). Recomendamos **OpenRouter** por:
- Soporte para múltiples proveedores (OpenAI, Anthropic, Google, etc.) en una sola API
- Coste por uso, sin compromisos fijos
- proxies de uso para GPT-4o, Claude 3.5, y otros modelos optimizados para tareas técnicas
- Gestión de claves API centralizada

Alternativas viables:
- OpenAI API (directa)
- Anthropic API (directa)
- Azure OpenAI (para entornos enterprise)

**2. Entorno de ejecución**

El sistema requiere un entorno donde desplegar los agentes. Es necesario conocer:

- **Infraestructura disponible:** ¿ Ümbrella dispone de servidores propios, infraestructura cloud (Hetzner, otros), o se requiere un nuevo aprovisionamiento?
- **Acceso a Base de datos:** PostgreSQL + pgvector para persistencia de resultados y base de conocimiento vectorial
- **Acceso a red:** Los agentes necesitan acceso a internet para consultar fuentes regulatorias (EFSA, AESAN, BELFRIT) y, opcionalmente, al ERP (Navision) si está en la nube
- **Entorno de ejecución Python:** El sistema está desarrollado en Python (Agno Framework). Se requiere un entorno donde ejecutar los pipelines

**3. Acceso a Navision / Business Central (para Fase 2)**

Si se contempla la Fase 2 (Integración ERP), es necesario disponer de:
- **Versión de Navision:** ¿Cloud (Business Central) o legacy on-premise? Esto determina el tipo de API disponible (OData v4 para cloud, API SOAP/REST para legacy)
- Credenciales de API para Navision / Business Central
- Documentación del API OData disponible
- Acceso a los endpoints de catálogo de artículos, Lista de Materiales, y proveedores
- **Acceso a Dropbox (u otro almacenamiento):** ¿Hay documentación adicional almacenada en Dropbox o similar? Fichas de proveedores, especificaciones de materias primas, certificados de análisis pueden residir en almacenamiento externo y ser relevantes para la base de conocimiento

**4. Formulaciones de prueba**

Para la Fase 0, Ümbrella debe proporcionar 5 formulaciones representativas de su catálogo actual o en desarrollo. Estas formulaciones se usarán para:
- Validar la precisión de los outputs de los agentes
- Comparar con la documentación existente
- Estimar el ahorro real en tiempo

### Calendario

```
Semana  1   2   3   4   5   6   7   8   9   10  11  12  13  14
        ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
Fase 0  [■ ■ ■ ■ ■]
Fase 1  ───────[■ ■ ■]────
Fase 1b ───────────[■ ■]────
Fase 2  ────────────────[A determinar]────
Fase 3  ────────────────────────[A determinar]────
```

| Fase | Descripción | Duración | Entregable | Coste |
|------|-------------|----------|------------|-------|
| **Fase 0: Descubrimiento + Evaluación BC** | Entender naturaleza BC, evaluar RAG, refinar prompts con 5 fórmulas | **1 semana** | Informe con recomendación de arquitectura BC | **3.000 €** |
| **Fase 1: Core** | Desplegar 4 agentes (KIC, Regulatorio, Ficha Técnica, Claims) + testing | **2 semanas** | 4 agentes funcionando | **10.000 €** |
| **Fase 1b: Core completo** | Desplegar 4 agentes restantes + testing integrado | **2 semanas** | Pipeline completo 8 agentes | **7.500 €** |
| **Fase 2: Integración ERP** | Conexión Navision/Business Central + diseño RAG | **A determinar** | LM automatizada + BC estructurada | **A determinar tras Phase 0** |
| **Fase 3: Personalización** | Plantillas Ümbrella + formación + ingesta BC | **A determinar** | Sistema adaptado, equipo formado, BC operativa | **A determinar tras Phase 0** |

**Total mínimo (Fases 0+1+1b): 20.500 €**  
**Nota:** Las fases 2 y 3 se presupuestan tras conocer la versión de Navision, la cantidad y naturaleza de documentos en Navision/Dropbox, y el diseño óptimo de la base de conocimiento RAG.

### Detalle de cada fase

#### Fase 0: Descubrimiento + Evaluación de Base de Conocimiento (Semana 1) — 3.000 €

- Reunión de kick-off para definir fuentes por agente
- Inventario de documentación disponible:
  - Explorar Navision: ¿qué datos existen? (catálogo, LM, proveedores, precios)
  - Explorar Dropbox: ¿qué documentos hay? (fichas proveedores, certificados, specs)
  - Estimar volumen y estructura de la información
- Evaluación de arquitectura RAG:
  - ¿Qué documentos requieren ingesta?
  - ¿Qué estructura de chunks es óptima?
  - ¿Qué modelo de embeddings usar?
- Selección de 5 formulaciones representativas del catálogo de Ümbrella
- Refinamiento de prompts con las 5 fórmulas
- **Entregable:** Informe con:
  - Inventario de documentación disponible
  - Diseño recomendado de base de conocimiento (RAG)
  - Esfuerzo estimado para Fase 2 y 3
  - Recomendación de versiones de Navision y arquitectura

#### Fase 1: Core — Despliegue de 4 agentes (Semanas 2-3)

- Despliegue y configuración de los 4 agentes core:
  - Ag.1 KIC (Análisis de composición)
  - Ag.2 Regulatorio (Validación legal)
  - Ag.3 Ficha Técnica (Dossier AESAN)
  - Ag.4 Claims (Claims comerciales)
- Integración con fuentes regulatorias configuradas en Phase 0
- Testing con formulaciones de Ümbrella
- **Entregable:** Sistema funcionando con 4 agentes core, outputs validados
- **Coste:** 10.000 €

#### Fase 1b: Core completo — 4 agentes restantes (Semanas 4-5)

- Despliegue de los 4 agentes adicionales:
  - Ag.5 Etiqueta (Texto de etiqueta conforme Reg. 1169/2011)
  - Ag.6 Formatos (Innovación y reactividad)
  - Ag.7 Docs Internos (Lista de Materiales, proceso de fabricación)
  - Ag.8 QC (Plan de control de calidad Ph. Eur./ICH)
- Testing integrado de todos los agentes
- **Entregable:** Pipeline completo de 8 agentes, listo para producción
- **Coste:** 7.500 €

#### Fase 2: Integración ERP + Base de Conocimiento (a determinar) — Opcional

- Conexión con Navision / Business Central de Ümbrella (versión a determinar)
- Diseño e implementación de la arquitectura RAG según resultados de Phase 0
- Mapeo de artículos, proveedores y Lista de Materiales
- Ingesta de documentación de Navision y Dropbox a la base de conocimiento
- **Entregable:** Sistema con acceso a datos reales de ERP y base de conocimiento operativa
- **Coste adicional:** A determinar tras Phase 0

#### Fase 3: Personalización + Formación + BC Completa (a determinar) — Opcional

- Adaptación de outputs a las plantillas internas de Ümbrella
- Formación del equipo técnico (2 sesiones de 2h)
- Testing y validación de la base de conocimiento con casos reales
- Documentación de uso y procedimientos
- Soporte incluido durante 3 meses
- **Coste adicional:** A determinar tras Phase 0
- **Coste adicional:** 25.000 – 40.000 €

### Ventajas del modelo progresivo

| Ventaja | Descripción |
|---------|-------------|
| **Validación con datos reales** | Se prueba directamente con formulaciones de Ümbrella |
| **Riesgo mínimo** | Cada fase se valida antes de invertir en la siguiente |
| **Valor inmediato** | Con 4 agentes (Semana 4), el equipo ya puede trabajar más rápido |
| **Decisión en cada hito** | Tras ver resultados, Ümbrella decide si continúa |

---

## 6. Métricas de impacto

| Métrica | Antes | Después | Ahorro |
|---------|-------|---------|--------|
| Tiempo por formulación completa | 18-22h (técnico a 80 €/h) | 3-5 min | ~99% |
| Coste por formulación | 1.440 – 1.760 € (80 €/h × 18-22h) | 25 € (coste compute) | ~99% |
| Dossiers generados por mes | 15-20 | 80-120+ | 5-6x |
| Errores de transcripción normativa | Frecuentes (humano) | Prácticamente nulos | — |
| Trazabilidad regulatoria | Manual, incompleta | Automática, completa | — |
| Tiempo hasta dossier AESAN | 4-8 semanas | 1-2 semanas | 60-75% |

**Ejemplo de ROI para Ümbrella (desarrollo de 100 formulaciones/año):**
- Coste actual (100 × 1.600 €): **160.000 €/año**
- Coste con Umbrella AI (100 × 25 €): **2.500 €/año**
- **Ahorro anual:** 157.500 €
- **Break-even:** Con ~13 formulaciones se recupera la inversión total de Fases 0+1+1b (20.500 €) — menos de 2 meses a 100 formulaciones/año

---

## 7. Seguridad, confidencialidad y privacidad

### Infraestructura del sistema

El sistema puede desplegarse en diferentes configuraciones de infraestructura:

| Opción | Descripción | Adecuado para |
|--------|-------------|---------------|
| **Cloud (recomendado)** | Despliegue en Hetzner Cloud / VPS del cliente o en infraestructura propia de Ümbrella | Mayor flexibilidad, escalabilidad, coste optimizado |
| **On-premise** | Todo en servidores propios de Ümbrella | Requisitos de datos en premisa |
| **Híbrido** | Pipeline en cloud, datos sensibles on-premise | Equilibrio entre flexibilidad y control |

Durante la Fase 0 se evaluará la infraestructura disponible de Ümbrella y se recomendará la configuración óptima.

### Confidencialidad de datos

- **Fórmulas y documentación interna.** Las formulaciones introducidas por Ümbrella y los outputs generados son propiedad exclusiva de Ümbrella. No se comparten con terceros ni se usan para entrenar modelos.
- **Base de conocimiento regulatoria.** La normativa europea (Directivas, Reglamentos, listas BELFRIT/AESAN) es información pública. No requiere confidencialidad.
- **Datos de proveedores y precios.** La información de Navision (catálogo, precios, proveedores) permanece en el entorno de Ümbrella. El sistema solo consulta los datos necesarios vía API.
- **Fichas técnicas de proveedores.** Si se ingieren fichas de proveedores, permanecen cifradas en la base de datos de Ümbrella.

### Proveedor de LLM y privacidad

El uso de un proveedor de LLM (OpenRouter, OpenAI, Anthropic) implica el envío de prompts a servidores externos para inferencia. Consideraciones:

| Proveedor | Datos de entrenamiento | Cumplimiento |
|-----------|----------------------|--------------|
| **OpenRouter** | No entrena con datos de clientes (por defecto) | GDPR compliant |
| **OpenAI** | No entrena con datos de API por defecto (opt-in) | GDPR compliant |
| **Anthropic** | No entrena con datos de API | GDPR, SOC 2 |

**Recomendación:** Usar la configuración de no-entrenamiento (default en la mayoría de proveedores). Para máxima privacidad, considerar modelos auto-alojados (Mistral, Llama) en infraestructura propia.

### Auditoría y trazabilidad

- Cada output incluye las fuentes exactas consultadas — artículo, anexo, url si aplica
- Trazabilidad completa para cualquier inspección AESAN o auditoría interna
- Log de ejecuciones disponible para revisión

### Responsabilidad

- El sistema asiste y genera documentación. La validación final es siempre del equipo técnico de Ümbrella.
- Ümbrella mantiene la responsabilidad sobre la conformidad regulatoria de sus productos.

---

## 8. Inversión

La inversión se estructura en fases progresivas:

### Modelo progresivo

| Fase | Descripción | Duración | Inversión |
|------|-------------|----------|----------|
| **Fase 0: Descubrimiento + Evaluación BC** | Inventario docs, diseño RAG, refinar prompts | 1 semana | **3.000 €** |
| **Fase 1: Core** | Desplegar 4 agentes + testing | 2 semanas | **10.000 €** |
| **Fase 1b: Core completo** | Desplegar 4 agentes restantes + testing integrado | 2 semanas | **7.500 €** |
| **Fase 2: Integración ERP + RAG** | Conexión Navision + diseño e ingesta BC | **A determinar tras Phase 0** | **A determinar** |
| **Fase 3: Personalización** | Plantillas Ümbrella + formación + BC operativa | **A determinar** | **A determinar** |

### Inversión total por escenario

| Escenario | Fases | Total |
|-----------|-------|-------|
| **Core** | 0 + 1 + 1b | **20.500 €** |
| **Core + ERP + BC** | 0 + 1 + 1b + 2 | **A determinar tras Phase 0** |
| **Completo** | 0 + 1 + 1b + 2 + 3 | **A determinar tras Phase 0** |

**Mantenimiento anual (opcional):** 8.000 – 12.000 €/año (soporte, actualizaciones regulatorias, compute)

### Forma de pago

- **Fase 0:** 100% al inicio
- **Fase 1:** 50% inicio, 50% al delivery
- **Fases 1b, 2 y 3:** Pago en hitos según alcance

### ROI

Con las Fases 0 + 1 + 1b (20.500 €) y 100 formulaciones/año:
- **Ahorro anual:** 157.500 €
- **ROI primer año:** 669%
- **Payback:** 2 meses

---

## 9. Próximos pasos

1. **Reunión de 30 minutos** — Revisar la propuesta y validar el encaje con las necesidades de Ümbrella
2. **Selección de 5 formulaciones** — Elegir formulaciones representativas del catálogo para la validación
3. **Fase 0: Descubrimiento (1 semana)** — 3.000 €. Incluye inventario de documentación, diseño RAG, refinado de prompts
4. **Revisión de resultados** — Informe con diseño de arquitectura BC, estimación de esfuerzo para Fases 2 y 3
5. **Decisión** — ¿Continuar con Fase 1?
6. **Fases 1 y 1b (4 semanas)** — Despliegue del pipeline completo de 8 agentes
7. **Decisión sobre Fases 2 y 3** — Tras conocer el diseño de BC y versión de Navision

---

## 10. Sobre Ümbrella y Umbrella AI

Ümbrella Flavours & Functional Ingredients, S.L. es una empresa especializada en ingredientes funcionales y complementos alimenticios, con experiencia en formulación a medida y fabricación propia.

Umbrella AI nació de la necesidad interna de Ümbrella: un equipo técnico dedicando horas a tareas repetitivas (buscar normativa, calcular claims, redactar fichas) cuando podría estar innovando en nuevas fórmulas.

El sistema Umbrella AI ya está en uso interno para el desarrollo de fórmulas propias. Esta propuesta es para completar la implantación, integrar con Navision, y formalizar el sistema para uso en producción con el equipo de Ümbrella.

---

*Este documento es confidencial.*
