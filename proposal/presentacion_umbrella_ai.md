---
marp: true
theme: default
paginate: true
lang: es
style: |
  section {
    background: #ffffff;
    font-family: 'Inter', 'Helvetica Neue', sans-serif;
  }
  h1 {
    color: #1a1a2e;
  }
  h2 {
    color: #16213e;
    border-bottom: 3px solid #0f3460;
    padding-bottom: 0.5em;
  }
  table {
    font-size: 0.8em;
  }
  th {
    background: #0f3460;
    color: white;
    padding: 0.5em 1em;
  }
  td {
    border-bottom: 1px solid #ddd;
    padding: 0.4em 1em;
  }
  blockquote {
    border-left: 4px solid #0f3460;
    padding-left: 1em;
    color: #555;
  }
  code {
    background: #f4f4f8;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 0.85em;
  }
  strong {
    color: #0f3460;
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2em;
  }
---

<!-- Slide 1 -->

# Umbrella AI

## Plataforma Inteligente de Desarrollo de Complementos Alimentarios

**De 3 semanas a 5 minutos**

---

<!-- Slide 2 -->

# El problema

<div class="columns">
<div>

### Hoy: proceso manual

- Un técnico consulta la Directiva 2002/46/CE
- Otro verifica claims en el Reg. 432/2012
- Otro elabora la ficha técnica
- Otro revisa interacciones
- Otro redacta la etiqueta
- Otro diseña el plan de QC

</div>
<div>

### Consecuencias

- 18-25 horas por formulación
- 8 documentos de 8 personas distintas
- Errores de transcripción frecuentes
- Cada cambio = empezar de cero
- Claim no autorizada = sanción
- Dosis errónea = devolución AESAN

</div>
</div>

---

<!-- Slide 3 -->

# En números

| Métrica | Hoy | Con Umbrella AI |
|--------|------|----------------|
| Horas por formulación | 18-25h | 5-10 min |
| Dossiers / mes (equipo de 3) | 15-20 | 80-120+ |
| Coste por dossier | 400-600€ | 5-15€ |
| Tiempo hasta registro AESAN | 4-8 semanas | 1-2 semanas |
| Errores de transcripción | Frecuentes | ~0 |
| Trazabilidad normative | Manual | Automática |

---

<!-- Slide 4 -->

# La solución

**8 agentes de IA especializados** que ejecutan todo el ciclo de desarrollo en paralelo

```
Fórmula → Umbrella AI → 8 documentos + informe ejecutivo
```

El usuario introduce una fórmula. Los agentes trabajan en paralelo. El sistema entrega resultados en minutos con referencias normativas exactas.

---

<!-- Slide 5 -->

# Los 8 agentes

| Agente | Entrega | Ahorro |
|--------|---------|--------|
| **KIC** — Composición | Clasificación, biodisponibilidad, interacciones | 3-4h |
| **Regulatorio** — Validación legal | Semáforo por ingrediente (✅⚠️❌) | 2-3h |
| **Ficha Técnica** — Dossier AESAN | Composición, alérgenos, nutricional | 3-4h |
| **Claims** — Claims comerciales | Claims autorizados, selling points | 2-3h |
| **Etiqueta** — Texto de etiqueta | Cara principal, secundaria, lateral | 2h |
| **Formatos** — Innovación | Evaluación de formatos, reactividad | 1-2h |
| **Docs Internos** — Producción | Lista materiales NAVISION, fabricación | 2-3h |
| **QC** — Control de calidad | Plan FTIR, estabilidad ICH Q1A | 2-3h |

---

<!-- Slide 6 -->

# Ejemplo: entrada y salida

**Entrada (30 segundos):**

```text
Inmuno Complex Pro
- Vitamina C (ác. ascórbico): 120mg (150% VRN)
- Zinc (gluconato): 10mg (100% VRN)
- Vitamina D3 (colecalciferol): 15μg (300% VRN)
- Equinácea (extracto 4:1): 200mg
- Propóleo (extracto): 150mg
```

**Salida (3-5 minutos):**

8 documentos completos + informe ejecutivo con veredicto de viabilidad, alertas cruzadas y fuentes normativas

---

<!-- Slide 7 -->

# ¿Cómo funciona?

```
Batch 1 (paralelo)         Batch 2
├── KIC ──────────────┐     └── Regulatorio
├── Formatos            │            │
├── Docs Internos       │            ▼
└── QC                 │     Batch 3 (paralelo)
                         │     ├── Ficha Técnica ─┐
                         │     └── Claims ────────┤
                         │                        ▼
                         └────────── Etiqueta
```

Cada agente recibe **solo el contexto que necesita** del anterior. Sin contaminación cruzada. Los 4 batches se ejecutan en ~3 minutos.

---

<!-- Slide 8 -->

# Diferenciadores

<div class="columns">
<div>

### Precisión, no aproximación

Los valores NRV y límites de dosificación son los **exactos** de la normativa UE. Nunca "aproximadamente correctos".

### Integración Navision

Stock, precios y códigos de artículo reales consultados en tiempo real. BOMs con referencias reales.

</div>
<div>

### Auditoría completa

Cada decisión traza la referencia normativa exacta consultada. Si AESAN pregunta, el rastro existe.

### Escala sin fricción

Añadir un agente (costes, packaging, estabilidad) = un archivo de configuración.

</div>
</div>

---

<!-- Slide 9 -->

# Caso de uso: laboratorio

### Sin Umbrella AI

1. Técnico busca ingredientes y verifica normativa (2 días)
2. Elabora ficha técnica (1 día)
3. Calcula claims permitidas (medio día)
4. Redacta etiqueta (medio día)
5. Diseña plan de QC (1 día)
6. **Total: 1-2 semanas por variante**

### Con Umbrella AI

1. Introduce 4 variantes de fórmula
2. Recibe 4 informes completos en 15 minutos
3. Compara viabilidad y selecciona la mejor
4. **Total: 15 minutos para 4 opciones**

---

<!-- Slide 10 -->

# Caso de uso: fabricante / distribuidor

### Sin Umbrella AI

- 30 nuevos productos/año
- 20h de trabajo técnico por producto
- **600 horas/año** de salario senior
- Cuello de botella permanente

### Con Umbrella AI

- 30 productos introducidos en paralelo
- El equipo revisa y valida, no redacta desde cero
- **Tiempo ahorrado: 500+ horas/año**
- El equipo se dedica a decisiones, no a transcripción

---

<!-- Slide 11 -->

# Arquitectura

```
Fórmula
    │
    ▼
┌─────────────────────────────────────┐
│         Umbrella AI Pipeline         │
│                                     │
│  8 agentes especializados           │
│  (paralelo por batches)            │
│                                     │
├─────────┬───────────┬──────────────┤
│         │           │              │
│ ▼       ▼           ▼              ▼
YAML   pgvector    Navision API
(regla-  (documentos (stock,
toria)  proveedores)  precios)
└─────────────────────────────────────┘
```

---

<!-- Slide 12 -->

# Plan de implantación

| Fase | Duración | Entregable |
|------|----------|------------|
| **1. Validación** | 4 semanas | Prueba con 5-10 formulaciones reales |
| **2. Integración** | 4-6 semanas | Conexión ERP + plantillas personalizadas |
| **3. Producción** | 2 semanas | Sistema en producción + formación |

> La Fase 1 se ejecuta **sin coste** para el prospecto.

---

<!-- Slide 13 -->

# Seguridad y confidencialidad

- **Datos:** Las formulaciones permanecen en el entorno del cliente. Nunca se comparten.
- **Conocimiento:** Normativa pública + datos propietarios cifrados en la base del cliente.
- **Cumplimiento:** El sistema asiste, no decide. Responsabilidad humana final. Cada output incluye fuentes normativas.
- **Acceso:** Control por roles (lectura, ejecución, administración).

---

<!-- Slide 14 -->

# Próximos pasos

1. **Reunión de 30 min** para entender sus necesidades
2. **Seleccionar 5-10 formulaciones** representativas
3. **Ejecutar la prueba** (5-7 días laborables)
4. **Revisar resultados** conjuntamente
5. **Propuesta de implantación** personalizada

> No hay compromiso. La prueba es gratuita.

---

<!-- Slide 15 -->

# Contacto

**Umbrella AI**

- [Nombre]
- [Cargo]
- [Email]
- [Teléfono]

---

**¿Una pregunta?**

[Email / teléfono]
