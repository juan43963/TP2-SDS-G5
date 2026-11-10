# Transcripción – Consultas SDS (Grupo 5)

_Transcripción automática (Whisper) con separación de voces automática: puede haber errores de palabras y de atribución del hablante, sobre todo donde hablan superpuestos. Se corrigieron a mano los términos técnicos obvios._

**[00:00] PROFESOR:** Bueno, ¿quién quiere comenzar? Adelante. ¿Queré compartir pantalla?

**[01:29] VOS (Lucas):** La parte de la fuerza de rozamiento tangencial.

**[01:37] PROFESOR:** Sí, que si se les bloquea pueden sacar la fuerza tangencial.

**[01:50] VOS (Lucas):** Es que claro, nosotros hicimos los dos análisis por las dudas. Y nos daba uno que era mucho más rápido que el otro al evacuar. Claro. Y no sabíamos si dejar los dos, si dejar uno.

**[02:09] PROFESOR:** No, lo que dice es que si se bloquea con la fuerza tangencial la podrían sacar para que no se bloquee. Porque la puerta está medio chica. Pero si no se les bloquea, está bien. ¿Qué grupo? El 5. Sí, creo pues.

**[02:32] COMPAÑERO:** Bueno.

**[02:34] VOS (Lucas):** Entonces, o sea, nos da bastante más en el... Cuando hicimos la comparación de Time Step contra Event Driven, nos daba, por ejemplo, que daba mucho más en Time Step. Daba 900 segundos contra 200. Y en el híbrido, como está mucho más tiempo en estado Time Step que en Event Driven, nos daba más parecido al Time Step. Pero después, cuando lo sacamos, nos dio más parecido. Nos dio casi 140 segundos, más o menos, que es parecido a Event Driven.

**[03:13] PROFESOR:** Perdón, ahí en esa tabla, fíjate el número de decimales que yo pondría una cifra significativa menos. Grupo 5.

**[03:43] VOS (Lucas):** Sí, esto fue un análisis rápido, en realidad, para ver cómo daba comparando con y sin. No, no creo que presentemos esto más que bien.

**[03:56] PROFESOR:** No, o sea, para no sobrecargar las cosas, sí. Esperá un cacho, ¿eh? Sí, sí. El tema es que cuando están amontonados en la puerta, la solución como verdadera es la de Time Step Driven, porque Event Driven, lo que debería pasar es que no se puede resolver bien. Porque para Event Driven hay que poner una regla de cómo resolver las colisiones, que es una regla artificialmente inventada para poder avanzar. Digamos, un esquema de simulación que sería fiel a resolver el problema es que una vez que entran en contacto, dos partículas, todo ese proceso de contacto se resuelva con Time Step Driven. Eso sería fiel a resolver bien el problema. Como se pide hacer toda una simulación sin usar Time Step Driven, ahí en el Event Driven hay que poner alguna regla de resolver colisiones. O sea, ahí, al haber esa regla de resolver colisiones, que es arbitraria, como que no habría rozamiento, podría no haber rozamiento, o podría también generarse como una efervescencia que deje que las partículas salgan fácilmente, o podría generarse algo que las partículas no salen. Entonces, bueno, la parte del Event Driven es como medio solo para comparar, pero está sujeto a la arbitrariedad de la regla con la que definimos las colisiones. Entonces, como que lo que es lo verdadero es Time Step Driven, y usando el Social Force Model, que es lo que se pide, sin fuerza social, se pide en el enunciado. Entonces, al no haber fuerza social, y haber rozamiento, y haber una puerta muy chica, es posible que se trabe, a algunos grupos se les trababan. Entonces, ante ese escenario, les dije, pueden sacar la fuerza tangencial. Pero si no se les traba, y siempre logran completar las evacuaciones, con la fuerza tangencial, entonces no hace falta hacer nada. Ya está.

**[07:05] VOS (Lucas):** Ok. No, o sea, nosotros, bueno, acá se ve, los completos son casi la mitad. Habíamos fijado un tiempo máximo de, creo que, no sé si, 3.000 segundos, o algo por el estilo. Y si pasaba de sombral, la cancelábamos. Y nada, completaron 15.32.

**[07:26] PROFESOR:** 15.32 en Time Step Driven con fuerza tangencial, digamos.

**[07:30] VOS (Lucas):** Claro. Y en el otro lo sacamos y se completaron 13.14. Corrimos menos, pero, bueno, proporcionalmente bastante más.

**[07:40] PROFESOR:** Bueno. Está bien. Entonces, en ese caso, pueden sacarla y listo. Pero no hagámoslo, si quieren hacer una comparación con eso, pónganlo en un apéndice para no sobrecargar la presentación. Ok. Pero elijamos una para la presentación. Yo diría, entonces, viendo esto, sin fuerza social.

**[08:07] VOS (Lucas):** O sea, sin rozamiento.

**[08:10] PROFESOR:** Sin rozamiento, perdón. Ok. Pero ya que estábamos, Lucas, y estamos hablando de este tema, ¿podrías, por favor, ahora, que pasaron unos días, lo que estábamos charlando el otro día en el pizarrón?

**[08:25] VOS (Lucas):** Sí, sí. De hecho, armé una animación.

**[08:27] PROFESOR:** De cómo funciona el mecanismo de resolver las colisiones, en el caso de Event Driven.

**[08:38] VOS (Lucas):** Sí, armé la animación esta que me pareció que está buena, porque muestra los eventos que tiene el sistema. Y nada, básicamente, estos son todos los tipos de eventos que van pasando. Y cada 0,1 segundos, sea cual sea el escenario, mete un steer, que sería como un, si se quiere, un volantazo para la velocidad deseada. ¿Qué es el agujero? Obviamente acá tienen mucho menos partículas, pero la idea es que, bueno, cuando hay un contacto entre dos partículas, hay un evento. Y después de ese evento, puede, por ejemplo, cuando cambia de celda, ahí hay otro evento. O cada 0,1 segundos, cambia la velocidad y sería otro evento. O bueno, todos los otros escenarios que, bueno, contacto con la pared, con el borde de la puerta, o cuando sale del radio fijado.

**[09:46] PROFESOR:** Bueno, pero acá hay, está bien, hay pocas partículas, pero cuando se empiezan a amontonar no me termina de quedar claro. O sea, porque chocan muy cerca de la puerta y en la puerta ahí ya hay muchos círculos y no se entiende. ¿Podríamos hacer un caso con solo dos partículas?

**[10:15] VOS (Lucas):** No sé, porque este ya lo, como que lo, es un GIF.

**[10:19] PROFESOR:** No, no, está bien, pero bueno, plantea una simulación que sean solo dos partículas que empiezan muy cerca, una de otra, ponele... Y decís que cambian la dirección por el choque. Que empiecen para, ponele a cuatro metros de la puerta, en Y4 y X justo al centro de la puerta, que será 5. No, X, mentira. El X del centro, el X del centro que corresponda para que estén a un milímetro sin tocarse...

**[11:03] VOS (Lucas):** Claro, 5 más menos algo.

**[11:04] PROFESOR:** Sí, sí, sí, más o menos los radios de cada una, pero además más un milímetro para que no se estén tocando al principio. Y entonces empiezan a caminar hacia el centro, como las dos van hacia el mismo punto, en algún momento se van a tocar. Y entonces ahí se chocan y ahí se va a ver bien claro cómo se resuelve el tema del choque. Pero bueno, ahí se vería claro en la animación, pero también... O sea, si pueden hacer una animación así para que también quede claro, buenísimo. También se podría hacer con un dibujo, digamos, o con una explicación. Vos la tenés a mano esa explicación, digamos, la...

**[12:00] VOS (Lucas):** Bueno, a un paint. Perdida, ¿no?

**[12:03] PROFESOR:** Sí, sí, con un paint o con palabras, como quieras.

**[12:06] VOS (Lucas):** O sea, irían así dos partículas y acá... Bueno, me quedo medio... Medio malo, pero se entienden. Las dos irían apuntando al...

**[12:26] PROFESOR:** Sí, chocan. Y después del choque...

**[12:30] VOS (Lucas):** Chocan y ahí entran un evento y después las dos... Siguen después del choque con dirección distinta. Y cada 0,1 segundos hay un steer, que es esto que decía acá... Que reacomoda la velocidad a la dc...

**[12:59] PROFESOR:** Bueno, que sería hacia el centro.

**[13:01] VOS (Lucas):** Claro, sí. O sea, iría...

**[13:08] PROFESOR:** Eso, ¿cómo la reacomoda?

**[13:11] VOS (Lucas):** Con el steer y la ecuación. La velocidad.

**[13:26] PROFESOR:** O sea, pero la... Cuando... 0,1 segundos después del choque... Ahí en la ecuación... La... O sea, porque no sé si lo que estás dibujando... Estas flechitas acá son... La velocidad real de la partícula o la velocidad deseada de la partícula.

**[13:50] VOS (Lucas):** Claro. O sea... Supongamos que esta es la deseada y esta es la real. Bueno, lo pongo con otro color. Esa es la real. Esto sería, no sé, en 0,5 segundos. No, en 0,1. Y esto, no sé, en 0,05, por decir algo. Y acá en 0.

**[14:14] PROFESOR:** ¿Por qué 0,05? Recién me habías dicho cada 0,1 segundos.

**[14:20] VOS (Lucas):** Porque quería... Decir entre... O sea, esta sería la velocidad real de un esquema normal. O sea... Saldría para este lado. Esto no lo considero como un análisis más práctico. Pero bueno, esto se vería así.

**[14:43] PROFESOR:** ¿Cómo se vería? O sea, el evento real en la simulación. ¿Y por qué dibujaste ese intermedio? Eso es lo que estamos todavía en... Si los eventos son 0 porque es el choque. Y 0,1 porque... Sí, no, tenés razón. Elegimos un 0,1. Entonces los eventos son esos. ¿Por qué dibujaste el intermedio? Quiero que te queden...

**[15:17] VOS (Lucas):** Era más didáctico.

**[15:19] PROFESOR:** No, porque... Indica... Que están pasando cosas en el intermedio que no estás calculando en ningún lado. O sea, como que... Le querés dar una... Una cierta continuidad al razonamiento, pero la simulación no la tiene. Sí, sí, tenés razón. De evento a evento. Igual no está mal. Puede ser que al 0,1 segundo... Pero de nuevo, el otro podría estar... Si querés volver al caso anterior. Al que estaba el intermedio. Y en vez de 0,05 poner el 0,1. Que es lo que vos me dijiste que tenés eventos. Y al de abajo 0,2. Bueno. Esto sí es razonable. Porque es cuando vos decís que tenés eventos. ¿No?

**[16:25] VOS (Lucas):** Pero ahí no le hubiera puesto la velocidad deseada.

**[16:32] PROFESOR:** Sí. Porque... Eso que yo antes te pregunté. Si lo que estabas dibujando era la velocidad deseada o la velocidad actual de la partícula.

**[16:42] PROFESOR:** Porque... Cuando la velocidad de la partícula... Si vos le cambiás abruptamente la velocidad deseada, como...

**[16:56] VOS (Lucas):** Claro, pasar directo de esto a esto.

**[16:58] PROFESOR:** O sea, acá también hay otra cosa. No falta que digas cómo son las nuevas velocidades después del choque. Hacia dónde están apuntando. Ahí hay un dibujo, pero falta decir el criterio. O sea, lo que vos tenés para estar cambiando son velocidades deseadas. Las velocidades verdaderas no las podés cambiar. O sea, vos tenías una partícula viajando con una cierta velocidad. Sí. Le cambiás la velocidad deseada. Y la velocidad se va a ajustar a la velocidad deseada con una cierta inercia. Y va a tardar un cierto tiempo. No es que se... No es que automáticamente la velocidad de la partícula es la velocidad deseada.

**[17:54] VOS (Lucas):** Claro, diría. ¿Cómo ando?

**[17:55] PROFESOR:** Tarda un tiempo hasta que converge la velocidad de la partícula a la velocidad deseada en un esquema de Time Step Driven. Eso tarda un tiempo. Entonces, eh...

**[18:14] VOS (Lucas):** Sí, acá creo que alguna se ve. Bueno, sí, está muy pegada. Ahí tendría que armar una de... ¿Cómo vos decís?

**[18:29] PROFESOR:** Están ahí dibujadas las... No, igual, perdón, porque en el caso del Time Step Driven está claro que la velocidad deseada y la velocidad actual serían distintas. En el caso de even driven no me queda claro cómo... Si vos cambias la velocidad deseada y la velocidad se ajusta en un delta T de 0,1 puede pasar. Que todavía no coincida. Pero ahí yo no sé si vos estás calculando la velocidad a partir de la velocidad deseada o cómo estás haciendo.

**[19:12] VOS (Lucas):** ¿Cómo, perdón?

**[19:12] PROFESOR:** Claro, me tenés que decir después del choque que hay en 0,1 la velocidad que hay o sea, ¿por qué se fueron a esa posición? ¿Cómo fue la regla que dice cuál es la nueva velocidad después del choque? O sea, las partículas vienen con una cierta velocidad y chocan. ¿Cómo es la nueva velocidad después del choque? O sea, ¿por qué hay falta dibujar en la... Ah, digamos después de ese choque hubo una... entre 0 y 0,1 hubo una traslación. ¿Cómo... ¿Cuál fue la regla para... para esa traslación? ¿Cómo apuntaban las velocidades? ¿Meguamente después del choque?

**[20:09] VOS (Lucas):** Con las ecuaciones.

**[20:55] PROFESOR:** Explícamelo vos. No me des algo para leer porque no sé quién lo escribió y lo importante es que vos lo entiendas.

**[21:01] VOS (Lucas):** Sí, sí. Con las ecuaciones de colisiones se determina el próximo... la próxima posición y velocidad inicial del 0,1. No sé si hay mucho más para decir, pero...

**[21:43] PROFESOR:** Sí, hay un montón para decir. Chocan y... ¿Cómo decidís cuáles son las nuevas velocidades después del choque? Si fueran las... las pelotas de billar del... del TP3... está claro porque... ahí no... como no hay fuerzas... y solo tienen movimiento recto y uniforme... con la conservación del impulso y todo... se obtienen las nuevas velocidades. Ahora acá... ¿Cómo se determinan? ¿Qué regla estás usando para decir cuáles son las nuevas velocidades? ¿Ves ahí? Mirá. ¿Esa línea de puntos que hay entre 0 y 0,1? Bueno, esa es una velocidad que las partículas usaron para desplazarse entre 0 y 0,1. ¿De dónde salió esa velocidad? ¿Qué regla usaste para... usaron... ¿Hay compañeros tuyos hoy? Sí. Bueno, díganme entre todos qué regla usaron para decidir que esa línea de puntos que en realidad es la velocidad después del choque porque después del choque fueron a parar en 0,1 segundos a esas posiciones que están ahí dibujadas ¿Con qué regla decidieron cuál es esa velocidad? Bueno, escúcheme les hago... yo tengo toda la sensación y como les dije el otro día me puedo estar equivocando ¿no? de que ustedes le están pidiendo a la IA que dé estas respuestas pero ustedes no están entendiendo lo que está pasando y eso es lo que no puede pasar o sea, quiero ser claro con esto no puede pasar que ustedes no tengan idea de lo que está pasando entonces les sugiero una cosa para cortar radicalmente con este problema no... no usen la IA para nada porque la IA le da un código hecho y eso anda ven una imagen pero no tienen mucho insight de lo que está resolviendo la IA y eso es totalmente lo que no puede pasar y que sería un mal uso de la IA porque nos deja sin entender las cosas y sin pensar entonces dejen a un costado lo que lo que les da la IA y no sabemos qué hace y piénsenlo de cero como si no existiera la IA cómo harían para resolver este problema digamos, porque además es el problema que había dos opciones y ustedes eligieron estas por algún motivo les resultaría más familiar o a lo mejor no vieron detalles que ahora ahora sí están viendo y que ven que son más complicados pero bueno como sea piensen en papel y lápiz cómo resuelven esto o sea piensen que en el TP3 dos partículas chocaban a un cierto evento y y cómo se resolvía eso y las partículas seguían viajando con las nuevas velocidades hasta que chocaran de nuevo pero eso funciona bien para un gas que las partículas no tienen ninguna dirección hacia dónde ir ahora las partículas tienen una una velocidad deseada entonces un choque como Event Driven las mandaría a cualquier lugar distinto de sus velocidades deseadas entonces están poniendo eventos que son pasos de tiempo para recuperar la trayectoria hacia la velocidad deseada cosa que no era necesario hacer en el TP3 ¿no? queda claro por qué

**[26:09] VOS (Lucas):** entonces bueno

**[26:12] PROFESOR:** esta esta forma de de definir las velocidades después del choque lo de plantear el 0,1 está bien eso creo que lo entienden y bueno es razonable plantear un evento en un cierto tiempo para enderezar la velocidad y ese 0,1 ¿cuándo deja de de ser necesario? porque si si una vez que chocaron ahí está la la restitución lo están dibujando acá en algún momento volverían a chocar o sea cuando llega

**[26:54] VOS (Lucas):** a la velocidad deseada

**[26:55] PROFESOR:** si no sé en algún momento o suponete que no choca más no importa siguen avanzando de a 0,1 o hasta que la velocidad coincide con la velocidad deseada ahí dejan de avanzar con 0,1 y vuelven a Time Step Driven

**[27:18] VOS (Lucas):** no actualmente estamos avanzando siempre aunque esté en la velocidad deseada ¿cómo? que actualmente está avanzando siempre el 0,1 aunque ya cumpla con la velocidad deseada

**[27:31] PROFESOR:** o sea siempre siempre hasta que terminan de salir y bueno pero entonces eso ya se convirtió en un time step no es más even driven

**[27:45] VOS (Lucas):** no pero tiene un delta t muy alto 0,1 bueno pero es

**[27:50] PROFESOR:** pero es un time step lo que diferenciaría de de un time step a un even driven es ya pierde lo de even driven en el sentido que que los eventos están dados por un paso fijo entonces está bien son eventos de paso fijo que ya sería un un Time Step Driven pero además está bien el Time Step Driven con un paso chiquito resolvería las ecuaciones con el overlap de las partículas o sea que la que habría muchos time step en cada en cada choque y acá eso están sin hacerlo o sea que avanzaría qué pasa si cuando se mueven 0,1 acá porque hay pocas partículas pero bueno en la puerta por ahí está pasando en el dibujo que vos hiciste volví al dibujo qué pasa si si cuando los moviste a 0,1 ahí se superponen con otras partículas que venían de otro choque parecido al costado y alguna va a parar a una posición que se superpone con esa qué pasa en ese caso

**[29:20] VOS (Lucas):** no no entendí no entendí muy bien el caso o sea que hay otras partículas que vienen de otros choques y chocan con estas dos claro

**[29:31] PROFESOR:** así como están estas dos chocando al costadito hay otras dos chocando igual y entonces estas posiciones que en las cuales fueron a parar al 0,1 segundo son tales que hay dos partículas superpuestas

**[29:50] VOS (Lucas):** no pero eso tendría otro choque y sería otro evento

**[29:55] PROFESOR:** antes del 0,1 segundo ah está bien

**[30:03] VOS (Lucas):** entre entre esto no

**[30:06] PROFESOR:** está bien está bien ahí habría un evento

**[30:09] VOS (Lucas):** o sea que chocarían y sería otro evento

**[30:12] PROFESOR:** habría un evento anterior al 0,1 segundo entonces bueno entonces o sea antes de que cambia la velocidad esperá no la velocidad ya cambió cuando chocó cambió la velocidad y es lo que no saben

**[30:34] VOS (Lucas):** no si pero digo digo del del del steer del como lo puedo decir o sea el 0,1 va acomodando gradualmente la velocidad hasta que llegue la velocidad deseada

**[30:50] PROFESOR:** si pero bueno si hay un evento antes de eso va a tener una velocidad que todavía no es la deseada pero no va a poder hacer todo este proceso de de varios delta test de 0,1 para llegar a acomodarse porque si choca con otro va a tener que aplicarse la regla de qué pasa con la velocidad cuando choca que es la que no sabemos actualmente pero no importa ahí ahí tienen que decidir qué regla es esa

**[31:21] VOS (Lucas):** aplicaría esa regla

**[31:32] PROFESOR:** y se haría el steer a partir de esa regla perdón que decís el steer

**[31:39] VOS (Lucas):** bueno se iría gradualmente se iría gradualmente pero no

**[31:48] PROFESOR:** no entiendo la palabra te referís al a la relajación digamos

**[31:54] VOS (Lucas):** por eso

**[32:02] PROFESOR:** ese proceso de relajación sucede limpio si si no hay si las partículas no se interrumpieron después de chocar pero si antes de que se llegue a terminar el proceso de relajación hay un nuevo choque bueno empieza de nuevo el proceso ese y ese es un evento que sucede antes del 0,1 en ese sentido está bien el 0,1 este no serían los únicos eventos que hay podría haber eventos anteriores por choques bueno cuando esos choques se vuelvan muy muy frecuentes es posible que la simulación empiece a no avanzar porque hay muchos choques a delta T muy chiquitos puede pasar si pasa eso si la simulación no termina está bien es un resultado posible acá no es un resultado válido

**[33:04] VOS (Lucas):** el tiempo de ejecución queda mucho más que asumimos que es por eso que está diciendo

**[33:15] PROFESOR:** esto para cuántas partículas es 500 sí qué estamos viendo acá

**[33:27] VOS (Lucas):** el tiempo de ejecución de la aplicación en sí o sea de la simulación no de evacuación que bueno es lo que estaba diciendo que tardaba más en event driven cuando se acumulan en en el arco y hay muchas partículas pedazas hay más eventos que el delta T entonces tarda más en event driven que en time step

**[33:47] PROFESOR:** está bien ok bueno bueno acá lo que decía en el anuncio de probar con 200 a ver si si esto si el híbrido mejora a los dos otros esquemas con 500 aparentemente no claro bueno pero volviendo al anterior les digo por favor olvídense del código que les dio el chat y piensen ustedes cómo son las reglas cómo dicen bueno lo tengo que programar de cero cómo lo hago qué reglas pongo

**[34:35] COMPAÑERO:** acá estoy leyendo el código igual no sé si igualmente lo tendríamos que repensar pero para calcular la velocidad después del choque lo que se hace es se calcula el producto escalar entre la diferencia de las velocidades y el vector normal de las partículas A y B después se calcula un impulso usando un coeficiente de restitución que es una variable de entrada y después a la velocidad de A se le resta el producto entre el versor entre las dos partículas por ese impulso dividió su masa y a la velocidad de B lo mismo pero se le suma eso está bien si querés te puedo pasar la función

**[35:13] PROFESOR:** pero si ustedes lo hubieran pensado de cero hubieran hecho eso no ni lo hubieran hecho eso pensando de cero uno toma unas decisiones más fáciles más directas entonces por favor piénsenlo ustedes cómo lo hubieran hecho o por qué porque me estás dando algo que que hizo la IA y que no sabemos por qué decidió eso qué motivación tuvo estamos como tratando de explicar lo que hizo la IA que lo hizo porque lo hizo o sea tenemos que nosotros ser los que proponemos las cosas entendemos por qué las pensamos y después que la IA lo implemente o sea nos sentamos frente a la hoja de papel decimos bueno esto el problema es así asá y así cómo vamos a hacer acá bueno entonces lo resolvemos así ahora le pedimos a la IA implementar esto ya sabemos cómo es cada cosa porque si no no tenemos idea de varias decisiones que va tomando la IA porque sí como en este caso es una decisión compleja que podría estar bien qué sé yo pero si si comulgan con esa idea entiendan que es la mejor aunque sea un poco más compleja que otra porque una forma fácil de las dos partículas se chocan y durante 0,1 segundo tienen las velocidades opuestas a sus centros como lo mismo que pasa con el Contractile Particle Model o sea tienen las velocidades tal que se alejan durante 0,1 segundo perdón y después empieza

**[36:56] VOS (Lucas):** así chocarían y se irían cada una por el lado ni siquiera para allá o dependiendo de cómo chocan

**[37:13] PROFESOR:** no sé si lo más directo es porque aparte tenemos el Contractile Particle Model no es necesario ignorarlo por completo o olvidarse que existe que su regla una vez cuando chocan salen con las flechas horizontales que dibujaste ahí

**[37:30] VOS (Lucas):** o sea

**[37:32] PROFESOR:** durante un durante un delta T que acá estamos haciendo un delta T de 0,1 para eso es lo primero que a uno se le ocurre es fácil no hay que hacer toda esa cuenta que me acaban de decir porque es arbitrario porque no necesita está bien si ustedes quieren que las flechas que dibujaste en diagonal hacia abajo es de alguna forma un promedio entre esa dirección y la dirección de la velocidad deseada puede ser también o ahí si quiere dibujar la velocidad deseada

**[38:10] VOS (Lucas):** suponiendo que para abajo ahí

**[38:13] PROFESOR:** y entonces calcularías la la suma de esos dos vectores que te darían en diagonal

**[38:22] VOS (Lucas):** bueno

**[38:24] PROFESOR:** ves ahí esas celestes serían lo que dibujaste a la derecha entonces ante mi pregunta de dónde salió eso me puede decir que es el vector suma y después normalizado de de esta regla de alejar los de alejar las partículas parecido al Contractile Particle Model más la velocidad deseada que apunta hacia el target final entonces saco ese promedio para que no se alejen tan irrazonablemente pero bueno esta decisión me la podés decir pero ves que esto es una cosa que se entiende rápido no ves todo lo otro ahora si todo lo otro fuera necesario porque quieren además tratar de conservar cosas físicas en este choque o que sea fiel a algo bueno está bien pero entiéndanlo porque lo quieren hacer así entonces a esto me refiero si lo piensan en papel uno pensaría algo con este grado de simplicidad y después lo implementa y ve que pasa si ustedes están de acuerdo en que sea tan complicado como está escrito bueno díganme por qué tiene que ser así y complicado entiéndanlo perfectamente por qué y cómo digamos se calcula eso o sea esta regla que es lo que decían en el anuncio tiene que estar bien explicada en la presentación en la parte de introducción no solo en la diapositiva 10 o sea la diapositiva 10 no explica esto

**[40:11] PROFESOR:** que es una animación que si fueran dos partículas solas y mostrase todos estos vectores intermedios cómo se calculan y qué sé yo que se entienda lo explicaría pero tendría que poner todas esas ecuaciones que me leyeron recién pero bueno pero me entienden que que eso es lo que nos está haciendo pasar un momento de mayor trabajo digamos por decirlo o sea que así como está faster y slower podemos decir que por querer facilitar las cosas usando la IA terminamos trabajando más que si no la hubiéramos usado es una especie de faster y slower con la IA

**[41:08] VOS (Lucas):** sí

**[41:10] COMPAÑERO:** es verdad es verdad

**[41:11] PROFESOR:** entonces bueno eso es a lo que nos venimos enfrentando estas últimas prácticas en las cuales ustedes me muestran una presentación y todas sus respuestas radican en lo que está en la presentación pero entonces ustedes no están entendiendo bien lo que está pasando así que bueno este punto que es un punto que hay que tiene que estar bien explicado con este grado de entendimiento que estamos diciendo ahora en estos dibujos piénsenlo si lo pueden plantear más fácil le piden al código que lo haga así o sea el código lo pueden hacer ustedes o lo hacen con la IA pero bueno ya saben bien lo que está haciendo verifican que hace si se lo piden a la IA verifican que hace lo que ustedes le están pidiendo entonces para eso está bueno ver algo como lo de la diapositiva 10 donde dibujan las flechas de velocidades deseadas o sea dirección al target velocidad actual calculada entonces bueno esto igual todavía tiene cosas para terminar de definir porque cuando les cambian la velocidad deseada o les cambian acá cuando están en este dibujo de la izquierda cuando están las dos flechas negras esas dos flechas negras son como serían dos velocidades deseadas que por ese tiempo están apuntando así o como en instante

**[42:55] COMPAÑERO:** principal

**[42:55] PROFESOR:** claro o sea esto sería como que las velocidades deseadas por momentos cambian o sea ahí cambiarían durante un delta T los movería para alejarlas por ahí su velocidad verdadera no termina siendo justo la velocidad deseada capaz que si la velocidad deseada es la negra como la partícula antes tenía otra velocidad ahí tienen que decidir la velocidad actual como se acomoda a la velocidad deseada o sea si fuera el caso de time step eso se va dando naturalmente en cada pasito la velocidad actual se va acercando a la velocidad deseada

**[43:41] COMPAÑERO:** ahora acá

**[43:45] PROFESOR:** hay que ver que pasa si si en 0,1 todavía no se había acercado entonces quedará en un lugar intermedio bueno hay que ver cómo cómo se resuelven estos detalles entonces bueno es lo que los invito a que lo piensen en papel ustedes y después lo implementen y cuando lo implementan sea quien sea que lo implementa porque aunque lo implementen ustedes después está bueno chequear que la implementación hace lo que habían pensado hoy en la teoría y eso se logra haciendo dos partículas situaciones fáciles como esta que estamos dibujando acá en el papel y graficando esas flechas entonces viendo que las flechas están haciendo lo que uno quería bueno después de hacer las diapos que veo que tienen bastantes palabras traten de limpiarlas un poco esto ya me parece lo habíamos hablado

**[44:52] VOS (Lucas):** si si totalmente

**[44:53] PROFESOR:** también eso en función de lo que entendemos pongamos las cosas que son las importantes bueno buenísimo estamos avanzando vamos vamos que es importante que usted como lo dijimos otras veces que la la guía funcione debajo nuestra a nuestras órdenes y no y no que no que tenga de alguna forma un control que nosotros no sepamos que está pasando bueno

**[45:34] VOS (Lucas):** buenísimo bueno muchísimas gracias

**[45:36] PROFESOR:** dale a ustedes bueno

**[45:47] Otro grupo (Grupo 4) – ya no es tu consulta:** profe cómo va qué tal sí bueno justo nuestro grupo era una consulta más va por mi lado de TP4 que lo tenemos que recuperar

**[45:56] Otro grupo (Grupo 4) – ya no es tu consulta:** ¿ustedes son grupo 4? sí sí

**[45:59] Otro grupo (Grupo 4) – ya no es tu consulta:** nada era particularmente esto del gráfico porque si tenemos mal esta parte de esto vamos a hacer todo lo demás era el problema esto del escalonado que bueno corregimos lo que nos habías dicho de que despejábamos claramente la posición de forma implícita en la velocidad que fue lo que sugirió la guía estaba mal y nada y después de correr de vuelta con el verlet corregido nos dio yo ahí lo estaba comparando entre los dos o sea se redujo bastante el escalonado pero como que tiene el ¿cómo se dice? esta tendencia a pasos pequeños la posición


_(Desde ~45:47 empieza la consulta de otro grupo; el audio posterior es corto y poco confiable, se omite.)_