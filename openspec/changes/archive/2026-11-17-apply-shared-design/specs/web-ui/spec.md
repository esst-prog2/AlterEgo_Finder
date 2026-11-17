## ADDED Requirements

### Requirement: Shared look and logo
The page SHALL follow the project's shared design system (DESIGN.md): a
paper-coloured background, navy as the only accent colour, square corners,
the shared text and heading fonts, and the shared label colours, so that a
card's label, the target's dots, the promo page and the tour video use the
same green for Same person, gold for Alter Ego and grey for Not You. The
page SHALL show the AlterEgo Finder logo (the target in miniature beside
the name) at the top of its sidebar and as the browser-tab icon. Fonts and
the logo SHALL be served by the page itself from the user's machine; the
page SHALL NOT load fonts, images or styles from the network.

#### Scenario: Logo on the page
- **WHEN** the page is opened
- **THEN** the AlterEgo Finder logo appears at the top of the sidebar and
  as the browser tab's icon

#### Scenario: Shared label colours
- **WHEN** a match is shown
- **THEN** each card's label uses green #1a7f37 for Same person, gold
  #d4a72c for Alter Ego and grey #8c959f for Not You, the same colours as
  the target's dots for those labels

#### Scenario: Shared fonts and colours
- **WHEN** the page is opened
- **THEN** its background is the shared paper colour, its accent the
  shared navy, its text set in the shared body font and its headings in
  the shared display font

#### Scenario: Nothing loaded from the network
- **WHEN** the page is opened and a match is shown
- **THEN** every font, image and stylesheet it loads comes from the local
  server on localhost or is inline, and no request goes to another host
