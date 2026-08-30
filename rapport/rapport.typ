#set document(title: "La courbe des taux canadienne : ce que quarante ans disent, et ce qu'ils ne prédisent pas", author: "Guillaume Vaudescal")
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
    #text(size: 18pt, weight: "bold")[La courbe des taux canadienne : ce que quarante ans disent, et ce qu'ils ne prédisent pas]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-08-30 · #link("https://github.com/Guilou001/11-courbe-des-taux")[Guilou001/11-courbe-des-taux]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Trois exercices sur la courbe zéro-coupon de la Banque du Canada (10 596 jours, 1986-2026) : la prévision de Diebold et Li rejouée hors échantillon, le probit de récession avec et sans prime de terme, et un module ALM sous les chocs réglementaires IRRBB. _English summary below._

Le même contenu en PDF : #link("rapport/rapport.pdf")[rapport/rapport.pdf].

== En bref

+ *La marche aléatoire bat le Nelson-Siegel dynamique sur la courbe canadienne.* Sur 367 origines mensuelles 1996-2026 (356 à l'horizon d'un an), le modèle de Diebold et Li fait pire que « demain égale aujourd'hui » dans 26 cases sur 27 (maturité x horizon), significativement à 1 et 6 mois. Le résultat américain de 2006 ne se transpose pas. (Mesuré.)
+ *Hors échantillon, la pente canadienne prédit les récessions au niveau du hasard.* AUROC de 0,50 pour la pente brute, et 0,27 en retirant la fenêtre COVID : les inversions de 2000, 2006-07 et 2022-24 n'ont été suivies d'aucune récession dans les 12 mois, celle de 2019 ne l'a été que par la pandémie (que la courbe ne pouvait pas prédire), et la récession de 2008 est arrivée sans inversion franche. La pente nette de prime de terme, censée corriger le signal, fait pire sur son échantillon court. (Mesuré.)
+ *En ALM, la forme du choc compte autant que son ampleur.* Le choc réalisé de 2022 (+412 pb à 3 mois) dépasse le gabarit réglementaire court (275 pb), mais son profil d'aplatissement limite la perte du bilan stylisé à 2,3 G\$, contre 3,7 G\$ pour les pires gabarits (parallèle hausse et pentification, à 0,04 G\$ l'un de l'autre). (Mesuré sur bilan précepte.)

Le fil du portfolio, ce qui survit hors échantillon, donne ici son épisode le plus net : deux outils canoniques de la courbe des taux, célèbres sur données américaines d'avant 2000, ne survivent ni l'un ni l'autre au Canada d'après 1996.

== La question

Diebold et Li (2006) montrent qu'un modèle à trois facteurs prévoit la courbe américaine mieux que la marche aléatoire à 12 mois ; Estrella et Mishkin (1998) montrent que la pente prédit les récessions. Or la courbe canadienne s'est inversée 29 mois d'affilée en 2022-24 sans qu'aucune récession ne suive (chronologie C.D. Howe, décision 2024). Ces deux résultats fondateurs tiennent-ils encore, hors échantillon, sur les données canadiennes ?

== Les données (100 % libres, téléchargées par script, jamais commitées)

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Source*],
    [*Contenu*],
    [*Période*],
    [*Statut*],
    [Banque du Canada, courbe zéro-coupon],
    [120 maturités (0,25 à 30 ans), quotidien],
    [1986-01-02 au 2026-08-12 (10 596 lignes, 9 971 jours cotés)],
    [mesuré],
    [Valet #raw("FVI_FINANCIAL_MARKETS_TP_GOC")],
    [prime de terme ACM à 10 ans],
    [1995-01 au 2026-06],
    [mesuré],
    [C.D. Howe, Business Cycle Council],
    [pics et creux mensuels, 12 récessions 1929-2020],
    [colonne révisée 2021],
    [mesuré],
)

Trois précisions de première main. Les 20 maturités les plus longues (25,25 à 30 ans) manquent avant janvier 1991 ; les paires concernées sont écartées de l'évaluation, pas imputées. La prime de terme ACM à 10 ans ne commence qu'en 1995, pas en 1990 comme le groupe Valet qui l'héberge : l'échantillon commun des trois pentes part de 1995. La chronologie C.D. Howe existe en deux versions ; le dépôt lit la colonne révisée de 2021 (creux de 1992 en mai, épisode de 1980 retiré) et le déclare.

La courbe est publiée en composition continue (Bolder, Johnson et Metzler 2004 ; rapporté par BIS Papers 25). Tout le dépôt garde cette convention : le taux forward entre t1 et t2 vaut (z2 t2 - z1 t1)/(t2 - t1) et le facteur d'actualisation exp(-z t).

== Volet 1 : trois nombres résument une courbe

Le modèle de Nelson et Siegel écrit chaque courbe comme la somme de trois formes : un niveau (la même valeur à toutes les échéances), une pente (forte au court terme, nulle au long) et une courbure (maximale au milieu). Le paramètre de décroissance lambda, qui fixe l'échéance où la courbure culmine, est repris de Diebold et Li : 0,0609 par mois, soit 0,7308 par année, et un maximum de courbure à 2,5 ans. Il n'est pas réoptimisé.

Chaque mois, les trois betas sont estimés par moindres carrés sur la seule coupe du mois : aucune information future n'entre dans l'ajustement. Sur 488 mois, l'erreur d'ajustement moyenne est de 14,1 pb, et les facteurs retrouvent leurs jumeaux observables : corrélation de 0,986 entre le niveau et le taux 10 ans, de 0,992 entre la pente (au signe près) et l'écart 10 ans moins 3 mois, de 0,799 entre la courbure et son proxy papillon. (Mesuré.)

#figure(image("../results/figures/facteurs_ns.png", width: 100%), caption: [Facteurs Nelson-Siegel])

*Comment lire cette figure.* Trois panneaux, un par facteur, bandes grises aux récessions C.D. Howe. Le niveau (haut) tombe de 10 % en 1990 à 1 % en 2020 puis remonte vers 4 % : c'est la grande désinflation, puis 2022. La pente (milieu) est négative quand la courbe monte avec l'échéance, la situation normale ; ses pics au-dessus de zéro sont les inversions : 1990, brièvement 2000 et 2007, puis le plateau de 2022-24. La courbure (bas) plonge dans les récessions.

#figure(image("../results/figures/courbes_instantanees.png", width: 100%), caption: [Instantanés de courbe])

*Comment lire cette figure.* Cinq coupes de la même surface : avril 1990 (de 10 à 13,4 %, courbe inversée), juin 2007 (plate à 4,5 %), juillet 2020 (écrasée sous 1 %), décembre 2022 (inversée : 4,7 % à 1 an, 3,3 % à 10 ans), et la dernière courbe disponible. La coupe de 1990 s'arrête à 25 ans : le très long bout n'est publié qu'à partir de 1991.

== Volet 2 : Diebold-Li contre la marche aléatoire, et la marche aléatoire gagne

Le protocole suit l'article de 2006. À chaque fin de mois t depuis janvier 1996, un AR(1), une régression du facteur sur sa propre valeur du mois précédent, est estimé par facteur sur les betas connus jusqu'à t seulement, en fenêtre expansive, puis itéré à 1, 6 et 12 mois ; la courbe prévue se reconstruit avec les charges de Nelson-Siegel. Deux adversaires : la marche aléatoire, qui prédit que la courbe de t + h sera celle de t, et un AR(1) appliqué directement à chaque rendement. La cible est la courbe réalisée en t + h, sur neuf maturités de 3 mois à 30 ans.

Ratio de RMSE du DNS contre la marche aléatoire (sous 1, le modèle gagne ; mesuré, #raw("results/tables/rmse_prevision.csv")) :

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Maturité*],
    [*h = 1 mois*],
    [*h = 6 mois*],
    [*h = 12 mois*],
    [3 mois],
    [1,456],
    [1,068],
    [*0,988*],
    [2 ans],
    [1,154],
    [1,131],
    [1,112],
    [5 ans],
    [1,100],
    [1,168],
    [1,222],
    [10 ans],
    [1,102],
    [1,176],
    [1,246],
    [30 ans],
    [1,643],
    [1,370],
    [1,396],
)

*Lecture guidée.* La seule case sous 1 est le taux 3 mois à horizon 12 mois (0,988), et le test de Diebold-Mariano ne la distingue pas du hasard (p = 0,85). Partout ailleurs le DNS perd, de 6 % à 64 %, et la perte est significative à 1 mois (p \< 0,001 sur les neuf maturités) comme à 6 mois (p \< 0,05 sur huit maturités sur neuf). L'AR(1) direct perd aussi, mais moins : la structure de facteurs n'apporte rien que la persistance de chaque taux ne contienne déjà. À titre d'échelle, la marche aléatoire se trompe de 21 pb à 1 mois et de 69 pb à 12 mois sur le taux 10 ans.

Chez Diebold et Li, sur la courbe américaine 1994-2000, le DNS gagnait environ 20 % sur la marche aléatoire à 12 mois (rapporté, leur tableau 6). Sur la courbe canadienne 1996-2026, rien de tel ne survit. Ce n'est pas un échec d'implémentation : le même code retrouve exactement des betas connus sur courbes synthétiques (testé), et la littérature d'après-publication (Duffee 2002 sur la faiblesse prédictive des modèles affines) pointait déjà dans cette direction.

#figure(image("../results/figures/prevision_rmse.png", width: 100%), caption: [Prévision])

*Comment lire cette figure.* Un panneau par horizon, le ratio de RMSE en ordonnée, la ligne à 1 marque l'égalité avec la marche aléatoire. Tout point au-dessus de 1 est une défaite du modèle. Le pic à 30 ans vient du très long bout, que trois facteurs ajustent mal ; le pic à 3 mois et h = 1 vient de l'erreur d'ajustement transversal, que la marche aléatoire n'a pas à payer.

== Volet 3 : la pente prédit-elle encore les récessions ? Hors échantillon, non

Trois variables mensuelles, en points de pourcentage. La pente brute : taux 10 ans moins taux 3 mois. La pente nette : la même, moins la prime de terme ACM à 10 ans, l'estimation par la Banque du Canada de la rémunération exigée pour porter le risque de duration ; ce qui reste est l'écart des anticipations de taux courts, la composante que la théorie relie au cycle (la prime du 3 mois est traitée comme nulle, approximation déclarée). L'écart forward de court terme d'Engstrom et Sharpe : le taux 3 mois attendu dans 6 trimestres, calculé du forward 1,50-1,75 an, moins le taux 3 mois courant.

La cible vaut 1 si un mois de récession survient dans les 12 mois suivants ; un mois de récession court du mois suivant le pic C.D. Howe au creux inclus (convention déclarée). Le probit est estimé en fenêtre expansive depuis 1996, et la cible du mois t n'entre dans l'estimation qu'à partir de t + 12, quand elle devient observable : rien ne fuit.

Résultats (mesuré, #raw("results/tables/probit_recession.csv")) :

#table(
  columns: 8,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Variable*],
    [*Échantillon*],
    [*AUROC in*],
    [*IC 90 % (blocs)*],
    [*AUROC hors éch.*],
    [*idem, hors COVID*],
    [*Prob. max 2022-23*],
    [*Prob. max avant oct. 2008*],
    [Pente brute],
    [1986-],
    [0,706],
    [0,52 à 0,90],
    [0,499],
    [0,266],
    [0,594],
    [0,280],
    [Pente nette de prime],
    [1995-],
    [0,428],
    [0,28 à 0,62],
    [0,155],
    [0,154],
    [0,160],
    [non calculable],
    [Écart forward],
    [1986-],
    [0,728],
    [0,57 à 0,90],
    [0,539],
    [0,362],
    [0,725],
    [0,277],
)

*Lecture guidée, épisode par épisode.* L'AUROC, la probabilité qu'un mois d'avant récession reçoive un score plus alarmant qu'un mois ordinaire, vaut 0,5 pour une pièce de monnaie. En échantillon, la pente brute affiche 0,71, mais l'intervalle de confiance par bootstrap de blocs descend à 0,52 : trois récessions depuis 1986, cela ne fait pas une loi. Hors échantillon, tout s'effondre, et le détail des inversions dit pourquoi (mesuré, #raw("results/tables/pentes_mensuelles.csv")) :

- 1988-09 à 1991-03, 31 mois d'inversion jusqu'à -3,1 pp : la récession de 1990-92 suit.

C'est le seul succès, et il est dans l'échantillon d'apprentissage.

- 2000 : deux brèves inversions (-0,2 pp). Récession américaine en 2001, aucune au Canada.
- 2006-08 à 2007-07 : dix mois d'inversion peu profonde (-0,26 pp). Le premier mois de

récession, novembre 2008, tombe 16 mois après la dernière inversion : la fenêtre de 12 mois manque l'épisode. À la veille de la crise, le probit ne donnait que 28 % de probabilité.

- 2019 : sept mois d'inversion, puis la pandémie. Le « succès » de 2020 est un accident :

aucune courbe de taux ne prédit un virus, et retirer cette fenêtre fait TOMBER l'AUROC hors échantillon sous 0,5 : le classement devient pire que le hasard.

- 2022-07 à 2024-11, 29 mois jusqu'à -2,0 pp, la plus longue inversion depuis 1990 :

probabilité montée à 59 %, et aucune récession (décision C.D. Howe de 2024).

La pente nette, l'idée défendue pour 2022-23 (la prime de terme négative rendait la pente brute trompeuse), ne sauve rien : sur son échantillon 1995-2026, son coefficient sort du mauvais signe et son AUROC est sous 0,5, car ses deux récessions observables (2008, 2020) sont précisément celles que la pente ne voit pas. Allonger la fenêtre à 18 mois, pour donner sa chance à l'épisode 2006-08, remonte la pente brute à 0,58 hors échantillon (0,41 hors COVID) mais gonfle la fausse alarme de 2022-23 à 80 % (#raw("results/tables/probit_recession_h18.csv") ; l'estimation y attend t + 18 avant d'utiliser une cible, même règle anti-fuite qu'à 12 mois).

#figure(image("../results/figures/probit_recession.png", width: 100%), caption: [Probit de récession])

*Comment lire cette figure.* En haut, les deux pentes ; sous zéro, la courbe est inversée ; bandes grises aux récessions. En bas, les probabilités hors échantillon des trois variables. Le sommet jaune de 2010 est un artefact d'échantillon court : le probit de la pente nette, estimable seulement depuis fin 2008, sort avec un signe instable. Les sommets de 2022-24 (59 à 73 %) ne sont suivis d'aucune bande grise : c'est la fausse alarme centrale du dépôt.

== Volet 4 : l'ALM, où la forme du choc compte autant que l'ampleur

Un bilan de banque de détail stylisé (précepte déclaré, 100 G\$ d'actifs) : hypothèques 5 ans (45), obligations 10 ans (20), prêts à taux variable (25), encaisse (10), contre dépôts à vue à duration comportementale de 2,5 ans (40), CPG 1,5 an (30) et financement de gros 2 ans (22). La duration comportementale, l'échéance effective que la banque prête à des dépôts remboursables à vue, est un précepte : le cadre standardisé de Bâle (d368) plafonne à 5 ans l'échéance moyenne de la part stable des dépôts de détail transactionnels (rapporté) ; la ligne directrice B-12 de l'OSFI exige des hypothèses comportementales documentées sans fixer de plafond chiffré (rapporté).

Chaque poste est revalorisé flux par flux sur la courbe du 2026-08-12, puis sous les six scénarios IRRBB du gabarit CAD recalibré du Comité de Bâle (d578, 2024, en vigueur depuis janvier 2026, rapporté) : parallèle 200 pb, choc court 275 pb décroissant en exp(-t/4), choc long 175 pb, pentification et aplatissement combinés. S'y ajoute un scénario mesuré : le déplacement réellement observé de décembre 2021 à décembre 2022, soit +412 pb à 3 mois et +180 pb à 10 ans.

Delta-EVE, la variation de valeur économique des fonds propres (mesuré sur bilan précepte, #raw("results/tables/delta_eve.csv")) :

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Scénario*],
    [*Delta-EVE (G\$)*],
    [Parallèle hausse],
    [*-3,72*],
    [Parallèle baisse],
    [+4,61],
    [Pentification],
    [-3,68],
    [Aplatissement],
    [+2,75],
    [Court hausse / baisse],
    [+0,45 / -0,47],
    [*2022 mesuré*],
    [*-2,31*],
)

*Lecture guidée.* Le bilan est long en duration (actifs à 5-10 ans, passifs à 1,5-2,5 ans) : toute hausse du long bout coûte. Le pire scénario est le parallèle hausse, d'un cheveu (0,04 G\$) devant la pentification : cet ordre-là n'est pas robuste aux montants du bilan précepte, et c'est déclaré ; ce qui est robuste, c'est que les deux chocs qui montent le long bout font perte, et les deux qui l'abaissent font gain. Et 2022, pourtant plus violent que tout gabarit au court terme (412 pb contre 275), coûte un tiers de moins que le pire scénario : c'était un aplatissement, et l'aplatissement est le scénario ami de ce bilan. Le revenu net d'intérêts à 12 mois sous +200 pb ne dépend pas d'abord de la structure d'échéances mais du bêta de dépôt, la part du choc répercutée sur le coût des dépôts à vue : il vaut *+0,558 G\$ à bêta nul, +0,158 G\$ à bêta 0,5 et −0,242 G\$ à bêta 1* (mesuré, #raw("results/tables/delta_nii.csv"), bilan précepte). L'audit du 2026-08-29 a montré que la première version confondait la duration comportementale des dépôts, 2,5 ans, avec leur date de refixation : aucun passif n'entrait alors dans la fenêtre de douze mois et le gap était positif par construction. La somme des durations par taux clés de l'obligation 10 ans (8,34) retrouve sa duration totale (test).

#figure(image("../results/figures/delta_eve.png", width: 100%), caption: [Delta-EVE])

*Comment lire cette figure.* Une barre par scénario ; rouge, une perte ; vert, un gain ; bleu, le choc mesuré de 2022. La barre de 2022 est plus courte que celle de la pentification : l'ampleur historique du choc ne suffit pas à en faire le pire cas.

Le classeur #raw("reports/calculs_obligataires.xlsx") refait tout en formules Excel vivantes : prix par actualisation flux par flux (EXP(-z t), RECHERCHEV exacte sur la grille de la courbe), duration de Macaulay, et revalorisation sous les six chocs. Changez le coupon ou l'échéance (arrondie au pas de coupon, 30 ans au plus), tout se recalcule. (Généré par #raw("ycc alm") ; la fonction Python que les formules reproduisent est vérifiée sur cas plat contre la forme fermée, test #raw("test_bond_price_flat_curve_closed_form") ; les formules Excel elles-mêmes sont relues, non évaluées automatiquement, déclaré.)

== Reproduire

#raw("uv sync --locked --all-extras\nuv run pytest              # 15 tests synthétiques, sans réseau\nuv run ycc fetch           # ~21 Mo : courbe BdC, primes Valet, chronologie C.D. Howe\nuv run ycc factors         # betas NS, figures des facteurs et instantanés\nuv run ycc forecast        # 367 origines x 3 horizons x 3 modèles (~1 min)\nuv run ycc recession       # probit, AUROC bootstrap, probabilités hors échantillon\nuv run ycc alm             # Delta-EVE, KRD, Delta-NII, classeur Excel", block: true, lang: "bash")

Les tests vérifient chaque brique contre une vérité connue : l'ajustement NS retrouve exactement des betas synthétiques, l'AR(1) retrouve une persistance connue, le forward d'une courbe plate est plat, le prix d'une obligation sur courbe plate égale la forme fermée, la duration d'un zéro-coupon égale son échéance, les durations par taux clés somment à la duration totale, et le Diebold-Mariano détecte un modèle dominé.

== Limites, avec statut

+ *Trois récessions depuis 1986.* Aucune conclusion probabiliste ferme n'est possible avec trois événements ; les intervalles par bootstrap de blocs sont là pour le rappeler (largeur moyenne de 0,35 d'AUROC, mesuré). Le verdict est un constat d'échec hors échantillon, pas une preuve d'inutilité de la pente.
+ *La prime de terme est elle-même un modèle.* L'ACM canadien est estimé par la Banque du Canada ; la pente « nette » hérite de ses erreurs (rapporté). Sa version à taux fantôme existe dans le même groupe Valet et n'est pas exploitée ici.
+ *Le DNS est le représentant le plus simple de sa famille.* Un filtre de Kalman (estimation d'état en une étape) ou un ajout macro (Diebold, Rudebusch et Aruoba 2006) pourrait faire mieux ; non testé ici, déclaré comme suite naturelle.
+ *Le bilan ALM est un précepte.* Les montants et durations sont plausibles mais posés ; le verdict porte sur la hiérarchie des scénarios pour un bilan de détail classique, pas sur une banque réelle. Les rapports aux actionnaires des banques canadiennes publient leurs sensibilités réelles ; le rapprochement est une suite possible.
+ *Le très long bout manque avant 1991* (mesuré) et l'ajustement NS y reste fragile (ratio de 1,4 à 1,6 au 30 ans) : les conclusions du volet 2 sont les plus solides entre 3 mois et 20 ans.

== Références

- Diebold, F. X. et C. Li (2006), « Forecasting the term structure of government bond

yields », _Journal of Econometrics_ 130(2), 337-364. PDF libre chez Diebold.

- Estrella, A. et F. S. Mishkin (1998), « Predicting U.S. recessions », _REStat_ 80(1).
- Engstrom, E. et S. Sharpe (2019), « The near-term forward yield spread as a leading

indicator », _FEDS Notes_ et _Financial Analysts Journal_ 75(4).

- Bolder, D. J., G. Johnson et A. Metzler (2004), « An empirical analysis of the Canadian

term structure of zero-coupon interest rates », Banque du Canada, WP 2004-48.

- Poulin-Moore, A. et K. Tuzcuoglu (2024), « Forecasting recessions in Canada », Banque

du Canada, SWP 2024-10.

- Atta-Mensah, J. et G. Tkacz (1998), « Predicting Canadian recessions using financial

variables », Banque du Canada, WP 98-5.

- Comité de Bâle (2016, d368 ; recalibrage 2024), norme IRRBB ; OSFI, ligne directrice

B-12.

- C.D. Howe Institute, Business Cycle Council, chronologie des récessions canadiennes.

== English summary

Three exercises on the Bank of Canada zero-coupon curve (10,596 days, 1986-2026, 120 maturities). (1) Dynamic Nelson-Siegel vs. random walk, 367 monthly out-of-sample origins: the random walk wins in 26 of 27 maturity-horizon cells; the only DNS win (3-month yield, 12-month horizon, ratio 0.988) is statistically indistinguishable from luck. The celebrated US result does not carry over to Canada. (2) Recession probits on the raw slope, the ACM term-premium-adjusted slope, and the near-term forward spread: out-of-sample AUROC is 0.50 for the raw slope, and drops BELOW 0.5 excluding the COVID window, because the 2000, 2006-07 and 2022-24 inversions were followed by no C.D. Howe recession within 12 months (the 2019 inversion was only "followed" by the pandemic, which no yield curve predicts) while October 2008 arrived without a deep inversion. The term-premium correction makes things worse on its short 1995- sample. (3) A stylized 100-G\$ retail-bank balance sheet under the six recalibrated Basel IRRBB shocks (CAD: 200/275/175 bp, d578) plus the measured Dec-2021 to Dec-2022 curve move: the realized 2022 shock exceeds the short-rate template (+412 bp at 3 months) yet costs -2.3 G\$ against -3.7 G\$ for the worst templates (parallel up and steepener, within 0.04 G\$ of each other), because its flattening shape favours a long-duration book. A live-formula Excel workbook reprices the bond under every scenario. All data free and script-downloaded; 15 synthetic tests, each against a known truth.

== Licence et citation

Code sous licence MIT ; rapport et figures CC BY 4.0. Données : Banque du Canada (conditions d'utilisation de la Banque, attribution requise), C.D. Howe (document public cité). Citer via #raw("CITATION.cff").
