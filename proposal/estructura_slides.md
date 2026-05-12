# Estructura de Presentación — Umbrella AI
## 12-15 diapositivas, ~20 minutos

---

### Slide 1: Portada

**Umbrella AI**
Plataforma Inteligente de Desarrollo de Complementos Alimentarios

[Logo empresa]

---

### Slide 2: El problema (ahora)

- Desarrollar un complemento = 18-25 horas de trabajo manual
- 8 documentos distintos producidos por 8 personas distintas
- Errores de transcripción entre documentos
- Cada cambio de fórmula = empezar de cero
- Un claim no autorizado = sanción
- Una dosis errónea = devolución AESAN

**Visual:** Timeline mostrando 8 personas trabajando en secuencia con un reloj de 3 semanas

---

### Slide 3: El problema (en números)

| Métrica | Valor actual |
|---------|-------------|
| Horas por formulación | 18-25 |
| Dossiers/mes (equipo de 3) | 15-20 |
| Coste por dossier | 400-600€ |
| Tiempo hasta registro AESAN | 4-8 semanas |
| Trazabilidad de decisiones | Manual, incompleta |

---

### Slide 4: La solución

**Umbrella AI:** 8 agentes de IA especializados que ejecutan todo el ciclo de desarrollo en paralelo, en minutos.

- Introduces una fórmula
- Los 8 agentes trabajan en paralelo
- Recibes los 8 documentos + informe ejecutivo
- Incluye referencias normativas exactas

**Visual:** Diagrama del pipeline con los 8 agentes en batches paralelos, flechas de dependencia

---

### Slide 5: Los 8 agentes

| Agente | Genera | Tiempo manual ahorrado |
|--------|---------|----------------------|
| KIC | Análisis de composición, interacciones, biodisponibilidad | 3-4h |
| Regulatorio | Semáforo legal por ingrediente | 2-3h |
| Ficha Técnica | Dossier completo para AESAN | 3-4h |
| Claims | Claims autorizados + selling points | 2-3h |
| Etiqueta | Texto conforme a 1169/2011 | 2h |
| Formatos | Evaluación de formatos e innovación | 1-2h |
| Docs Internos | Lista de materiales NAVISION, proceso fabricación | 2-3h |
| QC | Plan de control de calidad (FTIR, ICH Q1A) | 2-3h |

**Total ahorrado por formulación: 18-25 horas**

---

### Slide 6: Demo en vivo

- Mostrar la entrada de una fórmula real
- Mostrar los outputs generados (al menos 2-3 agentes)
- Resaltar que todo se genera en paralelo, no en secuencia
- Mostrar el informe ejecutivo con el veredicto de viabilidad

**Nota:** Si no es posible demo en vivo, capturas de pantalla con la ejecución real

---

### Slide 7: 3 casos de uso

**Laboratorio:** 4 variantes de una misma formulación evaluadas en 15 min en lugar de 2 semanas

**Fabricante:** Escalar de 30 a 200 dossiers/año sin aumentar el equipo técnico

**Distribuidor:** Evaluar 5 proveedores en paralelo y tomar decisión informada en horas, no semanas

---

### Slide 8: Diferenciadores

1. **Precisión, no aproximación** — NRV y dosis máximas son los valores exactos de la normativa, no "aproximadamente"
2. **Integración Navision** — Stock, precios y códigos de artículo reales, no placeholders
3. **Auditoría completa** — Cada decisión traza la normativa exacta consultada
4. **Escala sin fricción** — Añadir un agente = un archivo de configuración

---

### Slide 9: Arquitectura

**Visual:** Diagrama simplificado mostrando:
- Entrada (fórmula) → Pipeline de agentes → Outputs
- Tres capas de conocimiento: estructurada (YAML), documental (pgvector), ERP (Navision API)
- Modelos configurables por agente (puede usar los del cliente)

---

### Slide 10: Plan de implantación

| Fase | Duración | Entregable |
|------|----------|------------|
| 1. Validación | 4 semanas | Prueba con 5-10 formulaciones reales |
| 2. Integración | 4-6 semanas | Conexión ERP + plantillas personalizadas |
| 3. Producción | 2 semanas | Sistema en producción + formación del equipo |

**Fase 1 sin coste para el prospecto** (prueba de valor)

---

### Slide 11: Impacto medido

| Métrica | Antes | Después |
|---------|-------|---------|
| Tiempo por formulación | 18-25h | 5-10 min |
| Dossiers por mes | 15-20 | 80-120+ |
| Coste por dossier | 400-600€ | 5-15€ |
| Errores de transcripción | Frecuentes | Prácticamente nulos |
| Tiempo hasta registro AESAN | 4-8 semanas | 1-2 semanas |

---

### Slide 12: Seguridad

- Datos del cliente: permanecen en su entorno, nunca se comparten
- Base de conocimiento: normativa pública + datos propietarios cifrados
- Cumplimiento: el sistema asiste, no decide. Responsabilidad humana final.
- Control de acceso por roles

---

### Slide 13: Próximos pasos

1. Reunión de 30 min para entender sus necesidades
2. Selección de 5-10 formulaciones representativas
3. Ejecución de la prueba (5-7 días laborables)
4. Revisión conjunta de resultados
5. Propuesta de implantación personalizada

---

### Slide 14: Contacto

**Umbrella Group**

[Nombre]
[Cargo]
[Email]
[Teléfono]

[Logo]

**¿Una pregunta?** [Email/telefono]
