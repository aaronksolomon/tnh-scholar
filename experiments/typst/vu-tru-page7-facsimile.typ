// Experimental first-page English facsimile-translation for the 1957 journal article
// "Vũ-trụ-quan Phật học" from Phật Giáo Việt Nam.
//
// Render with:
//   make typst-facsimile

#set page(width: 140mm, height: 210mm, margin: 0mm)

#set text(
  font: ("Libertinus Serif", "New Computer Modern", "Georgia", "Times New Roman"),
  size: 6.7pt,
  lang: "en",
  fill: rgb("#1a1611"),
)

#set par(justify: true, leading: 0.34em, first-line-indent: 1.45em)

#let page-width = 140mm
#let page-height = 210mm
#let ink = rgb("#17130f")
#let soft-ink = rgb("#383026")
#let hairline = rgb("#6c6251")
#let title-image = "assets/title-buddhist-cosmology-din-tight.png"
#let paper-texture = "assets/page7-paper-texture.png"

#let first-para() = [
  In the time of the Buddha, the question of the first principle of all things held a very
  important place in the intellectual life of India. The Brahmajāla Sutta records as many
  as sixty-two different explanations offered by the Indian philosophical schools of that
  age. Broadly speaking, we can see three principal tendencies:
]

#let item-heading(num, heading, gloss) = [
  #set par(first-line-indent: 0em)
  #text(size: 6.35pt, weight: "medium")[#num.  ]
  #text(weight: "semibold")[#heading]
  #h(0.2em)
  #text(size: 5.55pt, style: "italic", fill: soft-ink)[(#gloss)]
]

#let body-copy() = [
  #first-para()

  #v(1.35mm)
  #item-heading([1], [The tendency of fatalism], [Pubba-kata-hetu])

  The schools belonging to this tendency held that the whole natural world and the human
  world are arranged by predestination. Everything proceeds according to fixed natural laws
  already laid down. The value of human effort and material means is not acknowledged here.

  #v(1.1mm)
  #item-heading([2], [The tendency of theism, or divine will], [Issara-nimmāna-hetu])

  The schools belonging to this tendency held that all things exist through the will of a
  divine being. This divine being is Brahmā, and the center of the schools of this tendency
  is Brahmanism.

  #v(1.1mm)
  #item-heading([3], [The tendency of chance], [Ahetu-apaccaya])

  The schools belonging to this tendency did not admit the principle of causation. All
  phenomena arise and continue by chance, without following any law or principle at all.

  The first and second tendencies assign all responsibility to a supernatural power.
  Personal responsibility therefore does not become a real question; blessing and misfortune
  alike are things that human beings cannot determine. Good and evil actions on the part of
  human beings are not regarded as the motive force behind success or failure, growth or
  decline.

  The third tendency also cannot establish any basis for personal moral responsibility. If
  everything is mere chance, then good is also chance, evil is also chance, fortune and
  misfortune are also chance; there is nothing that can serve as a standard for human
  conduct. Because of this, human beings cannot gradually advance toward truth, beauty, and
  goodness. On the contrary, they may very easily slide down the slope of wrongdoing and
  corruption.

  From the point of view of theory, the doctrines belonging to these tendencies all have
  many shortcomings. From the point of view of human life, the consequences they bring are
  dark and discouraging. None of them can give a person peace of mind or a secure ground
  for life, nor do they affirm the necessary and already present capacities of the human
  being.
]

#place(top + left)[
  #image(paper-texture, width: page-width, height: page-height)
]

#place(top + left, dx: 33.4mm, dy: 36.6mm)[
  #image(title-image, width: 63.2mm)
]

#place(top + left, dx: 86.4mm, dy: 68.7mm)[
  #box(inset: (x: 0.65mm, y: 0mm), stroke: 0.28pt + hairline)[
    #set text(
      font: ("Helvetica Neue", "Arial", "Helvetica"),
      size: 5.4pt,
      tracking: 0.15em,
      fill: soft-ink,
    )
    THAC-DUC
  ]
]

#place(top + left, dx: 14.5mm, dy: 82.2mm)[
  #box(width: 108.5mm)[
    #body-copy()
  ]
]

#place(top + left, dx: 100.5mm, dy: 186.7mm)[
  #set text(
    font: ("Helvetica Neue", "Arial", "Helvetica"),
    size: 5.9pt,
    tracking: 0.06em,
    fill: ink,
  )
  PHAT-GIAO VIET-NAM
]
