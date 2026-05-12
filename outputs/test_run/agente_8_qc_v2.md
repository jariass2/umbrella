# Agente 8: QC v2

**Fase 1 ftir:**
  **Objetivo:** Identificación inequívoca de cada materia prima activa y verificación de identidad del mix final, detectando sustituciones o adulteraciones
  **Metodologia general:**
    **Nombre:** FTIR-ATR
    **Tecnica:** Espectroscopía infrarroja por transformada de Fourier con reflectancia total atenuada
    **Equipo:** Espectrómetro FTIR equipado con cristal de diamante ATR
    **Software:** Comparación espectral por índice de correlación (algoritmo Pearson o comparable)
  **Control mix final:**
    **Criterio aceptacion:** Índice de correlación ≥0,98 respecto al espectro de referencia del mix maestro validado; factor de concordancia ≥95% para picos marcadores de cada activo
  **Espectros referencia:**
    **Vitamina c (ácido ascórbico):**
      **Picos principales:**
        -
          **Numero onda:** 1750-1760
          **Asignacion:** Ester C=O (lactona)
        -
          **Numero onda:** 3300-3400
          **Asignacion:** OH alcohólico y enol (banda ancha asociada)
        -
          **Numero onda:** 1650
          **Asignacion:** C=C alquénico conjugado
      **Criterio aceptacion:** Concordancia posicional de picos ±5 cm⁻¹ vs referencia
    **Zinc (gluconato):**
      **Picos principales:**
        -
          **Numero onda:** 1600
          **Asignacion:** Carboxilato asimétrico (COO⁻)
        -
          **Numero onda:** 1080
          **Asignacion:** C-O alcohólico
        -
          **Numero onda:** 3400
          **Asignacion:** OH de humedad/hidroxilos (banda ancha)
      **Criterio aceptacion:** Concordancia posicional de picos ±5 cm⁻¹ vs referencia
    **Magnesio (bisglicinato):**
      **Picos principales:**
        -
          **Numero onda:** 1590-1610
          **Asignacion:** Carboxilato asimétrico (COO⁻) quelado
        -
          **Numero onda:** 1400-1410
          **Asignacion:** Carboxilato simétrico (COO⁻)
        -
          **Numero onda:** 3300-3500
          **Asignacion:** NH/OH (banda ancha de amina e hidroxilos)
        -
          **Numero onda:** 1500-1550
          **Asignacion:** Deformación N-H
      **Criterio aceptacion:** Concordancia posicional de picos ±5 cm⁻¹ vs referencia; ausencia de picos de glicina libre a ~1710-1720 cm⁻¹ (ácido carboxílico no ionizado)
  **Deteccion adulteracion:**
    **Descripcion:** Se comparan frente a biblioteca de espectros de excipientes comunes y sustancias de relleno fraudulentas (almidón, maltodextrina, carbonato cálcico). Desviaciones >5 cm⁻¹ en picos marcadores o aparición de bandas extrañas (ej. 1710 cm⁻¹ indicando ácido carboxílico libre en lugar de quelato) rechazan el lote.
  **Frecuencia:** CADA_LOTE
**Fase 2 granulometria:**
  **Objetivo:** Garantizar la fluidez del polvo, minimizar la segregación durante el transporte y asegurar la homogeneidad de la mezcla en la dosificación
  **Metodo primario:**
    **Nombre:** Difracción láser
    **Norma:** ISO 13320:2020
    **Equipo:** Difractómetro láser en modo seco o húmedo según adecuación del material
    **Dispersante:** Aire comprimido seco (método seco) o isopropanol (método húmedo si el polvo es cohesivo)
  **Especificaciones generales:**
    **D10:** >10 µm (control de fines excesivos que aumentan cohesión)
    **D50:** 50-150 µm (tamaño mediano óptimo para mezcla y fluidez)
    **D90:** <300 µm (prevención de segregación por arrastre de partículas grandes)
  **Criterio homogeneidad:**
    **Descripcion:** RSD ≤5% en 10 puntos de muestreo espacialmente distribuidos en el mixer (ensayo de homogeneidad del mix previo al envasado)
    **Metodo:** Muestreo por thief probe en diferentes profundidades y alturas; análisis de contenido de Mg o Zn como marcadores
  **Frecuencia:** CADA_LOTE
**Fase 3 densidad:**
  **Objetivo:** Caracterizar la reología del polvo para predecir problemas de flujo en dosificación, llenado y almacenamiento
  **Metodos:**
    **Densidad aparente:**
      **Nombre:** Densidad aparente (bulk density)
      **Norma:** Ph. Eur. 2.9.15
      **Tecnica:** Vertido libre en cilindro gradado de 100 mL; pesada
      **Rango especificacion:** 0.40-0.70 g/cm³
    **Densidad compactada:**
      **Nombre:** Densidad compactada (tapped density)
      **Norma:** Ph. Eur. 2.9.34
      **Tecnica:** Golpeteo mecanizado (1250 golpes)
      **Rango especificacion:** Reportar valor y calcular índices
  **Indices reologia:**
    **Indice carr:**
      **Nombre:** Índice de compresibilidad de Carr
      **Formula:** ((densidad_compactada - densidad_aparente) / densidad_compactada) × 100
      **Rango especificacion:** <20% (buena fluidez)
      **Interpretacion:** 15-20% aceptable; >25% rechazado por riesgo de formación de puentes
    **Indice hausner:**
      **Nombre:** Índice de Hausner
      **Formula:** densidad_compactada / densidad_aparente
      **Rango especificacion:** <1.25
      **Interpretacion:** Polvo de libre flujo; ≥1.25 indica cohesividad
  **Frecuencia:** CADA_LOTE
**Fase 4 ph:**
  **Objetivo:** Control del pH de la matriz en suspensión como indicador indirecto de estabilidad química y ausencia de degradación/degradados ácidos
  **Preparacion muestra:**
    **Concentracion:** 5% p/v
    **Disolvente:** Agua destilada libre de CO₂
    **Agitacion:** Agitación magnética 5 min; reposo 2 min antes de medida
  **Condiciones medicion:**
    **Temperatura:** 20 ± 2°C
    **Equipo:** pH-metro calibrado con buffer 4,0; 7,0 y 10,0 (Ph. Eur. 2.2.3)
  **Rango esperado:**
    **Ph min:** 4.5
    **Ph max:** 6.5
    **Justificacion:** El ácido ascórbico es estable entre pH 4-6; el bisglicinato de magnesio y el gluconato de zinc mantienen solubilidad y estabilidad quelática/química en este rango, evitando precipitación de hidróxidos metálicos a pH alcalino o hidrólisis ácida extrema.
  **Especificacion aceptacion:** pH entre 4.5 y 6.5 en suspensión al 5% p/v a 20 ± 2°C
  **Impacto fuera rango:**
    **Vitamina c:** A pH >7 se inicia la oxidación irreversible a ácido deshidroascórbico y 2,3-diketogulonico, con pérdida de actividad y amarilleamiento. A pH <3 la degradación por hidrólisis de la lactona se acelera y puede resultar irritante.
    **Zinc gluconato:** A pH >8 el Zn²⁺ precipita como Zn(OH)₂; a pH muy ácido se disocia del gluconato, alterando biodisponibilidad.
    **Magnesio bisglicinato:** A pH >8.5 precipita Mg(OH)₂ y puede romperse el quelato; a pH <4 la glicina se protona, debilitando la estabilidad del complejo y liberando Mg²⁺ libre.
  **Frecuencia:** CADA_LOTE
**Fase 5 aspecto organoleptico:**
  **Descripcion producto:** Polvo fino y homogéneo de color blanco a blanco-crema, inodoro o con ligero olor ácido característico
  **Criterios aceptacion:**
    **Color:** Blanco a blanco-crema uniforme. Variación intra-lote ΔE* <2 respecto a patrón maestro (escala CIE L*a*b* si se dispone de colorímetro)
    **Olor:** Inodoro a ligeramente ácido característico del ácido ascórbico, sin notas rancias ni amoniacales
    **Textura:** Polvo fino, seco, libre de grumos, aglomerados o partículas extrañas
    **Criterio rechazo:** Apelmazamiento superior al 10% en peso tras tamizado por malla 1 mm; decoloración amarillenta/naranja intensa (signo de oxidación de vitamina C); presencia de manchas oscuras; olor rancio, metálico o desagradable
  **Metodo inspeccion:**
    **Nombre:** Inspección visual y táctil
    **Condiciones:** Luz estándar D65, fondo blanco/neutro, observador entrenado. Tacto con guantes para detectar aglomerados.
    **Muestra:** Mínimo 50 g observada en bandeja Petri blanca extendida en capa fina
  **Frecuencia:** CADA_LOTE
**Fase 6 ensayos analiticos adicionales:**
  **Cuantificacion activos:**
    -
      **Parametro:** Vitamina C (ácido ascórbico)
      **Metodo:** HPLC-UV (Ph. Eur. monografía Ácido ascórbico) o titulación iodométrica (Ph. Eur. 2.5.11)
      **Especificacion:** 90% - 110% del valor declarado en etiqueta (≥72 mg y ≤88 mg por dosis)
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Zinc (Zn)
      **Metodo:** ICP-OES (Ph. Eur. 2.2.22) o complejometría con EDTA (monografía Zinc gluconate Ph. Eur.)
      **Especificacion:** 90% - 110% del valor declarado en etiqueta (≥9 mg y ≤11 mg por dosis de Zn)
      **Nota:** El resultado se expresa como Zn elemental
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Magnesio (Mg)
      **Metodo:** ICP-OES (Ph. Eur. 2.2.22) o complejometría con EDTA (monografía Magnesii bisglycinas Ph. Eur.)
      **Especificacion:** 90% - 110% del valor declarado en etiqueta (≥180 mg y ≤220 mg por dosis de Mg)
      **Nota:** El resultado se expresa como Mg elemental
      **Frecuencia:** CADA_LOTE
  **Uniformidad contenido:**
    **Parametro:** Uniformidad de unidades de dosificación (por dosis)
    **Metodo:** Ph. Eur. 2.9.40 (Dosage units) o 2.9.6 según formato; si es polvo a granel sin unidades individuales: homogeneidad del mix (Ph. Eur. 2.9.5)
    **Especificacion:** RSD ≤6.0% (Aceptación 1: L1 ≤15; Aceptación 2: L2 ≤25 según valoración de contenido analítico por unidad)
    **Frecuencia:** CADA_LOTE
  **Microbiologia:**
    **Referencia normativa:** Reglamento (CE) 2073/2005 y guías de criterios microbiológicos para suplementos alimenticios
    **Criterios microbiologicos:**
      -
        **Parametro:** Recuento aerobios mesófilos (TAMC)
        **Criterio:** ≤1×10⁴ UFC/g (n=5, c=2, m=10⁴, M=10⁵)
        **Frecuencia:** CADA_LOTE
      -
        **Parametro:** Recuento de levaduras y mohos (TYMC)
        **Criterio:** ≤1×10³ UFC/g (n=5, c=2, m=10³, M=10⁴)
        **Frecuencia:** CADA_LOTE
      -
        **Parametro:** Escherichia coli
        **Criterio:** Ausente en 10 g (n=5, c=0)
        **Frecuencia:** CADA_LOTE
      -
        **Parametro:** Salmonella spp.
        **Criterio:** Ausente en 25 g (n=5, c=0)
        **Frecuencia:** CADA_LOTE
  **Metales pesados:**
    **Metodo:** ICP-MS o ICP-OES (Ph. Eur. 2.4.20 / 2.2.22)
    **Criterios:**
      -
        **Elemento:** Plomo (Pb)
        **Limite:** ≤1.0 mg/kg
      -
        **Elemento:** Cadmio (Cd)
        **Limite:** ≤0.3 mg/kg
      -
        **Elemento:** Mercurio (Hg)
        **Limite:** ≤0.1 mg/kg
      -
        **Elemento:** Arsénico (As)
        **Limite:** ≤1.0 mg/kg
    **Frecuencia:** CADA_LOTE
  **Humedad:**
    **Parametro:** Pérdida por desecación o contenido de agua
    **Metodo:** Ph. Eur. 2.2.32 (Pérdida por desecación, 105°C hasta peso constante) o Karl Fischer (2.5.12) si es crítico
    **Especificacion:** ≤3.0% p/p
    **Frecuencia:** CADA_LOTE
**Fase 7 plan estabilidad:**
  **Normativa base:** ICH Q1A(R2) y ICH Q1B (fotoestabilidad)
  **Zona climatica:** Zona II (25°C ± 2°C / 60% HR ± 5%)
  **Numero lotes:** 3
  **Vida util estimada:**
    **Objetivo meses:** 24
    **Alcanzable:** True
    **Condiciones almacenamiento:** Conservar en lugar fresco y seco (≤25°C); envase primario hermético opaco (protección frente a luz y humedad)
  **Condiciones estudio:**
    -
      **Tipo:** Larga duración
      **Temperatura:** 25°C ± 2°C
      **Humedad relativa:** 60% ± 5%
      **Duracion:** 24 meses
      **Orientacion:** Envases primarios en posición vertical u horizontal según peor caso; protegidos de luz directa
    -
      **Tipo:** Acelerado
      **Temperatura:** 40°C ± 2°C
      **Humedad relativa:** 75% ± 5%
      **Duracion:** 6 meses
    -
      **Tipo:** Fotodegradación
      **Norma:** ICH Q1B
      **Exposicion:** ≥1.2 millones de lux·h y 200 Wh/m² en rango 320-400 nm
      **Condicion:** Muestras expuestas directamente y con envase; comparación vs oscuridad
  **Cronograma estudio:**
    **Puntos tiempo:**
      -
        **Tiempo:** T=0
        **Condicion:** Larga duración y Acelerado
        **Parametros monitorizados:**
          - Aspecto organoléptico
          - pH (suspensión 5%)
          - Humedad
          - Vitamina C (mg/dosis)
          - Zinc (mg/dosis)
          - Magnesio (mg/dosis)
          - Microbiología
      -
        **Tiempo:** T=3m
        **Condicion:** Larga duración y Acelerado
        **Parametros monitorizados:**
          - Aspecto organoléptico
          - pH
          - Humedad
          - Vitamina C
          - Zinc
          - Magnesio
      -
        **Tiempo:** T=6m
        **Condicion:** Larga duración y Acelerado
        **Parametros monitorizados:**
          - Aspecto organoléptico
          - pH
          - Humedad
          - Vitamina C
          - Zinc
          - Magnesio
      -
        **Tiempo:** T=9m
        **Condicion:** Larga duración
        **Parametros monitorizados:**
          - Aspecto organoléptico
          - pH
          - Humedad
          - Vitamina C
          - Zinc
          - Magnesio
      -
        **Tiempo:** T=12m
        **Condicion:** Larga duración
        **Parametros monitorizados:**
          - Aspecto organoléptico
          - pH
          - Humedad
          - Vitamina C
          - Zinc
          - Magnesio
          - Microbiología
      -
        **Tiempo:** T=18m
        **Condicion:** Larga duración
        **Parametros monitorizados:**
          - Aspecto organoléptico
          - pH
          - Humedad
          - Vitamina C
          - Zinc
          - Magnesio
      -
        **Tiempo:** T=24m
        **Condicion:** Larga duración
        **Parametros monitorizados:**
          - Aspecto organoléptico
          - pH
          - Humedad
          - Vitamina C
          - Zinc
          - Magnesio
          - Microbiología
  **Criterios fin vida util:**
    -
      **Criterio:** Contenido de activos
      **Descripcion:** Descenso por debajo del 90% del valor declarado en etiqueta para vitamina C, zinc o magnesio
    -
      **Criterio:** Cambio organoléptico
      **Descripcion:** Decoloración amarillenta/naranja intensa, apelmazamiento superior al 10%, olor rancio o desviación táctil respecto a T=0
    -
      **Criterio:** Humedad
      **Descripcion:** Incremento >3.0% p/p que favorece degradación química y crecimiento microbiológico
    -
      **Criterio:** Microbiología
      **Descripcion:** Cualquier resultado fuera de especificación según Reglamento (CE) 2073/2005
**Fase 8 resumen ejecutivo:** El plan de control de calidad de Test Mineral Boost prioriza la verificación de identidad por FTIR-ATR de cada materia prima (magnesio bisglicinato, zinc gluconato y ácido ascórbico) y del mix final, asegurando la ausencia de adulteraciones con un índice de correlación ≥0,98. Se controlarán críticamente la granulometría (D50 50-150 µm, D90 <300 µm), los índices de fluidez (Carr <20%, Hausner <1,25) y el pH en suspensión al 5% (4,5-6,5), dado que la estabilidad de la vitamina C y la integridad de los minerales quelatos dependen de una matriz seca y de pH controlado. Todos los activos se cuantificarán analíticamente en cada lote (HPLC/titulación para vitamina C; ICP-OES/complejometría para Mg y Zn), junto con microbiología según CE 2073/2005, metales pesados y humedad ≤3%. El estudio de estabilidad ICH Q1A(R2) en 3 lotes (Zona II y acelerado 40°C/75% HR) confirmará los 24 meses de vida útil, monitorizando especialmente el descenso de vitamina C (termolábil y fotosensible) y el incremento de humedad. Se recomienda muestreo 100% de identidad para MP y análisis completo por lote de producto terminado, manteniendo la zona de mezcla a HR <40% y utilizando envases opacos herméticos para mitigar riesgos de oxidación y degradación fotoquímica.
**Metadata:**
  **Version:** 2.0
  **Disclaimer:** Este plan QC es orientativo y debe ser adaptado y validado por el laboratorio de control de calidad antes de su implementación comercial.
  **Fecha generacion:** 2024-05-24
  **Producto:** Test Mineral Boost
** trazabilidad:**
  **Prompt version:** 2.0.0
  **Model:** moonshotai/kimi-k2.6
  **Base url:** https://openrouter.ai/api/v1
  **Timestamp utc:** 2026-05-12T14:59:13+00:00
  **Duration s:** 632.57
  **Attempts:** 1
  **Transient retries:** 0
  **Deterministic retries:** 0

---
## Fuentes consultadas

[1] **ICH Q1A(R2) Stability Testing of New Drug Substances and Products** _normativa_
[2] **ICH Q1B Photostability Testing of New Drug Substances and Products** _normativa_
[3] **Ph. Eur. 11.0 - Monografías Ácido ascórbico, Zinc gluconate, Magnesii bisglycinas; Capítulos 2.2.3, 2.2.22, 2.4.20, 2.5.11, 2.5.12, 2.9.6, 2.9.15, 2.9.34, 2.9.40** _normativa_
[4] **Reglamento (CE) 2073/2005 del Parlamento Europeo y del Consejo, de 15 de noviembre de 2005, relativo a los criterios microbiológicos aplicables a los productos alimenticios** _normativa_
[5] **ISO 13320:2020 Particle size analysis — Laser diffraction methods** _normativa_
[6] **Conocimiento experto en control de calidad de complementos alimentarios y matrices sólidas** _conocimiento_experto_