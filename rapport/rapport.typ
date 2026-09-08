#set document(title: "Les taux d'intérêt d'aujourd'hui aident-ils à prévoir demain ?", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [yield-curve-ca], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Les taux d'intérêt d'aujourd'hui aident-ils à prévoir demain ?]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-08 · #link("https://github.com/Guilou001/11-courbe-des-taux")[Guilou001/11-courbe-des-taux]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Prêter de l'argent pendant trois mois ou pendant dix ans ne rapporte pas le même taux. La courbe des taux rassemble ces taux selon la durée du prêt.

Sa forme peut donner des indices sur l'avenir. Ce projet vérifie ce qu'ils valent au Canada en comparant des prévisions faites avec les seules observations passées.

*Pour prévoir les taux, garder le taux actuel fait mieux que le modèle étudié dans 26 comparaisons sur 27.*

== Une prévision simple comme point de comparaison

Le modèle de Diebold et Li résume la courbe par son niveau, sa pente et sa courbure, puis prévoit l'évolution de ces trois éléments. Il est comparé à une règle qui annonce simplement le taux d'aujourd'hui pour la date future.

#figure(image("../results/figures/presentation.png", width: 100%), caption: [Erreur de prévision du modèle comparée à celle du taux inchangé])

La ligne à 1 représente une égalité. Au-dessus, le modèle se trompe davantage que la règle simple. Chaque panneau correspond au délai avant la date prévue.

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Taux à prévoir*],
    [*Dans un mois*],
    [*Dans six mois*],
    [*Dans un an*],
    [Prêt à trois mois],
    [1,456],
    [1,068],
    [0,988],
    [Prêt à cinq ans],
    [1,100],
    [1,168],
    [1,222],
    [Prêt à dix ans],
    [1,102],
    [1,176],
    [1,246],
)

Par exemple, 1,246 signifie une erreur environ 25 % plus grande. Le test commence en 1996 et utilise les courbes disponibles jusqu'en août 2026. La petite victoire à 0,988 ne se distingue pas du hasard au test employé. #link("results/tables/rmse_prevision.csv")[Les 27 comparaisons].

== Deux autres usages de la même courbe

Le dépôt teste aussi l'idée qu'un taux court supérieur au taux long annonce une récession. Sur les mois gardés pour l'évaluation, le score de classement est de 0,50, le niveau du hasard. Le très petit nombre de récessions empêche d'en tirer une règle générale.

Enfin, il applique des hausses de taux à un bilan bancaire fictif de 100 milliards de dollars canadiens. La perte dépend des échéances qui montent, pas seulement de la plus forte hausse. Un #link("reports/calculs_obligataires.xlsx")[classeur obligataire] permet de modifier les hypothèses.

== Ce que le résultat permet de dire

Ce modèle précis n'améliore pas les prévisions sur cet échantillon canadien. Cela ne prouve ni que tous les modèles de taux échouent, ni que les taux ne contiennent aucune information économique. Le bilan bancaire est construit pour l'exercice et ne représente aucune banque réelle.

== Refaire les calculs

#raw("uv sync --locked --all-extras\nuv run pytest\nuv run ycc fetch\nuv run ycc factors\nuv run ycc forecast\nuv run ycc recession\nuv run ycc alm", block: true, lang: "bash")

Les commandes de téléchargement accèdent aux sources externes. Les résultats publiés restent consultables sans lancer les calculs. Le graphique de présentation se régénère hors réseau avec #raw("uv run python scripts/figure_presentation.py"), depuis les tableaux publiés.

== Pour aller plus loin

#link("docs/ETUDE_DETAILLEE.md")[Méthodes, résultats complets et références] · #link("rapport/rapport.pdf")[Présentation en PDF] · #link("CITATION.cff")[Citer le projet] · #link("LICENSE")[Licence].

== English summary

A three-factor yield-curve model loses to unchanged-rate forecasts in 26 of 27 Canadian comparisons. Separate exercises examine recession signals and interest-rate losses on a hypothetical bank balance sheet.
