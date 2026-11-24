# What if you jumped into a hole straight through the Earth? (STORY A, 2026-11-24, category: What if)

## Facts (>= 2 sources each)
- Deepest hole: Kola Superdeep Borehole, Russia, 12,262 m (1989), ~20 years of drilling, ~180 °C at depth.
  - https://en.wikipedia.org/wiki/Kola_Superdeep_Borehole
  - https://www.scientificamerican.com/article/how-deep-is-the-deepest-hole-in-the-world/
  - https://www.livescience.com/50312-how-long-to-fall-through-earth.html ("only got 12 kilometers deep")
- Fall time end to end: 42 min 12 s for uniform density; 38 min (38 min 11 s) with Earth's real density (Klotz 2015, Am. J. Phys.).
  - https://arxiv.org/abs/1308.1342
  - https://www.livescience.com/50312-how-long-to-fall-through-earth.html
  - https://discovermagazine.com/the-sciences/journey-through-the-center-of-the-earth
- Speed: "over 8 km/s" (Klotz in Live Science); uniform-Earth check sqrt(gR) = 7.9 km/s (maths below), real Earth is faster.
- Core ~6,000 °C, as hot as the Sun's surface (2013 ESRF study):
  - https://www.smithsonianmag.com/smart-news/the-center-of-the-earth-is-as-hot-as-the-sun-43631207
  - https://www.ctvnews.ca/sci-tech/earth-s-core-1-000-degrees-hotter-than-thought-on-par-with-the-sun-1.1255356
- Earth's diameter ~12,742 km (2 x 6,371 km mean radius). Without air you oscillate like a pendulum (simple harmonic motion); air drag damps it so you settle at the centre (Klotz: assume the air is pumped out).

## Maths (python)
- v_max (uniform) = sqrt(9.81 * 6.371e6) = 7,906 m/s
- half period (uniform) = pi * sqrt(R/g) = 42.2 min
- London–Moscow ~2,500 km at 8 km/s = 5.2 min
