"""Site languages: URL prefixes, interface text and the astrology vocabulary used on the content pages.

English pages live at /..., Tamil at /ta/... and Hindi at /hi/... . The forms themselves stay in English for now;
everything around them (navigation, headings, articles, reference pages, results) follows the page language.
Tamil and Hindi text is a draft for native-speaker review.
"""
from __future__ import annotations

import re

SITE_LANGS = ("en", "ta", "hi", "te", "ml", "kn")
BASE_LANGS = ("en", "ta", "hi")      # the tuples in this file hold these three, in this order
LANG_LABEL = {"en": "English", "ta": "தமிழ்", "hi": "हिन्दी", "te": "తెలుగు", "ml": "മലയാളം", "kn": "ಕನ್ನಡ"}
LOCALIZED = re.compile(r"^/(?:$|horoscope$|match$|dasha$|learn(?:/.*)?$|upcoming$|credits$|privacy$|terms$)")


def prefix(lang: str) -> str:
    return "" if lang == "en" else f"/{lang}"


def lpath(lang: str, path: str) -> str:
    """Logical path (/learn/x) → the page's URL in a language (/ta/learn/x)."""
    if lang == "en":
        return path
    return prefix(lang) if path == "/" else prefix(lang) + path


_HREF = re.compile(r'(?<!hreflang="[a-z]{2}" )href="(/[^"?#]*)([?#][^"]*)?"')


def localize_links(html: str, lang: str) -> str:
    """Point internal links at the same language. Links marked with hreflang (the language switch) are left alone."""
    if lang == "en":
        return html

    def sub(m):
        path, rest = m.group(1), m.group(2) or ""
        return f'href="{lpath(lang, path)}{rest}"' if LOCALIZED.match(path) else m.group(0)
    return _HREF.sub(sub, html)


def split_lang(path: str) -> tuple[str, str]:
    """/ta/learn/x → ("ta", "/learn/x")"""
    for code in SITE_LANGS[1:]:
        if path == f"/{code}" or path.startswith(f"/{code}/"):
            return code, path[len(code) + 1:] or "/"
    return "en", path


# ------------------------------------------------------------------ interface text: key → (en, ta, hi)
_T: dict[str, tuple[str, str, str]] = {
    # chrome
    "nav_horoscope": ("Horoscope", "ஜாதகம்", "कुंडली"),
    "nav_match": ("Matching", "திருமணப் பொருத்தம்", "कुंडली मिलान"),
    "nav_learn": ("Learn", "கற்க", "जानें"),
    "nav_credits": ("Credits", "நன்றி", "आभार"),
    "skip": ("Skip to content", "உள்ளடக்கத்திற்குச் செல்ல", "सामग्री पर जाएँ"),
    "foot_disclaimer": ("For guidance only — consult an astrologer before taking decisions.",
                        "வழிகாட்டுதலுக்கு மட்டுமே — முடிவெடுக்கும் முன் ஜோதிடரை அணுகவும்.",
                        "केवल मार्गदर्शन के लिए — निर्णय लेने से पहले ज्योतिषी से सलाह लें।"),
    "foot_privacy": ("Privacy", "தனியுரிமை", "गोपनीयता"),
    "foot_terms": ("Terms", "விதிமுறைகள்", "नियम"),
    "foot_upcoming": ("Coming soon", "விரைவில்", "जल्द आ रहा है"),
    "foot_attrib": ("Place data © {geonames} (CC BY 4.0). Calculations use the Swiss Ephemeris © Astrodienst AG.",
                    "இட விவரங்கள் © {geonames} (CC BY 4.0). கணக்கீடுகள்: Swiss Ephemeris © Astrodienst AG.",
                    "स्थान डेटा © {geonames} (CC BY 4.0)। गणना: Swiss Ephemeris © Astrodienst AG।"),
    "consent": ("We use {what}, which use cookies. Your birth details are never shared with Google.",
                "நாங்கள் {what} பயன்படுத்துகிறோம்; இவை குக்கீகளைப் பயன்படுத்துகின்றன. உங்கள் பிறப்பு விவரங்கள் "
                "Google-உடன் ஒருபோதும் பகிரப்படுவதில்லை.",
                "हम {what} का उपयोग करते हैं, जो कुकीज़ का उपयोग करते हैं। आपके जन्म विवरण कभी Google के साथ साझा "
                "नहीं किए जाते।"),
    "consent_ads": ("ads from Google AdSense", "Google AdSense விளம்பரங்கள்", "Google AdSense विज्ञापनों"),
    "consent_ga": ("Google Analytics to count visits", "வருகைகளைக் கணக்கிட Google Analytics",
                   "विज़िट गिनने के लिए Google Analytics"),
    "and": (" and ", " மற்றும் ", " और "),
    "or": (" or ", " அல்லது ", " या "),
    "home": ("Home", "முகப்பு", "मुखपृष्ठ"),
    "language": ("Language", "மொழி", "भाषा"),
    "theme": ("Theme", "தோற்றம்", "थीम"),
    "theme_auto": ("Device Setting", "சாதன அமைப்பு", "डिवाइस के अनुसार"),
    "theme_light": ("Light", "வெளிர்", "हल्का"),
    "theme_dark": ("Dark", "இருள்", "गहरा"),

    # home
    # Page copy speaks to quality; "free" is kept for page titles and search descriptions only (PAGE_META)
    "home_h1": ("Horoscope, marriage matching and dasha — the traditional way", "பாரம்பரிய முறையில் ஜாதகம், திருமணப் பொருத்தம், தசை புக்தி", "पारंपरिक पद्धति से कुंडली, कुंडली मिलान और दशा"),
    "home_intro": ("South Indian Rasi and Navamsa charts calculated with the Swiss Ephemeris, and matching by Porutham and Ashtakoota — checked against an astrologer's own results. Also Chevvai/Manglik dosham under South and North Indian rules, and Vimshottari dasha down to prana. Your horoscope comes as a neatly formatted page in English, தமிழ், తెలుగు, മലയാളം, ಕನ್ನಡ or हिन्दी, and nothing you enter is ever stored.", "Swiss Ephemeris கணக்கீட்டில் தென்னிந்திய முறை ராசி, நவாம்சக் கட்டங்கள்; 10 பொருத்தம் (வர்ணம், நாடி சேர்த்து 12), அஷ்டகூடம் (36 புள்ளிகள்) — ஜோதிடரின் கணிப்புகளுடன் சரிபார்க்கப்பட்டவை. தென்–வட இந்திய முறைகளில் செவ்வாய் தோஷமும், பிராணம் வரை விம்சோத்தரி தசையும் உண்டு. உங்கள் ஜாதகம் தமிழிலேயே நேர்த்தியான வடிவில் கிடைக்கும்; நீங்கள் உள்ளிடும் விவரங்கள் எதுவும் சேமிக்கப்படுவதில்லை.", "Swiss Ephemeris की सटीक गणना से दक्षिण भारतीय शैली के राशि और नवांश चार्ट, और अष्टकूट गुण मिलान (36 गुण) व 12 पोरुथम जाँच — ज्योतिषी के परिणामों से मिलाकर परखी गई। साथ ही दक्षिण व उत्तर भारतीय नियमों से मांगलिक दोष, और प्राण स्तर तक विंशोत्तरी दशा। आपकी कुंडली हिंदी में सुव्यवस्थित, सुंदर रूप में मिलती है, और आपकी दी हुई कोई भी जानकारी सहेजी नहीं जाती।"),
    "card_h": ("Horoscope", "ஜாதகம் கணிக்க", "कुंडली बनाएँ"),
    "card_h_desc": ("Rasi and Navamsa charts with your family and personal details, laid out as an elegant "
                    "horoscope you can print or share.",
                    "பிறந்த தேதி, நேரம், ஊர் கொடுத்தால் ராசி, நவாம்சக் கட்டங்கள், கோத்திரம், குடும்ப விவரங்களுடன் "
                    "நேர்த்தியாக வடிவமைக்கப்பட்ட ஜாதகம்.",
                    "राशि और नवांश चार्ट, परिवार और व्यक्तिगत विवरण के साथ — सुंदर ढंग से सजी कुंडली, जिसे आप प्रिंट "
                    "या साझा कर सकते हैं।"),
    "card_m": ("Marriage Matching", "திருமணப் பொருத்தம்", "कुंडली मिलान"),
    "card_m_desc": ("Ashtakoota (36 gunas) and Porutham for a bride and groom, with both Rasi charts.",
                    "மணமகள், மணமகன் இருவரின் பிறப்பு விவரங்களைக் கொண்டு 12 பொருத்தங்களும் அஷ்டகூட மதிப்பெண்ணும், "
                    "இருவரின் ராசிக் கட்டங்களுடன்.",
                    "वर और वधू के जन्म विवरण से 36 में से गुण, नाड़ी, भकूट और गण दोष, 12 पोरुथम और दोनों के राशि "
                    "चार्ट।"),
    "card_table": ("Nakshatra Porutham Table", "நட்சத்திரப் பொருத்த அட்டவணை", "नक्षत्र मिलान तालिका"),
    "card_table_desc": ("Every bride's star against every groom's star — how many poruthams match, and which pairs "
                        "are rejected.",
                        "27 நட்சத்திரங்களுக்கும் — எத்தனை பொருத்தம், எந்த ஜோடிகள் பொருந்தாது.",
                        "सभी 27 नक्षत्रों के जोड़ों के लिए — कितने पोरुथम मिलते हैं, और कौन-से जोड़े अस्वीकार हैं।"),
    "card_learn": ("Learn", "கற்க", "जानें"),
    "card_learn_desc": ("Short guides to ayanamsa, Rasi and Navamsa charts, Ashtakoota, Porutham, Rajju and Nadi, "
                        "and KP astrology.",
                        "அயனாம்சம், ராசி–நவாம்சக் கட்டங்கள், அஷ்டகூடம், பொருத்தம், ரஜ்ஜு–நாடி, KP ஜோதிடம் பற்றிய "
                        "சுருக்கமான விளக்கங்கள்.",
                        "अयनांश, राशि और नवांश चार्ट, अष्टकूट, पोरुथम, रज्जु और नाड़ी, और KP ज्योतिष पर छोटे लेख।"),
    "stars_h": ("The 27 nakshatras", "27 நட்சத்திரங்கள்", "27 नक्षत्र"),
    "stars_intro": ("Each star's lord, rasi, gana, nadi, rajju and best matches:",
                    "ஒவ்வொரு நட்சத்திரத்தின் அதிபதி, ராசி, கணம், நாடி, ரஜ்ஜு மற்றும் சிறந்த பொருத்தங்கள்:",
                    "हर नक्षत्र का स्वामी, राशि, गण, नाड़ी, रज्जु और सबसे अच्छे मिलान:"),
    "rasis_h": ("The 12 rasis", "12 ராசிகள்", "12 राशियाँ"),

    # form pages (the forms themselves stay in English)
    "hform_h1": ("Create your horoscope (jathagam)", "உங்கள் ஜாதகம் கணிக்க", "अपनी कुंडली (जन्मपत्री) बनाएँ"),
    "hform_lead": (
        "Fill in the birth details — only the starred fields are required. You get a well-formatted horoscope with "
        "the Rasi and Navamsa charts and the details you choose, in English, Tamil, Telugu, Malayalam, Kannada or "
        "Hindi.",
        "பிறப்பு விவரங்களை நிரப்பவும்; நட்சத்திரக் குறியிட்ட புலங்கள் மட்டுமே கட்டாயம். நீங்கள் தேர்ந்தெடுக்கும் "
        "விவரங்களுடன் ராசி, நவாம்சக் கட்டங்கள் கொண்ட நேர்த்தியான ஜாதகம் கிடைக்கும் — தமிழ் உட்பட ஆறு மொழிகளில்.",
        "जन्म विवरण भरें; केवल तारांकित फ़ील्ड ज़रूरी हैं। आपको चुने गए विवरणों के साथ राशि और नवांश चार्ट वाली "
        "सुव्यवस्थित कुंडली मिलती है — हिंदी सहित छह भाषाओं में।"),
    "mform_h1": ("Marriage matching (Porutham and Guna Milan)", "திருமணப் பொருத்தம் (10 பொருத்தம், அஷ்டகூடம்)",
                 "कुंडली मिलान (गुण मिलान और पोरुथम)"),
    "mform_lead": (
        'Enter the bride\'s details on the left and the groom\'s on the right. You get the 12 poruthams, the '
        'Ashtakoota score out of 36, Chevvai/Manglik dosham, Rahu–Ketu, and both Rasi charts. Only know the birth stars? See the '
        '<a href="/learn/nakshatra-porutham-table">nakshatra porutham table</a>.',
        'மணமகளின் விவரங்களை இடப்புறமும் மணமகனின் விவரங்களை வலப்புறமும் உள்ளிடவும். 12 பொருத்தங்கள், 36-க்கு '
        'அஷ்டகூட மதிப்பெண், செவ்வாய் தோஷம், ராகு–கேது, இருவரின் ராசிக் கட்டங்கள் கிடைக்கும். நட்சத்திரம் மட்டும் தெரியுமா? '
        '<a href="/learn/nakshatra-porutham-table">நட்சத்திரப் பொருத்த அட்டவணையைப்</a> பார்க்கவும்.',
        'वधू का विवरण बाईं ओर और वर का दाईं ओर भरें। आपको 12 पोरुथम, 36 में से अष्टकूट गुण, मांगलिक दोष, राहु–केतु और दोनों के राशि चार्ट '
        'मिलेंगे। केवल जन्म नक्षत्र पता है? <a href="/learn/nakshatra-porutham-table">नक्षत्र मिलान तालिका</a> '
        'देखें।'),
    "form_note": ("",
                  "படிவம் ஆங்கிலத்தில் உள்ளது; அச்சு மொழியாகத் தமிழ் ஏற்கெனவே தேர்ந்தெடுக்கப்பட்டுள்ளது.",
                  "फ़ॉर्म अंग्रेज़ी में है; प्रिंट की भाषा के रूप में हिंदी पहले से चुनी गई है।"),

    # result pages
    "res_h": ("Your horoscope", "உங்கள் ஜாதகம்", "आपकी कुंडली"),
    "res_d": ("Dasha result", "தசை முடிவு", "दशा परिणाम"),
    "nav_dasha": ("Dasha", "தசை", "दशा"),
    "dform_h1": ("Vimshottari dasha calculator", "விம்சோத்தரி தசை கணிப்பு", "विंशोत्तरी दशा गणना"),
    "dform_lead": (
        "Enter the birth details to see every dasha period from birth — mahadasha, bhukti, antara, sookshma and "
        "prana — with the running period marked. Uses the KP ayanamsa unless you choose Lahiri.",
        "பிறப்பு விவரங்களை உள்ளிட்டு, பிறப்பு முதல் எல்லாத் தசைக் காலங்களையும் — மகா தசை, புக்தி, அந்தரம், "
        "சூட்சுமம், பிராணம் — நடப்புக் காலம் குறிக்கப்பட்டதாகப் பாருங்கள். லாகிரி தேர்ந்தெடுக்காவிட்டால் KP அயனாம்சம் "
        "பயன்படும்.",
        "जन्म विवरण भरें और जन्म से हर दशा अवधि देखें — महादशा, अंतर्दशा, प्रत्यंतर, सूक्ष्म और प्राण — चालू अवधि "
        "चिह्नित के साथ। लाहिड़ी न चुनें तो KP अयनांश लिया जाता है।"),
    "cta_dasha_q": ("Looking for the dasha periods?", "தசைக் காலங்கள் வேண்டுமா?", "दशा अवधियाँ देखनी हैं?"),
    "cta_dasha_text": (
        "See every mahadasha, bhukti, antara, sookshma and prana for this birth, with the running period marked. "
        "The details you entered come along.",
        "இந்தப் பிறப்புக்கான எல்லா மகா தசை, புக்தி, அந்தரம், சூட்சுமம், பிராணம் — நடப்புக் காலம் குறிக்கப்பட்டு. "
        "நீங்கள் உள்ளிட்ட விவரங்கள் அப்படியே எடுத்துச் செல்லப்படும்.",
        "इस जन्म की हर महादशा, अंतर्दशा, प्रत्यंतर, सूक्ष्म और प्राण — चालू अवधि चिह्नित। आपके भरे विवरण साथ चले "
        "जाएँगे।"),
    "cta_dasha_btn": ("Calculate Dasha →", "தசை கணிப்புக்குச் செல் →", "दशा कैलकुलेटर खोलें →"),
    "cta_h_q": ("Looking for the full horoscope?", "முழு ஜாதகம் வேண்டுமா?", "पूरी कुंडली चाहिए?"),
    "cta_h_text": (
        "Rasi and Navamsa charts, family and personal details and doshas, neatly formatted to print. "
        "The details you entered come along.",
        "ராசி, நவாம்சக் கட்டங்கள், குடும்ப, சுய விவரங்கள், தோஷங்கள் — அச்சிட அழகாக வடிவமைக்கப்பட்டவை. நீங்கள் "
        "உள்ளிட்ட விவரங்கள் அப்படியே எடுத்துச் செல்லப்படும்.",
        "राशि और नवांश चार्ट, पारिवारिक व व्यक्तिगत विवरण और दोष — प्रिंट के लिए सुव्यवस्थित। आपके भरे विवरण साथ "
        "चले जाएँगे।"),
    "cta_h_btn": ("Create Horoscope →", "ஜாதகம் உருவாக்கு →", "कुंडली बनाएँ →"),
    "hl_h": ("Simple Tools, Built for Privacy",
        "எளிய கருவிகள், உங்கள் தனியுரிமைக்கு முன்னுரிமை",
        "आसान टूल, आपकी निजता सबसे पहले"),
    "hl_easy_t": ("Easy to Use",
        "எளிதாகப் பயன்படுத்தலாம்",
        "इस्तेमाल में आसान"),
    "hl_easy": ("Enter the birth details and get the result in seconds — no sign-up, no app to install.",
        "பிறப்பு விவரங்களை உள்ளிட்டால் சில நொடிகளில் முடிவு — பதிவு தேவையில்லை, செயலி நிறுவத் தேவையில்லை.",
        "जन्म विवरण भरें और कुछ ही पलों में परिणाम पाएँ — न साइन-अप, न कोई ऐप इंस्टॉल।"),
    "hl_private_t": ("Private by Design",
        "தனியுரிமை முதன்மை",
        "निजता सबसे पहले"),
    "hl_private": ("Nothing you enter is stored — no accounts, no database. Names and birth details are used only to draw your page.",
        "நீங்கள் உள்ளிடுவது எதுவும் சேமிக்கப்படுவதில்லை — கணக்கு இல்லை, தரவுத்தளம் இல்லை. பெயரும் பிறப்பு விவரங்களும் உங்கள் பக்கத்தை உருவாக்க மட்டுமே பயன்படும்.",
        "आपकी दी हुई कोई जानकारी सहेजी नहीं जाती — न खाता, न डेटाबेस। नाम और जन्म विवरण केवल आपका पृष्ठ बनाने में उपयोग होते हैं।"),
    "hl_lang_t": ("In Your Language",
        "உங்கள் மொழியில்",
        "आपकी भाषा में"),
    "hl_lang": ("Tamil, Telugu, Malayalam, Kannada, Hindi and English — on screen and on the printout.",
        "தமிழ், தெலுங்கு, மலையாளம், கன்னடம், இந்தி, ஆங்கிலம் — திரையிலும் அச்சிலும்.",
        "हिंदी, तमिल, तेलुगु, मलयालम, कन्नड़ और अंग्रेज़ी — स्क्रीन पर भी, प्रिंट में भी।"),
    "hl_acc_t": ("Carefully Calculated",
        "துல்லியமான கணிப்பு",
        "सटीक गणना"),
    "hl_acc": ("Swiss Ephemeris positions with Lahiri or KP ayanamsa; charts and matching checked against an astrologer's results.",
        "Swiss Ephemeris கிரக நிலைகள், லாகிரி அல்லது KP அயனாம்சம்; கட்டங்களும் பொருத்தமும் ஜோதிடரின் கணிப்புகளுடன் சரிபார்க்கப்பட்டவை.",
        "Swiss Ephemeris से ग्रह स्थिति, लाहिड़ी या KP अयनांश; चार्ट और मिलान ज्योतिषी के परिणामों से परखे गए।"),
    "form_private": ("Private: nothing you enter is saved, and no account is needed.",
        "தனியுரிமை: நீங்கள் உள்ளிடுவது எதுவும் சேமிக்கப்படாது; கணக்கு தேவையில்லை.",
        "निजी: आपकी भरी जानकारी सहेजी नहीं जाती, और खाते की ज़रूरत नहीं।"),
    "card_d": ("Vimshottari Dasha", "விம்சோத்தரி தசை", "विंशोत्तरी दशा"),
    "card_d_desc": ("Every dasha period from birth — mahadasha down to prana — with dates, time left and the "
                    "running period marked.",
                    "பிறப்பு முதல் எல்லாத் தசைக் காலங்களும் — மகா தசை முதல் பிராணம் வரை — தேதிகள், மீதமுள்ள காலம், "
                    "நடப்புக் காலத்துடன்.",
                    "जन्म से हर दशा अवधि — महादशा से प्राण तक — तिथियों, शेष समय और चालू अवधि के साथ।"),
    "res_m": ("Matching result", "பொருத்த முடிவு", "मिलान परिणाम"),
    "print": ("Print", "அச்சிடு", "प्रिंट करें"),
    "edit": ("Edit Details", "விவரங்களைத் திருத்த", "विवरण बदलें"),
    "again": ("Start Again", "புதிதாகத் தொடங்க", "फिर से शुरू करें"),
    "print_hint": ("Print on A5 paper with default margins and “Background graphics” on.",
                   "A5 தாளில், இயல்புநிலை ஓரங்களுடன், “Background graphics” இயக்கி அச்சிடவும்.",
                   "A5 कागज़ पर, सामान्य मार्जिन और “Background graphics” चालू रखकर प्रिंट करें।"),

    # learn
    "learn_h1": ("Learn", "கற்க", "जानें"),
    "learn_lead": ("Short guides to the charts and matching methods used on {site}.",
                   "{site}-இல் பயன்படுத்தப்படும் கட்டங்கள், பொருத்த முறைகள் பற்றிய சுருக்கமான விளக்கங்கள்.",
                   "{site} पर इस्तेमाल होने वाले चार्ट और मिलान के तरीकों पर छोटे लेख।"),
    "guides": ("Guides", "விளக்கங்கள்", "लेख"),
    "reference": ("Reference", "குறிப்புகள்", "संदर्भ"),
    "ref_table_desc": ("Porutham for every pair of birth stars, at a glance.",
                       "ஒவ்வொரு நட்சத்திர ஜோடிக்கும் பொருத்தம், ஒரே பார்வையில்.",
                       "हर नक्षत्र जोड़े का पोरुथम, एक नज़र में।"),
    "ref_naks_desc": ("Each birth star's lord, rasi, gana, yoni, nadi, rajju and best matches.",
                      "ஒவ்வொரு நட்சத்திரத்தின் அதிபதி, ராசி, கணம், யோனி, நாடி, ரஜ்ஜு, சிறந்த பொருத்தங்கள்.",
                      "हर नक्षत्र का स्वामी, राशि, गण, योनि, नाड़ी, रज्जु और सबसे अच्छे मिलान।"),
    "ref_rasis_desc": ("Each Moon sign's lord, element, nakshatras and matching rules.",
                       "ஒவ்வொரு ராசியின் அதிபதி, தத்துவம், நட்சத்திரங்கள், பொருத்த விதிகள்.",
                       "हर चंद्र राशि का स्वामी, तत्व, नक्षत्र और मिलान के नियम।"),
    "more_guides": ("More guides", "மேலும் விளக்கங்கள்", "और लेख"),
    "cta_h": ("Create Horoscope", "ஜாதகம் கணிக்க", "कुंडली बनाएँ"),
    "cta_m": ("Check Matching", "பொருத்தம் பார்க்க", "मिलान देखें"),
    "guidance": ("For guidance only. Please consult an astrologer before taking decisions.",
                 "இது வழிகாட்டுதலுக்கு மட்டுமே. முடிவெடுக்கும் முன் ஜோதிடரை அணுகவும்.",
                 "यह केवल मार्गदर्शन के लिए है। निर्णय लेने से पहले ज्योतिषी से सलाह लें।"),

    # coming soon
    "up_h1": ("Coming soon", "விரைவில் வருபவை", "जल्द आ रहा है"),
    "up_lead": ("What we are working on for {site}. Features appear only after their results have been checked "
                "against an astrologer's.",
                "{site}-இல் நாங்கள் தற்போது உருவாக்கிவருபவை. ஒவ்வொரு வசதியும் அதன் முடிவுகள் ஜோதிடரின் "
                "முடிவுகளுடன் சரிபார்க்கப்பட்ட பிறகே வெளியிடப்படும்.",
                "{site} पर हम जिन सुविधाओं पर काम कर रहे हैं। हर सुविधा तभी आएगी जब उसके परिणाम किसी ज्योतिषी के "
                "परिणामों से जाँच लिए जाएँगे।"),
    "st_review": ("In review", "பரிசீலனையில்", "समीक्षा में"),
    "st_planned": ("Planned", "திட்டமிடப்பட்டது", "योजना में"),
    "st_exploring": ("Exploring", "ஆராய்ச்சியில்", "विचाराधीन"),

    # credits / privacy / terms / errors
    "credits_h1": ("Credits", "நன்றி", "आभार"),
    "agpl": ("This site is free software under the GNU Affero General Public License v3.",
             "இந்தத் தளம் GNU Affero General Public License v3 உரிமத்தின் கீழ் கட்டற்ற மென்பொருள்.",
             "यह साइट GNU Affero General Public License v3 के तहत मुक्त सॉफ़्टवेयर है।"),
    "get_source": ("Get the source code", "மூலக் குறியீட்டைப் பெற", "सोर्स कोड प्राप्त करें"),
    "thanks": ("Built with these projects and data sources — thank you to their authors.",
               "இந்தத் திட்டங்கள், தரவு மூலங்களைக் கொண்டு உருவாக்கப்பட்டது — அவற்றின் படைப்பாளிகளுக்கு நன்றி.",
               "यह साइट इन परियोजनाओं और डेटा स्रोतों से बनी है — इनके रचनाकारों को धन्यवाद।"),
    "col_project": ("Project", "திட்டம்", "परियोजना"),
    "col_licence": ("Licence", "உரிமம்", "लाइसेंस"),
    "col_use": ("Used for", "பயன்பாடு", "उपयोग"),
    "rules_note": ("Matching rules follow traditional Ashtakoota and South Indian Porutham practice; the exact tables "
                   "are in the source code ({code}).",
                   "பொருத்த விதிகள் பாரம்பரிய அஷ்டகூட, தென்னிந்தியப் பொருத்த முறைகளைப் பின்பற்றுகின்றன; சரியான "
                   "அட்டவணைகள் மூலக் குறியீட்டில் ({code}) உள்ளன.",
                   "मिलान के नियम पारंपरिक अष्टकूट और दक्षिण भारतीय पोरुथम पद्धति पर आधारित हैं; सटीक तालिकाएँ "
                   "सोर्स कोड ({code}) में हैं।"),
    "terms_h1": ("Terms of use", "பயன்பாட்டு விதிமுறைகள்", "उपयोग की शर्तें"),
    "source_code": ("source code", "மூலக் குறியீடு", "सोर्स कोड"),
    "not_found": ("Not found", "கிடைக்கவில்லை", "नहीं मिला"),
    "no_page": ("That page doesn't exist.", "அந்தப் பக்கம் இல்லை.", "यह पृष्ठ मौजूद नहीं है।"),
}


def _extra(lang: str):
    """Telugu, Malayalam and Kannada text lives in lang_te.py, lang_ml.py, lang_kn.py."""
    from . import lang_kn, lang_ml, lang_te
    return {"te": lang_te, "ml": lang_ml, "kn": lang_kn}.get(lang)


def pick(row: tuple, lang: str, overlay: dict | None = None, key: str | None = None) -> str:
    """Text for a language from an (en, ta, hi) row, or from the language module's overlay dict."""
    if lang in BASE_LANGS:
        return row[BASE_LANGS.index(lang)]
    if overlay is not None and key in overlay:
        return overlay[key]
    return row[0]


def T(lang: str, key: str, **kw) -> str:
    ex = _extra(lang)
    text = pick(_T[key], lang, ex.UI if ex else None, key)
    return text.format(**kw) if kw else text


def keys() -> list[str]:
    return list(_T)


# ------------------------------------------------------------------ page titles and descriptions: key → {lang: (title, desc)}
PAGE_META = {
    "home": {"en": ("Free Horoscope, Porutham Matching & Dasha | {site}", "Free jathagam with Rasi–Navamsa charts, Porutham and 36-guna matching, Chevvai dosham and Vimshottari dasha. No sign-up; nothing you enter is stored."), "ta": ("இலவச ஜாதகம், திருமணப் பொருத்தம், தசை புக்தி | {site}", "இலவச ஜாதகம் — ராசி, நவாம்சக் கட்டங்கள்; 10 பொருத்தம், 36 குண அஷ்டகூடம், செவ்வாய் தோஷம், விம்சோத்தரி தசை. பதிவு தேவையில்லை; எதுவும் சேமிக்கப்படாது."), "hi": ("मुफ़्त कुंडली, कुंडली मिलान और दशा | {site}", "मुफ़्त जन्म कुंडली — राशि और नवांश चार्ट; 36 गुण मिलान और पोरुथम, मांगलिक दोष जाँच और विंशोत्तरी दशा। न साइन-अप, न कोई जानकारी सहेजी जाती।")},
    "horoscope": {"en": ("Free Jathagam / Horoscope Online – Rasi & Navamsa Chart | {site}", "Free jathagam with Rasi and Navamsa charts, Vimshottari dasha, Chevvai dosham and optional KP tables, neatly formatted to print in six languages."), "ta": ("இலவச ஜாதகம் ஆன்லைன் – ராசி, நவாம்சக் கட்டம் | {site}", "இலவசமாகத் தென்னிந்திய ஜாதகம்: ராசி, நவாம்சக் கட்டங்கள், விம்சோத்தரி தசை, செவ்வாய் தோஷம், விருப்பமான KP அட்டவணைகள் — தமிழில் நேர்த்தியாக அச்சிடலாம்."), "hi": ("मुफ़्त जन्म कुंडली ऑनलाइन – राशि और नवांश चार्ट | {site}", "मुफ़्त दक्षिण भारतीय जन्म कुंडली: राशि और नवांश चार्ट, विंशोत्तरी दशा, मांगलिक दोष और वैकल्पिक KP तालिकाएँ — हिंदी में सुव्यवस्थित, प्रिंट योग्य।")},
    "match": {
        "en": ("Marriage Matching – 10 Porutham & 36 Guna Milan Online | {site}",
               "Free marriage matching: 10/12 Porutham (Rajju, Nadi, Vedha), 36-guna Ashtakoota, Chevvai/Manglik "
               "dosham and Rahu–Ketu, with both Rasi charts side by side."),
        "ta": ("திருமணப் பொருத்தம் ஆன்லைன் – 10 பொருத்தம், ரஜ்ஜு, நாடி | {site}",
               "இலவசத் திருமணப் பொருத்தம்: 12 பொருத்தங்கள் (ரஜ்ஜு, நாடி, வேதை உட்பட), 36-க்கு அஷ்டகூட மதிப்பெண், "
               "செவ்வாய் தோஷம், ராகு–கேது, இருவரின் ராசிக் கட்டங்கள்."),
        "hi": ("कुंडली मिलान ऑनलाइन – 36 गुण मिलान और पोरुथम | {site}",
               "वर और वधू के जन्म विवरण से मुफ़्त कुंडली मिलान: अष्टकूट के 36 में से गुण, नाड़ी, भकूट और गण दोष, "
               "12 पोरुथम, मांगलिक दोष, राहु–केतु और दोनों के राशि चार्ट।"),
    },
    "learn": {
        "en": ("Learn Vedic Astrology: Porutham, Guna Milan & Nakshatras | {site}",
               "Plain-language guides to Rasi and Navamsa charts, ayanamsa, Porutham, Ashtakoota, Rajju and Nadi, "
               "KP astrology, the 27 nakshatras and 12 rasis."),
        "ta": ("ஜோதிடம் கற்க: பொருத்தம், அஷ்டகூடம், நட்சத்திரங்கள், ராசிகள் | {site}",
               "ஜாதகக் கட்டங்கள், திருமணப் பொருத்தம் பற்றிய எளிய விளக்கங்கள்: அயனாம்சம், ராசி–நவாம்சம், 10 "
               "பொருத்தம், அஷ்டகூடம், ரஜ்ஜு–நாடி, KP, 27 நட்சத்திரங்கள், 12 ராசிகள்."),
        "hi": ("ज्योतिष सीखें: गुण मिलान, पोरुथम, नक्षत्र और राशियाँ | {site}",
               "कुंडली चार्ट और विवाह मिलान पर सरल लेख: अयनांश, राशि और नवांश, अष्टकूट, पोरुथम, रज्जु और नाड़ी, "
               "KP, 27 नक्षत्र और 12 राशियाँ।"),
    },
    "credits": {
        "en": ("Credits and Open-Source Licences | {site}",
               "The open-source software, data and fonts behind {site}, with their licences."),
        "ta": ("நன்றி மற்றும் திறந்த மூல உரிமங்கள் | {site}",
               "{site}-இன் பின்னால் உள்ள திறந்த மூல மென்பொருள்கள், தரவு, எழுத்துருக்கள் — அவற்றின் உரிமங்களுடன்."),
        "hi": ("आभार और ओपन-सोर्स लाइसेंस | {site}",
               "{site} में इस्तेमाल ओपन-सोर्स सॉफ़्टवेयर, डेटा और फ़ॉन्ट, उनके लाइसेंस के साथ।"),
    },
    "privacy": {
        "en": ("Privacy – Nothing You Enter Is Stored | {site}",
               "{site} does not store names, birth details or anything else you enter. What is processed, by whom, "
               "and your choices."),
        "ta": ("தனியுரிமை – நீங்கள் உள்ளிடுவது எதுவும் சேமிக்கப்படாது | {site}",
               "{site} பெயர்கள், பிறப்பு விவரங்கள் என நீங்கள் உள்ளிடும் எதையும் சேமிப்பதில்லை. எது, யாரால் "
               "செயலாக்கப்படுகிறது, உங்கள் தேர்வுகள் என்ன."),
        "hi": ("गोपनीयता – आपकी दी हुई कोई जानकारी सहेजी नहीं जाती | {site}",
               "{site} नाम, जन्म विवरण या आपकी दी हुई कोई भी जानकारी नहीं सहेजता। क्या प्रोसेस होता है, किसके "
               "द्वारा, और आपके विकल्प।"),
    },
    "terms": {
        "en": ("Terms of Use | {site}", "The terms for using {site}'s free horoscope and marriage matching tools."),
        "ta": ("பயன்பாட்டு விதிமுறைகள் | {site}", "{site}-இன் இலவச ஜாதக, திருமணப் பொருத்தக் கருவிகளைப் "
               "பயன்படுத்துவதற்கான விதிமுறைகள்."),
        "hi": ("उपयोग की शर्तें | {site}", "{site} के मुफ़्त कुंडली और कुंडली मिलान टूल के उपयोग की शर्तें।"),
    },
    "dasha": {
        "en": ("Vimshottari Dasha Calculator – Mahadasha, Bhukti, Antara | {site}",
               "Vimshottari dasha from birth details: mahadasha, bhukti, antara, sookshma and prana periods with dates "
               "and the running period marked. KP or Lahiri ayanamsa."),
        "ta": ("விம்சோத்தரி தசை கணிப்பு – மகா தசை, புக்தி, அந்தரம் | {site}",
               "பிறப்பு விவரங்களிலிருந்து விம்சோத்தரி தசை: மகா தசை, புக்தி, அந்தரம், சூட்சுமம், பிராணம் — தேதிகளுடன், "
               "நடப்புக் காலம் குறிக்கப்பட்டு. KP அல்லது லாகிரி அயனாம்சம்."),
        "hi": ("विंशोत्तरी दशा कैलकुलेटर – महादशा, अंतर्दशा, प्रत्यंतर | {site}",
               "जन्म विवरण से विंशोत्तरी दशा: महादशा, अंतर्दशा, प्रत्यंतर, सूक्ष्म और प्राण अवधियाँ तिथियों सहित, चालू "
               "अवधि चिह्नित। KP या लाहिड़ी अयनांश।"),
    },
    "upcoming": {
        "en": ("Coming Soon: KP Matching, Templates and More | {site}",
               "Features in progress on {site}: KP 7th cusp and Dasavidha Porutham matching, more matching methods, "
               "templates and sharing."),
        "ta": ("விரைவில்: KP பொருத்தம், வடிவமைப்புகள் மற்றும் பல | {site}",
               "{site}-இல் வரவிருக்கும் வசதிகள்: KP 7-ஆம் பாவம், தசவித பொருத்தம், "
               "வடிவமைப்புகள், பகிர்வு."),
        "hi": ("जल्द आ रहा है: KP मिलान, टेम्पलेट और बहुत कुछ | {site}",
               "{site} पर आने वाली सुविधाएँ: KP सप्तम भाव और दशविध पोरुथम मिलान, "
               "टेम्पलेट और शेयरिंग।"),
    },
}


# ------------------------------------------------------------------ astrology vocabulary (en, ta, hi)
GANA = {"Deva": ("Deva", "தேவ", "देव"), "Manushya": ("Manushya", "மனுஷ", "मनुष्य"),
        "Rakshasa": ("Rakshasa", "ராட்சஸ", "राक्षस")}
NADI = {"Adi": ("Adi", "ஆதி", "आदि"), "Madhya": ("Madhya", "மத்திய", "मध्य"), "Antya": ("Antya", "அந்திய", "अंत्य")}
RAJJU = {"Siro": ("Siro", "சிரசு", "शिरो"), "Kantha": ("Kantha", "கண்டம்", "कंठ"), "Nabhi": ("Nabhi", "நாபி", "नाभि"),
         "Kati": ("Kati", "கடி", "कटि"), "Pada": ("Pada", "பாதம்", "पाद")}
YONI = {"Horse": ("Horse", "குதிரை", "घोड़ा"), "Elephant": ("Elephant", "யானை", "हाथी"), "Sheep": ("Sheep", "ஆடு", "भेड़"),
        "Serpent": ("Serpent", "பாம்பு", "सर्प"), "Dog": ("Dog", "நாய்", "कुत्ता"), "Cat": ("Cat", "பூனை", "बिल्ली"),
        "Rat": ("Rat", "எலி", "चूहा"), "Cow": ("Cow", "பசு", "गाय"), "Buffalo": ("Buffalo", "எருமை", "भैंस"),
        "Tiger": ("Tiger", "புலி", "बाघ"), "Deer": ("Deer", "மான்", "हिरण"), "Monkey": ("Monkey", "குரங்கு", "बंदर"),
        "Mongoose": ("Mongoose", "கீரி", "नेवला"), "Lion": ("Lion", "சிங்கம்", "सिंह")}
SEX = {"M": ("male", "ஆண்", "नर"), "F": ("female", "பெண்", "मादा")}
ELEMENT = {"Fire": ("Fire", "நெருப்பு", "अग्नि"), "Earth": ("Earth", "நிலம்", "पृथ्वी"), "Air": ("Air", "காற்று", "वायु"),
           "Water": ("Water", "நீர்", "जल")}
QUALITY = {"Movable (chara)": ("Movable (chara)", "சர ராசி", "चर"),
           "Fixed (sthira)": ("Fixed (sthira)", "ஸ்திர ராசி", "स्थिर"),
           "Dual (dwiswabhava)": ("Dual (dwiswabhava)", "உபய ராசி", "द्विस्वभाव")}
VARNA = {"Brahmin": ("Brahmin", "பிராமணர்", "ब्राह्मण"), "Kshatriya": ("Kshatriya", "சத்திரியர்", "क्षत्रिय"),
         "Vaishya": ("Vaishya", "வைசியர்", "वैश्य"), "Shudra": ("Shudra", "சூத்திரர்", "शूद्र")}
VASHYA = {"Chatushpada": ("Chatushpada", "சதுஷ்பாதம் (நாற்கால்)", "चतुष्पद"),
          "Manava": ("Manava", "மானவம் (மனிதர்)", "मानव"), "Jalachara": ("Jalachara", "ஜலசரம் (நீர்வாழ்)", "जलचर"),
          "Vanachara": ("Vanachara", "வனசரம் (காட்டு)", "वनचर"), "Keeta": ("Keeta", "கீடம் (பூச்சி)", "कीट")}
GRADE = {"UTTAMAM": ("Uttamam (excellent)", "உத்தமம்", "उत्तम"),
         "MADHYAMAM": ("Madhyamam (average)", "மத்திமம்", "मध्यम"),
         "ADHAMAM": ("Adhamam (poor)", "அதமம்", "अधम"),
         "REJECTED": ("Rejected", "நிராகரிப்பு", "अस्वीकार")}
GRADE_SHORT = {"UTTAMAM": ("Uttamam", "உத்தமம்", "उत्तम"), "MADHYAMAM": ("Madhyamam", "மத்திமம்", "मध्यम"),
               "ADHAMAM": ("Adhamam", "அதமம்", "अधम"), "REJECTED": ("Rejected", "நிராகரிப்பு", "अस्वीकार")}

DEITY_SYMBOL_TA = [
    ("அஸ்வினி குமாரர்கள் (தேவ மருத்துவர்கள்)", "குதிரைத் தலை"),
    ("யமன் (தர்மம், மரணத்தின் அதிபதி)", "யோனி"),
    ("அக்னி (நெருப்புக் கடவுள்)", "கத்தி அல்லது தீச்சுடர்"),
    ("பிரம்மா (படைப்பவர்)", "மாட்டு வண்டி அல்லது தேர்"),
    ("சோமன் (சந்திரக் கடவுள்)", "மானின் தலை"),
    ("ருத்திரன் (சிவனின் புயல் வடிவம்)", "கண்ணீர்த் துளி அல்லது வைரம்"),
    ("அதிதி (தேவர்களின் தாய்)", "வில்லும் அம்பறாத்தூணியும்"),
    ("பிருகஸ்பதி (தேவகுரு)", "பசுவின் மடி அல்லது தாமரை"),
    ("நாகர்கள் (பாம்புத் தெய்வங்கள்)", "சுருண்ட பாம்பு"),
    ("பித்ருக்கள் (முன்னோர்)", "அரியணை"),
    ("பகன் (செல்வம், இல்லற இன்பத்தின் கடவுள்)", "கட்டிலின் முன்கால்கள் அல்லது ஊஞ்சல்"),
    ("அர்யமான் (ஒப்பந்தம், நட்பின் கடவுள்)", "கட்டிலின் பின்கால்கள்"),
    ("சவிதா (உயிர் தரும் சூரியன்)", "திறந்த கை"),
    ("த்வஷ்டா (விஸ்வகர்மா, தேவ சிற்பி)", "ஒளிரும் ரத்தினம் அல்லது முத்து"),
    ("வாயு (காற்றுக் கடவுள்)", "காற்றில் அசையும் இளந்தளிர்"),
    ("இந்திரன், அக்னி", "தோரண வாயில் அல்லது குயவர் சக்கரம்"),
    ("மித்திரன் (நட்பின் கடவுள்)", "தாமரை"),
    ("இந்திரன் (தேவர்களின் அரசன்)", "காதணி அல்லது குடை"),
    ("நிருதி (அழிவின் தேவி)", "வேர்க்கொத்து"),
    ("ஆபஸ் (நீர்த் தேவதை)", "முறம் அல்லது விசிறி"),
    ("விஸ்வேதேவர்கள்", "யானைத் தந்தம்"),
    ("விஷ்ணு (காப்பவர்)", "காது அல்லது மூன்று காலடிகள்"),
    ("அஷ்ட வசுக்கள்", "மிருதங்கம்"),
    ("வருணன் (நீர்களின் அதிபதி)", "வெற்று வட்டம்"),
    ("அஜ ஏகபாதர் (ஒற்றைக் கால் ஆடு)", "வாள் அல்லது பாடையின் முன்பகுதி"),
    ("அஹிர் புத்னியர் (ஆழத்தின் நாகம்)", "பாடையின் பின்பகுதி அல்லது இரட்டையர்"),
    ("பூஷன் (பயணிகளைக் காப்பவர்)", "மீன் அல்லது முரசு"),
]
DEITY_SYMBOL_HI = [
    ("अश्विनी कुमार (देवताओं के वैद्य)", "घोड़े का सिर"),
    ("यम (धर्म और मृत्यु के देवता)", "योनि"),
    ("अग्नि (अग्नि देव)", "उस्तरा या ज्वाला"),
    ("ब्रह्मा (प्रजापति, सृष्टिकर्ता)", "बैलगाड़ी या रथ"),
    ("सोम (चंद्र देव)", "हिरण का सिर"),
    ("रुद्र (शिव का उग्र रूप)", "आँसू की बूँद या हीरा"),
    ("अदिति (देवताओं की माता)", "धनुष और तरकश"),
    ("बृहस्पति (देवगुरु)", "गाय का थन या कमल"),
    ("नाग (सर्प देवता)", "कुंडली मारे सर्प"),
    ("पितृ (पूर्वज)", "राजसिंहासन"),
    ("भग (सौभाग्य और दांपत्य सुख के देवता)", "पलंग के अगले पाए या झूला"),
    ("अर्यमा (संविदा और मित्रता के देवता)", "पलंग के पिछले पाए"),
    ("सविता (जीवन देने वाले सूर्य)", "खुली हथेली"),
    ("त्वष्टा (विश्वकर्मा, दिव्य शिल्पी)", "चमकता रत्न या मोती"),
    ("वायु (पवन देव)", "हवा में झूलता अंकुर"),
    ("इंद्र और अग्नि", "तोरण द्वार या कुम्हार का चाक"),
    ("मित्र (मित्रता के देवता)", "कमल"),
    ("इंद्र (देवराज)", "कुंडल या छत्र"),
    ("निऋति (विनाश की देवी)", "जड़ों का गुच्छा"),
    ("आपः (जल देवता)", "सूप या पंखा"),
    ("विश्वेदेव", "हाथी दाँत"),
    ("विष्णु (पालनहार)", "कान या तीन पदचिह्न"),
    ("अष्ट वसु", "मृदंग"),
    ("वरुण (जल के स्वामी)", "खाली वृत्त"),
    ("अज एकपाद (एक पैर वाले अज)", "तलवार या अर्थी का अगला भाग"),
    ("अहिर्बुध्न्य (गहराई के सर्प)", "अर्थी का पिछला भाग या जुड़वाँ"),
    ("पूषा (यात्रियों के रक्षक)", "मछली या ढोल"),
]
RASI_SYMBOL_TA = ["ஆடு", "காளை", "இரட்டையர்", "நண்டு", "சிங்கம்", "கன்னிப் பெண்", "தராசு", "தேள்", "வில் (வில்லாளி)",
                  "மகர மீன் (முதலை)", "குடம்", "இரண்டு மீன்கள்"]
RASI_SYMBOL_HI = ["मेढ़ा", "बैल", "जुड़वाँ", "केकड़ा", "सिंह", "कन्या", "तराज़ू", "बिच्छू", "धनुष (धनुर्धर)", "मगर",
                  "घड़ा", "दो मछलियाँ"]

# what each library is used for (credits page), in English order of views.CREDITS
CREDIT_USES = {
    "Planetary positions and houses": ("கிரக நிலைகளும் பாவங்களும்", "ग्रहों की स्थिति और भाव"),
    "Python bindings for the Swiss Ephemeris": ("Swiss Ephemeris-க்கான Python இணைப்பு", "Swiss Ephemeris के लिए Python बाइंडिंग"),
    "Place names, coordinates and time zones": ("ஊர்ப் பெயர்கள், அட்சரேகை–தீர்க்கரேகை, நேர மண்டலங்கள்",
                                                "स्थानों के नाम, निर्देशांक और समय क्षेत्र"),
    "Map data": ("வரைபடத் தரவு", "मानचित्र डेटा"),
    "Interactive map": ("ஊடாடும் வரைபடம்", "इंटरैक्टिव मानचित्र"),
    "Map tiles for “Use Map”": ("“வரைபடத்தில் தேர்வு” வசதிக்கான வரைபடப் படங்கள்", "“मानचित्र पर चुनें” के लिए मानचित्र टाइलें"),
    "Web framework": ("வலை நிரல் கட்டமைப்பு", "वेब फ़्रेमवर्क"),
    "Web toolkit under FastAPI": ("FastAPI-இன் அடிப்படைக் கருவித்தொகுப்பு", "FastAPI के नीचे का वेब टूलकिट"),
    "Data validation": ("தரவுச் சரிபார்ப்பு", "डेटा सत्यापन"),
    "Web server": ("வலை சேவையகம்", "वेब सर्वर"),
    "Fuzzy place-name search": ("ஊர்ப் பெயர்த் தேடல்", "स्थान के नाम की खोज"),
    "Historical time zones": ("வரலாற்று நேர மண்டலங்கள்", "ऐतिहासिक समय क्षेत्र"),
    "Tamil, Telugu, Malayalam, Kannada and Devanagari text": ("தமிழ், தெலுங்கு, மலையாளம், கன்னடம், தேவநாகரி எழுத்துகள்",
                                                              "तमिल, तेलुगु, मलयालम, कन्नड़ और देवनागरी लिपि"),
    "Bot protection": ("தானியங்கி நிரல்களிலிருந்து பாதுகாப்பு", "बॉट से सुरक्षा"),
    "Fallback calculation engine": ("மாற்றுக் கணக்கீட்டு இயந்திரம்", "वैकल्पिक गणना इंजन"),
}


_VOCAB_NAME = {}  # filled below: id(table) → name used in the language modules' VOCAB dicts


def V(table: dict, key: str, lang: str) -> str:
    """Translate a vocabulary value."""
    row = table.get(key)
    if not row:
        return key
    ex = _extra(lang)
    return pick(row, lang, ex.VOCAB.get(_VOCAB_NAME.get(id(table)), {}) if ex else None, key)


for _n in ("GANA", "NADI", "RAJJU", "YONI", "SEX", "ELEMENT", "QUALITY", "VARNA", "VASHYA", "GRADE", "GRADE_SHORT"):
    _VOCAB_NAME[id(globals()[_n])] = _n


def deity_symbol(lang: str, n: int, english: tuple[str, str]) -> tuple[str, str]:
    if lang == "ta":
        return DEITY_SYMBOL_TA[n]
    if lang == "hi":
        return DEITY_SYMBOL_HI[n]
    ex = _extra(lang)
    return ex.DEITY_SYMBOL[n] if ex else english


def rasi_symbol(lang: str, r: int, english: str) -> str:
    if lang == "ta":
        return RASI_SYMBOL_TA[r]
    if lang == "hi":
        return RASI_SYMBOL_HI[r]
    ex = _extra(lang)
    return ex.RASI_SYMBOL[r] if ex else english


def credit_use(lang: str, english: str) -> str:
    if lang == "en":
        return english
    if lang in BASE_LANGS:
        return CREDIT_USES.get(english, (english, english))[BASE_LANGS.index(lang) - 1]
    ex = _extra(lang)
    return ex.CREDIT_USES.get(english, english) if ex else english


def page_meta(key: str, lang: str) -> tuple[str, str]:
    if lang in PAGE_META[key]:
        return PAGE_META[key][lang]
    ex = _extra(lang)
    return ex.META[key] if ex and key in ex.META else PAGE_META[key]["en"]
