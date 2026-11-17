# Tour: one photo through AlterEgo Finder

GOAL:    a viewer who has never heard of the program knows what it does (drop a face, get the closest
         public figures with honest labels) and that it runs on their own computer.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, silent (it plays muted on the promo page).
TIME:    30 s x 30 fps = 900 frames.
LOOK:    the promo page's scorecard world. Ground #f4f7fb with a printed grid (40 px, rgba(29,60,120,.09));
         ink #1f2328; rule navy #1d3c78 for every display line and frame. Label colours appear only on
         labels: #1a7f37 Same person, #d4a72c Alter Ego, #8c959f Not You.
         Display: Barlow Condensed 700, uppercase, 72-150 px, tracking 0.01em. Body: Barlow 500, 30-34 px.
         The medium is the real product UI: screenshots of the running Streamlit app (pool of 500,
         query photo of Marie Curie), framed by a 3 px navy rule like the page's cards. No shadows,
         no grain, no vignette.
OBJECTS: the Curie photograph (a printed photo with its credit), the app window, the similarity
         target, the result cards with their real labels and photo credits.
MOTION:  enter expo.out, camera power2.inOut, exit power3.in. Titles per word: blur 6 px -> 0 and
         opacity 0 -> 1 in 0.13 s, 0.067 s apart. Exits 40-50% of entrances. Landed text holds still.
SHOTS:
  0-3 s     drop   "Who does she look like?" beside the Curie photo and its credit.
  3-9 s     drop   the app slides in; the photo is carried into the query box; the result replaces the
                   empty app. "Drop a face photo on the page." -> "It compares her with 500 public figures."
  9-16 s    target camera pushes from the whole app into the similarity target (2x).
                   "Closest: Marco van Basten, 0.2097" -> "Gold means Alter Ego: close, but not her."
  16-23.5 s cards  the ten real cards reveal left to right. "Four Alter Egos. The rest: Not You." ->
                   "Nobody reached Same person: that needs 0.3706."
  23.5-27 s local  push into the app's own line "Runs on this machine only..." "Nothing is uploaded."
  27-30 s   end    wordmark, the action (commands on this page), address, photo credits; held 2 s+.
BANNED:  dark void; glow; gradients; glass; everything centred; everything fading in at once;
         text moving while read; three cards in a row as a feature list; a title over a dimmed
         screenshot; invented UI; logo docked in a corner.
QA:      t=1.5 (hook readable), 5.0 (photo in the query box), 8.0, 12.5 (target labels readable),
         20.0 (card labels and credits readable), 25.5, 29.0 (address held).
