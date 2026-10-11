# Guion: Landing con video IA gratis en mi RTX

Debajo de algunas frases, en cursiva, va cómo las pronuncia la voz IA.


## Intro


**En pantalla:** `landing:ia`

- Esta landing se recorre como una película.
- Cada escena es una foto que la inteligencia artificial convirtió en video.
- Y todo lo generé en mi propia computadora, sin pagar un solo crédito.

**En pantalla:** `slide:hook`

- En este video te cuento cómo lo hice, cuánto tarda, qué me salió mal y el truco que lo hizo el doble de rápido.

## La idea


**En pantalla:** `slide:idea`

- Todo empezó con un video donde convertían seis fotos de un restaurante en una landing animada.
- Usaban Claude Code y Higgsfield, un servicio que genera los videos en la nube.
  - _voz: Usaban Clod Coud y Jigsfild, un servicio que genera los videos en la nube._
- El problema: Higgsfield funciona con créditos que se pagan.
  - _voz: El problema: Jigsfild funciona con créditos que se pagan._
- Así que me pregunté: ¿se puede hacer lo mismo gratis?

## El setup


**En pantalla:** `slide:setup`

- Tengo una PC con una RTX 5060 Ti de 16 GB, y la uso desde mi laptop a través de Tailscale.
  - _voz: Tengo una pe ce con una erre te equis cincuenta sesenta te i de dieciséis gigas, y la uso desde mi laptop a través de Teil Skeil._
- En esa PC instalé ComfyUI, que es como un motor para correr modelos de imagen y video.
  - _voz: En esa pe ce instalé Cómfi iu ai, que es como un motor para correr modelos de imagen y video._

**En pantalla:** `slide:modelos`

- Antes de descargar nada, comparé los modelos de video abiertos que hay hoy.
- Me quedé con Wan 2.2: es el que más respeta la foto original y tiene licencia Apache, libre para todo.
  - _voz: Me quedé con Guan dos punto dos: es el que más respeta la foto original y tiene licencia Apache, libre para todo._
- Los más nuevos, como LTX 2.5 o MiniMax H3, no entran bien en 16 GB o tienen licencias raras.
  - _voz: Los más nuevos, como ele te equis dos punto cinco o Mini Max hache tres, no entran bien en dieciséis gigas o tienen licencias raras._
- También uso una LoRA que hace que el modelo genere en cuatro pasos en vez de treinta.
  - _voz: También uso una lora que hace que el modelo genere en cuatro pasos en vez de treinta._

## Paso a paso


**En pantalla:** `slide:paso1`

- Si lo quieres replicar, estos son los pasos. Primero, descarga ComfyUI portable para NVIDIA desde su GitHub.
  - _voz: Si lo quieres replicar, estos son los pasos. Primero, descarga Cómfi iu ai portable para envidia desde su Guit Jab._
- Si tu tarjeta es de la serie 50, fíjate que sea una versión con CUDA 12.8 o más nueva. Las viejas no funcionan.
  - _voz: Si tu tarjeta es de la serie cincuenta, fíjate que sea una versión con cuda doce punto ocho o más nueva. Las viejas no funcionan._
- No necesitas instalar Python: la versión portable trae el suyo.
  - _voz: No necesitas instalar páiton: la versión portable trae el suyo._

**En pantalla:** `slide:paso2`

- Segundo, los modelos. Son seis archivos, unos treinta y cinco gigas, y van en carpetas distintas dentro de models.
- Los dos modelos de Wan, el de ruido alto y el de ruido bajo, en la versión fp8, que entra en 16 GB.
  - _voz: Los dos modelos de Guan, el de ruido alto y el de ruido bajo, en la versión efe pe ocho, que entra en dieciséis gigas._
- El codificador de texto, el VAE y las dos LoRAs de cuatro pasos. Todo eso está en el repositorio de Comfy en Hugging Face.
  - _voz: El codificador de texto, el ve a e y las dos loras de cuatro pasos. Todo eso está en el repositorio de Cómfi en Jaguin Feis._
- Ponlos en un disco SSD. Desde un disco duro externo, cargar treinta gigas tarda una eternidad.
  - _voz: Ponlos en un disco ese ese de. Desde un disco duro externo, cargar treinta gigas tarda una eternidad._

**En pantalla:** `slide:paso3`

- Tercero, si lo vas a usar desde otra computadora como yo, arranca ComfyUI con listen y abre el puerto solo para tu red de Tailscale.
  - _voz: Tercero, si lo vas a usar desde otra computadora como yo, arranca Cómfi iu ai con lisen y abre el puerto solo para tu red de Teil Skeil._
- Así no queda expuesto a toda tu red local, ni a internet.

**En pantalla:** `slide:paso4`

- Y cuarto, tu RAM importa. Con 16 GB de video el modelo pasa una parte a la memoria del sistema, y con 32 GB vas justo.
  - _voz: Y cuarto, tu ram importa. Con dieciséis gigas de video el modelo pasa una parte a la memoria del sistema, y con treinta y dos gigas vas justo._
- Si tienes 16 GB de RAM, usa la versión de 5B de Wan, que es más liviana.
  - _voz: Si tienes dieciséis gigas de ram, usa la versión de cinco be de Guan, que es más liviana._

## Los primeros clips


**En pantalla:** `imagen:fotos`

- Para probar usé seis fotos de Unsplash: una terraza, el salón, tres platos y una mesa compartida.
  - _voz: Para probar usé seis fotos de Ansplash: una terraza, el salón, tres platos y una mesa compartida._

**En pantalla:** `clip:04`

- A cada foto le escribí un prompt con el movimiento que quería: vapor, la salsa brillando, la cámara acercándose.

**En pantalla:** `clip:05`

- Cada clip de cinco segundos tardó unos dos minutos y medio.

**En pantalla:** `clip:03`

- Y en la comida, el resultado es muy bueno. Mira ese brillo.

## El problema de las caras


**En pantalla:** `clip:01`

- Pero en las escenas con gente apareció un problema.

**En pantalla:** `imagen:caras`

- Si haces zoom, las caras son manchas. A 480p, cada cara ocupa unos ocho píxeles y el modelo las inventa.
  - _voz: Si haces zoom, las caras son manchas. A cuatrocientos ochenta pe, cada cara ocupa unos ocho píxeles y el modelo las inventa._
- La solución fue generar esas escenas a 720p. Abajo ves la diferencia.
  - _voz: La solución fue generar esas escenas a setecientos veinte pe. Abajo ves la diferencia._

**En pantalla:** `clip:01_720p`

- No quedan perfectas, pero en una landing que se recorre rápido funcionan bien.

**En pantalla:** `landing:fotos`

- Igual armé una segunda versión que usa las fotos originales con movimiento hecho en código, para comparar.

## SageAttention


**En pantalla:** `slide:atencion`

- Ahora, el truco. Para generar un video, el modelo divide cada frame en miles de pedacitos.
- Y cada pedacito mira a todos los demás para decidir cómo verse. Eso se llama atención, y es lo más lento de todo.

**En pantalla:** `slide:sage`

- SageAttention hace ese mismo cálculo con números más cortos, de ocho bits en vez de dieciséis.
  - _voz: Seich atenshon hace ese mismo cálculo con números más cortos, de ocho bits en vez de dieciséis._
- Es como redondear: casi no cambia el resultado, pero la tarjeta lo calcula mucho más rápido.

**En pantalla:** `comparacion:A_base:B_sage`

- Lo medí con la misma foto, el mismo prompt y la misma semilla. A la izquierda sin SageAttention: 166 segundos.
  - _voz: Lo medí con la misma foto, el mismo prompt y la misma semilla. A la izquierda sin Seich atenshon: ciento sesenta y seis segundos._
- A la derecha, con SageAttention: 81 segundos. El doble de rápido.
  - _voz: A la derecha, con Seich atenshon: ochenta y un segundos. El doble de rápido._
- La calidad es la misma. La gente se mueve un poco distinto, como si tiraras el dado otra vez, pero no se ve peor.

**En pantalla:** `slide:sage_tip`

- Ojo si tienes una tarjeta de la serie 50: no lo instales con pip directo, porque baja una versión vieja que da frames negros.
  - _voz: Ojo si tienes una tarjeta de la serie cincuenta: no lo instales con pip directo, porque baja una versión vieja que da frames negros._
- Busca un wheel precompilado para Windows que coincida con tu versión de PyTorch, e instala también Triton para Windows.
  - _voz: Busca un güil precompilado para güindous que coincida con tu versión de pái torch, e instala también tráiton para güindous._
- Y en vez de activarlo para todo ComfyUI, lo activo con un nodo de KJNodes dentro del flujo. Así puedo comparar con y sin.
  - _voz: Y en vez de activarlo para todo Cómfi iu ai, lo activo con un nodo de ka jota nouds dentro del flujo. Así puedo comparar con y sin._

**En pantalla:** `clip:02_720p`

- Con SageAttention, las escenas a 720p bajaron de casi ocho minutos a unos cuatro y medio.
  - _voz: Con Seich atenshon, las escenas a setecientos veinte pe bajaron de casi ocho minutos a unos cuatro y medio._

## Mi error


**En pantalla:** `comparacion:A_base:C_3samplers`

- También probé otra técnica: hacer los primeros pasos sin la LoRA rápida, para que el movimiento salga mejor.
  - _voz: También probé otra técnica: hacer los primeros pasos sin la lora rápida, para que el movimiento salga mejor._
- Y pasó esto: el modelo llenó la terraza de luces navideñas que no estaban en la foto.

**En pantalla:** `slide:error`

- Mi primera conclusión fue que la técnica no servía. Pero en realidad el error era mi configuración.
- Así que lo repetí con ocho configuraciones distintas.

**En pantalla:** `comparacion:D_sage_3s:J_sage_3s_v5_neutro`

- El culpable era el prompt. Decía luces cálidas, y sin la LoRA el modelo le hace mucho más caso al texto.
  - _voz: El culpable era el prompt. Decía luces cálidas, y sin la lora el modelo le hace mucho más caso al texto._
- Vio unos pinos, leyó luces, y los decoró como árboles de Navidad.

**En pantalla:** `slide:leccion`

- La lección: si el prompt dice luces, el modelo va a dibujar luces. Describe solo lo que hay y el movimiento que quieres.
- Y para esta foto, la técnica tardaba hasta tres veces más sin verse mejor. Así que me quedé con lo simple.

## La landing


**En pantalla:** `landing:ia`

- Para la landing, extraje cada clip a imágenes y las dibujo en un canvas según cuánto haces scroll.
- Así el video avanza con tu dedo, sin saltos, como en las páginas de producto de Apple.
- ¿Por qué no un video normal? Porque al mover un video con el scroll, el navegador tiene que buscar cuadros y se traba.
- Con imágenes sueltas, cada posición del scroll es un cuadro exacto, y se ve fluido hasta en el celular.
- Entre escena y escena hago un fundido, y los textos aparecen y desaparecen según avanzas.

**En pantalla:** `web:benchmark`

- Está publicada en GitHub Pages, con las dos versiones y una página para comparar todos los videos del benchmark.
  - _voz: Está publicada en Guit Jab Peiyes, con las dos versiones y una página para comparar todos los videos del benchmark._

## Una cosa más


**En pantalla:** `slide:voz`

- Una cosa más: esta voz que estás escuchando no la grabé yo. Es mi voz clonada con IA, también en mi RTX.
  - _voz: Una cosa más: esta voz que estás escuchando no la grabé yo. Es mi voz clonada con IA, también en mi erre te equis._
- Grabé veinte segundos, comparé dos modelos y me quedé con F5, que es el que más se parece a mí.
  - _voz: Grabé veinte segundos, comparé dos modelos y me quedé con efe cinco, que es el que más se parece a mí._
- Genera cada frase en unos dos segundos.

## Cierre


**En pantalla:** `slide:resumen`

- En resumen: Wan 2.2 en tu propia tarjeta, SageAttention para ir el doble de rápido, y 720p si hay caras.
  - _voz: En resumen: Guan dos punto dos en tu propia tarjeta, Seich atenshon para ir el doble de rápido, y setecientos veinte pe si hay caras._
- Todo el código, los scripts y el benchmark están en GitHub. Te dejo los links en la descripción.
  - _voz: Todo el código, los scripts y el benchmark están en Guit Jab. Te dejo los links en la descripción._

**En pantalla:** `landing:ia`

- Si te sirvió, suscríbete. Y cuéntame en los comentarios qué te gustaría que pruebe en mi RTX.
  - _voz: Si te sirvió, suscríbete. Y cuéntame en los comentarios qué te gustaría que pruebe en mi erre te equis._
