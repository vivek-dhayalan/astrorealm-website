"""Display labels for chart images. Add a language by adding one entry to LANGUAGES.

Telugu, Malayalam and Kannada terms are drafts pending native-speaker review."""
from __future__ import annotations

from ..core.reference import NAKSHATRAS, PLANETS, RASHIS

LANGUAGES: dict[str, dict] = {
    "en": {
        "planet_short": {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
                         "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"},
        "planet": {p: p for p in PLANETS},
        "rashi": dict(zip(RASHIS, RASHIS)),
        "nakshatra": dict(zip(NAKSHATRAS, NAKSHATRAS)),
        "lagna_short": "Asc",
        "retro": "(R)",
        "labels": {
            "rasi": "Rasi", "navamsa": "Navamsa", "kp_planets": "KP planets", "kp_cusps": "KP cusps",
            "planet": "Planet", "sign": "Sign", "degree": "Degree", "sign_lord": "Sign lord",
            "star_lord": "Star lord", "sub_lord": "Sub lord", "signifies": "Signifies", "house": "House",
            "nakshatra": "Nakshatra", "lagna": "Lagna", "ayanamsa": "Ayanamsa",
        },
        "font": "Noto Sans, Segoe UI, Helvetica, Arial, sans-serif",
    },
    "ta": {
        "planet_short": {"Sun": "சூரி", "Moon": "சந்", "Mars": "செ", "Mercury": "புத", "Jupiter": "குரு",
                         "Venus": "சுக்", "Saturn": "சனி", "Rahu": "ரா", "Ketu": "கே"},
        "planet": {"Sun": "சூரியன்", "Moon": "சந்திரன்", "Mars": "செவ்வாய்", "Mercury": "புதன்",
                   "Jupiter": "குரு", "Venus": "சுக்கிரன்", "Saturn": "சனி", "Rahu": "ராகு", "Ketu": "கேது"},
        "rashi": dict(zip(RASHIS, ["மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி",
                                   "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"])),
        "nakshatra": dict(zip(NAKSHATRAS, [
            "அசுவினி", "பரணி", "கார்த்திகை", "ரோகிணி", "மிருகசீரிடம்", "திருவாதிரை", "புனர்பூசம்",
            "பூசம்", "ஆயில்யம்", "மகம்", "பூரம்", "உத்திரம்", "அஸ்தம்", "சித்திரை", "சுவாதி",
            "விசாகம்", "அனுஷம்", "கேட்டை", "மூலம்", "பூராடம்", "உத்திராடம்", "திருவோணம்",
            "அவிட்டம்", "சதயம்", "பூரட்டாதி", "உத்திரட்டாதி", "ரேவதி"])),
        "lagna_short": "லக்",
        "retro": "(வ)",
        "labels": {
            "rasi": "ராசி", "navamsa": "நவாம்சம்", "kp_planets": "கிரக நிலை", "kp_cusps": "பாவ நிலை",
            "planet": "கிரகம்", "sign": "ராசி", "degree": "பாகை", "sign_lord": "ராசி நாதன்",
            "star_lord": "நட்சத்திர நாதன்", "sub_lord": "உப நாதன்", "signifies": "குறிகாட்டிகள்",
            "house": "பாவம்", "nakshatra": "நட்சத்திரம்", "lagna": "லக்னம்", "ayanamsa": "அயனாம்சம்",
        },
        "font": "Noto Sans Tamil, Nirmala UI, Latha, sans-serif",
    },
    "hi": {
        "planet_short": {"Sun": "सू", "Moon": "चं", "Mars": "मं", "Mercury": "बु", "Jupiter": "गु",
                         "Venus": "शु", "Saturn": "श", "Rahu": "रा", "Ketu": "के"},
        "planet": {"Sun": "सूर्य", "Moon": "चंद्र", "Mars": "मंगल", "Mercury": "बुध", "Jupiter": "गुरु",
                   "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"},
        "rashi": dict(zip(RASHIS, ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
                                   "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"])),
        "nakshatra": dict(zip(NAKSHATRAS, [
            "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य",
            "आश्लेषा", "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाति",
            "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा",
            "शतभिषा", "पूर्वा भाद्रपद", "उत्तरा भाद्रपद", "रेवती"])),
        "lagna_short": "लग्न",
        "retro": "(व)",
        "labels": {
            "rasi": "राशि चक्र", "navamsa": "नवांश", "kp_planets": "ग्रह स्थिति", "kp_cusps": "भाव स्थिति",
            "planet": "ग्रह", "sign": "राशि", "degree": "अंश", "sign_lord": "राशि स्वामी",
            "star_lord": "नक्षत्र स्वामी", "sub_lord": "उप स्वामी", "signifies": "कारकत्व", "house": "भाव",
            "nakshatra": "नक्षत्र", "lagna": "लग्न", "ayanamsa": "अयनांश",
        },
        "font": "Noto Sans Devanagari, Nirmala UI, Mangal, sans-serif",
    },
    "te": {
        "planet_short": {"Sun": "సూ", "Moon": "చం", "Mars": "కు", "Mercury": "బు", "Jupiter": "గు",
                         "Venus": "శు", "Saturn": "శ", "Rahu": "రా", "Ketu": "కే"},
        "planet": {"Sun": "సూర్యుడు", "Moon": "చంద్రుడు", "Mars": "కుజుడు", "Mercury": "బుధుడు",
                   "Jupiter": "గురువు", "Venus": "శుక్రుడు", "Saturn": "శని", "Rahu": "రాహువు", "Ketu": "కేతువు"},
        "rashi": dict(zip(RASHIS, ["మేషం", "వృషభం", "మిథునం", "కర్కాటకం", "సింహం", "కన్య",
                                   "తుల", "వృశ్చికం", "ధనుస్సు", "మకరం", "కుంభం", "మీనం"])),
        "nakshatra": dict(zip(NAKSHATRAS, [
            "అశ్విని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర", "ఆర్ద్ర", "పునర్వసు", "పుష్యమి",
            "ఆశ్లేష", "మఖ", "పుబ్బ", "ఉత్తర", "హస్త", "చిత్త", "స్వాతి", "విశాఖ", "అనూరాధ",
            "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ", "ఉత్తరాషాఢ", "శ్రవణం", "ధనిష్ఠ", "శతభిషం",
            "పూర్వాభాద్ర", "ఉత్తరాభాద్ర", "రేవతి"])),
        "lagna_short": "లగ్న",
        "retro": "(వ)",
        "labels": {
            "rasi": "రాశి", "navamsa": "నవాంశ", "kp_planets": "గ్రహ స్థితి", "kp_cusps": "భావ స్థితి",
            "planet": "గ్రహం", "sign": "రాశి", "degree": "భాగలు", "sign_lord": "రాశ్యధిపతి",
            "star_lord": "నక్షత్రాధిపతి", "sub_lord": "ఉప అధిపతి", "signifies": "కారకత్వం", "house": "భావం",
            "nakshatra": "నక్షత్రం", "lagna": "లగ్నం", "ayanamsa": "అయనాంశ",
        },
        "font": "Noto Sans Telugu, Nirmala UI, Gautami, sans-serif",
    },
    "ml": {
        "planet_short": {"Sun": "സൂ", "Moon": "ച", "Mars": "ചൊ", "Mercury": "ബു", "Jupiter": "വ്യാ",
                         "Venus": "ശു", "Saturn": "മ", "Rahu": "രാ", "Ketu": "കേ"},
        "planet": {"Sun": "സൂര്യൻ", "Moon": "ചന്ദ്രൻ", "Mars": "ചൊവ്വ", "Mercury": "ബുധൻ",
                   "Jupiter": "വ്യാഴം", "Venus": "ശുക്രൻ", "Saturn": "ശനി", "Rahu": "രാഹു", "Ketu": "കേതു"},
        "rashi": dict(zip(RASHIS, ["മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം", "ചിങ്ങം", "കന്നി",
                                   "തുലാം", "വൃശ്ചികം", "ധനു", "മകരം", "കുംഭം", "മീനം"])),
        "nakshatra": dict(zip(NAKSHATRAS, [
            "അശ്വതി", "ഭരണി", "കാർത്തിക", "രോഹിണി", "മകയിരം", "തിരുവാതിര", "പുണർതം", "പൂയം",
            "ആയില്യം", "മകം", "പൂരം", "ഉത്രം", "അത്തം", "ചിത്തിര", "ചോതി", "വിശാഖം", "അനിഴം",
            "തൃക്കേട്ട", "മൂലം", "പൂരാടം", "ഉത്രാടം", "തിരുവോണം", "അവിട്ടം", "ചതയം",
            "പൂരുരുട്ടാതി", "ഉത്രട്ടാതി", "രേവതി"])),
        "lagna_short": "ല",
        "retro": "(വ)",
        "labels": {
            "rasi": "രാശി", "navamsa": "നവാംശം", "kp_planets": "ഗ്രഹസ്ഥിതി", "kp_cusps": "ഭാവസ്ഥിതി",
            "planet": "ഗ്രഹം", "sign": "രാശി", "degree": "ഡിഗ്രി", "sign_lord": "രാശ്യാധിപൻ",
            "star_lord": "നക്ഷത്രാധിപൻ", "sub_lord": "ഉപാധിപൻ", "signifies": "കാരകത്വം", "house": "ഭാവം",
            "nakshatra": "നക്ഷത്രം", "lagna": "ലഗ്നം", "ayanamsa": "അയനാംശം",
        },
        "font": "Noto Sans Malayalam, Nirmala UI, Kartika, sans-serif",
    },
    "kn": {
        "planet_short": {"Sun": "ಸೂ", "Moon": "ಚಂ", "Mars": "ಕು", "Mercury": "ಬು", "Jupiter": "ಗು",
                         "Venus": "ಶು", "Saturn": "ಶ", "Rahu": "ರಾ", "Ketu": "ಕೇ"},
        "planet": {"Sun": "ಸೂರ್ಯ", "Moon": "ಚಂದ್ರ", "Mars": "ಕುಜ", "Mercury": "ಬುಧ", "Jupiter": "ಗುರು",
                   "Venus": "ಶುಕ್ರ", "Saturn": "ಶನಿ", "Rahu": "ರಾಹು", "Ketu": "ಕೇತು"},
        "rashi": dict(zip(RASHIS, ["ಮೇಷ", "ವೃಷಭ", "ಮಿಥುನ", "ಕರ್ಕಾಟಕ", "ಸಿಂಹ", "ಕನ್ಯಾ",
                                   "ತುಲಾ", "ವೃಶ್ಚಿಕ", "ಧನು", "ಮಕರ", "ಕುಂಭ", "ಮೀನ"])),
        "nakshatra": dict(zip(NAKSHATRAS, [
            "ಅಶ್ವಿನಿ", "ಭರಣಿ", "ಕೃತ್ತಿಕಾ", "ರೋಹಿಣಿ", "ಮೃಗಶಿರಾ", "ಆರ್ದ್ರಾ", "ಪುನರ್ವಸು", "ಪುಷ್ಯ",
            "ಆಶ್ಲೇಷಾ", "ಮಘಾ", "ಪೂರ್ವ ಫಲ್ಗುಣಿ", "ಉತ್ತರ ಫಲ್ಗುಣಿ", "ಹಸ್ತ", "ಚಿತ್ತಾ", "ಸ್ವಾತಿ",
            "ವಿಶಾಖಾ", "ಅನುರಾಧಾ", "ಜ್ಯೇಷ್ಠಾ", "ಮೂಲಾ", "ಪೂರ್ವಾಷಾಢಾ", "ಉತ್ತರಾಷಾಢಾ", "ಶ್ರವಣ",
            "ಧನಿಷ್ಠಾ", "ಶತಭಿಷಾ", "ಪೂರ್ವಾಭಾದ್ರ", "ಉತ್ತರಾಭಾದ್ರ", "ರೇವತಿ"])),
        "lagna_short": "ಲಗ್ನ",
        "retro": "(ವ)",
        "labels": {
            "rasi": "ರಾಶಿ", "navamsa": "ನವಾಂಶ", "kp_planets": "ಗ್ರಹ ಸ್ಥಿತಿ", "kp_cusps": "ಭಾವ ಸ್ಥಿತಿ",
            "planet": "ಗ್ರಹ", "sign": "ರಾಶಿ", "degree": "ಅಂಶ", "sign_lord": "ರಾಶ್ಯಾಧಿಪತಿ",
            "star_lord": "ನಕ್ಷತ್ರಾಧಿಪತಿ", "sub_lord": "ಉಪಾಧಿಪತಿ", "signifies": "ಕಾರಕತ್ವ", "house": "ಭಾವ",
            "nakshatra": "ನಕ್ಷತ್ರ", "lagna": "ಲಗ್ನ", "ayanamsa": "ಅಯನಾಂಶ",
        },
        "font": "Noto Sans Kannada, Nirmala UI, Tunga, sans-serif",
    },
}

SUPPORTED = tuple(LANGUAGES)


def get(lang: str) -> dict:
    return LANGUAGES.get(lang, LANGUAGES["en"])
