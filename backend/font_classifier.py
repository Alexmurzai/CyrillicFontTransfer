"""
Классификатор шрифтов по категориям (Serif / Sans / Script / Display / Mono).
Использует эвристику на основе имени файла + опционально анализ глифов.
"""
import re

# Ключевые слова для определения категории по имени шрифта
CATEGORY_PATTERNS = {
    "serif": [
        r"\bserif\b", r"\bgara", r"\bbodoni\b", r"\bcambria\b", r"\btimes\b",
        r"\bgeorgia\b", r"\bpalatino\b", r"\bbaskerville\b", r"\bcentury\b",
        r"\brockwell\b", r"\bslab\b", r"\bmerriweather\b", r"\blora\b",
        r"\bplayfair\b", r"\bpt\s*serif\b", r"\bnoto\s*serif\b", r"\bsitka\b",
        r"\bsabon\b", r"\bsagona\b", r"\bwalbaum\b", r"\blibro\b",
        r"\bbook\b", r"\bantiqua\b", r"\bcalisto\b", r"\bconstantia\b",
        r"\beb\s*garamond\b", r"\bfrank\s*ruhl\b", r"\blucida\s*(bright|fax)\b",
        r"\bsource\s*serif\b", r"\bibm\s*plex\s*serif\b", r"\broboto\s*serif\b",
        r"\broboto\s*slab\b", r"\bdm\s*serif\b", r"\bfootlight\b",
        r"\bbell\s*mt\b", r"\bbembo\b", r"\bperpetua\b", r"\bgoudy\b",
        r"\bcentaur\b", r"\btisa\b", r"\bcalif\b", r"\bhigh\s*tower\b",
        r"\blibre\s*baskerville\b", r"\bquattrocento(?!\s*sans)\b",
    ],
    "sans": [
        r"\bsans\b", r"\barial\b", r"\bhelvetica\b", r"\bverdana\b",
        r"\btahoma\b", r"\btrebuchet\b", r"\bcalibri\b", r"\bsegoe\b",
        r"\bopen\s*sans\b", r"\broboto(?!\s*(serif|slab|mono))\b",
        r"\bmontserrat\b", r"\blato\b", r"\bpoppins\b", r"\bnunito\b",
        r"\boswald\b", r"\brubik\b", r"\binter\b", r"\bwork\s*sans\b",
        r"\bpt\s*sans\b", r"\bsource\s*sans\b", r"\bibm\s*plex\s*sans\b",
        r"\bnoto\s*sans\b", r"\bfira\s*sans\b", r"\bdm\s*sans\b",
        r"\braleway\b", r"\bbarlow\b", r"\bbahnschrift\b", r"\baptos\b",
        r"\bbierstadt\b", r"\bcandara\b", r"\bcorbel\b", r"\bgill\b",
        r"\bkarla\b", r"\blivvic\b", r"\bmanrope\b", r"\boxygen\b",
        r"\brunito\b", r"\bexo\b", r"\bdosis\b", r"\bhind\b",
        r"\bfranklin\b", r"\btrade\s*gothic\b", r"\bunivers\b",
        r"\bconcert\b", r"\bhammersmith\b", r"\bfjalla\b", r"\banton\b",
        r"\bbebas\b", r"\btitillium\b", r"\bquattrocento\s*sans\b",
        r"\blibre\s*franklin\b", r"\bgrandview\b", r"\bgrotesk\b",
        r"\bhaas\b", r"\bgothic\b", r"\bquestrial\b", r"\bvarela\b",
        r"\bseaford\b", r"\bskeena\b", r"\btenorite\b", r"\bkermit\b",
        r"\bdaytona\b", r"\bbiome\b", r"\bselawik\b", r"\bconvection\b",
        r"\bdidact\b", r"\bsecular\b", r"\bimpact\b",
    ],
    "script": [
        r"\bscript\b", r"\bcursive\b", r"\bhand\b", r"\bcallig\b",
        r"\bbrush\b", r"\bwriting\b", r"\binkfree\b", r"\bink\s*free\b",
        r"\bsacramento\b", r"\bpacifico\b", r"\blobster\b", r"\bitalianno\b",
        r"\bdancing\b", r"\bcaveat\b", r"\bshadows\b", r"\bpatrick\b",
        r"\bmistral\b", r"\bpristina\b", r"\brage\b", r"\bvladimir\b",
        r"\bvivaldi\b", r"\bedwardian\b", r"\bfreestyle\b", r"\bfrench\b",
        r"\bkunstler\b", r"\bpalace\b", r"\bblackadder\b", r"\bmeddon\b",
        r"\bmonotype\s*corsiva\b", r"\bdreaming\b", r"\bfairwater\b",
        r"\bfave\b", r"\bpetit\s*formal\b", r"\bbaguet\b", r"\bmystical\b",
        r"\byesteryear\b", r"\bcochocib\b",
    ],
    "display": [
        r"\bdisplay\b", r"\bposter\b", r"\bstencil\b", r"\bengraved\b",
        r"\binline\b", r"\bdecorative\b", r"\bfantasy\b", r"\bjokerman\b",
        r"\bravie\b", r"\bsnap\b", r"\bchiller\b", r"\bgigi\b",
        r"\bcurlz\b", r"\bcooper\b", r"\bbauhaus\b", r"\bbroadway\b",
        r"\bplaybill\b", r"\bshowcard\b", r"\bwide\s*latin\b",
        r"\bmagneto\b", r"\bharrington\b", r"\bcolonna\b", r"\bjuice\b",
        r"\bpapyrus\b", r"\bparchment\b", r"\bold\s*english\b",
        r"\bcastellar\b", r"\balgerian\b", r"\bbritannic\b",
        r"\bcopperplate\b", r"\bengravers\b", r"\bfelix\b",
        r"\bniagara\b", r"\bonyx\b", r"\bpoor\s*richard\b",
        r"\bmodern\s*love\b", r"\bnordique\b", r"\bchamberi\b",
        r"\bpoiret\b", r"\bstaat\b", r"\bfredoka\b",
    ],
    "mono": [
        r"\bmono\b", r"\bconsol\b", r"\bcourier\b", r"\btypewriter\b",
        r"\bfixed\b", r"\bfira\s*code\b", r"\bfira\s*mono\b",
        r"\bjbmono\b", r"\bjetbrains\b", r"\bsource\s*code\b",
        r"\binconsolata\b", r"\bibm\s*plex\s*mono\b", r"\broboto\s*mono\b",
        r"\bdm\s*mono\b", r"\bpt\s*mono\b", r"\bubuntu\s*mono\b",
        r"\bligcon\b", r"\bocrb\b",
    ]
}


def classify_font(font_name: str) -> str:
    """
    Определяет категорию шрифта по его имени.
    Возвращает: 'serif', 'sans', 'script', 'display', 'mono', 'unknown'
    
    Приоритет: mono > script > display > serif > sans
    (т.к. "Roboto Mono" — mono, не sans; "Lobster" — script, не display)
    """
    name_lower = font_name.lower()
    
    # Проверяем в порядке приоритета
    for category in ["mono", "script", "display", "serif", "sans"]:
        patterns = CATEGORY_PATTERNS[category]
        for pattern in patterns:
            if re.search(pattern, name_lower):
                return category
    
    return "unknown"


def classify_all_fonts(metadata: list[dict]) -> dict[int, str]:
    """
    Классифицирует все шрифты в метаданных.
    Возвращает словарь {id: category}.
    """
    result = {}
    for entry in metadata:
        result[entry["id"]] = classify_font(entry["name"])
    return result
