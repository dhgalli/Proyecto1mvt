# JUSTICOMBAT v8 — Auditoría y plan de mejoras

Fecha: 9 de octubre de 2026. Base analizada: `Justicombat-v8-continuar.zip` (fuentes en `proyecto/dist/`, release HTML, referencias y pruebas).

> **Nota sobre este repositorio:** `dhgalli/Proyecto1mvt` es **público**. El proyecto del juego incluye las fotos originales de los amigos, y los criterios de trabajo exigen acordar destino antes de publicarlas. Por eso acá solo se versiona esta auditoría (texto). El código del juego se trabaja aparte hasta que el repo sea privado o exista uno privado nuevo.

## Qué se verificó y qué se infiere

**Verificado en este entorno:** lectura completa de las fuentes (`engine.js`, `game.js`, `backdrop.js`, `presentation.js`, `finishers.js`, `tournament.js`, `index.html`), ejecución de `npm test` con Node 22 (las 8 suites pasan), ejecución del juego servido con `tools/serve.cjs` en Chromium headless con capturas propias a 844×390 y 390×844 (selección y pelea, incluida la escena de agarre), y revisión de los atlas (`fighter-atlas.png`, `signature-sprites.png`) y las láminas QA.

**Inferido (no medido):** el costo real de fps en un teléfono físico. El headless corre con render por software y no es representativo. Lo que sí es un hecho de código: hay `ctx.filter` y `shadowBlur` ejecutándose por cuadro sobre superficies grandes, un patrón conocidamente caro en móvil (detalle abajo). El equilibrio de combate tampoco tiene sesiones humanas; lo que se afirma sale de leer el motor y de simulaciones.

---

## A. Diagnóstico: las cinco limitaciones más importantes

**1. La sensación de recorte viene de tres fuentes concretas, no de una.**
(a) **Luz incompatible**: las caras son fotos de exterior con luz cálida real; los cuerpos del atlas tienen sombreado pintado de estudio. El tratamiento actual (`saturate(.88) contrast(1.03)` en la cara, `saturate(.82) contrast(1.06)` en el cuerpo, `game.js:144,171`) acerca saturaciones pero no unifica la dirección ni la temperatura de la luz. (b) **Borde duro**: el contorno de la cara (`faceContours`, `game.js:22-26`) corta a píxel seco; la unión con el cuello es un tope con una elipse de sombra de 3.5 px (`game.js:170`). (c) **Defectos del atlas**: las filas 2–4 de `fighter-atlas.png` tienen halos rojos de generación en los bordes, visibles en pantalla clara. Además, tres de los cuatro cuerpos son la misma plantilla musculosa con distinta ropa: el cuerpo no aporta identidad (el saco de Park sí).

**2. Hay cuatro poses de cuerpo y ninguna de las tres que más se leen.**
No existe pose de **golpe recibido** (la reacción es inclinación y squash de la guardia, `game.js:120-131`), ni de **salto** (squash de la guardia), ni de **festejo** (se reusa guardia/puño con el objeto). En un juego de pelea, la pose de daño es la señal número uno de quién ganó el intercambio; hoy eso se lee solo por partículas y barras. Las transiciones entre columnas (guardia→puño) saltan sin cuadro intermedio; la anticipación por transformaciones (`fighterPose`) ayuda pero el cambio de silueta sigue siendo un "pop".

**3. Escala y cámara: los personajes son chicos y la cámara no mira la pelea.**
En 844×390 las caras quedan en ~55–60 px y el estadio ocupa la mayoría del cuadro (verificado en captura propia). La cámara actual solo panea y hace zoom ambiental del fondo (`backdrop.js:10-24`); los luchadores se dibujan a escala fija `.61` (`game.js:157`). El propio historial fija el criterio correcto («la cara ocupe al menos 65 px mientras pelea») y hoy no se cumple en horizontal.

**4. Riesgo real de rendimiento: filtros y sombras por cuadro.**
Cada frame: el estadio completo se dibuja con `ctx.filter='saturate(.72) contrast(1.08)'` (`backdrop.js:24`), un rectángulo fullscreen en `soft-light` (`backdrop.js:44`), filas de público con `filter='grayscale(1)'` (`backdrop.js:56`), y cada cabeza con `ctx.filter` + `shadowBlur=1.8` (`game.js:171`). En muchos navegadores móviles eso rasteriza en CPU y es el candidato principal a romper los 60 fps. Todo es horneable una sola vez sin cambiar el aspecto (el patrón ya existe: `treatedSheet` y `faceCache`).

**5. El combate es correcto pero plano: no hay encadenado real ni castigo a la tortuga, y el K.O. termina seco.**
Con stun de puño 0,17 s y impacto de patada a 0,23 s (`engine.js:3`), ningún paso de las recetas conecta garantizado: los "combos" son golpes sueltos en una ventana de 2,3 s. El bloqueo reduce a 12 % sin costo ni desgaste (`engine.js:99-103`); solo Vict tiene respuesta directa (abrazo); los demás dependen de cruzar con técnica. Y el momento más importante del partido —el golpe final— no tiene tratamiento: ni cámara lenta, ni repetición, ni placa. El hitstop y la reacción visual existen (bien resuelto en v5) pero están calibrados tímidos.

---

## B. Doce mejoras concretas

### Eje 1 · Gráficos y animación

**1. Hornear luz y color (mismo aspecto, mucho más rápido).**
Pre-renderizar una vez por arena el estadio ya graduado (filtro + veladuras + soft-light) a un canvas oculto, y hornear el tratamiento de caras y atlas dentro de los cachés existentes, eliminando `ctx.filter`/`shadowBlur` del camino caliente.
Beneficio: probablemente la mayor ganancia de fps disponible; habilita todo lo demás. Esfuerzo: **bajo**. Riesgo: **bajo**. Archivos: `backdrop.js`, `game.js`. Verificación: lámina antes/después idéntica + contador de fps de desarrollo (`?debug=1`) en un teléfono real.

**2. Integración cara–cuerpo y limpieza del atlas (muestra primero).**
Quitar los halos rojos del atlas; plumar el borde del contorno de cara (1–2 px) con sombra de mentón proyectada sobre el cuello; aplicar una tinta ambiental por estadio **a cuerpo y cara juntos** para que compartan luz. Muestra: **Matt en La Bombonera**, lado a lado con la versión actual, antes de tocar a los cuatro.
Beneficio: ataca la causa directa del "recorte" conservando las fotos. Esfuerzo: **medio**. Riesgo: **medio** (el parecido manda; se aprueba con capturas). Archivos: `assets/fighter-atlas.png`, `game.js` (`face`, `drawFighter`), herramienta nueva en `tools/`. Verificación: capturas 390×844 y 844×390, aprobación del parecido.

**3. Tres poses nuevas: golpe recibido, salto y festejo.**
Generadas con el mismo pipeline de `SPRITES-PROMPT.txt`/`SIGNATURES-PROMPT.txt`, con anclajes y baseline registrados como los actuales.
Beneficio: la pose de daño es la mejora de lectura más grande posible; salto y festejo completan entradas, aire y final. Esfuerzo: **medio-alto**. Riesgo: **medio** (coherencia de estilo entre tandas de generación; se valida con lámina QA). Archivos: atlas nuevo o columnas extra, `game.js` (`anchors`, `fighterPose`). Verificación: lámina QA de 4 identidades × 3 poses + capturas en pelea.

**4. Cámara de pelea dinámica.**
Encuadre que sigue a los dos luchadores: zoom hasta ~1.35× cuando están cerca (manteniendo piso y ambos cuerpos), punch-in breve en impactos fuertes y en el K.O. Con `prefers-reduced-motion`, cámara fija como hoy.
Beneficio: cumple el criterio de caras ≥65 px la mayor parte del tiempo **sin tocar arte**, y le da lenguaje de transmisión. Esfuerzo: **medio-bajo**. Riesgo: **bajo** (la simulación no cambia; es transformación de render). Archivos: `game.js` (`draw`), `backdrop.js`. Verificación: capturas cerca/lejos en ambas orientaciones; suites intactas.

### Eje 2 · Jugabilidad

**5. K.O. con peso: cámara lenta y repetición del golpe final.**
Al conectar el golpe que define la pelea: 0,8 s a velocidad 0,3 con zoom; después, repetición de ~2,5 s del intercambio final con placa «REPETICIÓN» (buffer circular de snapshots del motor; el estado es chico y ya existe `snapshot()`). Se puede saltar.
Beneficio: el momento que más importa en un juego entre amigos pasa a festejarse. Esfuerzo: **medio**. Riesgo: **bajo-medio** (interacción con pausa/skip). Archivos: `game.js`, `presentation.js`. Verificación: prueba de que el buffer no muta el motor + manual.

**6. Combos que encadenan de verdad.**
Ventana de cancelación **solo al acertar** y **solo dentro de la receta del personaje**: conectar el paso N permite iniciar el paso N+1 durante la recuperación, con stun que lo sostiene. El daño total del encadenado queda acotado (escala 100 % / 80 % / 70 %).
Beneficio: las recetas pasan de decorativas a tácticas; el rival aprende a bloquear el cierre. Esfuerzo: **medio**. Riesgo: **medio** (equilibrio; la CPU en Difícil/Experto debe poder defenderse). Archivos: `engine.js`, pruebas nuevas en `tests/`. Verificación: tests de encadenado garantizado al acertar + simulaciones de dificultad existentes.

**7. Resistencia de guardia.**
Barra corta que se desgasta al absorber golpes bloqueando y se regenera al soltar; al vaciarse, apertura de 0,8 s con anuncio del relator. El abrazo de Vict sigue siendo el especialista anti-bloqueo (lo rompe sin desgastarlo).
Beneficio: todos los personajes tienen respuesta a la tortuga y bloquear se vuelve una decisión, no un estado. Esfuerzo: **medio**. Riesgo: **medio** (HUD + CPU). Archivos: `engine.js`, `game.js` (HUD), `style.css`, `tests/`. Verificación: tests de desgaste/regeneración y simulación de Experto.

**8. Entrenador de combo en vivo.**
Al acertar un paso de tu receta, el botón del paso siguiente se ilumina mientras dura la ventana; el relator lo canta la primera vez por partida.
Beneficio: enseña la técnica dentro de una partida breve, como pide el encargo, sin tutorial aparte. Esfuerzo: **bajo**. Riesgo: **bajo**. Archivos: `game.js` (`updateHud`), `style.css`, `presentation.js`. Verificación: manual + prueba del estado de resaltado.

### Eje 3 · Originalidad (liga de amigos y transmisión argentina)

**9. EL ALIENTO — la tribuna como mecánica (la principal; ver sección C).**
Medidor de tribuna que sube con combos, técnicas y jugar hacia adelante, y baja con la tortuga y el tiempo muerto. Tribuna encendida: energía carga más rápido, banderas y bombo, relator al palo. Regla anunciada y legible: «jugá vistoso y la tribuna te empuja». Es mecánica (cambia decisiones: vistoso vs. seguro), no decoración — el público que ya reacciona (`backdrop.cheer`) pasa de adorno a recurso.
Esfuerzo: **medio**. Riesgo: **medio** (equilibrio del bonus; empezar suave). Archivos: `engine.js` (medidor y regla), `backdrop.js`, `game.js` (HUD), `presentation.js`. Verificación: tests de las reglas del medidor + sesión de juego.

**10. Tabla de la Liga de Amigos (persistencia local).**
Guardar en `localStorage` resultados por personaje y dificultad: rachas, torneos ganados, historial entre personajes. Pantalla «LA FECHA» en el menú con la tabla y el título del momento («EL PARK viene de 3 al hilo»). Sin cuentas, sin red; si no hay storage, se oculta.
Beneficio: convierte partidas sueltas en una liga permanente del grupo — el corazón «Crash Bash con amigos». Esfuerzo: **bajo-medio**. Riesgo: **bajo**. Archivos: módulo nuevo `league.js`, `index.html`, `style.css`, `tests/`. Verificación: pruebas con storage simulado.

**11. Transmisión con memoria.**
El «CARA A CARA» y el relator usan la tabla: historial entre esos dos («3–1 en el año»), racha, revancha pendiente, frases parametrizadas por contexto (remontada, últimos diez, paliza). Solo datos de partidas: nada biográfico inventado, listo para recibir las frases reales del grupo cuando estén.
Beneficio: la transmisión deja de ser genérica y se vuelve de ustedes. Esfuerzo: **bajo**. Riesgo: **bajo**. Archivos: `presentation.js`, `league.js`. Verificación: manual con historial simulado.

### Eje 4 · Vanguardia con utilidad

**12. PWA + vibración + pantalla despierta + calidad adaptable.**
`manifest` + service worker en `dist/` (instalable en pantalla de inicio, carga offline: los ~9 MB se bajan una vez); `navigator.vibrate` opcional en impactos (Android; iOS Safari no lo soporta y queda en silencio — respaldo limpio); Wake Lock durante la pelea; medidor interno de frame-time que reduce partículas/efectos si el teléfono no sostiene el ritmo. Todas APIs probadas y documentadas, sin dependencias.
Beneficio: en el teléfono se siente app nativa; nadie re-descarga 9 MB por partida. Esfuerzo: **medio**. Riesgo: **bajo** (el HTML de release sigue igual; el SW vive solo en la versión servida). Archivos: `dist/manifest.webmanifest`, `dist/sw.js`, `index.html`, `game.js`, `tools/build-offline.cjs`. Verificación: Lighthouse PWA, instalación real en Android, suite offline existente.

Extra de bajo costo si sobra lugar: **Gamepad API** para jugar con joystick cuando lo abren en una compu o TV (mapea a las acciones existentes; sin UI nueva).

---

## C. Dirección artística y mecánica original

**Dirección artística recomendada: «figurita de potrero en transmisión».**
No perseguir el fotorealismo (con 4 poses generadas es imposible sostenerlo); asumir el collage como estética deliberada de **figurita de álbum**: borde de sticker sutil y parejo alrededor de cada luchador (trazo claro de ~2 px + sombra dura, aplicable por código), tintas ambientales planas por estadio que bañan cuerpo y cara juntos, grano de imprenta en placas y UI (la identidad JK Sports ya existe y es buena). La cabeza fotográfica grande es la gracia del juego —estilo bobblehead—: no se "arregla", se **integra** (misma luz, mismo borde, mismo piso). Razones propias de este juego: las caras reconocibles son requisito; la figurita conecta fútbol argentino + amigos + humor; y casi todo se aplica en runtime u horneado, sin regenerar arte.

**Mecánica original principal: EL ALIENTO (ítem 9).**
Es la que más conecta lo que el juego ya es (estadios reales, público que reacciona, relator) con una decisión de juego legible. Primera regla simple: el medidor sube con combos/técnicas/iniciativa y baja con tortuga y pasividad; lleno, la energía carga más rápido y la tribuna explota. A futuro escala naturalmente (hinchada propia por personaje, cánticos, interacción de escenario anunciada).

---

## D. Plan en tres entregas (cada una termina jugable)

**v9 — «La transmisión» (alto impacto, poco esfuerzo):** ítems 1 (horneado), 4 (cámara dinámica), 5 (K.O. lento + repetición), 8 (entrenador de combo) + limpieza rápida de halos rojos del atlas (parte del 2) + contador fps de desarrollo. Resultado: el mismo juego, más grande en pantalla, más fluido, con finales con peso y combos que se entienden.

**v10 — «El cuerpo» (animación y combate):** ítems 2 (integración, con muestra Matt/Bombonera aprobada antes de los cuatro), 3 (poses de daño/salto/festejo), 6 (encadenado real), 7 (resistencia de guardia). Resultado: el salto visible de calidad de animación y un combate con decisiones.

**v11 — «La liga» (innovación justificada):** ítems 9 (Aliento), 10 (tabla), 11 (transmisión con memoria), 12 (PWA + vibración + calidad adaptable). Resultado: app instalable, con liga permanente y tribuna como mecánica.

Criterios transversales: trabajar sobre copia con registro por versión; `npm test` + `npm run build` + suite offline en cada entrega; capturas a 390×844 y 844×390; `prefers-reduced-motion` respetado en cámara, vibración y Aliento; el crecimiento de peso se justifica por entrega (v9 no agrega imágenes; v10 agrega un atlas).

---

## E. Primer paquete a implementar (v9)

**Se conserva (existente):** motor y reglas intactas (`engine.js` no se toca en v9), torneo, dificultades, Justialities, pruebas, build de release.

**Defectos observados que corrige:** filtros/sombras por cuadro (`backdrop.js:24,44,56`, `game.js:166,171`); cámara que no mira la pelea; caras bajo el criterio de 65 px en horizontal; K.O. sin tratamiento; recetas de combo sin guía en vivo; halos rojos del atlas.

**Propuestas nuevas que agrega:** cámara dinámica con reduce-motion, cámara lenta + repetición del K.O., entrenador de combo, overlay de fps con `?debug=1`.

**Verificación comprometida:** las 8 suites + una nueva (buffer de repetición no muta el motor); `npm run build` y suite offline; lámina antes/después del horneado (igualdad visual); capturas en ambas orientaciones; medición de fps en emulación de este entorno **declarada como emulación**, más una pasada tuya en teléfono físico con el overlay.

**Supuestos explícitos (resuelvo así salvo que digas otra cosa):** se mantiene el bobblehead y las fotos reales de estadios; apodos y frases siguen siendo ficción del juego hasta que pases las reales; el quinto lugar no se toca; la entrega sigue siendo fuentes + HTML único regenerado con `npm run build`; la muestra de integración (Matt/Bombonera) se aprueba antes de aplicar el cambio a los cuatro.

**Tres preguntas que cambian materialmente el resultado:**

1. **GitHub y las fotos.** El repo `dhgalli/Proyecto1mvt` es **público**, así que subir el juego ahí publica las fotos de tus amigos. ¿Lo pasás a privado (en GitHub: Settings → General → abajo de todo, «Change repository visibility» → Private) o creo la estructura para que el juego viva en este repo recién cuando sea privado? Mientras tanto trabajo con el zip y te devuelvo zip + HTML jugable.
2. **Teléfono de referencia.** ¿Qué modelo usan más para jugar? (marca/modelo alcanza). Define el presupuesto real de calidad para el objetivo de 60 fps y contra qué pruebo el overlay de fps.
3. **Sabor del combate.** ¿Querés que las recetas encadenen garantizado al acertar (más arcade: conectás el primero y la secuencia sale) o preferís el ritmo actual de golpes sueltos donde el combo es solo un bonus? Define los ítems 6 y 7.

---

## Actualización — 9 de octubre de 2026: v9 entregada

Decisiones del usuario: el repo pasará a privado (pendiente de hacerse efectivo; hasta entonces el código del juego viaja por zip), teléfono de referencia **Samsung Galaxy A56**, y el combate conserva el ritmo actual (sin encadenado arcade; el ítem 6 queda descartado).

Entrega 1 («La transmisión») implementada y entregada como `Justicombat-v9-continuar.zip` + HTML jugable: luz y color horneados (en emulación por software la pelea pasó de ~9 a ~38 fps; falta la medición física con `?debug=1` en el A56), cámara de transmisión con zoom hasta 1,3×, K.O. en cámara lenta con caída animada, repetición saltable del golpe final tras un K.O., entrenador de combo en vivo, halos rojos de los atlas atenuados y overlay de fps de desarrollo. `engine.js` intacto; las 8 suites de v8 más una nueva (`test-v9.cjs`) pasan y el release offline se regeneró. El detalle completo está en `NOTAS-V9.md` dentro del zip.
