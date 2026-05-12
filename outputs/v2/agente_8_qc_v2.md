# Agente 8: QC v2

**Fase 1 ftir:**
  **Objetivo:** Identificación de materias primas y control de identidad del mix final mediante comparación espectral
  **Metodologia general:**
    **Nombre:** FTIR-ATR
    **Tecnica:** Espectroscopía infrarroja por transformada de Fourier con reflectancia total atenuada
    **Equipo:** FTIR con cristal ATR de diamante, resolución 4 cm⁻¹, rango 4000-600 cm⁻¹, 32 escaneos promediados
  **Control mix final:**
    **Criterio aceptacion:** Índice de correlación espectral ≥0,98 vs espectro de referencia del mix final certificado
    **Deteccion adulteraciones:** Cualquier pico adicional no atribuible a los ingredientes declarados con intensidad relativa >5% será investigado como posible adulteración o sustitución
    **Metodo comparacion:** Primer derivada + coeficiente de correlación de Pearson sobre la región 1800-800 cm⁻¹
  **Espectros referencia:**
    **Péptidos de colágeno:**
      **Picos principales:**
        -
          **Numero onda:** 1650
          **Asignacion:** Amida I (C=O estiramiento)
        -
          **Numero onda:** 1550
          **Asignacion:** Amida II (N-H flexión + C-N estiramiento)
        -
          **Numero onda:** 1240
          **Asignacion:** Amida III (C-N estiramiento + N-H flexión)
        -
          **Numero onda:** 3400
          **Asignacion:** OH/NH estiramiento (amplio)
      **Criterio aceptacion:** Concordancia ≥95% en posición de picos Amida I, II y III
    **L-glicina:**
      **Picos principales:**
        -
          **Numero onda:** 3160
          **Asignacion:** NH₃⁺ estiramiento asimétrico
        -
          **Numero onda:** 1610
          **Asignacion:** COO⁻ estiramiento asimétrico
        -
          **Numero onda:** 1410
          **Asignacion:** COO⁻ estiramiento simétrico
        -
          **Numero onda:** 1505
          **Asignacion:** NH₃⁺ flexión
      **Criterio aceptacion:** Concordancia ≥95% en los 4 picos característicos
    **Ácido hialurónico:**
      **Picos principales:**
        -
          **Numero onda:** 3420
          **Asignacion:** OH estiramiento (puente de hidrógeno)
        -
          **Numero onda:** 1630
          **Asignacion:** C=O carboxilato asimétrico
        -
          **Numero onda:** 1410
          **Asignacion:** COO⁻ simétrico
        -
          **Numero onda:** 1150
          **Asignacion:** C-O-C puente glucosídico
      **Criterio aceptacion:** Concordancia ≥95% en posición de picos
    **Astaxantina:**
      **Picos principales:**
        -
          **Numero onda:** 1660
          **Asignacion:** C=O cetona conjugada
        -
          **Numero onda:** 1570
          **Asignacion:** C=C polieno conjugado
        -
          **Numero onda:** 2960
          **Asignacion:** C-H metilo
        -
          **Numero onda:** 960
          **Asignacion:** C-H fuera del plano (trans)
      **Criterio aceptacion:** Concordancia ≥95% en pico C=O y C=C conjugado
    **Akba (boswellia serrata extracto 30%):**
      **Picos principales:**
        -
          **Numero onda:** 1705
          **Asignacion:** C=O ácido carboxílico
        -
          **Numero onda:** 1610
          **Asignacion:** C=C olefínico
        -
          **Numero onda:** 1470
          **Asignacion:** CH₂ flexión
        -
          **Numero onda:** 1240
          **Asignacion:** C-O ácido carboxílico
      **Criterio aceptacion:** Concordancia ≥95% en los 4 picos principales
**Fase 2 granulometria:**
  **Objetivo:** Control del tamaño de partícula para garantizar fluidez, homogeneidad del mix, ausencia de segregación y correcta dosificación del polvo
  **Metodo primario:**
    **Nombre:** Difracción láser
    **Equipo:** ISO 13320 (dispersión en seco, presión 2-3 bar)
    **Metodo alternativo:** Tamizado en seco según ISO 3310-1 (serie de tamices 45-500 μm)
  **Especificaciones por ingrediente:**
    **Péptidos de colágeno:**
      **D10:** 20-50 μm
      **D50:** 80-150 μm
      **D90:** 180-300 μm
      **Observacion:** Ingrediente mayoritario, define la granulometría base del mix
    **L-glicina:**
      **D10:** 15-40 μm
      **D50:** 60-120 μm
      **D90:** 150-250 μm
      **Observacion:** Granulometría fina, compatible con mezcla por orden decreciente
    **Akba (boswellia extracto):**
      **D10:** 5-20 μm
      **D50:** 30-80 μm
      **D90:** 100-180 μm
      **Observacion:** Ingrediente minoritario, verificar dispersión homogénea
  **Especificaciones mix final:**
    **D10:** 15-45 μm
    **D50:** 70-140 μm
    **D90:** 180-280 μm
    **Criterio homogeneidad:** RSD ≤5% en D50 medido en 10 puntos de muestreo aleatorios del lote (ISO 3951)
    **Orden incorporacion:** Incorporación por orden de tamaño decreciente: colágeno primero (mayor D50), seguido de glicina, minerales y finalmente micropartículas (AKBA, vitaminas) con pre-mezcla previa
  **Frecuencia:** CADA_LOTE
**Fase 3 densidad:**
  **Objetivo:** Control de fluidez y compresibilidad del polvo para asegurar comportamiento adecuado en dosificación y envasado
  **Metodos:**
    **Densidad aparente:**
      **Nombre:** Densidad aparente (bulk density)
      **Tecnica:** Ph. Eur. 2.9.15 — cilindro graduado de 100 mL, sin compactación
    **Densidad compactada:**
      **Nombre:** Densidad compactada (tapped density)
      **Tecnica:** Ph. Eur. 2.9.34 — 1250 golpes en aparato de compactación (tap density tester)
  **Especificaciones numericas:**
    **Densidad aparente:**
      **Rango:** 0,40-0,65 g/cm³
      **Justificacion:** Los péptidos de colágeno hidrolizado presentan densidades aparentes en este rango; la glicina tiende a aumentar ligeramente la densidad
    **Densidad compactada:**
      **Rango:** 0,50-0,78 g/cm³
  **Indices reologia:**
    **Indice carr:**
      **Rango especificacion:** <18%
      **Formula:** ((ρcompactada - ρaparente) / ρcompactada) × 100
      **Interpretacion:** <15% excelente fluidez; 15-18% buena fluidez; >20% fluidez deficiente (riesgo de bridges en dosificadora)
    **Indice hausner:**
      **Rango especificacion:** <1,20
      **Formula:** ρcompactada / ρaparente
      **Interpretacion:** <1,25 libre flujo aceptable; <1,20 óptimo para polvos de complementos
  **Frecuencia:** CADA_LOTE
**Fase 4 ph:**
  **Objetivo:** Control del pH del mix en suspensión para garantizar estabilidad química de todos los activos, especialmente vitaminas K2, folato y astaxantina
  **Rango esperado:**
    **Ph esperado:** 4,5-6,5
    **Justificacion:** El colágeno hidrolizado aporta pH ligeramente ácido (4,0-5,5); el ácido hialurónico es ácido (pKa 3-4); los minerales (Mg, Fe, Zn) pueden elevar ligeramente el pH; el AKBA aporta acidez residual
  **Especificacion aceptacion:** pH 4,5-6,5 en suspensión al 5% (p/v) en agua destilada
  **Metodo:**
    **Nombre:** Potenciometría
    **Tecnica:** pH metro calibrado con buffers pH 4,0 y 7,0 (Ph. Eur. 2.2.3); suspensión al 5% p/v, agitación magnética 10 min, medición a 20±2°C; reposo 2 min antes de lectura
    **Preparacion muestra:** 5,0 g de polvo + 95 mL de agua destilada Tipo II (ISO 3696), agitar 10 min
  **Impacto ph fuera rango:**
    **Ph menor 4 0:** Riesgo de hidrólisis acelerada de péptidos de colágeno; posible desnaturalización del ácido hialurónico; inestabilidad del enlace glucosídico
    **Ph mayor 7 0:** Degradación oxidativa de astaxantina (muy sensible a pH alcalino); isomerización de Vitamina K2 (MK-7); degradación del folato (ácido fólico inestable a pH alcalino); oxidación acelerada de AKBA
    **Ph optimo astaxantina:** Estable en rango ácido-neutro (pH 3-7); vida media reducida drásticamente a pH >7
    **Ph optimo vitamina k2:** Máxima estabilidad en medio neutro-ligeramente ácido (pH 5-7); descomposición por hidrólisis a pH alcalino
    **Ph optimo folato:** Estable a pH 4-6; degradación a pH >7 con apertura del anillo pteridina
  **Frecuencia:** CADA_LOTE
**Fase 5 aspecto organoleptico:**
  **Descripcion producto:** Polvo fino y homogéneo de color blanco a blanco-amarillento, con posible leve tonalidad anaranjada por presencia de astaxantina a baja concentración
  **Criterios aceptacion:**
    **Polvo:**
      **Color:** Blanco a blanco-amarillento, con leve tono anaranjado homogéneo aceptable
      **Olor:** Característico suave a colágeno, ligeramente amaderado por Boswellia serrata; sin olores extraños
      **Textura:** Polvo fino, homogéneo, libre-fluente, sin grumos ni aglomerados duros
      **Criterio rechazo:** Presencia de apelmazamiento >10% de la muestra; decoloración visible (pardeamiento, manchas); olor rancio, a humedad o químico extraño; presencia de cuerpos extraños; textura pegajosa o compactada
  **Metodo inspeccion:**
    **Nombre:** Inspección visual y olfatométrica
    **Tecnica:** Personal entrenado bajo iluminación D65 (ISO 3664); muestra sobre superficie blanca nitrurada; comparación con patron de referencia aprobado; evaluación olfativa a 10-15 cm de distancia
  **Frecuencia:** CADA_LOTE
**Fase 6 ensayos analiticos adicionales:**
  **Cuantificacion activos:**
    -
      **Parametro:** Péptidos de Colágeno
      **Justificacion:** Ingrediente principal (5g/dosis); la cuantificación por hidroxiprolina es el método de referencia para proteínas colagénicas
      **Especificacion:** 90-110% del valor declarado (4,50-5,50 g/dosis)
      **Metodo:** Espectrofotometría UV-Vis tras hidrólisis ácida y reacción con cloramina-T / ácido perclórico (basado en Ph. Eur. monografía de colágeno; AOAC 990.26 modificado); λ=560 nm
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** L-Glicina
      **Justificacion:** Ingrediente principal (5g/dosis); la glicina es el aminoácido más abundante en el colágeno y se adiciona libremente, requiere control individual
      **Especificacion:** 90-110% del valor declarado (4,50-5,50 g/dosis)
      **Metodo:** HPLC-UV con derivatización pre-columna OPA/FMOC (Ph. Eur. 2.2.56); detector UV λ=338 nm; columna C18; cuantificación vs estándar de L-glicina
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Ácido Hialurónico
      **Justificacion:** Ingrediente funcional (100 mg/dosis); susceptibilidad a degradación hidrolítica
      **Especificacion:** 90-110% del valor declarado (90-110 mg/dosis)
      **Metodo:** HPLC-SEC con detector de índice de refracción (RI); columna de exclusión por tamaño acuosa (ej: TSKgel G3000PWxl); fase móvil: NaCl 0,1M; cuantificación vs estándar de AH de PM conocido
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** AKBA (ácido 11-ceto-β-boswélico)
      **Justificacion:** Marcador cualitativo y cuantitativo del extracto de Boswellia serrata 30% AKBA; concentración baja (10 mg/dosis), requiere método sensible
      **Especificacion:** ≥90% del valor declarado (≥9,0 mg/dosis de AKBA; equivalente a ≥30 mg/dosis de extracto)
      **Metodo:** HPLC-UV; columna C18 (150×4,6 mm, 3 μm); fase móvil: Acetonitrilo/água con ácido fosfórico 0,1% (gradiente); λ=254 nm; patrón de referencia AKBA certificado
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Astaxantina
      **Justificacion:** Altamente fotosensible y oxidable; concentración muy baja (1 mg/dosis); requiere método específico y protección de la muestra
      **Especificacion:** ≥90% del valor declarado (≥0,90 mg/dosis)
      **Metodo:** HPLC-UV-Vis; columna C30 o C18 especial para carotenoides; fase móvil: metanol/MTBE/água (gradiente); λ=476 nm; extracción previa con hexano:acetona (1:1) bajo luz amber; patrón de astaxantina trans
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Magnesio
      **Justificacion:** Mineral en concentración relevante (75 mg/dosis); control de sobredosificación
      **Especificacion:** 90-110% del valor declarado (67,5-82,5 mg/dosis)
      **Metodo:** ICP-OES (ISO 17053) o AAS de llama (Ph. Eur. 2.2.23); digestión ácida previa con HNO₃/HCl; λ=285,2 nm (AAS) o 279,6 nm (ICP)
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Hierro
      **Justificacion:** Mineral traza (3,5 mg/dosis); control crítico por toxicidad potencial en sobredosis y compatibilidad con colágeno
      **Especificacion:** 90-110% del valor declarado (3,15-3,85 mg/dosis)
      **Metodo:** ICP-OES o AAS de llama; digestión ácida; λ=248,3 nm (AAS) o 238,2 nm (ICP)
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Zinc
      **Justificacion:** Mineral traza (2,5 mg/dosis); posible interacción con absorción de hierro
      **Especificacion:** 90-110% del valor declarado (2,25-2,75 mg/dosis)
      **Metodo:** ICP-OES o AAS de llama; digestión ácida; λ=213,9 nm (AAS) o 206,2 nm (ICP)
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Vitamina K2 (MK-7)
      **Justificacion:** Concentración muy baja (25 μg/dosis); altamente fotosensible y termolábil; requiere método sensible
      **Especificacion:** ≥90% del valor declarado (≥22,5 μg/dosis)
      **Metodo:** HPLC-FLD (fluorescencia) pos-columna con reducción química (Zn) o LC-MS/MS; columna C18; extracción con hexano; λ_ex=248 nm, λ_em=430 nm (post-reducción); patrón MK-7 all-trans certificado
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Vitamina B12 (cianocobalamina)
      **Justificacion:** Concentración traza (0,63 μg/dosis); la deficiencia más crítica en formulaciones multivitamínicas
      **Especificacion:** ≥90% del valor declarado (≥0,57 μg/dosis)
      **Metodo:** HPLC-UV o LC-MS/MS; columna C18; λ=361 nm; extracción con tampón acetato pH 4,0; límite de cuantificación <0,1 μg/dosis
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Vitamina B2 (riboflavina)
      **Justificacion:** Fotosensible; concentración baja (0,35 mg/dosis)
      **Especificacion:** 90-110% del valor declarado (0,315-0,385 mg/dosis)
      **Metodo:** HPLC-FLD; λ_ex=445 nm, λ_em=525 nm; columna C18; tampón fosfato pH 6,0/metanol; protección de muestra de la luz
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Vitamina B6 (piridoxina clorhidrato)
      **Justificacion:** Concentración baja (0,35 mg/dosis)
      **Especificacion:** 90-110% del valor declarado (0,315-0,385 mg/dosis)
      **Metodo:** HPLC-UV; λ=290 nm; columna C18; tampón hexanosulfonato sódico pH 3,0/metanol (isocrático)
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Vitamina B5 (ácido pantoténico)
      **Justificacion:** Concentración baja (1,5 mg/dosis)
      **Especificacion:** 90-110% del valor declarado (1,35-1,65 mg/dosis)
      **Metodo:** HPLC-UV; λ=210 nm; columna C18; tampón fosfato pH 3,0/metanol
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Vitamina B1 (tiamina clorhidrato)
      **Justificacion:** Concentración baja (0,275 mg/dosis); termolábil
      **Especificacion:** 90-110% del valor declarado (0,248-0,303 mg/dosis)
      **Metodo:** HPLC-UV post-columna con oxidación a tioflavina (Ph. Eur.); λ_ex=375 nm, λ_em=435 nm; o HPLC-UV directo λ=254 nm
      **Frecuencia:** CADA_LOTE
    -
      **Parametro:** Folato (ácido fólico)
      **Justificacion:** Concentración traza (50 μg/dosis); inestable a pH alcalino y luz
      **Especificacion:** ≥90% del valor declarado (≥45 μg/dosis)
      **Metodo:** HPLC-UV; λ=280 nm; columna C18; tampón fosfato pH 6,5/metanol; protección de la luz
      **Frecuencia:** CADA_LOTE
  **Uniformidad contenido:**
    **Parametro:** Uniformidad de contenido por dosis
    **Justificacion:** El producto contiene ingredientes en concentraciones muy bajas (Vitamina K2: 25 μg, B12: 0,63 μg, Folato: 50 μg) donde la homogeneidad es crítica
    **Especificacion:** RSD ≤6% en 10 unidades de dosificación individuales para los marcadores críticos (K2, B12, AKBA, astaxantina); valor medio dentro de 90-110%
    **Metodo:** Muestreo de 10 dosis individuales (ej: 10 sobres o porciones de 12,8 g); análisis por HPLC de los marcadores de bajo contenido
    **Frecuencia:** CADA_LOTE
    **Referencia:** Inspired by USP <905> Uniformity of Dosage Units, adaptado a complementos alimentarios con trazas
  **Humedad:**
    **Parametro:** Pérdida por desecación
    **Justificacion:** El colágeno es higroscópico; humedad excesiva favorece reacciones de Maillard (colágeno + azúcares), degradación de vitaminas y apelmazamiento
    **Especificacion:** ≤5,0% (p/p)
    **Metodo:** Ph. Eur. 2.2.32 — Termobalanza a 105°C hasta peso constante, o Ph. Eur. 2.2.35 (Karl Fischer) si se requiere mayor precisión
    **Frecuencia:** CADA_LOTE
  **Metales pesados:**
    **Parametro:** Plomo, Cadmio, Mercurio, Arsénico total
    **Justificacion:** Requisito reglamentario obligatorio (Reglamento UE 2023/915); el colágeno bovino/porcino/marino es una fuente potencial de metales pesados
    **Especificacion:**
      **Plomo:** <3,0 mg/kg (límite Reg. UE 2023/915 para suplementos alimenticios)
      **Cadmio:** <1,0 mg/kg
      **Mercurio:** <0,10 mg/kg
      **Arsenico total:** <1,0 mg/kg
    **Metodo:** ICP-MS (ISO 17294-2) tras digestión microondas con HNO₃/H₂O₂; cuantificación por calibración externa con patrón interno (Ge, In, Bi)
    **Frecuencia:** CADA_LOTE_MATERIA_PRIMA_COLAGENO + CADA_3_LOTES_PRODUCTO_FINAL
  **Microbiologia:**
    **Criterios microbiologicos:**
      -
        **Parametro:** Recuento total de aerobios mesófilos
        **Criterio:** m=1000 UFC/g, M=10000 UFC/g (n=5, c=2)
        **Metodo:** ISO 4833-1:2013 — Siembra en profundidad en PCA, 30°C, 72 h
        **Frecuencia:** CADA_LOTE
      -
        **Parametro:** Levaduras y mohos
        **Criterio:** m=100 UFC/g, M=1000 UFC/g (n=5, c=2)
        **Metodo:** ISO 21527-1:2008 — DG18, 25°C, 5 días
        **Frecuencia:** CADA_LOTE
      -
        **Parametro:** Enterobacteriaceae
        **Criterio:** m=10 UFC/g, M=100 UFC/g (n=5, c=2)
        **Metodo:** ISO 21528-2:2017 — VBGA, 37°C, 24 h
        **Frecuencia:** CADA_LOTE
      -
        **Parametro:** Escherichia coli
        **Criterio:** Ausencia en 1 g
        **Metodo:** ISO 16649-3:2015 — TBX, 44°C, 24 h
        **Frecuencia:** CADA_LOTE
      -
        **Parametro:** Salmonella spp.
        **Criterio:** Ausencia en 25 g
        **Metodo:** ISO 6579-1:2017 — Pre-enriquecimiento en BPW, enriquecimiento selectivo en RVS/TTB, aislamiento en XLD/BSA
        **Frecuencia:** CADA_LOTE
      -
        **Parametro:** Bacillus cereus
        **Criterio:** m=100 UFC/g, M=1000 UFC/g (n=5, c=2)
        **Metodo:** ISO 7932:2004 — MYP, 30°C, 24 h
        **Frecuencia:** CADA_LOTE
        **Justificacion:** Relevante en polvos de proteínas por riesgo de formación de esporas
      -
        **Parametro:** Clostridium perfringens
        **Criterio:** Ausencia en 1 g
        **Metodo:** ISO 7937:2004 — TSC, 37°C, anaerobiosis, 24 h
        **Frecuencia:** CADA_5_LOTES
        **Justificacion:** Relevante si el colágeno es de origen bovino/porcino
    **Referencia normativa:** Reglamento CE 2073/2005 y sus modificaciones; categorías aplicables: 1.24 (suplementos alimenticios) y criterios adicionales según AP de origen
**Fase 7 plan estabilidad:**
  **Zona climatica:** II (25°C/60% HR según clasificación ICH Q1A(R2))
  **Numero lotes:** 3
  **Vida util estimada:**
    **Objetivo meses:** 24
    **Alcanzable:** True
    **Condiciones para alcanzabilidad:** Requiere envase opaco con barrera a humedad (PET/PE con EVOH o aluminio interior); almacenamiento en lugar fresco y seco; posible sobreformulación del 10-15% en vitaminas más lábiles (K2, B12, B1, astaxantina, folato)
  **Formato envase recomendado:** Sobres monodosis termosellados (PET/Al/PE) o bote con desecante integrado y cierre hermético (HDPE con liner de aluminio); barrera WVTR <0,5 g/m²/24h
  **Condiciones estudio:**
    -
      **Tipo:** Larga duración
      **Temperatura:** 25°C ± 2°C
      **Humedad relativa:** 60% ± 5%
      **Duracion:** 24 meses
      **Envase:** Envase comercial final cerrado
    -
      **Tipo:** Acelerado
      **Temperatura:** 40°C ± 2°C
      **Humedad relativa:** 75% ± 5%
      **Duracion:** 6 meses
      **Envase:** Envase comercial final cerrado
    -
      **Tipo:** Fotodegradación
      **Temperatura:** 25°C
      **Humedad relativa:** Ambiente
      **Duracion:** 1,2 millones de lux·horas luz visible + 200 W·h/m² luz UV
      **Envase:** Producto expuesto (sin envase) y en envase final para evaluar protección
      **Justificacion:** OBLIGATORIO: la astaxantina, vitamina K2 (MK-7), vitamina B2 (riboflavina) y AKBA son fotosensibles. ICH Q1B requiere estudio de fotodegradación para confirming la necesidad de protección lumínica del envase
  **Cronograma estudio:**
    **Puntos tiempo:**
      -
        **Tiempo:** T=0
        **Condicion:** Todas las condiciones
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH (suspensión 5%)
          - Pérdida por desecación
          - Péptidos de colágeno (hidroxiprolina)
          - L-Glicina (HPLC)
          - AKBA (HPLC-UV)
          - Astaxantina (HPLC-UV-Vis)
          - Vitamina K2 MK-7 (HPLC-FLD)
          - Vitamina B12 (HPLC-UV)
          - Folato (HPLC-UV)
          - Vitamina B1 (HPLC-UV)
          - Vitamina B2 (HPLC-FLD)
          - Magnesio, Hierro, Zinc (ICP-OES)
          - Recuento total aerobios mesófilos
          - Levaduras/mohos
          - Salmonella spp.
          - E. coli
      -
        **Tiempo:** T=1m
        **Condicion:** Acelerado
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH
          - Pérdida por desecación
          - Astaxantina
          - Vitamina K2
          - AKBA
          - Vitamina B12
          - Folato
      -
        **Tiempo:** T=2m
        **Condicion:** Acelerado
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH
          - Pérdida por desecación
          - Astaxantina
          - Vitamina K2
          - AKBA
          - Vitamina B12
          - Folato
      -
        **Tiempo:** T=3m
        **Condicion:** Larga duración + Acelerado
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH
          - Pérdida por desecación
          - Colágeno
          - Glicina
          - AKBA
          - Astaxantina
          - Vitamina K2
          - Vitamina B12
          - Folato
          - Vitamina B1
          - Vitamina B2
          - Mg, Fe, Zn
      -
        **Tiempo:** T=6m
        **Condicion:** Larga duración + Acelerado
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH
          - Pérdida por desecación
          - Colágeno
          - Glicina
          - Ácido Hialurónico
          - AKBA
          - Astaxantina
          - Vitamina K2
          - Vitamina B12
          - Folato
          - Vitamina B1
          - Vitamina B2
          - Vitamina B5
          - Vitamina B6
          - Mg, Fe, Zn
          - Microbiología completa
      -
        **Tiempo:** T=9m
        **Condicion:** Larga duración
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH
          - Pérdida por desecación
          - Colágeno
          - Glicina
          - AKBA
          - Astaxantina
          - Vitamina K2
          - Vitamina B12
          - Folato
          - Mg, Fe, Zn
      -
        **Tiempo:** T=12m
        **Condicion:** Larga duración
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH
          - Pérdida por desecación
          - Colágeno
          - Glicina
          - Ácido Hialurónico
          - AKBA
          - Astaxantina
          - Vitamina K2
          - Vitamina B12
          - Folato
          - Vitamina B1
          - Vitamina B2
          - Vitamina B5
          - Vitamina B6
          - Mg, Fe, Zn
          - Microbiología completa
      -
        **Tiempo:** T=18m
        **Condicion:** Larga duración
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH
          - Pérdida por desecación
          - Colágeno
          - Glicina
          - AKBA
          - Astaxantina
          - Vitamina K2
          - Vitamina B12
          - Folato
          - Mg, Fe, Zn
      -
        **Tiempo:** T=24m
        **Condicion:** Larga duración
        **Parametros monitorizados:**
          - Aspecto, color, olor
          - pH
          - Pérdida por desecación
          - Colágeno
          - Glicina
          - Ácido Hialurónico
          - AKBA
          - Astaxantina
          - Vitamina K2
          - Vitamina B12
          - Folato
          - Vitamina B1
          - Vitamina B2
          - Vitamina B5
          - Vitamina B6
          - Mg, Fe, Zn
          - Microbiología completa
      -
        **Tiempo:** Fin estudio fotodegradación
        **Condicion:** Fotodegradación ICH Q1B
        **Parametros monitorizados:**
          - Aspecto, color
          - Astaxantina
          - Vitamina K2
          - Vitamina B2
          - AKBA
          - Colágeno
  **Criterios fin vida util:**
    -
      **Criterio:** Contenido de activos - Vitaminas y trazas
      **Descripcion:** Descenso por debajo del 90% del valor declarado en etiqueta para: Vitamina K2, B12, folato, B1, B2, B5, B6, astaxantina, AKBA
    -
      **Criterio:** Contenido de activos - Principales
      **Descripcion:** Descenso por debajo del 90% del valor declarado para péptidos de colágeno, L-glicina, ácido hialurónico
    -
      **Criterio:** Contenido de minerales
      **Descripcion:** Descenso por debajo del 90% del valor declarado para Mg, Fe, Zn (inusual pero posible por migración o interacción con envase)
    -
      **Criterio:** Cambio organoléptico
      **Descripcion:** Decoloración significativa (pardeamiento por reacción de Maillard), olor rancio, apelmazamiento que impida dosificación correcta
    -
      **Criterio:** pH fuera de especificación
      **Descripcion:** pH fuera del rango 4,5-6,5, indicando degradación ácido-base de componentes
    -
      **Criterio:** Humedad excesiva
      **Descripcion:** Pérdida por desecación >7,0% (indicador de fallo de barrera del envase o problemas de almacenamiento)
    -
      **Criterio:** Contaminación microbiológica
      **Descripcion:** Cualquier resultado fuera de especificación según CE 2073/2005 en los puntos de control microbiológico
    -
      **Criterio:** Cambio significativo en condición acelerada
      **Descripcion:** Si a T=6m en condición acelerada (40°C/75% HR) se observa cambio significativo (>5% degradación de cualquier activo), la vida útil debe ser reducida y justificada con datos de larga duración
  **Ingredientes criticos estabilidad:**
    -
      **Ingrediente:** Astaxantina
      **Riesgo:** ALTO - Fotosensibilidad extrema y oxidación; degradación acelerada por calor, luz y oxígeno
      **Mitigacion:** Envase opaco, atmósfera protectora (N₂), antioxidante en formulación si es posible, sobreformulación 15-20%
    -
      **Ingrediente:** Vitamina K2 (MK-7)
      **Riesgo:** ALTO - Fotosensible, termolábil, sensible a pH alcalino y oxidación
      **Mitigacion:** Envase opaco, sobreformulación 15%, matriz de colágeno puede ejercer efecto protector por encapsulación física
    -
      **Ingrediente:** Vitamina B12
      **Riesgo:** MEDIO-ALTO - Fotosensible, termolábil a pH alcalino; degradación a cobinamida y análogos inactivos
      **Mitigacion:** Control estricto de pH, sobreformulación 10-15%
    -
      **Ingrediente:** Folato (ácido fólico)
      **Riesgo:** MEDIO - Inestable a pH alcalino y luz UV; degradación por apertura del anillo pteridina
      **Mitigacion:** Mantener pH <6,5, sobreformulación 10%, protección lumínica
    -
      **Ingrediente:** Vitamina B1 (tiamina)
      **Riesgo:** MEDIO - Termolábil; degradación por reacción de Maillard con azúcares reductores; pH óptimo 3-4
      **Mitigacion:** Evitar azúcares reductores en formulación, sobreformulación 10%
    -
      **Ingrediente:** AKBA
      **Riesgo:** MEDIO - Oxidación del grupo 11-ceto; termolabilidad moderada
      **Mitigacion:** Protección de oxígeno, sobreformulación 10%
    -
      **Ingrediente:** Ácido Hialurónico
      **Riesgo:** BAJO-MEDIO - Hidrólisis del enlace glucosídico por humedad y temperatura
      **Mitigacion:** Control de humedad <5%, envase con barrera a humedad
**Fase 8 resumen ejecutivo:** El plan de control de calidad para Collagen Complex Pro se centra en tres ejes críticos: (1) Homogeneidad del mix, dada la enorme disparidad de concentraciones entre ingredientes (desde 5 g de colágeno hasta 0,63 μg de vitamina B12), lo que hace obligatorio el ensayo de uniformidad de contenido por dosis con RSD ≤6% en los marcadores de bajo contenido (K2, B12, folato, AKBA, astaxantina), requiriendo pre-mezcla certificada de los micronutrientes antes de su incorporación al colágeno; (2) Protección de la estabilidad de los activos fotosensibles y termolábiles, siendo la astaxantina y la vitamina K2 los ingredientes de mayor riesgo, lo que impone envase opaco con barrera a humedad y oxígeno (PET/Al/PE o HDPE con liner), control estricto de pH en rango 4,5-6,5 para evitar degradación alcalina del folato y la K2, y estudio de fotodegradación ICH Q1B obligatorio; (3) Control microbiológico riguroso, especialmente por la naturaleza proteica del colágeno (riesgo de B. cereus por esporulación) y el origen animal potencial (C. perfringens en T=0 cada 5 lotes). La frecuencia de muestreo recomendada por lote incluye: controles físicos (FTIR, granulometría, densidad, aspecto, pH, humedad) en 100% de lotes; cuantificación completa de todos los activos por HPLC/ICP en 100% de lotes dado el perfil multicomponente; microbiología completa en 100% de lotes; y metales pesados en 100% de lotes de materia prima de colágeno y cada 3 lotes de producto final. Puntos de atención especial para producción: realizar la mezcla por orden de tamaño de partícula decreciente, verificar que el Índice de Carr sea <18% antes del envasado, proteger las zonas de mezcla y envasado de luz UV directa, y considerar sobreformulación del 10-20% en astaxantina, K2, B12, B1 y folato para compensar la degradación esperada durante la vida útil de 24 meses.
**Metadata:**
  **Version:** 2.0
  **Disclaimer:** Este plan QC es orientativo. Los métodos y criterios deben validarse internamente antes de su implementación. Las sobreformulaciones sugeridas deben verificarse con datos de estabilidad reales. La clasificación del producto como complemento alimentario debe confirmarse con la legislación nacional aplicable.

---
## Fuentes consultadas

[1] **ICH Q1A(R2) - Stability Testing of New Drug Substances and Products** _normativa_
[2] **ICH Q1B - Photostability Testing of New Drug Substances and Products** _normativa_
[3] **ICH Q2(R1) - Validation of Analytical Procedures** _normativa_
[4] **Farmacopea Europea (Ph. Eur.) - Monografías de Colágeno, Tiamina, Riboflavina, Piridoxina, Cianocobalamina, Ácido Fólico; Capítulos 2.2.32, 2.2.35, 2.9.15, 2.9.34, 2.2.3, 2.2.23, 2.2.56** _normativa_
[5] **Reglamento (CE) 2073/2005 relativo a los criterios microbiológicos aplicables a los productos alimenticios (modificaciones posteriores incluidas)** _normativa_
[6] **Reglamento (UE) 2023/915 sobre contenidos máximos de ciertos contaminantes en los alimentos (metales pesados)** _normativa_
[7] **ISO 13320 - Análisis granulométrico por difracción láser** _normativa_
[8] **ISO 3310-1 - Tamices de ensayo - Requisitos técnicos y verificación** _normativa_
[9] **AOAC 990.26 - Hydroxyproline in Collagen (modificado para péptidos de colágeno)** _normativa_
[10] **ISO 17053 - Determinación de elementos traza por ICP-OES** _normativa_
[11] **USP <905> Uniformity of Dosage Units (referencia metodológica adaptada)** _normativa_
[12] **Conocimiento experto en espectroscopía FTIR de péptidos, aminoácidos, carotenoides y triterpenos** _conocimiento_experto_
[13] **Conocimiento experto en estabilidad de vitaminas liposolubles (K2, astaxantina) y vitaminas del grupo B en matrices de polvo** _conocimiento_experto_