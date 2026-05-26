// Experimental first-page English facsimile-translation for the 1957 journal article
// "Vũ-trụ-quan Phật học" from Phật Giáo Việt Nam.
//
// Render with:
//   make typst-facsimile

#set page(width: 140mm, height: 210mm, margin: 0mm)

#set text(
  font: ("Courier New", "Courier", "Times New Roman"),
  size: 7.55pt,
  lang: "en",
  fill: rgb("#120e0b"),
)

#set par(justify: true, leading: 0.36em, first-line-indent: 1.35em)

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
  #text(size: 7.15pt, weight: "bold")[#num.  ]
  #text(weight: "bold")[#heading]
  #h(0.2em)
  #text(size: 6.55pt, style: "italic", fill: soft-ink)[(#gloss)]
]

#let body-copy() = [
  #first-para()

  #v(1.15mm)
  #item-heading([1], [The tendency of fatalism], [Pubba-kata-hetu])

  The schools belonging to this tendency held that the whole natural world and the human
  world are arranged by predestination. Everything proceeds according to fixed natural laws
  already laid down. The value of human effort and material means is not acknowledged here.

  #v(0.95mm)
  #item-heading([2], [The tendency of theism, or divine will], [Issara-nimmāna-hetu])

  The schools belonging to this tendency held that all things exist through the will of a
  divine being. This divine being is Brahmā, and the center of the schools of this tendency
  is Brahmanism.

  #v(0.95mm)
  #item-heading([3], [The tendency of chance], [Ahetu-apaccaya])

  The schools belonging to this tendency did not admit the principle of causation. All
  phenomena arise and continue by chance, without following any law or principle at all.

  The first and second tendencies assign all responsibility to a supernatural power.
  Personal responsibility therefore does not become a real question; blessing and misfortune
  alike are things that human beings cannot determine.
]

#place(top + left)[
  #image(paper-texture, width: page-width, height: page-height)
]

#place(top + left, dx: 27.4mm, dy: 31.8mm)[
  #image(title-image, width: 83.5mm)
]

#place(top + left, dx: 94.2mm, dy: 72.8mm)[
  #box(inset: (x: 0.65mm, y: 0mm), stroke: 0.28pt + hairline)[
    #set text(
      font: ("Helvetica Neue", "Arial", "Helvetica"),
      size: 6.1pt,
      tracking: 0.15em,
      fill: soft-ink,
    )
    THAC-DUC
  ]
]

#place(top + left, dx: 15.8mm, dy: 90.8mm)[
  #box(width: 106.5mm)[
    #body-copy()
  ]
]

#place(top + left, dx: 15.5mm, dy: 179.9mm)[
  #line(length: 106.8mm, stroke: 0.42pt + hairline)
]

#place(top + left, dx: 13.7mm, dy: 181.4mm)[
  #set text(
    font: ("Helvetica Neue", "Arial", "Helvetica"),
    size: 6.1pt,
    tracking: 0.02em,
    fill: ink,
  )
  6
]

#place(top + left, dx: 98.8mm, dy: 181.6mm)[
  #set text(
    font: ("Helvetica Neue", "Arial", "Helvetica"),
    size: 6.7pt,
    tracking: 0.06em,
    fill: ink,
  )
  PHAT-GIAO VIET-NAM
]
