# Agente 7: Docs Internos v2

**Fase 1 lista materiales navision:**
  -
    **Orden incorporacion:** 1
    **Denominacion navision:** Maltodextrina aglomerada
    **Codigo referencia:** PENDIENTE_PROVEEDOR
    **Cantidad por unidad mg:** 421
    **Cantidad lote con merma g:** 4294.2
    **Estado material:** HOMOLOGADO
  -
    **Orden incorporacion:** 2
    **Denominacion navision:** Bisglicinato de magnesio
    **Codigo referencia:** PENDIENTE_PROVEEDOR
    **Cantidad por unidad mg:** 1429
    **Cantidad lote con merma g:** 14575.8
    **Estado material:** HOMOLOGADO
  -
    **Orden incorporacion:** 3
    **Denominacion navision:** Ácido ascórbico
    **Codigo referencia:** PENDIENTE_PROVEEDOR
    **Cantidad por unidad mg:** 80
    **Cantidad lote con merma g:** 816
    **Estado material:** HOMOLOGADO
  -
    **Orden incorporacion:** 4
    **Denominacion navision:** Gluconato de zinc
    **Codigo referencia:** PENDIENTE_PROVEEDOR
    **Cantidad por unidad mg:** 70
    **Cantidad lote con merma g:** 714
    **Estado material:** HOMOLOGADO
**Fase 2 formula cuantitativa:**
  **Total capsula mg:** 2000
  **Subtotales:**
    **Activos mg:** 1579
    **Excipientes mg:** 421
    **Total mg:** 2000
  **Composicion:**
    **Bisglicinato de magnesio:**
      **Cantidad mg:** 1429
      **Porcentaje:** 71.45%
    **Maltodextrina aglomerada:**
      **Cantidad mg:** 421
      **Porcentaje:** 21.05%
    **Ácido ascórbico:**
      **Cantidad mg:** 80
      **Porcentaje:** 4.00%
    **Gluconato de zinc:**
      **Cantidad mg:** 70
      **Porcentaje:** 3.50%
**Fase 2b proceso fabricacion:**
  **Pasos:**
    -
      **Paso:** 1
      **Operacion:** Pesada de materiales
      **Descripcion:** Pesar cada componente en balanza calibrada siguiendo orden decreciente de cantidad (maltodextrina, bisglicinato de magnesio, ácido ascórbico, gluconato de zinc). Verificar identidad y pureza por etiqueta/certificado de análisis. Registrar lotes de materia prima.
      **Punto critico:** True
      **Condiciones:**
        **Tiempo:** Según rendimiento
        **Temperatura:** <25°C
        **Humedad relativa:** <45%
    -
      **Paso:** 2
      **Operacion:** Tamizado individual
      **Descripcion:** Tamizar cada material por separado mediante malla 40-60 para eliminar grumos, aglomerados y homogeneizar tamaño de partícula antes de la mezcla.
      **Punto critico:** False
      **Condiciones:**
        **Tiempo:** Continuo
        **Temperatura:** Ambiente
        **Humedad relativa:** <45%
    -
      **Paso:** 3
      **Operacion:** Premix de activos minoritarios
      **Descripcion:** En contenedor auxiliar, mezclar el ácido ascórbico y el gluconato de zinc con aproximadamente el 10% de la maltodextrina total (geometric dilution) para garantizar la distribución uniforme de las trazas antes de incorporar al bulk.
      **Punto critico:** True
      **Condiciones:**
        **Tiempo:** 5 min
        **Temperatura:** <25°C
        **Humedad relativa:** <40%
    -
      **Paso:** 4
      **Operacion:** Mezcla principal en V-blender
      **Descripcion:** Cargar en mezcladora de doble cono o V-blender la maltodextrina restante, el bisglicinato de magnesio y el premix de activos minoritarios. Mezclar hasta obtener distribución homogénea. El bisglicinato de magnesio actúa como matriz de mayor densidad; la maltodextrina como diluyente ligero.
      **Punto critico:** True
      **Condiciones:**
        **Tiempo:** 15-20 min
        **Velocidad:** Media (según equipo)
        **Temperatura:** <25°C
        **Humedad relativa:** <45%
    -
      **Paso:** 5
      **Operacion:** Comprobación de homogeneidad
      **Descripcion:** Extraer muestras representativas en 3 puntos (superior, medio e inferior) del tambor. Analizar contenido de zinc como marcador de traza (dosis minoritaria). Coefficient of Variation (CV) objetivo <5%. Si falla, extender mezcla 5 min adicionales y reanalizar.
      **Punto critico:** True
      **Condiciones:**
        **Tiempo:** Según laboratorio
        **Temperatura:** Ambiente controlado
    -
      **Paso:** 6
      **Operacion:** Envasado en stick aluminio monodosis
      **Descripcion:** Dosificar el polvo en stick de aluminio termosellable mediante sistema de sinfín o báscula de pérdida de peso. Peso dosis objetivo 2000 mg. Realizar sellado longitudinal y transversal por calor controlado. Incluir opcionalmente sobrecito desecante en bobinado previo.
      **Punto critico:** False
      **Condiciones:**
        **Tiempo:** Continuo
        **Temperatura:** <25°C
        **Humedad relativa:** <45%
    -
      **Paso:** 7
      **Operacion:** Control en proceso y peso de dosis
      **Descripcion:** Verificar peso neto de stick cada 15 min (n=10), integridad de sellado por presión manual, apariencia del polvo (blanco a crema, sin decoloración) y hermeticidad por inmersión. Rechazar lotes de envasado con desviación >±5% en peso.
      **Punto critico:** True
      **Condiciones:**
        **Tiempo:** Cada 15 min
        **Temperatura:** Ambiente
        **Humedad relativa:** <45%
**Fase 3 mapa reactividad:**
  -
    **Formato:** Stick de aluminio monodosis
    **Caducidad estimada:** 36 meses (óptima); 18 meses (subóptima >30°C o HR>60%)
    **Riesgo global:** MEDIO
    **Parametros:**
      -
        **Parametro:** Humedad (>40% HR)
        **Nivel riesgo:** BAJO
        **Ingredientes afectados:**
          - Ácido ascórbico
          - Gluconato de zinc
        **Medida preventiva:** Barrera de aluminio termosellado; HR de proceso <45%; desecante opcional en bobinado
      -
        **Parametro:** Luz UV
        **Nivel riesgo:** BAJO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Opacidad total del laminado de aluminio; almacenaje en ausencia de luz
      -
        **Parametro:** Temperatura (>25°C)
        **Nivel riesgo:** MEDIO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Almacenaje y transporte refrigerado o entre 15-25°C; evitar picos térmicos
      -
        **Parametro:** Oxígeno
        **Nivel riesgo:** MEDIO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Sellado hermético; posible enriquecimiento con N2 durante mezcla/llenado
      -
        **Parametro:** pH del medio
        **Nivel riesgo:** BAJO
        **Ingredientes afectados:**         _(vacío)_
        **Medida preventiva:** No aplica en formulación sólida seca
  -
    **Formato:** Cápsula vegetal (HPMC) en blister
    **Caducidad estimada:** 24 meses (óptima); 12 meses (subóptima)
    **Riesgo global:** MEDIO
    **Parametros:**
      -
        **Parametro:** Humedad (>40% HR)
        **Nivel riesgo:** MEDIO
        **Ingredientes afectados:**
          - Ácido ascórbico
          - Gluconato de zinc
        **Medida preventiva:** Blister aluminio/PVC con desecante en envase secundario; HR almacén <60%
      -
        **Parametro:** Luz UV
        **Nivel riesgo:** BAJO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Blister opaco o cartucho de cartón
      -
        **Parametro:** Temperatura (>25°C)
        **Nivel riesgo:** MEDIO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Cadena de frío 15-25°C
      -
        **Parametro:** Oxígeno
        **Nivel riesgo:** MEDIO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Blister con barrera de aluminio
      -
        **Parametro:** pH del medio
        **Nivel riesgo:** BAJO
        **Ingredientes afectados:**         _(vacío)_
        **Medida preventiva:** No aplica
  -
    **Formato:** Bote polvo HDPE con doble tapón
    **Caducidad estimada:** 18 meses (óptima); 9 meses (subóptima)
    **Riesgo global:** ALTO
    **Parametros:**
      -
        **Parametro:** Humedad (>40% HR)
        **Nivel riesgo:** ALTO
        **Ingredientes afectados:**
          - Ácido ascórbico
          - Gluconato de zinc
          - Bisglicinato de magnesio
        **Medida preventiva:** Bote con rosca hermética, sello de inducción y dos desecantes; instrucciones de cierre inmediato
      -
        **Parametro:** Luz UV
        **Nivel riesgo:** MEDIO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Envase opaco o ámbar; almacenaje en oscuridad
      -
        **Parametro:** Temperatura (>25°C)
        **Nivel riesgo:** MEDIO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Almacén refrigerado
      -
        **Parametro:** Oxígeno
        **Nivel riesgo:** MEDIO
        **Ingredientes afectados:**
          - Ácido ascórbico
        **Medida preventiva:** Atmósfera modificada con N2 al envasar; cierre hermético
      -
        **Parametro:** pH del medio
        **Nivel riesgo:** BAJO
        **Ingredientes afectados:**         _(vacío)_
        **Medida preventiva:** No aplica
**Fase 4 alertas navision:** _(vacío)_
**Metadata:**
  **Version:** 2.0
  **Disclaimer:** Este documento es un borrador técnico. Las referencias NAVISION deben verificarse con el equipo de compras de Umbrella Group.
** trazabilidad:**
  **Prompt version:** 2.0.0
  **Model:** moonshotai/kimi-k2.6
  **Base url:** https://openrouter.ai/api/v1
  **Timestamp utc:** 2026-05-12T14:53:05+00:00
  **Duration s:** 264.82
  **Attempts:** 1
  **Transient retries:** 0
  **Deterministic retries:** 0