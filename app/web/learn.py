"""Explainer articles ("Learn" section). Plain HTML we write ourselves — no user input here."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    slug: str
    title: str
    summary: str
    body: str


ARTICLES: list[Article] = [
    Article(
        "ayanamsa",
        "What is Ayanamsa, and which one should I choose?",
        "Why Indian charts differ from Western ones by about 24°, and the difference between Lahiri and KP.",
        """
<p>Western astrology measures planets from the point where the Sun crosses the equator in spring (the
<em>tropical</em> zodiac). Indian astrology measures them against the fixed stars (the <em>sidereal</em> zodiac).
Because the Earth's axis slowly wobbles — a motion called <em>precession</em> — these two starting points drift
apart by about 50 seconds of arc every year. The gap between them is the <strong>ayanamsa</strong>.</p>
<p>Today the ayanamsa is a little over 24°. That is why a planet at 10° Taurus in a Western chart sits at about
16° Aries in an Indian one, and why the Sun's sign in a Western chart is usually one sign ahead of the Sun's
sign in an Indian chart.</p>
<h2>Why there is more than one</h2>
<p>Everyone agrees on the drift; astronomers and astrologers differ on the exact year the two zodiacs coincided.
Each choice gives a slightly different ayanamsa. AstroRealm offers the two used most in South India:</p>
<ul>
<li><strong>Lahiri (Chitrapaksha)</strong> — recommended by the Government of India's Calendar Reform Committee
(1955) and used in most Indian panchangams and horoscope software.</li>
<li><strong>Krishnamurti (KP)</strong> — used in the Krishnamurti Paddhati (KP) system. It is about 6 arc-minutes
smaller than Lahiri.</li>
</ul>
<h2>Does the choice matter?</h2>
<p>For most people, no: a 6′ difference rarely changes the rasi, nakshatra or lagna. It matters when the Moon or
the lagna sits very close to a boundary, and it matters a great deal in KP astrology, where sub lords span only
a fraction of a degree. If you are taking the chart to an astrologer, choose the ayanamsa they use. Every
AstroRealm printout states which ayanamsa it used, with its exact value.</p>
""",
    ),
    Article(
        "rasi-navamsa",
        "How to read a South Indian Rasi and Navamsa chart",
        "The twelve fixed boxes, where the Lagna is marked, and what the Navamsa (D-9) adds.",
        """
<p>The <strong>Rasi chart</strong> (also called D-1) is the birth chart itself: it shows which of the twelve
signs (rasis) each planet occupied at the moment of birth, and which sign was rising on the eastern horizon —
the <strong>Lagna</strong> or ascendant.</p>
<h2>The South Indian layout</h2>
<p>In the South Indian style the signs never move. The grid has twelve boxes around an empty centre, starting
with <em>Meena</em> (Pisces) at the top left and running clockwise: Mesha, Rishabha and Mithuna along the top,
Kataka and Simha down the right, Kanni, Thula, Vrischika and Dhanu along the bottom, and Makara and Kumbha up the
left.
Because the signs are fixed, the Lagna is marked inside its box (as “Asc” or “Lagna”) instead of always being at
the top, as in North Indian charts.</p>
<p>Planets are written in short form — Su (Sun), Mo (Moon), Ma (Mars), Me (Mercury), Ju (Jupiter), Ve (Venus),
Sa (Saturn), Ra (Rahu) and Ke (Ketu). An “(R)” means the planet was retrograde.</p>
<h2>Houses</h2>
<p>Counting from the Lagna box as the 1st house, the next box clockwise is the 2nd house, and so on. The 7th
house, directly opposite the Lagna, is the house of marriage and partnership.</p>
<h2>The Navamsa chart (D-9)</h2>
<p>Each sign spans 30°. Divide it into nine equal parts of 3°20′ and you get the <strong>navamsa</strong>.
Each of the 108 navamsas also corresponds to one pada (quarter) of the 27 nakshatras. The Navamsa chart places
every planet according to the navamsa it falls in.</p>
<p>Astrologers traditionally read the Navamsa for marriage and the spouse, and to judge how strong a planet
really is: a planet in the same sign in both charts (<em>vargottama</em>) is considered especially strong.</p>
<p>Because the Lagna moves through a navamsa in about 13 minutes, the Navamsa Lagna is sensitive to the birth
time — see <a href="/learn/birth-time">why the exact birth time matters</a>.</p>
""",
    ),
    Article(
        "ashtakoota",
        "Ashtakoota matching: the 8 kootas and 36 gunas explained",
        "What each koota measures, how the score out of 36 is read, and the main doshas.",
        """
<p><strong>Ashtakoota</strong> (“eight aspects”), also called Guna Milan, compares the Moon's nakshatra and rasi
in the bride's and groom's charts. Each of the eight kootas carries a number of points (gunas), adding up to 36.</p>
<table class="grid">
<thead><tr><th>Koota</th><th class="num">Points</th><th>What it compares</th></tr></thead>
<tbody>
<tr><td>Varna</td><td class="num">1</td><td>Spiritual temperament, by rasi</td></tr>
<tr><td>Vashya</td><td class="num">2</td><td>Mutual attraction and influence, by rasi group</td></tr>
<tr><td>Tara</td><td class="num">3</td><td>Auspiciousness of the birth stars counted from each other</td></tr>
<tr><td>Yoni</td><td class="num">4</td><td>Physical compatibility, by the animal symbol of each nakshatra</td></tr>
<tr><td>Graha Maitri</td><td class="num">5</td><td>Friendship between the lords of the two Moon signs</td></tr>
<tr><td>Gana</td><td class="num">6</td><td>Temperament: Deva, Manushya or Rakshasa</td></tr>
<tr><td>Bhakoot</td><td class="num">7</td><td>Relative position of the two Moon signs</td></tr>
<tr><td>Nadi</td><td class="num">8</td><td>Constitution (Adi, Madhya, Antya); traditionally linked to health and children</td></tr>
</tbody></table>
<h2>Reading the total</h2>
<ul>
<li><strong>33–36</strong>: Ati Uttamam — excellent</li>
<li><strong>25–32</strong>: Uttamam — good</li>
<li><strong>18–24</strong>: Madhyamam — average; commonly treated as acceptable</li>
<li><strong>Below 18</strong>: Adhamam — not recommended</li>
</ul>
<h2>Doshas and cancellations</h2>
<p>Three kootas carry named doshas when they score zero: <strong>Nadi dosha</strong> (same nadi),
<strong>Bhakoot dosha</strong> (Moon signs 2/12, 5/9 or 6/8 from each other) and <strong>Gana dosha</strong>.
Classical texts list exceptions that cancel them — for example, Bhakoot dosha is cancelled when the lords of the
two Moon signs are the same planet or friends. AstroRealm shows each dosha, whether it is cancelled and why,
and (following the practice of the astrologer we validated against) restores Bhakoot's points when its dosha is
cancelled.</p>
<p>Ashtakoota is one view of compatibility. South Indian families usually also look at the
<a href="/learn/porutham">Porutham</a> system, and astrologers read both charts as a whole before advising.</p>
""",
    ),
    Article(
        "porutham",
        "Porutham: the South Indian 10 (and 12) matches",
        "Dina, Gana, Mahendra, Rajju, Vedha and the rest — what each checks and how the result is graded.",
        """
<p><strong>Porutham</strong> (“agreement”) is the matching system used across Tamil Nadu and Kerala. Like
Ashtakoota it compares the Moon's nakshatra and rasi, but instead of points each check is simply matched or not.
Most counts start from the bride's birth star and run to the groom's.</p>
<h2>The checks</h2>
<ul>
<li><strong>Dina</strong> — day-to-day harmony and health, from the star count.</li>
<li><strong>Gana</strong> — temperament (Deva, Manushya, Rakshasa).</li>
<li><strong>Mahendra</strong> — prosperity and children; matches when the count is 4, 7, 10, 13, 16, 19, 22 or 25.</li>
<li><strong>Stree Deergha</strong> — the wife's well-being; matches when the groom's star is far enough from the bride's.</li>
<li><strong>Yoni</strong> — physical compatibility, by the animal of each star.</li>
<li><strong>Rasi</strong> — the relative position of the two Moon signs.</li>
<li><strong>Rasyadhipathi</strong> — friendship between the lords of the two Moon signs.</li>
<li><strong>Vasya</strong> — mutual attraction between the two signs.</li>
<li><strong>Rajju</strong> — the 27 stars are grouped into five body parts (Pada, Kati, Nabhi, Kantha, Siro).
Both partners in the same rajju is considered a serious mismatch.</li>
<li><strong>Vedha</strong> — certain pairs of stars “obstruct” each other; such a pair fails.</li>
<li><strong>Varna</strong> and <strong>Nadi</strong> — many astrologers add these two, giving twelve checks.</li>
</ul>
<h2>How AstroRealm grades the result</h2>
<p>Counting how many checks pass is less important than <em>which</em> ones pass. Following the grading
used by the astrologer we validated against:</p>
<ul>
<li><strong>Rejected</strong> if Nadi (without a recognised exception) or Vedha fails.</li>
<li><strong>Uttamam</strong> when Rajju, Varna, Nadi, Rasi, Rasyadhipathi and Stree Deergha all match.</li>
<li><strong>Madhyamam</strong> when at least Rajju matches.</li>
<li><strong>Adhamam</strong> otherwise.</li>
</ul>
<p>Some checks have a “partial” middle ground, so AstroRealm shows two views: <em>strict</em> (partial counts as
not matched) and <em>lenient</em> (partial counts as matched). Traditions differ on the exact counts for Dina,
Stree Deergha and Rasi; the rules this site uses are published in its <a href="/credits">source code</a>.</p>
""",
    ),
    Article(
        "kp-astrology",
        "KP astrology in brief: star lords, sub lords and significators",
        "How Krishnamurti Paddhati divides the zodiac and how to read the KP tables.",
        """
<p><strong>Krishnamurti Paddhati (KP)</strong> was developed by Prof. K. S. Krishnamurti in the mid-20th century.
It keeps the nakshatras of traditional astrology but adds a finer division and uses Placidus house cusps, with its
own ayanamsa.</p>
<h2>Sign lord, star lord and sub lord</h2>
<p>Every point in the zodiac has three rulers in KP:</p>
<ul>
<li>the <strong>sign lord</strong> — the ruler of the rasi (30° each);</li>
<li>the <strong>star lord</strong> — the ruler of the nakshatra (13°20′ each);</li>
<li>the <strong>sub lord</strong> — each nakshatra is split into nine unequal subs, in proportion to the
years each planet rules in the Vimshottari dasha system.</li>
</ul>
<p>The same proportional split applied again gives the <strong>sub-sub (SS)</strong> and
<strong>sub-sub-sub (SSS)</strong> lords shown in AstroRealm's KP tables. KP holds that the planet shows the
source, the star lord shows the matter, and the sub lord decides whether it will be favourable.</p>
<h2>Significators</h2>
<p>A planet <em>signifies</em> the houses it occupies and owns, and especially the houses connected through its
star lord. The “Signifies” column lists those houses. For marriage, KP looks at the sub lord of the 7th cusp:
when it signifies the 2nd, 7th and 11th houses, marriage is said to be promised.</p>
<h2>Why the birth time matters even more in KP</h2>
<p>Sub lords of the house cusps can change within a few minutes of birth time. Always check the time against the
birth certificate or hospital record, and see <a href="/learn/birth-time">why exact birth details matter</a>.</p>
""",
    ),
    Article(
        "birth-time",
        "Why the exact birth time and place matter",
        "How much a few minutes or a wrong town can change the lagna, nakshatra and matching.",
        """
<p>A horoscope is a snapshot of the sky from one place at one moment. Small errors in either can change the
result.</p>
<h2>Time</h2>
<ul>
<li>The <strong>Lagna</strong> moves through a whole sign in roughly two hours, about 1° every 4 minutes. A birth
time a few minutes off can change the Lagna when it is near the edge of a sign.</li>
<li>The <strong>Moon</strong> moves about 13° a day, so the nakshatra changes roughly once a day. Near a boundary,
even 20–30 minutes can change the nakshatra — and with it the Ashtakoota and Porutham results.</li>
<li>In <strong>KP</strong>, house sub lords can change within a few minutes.</li>
</ul>
<p>Use the time from the birth certificate or hospital record where possible. AstroRealm uses the historical
time-zone rules for the place you choose, including India's wartime +06:30 offset in 1942–45.</p>
<h2>Place</h2>
<p>The place sets the latitude and longitude, which determine the Lagna and the house cusps. Choose the town of
birth from the suggestions, or pick it on the map for villages and hospitals outside town. A nearby town is
usually close enough, but the exact spot is better for KP.</p>
<h2>Privacy</h2>
<p>AstroRealm does not store what you enter — see the <a href="/privacy">privacy page</a>.</p>
""",
    ),
]

BY_SLUG = {a.slug: a for a in ARTICLES}
