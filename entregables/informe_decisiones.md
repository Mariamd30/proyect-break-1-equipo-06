# Informe de decisiones — Project Break 1: RAG Engineering

## 1. Tema y corpus
- Tema: Deporte municipal
- Fuentes:
  - **CSV/XLSX** (datos.madrid.es):
    - Polideportivos — `200186-0-polideportivos-csv.csv` (82 registros)
    - Instalaciones deportivas básicas — `200215-0-instalaciones-deportivas-csv.csv` (607 registros)
    - Piscinas públicas — `210227-0-piscinas-publicas-csv.csv` (56 registros; solapa en gran parte con polideportivos, mismo esquema de fichas de centro)
    - Tarifas de instalaciones deportivas — `300083-10-deportes-tarifas.xlsx` (205 registros, precio + descuentos por servicio)
    - Descuentos en instalaciones — `300097-3-deportes-descuentos-csv.csv` (110.746 registros de uso; agregado a 8 documentos-resumen por grupo de descuento en vez de convertirse fila a fila)
  - **PDF** (madrid.es / sede.madrid.es):
    - Precios Públicos 2026 — `PreciosPublicos2026.pdf`
    - Tarifas de servicios en centros deportivos — `Tarifas_deportivas.pdf`
    - Reglamento sobre la Utilización de las Instalaciones y Servicios Deportivos Municipales (2012) — `eli-es-md-01860896-reg-2012-10-15-(1)-dof-spa.pdf` (25 páginas)
    - Infografía "Cómo adquirir o renovar un Abono Deporte Madrid" — `20250912_InfografíaCómoAdquirirOrenovarUnADM.pdf`
- Formatos: CSV/XLSX + PDF

## 2. Experimento de chunking
- CHUNK_SIZE / CHUNK_OVERLAP probados:
- Observaciones:

## 3. Retrieval — observación con 2 valores de K
Query de prueba: "¿Cuánto cuesta el abono de piscina?"

- **K=3**: los 3 resultados son variantes del mismo servicio (ENTRADA PISCINA
  DE VERANO, distintas categorías de edad), scores muy juntos (0.71-0.73).
  Redundante: no aporta información más allá del primer resultado.
- **K=5**: añade 1 resultado nuevo (ENTRADA PISCINA CUBIERTA), con una caída
  de score notable (0.58 vs 0.69 del anterior) — servicio distinto pero
  claramente menos relevante para la query literal.
- **Observación general**: aumentar K no diversifica demasiado en corpus con
  muchas filas casi idénticas (misma tarifa por categoría de edad) que
  compiten por los primeros puestos — el cuello de botella no es K, es la
  redundancia estructural del CSV/XLSX de tarifas.

## 4. Generación
- 1 acierto in-corpus:
- 1 abstención fuera de corpus:

## 5. Fallos conocidos (3) y próximos pasos

1. **Límite diario de cuota gratuita de Gemini Embeddings.** Al generar
   embeddings del corpus completo (1712 chunks) con `gemini-embedding-001`,
   el proceso se cortaba repetidamente con errores 429. Diagnosticamos en
   el panel de uso de Google AI Studio que el bloqueante real era el límite
   **RPD (Requests Per Day) = 1000/día** del free tier —cada texto cuenta
   como una petición, así que con 1712 chunks era matemáticamente imposible
   completarlo en un solo día—. Solución: migramos a embeddings locales
   con `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`,
   384D), que no dependen de red ni cuota. Resultado: los mismos 1712
   chunks pasaron de no poder completarse en un día a procesarse en **63
   segundos** en local. Trade-off: 384 dimensiones frente a las 3072 de
   Gemini (posible pérdida de matiz semántico, no cuantificada). La
   generación de respuestas sigue usando Gemini; solo cambió la fase de
   embeddings. Más detalle en el apéndice.
2. **El retriever no encuentra el "Abono Deporte Madrid" al preguntar por
   el precio del abono de piscina.** Con la query "¿Cuánto cuesta el abono
   de piscina?", el chunk más relevante real (`CUOTA MENSUAL ABONO DEPORTE
   MADRID USO LIBRE`) aparece en el puesto **728 de 1712** (score 0.199) —
   muy lejos de cualquier K razonable. Con K=3, K=5 o incluso K=20 solo se
   recuperan variantes de "ENTRADA PISCINA DE VERANO/CUBIERTA" (entradas
   sueltas, no abonos), con scores entre 0.5 y 0.73. Causa: el texto del
   "Abono" no contiene la palabra "piscina" (es un abono general a
   instalaciones deportivas), mientras el modelo de embeddings da mucho
   peso al término literal "piscina", presente en cientos de chunks de
   menor relevancia real. Próximo paso: enriquecer el texto/metadata de
   los servicios "Abono" con sinónimos o categorías relacionadas (p. ej.
   "incluye acceso a piscina") para mejorar el matching semántico.
3.

## Próximos pasos
-
-

---

## Apéndice: detalle técnico del cambio de embeddings (Gemini → Hugging Face local)

### El problema: límite diario del free tier de Gemini

Al generar los embeddings del corpus completo (1712 chunks) con
`gemini-embedding-001`, el proceso se cortaba repetidamente con errores
`429 RESOURCE_EXHAUSTED`. Tras revisar el panel de uso de Google AI Studio,
identificamos que el cuello de botella real era el límite **RPD (Requests
Per Day) = 1000 peticiones/día** del nivel gratuito — no el límite por
minuto, que fue lo primero que ajustamos sin éxito.

Cada texto embeddeado cuenta como una petición hacia ese contador diario,
independientemente del tamaño del lote en que se envíe. Con 1712 chunks,
necesitábamos casi el doble de lo que el free tier permite completar en un
único día: habría hecho falta repartir la ingesta en al menos 2 días, o
activar facturación de pago en Google Cloud.

### Por qué era lento y fallaba

Con Gemini, cada lote de texto viaja por red hasta los servidores de
Google, se procesa allí, y vuelve — pero el problema no era solo la
latencia de red: al superar la cuota, la API **rechaza directamente la
petición** (error 429) y obliga a esperar (en nuestras pruebas, ~60
segundos entre lotes) antes de poder reintentar. No es un problema de
optimización de nuestro código: es un techo impuesto por el proveedor.

### La solución: embeddings locales

Cambiamos a **`sentence-transformers`** con el modelo
`paraphrase-multilingual-MiniLM-L12-v2` (multilingüe, funciona bien en
español, 384 dimensiones), que se ejecuta **en la máquina local** sin
llamadas a ninguna API externa. El modelo se descarga una única vez
(~470 MB) y después no requiere red ni cuota de ningún tipo.

**Resultado medido:** los mismos 1712 chunks que antes no lograban
completarse ni en varias horas, con HF local se procesaron en **63
segundos** (54 lotes de ~32 textos, a 1.18s/lote de media).

### Trade-off asumido

El modelo local usa **384 dimensiones** frente a las **3072** de
`gemini-embedding-001` — en teoría, un espacio vectorial más rico puede
capturar matices semánticos más finos. Priorizamos la viabilidad práctica
del proyecto (poder completar la ingesta en minutos y de forma reproducible
para todo el equipo) frente a una posible mejora marginal de calidad de
embedding, dado el tamaño de nuestro corpus.

### Impacto en el resto del pipeline

- La **generación** de la respuesta final sigue usando Gemini
  (`GENERATION_MODEL`) — este cambio afecta solo a la fase de embeddings.
- El retriever debe embeddear las preguntas del usuario con el **mismo
  modelo local**, no con Gemini, para que los vectores sean comparables.