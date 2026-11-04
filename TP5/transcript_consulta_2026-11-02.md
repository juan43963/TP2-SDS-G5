# Transcripción — clase de consultas (2026-11-02)

Generada automáticamente con faster-whisper (modelo small, español); puede contener errores.

[00:00:00] Que hay que mezclar step driven y time step driven y event driven y nada la pregunta es más o menos
[00:00:14] para saber si está bien, la idea de cómo lo estamos encarando. Lo que tenemos pensado es en principio
[00:00:22] fijarnos, ir variando no sé si me explico o si me voy a entender lo que digo pero que para determinada
[00:00:32] altura en la caja uses un sistema o un método o el otro pero ahí la duda que se nos generaba era
[00:00:46] cómo manejo supongamos que estoy en las partículas con event driven y me dice y calcula que el tiempo
[00:00:55] de choque a una partícula tal es tanto pero esa partícula capaz es una de las que se mueve
[00:01:02] por time step driven y capaz cuando llega ese tiempo ya no esté en el mismo lugar no sé si
[00:01:10] crees cómo va a ser un dibujo a ver si
[00:01:35] yo le digo bueno aparte se ve el dibujo si
[00:01:44] digo que se yo a partir de acá para abajo uso time step y de acá para arriba uso event driven
[00:01:56] entonces yo tengo una partícula acá no sé tiene que venir para acá
[00:02:03] y dice bueno el próximo choque es con la partícula
[00:02:08] esta que está acá y va a ser en 20 segundos pero la partícula está cuando pasaron los 20
[00:02:14] segundos como se estuvo moviendo con estuvo avanzando por el time step driven que se yo capaz de estar
[00:02:18] acá y entonces el choque no se produce tenemos que tal vez lo de la
[00:02:46] una observación también lo de partir así en tan estrictamente por un por una altura
[00:02:58] no sea un buen criterio muy amigable pero bueno se puede plantear
[00:03:06] pero igual creo que esto está planteando es más allá de este criterio que podría pasar con
[00:03:12] otros sí pero bueno lo que se supone es que supongamos que la partícula de abajo
[00:03:24] está avanzando con time step driven pero
[00:03:31] la el pronóstico dice va a chocar en 10 segundos para la para la de arriba y si la
[00:03:39] abajo está aislada que no choca con nadie
[00:03:44] tendría que en esos 10 segundos seguir avanzando con su velocidad constante y efectivamente chocar
[00:03:51] a los 10 segundos claro pero si tuvo una colisión en el medio es el tema bueno también entonces
[00:03:58] tuvo una colisión en medio que claro bueno entonces por eso si las partículas que tienen
[00:04:05] que están teniendo colisiones para si tuve una colisión en el medio es que había un evento
[00:04:14] de choque más inmediato que el que el otro que me planteaste claro pero yo no los calculé porque
[00:04:21] estas entre estas dos partículas no calculó los tiempos de choque porque en realidad
[00:04:26] están estoy usando el time step driven entonces no me importan para el driven o si bueno parece
[00:04:33] que sí te tiene que importar porque se las hay a regular igual ok si porque porque la cuestión es
[00:04:43] que la para la partícula de abajo había un choque más inmediato que el que estás diciendo que es el
[00:04:50] más inmediato y ese choque no lo estás teniendo en cuenta porque porque estás diciendo de esta
[00:04:58] línea para abajo solo miro time step driven bueno claramente no o sea una cosa es que de la línea
[00:05:06] para abajo resuelva que las partículas se muevan con time step driven otra cosa es que
[00:05:12] que ignores los los choques en cuanto ahí vendrían que tendrían o sea más allá de los tiempos de
[00:05:26] colisión se pueden calcular suponente vos tenés un un esquema totalmente time step driven o sea todas
[00:05:34] las pelotas se mueven time step driven para ese esquema siempre en cada instante podés calcular
[00:05:41] todos los tiempos de colisión futuros con los métodos de y vendrían eso se hace de hecho se
[00:05:49] tenés se tiene una película con con posiciones de las partículas y velocidades todas cada un paso
[00:05:56] fijo pero en cada paso con las velocidades que tienen podés hacer el cálculo de que hacemos de
[00:06:03] colisiones cuando hacíamos y vendrían eso no no está prohibido no solo no está prohibido se hace
[00:06:09] y es necesario hacerlo y en este caso me está preguntando se pone evidencia de que es necesario
[00:06:15] hacerlo o sea no quiere decir que si haces moverse las partículas con time step fijos no
[00:06:23] puedas estar calculando cuál sería el próximo tiempo de choque dado que tienen la velocidad que
[00:06:30] tienen y las posiciones que tienen entendés eso si pero algo que no me termina de cerrar porque
[00:06:38] tomamos que yo los choque los tiempos de choque entre todas no por más que esté son lo solamente
[00:06:45] y vendrían acá en este tramo qué pasa acá me va a decir bueno acá tenés una colisión antes
[00:06:53] entonces termino autorizando por tae por termino van o no la actual tipo calculó el choque pero no
[00:07:01] hago la actualización por el time step driven sino por perdón por y vendrían sino por
[00:07:07] time step driven sería la lógica no sé la lógica es que tendría estas tres partículas que tenés acá
[00:07:15] no importa cómo lo resuelvas podés calcular los choques de todas contra todas el dos tiempo de
[00:07:22] choque de todas contra todas o sea eso no calcula esos tiempos de choque no es exclusivo de una
[00:07:30] simulación que avanza con eventos o sea es necesario hacerlo cuando avanza por eventos pero no es
[00:07:37] exclusivo no es que no puedes hacer ese cálculo en cualquier otra simulación así que acá podés
[00:07:45] calcular los tiempos de choque de estas tres partículas con las tres o sea los nueve choques
[00:07:52] posibles que hay o los seis choques posibles que hay los podés calcular todos esos tiempos y quedarte
[00:07:59] con lo que va a ser lo más inmediato si lo más inmediato va a ser que choca en las dos partículas
[00:08:04] abajo que se mueven con time step driven bueno move las constantes de priben hasta ese tiempo de
[00:08:10] choque move la de arriba durante ese tiempo de choque para actualizarla claro o sea claro si yo
[00:08:18] muevo esto ahora me genera otra duda que creo que debo tener el concepto mal si actualizo estas dos
[00:08:24] por time step no si a esta también la tengo a actualizar si pero no necesariamente todos los
[00:08:34] time step la puedes actualizar hasta que choca en las dos de abajo claro o sea si está bien
[00:08:44] que se yo está mi time step es de cinco y esta de uno perdón y esta tarda cinco entonces
[00:08:50] esta la actualizo cinco de golpe y a estar actualizando de uno es lo que les dice claro
[00:09:01] bien eso está entonces y los otros era igual pero algo igual esto nunca lo hicimos y
[00:09:12] y yo no tengo todas las respuestas mi franco ni nadie es importante que o sea no es lo típico
[00:09:21] que hay una forma establecida de hacerlo que nosotros le estamos tratando enseñar sino que lo que
[00:09:29] estamos tratando enseñar es de que resuelvan los problemas que surjan para poder llevar adelante
[00:09:35] algo distinto entonces ahora como que estamos pensando entre todos pero no es que quiero decir
[00:09:48] ustedes también piensen que es un problema que hay que resolver y fíjense qué idea se les ocurre
[00:09:56] para resolverlo ahora ahora esto lo resolvimos no pero capaz que en un rato surge otro problema
[00:10:02] parecido o mañana y no crean que a los profesores saben cómo se resuelve es que vamos la idea es
[00:10:12] que lo resolvamos que todos aportemos soluciones porque digamos que es un problema que no es nuevo para
[00:10:21] todos ok la leche esa creación seguir perdón que te interrumpí también y lo otro medio que acá es
[00:10:30] una de las cosas que pidi en un cedo que resolvamos que sé yo cómo se mueve en esta es cómo se
[00:10:37] actualizan las velocidades después de una colisión acá arriba no porque supongamos que se yo estas
[00:10:44] dos venían para acá y colisionaron acá y que se yo después salieron una disparada para acá
[00:10:52] y la otra salió disparada para acá y nada yo tengo que volver a acomodar las velocidades para
[00:10:59] que vuelvan a apuntar acá a la puertita es lo que habíamos pensado era avanzó lo que sería un
[00:11:08] time step de estos de acá del de lo que se está moviendo con este es esas dos partículas
[00:11:16] las avanza un time step con estas velocidades que calcula acá que me dio por la que me dieron
[00:11:21] por la colisión y después de eso las modificó directamente vuelven a apuntar a la puertita
[00:11:27] hasta que vuelvan a colisionar bueno es una buena idea esa vez no lo habíamos pensado así y es posible
[00:11:45] imagino que ahí pueden empezar a colisionar muchas veces pero bueno también no tienen no tienen
[00:11:58] porque esas velocidades que acabas de dibujar lo que sería la velocidad de inmediatamente después
[00:12:04] del impacto no tienen porque ser las mismas de del tp divendriven no porque porque aquellas
[00:12:14] partículas eran partículas que no tenían autopropulsión y eran como pelotas de billar
[00:12:20] digamos acá no no son pelotas de billar entonces no digamos no conservan el impulso no conservan
[00:12:29] nada no tendrían porque esas velocidades fue el choque ser iguales que la del tp 3
[00:12:38] como esto es una regla que estamos proponiendo ahí yo diría que esas velocidades podrían ser
[00:12:45] tipo en el contacto y parte que el model que en la dirección que más aleje a las partículas
[00:12:51] o sea me gusta porque no te habíamos dicho como separarlas algo arbitrario acá me gusta que sea
[00:13:01] una velocidad como la que tenían de caminar por un delta tchiquito lo que sí nada más trataría
[00:13:10] que la dirección sea la que más las aleja o sea que en las direcciones opuestas a la línea
[00:13:20] que une los centros de más puede ser que puede ser que esas dos igual están chocando bastante
[00:13:31] seguido pero bueno es esta regla sino también se puede pensar porque también algo que este esquema
[00:13:42] te impide es por ejemplo pensar que esas dos partículas que chocaron arriba mientras se
[00:13:52] resuelve el choque pueden hacer timestamp driven o sea que varios choques se estén
[00:14:10] o sea podría ser que eliven driven avanza las partículas hasta que están borde a borde
[00:14:15] y a partir de ahí se hace tan este trimen para resolver todo el choque bien hasta que se
[00:14:22] separen de nuevo y ahí cuando se paran de nuevo recuperan su estado y vendría o sea que sería y
[00:14:30] vendría mientras no choca en cuanto choca ahí está este trimen está este trimen dejan de
[00:14:37] chocar y ahí vuelve se vuelve a calcular como y vendría o sea esa sería otra forma de resolver
[00:14:44] los choques pero si no estuviera esta separación por por áreas se entiende esa sí sí igual la
[00:14:57] que vos propones igual a proponer está buena puede funcionar así que me parece bien primero
[00:15:08] la que propone y lo otro es una idea no es la forma de resolverlo porque está bueno que lo
[00:15:16] resolvamos de distintas maneras así que me gusta más la que usted propone a ver qué pasa perfecto
[00:15:24] bueno eso es la verdad era todo lo que teníamos por ahora para preguntar
[00:15:27] está bien bueno buenísimo gracias