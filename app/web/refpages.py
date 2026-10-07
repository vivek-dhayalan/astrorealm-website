"""Reference pages: the 27 nakshatras, the 12 rasis and the star-to-star Porutham table, in English, Tamil and Hindi.

Everything here is computed from the same rule tables the matcher uses (app/rules/v1.py), so the pages can't drift
from the results the site gives. Tamil and Hindi text is a draft for native-speaker review.
"""
from __future__ import annotations

from ..core.reference import NAKSHATRAS, RASHIS
from ..render import i18n
from . import stars as S
from .settings import Settings
from .ui import (ELEMENT, GANA, GRADE, GRADE_SHORT, LANG_LABEL, NADI, QUALITY, RAJJU, SEX, SITE_LANGS, T, V, VARNA,
                 VASHYA, YONI, _extra, deity_symbol, lpath, pick, rasi_symbol)
from .views import article_ld, breadcrumb_ld, esc, layout, site_lang

GRADE_CLASS = {"UTTAMAM": "g-ut", "MADHYAMAM": "g-md", "ADHAMAM": "g-ad", "REJECTED": "g-rj"}
TABLE_PATH = "/learn/nakshatra-porutham-table"

# page text: key → (en, ta, hi). {placeholders} are filled with already-escaped values or our own links.
RT = {
    "naks_crumb": ("Nakshatras", "நட்சத்திரங்கள்", "नक्षत्र"),
    "rasis_crumb": ("Rasis", "ராசிகள்", "राशियाँ"),
    "naks_h1": ("The 27 nakshatras (birth stars)", "27 நட்சத்திரங்கள்", "27 नक्षत्र (जन्म नक्षत्र)"),
    "naks_lead": (
        "The Moon's position at birth falls in one of 27 nakshatras of 13°20′ each — your janma nakshatra or birth "
        "star. It decides your Vimshottari dasha, and it is the starting point of every marriage-matching check.",
        "பிறக்கும் நேரத்தில் சந்திரன் நின்ற இடம் 13°20′ அளவுள்ள 27 நட்சத்திரங்களில் ஒன்றில் விழும் — அதுவே உங்கள் "
        "ஜன்ம நட்சத்திரம். உங்கள் விம்சோத்தரி தசையை அதுவே தீர்மானிக்கிறது; ஒவ்வொரு திருமணப் பொருத்தக் கணக்கும் "
        "அதிலிருந்தே தொடங்குகிறது.",
        "जन्म के समय चंद्रमा 13°20′ के 27 नक्षत्रों में से किसी एक में होता है — यही आपका जन्म नक्षत्र है। इसी से "
        "आपकी विंशोत्तरी दशा तय होती है, और विवाह मिलान की हर जाँच यहीं से शुरू होती है।"),
    "naks_p2": (
        "Each nakshatra has four padas (quarters) of 3°20′, so the 27 stars make 108 padas — nine to each rasi. Some "
        "stars, such as Krittika and Chitra, therefore fall in two rasis. Choose a star for its lord, deity, gana, "
        "yoni, nadi and rajju, and the stars it matches best with.",
        "ஒவ்வொரு நட்சத்திரத்துக்கும் 3°20′ அளவுள்ள நான்கு பாதங்கள் உண்டு; 27 நட்சத்திரங்களும் சேர்ந்து 108 பாதங்கள் "
        "— ஒவ்வொரு ராசிக்கும் ஒன்பது. அதனால் கார்த்திகை, சித்திரை போன்ற சில நட்சத்திரங்கள் இரண்டு ராசிகளில் "
        "விழுகின்றன. ஒரு நட்சத்திரத்தைத் தேர்ந்தெடுத்து அதன் அதிபதி, தேவதை, கணம், யோனி, நாடி, ரஜ்ஜு, சிறந்த "
        "பொருத்தங்களைப் பார்க்கவும்.",
        "हर नक्षत्र के 3°20′ के चार चरण (पाद) होते हैं, इसलिए 27 नक्षत्रों के 108 चरण हैं — हर राशि में नौ। इसी कारण "
        "कृत्तिका और चित्रा जैसे कुछ नक्षत्र दो राशियों में पड़ते हैं। किसी नक्षत्र को चुनकर उसका स्वामी, देवता, गण, "
        "योनि, नाड़ी, रज्जु और सबसे अच्छे मिलान देखें।"),
    "naks_outro": (
        'To compare two stars at once, see the <a href="{table}">nakshatra porutham table</a>. For what Rajju and Nadi '
        'mean, read <a href="/learn/rajju-nadi">Rajju and Nadi dosha</a>.',
        'இரண்டு நட்சத்திரங்களை ஒரே நேரத்தில் ஒப்பிட <a href="{table}">நட்சத்திரப் பொருத்த அட்டவணையைப்</a> '
        'பார்க்கவும். ரஜ்ஜு, நாடியின் பொருள் அறிய <a href="/learn/rajju-nadi">ரஜ்ஜு, நாடி தோஷம்</a> படிக்கவும்.',
        'दो नक्षत्रों की एक साथ तुलना के लिए <a href="{table}">नक्षत्र मिलान तालिका</a> देखें। रज्जु और नाड़ी का अर्थ '
        'जानने के लिए <a href="/learn/rajju-nadi">रज्जु और नाड़ी दोष</a> पढ़ें।'),
    "col_nak": ("Nakshatra", "நட்சத்திரம்", "नक्षत्र"),
    "col_rasi": ("Rasi", "ராசி", "राशि"),
    "col_other": ("Tamil / Hindi", "பிற பெயர்கள்", "अन्य नाम"),
    "col_lord": ("Lord", "அதிபதி", "स्वामी"),
    "col_gana": ("Gana", "கணம்", "गण"),
    "col_nadi": ("Nadi", "நாடி", "नाड़ी"),
    "col_rajju": ("Rajju", "ரஜ்ஜு", "रज्जु"),
    "col_english": ("English", "ஆங்கிலம்", "अंग्रेज़ी"),
    "col_element": ("Element", "தத்துவம்", "तत्व"),
    "col_naks": ("Nakshatras", "நட்சத்திரங்கள்", "नक्षत्र"),
    "naks_title": ("27 Nakshatras – Lord, Rasi, Gana, Nadi & Rajju of Each Star",
                   "27 நட்சத்திரங்கள் – அதிபதி, ராசி, கணம், நாடி, ரஜ்ஜு",
                   "27 नक्षत्रों की सूची – स्वामी, राशि, गण, नाड़ी और रज्जु"),
    "naks_desc": ("All 27 nakshatras with their Tamil and Hindi names, ruling planet, rasi, gana, nadi and rajju, and "
                  "links to each star's best marriage matches.",
                  "27 நட்சத்திரங்களும் — ஆங்கில, இந்திப் பெயர்கள், அதிபதி கிரகம், ராசி, கணம், நாடி, ரஜ்ஜு, ஒவ்வொன்றின் "
                  "சிறந்த திருமணப் பொருத்தங்களுக்கான இணைப்புகளுடன்.",
                  "सभी 27 नक्षत्र — तमिल और अंग्रेज़ी नाम, स्वामी ग्रह, राशि, गण, नाड़ी और रज्जु, और हर नक्षत्र के सबसे "
                  "अच्छे विवाह मिलान के लिंक के साथ।"),

    # one nakshatra
    "nak_h1": ("{name} nakshatra", "{name} நட்சத்திரம்", "{name} नक्षत्र"),
    "nak_lead": ("{name} is the {ord} of the 27 nakshatras. It is ruled by {lord}, its presiding deity is {deity}, "
                 "and its symbol is {symbol}.",
                 "{name} 27 நட்சத்திரங்களில் {n}-ஆவது நட்சத்திரம். இதன் அதிபதி {lord}; அதிதேவதை {deity}; சின்னம் "
                 "{symbol}.",
                 "{name} 27 नक्षत्रों में {n}वाँ नक्षत्र है। इसका स्वामी {lord} है, अधिष्ठाता देवता {deity} हैं, और "
                 "इसका प्रतीक {symbol} है।"),
    "f_other": ("Other languages", "பிற மொழிகளில்", "अन्य भाषाओं में"),
    "f_span": ("Span (sidereal)", "பாகை (நிராயனம்)", "विस्तार (निरयण)"),
    "f_lord": ("Ruling planet (dasha lord)", "அதிபதி (தசா நாதன்)", "स्वामी ग्रह (दशा स्वामी)"),
    "f_deity": ("Deity", "அதிதேவதை", "देवता"),
    "f_symbol": ("Symbol", "சின்னம்", "प्रतीक"),
    "f_yoni": ("Yoni (animal)", "யோனி (விலங்கு)", "योनि (पशु)"),
    "f_vedha": ("Vedha (obstructing) star", "வேதை நட்சத்திரம்", "वेध नक्षत्र"),
    "pada_all": ("all four padas", "நான்கு பாதங்களும்", "चारों चरण"),
    "pada_one": ("pada {p}", "{p}-ஆம் பாதம்", "चरण {p}"),
    "pada_some": ("padas {p}", "{p} பாதங்கள்", "चरण {p}"),
    "nak_para": (
        'People born with the Moon in {name} begin life in the dasha of {lord}. In marriage matching, its {gana} gana, '
        '{nadi} nadi and {rajju} rajju are compared with the partner\'s star — read <a href="/learn/porutham">how the '
        'poruthams work</a> and <a href="/learn/rajju-nadi">why Rajju and Nadi matter</a>.',
        '{name} நட்சத்திரத்தில் பிறந்தவர்களுக்கு முதல் தசை {lord} தசை. திருமணப் பொருத்தத்தில் இதன் {gana} கணம், '
        '{nadi} நாடி, {rajju} ரஜ்ஜு ஆகியவை துணையின் நட்சத்திரத்துடன் ஒப்பிடப்படுகின்றன — '
        '<a href="/learn/porutham">பொருத்தங்கள் எப்படி</a>, <a href="/learn/rajju-nadi">ரஜ்ஜு, நாடி ஏன் முக்கியம்</a> '
        'என்பதைப் படிக்கவும்.',
        '{name} नक्षत्र में जन्मे लोगों की पहली दशा {lord} की होती है। विवाह मिलान में इसका {gana} गण, {nadi} नाड़ी और '
        '{rajju} रज्जु साथी के नक्षत्र से मिलाए जाते हैं — <a href="/learn/porutham">पोरुथम कैसे काम करते हैं</a> और '
        '<a href="/learn/rajju-nadi">रज्जु व नाड़ी क्यों ज़रूरी हैं</a>, पढ़ें।'),
    "h_bride": ("Marriage matching for {a_name} bride", "{name} நட்சத்திர மணமகளுக்குப் பொருத்தம்",
                "{name} नक्षत्र की वधू के लिए मिलान"),
    "h_groom": ("Marriage matching for {a_name} groom", "{name} நட்சத்திர மணமகனுக்குப் பொருத்தம்",
                "{name} नक्षत्र के वर के लिए मिलान"),
    "best_b": ("Uttamam (excellent) with a groom born in:", "உத்தமம் — மணமகனின் நட்சத்திரம்:",
               "उत्तम — वर का नक्षत्र:"),
    "best_g": ("Uttamam (excellent) with a bride born in:", "உத்தமம் — மணமகளின் நட்சத்திரம்:",
               "उत्तम — वधू का नक्षत्र:"),
    "some": ("Uttamam for some padas:", "சில பாதங்களுக்கு மட்டும் உத்தமம்:", "कुछ चरणों के लिए उत्तम:"),
    "avoid": ("Rejected (same nadi or vedha) with:", "நிராகரிப்பு (ஒரே நாடி அல்லது வேதை):",
              "अस्वीकार (एक ही नाड़ी या वेध):"),
    "none_all": ("no star in all padas", "எல்லாப் பாதங்களிலும் எதுவும் இல்லை", "सभी चरणों में कोई नहीं"),
    "sum_b": ("All 27 groom's stars for {a_name} bride", "{name} மணமகளுக்கு 27 நட்சத்திரங்களும்",
              "{name} वधू के लिए सभी 27 नक्षत्र"),
    "sum_g": ("All 27 bride's stars for {a_name} groom", "{name} மணமகனுக்கு 27 நட்சத்திரங்களும்",
              "{name} वर के लिए सभी 27 नक्षत्र"),
    "col_groom_star": ("Groom's star", "மணமகன் நட்சத்திரம்", "वर का नक्षत्र"),
    "col_bride_star": ("Bride's star", "மணமகள் நட்சத்திரம்", "वधू का नक्षत्र"),
    "col_poruthams": ("Poruthams", "பொருத்தங்கள்", "पोरुथम"),
    "col_result": ("Result", "முடிவு", "परिणाम"),
    "dep_pada": (" (depends on pada)", " (பாதத்தைப் பொறுத்து)", " (चरण पर निर्भर)"),
    "disclaimer": (
        'Matching here uses the birth stars only, with the rules AstroRealm applies (strict view: partial matches not '
        'counted). A full match also depends on the rasi and pada, which come from the exact birth time — '
        '<a href="/match">check the full matching</a> with both birth details, and consult an astrologer before '
        'deciding.',
        'இங்குள்ள பொருத்தம் நட்சத்திரங்களை மட்டும் கொண்டது; AstroRealm விதிகளின்படி கண்டிப்பான பார்வையில் (பாதிப் '
        'பொருத்தம் கணக்கில் இல்லை). முழுப் பொருத்தத்துக்கு ராசி, பாதமும் தேவை — அவை பிறந்த நேரத்தைப் பொறுத்தவை. இரு '
        'பிறப்பு விவரங்களுடன் <a href="/match">முழுப் பொருத்தம் பார்க்கவும்</a>; முடிவெடுக்கும் முன் ஜோதிடரை அணுகவும்.',
        'यहाँ मिलान केवल जन्म नक्षत्रों से है, AstroRealm के नियमों के कठोर दृष्टिकोण से (आंशिक मिलान नहीं गिने गए)। '
        'पूरे मिलान के लिए राशि और चरण भी चाहिए, जो जन्म समय से तय होते हैं — दोनों के जन्म विवरण से '
        '<a href="/match">पूरा मिलान देखें</a>, और निर्णय से पहले ज्योतिषी से सलाह लें।'),
    "cta_full": ("Full Matching", "முழுப் பொருத்தம் பார்க்க", "पूरा मिलान देखें"),
    "cta_table": ("Porutham Table", "பொருத்த அட்டவணை", "मिलान तालिका"),
    "all_naks": ("All nakshatras", "அனைத்து நட்சத்திரங்கள்", "सभी नक्षत्र"),
    "nak_title": ("{name} Nakshatra – Lord, Rasi & Marriage Matching",
                  "{name} நட்சத்திரம் – அதிபதி, ராசி, கணம், திருமணப் பொருத்தம்",
                  "{name} नक्षत्र – स्वामी, राशि, गण और विवाह मिलान"),
    "nak_desc": ("{name} nakshatra ({ta}): ruled by {lord}, in {rasis} rasi, {gana} gana, {nadi} nadi, {rajju} rajju — "
                 "plus its best and worst Porutham matches.",
                 "{name} நட்சத்திரம்: அதிபதி {lord}, {rasis} ராசி, {gana} கணம், {nadi} நாடி, {rajju} ரஜ்ஜு — பொருத்த "
                 "முறைப்படி சிறந்த, தவிர்க்க வேண்டிய நட்சத்திரங்கள்.",
                 "{name} नक्षत्र: स्वामी {lord}, {rasis} राशि, {gana} गण, {nadi} नाड़ी, {rajju} रज्जु — पोरुथम के "
                 "अनुसार सबसे अच्छे और वर्जित विवाह मिलान।"),

    # rasis
    "rasis_h1": ("The 12 rasis (Moon signs)", "12 ராசிகள்", "12 राशियाँ (चंद्र राशि)"),
    "rasis_lead": (
        "The zodiac is divided into 12 rasis of 30° each. Your rasi in Indian astrology is usually the sign the Moon "
        "occupied at birth — the janma rasi — measured in the sidereal zodiac, so it is often one sign behind your "
        "Western Sun sign.",
        "ராசி மண்டலம் 30° அளவுள்ள 12 ராசிகளாகப் பிரிக்கப்படுகிறது. இந்திய ஜோதிடத்தில் உங்கள் ராசி என்பது பொதுவாகப் "
        "பிறக்கும்போது சந்திரன் நின்ற ராசி — ஜன்ம ராசி. இது நிராயன முறையில் கணக்கிடப்படுவதால், மேற்கத்திய சூரிய "
        "ராசிக்கு ஒரு ராசி பின்னால் இருப்பது வழக்கம்.",
        "राशिचक्र 30° की 12 राशियों में बँटा है। भारतीय ज्योतिष में आपकी राशि आम तौर पर वह राशि है जिसमें जन्म के समय "
        "चंद्रमा था — जन्म राशि। इसे निरयण पद्धति से मापा जाता है, इसलिए यह अक्सर पश्चिमी सूर्य राशि से एक राशि "
        "पीछे होती है।"),
    "rasis_outro": (
        'In marriage matching, the two Moon signs decide the Rasi, Rasyadhipathi, Vasya and Varna poruthams, and the '
        'Varna, Vashya, Graha Maitri and Bhakoot kootas of <a href="/learn/ashtakoota">Ashtakoota</a>.',
        'திருமணப் பொருத்தத்தில் இரு ஜன்ம ராசிகளும் ராசி, ராசி அதிபதி, வசியம், வர்ணப் பொருத்தங்களையும், '
        '<a href="/learn/ashtakoota">அஷ்டகூடத்தின்</a> வர்ணம், வச்யம், கிரக மைத்ரி, பகூடம் ஆகிய கூடங்களையும் '
        'தீர்மானிக்கின்றன.',
        'विवाह मिलान में दोनों चंद्र राशियाँ पोरुथम के राशि, राशि अधिपति, वश्य और वर्ण मिलान, और '
        '<a href="/learn/ashtakoota">अष्टकूट</a> के वर्ण, वश्य, ग्रह मैत्री और भकूट कूट तय करती हैं।'),
    "rasis_title": ("12 Rasis (Moon Signs) – Lord, Element, Nakshatras and Matching",
                    "12 ராசிகள் – அதிபதி, தத்துவம், நட்சத்திரங்கள், பொருத்தம்",
                    "12 राशियाँ – स्वामी, तत्व, नक्षत्र और मिलान"),
    "rasis_desc": ("The 12 rasis (Moon signs) with English, Tamil and Hindi names, ruling planet, element and the "
                   "nakshatras in each, and how they are used in marriage matching.",
                   "12 ராசிகளும் — ஆங்கில, இந்திப் பெயர்கள், அதிபதி கிரகம், தத்துவம், அதில் உள்ள நட்சத்திரங்கள், "
                   "திருமணப் பொருத்தத்தில் அவற்றின் பங்கு.",
                   "सभी 12 राशियाँ — तमिल और अंग्रेज़ी नाम, स्वामी ग्रह, तत्व, उनके नक्षत्र, और विवाह मिलान में उनका "
                   "उपयोग।"),
    "rasi_h1": ("{name} rasi ({english})", "{name} ராசி ({english})", "{name} राशि ({english})"),
    "rasi_lead": ("{name} is the {ord} rasi, spanning {a}° to {b}° of the sidereal zodiac. It is ruled by {lord}, its "
                  "symbol is {symbol}, and it is a {element} sign of the {quality} kind.",
                  "{name} {n}-ஆவது ராசி; நிராயன ராசி மண்டலத்தில் {a}° முதல் {b}° வரை. இதன் அதிபதி {lord}; சின்னம் "
                  "{symbol}; இது {element} தத்துவமுள்ள {quality}.",
                  "{name} {n}वीं राशि है, जो निरयण राशिचक्र में {a}° से {b}° तक फैली है। इसका स्वामी {lord} है, "
                  "प्रतीक {symbol} है, और यह {element} तत्व की {quality} राशि है।"),
    "f_western": ("Western name", "மேற்கத்தியப் பெயர்", "पश्चिमी नाम"),
    "f_other_r": ("Other languages", "பிற மொழிகளில்", "अन्य भाषाओं में"),
    "f_el_q": ("Element / quality", "தத்துவம் / வகை", "तत्व / प्रकृति"),
    "f_strength": ("Exaltation / debilitation", "உச்சம் / நீசம்", "उच्च / नीच"),
    "exalted": ("{p} is exalted here", "{p} உச்சம்", "{p} उच्च"),
    "debilitated": ("{p} is debilitated here", "{p} நீசம்", "{p} नीच"),
    "f_varna": ("Varna", "வர்ணம்", "वर्ण"),
    "f_vashya": ("Vashya group", "வசியக் குழு", "वश्य वर्ग"),
    "h_rasi_match": ("{name} in marriage matching", "திருமணப் பொருத்தத்தில் {name}", "विवाह मिलान में {name}"),
    "li_rasi": ("<strong>Rasi porutham</strong> — for a bride with {name} rasi, it matches when the groom's rasi is "
                "{list} (same rasi counts only with a different star).",
                "<strong>ராசிப் பொருத்தம்</strong> — {name} ராசி மணமகளுக்கு, மணமகனின் ராசி {list} ஆக இருந்தால் "
                "பொருத்தம் (ஒரே ராசி என்றால் நட்சத்திரம் வேறாக இருக்க வேண்டும்).",
                "<strong>राशि पोरुथम</strong> — {name} राशि की वधू के लिए, वर की राशि {list} हो तो मिलान होता है "
                "(एक ही राशि तभी, जब नक्षत्र अलग हो)।"),
    "li_vasya": ("<strong>Vasya</strong> — {name} is vasya with {list}.",
                 "<strong>வசியம்</strong> — {name} ராசிக்கு வசியமான ராசிகள்: {list}.",
                 "<strong>वश्य</strong> — {name} के साथ वश्य राशियाँ: {list}।"),
    "li_bhakoot": ("<strong>Bhakoot dosha</strong> (Ashtakoota) — Moon signs 2/12, 5/9 or 6/8 apart: {name} with "
                   "{list}. It is cancelled when the two sign lords are the same planet or mutual friends.",
                   "<strong>பகூட தோஷம்</strong> (அஷ்டகூடம்) — இரு ஜன்ம ராசிகளும் 2/12, 5/9, 6/8 நிலையில் இருந்தால்: "
                   "{name} உடன் {list}. இரு ராசி அதிபதிகளும் ஒரே கிரகமாகவோ பரஸ்பர நண்பர்களாகவோ இருந்தால் இது "
                   "நிவர்த்தியாகும்.",
                   "<strong>भकूट दोष</strong> (अष्टकूट) — चंद्र राशियाँ 2/12, 5/9 या 6/8 पर हों: {name} के साथ "
                   "{list}। दोनों राशियों के स्वामी एक ही ग्रह हों या परस्पर मित्र हों, तो यह रद्द हो जाता है।"),
    "li_lord": ("<strong>Rasyadhipathi</strong> — compares {lord} with the lord of the partner's rasi: the same planet "
                "or mutual friends match, an enemy on either side fails, anything else is partial.",
                "<strong>ராசி அதிபதிப் பொருத்தம்</strong> — {lord}, துணையின் ராசி அதிபதியுடன் ஒப்பிடப்படுகிறது: ஒரே "
                "கிரகம் அல்லது பரஸ்பர நண்பர்கள் என்றால் பொருத்தம்; ஒருபுறம் பகை இருந்தாலும் பொருத்தமில்லை; மற்றவை "
                "பாதிப் பொருத்தம்.",
                "<strong>राशि अधिपति</strong> — {lord} की तुलना साथी की राशि के स्वामी से होती है: एक ही ग्रह या "
                "परस्पर मित्र हों तो मिलान, किसी भी ओर शत्रुता हो तो नहीं, बाकी आंशिक।"),
    "all_rasis": ("All rasis", "அனைத்து ராசிகள்", "सभी राशियाँ"),
    "rasi_title": ("{name} Rasi ({english}) – Lord, Nakshatras & Matching",
                   "{name} ராசி ({english}) – அதிபதி, நட்சத்திரங்கள், திருமணப் பொருத்தம்",
                   "{name} राशि ({english}) – स्वामी, नक्षत्र और विवाह मिलान"),
    "rasi_desc": ("{name} rasi ({english}, {ta}): ruled by {lord}, {element} sign, with {naks} — and its role in "
                  "Porutham and Guna Milan.",
                  "{name} ராசி: அதிபதி {lord}, {element} தத்துவம், நட்சத்திரங்கள் {naks} — பொருத்தம், அஷ்டகூடத்தில் "
                  "இதன் பங்கு.",
                  "{name} राशि: स्वामी {lord}, {element} तत्व, नक्षत्र {naks} — पोरुथम और गुण मिलान में इसका उपयोग।"),

    # table
    "tbl_h1": ("Nakshatra porutham table", "நட்சத்திரப் பொருத்த அட்டவணை", "नक्षत्र मिलान तालिका (पोरुथम)"),
    "tbl_lead": (
        "Every bride's star (rows) against every groom's star (columns): how many of the 12 poruthams match, and the "
        "overall grade. Hover or tap a cell for the pair's names.",
        "ஒவ்வொரு மணமகள் நட்சத்திரமும் (வரிசைகள்) ஒவ்வொரு மணமகன் நட்சத்திரத்துடனும் (நெடுவரிசைகள்): 12 பொருத்தங்களில் "
        "எத்தனை பொருந்துகின்றன, ஒட்டுமொத்த நிலை என்ன. ஜோடியின் பெயர்களைக் காண ஒரு கட்டத்தின் மேல் சுட்டியை "
        "வைக்கவும் அல்லது தொடவும்.",
        "हर वधू नक्षत्र (पंक्तियाँ) के सामने हर वर नक्षत्र (स्तंभ): 12 पोरुथम में से कितने मिलते हैं, और कुल परिणाम। "
        "जोड़े के नाम देखने के लिए किसी खाने पर माउस रखें या टैप करें।"),
    "lg_rej": ("✕ Rejected (Nadi or Vedha)", "✕ நிராகரிப்பு (நாடி அல்லது வேதை)", "✕ अस्वीकार (नाड़ी या वेध)"),
    "lg_mixed": ("dashed: depends on pada", "புள்ளிக்கோடு: பாதத்தைப் பொறுத்து", "बिंदुदार: चरण पर निर्भर"),
    "corner": ("Bride ↓ / Groom →", "மணமகள் ↓ / மணமகன் →", "वधू ↓ / वर →"),
    "cell": ("Bride {g}, groom {b}: {grades}", "மணமகள் {g}, மணமகன் {b}: {grades}", "वधू {g}, वर {b}: {grades}"),
    "how_h": ("How to read it", "எப்படிப் படிப்பது", "कैसे पढ़ें"),
    "how1": ("Find the bride's star in the left column and the groom's star along the top. The number is how many "
             "poruthams match fully, out of 12. A range such as 5–7 means the answer depends on the pada (and so the "
             "rasi) of the stars.",
             "இடப்புற நெடுவரிசையில் மணமகளின் நட்சத்திரத்தையும் மேலே மணமகனின் நட்சத்திரத்தையும் கண்டறியவும். எண் என்பது "
             "12-இல் முழுமையாகப் பொருந்தும் பொருத்தங்களின் எண்ணிக்கை. 5–7 போன்ற வரம்பு, முடிவு நட்சத்திரத்தின் "
             "பாதத்தையும் (அதனால் ராசியையும்) பொறுத்தது என்பதைக் காட்டுகிறது.",
             "बाएँ स्तंभ में वधू का नक्षत्र और ऊपर वर का नक्षत्र खोजें। संख्या बताती है कि 12 में से कितने पोरुथम पूरी "
             "तरह मिलते हैं। 5–7 जैसी सीमा का अर्थ है कि परिणाम नक्षत्रों के चरण (और इसलिए राशि) पर निर्भर है।"),
    "how2": ("The colour is the grade AstroRealm gives: <strong>Uttamam</strong> when Rajju, Varna, Nadi, Rasi, "
             "Rasyadhipathi and Stree Deergha all match; <strong>Madhyamam</strong> when at least Rajju matches; "
             "<strong>Rejected</strong> when Nadi (without an exception) or Vedha fails.",
             "நிறம் AstroRealm தரும் நிலையைக் காட்டுகிறது: ரஜ்ஜு, வர்ணம், நாடி, ராசி, ராசி அதிபதி, ஸ்திரீ தீர்க்கம் "
             "அனைத்தும் பொருந்தினால் <strong>உத்தமம்</strong>; குறைந்தது ரஜ்ஜு பொருந்தினால் <strong>மத்திமம்</strong>; "
             "நாடி (விதிவிலக்கின்றி) அல்லது வேதை பொருந்தாவிட்டால் <strong>நிராகரிப்பு</strong>.",
             "रंग AstroRealm का परिणाम दिखाता है: रज्जु, वर्ण, नाड़ी, राशि, राशि अधिपति और स्त्री दीर्घ सभी मिलें तो "
             "<strong>उत्तम</strong>; कम से कम रज्जु मिले तो <strong>मध्यम</strong>; नाड़ी (बिना अपवाद) या वेध न मिले "
             "तो <strong>अस्वीकार</strong>।"),
    "how3": ("The count alone can mislead: a pair with 8 matches but the same rajju is still graded lower than a pair "
             'with 6 that passes the key checks. See <a href="/learn/porutham">the 10 poruthams explained</a>.',
             "எண்ணிக்கை மட்டும் தவறாக வழிநடத்தலாம்: 8 பொருத்தங்கள் இருந்தும் ஒரே ரஜ்ஜுவான ஜோடி, முக்கியப் பொருத்தங்கள் "
             "பொருந்தும் 6 பொருத்த ஜோடியைவிடக் குறைவாகவே மதிப்பிடப்படும். "
             '<a href="/learn/porutham">10 பொருத்தங்கள் விளக்கம்</a> பார்க்கவும்.',
             "केवल संख्या भ्रामक हो सकती है: 8 मिलानों वाला पर एक ही रज्जु वाला जोड़ा, मुख्य जाँचें पास करने वाले 6 "
             'मिलानों वाले जोड़े से नीचे आता है। <a href="/learn/porutham">पोरुथम की व्याख्या</a> देखें।'),
    "how4": ("The table is not symmetric, because several checks count from the bride's star to the groom's.",
             "பல கணக்குகள் மணமகளின் நட்சத்திரத்திலிருந்து மணமகனின் நட்சத்திரம் வரை எண்ணப்படுவதால் அட்டவணை "
             "சமச்சீராக இருக்காது.",
             "तालिका सममित नहीं है, क्योंकि कई जाँचें वधू के नक्षत्र से वर के नक्षत्र तक गिनी जाती हैं।"),
    "tbl_title": ("Nakshatra Porutham Table (27×27) – Matching by Birth Star",
                  "நட்சத்திரப் பொருத்த அட்டவணை (27×27) – திருமணப் பொருத்தம்",
                  "नक्षत्र मिलान तालिका (27×27) – जन्म नक्षत्र से विवाह मिलान"),
    "tbl_desc": ("Porutham chart for all 27 × 27 birth stars: how many of the 12 poruthams match for each bride–groom "
                 "nakshatra pair, and which pairs are rejected.",
                 "27 × 27 நட்சத்திரங்களுக்கும் திருமணப் பொருத்த அட்டவணை: ஒவ்வொரு மணமகள், மணமகன் நட்சத்திர ஜோடிக்கும் "
                 "12-இல் எத்தனை பொருத்தம், உத்தமம், மத்திமம் அல்லது நிராகரிப்பு.",
                 "सभी 27 × 27 जन्म नक्षत्रों के लिए पोरुथम तालिका: हर वधू और वर नक्षत्र के लिए 12 में से कितने पोरुथम "
                 "मिलते हैं, और कौन-से जोड़े उत्तम, मध्यम या अस्वीकार हैं।"),
}


def R_(lang: str, key: str, **kw) -> str:
    ex = _extra(lang)
    text = pick(RT[key], lang, ex.RT if ex else None, key)
    return text.format(**kw) if kw else text


# ------------------------------------------------------------------ small helpers
def nak_name(lang: str, i: int) -> str:
    return S.names(lang, "nakshatra", i)


def rasi_name(lang: str, r: int) -> str:
    return S.names(lang, "rashi", r)


def planet(lang: str, p: str) -> str:
    if lang == "en":
        return f"the {p}" if p in ("Sun", "Moon") else p
    return i18n.get(lang)["planet"][p]


def nak_link(i: int, lang: str = "en") -> str:
    return f'<a href="/learn/nakshatra/{S.NAK_SLUGS[i]}">{esc(nak_name(lang, i))}</a>'


def rasi_link(r: int, lang: str = "en") -> str:
    return f'<a href="/learn/rasi/{S.RASI_SLUGS[r]}">{esc(rasi_name(lang, r))}</a>'


def _list(items: list[int], link, lang: str, empty: str = "—") -> str:
    return ", ".join(link(i, lang) for i in items) if items else empty


def _padas(lang: str, padas: list[int]) -> str:
    if len(padas) == 4:
        return R_(lang, "pada_all")
    return R_(lang, "pada_one" if len(padas) == 1 else "pada_some", p=", ".join(str(p) for p in padas))


def _ordinal(k: int) -> str:
    return f"{k}{'th' if 11 <= k % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th')}"


def _pos(lang: str, x: float, end: bool = False) -> str:
    """Zodiac position as degrees within a rasi; an end exactly on a boundary is shown as 30°00′ of the sign before."""
    r = int(round(x * 3600) // (30 * 3600))
    within = x - r * 30
    if end and abs(within) < 1e-9:
        r, within = r - 1, 30.0
    return f"{S.dms(within)} {esc(rasi_name(lang, r % 12))}"


def _deity_symbol(lang: str, n: int) -> tuple[str, str]:
    return deity_symbol(lang, n, S.NAK_DEITY_SYMBOL[n])


def _rasi_symbol(lang: str, r: int) -> str:
    return rasi_symbol(lang, r, S.RASI_SYMBOL[r])


def _name_in(code: str, kind: str, i: int) -> str:
    return S.names(code, kind, i) if code != "en" else (NAKSHATRAS[i] if kind == "nakshatra" else RASHIS[i])


def _other_names(lang: str, kind: str, i: int) -> str:
    """The star's or rasi's name in every other site language, labelled."""
    return "<br>".join(f'{esc(LANG_LABEL[c])}: <span lang="{c}">{esc(_name_in(c, kind, i))}</span>'
                       for c in SITE_LANGS if c != lang)


def _index_other(lang: str, kind: str, i: int) -> str:
    """Second-name column in the index tables: Tamil / Hindi on the English page, English elsewhere."""
    if lang == "en":
        return " / ".join(f'<span lang="{c}">{esc(_name_in(c, kind, i))}</span>' for c in ("ta", "hi"))
    return esc(_name_in("en", kind, i))


def _page(s: Settings, lang: str, path: str, title: str, page_title: str, description: str, body: str,
          trail: list[tuple[str, str]], wide: bool = False) -> str:
    ld = [article_ld(s, lpath(lang, path), title, description, lang),
          breadcrumb_ld(s, [(T(lang, "home"), lpath(lang, "/")), (T(lang, "learn_h1"), lpath(lang, "/learn"))]
                        + [(n, lpath(lang, p)) for n, p in trail])]
    crumbs = " › ".join([f'<a href="/learn">{esc(T(lang, "learn_h1"))}</a>']
                        + [f'<a href="{p}">{esc(n)}</a>' for n, p in trail[:-1]])
    body = f'<article class="article ref{" wide" if wide else ""}"><p class="crumb">{crumbs}</p>{body}</article>'
    return layout(s, title, body, active="learn", path=path, lang=lang, description=description,
                  page_title=f"{page_title} | {s.site_name}", ld=ld, og_type="article")


def _disclaimer(lang: str) -> str:
    return f'<p class="small">{R_(lang, "disclaimer")}</p>'


# ------------------------------------------------------------------ nakshatras
def nakshatra_index(s: Settings, lang: str = "en") -> str:
    lang = site_lang(lang)
    rows = []
    for n in range(27):
        f = S.nak_facts(n)
        rasis = ", ".join(rasi_link(r, lang) for r, _ in f["rasis"])
        rows.append(f'<tr><th>{n + 1}</th><td>{nak_link(n, lang)}</td><td>{_index_other(lang, "nakshatra", n)}</td>'
                    f'<td>{esc(planet(lang, f["lord"]) if lang != "en" else f["lord"])}</td><td>{rasis}</td>'
                    f'<td>{esc(V(GANA, f["gana"], lang))}</td><td>{esc(V(NADI, f["nadi"], lang))}</td>'
                    f'<td>{esc(V(RAJJU, f["rajju"], lang))}</td></tr>')
    heads = "".join(f"<th>{esc(R_(lang, k))}</th>" for k in
                    ("col_nak", "col_other" if lang == "en" else "col_english", "col_lord", "col_rasi", "col_gana",
                     "col_nadi", "col_rajju"))
    body = f"""<h1>{esc(R_(lang, "naks_h1"))}</h1>
<p class="lead">{esc(R_(lang, "naks_lead"))}</p>
<p>{esc(R_(lang, "naks_p2"))}</p>
<div class="scroll"><table class="grid"><thead><tr><th>#</th>{heads}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p>{R_(lang, "naks_outro", table=TABLE_PATH)}</p>"""
    return _page(s, lang, "/learn/nakshatras", R_(lang, "naks_h1"), R_(lang, "naks_title"), R_(lang, "naks_desc"),
                 body, [(R_(lang, "naks_crumb"), "/learn/nakshatras")])


def _match_rows(lang: str, n: int, as_bride: bool) -> str:
    t = S.star_table()
    cells = [(o, t[n][o] if as_bride else t[o][n]) for o in range(27)]
    rank = {g: i for i, g in enumerate(S.GRADE_ORDER)}
    cells.sort(key=lambda c: (rank[c[1].grades[0]], -c[1].hi, -c[1].lo, c[0]))
    rows = []
    for o, c in cells:
        grade = T(lang, "or").join(V(GRADE_SHORT, g, lang) for g in c.grades)
        note = "" if c.always else R_(lang, "dep_pada")
        rows.append(f'<tr class="{GRADE_CLASS[c.grades[0]]}"><td>{nak_link(o, lang)}</td>'
                    f'<td class="num">{c.count_text} / {c.of}</td><td>{esc(grade + note)}</td></tr>')
    return "".join(rows)


def nakshatra_page(s: Settings, n: int, lang: str = "en") -> str:
    lang = site_lang(lang)
    f = S.nak_facts(n)
    name = esc(nak_name(lang, n))
    deity, symbol = (esc(x) for x in _deity_symbol(lang, n))
    lord = esc(planet(lang, f["lord"]))
    gana, nadi, rajju = (esc(V(tbl, f[k], lang)) for tbl, k in ((GANA, "gana"), (NADI, "nadi"), (RAJJU, "rajju")))
    yoni_animal, yoni_sex = f["yoni"].split(" (")
    yoni = f'{esc(V(YONI, yoni_animal, lang))} ({esc(V(SEX, "M" if yoni_sex.startswith("male") else "F", lang))})'
    rasis = "; ".join(f"{rasi_link(r, lang)} ({_padas(lang, p)})" for r, p in f["rasis"])
    span = f"{_pos(lang, f['start'])} – {_pos(lang, f['end'], end=True)}"
    bride, groom = S.matches_for(n, True), S.matches_for(n, False)
    a_name = ("an " if NAKSHATRAS[n][0] in "AEIOU" else "a ") + name if lang == "en" else name
    other = _other_names(lang, "nakshatra", n)
    h1_extra = f' <span lang="ta">({esc(f["ta"])})</span>' if lang == "en" else f" ({esc(NAKSHATRAS[n])})"
    none = R_(lang, "none_all")
    stop = "।" if lang == "hi" else "."
    body = f"""<h1>{R_(lang, "nak_h1", name=name)}{h1_extra}</h1>
<p class="lead">{R_(lang, "nak_lead", name=name, ord=_ordinal(n + 1), n=n + 1, lord=lord, deity=deity, symbol=symbol)}</p>
<table class="grid facts"><tbody>
<tr><th>{R_(lang, "f_other")}</th><td>{other}</td></tr>
<tr><th>{R_(lang, "f_span")}</th><td>{span}</td></tr>
<tr><th>{R_(lang, "col_rasi")}</th><td>{rasis}</td></tr>
<tr><th>{R_(lang, "f_lord")}</th><td>{lord if lang != "en" else f["lord"]}</td></tr>
<tr><th>{R_(lang, "f_deity")}</th><td>{deity}</td></tr>
<tr><th>{R_(lang, "f_symbol")}</th><td>{symbol}</td></tr>
<tr><th>{R_(lang, "col_gana")}</th><td>{gana}</td></tr>
<tr><th>{R_(lang, "f_yoni")}</th><td>{yoni}</td></tr>
<tr><th>{R_(lang, "col_nadi")}</th><td>{nadi}</td></tr>
<tr><th>{R_(lang, "col_rajju")}</th><td>{rajju}</td></tr>
<tr><th>{R_(lang, "f_vedha")}</th><td>{_list(f["vedha"], nak_link, lang)}</td></tr>
</tbody></table>
<p>{R_(lang, "nak_para", name=name, lord=lord, gana=gana, nadi=nadi, rajju=rajju)}</p>

<h2>{R_(lang, "h_bride", name=name, a_name=a_name)}</h2>
<p><strong>{R_(lang, "best_b")}</strong> {_list(bride["best"], nak_link, lang, none)}{stop}</p>
<p><strong>{R_(lang, "some")}</strong> {_list(bride["some"], nak_link, lang)}{stop}</p>
<p><strong>{R_(lang, "avoid")}</strong> {_list(bride["avoid"], nak_link, lang)}{stop}</p>
<details><summary>{R_(lang, "sum_b", name=name, a_name=a_name)}</summary>
<div class="scroll"><table class="grid match-list"><thead><tr><th>{R_(lang, "col_groom_star")}</th>
<th class="num">{R_(lang, "col_poruthams")}</th><th>{R_(lang, "col_result")}</th></tr></thead>
<tbody>{_match_rows(lang, n, True)}</tbody></table></div></details>

<h2>{R_(lang, "h_groom", name=name, a_name=a_name)}</h2>
<p><strong>{R_(lang, "best_g")}</strong> {_list(groom["best"], nak_link, lang, none)}{stop}</p>
<p><strong>{R_(lang, "some")}</strong> {_list(groom["some"], nak_link, lang)}{stop}</p>
<p><strong>{R_(lang, "avoid")}</strong> {_list(groom["avoid"], nak_link, lang)}{stop}</p>
<details><summary>{R_(lang, "sum_g", name=name, a_name=a_name)}</summary>
<div class="scroll"><table class="grid match-list"><thead><tr><th>{R_(lang, "col_bride_star")}</th>
<th class="num">{R_(lang, "col_poruthams")}</th><th>{R_(lang, "col_result")}</th></tr></thead>
<tbody>{_match_rows(lang, n, False)}</tbody></table></div></details>
{_disclaimer(lang)}
<p class="cta"><a class="button primary" href="/match">{R_(lang, "cta_full")}</a>
<a class="button" href="{TABLE_PATH}">{R_(lang, "cta_table")}</a></p>
<p class="pager">← {nak_link((n - 1) % 27, lang)} · <a href="/learn/nakshatras">{R_(lang, "all_naks")}</a> ·
{nak_link((n + 1) % 27, lang)} →</p>"""
    plain = nak_name(lang, n)
    desc = R_(lang, "nak_desc", name=plain, ta=f["ta"], lord=planet(lang, f["lord"]) if lang != "en" else f["lord"],
              rasis=", ".join(rasi_name(lang, r) for r, _ in f["rasis"]), gana=V(GANA, f["gana"], lang),
              nadi=V(NADI, f["nadi"], lang), rajju=V(RAJJU, f["rajju"], lang))
    return _page(s, lang, f"/learn/nakshatra/{S.NAK_SLUGS[n]}", R_(lang, "nak_h1", name=plain),
                 R_(lang, "nak_title", name=plain, ta=f["ta"]), desc, body,
                 [(R_(lang, "naks_crumb"), "/learn/nakshatras"), (plain, f"/learn/nakshatra/{S.NAK_SLUGS[n]}")])


# ------------------------------------------------------------------ rasis
def rasi_index(s: Settings, lang: str = "en") -> str:
    lang = site_lang(lang)
    rows = []
    for r in range(12):
        f = S.rasi_facts(r)
        naks = ", ".join(nak_link(n, lang) for n, _ in f["naks"])
        lord = f["lord"] if lang == "en" else planet(lang, f["lord"])
        rows.append(f'<tr><th>{r + 1}</th><td>{rasi_link(r, lang)}</td><td>{f["english"]}</td>'
                    + (f'<td>{_index_other(lang, "rashi", r)}</td>' if lang == "en" else "")
                    + f'<td>{esc(lord)}</td>'
                    f'<td>{esc(V(ELEMENT, f["element"], lang))}</td><td>{naks}</td></tr>')
    heads = "".join(f"<th>{esc(R_(lang, k))}</th>" for k in
                    ("col_rasi", "col_english") + (("col_other",) if lang == "en" else ()) + ("col_lord", "col_element", "col_naks"))
    body = f"""<h1>{esc(R_(lang, "rasis_h1"))}</h1>
<p class="lead">{esc(R_(lang, "rasis_lead"))}</p>
<div class="scroll"><table class="grid"><thead><tr><th>#</th>{heads}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p>{R_(lang, "rasis_outro")}</p>"""
    return _page(s, lang, "/learn/rasis", R_(lang, "rasis_h1"), R_(lang, "rasis_title"), R_(lang, "rasis_desc"), body,
                 [(R_(lang, "rasis_crumb"), "/learn/rasis")])


def rasi_page(s: Settings, r: int, lang: str = "en") -> str:
    lang = site_lang(lang)
    f = S.rasi_facts(r)
    name = esc(rasi_name(lang, r))
    lord = esc(planet(lang, f["lord"]))
    element = esc(V(ELEMENT, f["element"], lang))
    quality = esc(V(QUALITY, f["quality"], lang))
    naks = "; ".join(f"{nak_link(n, lang)} ({_padas(lang, p)})" for n, p in f["naks"])
    pl = (lambda p: p) if lang == "en" else (lambda p: planet(lang, p))
    strength = "; ".join(x for x in (
        R_(lang, "exalted", p=esc(pl(f["exalted"]))) if f["exalted"] else "",
        R_(lang, "debilitated", p=esc(pl(f["debilitated"]))) if f["debilitated"] else "") if x) or "—"
    lead_quality = f["quality"].split(" (")[0].lower() if lang == "en" else quality
    lead_element = f["element"].lower() if lang == "en" else element
    body = f"""<h1>{R_(lang, "rasi_h1", name=name, english=f["english"])}</h1>
<p class="lead">{R_(lang, "rasi_lead", name=name, ord=_ordinal(r + 1), n=r + 1, a=r * 30, b=r * 30 + 30, lord=lord,
                    symbol=esc(_rasi_symbol(lang, r)), element=lead_element, quality=lead_quality)}</p>
<table class="grid facts"><tbody>
<tr><th>{R_(lang, "f_western")}</th><td>{esc(f["english"])}</td></tr>
<tr><th>{R_(lang, "f_other_r")}</th><td>{_other_names(lang, "rashi", r)}</td></tr>
<tr><th>{R_(lang, "col_lord")}</th><td>{lord if lang != "en" else f["lord"]}</td></tr>
<tr><th>{R_(lang, "f_el_q")}</th><td>{element} / {quality}</td></tr>
<tr><th>{R_(lang, "f_strength")}</th><td>{strength}</td></tr>
<tr><th>{R_(lang, "col_naks")}</th><td>{naks}</td></tr>
<tr><th>{R_(lang, "f_varna")}</th><td>{esc(V(VARNA, f["varna"], lang))}</td></tr>
<tr><th>{R_(lang, "f_vashya")}</th><td>{esc(" / ".join(V(VASHYA, x, lang) for x in f["vashya"].split(" / ")))}</td></tr>
</tbody></table>
<h2>{R_(lang, "h_rasi_match", name=name)}</h2>
<ul>
<li>{R_(lang, "li_rasi", name=name, list=_list(f["rasi_good"], rasi_link, lang))}</li>
<li>{R_(lang, "li_vasya", name=name, list=_list(f["vasya"], rasi_link, lang))}</li>
<li>{R_(lang, "li_bhakoot", name=name, list=_list(f["bhakoot_bad"], rasi_link, lang))}</li>
<li>{R_(lang, "li_lord", lord=lord)}</li>
</ul>
{_disclaimer(lang)}
<p class="pager">← {rasi_link((r - 1) % 12, lang)} · <a href="/learn/rasis">{R_(lang, "all_rasis")}</a> ·
{rasi_link((r + 1) % 12, lang)} →</p>"""
    plain = rasi_name(lang, r)
    desc = R_(lang, "rasi_desc", name=plain, english=f["english"], ta=f["ta"],
              lord=f["lord"] if lang == "en" else planet(lang, f["lord"]),
              element=f["element"].lower() if lang == "en" else V(ELEMENT, f["element"], lang),
              naks=", ".join(nak_name(lang, n) for n, _ in f["naks"]))
    return _page(s, lang, f"/learn/rasi/{S.RASI_SLUGS[r]}", R_(lang, "rasi_h1", name=plain, english=f["english"]),
                 R_(lang, "rasi_title", name=plain, english=f["english"]), desc, body,
                 [(R_(lang, "rasis_crumb"), "/learn/rasis"), (plain, f"/learn/rasi/{S.RASI_SLUGS[r]}")])


# ------------------------------------------------------------------ star-to-star table
ABBR = ["Ash", "Bha", "Kri", "Roh", "Mri", "Ard", "Pun", "Pus", "Asl", "Mag", "PPh", "UPh", "Has", "Chi", "Swa",
        "Vis", "Anu", "Jye", "Mul", "PAs", "UAs", "Shr", "Dha", "Sha", "PBh", "UBh", "Rev"]


def porutham_table(s: Settings, lang: str = "en") -> str:
    lang = site_lang(lang)
    t = S.star_table()
    # column heads: English abbreviations, or numbers (with the full name on hover) where abbreviating would break
    # the script
    head = "".join(f'<th scope="col"><a href="/learn/nakshatra/{S.NAK_SLUGS[b]}" title="{esc(nak_name(lang, b))}">'
                   f'{ABBR[b] if lang == "en" else b + 1}</a></th>' for b in range(27))
    rows = []
    for g in range(27):
        cells = []
        for b in range(27):
            c = t[g][b]
            cls = GRADE_CLASS[c.grades[0]] + ("" if c.always else " mixed")
            text = "✕" if c.always == "REJECTED" else c.count_text
            tip = R_(lang, "cell", g=nak_name(lang, g), b=nak_name(lang, b),
                     grades=T(lang, "or").join(V(GRADE_SHORT, x, lang) for x in c.grades))
            cells.append(f'<td class="{cls}" title="{esc(tip)}">{text}</td>')
        label = nak_link(g, lang) if lang == "en" else f"{g + 1}. {nak_link(g, lang)}"
        rows.append(f'<tr><th scope="row">{label}</th>{"".join(cells)}</tr>')
    legend = "".join(f'<span class="{GRADE_CLASS[g]}">{esc(V(GRADE, g, lang))}</span>' for g in S.GRADE_ORDER[:3])
    how = "".join(f"<li>{R_(lang, k)}</li>" for k in ("how1", "how2", "how3", "how4"))
    body = f"""<h1>{esc(R_(lang, "tbl_h1"))}</h1>
<p class="lead">{esc(R_(lang, "tbl_lead"))}</p>
<p class="legend">{legend} <span class="g-rj">{esc(R_(lang, "lg_rej"))}</span>
<span class="mixed g-md">{esc(R_(lang, "lg_mixed"))}</span></p>
<div class="scroll"><table class="grid star-table"><thead><tr><th scope="col">{esc(R_(lang, "corner"))}</th>{head}</tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<h2>{esc(R_(lang, "how_h"))}</h2>
<ul>{how}</ul>
{_disclaimer(lang)}"""
    return _page(s, lang, TABLE_PATH, R_(lang, "tbl_h1"), R_(lang, "tbl_title"), R_(lang, "tbl_desc"), body,
                 [(R_(lang, "tbl_h1"), TABLE_PATH)], wide=True)


def sitemap_paths() -> list[str]:
    """Language-neutral paths of the reference pages."""
    return (["/learn/nakshatras", "/learn/rasis", TABLE_PATH]
            + [f"/learn/nakshatra/{x}" for x in S.NAK_SLUGS] + [f"/learn/rasi/{x}" for x in S.RASI_SLUGS])
