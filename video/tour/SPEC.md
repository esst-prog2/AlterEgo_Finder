# Tour: one photo through AlterEgo Finder

GOAL:    a viewer who has never heard of the program knows what it does (drop a face, get the closest
         public figures with honest labels) and that it runs on their own computer.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps. Music: "Carefree", Kevin MacLeod (incompetech.com), CC BY 4.0,
         first 30 s, 0.4 s fade-in, 2.5 s fade-out, -18 LUFS. It starts muted on the page and works without sound.
TIME:    30 s x 30 fps = 900 frames.
LOOK:    the promo page's scorecard world. Ground #eef3f8 (DESIGN.md paper) with a printed grid (40 px, rgba(29,60,120,.09));
         ink #1f2328; rule navy #1d3c78 for every display line and frame. Label colours appear only on
         labels: #1a7f37 Same person, #d4a72c Alter Ego, #8c959f Not You.
         Display: Barlow Condensed 700, uppercase, 72-150 px, tracking 0.01em. Body: Barlow 500, 30-34 px.
         The medium is the real product UI: screenshots of the running Streamlit app (pool of 500,
         query: a second photo of Leonardo DiCaprio, not the pool's own), framed by a 3 px navy rule like the page's cards. No shadows,
         no grain, no vignette.
OBJECTS: the DiCaprio photograph (a printed photo with its credit), the app window, the similarity
         target, the result cards with their real labels and photo credits.
MOTION:  enter expo.out, camera power2.inOut, exit power3.in. Titles per word: blur 6 px -> 0 and
         opacity 0 -> 1 in 0.13 s, 0.067 s apart. Exits 40-50% of entrances. Landed text holds still.
SHOTS:
  0-3 s     drop   "Brad Pitt or Leonardo DiCaprio?" beside a 2017 photo of DiCaprio and its credit.
  3-8 s     drop   the app slides in; the photo is carried into the query box; the result replaces the
                   empty app. "Ask AlterEgo Finder: drop the photo." -> "It compares him with 500 public figures."
  8-15 s    target camera pushes into the similarity target (2.4x). A ring draws round the one green dot:
                   "DiCaprio: inside the ring. Same person, 0.6867" -> round Brad Pitt's gold dot:
                   "Brad Pitt: 0.2109. Only an Alter Ego."
  15-21.5 s cards  the five real cards reveal, then pan to Brad Pitt. "A different photo, and it still finds
                   him." -> "Brad Pitt and three others: only lookalikes."
  21.5-25.5 s local push into the app's own line "Runs on this machine only..." "Try your own photo. It
                   never leaves your computer."
  25.5-30 s end  wordmark, the action (commands on this page), address, photo credits.
BANNED:  dark void; glow; gradients; glass; everything centred; everything fading in at once;
         text moving while read; three cards in a row as a feature list; a title over a dimmed
         screenshot; invented UI; logo docked in a corner.
BRAND:   the logo is the app's target in miniature (gold ring, green ring, navy cross, green dot) with
         "AlterEgo Finder" in Barlow Condensed, top right on every scene, beside the name on the end card.
         It uses the label colours on purpose: the mark is the target.
KEY:     during the target scene a key explains the numbers: score = how alike, 0 to 1; Same person
         0.37 and up; Alter Ego 0.19 to 0.37; Not you under 0.19.
QA:      t=1.5 (hook readable), 5.0 (photo in the query box), 8.0, 12.5 (target labels readable),
         20.0 (card labels and credits readable), 25.5, 29.0 (address held).
