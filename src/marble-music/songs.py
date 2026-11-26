"""Public-domain melodies for MARBLE MUSIC (composers died long ago; we synthesise our own performance).
Each song: list of sections; a section = (bpm, family, transpose, [(midi, eighths), ...]).
`eighths` = note length in eighth notes (a rest is midi None). Families: tube (brass tube chime), wood (walnut
block), glass (amber glass bar), saucer (copper dome). One family per section = a fresh 'version' every few seconds."""

# Grieg, In the Hall of the Mountain King (1875) — the famous 4-bar phrase, B minor.
B3, Cs4, D4, E4, F4, Fs4, A4, B4, C4 = 59, 61, 62, 64, 65, 66, 69, 71, 60
MOUNTAIN_PHRASE = [
    (B3, 1), (Cs4, 1), (D4, 1), (E4, 1), (Fs4, 1), (D4, 1), (Fs4, 2),
    (F4, 1), (Cs4, 1), (F4, 2), (E4, 1), (C4, 1), (E4, 2),
    (B3, 1), (Cs4, 1), (D4, 1), (E4, 1), (Fs4, 1), (D4, 1), (Fs4, 1), (B4, 1),
    (A4, 1), (Fs4, 1), (D4, 1), (Fs4, 1), (A4, 4),
]
SONGS = {
    "mountain-king": {
        "title": "In the Hall of the Mountain King",
        "composer": "Edvard Grieg (1875)",
        "sections": [
            (120, "wood", 0, MOUNTAIN_PHRASE),
            (148, "tube", 0, MOUNTAIN_PHRASE),
            (182, "glass", 12, MOUNTAIN_PHRASE),
            (224, "saucer", 12, MOUNTAIN_PHRASE[:-1] + [(A4, 2), (B4, 4)]),
        ],
        "final": (47, "tube"),          # a low B on a big tube to finish
    },
}

# ---- more public-domain melodies (all composers dead > 100 years; arrangements are our own) ----
ODE_A = [(66, 2), (66, 2), (67, 2), (69, 2), (69, 2), (67, 2), (66, 2), (64, 2), (62, 2), (62, 2), (64, 2), (66, 2), (66, 3), (64, 1), (64, 4)]
ODE_B = ODE_A[:-3] + [(64, 3), (62, 1), (62, 4)]
FUR_ELISE = [(76, 1), (75, 1), (76, 1), (75, 1), (76, 1), (71, 1), (74, 1), (72, 1), (69, 3), (60, 1), (64, 1), (69, 1),
             (71, 3), (64, 1), (68, 1), (71, 1), (72, 3), (64, 1), (76, 1), (75, 1), (76, 1), (75, 1), (76, 1), (71, 1),
             (74, 1), (72, 1), (69, 3), (60, 1), (64, 1), (69, 1), (71, 3), (64, 1), (72, 1), (71, 1), (69, 6)]
CANON_A = [(78, 2), (76, 2), (74, 2), (73, 2), (71, 2), (69, 2), (71, 2), (73, 2)]
CANON_B = [(74, 2), (73, 2), (71, 2), (69, 2), (67, 2), (66, 2), (67, 2), (64, 2)]
TURKISH = [(71, 1), (69, 1), (68, 1), (69, 1), (72, 4), (74, 1), (72, 1), (71, 1), (72, 1), (76, 4),
           (77, 1), (76, 1), (75, 1), (76, 1), (83, 1), (81, 1), (80, 1), (81, 1), (83, 1), (81, 1), (80, 1), (81, 1), (84, 8)]
JINGLE_A = [(71, 2), (71, 2), (71, 4), (71, 2), (71, 2), (71, 4), (71, 2), (74, 2), (67, 3), (69, 1), (71, 8),
            (72, 2), (72, 2), (72, 3), (72, 1), (72, 2), (71, 2), (71, 2), (71, 1), (71, 1)]
JINGLE_1 = JINGLE_A + [(71, 2), (69, 2), (69, 2), (71, 2), (69, 4), (74, 4)]
JINGLE_2 = JINGLE_A + [(74, 2), (74, 2), (72, 2), (69, 2), (67, 8)]
NACHTMUSIK = [(67, 2), (None, 1), (62, 1), (67, 2), (None, 1), (62, 1), (67, 1), (62, 1), (67, 1), (71, 1), (74, 4),
              (72, 2), (None, 1), (69, 1), (72, 2), (None, 1), (69, 1), (72, 1), (69, 1), (66, 1), (69, 1), (62, 4)]

SONGS.update({
    "ode-to-joy": {"title": "Ode to Joy", "composer": "Ludwig van Beethoven (1824)",
                   "sections": [(150, "wood", 0, ODE_A), (165, "glass", 0, ODE_B), (190, "tube", 12, ODE_A), (215, "saucer", 12, ODE_B)],
                   "final": (50, "tube")},
    "fur-elise": {"title": "Für Elise", "composer": "Ludwig van Beethoven (1810)",
                  "sections": [(150, "glass", 0, FUR_ELISE), (185, "tube", 0, FUR_ELISE)], "final": (45, "tube")},
    "canon-in-d": {"title": "Canon in D", "composer": "Johann Pachelbel (c. 1680)",
                   "sections": [(110, "tube", 0, CANON_A + CANON_B), (140, "glass", 0, CANON_A + CANON_B),
                                (180, "wood", -12, CANON_A + CANON_B), (220, "saucer", 0, CANON_A + CANON_B)],
                   "final": (50, "tube")},
    "turkish-march": {"title": "Rondo alla Turca (Turkish March)", "composer": "Wolfgang Amadeus Mozart (1783)",
                      "sections": [(170, "glass", 0, TURKISH), (190, "wood", 0, TURKISH), (215, "saucer", 0, TURKISH),
                                   (240, "tube", 0, TURKISH)], "final": (57, "tube")},
    "jingle-bells": {"title": "Jingle Bells", "composer": "James Lord Pierpont (1857)",
                     "sections": [(170, "tube", 0, JINGLE_1), (190, "glass", 0, JINGLE_2), (215, "saucer", 0, JINGLE_1)],
                     "final": (55, "tube")},
    "eine-kleine-nachtmusik": {"title": "Eine kleine Nachtmusik", "composer": "Wolfgang Amadeus Mozart (1787)",
                               "sections": [(130, "wood", 0, NACHTMUSIK), (150, "tube", 0, NACHTMUSIK), (175, "glass", 12, NACHTMUSIK),
                                            (205, "saucer", 12, NACHTMUSIK)], "final": (43, "tube")},
})

def notes(song):
    """-> list of (t, midi, family, section_index) for every struck note, and the end time."""
    out, t = [], 0.6                     # first hit 0.6 s in (the marble is already falling in frame 1)
    for si, (bpm, fam, tr, seq) in enumerate(song["sections"]):
        e = 30.0 / bpm
        for m, n in seq:
            if m is not None: out.append((round(t, 4), m + tr, fam, si))
            t += n * e
    if song.get("final"):
        m, fam = song["final"]; out.append((round(t, 4), m, fam, len(song["sections"])))
        t += 0.2
    return out, t
