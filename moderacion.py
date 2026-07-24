import re
import unicodedata

# ----------------------------------------------------------------- capa 1
# Raíces: se bloquea cualquier palabra que EMPIECE con ellas.
# Elegidas para no chocar con palabras normales (no "verg" porque
# bloquearía "vergüenza"; no "mens" porque bloquearía "mensaje";
# no "anal" porque bloquearía "análisis"; no "coj" porque bloquearía
# "cojín"). Los términos cortos o ambiguos van en EXACTAS.
RAICES = [
    # ---------------------------------------------- español: núcleo
    "put", "pendej", "pndj", "ching", "chng", "chingad", "chingon",
    "verga", "vergaz", "verguiz", "vrga", "vergud", "vergot",
    "mierd", "miard", "merd", "mrd", "mierc",
    "cabron", "cbron", "cbrn", "cabroniz",
    "culer", "culo", "culear", "culeo", "culiar", "culiand", "culiad",
    "culiao", "cliao", "reculi", "culicag", "culon", "culaz",
    "caga", "cago", "cague", "cagad", "cagon", "cagast", "cagarr",
    "mamad", "mamon", "mames", "mamast", "mamahuev", "mamaverg",
    "mamapij", "mamador", "mamaguev", "mamawev", "mamert",
    "chupam", "chupal", "chupap", "chupaverg", "chupapij", "chupapoll",
    "chupaguev", "chupahuev", "chupamel", "chupaculo", "chupapit",
    "lameculo", "lameverg", "lamehuev", "lamebot", "lamesuel",
    "comeverg", "comemierd", "comepij", "comerab", "comeculo",
    "tragaleche", "tragasable", "tragaverg",
    "joto", "jotol", "jotit", "jotaz", "maric", "marik",
    "pito", "pitud", "pitot", "pija", "pijud", "pijaz",
    "panoch", "polla", "pollon", "pollud", "ojete", "ojet",
    "nalg", "nalgon", "nalgaz",
    "huevon", "guevon", "webon", "wevon", "weon", "gueon", "hueon",
    "ueon", "aweon", "awebon", "awevon", "huevaz", "guevaz", "webiad",
    "wevad", "webi", "hueviad",
    "puñet", "punet", "puñal", "punal", "puñaler",
    "piruj", "prostitut", "ramera", "meretriz", "furcia", "buscon",
    "gilipoll", "gilipuert", "gilipuch",
    "bolud", "pelotud", "conchud", "conchetu", "conchesu", "chuchetu",
    "malparid", "malnacid", "desgraciad", "engendr", "aborton",
    "hijueput", "hijodeput", "hijaput", "hijoput", "hijadeput",
    "hijuemadr", "hijuemil", "hijueperr", "hijuemich", "jueput",
    "juemadr", "juepuch", "hidep", "hdep",
    "gonorre", "malparir", "marran", "cochambr",
    "carajo", "carrajo", "carajit",
    "joder", "jodid", "jodet", "jodel", "jodont", "jodanc",
    "coño", "coñaz", "coñeo", "cojon", "cojud", "cojonud",
    "carech", "carehuev", "carepij", "careverg", "careraj", "carepal",
    "chimb", "pichul", "pinch", "wil", "guil", "verguer",
    "madraz", "madread", "madrear", "putiz", "cerd", "cochin",
    "sorete", "soret", "arrech", "cachond", "salid",
    "pajer", "pajud", "pajaz", "pajill", "masturb",
    "pedorr", "cornud", "cabrear", "encabron",
    "chingaqued", "chingatumadr", "chingasumadr",
    "vergacion", "verguearl", "verguetazo",
    "mamerta", "mamalon", "mamavergaz",
    "culiflor", "culisuci", "culopronto",
    # ------------------------------------- español: insultos generales
    "estupid", "imbecil", "idiot", "tarad", "babos", "zopenc",
    "mongol", "retrasad", "subnormal", "machorr", "lenchon", "invertid",
    "patarajad", "mugros", "zarrapastros", "escori",
    "cretin", "mentecat", "majader", "papanat", "pazguat", "zoquet",
    "panfil", "bobalic", "abombad", "atarantad", "alelad",
    "pelmaz", "gañan", "ganan", "patan", "cafre", "energumen",
    "mequetrefe", "palurd", "paleto", "cateto", "garrul", "cerril",
    "zafied", "cenutri", "berzot", "melon", "merluz", "besugo",
    "chusm", "gentuz", "populach", "plebey", "viller", "flait",
    "arrastrad", "rastrer", "ruin", "vividor", "sanguijuel",
    "sinverguenz", "caradur", "jetont", "cinicaz",
    "mamarrach", "adefesi", "esperpent", "callej",
    "asquer", "repugnant", "nauseabund", "pestilent", "apestos",
    "inmund", "fetid", "hedion", "putrefact", "podrid",
    "malfoll", "malcog", "amargad",
    "tontuel", "tontorr", "estupidez", "burrad", "animalad",
    "salvajad", "barbarid", "atrocid",
    "inutil", "inservibl", "incompetent", "ineptit", "inept",
    "fracasad", "perdedor", "mediocr", "pusilanim", "cobard",
    "rastrojo", "escombr", "desperdici",
    # -------------------------------- español: LGBTIQ+ (insultos/slurs)
    "manflor", "mayat", "sidos", "marimach", "tortiller", "areper",
    "bujarr", "julandr", "mariposon", "colipat", "cochon", "cochonit",
    "travuk", "travelo", "traveco", "travest", "afeminad", "amanerad",
    "amariconad", "amaricad", "sodomit", "invertidaz",
    "chupapoll", "chupabolas", "rompeculo", "dalecul",
    "mariquit", "maricuel", "marimarich", "machirul",
    "camionerazo", "sopleta", "sopla nucas",
    # ------------------------------ español: racistas / xenófobos
    "sudak", "sudac", "negrat", "negrac", "negrer", "prietit",
    "indi ot", "indiaz", "cholaz", "chulaz",
    "veneq", "venec", "peruc", "bolit", "boliv iano",
    "panchit", "morac", "morunch", "gitanaz", "gitanad",
    "cabecit", "villamiseri", "espaldamojad",
    "chinit", "chinesc", "amarill os",
    "monigot", "simiesc", "primitiv",
    # ------------------------------ español: capacitistas / edadistas
    "espastic", "tullid", "lisiad", "invalid ez", "deficientement",
    "mongolit", "retard ad", "subnormalid", "anormalid",
    "viejit ux", "vejestori", "carcamal", "ruco",
    "gordinfl", "ballenat", "focaz", "cerdaz",
    # ------------------------------ español: amenazas (raíz verbal)
    "matarl", "matenl", "matare", "asesinar", "asesinat", "degoll",
    "descuartiz", "apuñal", "apunal", "acuchill", "balac", "fusil",
    "lynch", "linchar", "linchamient", "ahorc", "estrangul",
    "incinerar", "calcin", "gasear", "gaseal", "exterminar",
    "aniquilar", "masacr", "carniceri", "descabez",
    "secuestrar", "torturar", "mutilar", "castrar", "esterilizar",
    "violarl", "violador", "violacion", "abusador", "abusiv",
    # ---------------------------------------------- inglés: núcleo
    "fuck", "fuk", "fck", "fucc", "fuq", "phuck", "fugg", "fukk",
    "shit", "shyt", "shite", "shitt",
    "bitch", "biatch", "bytch", "btch", "biotch", "beeyotch",
    "asshole", "ashole", "arsehole", "asshat", "assclown", "asswipe",
    "assface", "asslick", "asskiss",
    "motherfuck", "mothafuck", "muthafuck", "mofuck",
    "cunt", "nigg", "nigr", "fagg", "whore", "slut", "sluts",
    "retard", "dumbass", "dumbfuck", "dumbshit", "jackass",
    "douche", "wank", "twat", "pussy", "bastard", "dickhead",
    "dickface", "dicksuck", "dickwad", "dickbag",
    "cocksuck", "cockhead", "cockwomble",
    "prick", "bollock", "bugger", "tosser", "knobhead", "knobjock",
    "minger", "slag", "skank", "hooker", "hussy", "harlot", "bimbo",
    "jerkoff", "jackoff", "circlejerk", "handjob", "blowjob",
    "rimjob", "dildo", "boner", "horny", "jizz", "nutsack",
    "ballsack", "titty", "clitor", "cumshot", "creampie",
    "gangbang", "deepthroat", "fisting", "bukkake", "porn",
    "wanker", "shithead", "shitbag", "shitface", "shitstain",
    "scumbag", "sleazeb", "trashbag",
    "stupid", "moron", "idioti", "dumb", "loser", "cretinous",
    "imbecilic", "braindead", "brainless", "nitwit", "halfwit",
    "dimwit", "numbskull", "knucklehead", "blockhead", "meathead",
    "piss", "pissed", "damn", "goddam", "bloodyhell",
    "bollocking", "arsewipe", "arseface",
    # --------------------------------------- inglés: odio / slurs
    "beaner", "wetback", "towelhead", "raghead", "jigaboo",
    "zipperhead", "redskin", "injun", "squaw", "gyppo", "pikey",
    "kaffir", "chinaman", "halfbreed", "mudperson",
    "tranny", "shemale", "dyke", "poofter", "batty boy",
    "sandnig", "camel jockey", "goatfucker",
    "whitepower", "whitepride", "whitegenocid",
    "pedophil", "pedofil", "pederast", "rapist", "molest",
    "incest", "bestialit", "zoophil", "necrophil",
    "supremacis", "skinhead", "neonazi", "hitlerite",
    # -------------------------------- portugués (frecuente en LatAm)
    "caralh", "porra", "buceta", "viad", "boiol", "baitol",
    "otari", "babac", "bosta", "cuzao", "cuzin", "arrombad",
    "desgracad", "corn o", "vadia", "piroca", "punhet",
    "vagabund", "safad", "escrot", "fdp", "krai",
    # -------------------- evasiones sin vocales / deformaciones comunes
    "wbn", "hjdp", "ptmr", "ctmr", "csmr", "vrgs", "chngd",
    "pndjs", "cbrns", "mrds", "kul iao", "qliad",
    "pvt", "pt0", "prr", "zrra", "gnrr",
    # ------------------------------ español: insultos (ampliación 2)
    "alcahuet", "arrastrapanz", "atolondrad", "atorrant", "bagart",
    "bandarr", "bellac", "bocaflo", "bocasuci", "botarat", "bribon",
    "buhoner", "calanchin", "calientahuev", "calzonaz", "canall",
    "canalh", "capull", "caraculo", "caraverg", "carapapa",
    "cascarrabi", "chafalot", "chapuc", "charlatan", "chismos",
    "cizañ", "cizan", "cochambros", "cretinism",
    "cuernud", "degollad", "delator", "depravad",
    "desalmad", "descarad", "descerebr", "desleal", "desmadr",
    "despot", "desquiciad", "difamador", "embuster", "embruter",
    "emputad", "enajenad", "enclenqu", "envidios", "escupitaj",
    "estafad", "estupidiz", "fanfarron", "fantoch", "farsant",
    "felon", "fullero", "gandul", "gorron", "granuj", "groser",
    "hampon", "haragan", "hipocrit", "holgazan", "huevea",
    "impresentabl", "indecent", "indeseabl", "infam", "ingrat",
    "insensat", "insolent", "insufribl", "irrespetuos", "jodiend",
    "ladill", "lagarton", "lambiscon", "lambon", "lameplat",
    "libertin", "malandrin", "malefic", "malevol", "maloliente",
    "malasangr", "malaleche", "manipulador", "manosead", "mañoso",
    "manoso", "marimandon", "matasiete", "mendrug", "miserabl",
    "mojigat", "morbos", "mugrient", "nefari", "obscen",
    "pandiller", "pedante", "pelafustan", "pelagat", "pelanas",
    "pelaverg", "pelabol", "pendencier", "perjur", "pervers",
    "petulant", "pillastre", "porquer", "prepotent", "puerc",
    "rufian", "sadic", "salvajism", "sanguinari", "saqueador",
    "sarnos", "timador", "traicioner", "trampos", "truhan",
    "truñ", "usurer", "vandal", "vejador", "verdug",
    "zorron", "zorrup", "zurull", "roñic", "ronic",
    "cabezahuec", "cabezabuec", "chupasangr", "sacoverg",
    "cagatint", "cagatorr", "cagapalo", "cagaprisa", "cagalastim",
    "meapil", "meacol", "muertohambr", "mierdec", "mierdol",
    # ------------------------------ inglés: ampliación 2
    "arsehat", "assmunch", "ballbag", "bellend", "bint", "bollix",
    "brownnos", "buttfuck", "butthole", "buttmunch", "chode",
    "clusterfuck", "cockblock", "cocknose", "crackwhore",
    "cumbucket", "cumdump", "cumguzzl", "dickbrain", "dickcheese",
    "dipshit", "fatass", "fatso", "fatty", "felch", "fingerbang",
    "gobshite", "hardon", "hoebag", "horseshit", "jackhole",
    "knobend", "lardass", "manwhore", "pissflap",
    "porker", "punkass", "queef", "ratfuck", "shitcan",
    "shithole", "shitlord", "skeet", "smegma", "spooge", "spunk",
    "turd", "twatwaffle", "wigger", "groomer", "libtard",
    "snowflake", "eurotrash", "trailertrash", "whitetrash",
    "cottonpick", "wanksta", "shitgibbon", "cockgoblin",
    "fucknugget", "fuckstick", "assgoblin", "dickweed",
    "titfuck", "slutshame", "whoremong", "manlet", "beta cuck",
    # ------------------------------ portugués: ampliación 2
    "fodas", "fodid", "fodase", "putaria", "raparig", "safadez",
    "cuzud", "bundud", "chupador", "punhetei", "rabud",
    "corninh", "otarion", "babaquic", "bostinh", "escrotid",
]

# ----------------------------------------------------------------- capa 2
# Palabras exactas (límite de palabra + plural/diminutivo), para términos
# que como prefijo darían falsos positivos ("menso" vs "mensaje",
# "teta" vs "tétanos", "ass" vs "assembly", "anal" vs "análisis").
EXACTAS = [
    # ------------------------------------------ español: sexual / vulgar
    "menso", "mensa", "naco", "naca", "zorra", "perra", "golfa",
    "teta", "chichi", "pene", "semen", "vagina", "verija", "chocho",
    "culito", "tortillera", "sudaca", "nazi", "hitler", "feminazi",
    "pedorro", "pedorra", "cornudo", "cornuda", "prosti",
    "picha", "pinga", "chota", "orto", "forro", "gil", "gila",
    "chucha", "papo", "cuca", "cuquita",
    "raja", "rajada", "bolas", "huevos", "guevos", "webos",
    "pelotas", "cojones", "chichis", "chiche", "nalga", "poto",
    "ano", "recto", "escroto", "testiculo", "prepucio",
    "paja", "pajita", "chaqueta", "manuela",
    "leche", "lechita", "corrida", "acabada",
    "puto", "puta", "putito", "putita", "pta", "ptas", "pvta",
    "vrg", "verg", "vrgn", "hp", "hpta", "mrd", "csm", "ctm",
    "ql", "qla", "qlo", "qliao", "qliada", "weona", "weones",
    # ------------------------------------------ español: insultos leves
    "tonto", "tonta", "bobo", "boba", "tarugo", "zonzo", "sonso",
    "lelo", "zoquete", "panfilo", "pazguato", "papanatas",
    "mentecato", "majadero", "cretino", "cafre", "patan", "ganan",
    "pelmazo", "palurdo", "paleto", "cateto", "garrulo", "zafio",
    "mamerto", "guarro", "guarra", "cerdo", "cerda", "marrano",
    "rata", "ratero", "chorro", "lacra", "escoria", "morralla",
    "nefasto", "penoso", "lamentable", "patetico", "ridiculo",
    "fracaso", "estorbo", "lastre", "parasito", "sanguijuela",
    # ------------------------------------------ español: slurs cortos
    "trolo", "trola", "trava", "maraco", "fleto", "sarasa", "playo",
    "hueco", "cundango", "pargo", "loca", "locaza", "bicha",
    "moraco", "veneco", "negrata", "negraco", "panchito", "cholo",
    "prieto", "guero", "gringo", "yanqui", "franchute", "gabacho",
    "guiri", "polaco", "sudamericano", "espalda mojada",
    # ------------------------------------------ inglés: vulgar
    "dick", "cock", "ass", "arse", "fag", "hoe", "tit", "tits",
    "bullshit", "boobs", "wtf", "stfu", "kys", "hdp", "ptm", "ctm",
    "csm", "alv", "vlv", "mms", "nmms", "gtfo", "milf", "simp",
    "anal", "rape", "cuck", "cucks", "incel", "thot", "mofo",
    "dilf", "nude", "nudes", "xxx", "pron", "kms", "smd", "ffs",
    "dafuq", "af", "bs", "nsfw", "hentai", "smut",
    "balls", "nuts", "wang", "schlong", "knob", "shag", "bang",
    "hump", "screw", "slutty", "hoes", "thots",
    # ------------------------------------------ inglés: slurs cortos
    "chink", "gook", "kike", "spic", "wop", "dago", "coon",
    "paki", "abo", "honky", "chav", "nonce", "yid", "zog",
    "shylock", "hymie", "heeb", "gyp", "nig", "negro", "coloured",
    "spaz", "spastic", "cripple", "mongoloid", "midget",
    "gimp", "psycho", "schizo", "lunatic", "nutjob", "wacko",
    "libtard", "fucktard", "dumbo", "wanksta",
    "femoid", "roastie", "coomer", "normie", "cuckold",
    "1488", "kkk", "wpww", "rahowa",
    # ------------------------------------------ ampliación 2: español
    "cu", "veado", "follar", "folla", "follo", "follada", "follame",
    "fundillo", "fondillo", "traste", "sieso", "culamen",
    "zorron", "zorrupia", "pucha", "putero", "putona",
    "chichona", "cachonda", "pajero", "pajera", "pajillero",
    "gonorreo", "carechimba", "malparida",
    "guaripola", "sopenco", "sopenca", "mameluco",
    "pendanga", "pendon", "pichicorto", "pirobo", "piroba",
    "gamin", "ñero", "nero", "chirris", "mamahuevo", "mamaguevo",
    "cachaco", "guacho", "guaricha", "jodon", "jodona",
    "lambe", "lambon", "lambona", "soplon", "gafo", "guebon",
    "carajito", "carajita", "mamalon", "mamalona",
    # ------------------------------------------ ampliación 2: inglés
    "clit", "fap", "fapping", "jugs", "wanky", "twatty",
    "pajeet", "polack", "guido", "greaseball", "gyppy",
    "gweilo", "whitey", "limey", "kraut", "wigga", "negroid",
    "mongy", "window licker", "sped", "sperg",
    "manwhore", "slut shamer", "boomer", "zoomer", "npc",
    "shitpost", "edgelord", "troll", "trolls", "flamer",
    "bootlicker", "shill", "grifter", "clout chaser",
    "degen", "sicko", "creep", "creeper", "perv", "pervo",
    "stalker", "predator", "groomers", "kiddy fiddler",
]

# Frases completas (subcadena sobre el texto normalizado).
FRASES = [
    # ------------------------------------------ español: insultos madre
    "hijo de puta", "hija de puta", "hijos de puta", "hijas de puta",
    "hijo de tu", "hija de tu", "hijo de la gran", "hija de la gran",
    "hijo de mil", "hijo de perra", "hija de perra",
    "chinga tu madre", "chingas a tu madre", "chingada madre",
    "chinga a tu madre", "chingue su madre", "chinguen a su madre",
    "puta madre", "puta que te pario", "la puta que te pario",
    "madre que te", "madre que los", "mecagoentumadre",
    "me cago en tu madre", "me cago en tus muertos",
    "me cago en la leche", "me cago en dios", "me cago en todo",
    "a la verga", "vales verga", "vete a la verga", "vayanse a la verga",
    "me la pelas", "me la pelan", "me la suda", "me la suda todo",
    "me la mamas", "me la maman", "chupame la", "chupenme la",
    "mamame la", "mamenme la", "come mierda", "comemierda",
    "concha de tu madre", "conchetumare", "conchetumadre",
    "conchesumadre", "la concha de", "la concha de tu",
    "chucha tu madre", "chuchatumadre", "ctm weon",
    "no mames", "no manches guey", "que te den", "que te jodan",
    "que se joda", "que se jodan", "vete a joder", "andate a joder",
    "vete al carajo", "vete a la chingada", "a la chingada",
    "vete a la mierda", "andate a la mierda", "vete a cagar",
    "andate a cagar", "vete a freir esparragos",
    "que te folle un pez", "que te parta un rayo",
    "hasta la madre", "de la verga", "un asco de",
    # ------------------------------------------ español: amenazas
    "muerte a", "maten a", "matenlos", "matenlas", "hay que matar",
    "voy a matar", "te voy a matar", "los voy a matar", "te mato",
    "los mato", "te voy a violar", "te voy a partir", "te parto la cara",
    "te rompo la cara", "te reviento", "te voy a reventar",
    "te voy a quemar", "te voy a golpear", "te voy a buscar",
    "te vamos a encontrar", "se donde vives", "se donde estudias",
    "cuidate la espalda", "estas muerto", "estas muerta",
    "eres hombre muerto", "no vas a llegar a", "te queda poco",
    "te voy a hacer pedazos", "te voy a desaparecer",
    "voy a ir por ti", "vamos por ti", "te vamos a linchar",
    "hay que lincharlos", "hay que quemarlos", "hay que colgarlos",
    "al paredon", "a la horca", "que los cuelguen",
    # ------------------------------------- español: incitación suicidio
    "ojala te mueras", "ojala se mueran", "ojala te maten",
    "ojala te violen", "ojala te atropellen", "ojala te de algo",
    "deberias morir", "deberian morir", "deberias matarte",
    "matate", "mata te", "suicidate", "quitate la vida",
    "cortate las venas", "tomate un cloro", "tomate un veneno",
    "tirate de un puente", "aventate de un puente",
    "muerete", "muerete ya", "mejor muerete", "pudrete",
    "pudrete en el infierno", "vete al infierno", "arde en el infierno",
    "nadie te quiere", "nadie te va a extrañar", "a nadie le importas",
    "el mundo estaria mejor sin ti", "sobras en este mundo",
    "deja de existir", "desaparece de este mundo",
    "haznos un favor y", "hazle un favor al mundo",
    "no sirves para nada", "eres un error",
    # --------------------------------------- español: odio identitario
    "no son humanos", "no son personas", "no es persona",
    "son animales", "como animales", "son una plaga",
    "son un cancer", "es un cancer", "son una enfermedad",
    "estan enfermos", "son enfermos", "son antinaturales",
    "contra natura", "raza superior", "raza inferior", "sangre pura",
    "limpieza etnica", "solucion final", "camara de gas",
    "camaras de gas", "a los hornos", "faltaron hornos",
    "falto hitler", "hitler tenia razon", "deberian gasearlos",
    "gaseenlos", "heil hitler", "sieg heil", "poder blanco",
    "supremacia blanca", "orgullo blanco", "ku klux",
    "gran reemplazo", "sangre y suelo", "catorce palabras",
    "volver a su pais", "regresen a su pais", "vuelvan a su pais",
    "fuera de mi pais", "fuera de aqui", "que se larguen",
    "no los queremos aqui", "no pertenecen aqui",
    "vienen a robar", "vienen a quitarnos", "nos quitan el trabajo",
    "quitan trabajos", "roban trabajos", "viven de nuestros impuestos",
    "deberian estar en jaulas", "hay que deportarlos",
    "hay que esterilizarlos", "no deberian tener hijos",
    "no deberian reproducirse", "no deberian votar",
    "no deberian existir", "no merecen vivir", "no merecen derechos",
    "no tienen derechos", "deberian desaparecer",
    "indio pata rajada", "chino cochino", "espaldas mojadas",
    # ------------------------------------------ inglés: insultos
    "kill yourself", "go kill", "eat shit", "eat a dick",
    "suck a dick", "suck my", "blow me", "choke on",
    "fuck you", "fuck off", "fuck yourself", "go fuck",
    "son of a bitch", "piece of shit", "piece of trash",
    "waste of oxygen", "waste of space", "waste of air",
    "shut the fuck up", "what the fuck", "get the fuck",
    "kiss my ass", "up your ass", "shove it up",
    # ------------------------------------------ inglés: amenazas
    "i will kill you", "im going to kill you", "i will find you",
    "i know where you live", "watch your back", "you are dead",
    "youre dead", "i will rape you", "ill rape you",
    "you should die", "you deserve to die", "hope you die",
    "neck yourself", "rope yourself", "end yourself",
    "drink bleach", "slit your wrists", "hang yourself",
    "jump off a bridge", "nobody loves you",
    "the world would be better without", "burn in hell",
    "go to hell", "rot in hell",
    # ------------------------------------------ inglés: odio
    "kill all", "death to", "hang them", "string them up",
    "gas them", "gas the jews", "white power", "white pride",
    "final solution", "great replacement", "blood and soil",
    "go back to your country", "get out of my country",
    "they dont belong", "they do not belong", "subhuman scum",
    "master race", "racial purity", "ethnic cleansing",
    "tar baby", "porch monkey", "slant eye", "sand nigger",
    "muerto de hambre", "muertos de hambre",
    # ------------------------------ ampliación 2: español (insultos)
    "chinga tu puta madre", "chingas a tu puta madre",
    "tu puta madre", "tu madre es", "tu madre la", "reputa madre",
    "la reputa madre", "la puta madre", "la re puta",
    "la concha de la lora", "la concha de tu hermana",
    "andate a la concha", "anda a la concha", "hijo de re mil",
    "forro de mierda", "pedazo de mierda", "pedazo de idiota",
    "pedazo de imbecil", "pedazo de animal", "pedazo de bestia",
    "cara de culo", "cara de verga", "cara de nalga",
    "cara de rata", "cara de perro", "cara de estupido",
    "no vales nada", "no vales verga", "vales pura verga",
    "vales madre", "vales sombrilla", "me vale verga",
    "me vale madre", "me vale sombrilla", "chupame un huevo",
    "chupame la pija", "chupame el pito", "mamame la verga",
    "chupenme la verga", "andate a la mierda", "tomatelas",
    "que te folle", "que te coja", "que te pisen",
    "que te muerdas", "mala leche", "cara de pocos amigos",
    "chinga tu vida", "chinga a toda tu familia",
    # ------------------------------ ampliación 2: español (autolesión)
    "ojala te pase algo", "ojala te pudras", "ojala te enfermes",
    "muerete de una vez", "tirate a un pozo", "comete un cable",
    "dejate de existir", "no mereces vivir", "no mereces nada",
    "el mundo te odia", "todos te odian", "nadie te extrañaria",
    "hubiera sido mejor que no nacieras", "no debiste nacer",
    "eres un estorbo para todos", "solo das lastima",
    # ------------------------------ ampliación 2: español (odio)
    "hay que exterminar", "hay que erradicar", "hay que eliminarlos",
    "hay que echarlos", "hay que encerrarlos", "hay que marcarlos",
    "hay que separarlos", "hay que humillarlos",
    "que los echen", "que los deporten", "que los maten",
    "que los quemen", "que se pudran", "que ardan",
    "al horno con", "a la hoguera", "muerte a los", "fuera los",
    "abajo los", "que ardan en el infierno", "hijos de satanas",
    "adoradores del demonio", "los infieles deben",
    "enfermos mentales", "hay que curarlos", "terapia de conversion",
    "no son familia", "no deberian adoptar", "no deberian criar",
    "corrompen a los niños", "adoctrinan a los niños",
    "vuelve a la cocina", "el lugar de la mujer",
    "las mujeres no sirven", "por eso te pegan",
    "calladita te ves mejor", "por algo le pegan",
    "cerdo asqueroso", "vaca gorda", "ballena gorda",
    "foca gorda", "gorda asquerosa", "gordo asqueroso",
    "raza maldita", "sangre sucia", "gente de segunda",
    "ciudadanos de segunda", "no son de aqui",
    "que se queden en su pais", "aqui no caben",
    "sobran en este pais", "estorban en este pais",
    # ------------------------------ ampliación 2: inglés
    "shut up bitch", "dumb bitch", "stupid bitch", "crazy bitch",
    "fucking idiot", "fucking moron", "fucking retard",
    "fucking loser", "you retard", "you idiot", "you moron",
    "go die", "just die", "end it all", "off yourself", "an hero",
    "do the world a favor", "nobody would miss you",
    "should have been aborted", "your parents hate you",
    "cut yourself", "kill em all", "kill them all",
    "burn them all", "death to all", "gas all",
    "make me a sandwich", "get back to the kitchen",
    "women belong in", "you people", "your kind",
    "go back where you came from", "we dont want you here",
    "this is our country", "not welcome here",
    "curry muncher", "ching chong", "uncle tom", "house slave",
    "no whites allowed", "whites only", "blacks only",
    "i hope you die", "i hope they kill you", "someone should shoot",
    "you deserve to be raped", "you should be gassed",
    "hitler was right", "six million wasnt enough",
]

# ----------------------------------------------------------------- capa 3
# Discurso de odio por co-ocurrencia: GRUPO protegido + expresión
# DENIGRANTE en el mismo mensaje.
GRUPOS = [
    # ------------------------------------------------ religión / etnia
    "judio", "judia", "hebreo", "sionista", "israeli", "palestino",
    "musulman", "islamico", "islam", "moro", "arabe", "turco",
    "persa", "irani", "iraqui", "afgano", "sirio", "libanes",
    "cristiano", "catolico", "evangelico", "protestante", "mormon",
    "testigo de jehova", "ateo", "atea", "agnostico", "budista",
    "hindu", "sij", "santero", "brujo", "bruja", "pagano",
    "gitano", "gitana", "romani", "judaismo", "sinagoga", "mezquita",
    # ------------------------------------------------ raza / color
    "negro", "negra", "afro", "afrodescendiente", "moreno", "morena",
    "blanco", "blanca", "prieto", "prieta", "guero", "guera",
    "mulato", "mulata", "mestizo", "mestiza", "criollo", "albino",
    "indigena", "indio", "india", "originario", "aborigen",
    "campesino", "cholo", "chola", "cholito",
    # ------------------------------------------------ nacionalidad
    "chino", "china", "japones", "japonesa", "coreano", "coreana",
    "vietnamita", "filipino", "hindues", "paquistani", "nepali",
    "gringo", "gringa", "yanqui", "estadounidense", "canadiense",
    "mexicano", "mexicana", "guatemalteco", "salvadoreño",
    "hondureño", "nicaraguense", "costarricense", "panameño",
    "cubano", "cubana", "dominicano", "haitiano", "puertorriqueño",
    "colombiano", "venezolano", "ecuatoriano", "peruano",
    "boliviano", "chileno", "argentino", "uruguayo", "paraguayo",
    "brasileño", "brasilero", "español", "gallego", "catalan",
    "vasco", "frances", "aleman", "italiano", "portugues",
    "ruso", "ucraniano", "polaco", "rumano", "africano", "nigeriano",
    "marroqui", "argelino", "egipcio", "etiope", "senegales",
    "latino", "latina", "latinoamericano", "hispano", "sudamericano",
    "centroamericano", "caribeño", "extranjero", "extranjera",
    "migrante", "inmigrante", "emigrante", "refugiado", "refugiada",
    "deportado", "indocumentado", "apatrida", "exiliado",
    # ------------------------------------------------ orientación / género
    "gay", "gei", "geis", "lesbiana", "homosexual", "bisexual",
    "pansexual", "asexual", "demisexual", "queer", "lgbt", "lgbtq",
    "trans", "transexual", "transgenero", "travesti", "no binario",
    "nobinario", "genero fluido", "intersex", "drag", "heterosexual",
    "hetero", "mujer", "hombre", "chica", "chico", "señora", "señor",
    "madre", "padre", "esposa", "esposo", "novia", "novio",
    "feminista", "machista", "masculinidad", "femineidad",
    "embarazada", "madre soltera", "padre soltero",
    # ------------------------------------------------ edad / cuerpo
    "niña", "niño", "niñas", "niños", "adolescente", "joven",
    "anciano", "anciana", "viejo", "vieja", "abuelo", "abuela",
    "jubilado", "pensionado", "gordo", "gorda", "gordito", "obeso",
    "obesa", "flaco", "flaca", "delgado", "anorexic", "bulimic",
    "enano", "enana", "bajito", "alto", "calvo", "pelon",
    "pelirrojo", "moreno claro", "lampiño", "peludo",
    # ------------------------------------------------ discapacidad / salud
    "discapacitado", "discapacitada", "discapacidad", "autista",
    "autismo", "asperger", "sindrome de down", "tdah", "tea",
    "sordo", "sorda", "ciego", "ciega", "mudo", "muda",
    "cojo", "coja", "paralitico", "parapleji", "cuadripleji",
    "silla de ruedas", "muletas", "protesis", "amputado",
    "bipolar", "esquizofren", "depresivo", "depresion", "ansiedad",
    "toc", "borderline", "suicida", "adicto", "alcoholico",
    "seropositivo", "vih", "sida", "cancer paciente", "diabetico",
    "epileptico", "celiaco", "alergico", "asmatico",
    # ------------------------------------------------ clase / trabajo
    "pobre", "rico", "clase baja", "clase alta", "mendigo",
    "indigente", "sin techo", "desempleado", "albañil",
    "empleada domestica", "sirvienta", "barrendero", "recolector",
    "vendedor ambulante", "taxista", "repartidor", "mesero",
    "campesina", "jornalero", "becario", "estudiante", "profesor",
    "maestro", "enfermera", "policia", "militar", "politico",
    # ------------------------------------------------ subcultura / afición
    "otaku", "friki", "nerd", "geek", "gamer", "emo", "punk",
    "metalero", "rockero", "reggaetoner", "trapero", "kpoper",
    "furro", "cosplayer", "hipster", "vegano", "vegana",
    "vegetariano", "carnivoro", "fitness", "gym rat",
    "chairo", "fifi", "facho", "comunista", "socialista",
    "capitalista", "anarquista", "derechista", "izquierdista",
    "liberal", "conservador", "progre", "provida", "proaborto",
    "sindicalista", "activista", "ecologista", "antivacuna",
    # ------------------------- ampliación 2: pueblos y etnias
    "quechua", "aymara", "mapuche", "guarani", "nahuatl", "maya",
    "zapoteco", "mixteco", "otomi", "wayuu", "tarahumara",
    "yanomami", "shipibo", "misquito", "garifuna", "afrocolombiano",
    "afromexicano", "afrobrasileño", "palenquero", "raizal",
    "pueblo originario", "comunidad indigena", "tribu", "etnia",
    "raza", "religion", "creencia", "culto", "casta",
    "kurdo", "armenio", "griego", "serbio", "croata", "bosnio",
    "albanes", "checo", "hungaro", "sueco", "noruego",
    "finlandes", "danes", "holandes", "belga", "suizo",
    "austriaco", "irlandes", "escoces", "gales",
    "britanico", "australiano", "neozelandes", "indonesio",
    "malayo", "tailandes", "camboyano", "birmano", "kazajo",
    "uzbeko", "georgiano", "azeri", "israelita", "jamaiquino",
    "antillano", "beliceño", "guyanes", "surinames", "andino",
    "amazonico", "altiplanico", "isleño", "fronterizo",
    # ------------------------- ampliación 2: género y orientación
    "transfemenina", "transmasculino", "cisgenero",
    "masculino", "femenino", "varon", "dama", "caballero",
    "muchacho", "muchacha", "señorita", "viuda", "viudo",
    "divorciado", "divorciada", "soltero", "soltera", "casado",
    "ama de casa", "madre trabajadora", "padre de familia",
    "madre adolescente", "familia homoparental", "pareja del mismo",
    "identidad de genero", "orientacion sexual", "salir del closet",
    "no heterosexual", "aliade", "aliado lgbt",
    # ------------------------- ampliación 2: discapacidad y salud
    "sordomudo", "invidente", "hipoacusico", "dislexic", "dispraxi",
    "tourette", "parkinson", "alzheimer", "demencia", "trisomia",
    "microcefali", "talla baja", "acondroplasia", "albinismo",
    "vitiligo", "psoriasis", "cicatriz", "quemado", "amputada",
    "oncologico", "quimioterapia", "trasplantado", "dializado",
    "inmunodeprimido", "celiaca", "intolerante", "silla electrica",
    "lengua de señas", "braille", "perro guia", "neurodivergente",
    "salud mental", "trastorno", "sindrome", "condicion cronica",
    "enfermedad rara", "paciente psiquiatrico", "internado",
    # ------------------------- ampliación 2: edad, cuerpo y clase
    "bebe", "recien nacido", "menor de edad", "adolescentes",
    "millennial", "generacion z", "tercera edad", "adulto mayor",
    "jubilada", "asilo de ancianos", "hogar de ancianos",
    "obesidad", "sobrepeso", "bajo peso", "estatura baja",
    "acne", "calvicie", "cana", "arruga", "estria", "celulitis",
    "clase media", "barrio popular", "asentamiento", "favela",
    "vecindad", "conventillo", "campamento", "zona rural",
    "sin estudios", "analfabeta", "becada", "beneficiario",
    "pension alimenticia", "subsidio", "ayuda social",
]

DENIGRANTES = [
    # ------------------------------------------------ desprecio directo
    "odio", "odia", "odian", "odiamos", "aborrezc", "detest",
    "asco", "asquer", "repugn", "nauseabund", "vomit", "arcada",
    "apesta", "apestos", "hedion", "inmund", "fetid", "putrefact",
    "maldit", "malnacid", "malparid", "desgraciad",
    "despreciabl", "detestabl", "abominabl", "aberrant", "aberracion",
    "antinatural", "degener", "perverti", "desviad", "enfermiz",
    "monstruo", "monstruos", "engendro", "aborto", "esperpent",
    "adefesi", "deforme", "defectuos", "error de la naturaleza",
    # ------------------------------------------------ deshumanización
    "rata", "ratas", "raton", "cucarach", "gusano", "alimaña",
    "sabandija", "garrapata", "sanguijuela", "piojo", "pulga",
    "bicho", "plaga", "parasit", "peste", "infest", "virus mental",
    "bestia", "salvaje", "primitiv", "atrasad", "incivilizad",
    "subhuman", "infrahuman", "no humano", "no humanos",
    "no son humanos", "no son personas", "no es persona",
    "son animales", "como animales", "manada", "horda", "chusma",
    "gentuza", "escoria", "lacra", "basura", "desperdicio",
    "escombro", "morralla", "podredumbre", "inmundicia",
    # ------------------------------------------------ criminalización
    "roba", "roban", "robando", "ladron", "ladrones", "ratero",
    "delincuent", "criminal", "maleant", "malandr", "malviv",
    "terrorist", "narco", "sicari", "violador", "abusador",
    "pedofil", "secuestrador", "estafador", "traficant",
    "ilegal", "indocument", "invasor", "invaden", "invasion",
    "usurpador", "colad", "clandestin",
    # ------------------------------------------------ inferioridad
    "inferior", "subdesarroll", "retrograd", "ignorant", "bruto",
    "incapaz", "inutil", "inservibl", "incompetent", "inept",
    "estorba", "estorbo", "sobra", "sobran", "lastre", "carga",
    "no sirven", "no sirve", "no deberia", "no deberian",
    "no merecen", "no merece", "no valen", "no vale nada",
    "no aportan", "no aporta", "no pertenecen", "no pertenece",
    "no tienen derecho", "no merecen vivir", "no merecen derechos",
    "no deberian existir", "no deberian votar",
    "no deberian tener hijos", "no deberian reproducirse",
    # ------------------------------------------------ parasitismo económico
    "a costa", "viven de", "vive de", "culpa de", "mantenid",
    "arrimad", "vividor", "aprovechad", "chupa del bote",
    "quitan el trabajo", "quitan trabajos", "roban trabajos",
    "nos quitan", "viven de nuestros impuestos", "de nuestros impuestos",
    "nos cuestan", "gasto publico", "limosner",
    # ------------------------------------------------ expulsión / violencia
    "fuera de aqui", "fuera del pais", "fuera de mi pais",
    "que se larguen", "que se vayan", "vuelvan a su pais",
    "regresen a su", "volver a su pais", "largo de aqui",
    "deportar", "expulsar", "echarlos", "sacarlos", "encerrar",
    "enjaular", "esclavo", "esclaviz", "esterilizar", "castrar",
    "quemar", "colgar", "fusilar", "lapidar", "linchar", "apalear",
    "golpear", "moler a palos", "gasear", "incinerar", "hornos",
    "extermin", "aniquil", "erradic", "eliminar a", "limpiar el pais",
    "purgar", "desaparec", "matar", "matarl", "matenl", "asesinar",
    "muerte a", "que se mueran", "ojala se mueran", "ojala mueran",
    "deberian morir", "merecen morir", "merece morir",
    # ------------------------------------------------ sucio / moral
    "sucio", "sucia", "sucios", "cochino", "cochina", "mugros",
    "piojos", "roñoso", "ronoso", "asquerosos", "guarro",
    "inmoral", "pecador", "impuro", "hereje", "infiel", "apostat",
    "satanic", "demoniac", "poseid",
    # ------------------------------------------------ inglés
    "hate", "hates", "hated", "disgusting", "revolting", "filthy",
    "nasty", "vile", "subhuman", "vermin", "parasite", "infest",
    "invade", "invasion", "invader", "plague", "cockroach",
    "scum", "trash", "garbage", "waste of", "worthless",
    "inferior", "savage", "primitive", "backward", "degenerate",
    "should die", "should be killed", "deserve to die",
    "dont belong", "do not belong", "go back to", "get out of",
    "steal our", "stealing our", "take our jobs", "taking our jobs",
    "exterminate", "eradicate", "lynch", "deport", "sterilize",
    "gas them", "kill them", "hang them", "ban them",
    # ------------------------- ampliación 2: deshumanización animal
    "macaco", "simio", "chimpanc", "primate", "orangutan",
    "hiena", "buitre", "carroñer", "carronier", "reptil",
    "vibora", "serpiente", "escorpion", "sanguijuel",
    "manada de", "horda de", "jauria", "camada",
    # ------------------------- ampliación 2: suciedad y desecho
    "turba", "lumpen", "gentualla", "desecho", "estiercol",
    "excremento", "porqueri", "pudricion", "cloaca",
    "estercoler", "vertedero", "alcantarill", "muladar",
    # ------------------------- ampliación 2: desprecio moral
    "traidor", "vendepatri", "quintacolumn", "infiltrad",
    "idolatr", "blasfem", "profan", "sacrileg",
    "pudrid", "desechabl", "prescindibl", "reemplazabl",
    "sin cerebro", "sin cultura", "sin educacion", "sin modales",
    "sin valores", "sin alma", "sin dignidad", "sin vergüenza",
    "no producen", "no trabajan", "no estudian", "no piensan",
    "no razonan", "no tienen cerebro", "no tienen cultura",
    "no tienen dignidad", "no tienen alma", "no tienen futuro",
    # ------------------------- ampliación 2: exclusión y violencia
    "deberian callarse", "que se callen", "no tienen voz",
    "no deberian opinar", "no deberian hablar", "no deberian salir",
    "no deberian estar aqui", "no deberian estudiar",
    "no deberian trabajar", "no deberian casarse",
    "no deberian adoptar", "no deberian criar",
    "hay que encerrarlos", "hay que separarlos", "hay que marcarlos",
    "hay que registrarlos", "hay que controlarlos",
    "hay que someterlos", "hay que humillarlos",
    "hay que golpearlos", "hay que quemarlos", "hay que matarlos",
    "hay que exterminarlos", "hay que erradicarlos",
    "hay que eliminarlos", "hay que deportarlos",
    "hay que expulsarlos", "hay que esterilizarlos",
    "son un cancer", "son una enfermedad", "son un problema",
    "son un estorbo", "son un lastre", "son una carga",
    "son inferiores", "son basura", "son escoria",
    "son animales", "no son humanos", "no valen nada",
    # ------------------------- ampliación 2: inglés
    "filth", "lowlife", "leech", "freeloader", "moocher",
    "breeding like", "overbreed", "roaches", "maggot",
    "should be gassed", "should be deported", "should be banned",
    "should be sterilized", "should be locked up",
    "dont deserve", "do not deserve", "have no rights",
    "are a disease", "are a plague", "are subhuman",
    "are vermin", "are animals", "are trash", "are worthless",
    "not welcome", "not human", "less than human",
    "breed like", "swarming in", "flooding in", "overrun",
]

_MAPA_LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "@": "a", "$": "s", "!": "i", "+": "t",
})

# Sustituciones fonéticas para evasiones: k4g4d4 -> cagada, pvta -> puta
_MAPA_FONETICO = str.maketrans({"k": "c", "q": "c", "v": "u", "z": "s"})

# Sufijos para las EXACTAS (plurales, diminutivos, aumentativos)
_SUFIJOS = (r"(?:s|es|a|o|as|os|ita|ito|itas|itos|illa|illo|illas|illos"
            r"|ote|ota|otes|otas|ada|adas|ado|ados|azo|aza|azos|azas"
            r"|on|ona|ones|onas|udo|uda|udos|udas|ero|era|eros|eras"
            r"|isimo|isima|isimos|isimas|zote|zotes)?")


def _normalizar(texto: str) -> str:
    texto = texto.lower().translate(_MAPA_LEET)
    # Quitar acentos (á -> a) pero conservar la ñ
    texto = texto.replace("ñ", "\x00")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace("\x00", "ñ")
    # Todo lo que no sea letra/número se vuelve espacio (p.u.t.o -> p u t o)
    texto = re.sub(r"[^a-z0-9ñ]+", " ", texto)
    return texto.strip()


def _variantes(texto: str):
    """Genera variantes del texto para atrapar evasiones."""
    normal = _normalizar(texto)
    base = [
        normal,
        # Letras repetidas colapsadas: "puuuuto" -> "puto"
        re.sub(r"(.)\1+", r"\1", normal),
        # Espacios eliminados: "p u t o" -> "puto"
        normal.replace(" ", ""),
    ]
    for v in base:
        yield v
        yield v.translate(_MAPA_FONETICO)


def _formas(palabra: str):
    """Forma normalizada + forma fonética de una entrada del diccionario."""
    norm = _normalizar(palabra)
    formas = {norm, norm.translate(_MAPA_FONETICO)}
    return [f for f in formas if f]


def _regex_alternativas(palabras, sufijo=""):
    alternativas = sorted({f for p in palabras for f in _formas(p)},
                          key=len, reverse=True)
    cuerpo = "|".join(re.escape(a) for a in alternativas)
    return re.compile(r"(?:^|\s)(" + cuerpo + r")" + sufijo + r"(?=\s|$)")


# Raíces: prefijo + cualquier terminación ("pito" -> "pitochico")
_RE_RAICES = _regex_alternativas(RAICES, sufijo=r"\w*")
# Exactas: palabra completa + sufijo común ("teta" -> "tetas", no "tétanos")
_RE_EXACTAS = _regex_alternativas(EXACTAS, sufijo=_SUFIJOS)
# Grupos y denigrantes: prefijo (cubre plurales y conjugaciones)
_RE_GRUPOS = _regex_alternativas(GRUPOS, sufijo=r"\w*")
_RE_DENIGRANTES = _regex_alternativas(
    [d for d in DENIGRANTES if " " not in d], sufijo=r"\w*")
_FRASES_DENIGRANTES = [d for d in DENIGRANTES if " " in d]

_FRASES_NORM = sorted({f for fr in FRASES for f in _formas(fr)},
                      key=len, reverse=True)

# Tamaño del diccionario (entradas únicas por capa), útil para pruebas.
TOTAL_ENTRADAS = {
    "raices": len(set(RAICES)),
    "exactas": len(set(EXACTAS)),
    "frases": len(set(FRASES)),
    "grupos": len(set(GRUPOS)),
    "denigrantes": len(set(DENIGRANTES)),
}


def _contiene_frase(variante: str, frases) -> str | None:
    con_margen = f" {variante} "
    for frase in frases:
        if f" {frase} " in con_margen or frase.replace(" ", "") == variante:
            return frase
    return None


def buscar_groseria(texto: str):
    """Devuelve la palabra/frase prohibida encontrada, o None si es limpio."""
    for variante in _variantes(texto):
        m = _RE_RAICES.search(variante)
        if m:
            return m.group(1)
        m = _RE_EXACTAS.search(variante)
        if m:
            return m.group(1)
        frase = _contiene_frase(variante, _FRASES_NORM)
        if frase:
            return frase
        # Discurso de odio: grupo protegido + expresión denigrante
        g = _RE_GRUPOS.search(variante)
        if g:
            d = _RE_DENIGRANTES.search(variante)
            if d:
                return f"discurso de odio ({g.group(1)} + {d.group(1)})"
            frase_d = _contiene_frase(
                variante, [_normalizar(f) for f in _FRASES_DENIGRANTES])
            if frase_d:
                return f"discurso de odio ({g.group(1)} + {frase_d})"
    return None


def es_limpio(texto: str) -> bool:
    return buscar_groseria(texto) is None
