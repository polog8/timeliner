# Journal des modifications

Récapitulatif de tout ce qui a été corrigé et ajouté depuis la version initiale
du dossier `Code` (commit `2f04b22`, `code.gs` 290 lignes + `index.html` 2015 lignes).
État actuel : `code.gs` 616 lignes, `index.html` 3401 lignes, plus un dossier `Template`.

Les fonctions et la logique de fonctionnement d'origine ont été conservées — voir
la section « Ce qui n'a pas changé » en fin de document.

Le document couvre les deux séries de modifications : la reprise initiale, puis les
retours qui ont suivi (débordement des libellés, rafraîchissement automatique,
correction du FTE), puis l'édition complète depuis le Gantt et trois fonctionnalités
d'analyse. Les ajouts de la seconde série sont signalés par **[v2]**, ceux de la
troisième par **[v3]**.

---

## 1. Bugs corrigés

### 1.1 Corruption silencieuse des dates (le plus grave)

- **Décalage d'un jour à chaque écriture dans la feuille.** Les dates étaient
  réécrites via `toISOString()` (11 occurrences), qui convertit minuit *local* en
  UTC. Dans tout fuseau UTC+, chaque tâche ou gate déplacée était enregistrée
  **un jour trop tôt**, sans aucun message d'erreur.
  Reproduit sur le code d'origine : à Paris, déplacer une tâche commençant le
  2026-01-01 écrivait `2025-12-31` dans la feuille.
  → Toute l'arithmétique de dates passe désormais par des numéros de jour UTC, et
  les chaînes ISO sont construites à la main. Vérifié stable en UTC, Europe/Paris,
  America/Los_Angeles et Pacific/Kiritimati.

- **Dates écrites en texte.** `shiftAllDates`, `updateTaskDates`, `updateGateDate`
  et `updateTaskDetails` écrivaient des chaînes `"2026-01-05"` dans des cellules
  date, dégradant leur format.
  → De véritables objets `Date` sont écrits, la cellule conserve son format et se
  relit correctement.

### 1.2 Plantages

- **`fetchDataViaGViz()` n'existait pas.** La fonction était appelée à deux
  endroits (`index.html` lignes 1285 et 1292) en cas d'échec du backend, mais
  **n'était définie nulle part** → `ReferenceError`. Tout incident Apps Script sur
  une feuille connectée cassait l'application au lieu de basculer sur le secours.
  → Réellement implémentée : lecture directe de la feuille via l'endpoint GViz
  (JSONP, donc sans problème CORS), en lecture seule et signalée comme telle.

- **`getPlannerData` plantait sur les feuilles étroites.** `getRange(1, 1, 1, 12)`
  avec `planLastCol = Math.max(12, …)` levait une exception sur toute feuille de
  moins de 12 colonnes.
  → Toutes les lectures sont bornées aux dimensions réelles de l'onglet
  (`readBlock_`). Testé sur une feuille de 8 colonnes.

- **`doGet` chargeait `'Index'`** alors que le fichier du projet s'appelle `index`
  (`createHtmlOutputFromFile` est sensible à la casse).
  → Les trois orthographes sont essayées, avec un message clair si aucune n'existe.

- **Les nombres étaient lus comme des timestamps.** Dans `parseDateVal`, un
  `typeof val === 'number'` faisait `new Date(val)`, interprétant le numéro de
  série Sheets (~46000) comme des millisecondes → toute date numérique devenait
  janvier 1970.
  → Les numéros de série (base 1899-12-30), les objets `Date`, l'ISO, le
  `jj/mm/aaaa` et le `mm/jj/aaaa` sont gérés ; les dates impossibles (31/02) sont
  rejetées au lieu de basculer sur mars.

- **`onError` était défini deux fois** (lignes 1222 et 1300) : la première
  définition était écrasée en silence.
  → Une seule définition.

### 1.3 Sécurité et robustesse

- **Injection HTML.** Titres, unités, commentaires et noms de gates partaient
  directement dans `innerHTML` sans échappement (aucune fonction d'échappement
  dans le fichier d'origine).
  → `escapeHtml` appliqué systématiquement (30 points d'appel). Vérifié : un titre
  `<b>item</b>` s'affiche littéralement et n'est pas interprété.

- **`localStorage` non protégé.** Deux appels directs, zéro `try`/`catch` dans tout
  le fichier : une iframe sandboxée ou une fenêtre privée faisait échouer le
  démarrage.
  → Tous les accès sont encapsulés ; l'application démarre normalement sans
  stockage, seules les préférences ne persistent pas.

- **Écritures non validées.** `updateTaskDates`, `updateGateDate` et
  `updateTaskDetails` écrivaient à l'indice de ligne reçu sans contrôle.
  → Le numéro de ligne est validé et la ligne d'en-tête est refusée.

- **[v3] Une barre étroite ne pouvait pas être déplacée.** Sous environ 16 px, les
  deux poignées de redimensionnement occupaient toute la largeur : impossible de
  l'attraper pour la déplacer, donc impossible de changer sa track. Les poignées se
  réduisent maintenant avec la barre et disparaissent en dessous de 16 px, la barre
  entière devenant alors une zone de déplacement.
- **[v3] Le double-clic sur une barre ouvrait l'éditeur en mode création.** Le
  `pointer-events: none` posé dès l'appui — nécessaire pour identifier la ligne
  survolée pendant un déplacement — faisait atterrir le second clic sur la ligne au
  lieu de la barre. Un appui ne devient un déplacement qu'au-delà de 4 px, ce qui
  rétablit le double-clic et évite aussi qu'un clic un peu tremblant décale un
  livrable d'une journée.

- **[v3] Un livrable déplacé revenait à sa track d'origine — trois causes
  distinctes, toutes corrigées.**
  1. *Une lecture périmée écrasait la modification.* Avec le rafraîchissement
     automatique, un sondage parti **avant** le déplacement livrait sa réponse
     **après** : elle décrivait la feuille d'avant l'édition, et l'appliquer
     ramenait le livrable à son ancienne track — alors que la feuille, elle,
     contenait bien la nouvelle. Chaque écriture incrémente désormais un compteur ;
     un sondage note sa valeur au départ et jette sa réponse si elle a changé
     entre-temps, puis relance aussitôt une lecture à jour.
  2. *Une écriture refusée laissait l'écran mentir.* Si la feuille refusait
     l'enregistrement — cas courant en « execute as user accessing » avec un
     utilisateur en lecture seule — le graphique continuait d'afficher le
     déplacement, que le rechargement suivant annulait sans explication. Un refus
     annule maintenant la modification à l'écran, retire l'entrée d'annulation
     correspondante et affiche la raison renvoyée par Google.
  3. *Une track explicite pouvait être purement ignorée.* `ref`, `reference` et
     `id` figuraient parmi les synonymes de la colonne *track* : un en-tête
     « Ref » ou « ID » en colonne A détournait la colonne track vers A. Un
     `TRK-1` écrit en colonne C n'était alors jamais lu, et un déplacement
     écrivait la nouvelle track **par-dessus la référence**. Les deux colonnes ont
     désormais des synonymes disjoints, et la résolution ne dépend plus de l'ordre
     des en-têtes.

  La règle est maintenant explicite et vérifiée : **une track écrite dans la
  feuille prime toujours** ; seul un livrable qui n'en a pas s'en voit dériver une,
  depuis sa référence puis, à défaut, depuis sa position de ligne.

- **[v2] Les filtres d'unités se réarmaient tout seuls.** Décocher toutes les
  unités puis rafraîchir les recochait toutes : la sélection vide était
  indistinguable d'une absence de préférence enregistrée. Bug sans conséquence
  tant que le rafraîchissement était manuel, mais il serait devenu visible
  toutes les 5 secondes avec le rafraîchissement automatique.
  → Une sélection vide est désormais respectée ; seule une liste enregistrée ne
  correspondant à aucune unité de la feuille (changement de feuille) retombe sur
  « tout sélectionner ».

### 1.4 Cosmétique

- **Classes Tailwind invalides.** `shadow-xs` (7×) et `rounded-xs` (4×) sont des
  noms Tailwind v4 alors que la page charge le CDN v3 : elles n'avaient aucun effet.
  → Remplacées par `shadow-sm` / `rounded-sm`.

---

### 1.5 Correction de convention

- **[v2] 1 FTE vaut 1580 h/an, et non 1560.** Valeur corrigée dans le calcul de
  la courbe FTE mensuelle, les totaux par stage, les infobulles, le panneau de
  synthèse, la légende, l'export CSV, ainsi que dans le classeur de référence et
  sa documentation. Le mois de référence passe de 130 h à 131,7 h.

---

## 2. Backend (`Code/code.gs`)

- **Colonnes résolues par libellé d'en-tête**, avec les positions actuelles en
  repli (`COLUMN_ALIASES`). Auparavant seules `currency` et `unit` étaient
  détectées ; déplacer une autre colonne faisait lire silencieusement la mauvaise
  cellule. Les libellés français sont reconnus (Titre, Étape, Montant, Début, Fin,
  Devise, Département…).
- **Montants tolérants** : `1 234,50`, `1,234.50`, `€ 1234` sont interprétés
  correctement (`toNumber_`), au lieu d'un `parseFloat` qui renvoyait 0.
- **Dates inversées permutées** au lieu d'être ignorées : une fin antérieure au
  début est une faute de saisie, pas une raison de supprimer la ligne.
- **Lignes ignorées comptées et remontées** (`skippedRows`), affichées au
  chargement — auparavant elles disparaissaient sans trace.
- **Identifiants de tâche stables** : `'task_' + rowNum` au lieu de
  `'task_' + rowNum + '_' + Math.random()`, qui changeait à chaque rechargement et
  rendait impossible tout suivi par identité (c'est ce qui permet l'annulation).
- **Unités triées**, `Unassigned` en dernier.
- **Messages d'erreur explicites** indiquant quoi corriger dans la feuille.

## 3. Interface (`Code/index.html`)

Nouveautés (toutes absentes de la version d'origine) :

- **Annulation / rétablissement** (`Ctrl+Z` / `Ctrl+Maj+Z`) sur toutes les
  modifications de dates, y compris le décalage global.
- **Éditeur de livrable** au double-clic, branché sur `updateTaskDetails` — une
  fonction backend qui existait mais **n'était jamais appelée** depuis l'interface.
  Validation des saisies (titre et track obligatoires, fin ≥ début).
- **Glissement aimanté au jour**, avec les dates affichées en direct pendant le
  déplacement.
- **Recherche** dans les titres, tracks, stages, unités et commentaires.
- **Stages repliables** en cliquant sur leur bandeau.
- **Repère « aujourd'hui »** et raccourci pour s'y rendre.
- **Zoom** : préréglages année/trimestre/mois, ajustement à la fenêtre,
  `Ctrl`+molette, et conservation de la date centrale pendant le zoom.
- **Export CSV** de la matrice de synthèse.
- **Libellés de track** au survol d'une ligne (l'origine n'affichait aucun nom de
  ligne — un `#sidebar` était déclaré en CSS mais masqué et sans contenu).
- **Écran vide explicite** quand aucun livrable ne correspond aux filtres.
- **Préférences persistées** : zoom, filtres d'unités, mode lecture seule,
  affichage des 0-Mh.
- **Rendu groupé par frame** (`requestAnimationFrame`) au lieu d'un rendu
  synchrone à chaque événement.
- **Détection de collisions** en balayage trié plutôt qu'en double boucle
  re-filtrant la liste complète pour chaque track.
- **Repli GViz** en lecture seule si le backend est injoignable, avec message clair
  et écriture désactivée.

Ajouts de la seconde série :

- **[v2] Les libellés trop longs débordent au lieu d'être coupés.** La largeur
  d'une barre code sa durée : elle ne peut donc pas s'élargir pour accueillir son
  texte. Le libellé est mesuré avant l'affichage ; s'il tient dans la barre il y
  reste, sinon il est posé à côté, dans une pastille lisible sur le fond. Le côté
  est choisi en fonction de la place réellement libre : à droite par défaut, à
  gauche quand la droite est occupée par la barre suivante de la même track ou
  qu'elle sortirait du canevas. Un libellé ne recouvre jamais la barre qu'il
  décrit. Sur une track dense où aucun côté ne suffit, survoler la barre fait
  passer son libellé au premier plan.
- **[v2] Rafraîchissement automatique** réglable (2, 5, 10, 30 ou 60 secondes),
  désactivé par défaut. Chaîne de `setTimeout` plutôt qu'un `setInterval` : la
  requête suivante n'est armée qu'au retour de la précédente, donc les appels ne
  s'empilent jamais. Un sondage est reporté pendant un glissement, pendant qu'une
  boîte de dialogue est ouverte, pendant l'écriture d'une modification et quand
  l'onglet est en arrière-plan. Surtout, la feuille reçue est comparée à celle
  affichée avant tout redessin : si rien n'a bougé, rien n'est redessiné — c'est
  ce qui rend une cadence de 5 secondes utilisable sans scintillement. L'historique
  d'annulation survit aux sondages.
- **[v2] Horodatage du dernier rafraîchissement** dans la barre d'état.
- **[v2] Export CSV du plan** : les livrables actuellement affichés, avec durée,
  effort, densité et équivalent FTE.

### Édition complète depuis le Gantt **[v3]**

- **Changement de track au glisser-déposer.** Une barre se déplace désormais aussi
  verticalement : la ligne survolée est mise en évidence, l'indicateur annonce la
  track cible, et la durée est conservée. Le stage de la track d'arrivée s'applique,
  puisqu'une track vit sous un seul stage — le dire explicitement vaut mieux que de
  laisser un stage qui ne correspond plus.
- **Création** par le bouton « ＋ New », par la touche `N`, ou par un double-clic sur
  un emplacement libre d'une track : le livrable est pré-rempli sur cette track et
  au jour cliqué. La ligne est ajoutée en bas de l'onglet `plan`, et c'est la feuille
  qui décide du numéro de ligne, lequel devient l'identité du livrable.
- **Suppression douce.** « Remove from chart » ne vide que les deux cellules de date
  (elles passent à `N/A`). La ligne, son titre et son montant restent dans la
  feuille, rien n'est perdu, et aucun numéro de ligne ne se décale sous les sessions
  ouvertes des autres. Annulable, et réversible en remettant des dates.
- **Montant, devise et unité éditables** dans l'éditeur, en plus du titre, de la
  track, du stage, des dates et du commentaire. Un sélecteur propose les tracks
  existantes pour déplacer sans risque de faute de frappe.
- Côté backend : `updateTaskFields` (écriture d'un jeu de champs quelconque en une
  seule plage), `addTask`, `deleteTask` et `updateTaskDatesBatch`. `updateTaskDetails`
  est conservée et devient une façade sur `updateTaskFields`.

### Capacité et surcharge **[v3]**

- Nouvel onglet optionnel **`capacity`** : l'effectif réel de chaque unité, exprimé
  en périodes plutôt qu'en grille mensuelle — une montée en charge tient en une ligne
  au lieu de douze. Les lignes d'une même unité s'additionnent.
- Nouvelle vue **Capacity** : matrice unité × mois, chaque cellule affichant la
  demande sur la capacité, colorée selon le taux de charge, avec le déficit chiffré
  en FTE et en Mh.
- Le bandeau mensuel signale en rouge les mois non tenables, et l'infobulle nomme les
  unités en déficit.
- **Le déficit se calcule par unité et ne se compense jamais entre unités.** Une
  personne disponible aux Achats ne remplace pas un ingénieur manquant au Logiciel :
  les déficits se somment au lieu de s'annuler. Un mois est en surcharge dès qu'une
  unité est courte, même si le programme s'équilibre une fois toutes les unités
  additionnées. Pour la même raison, la courbe mensuelle n'affiche que la demande :
  une ligne de plafond globale sous-entendrait une interchangeabilité inexistante.
- Seuls les livrables en Mh créent de la demande ; une ligne en EUR achète un
  résultat, elle n'occupe personne.

### Référence et dérive **[v3]**

- Nouvel onglet **`baseline`**, écrit par l'outil : « Capture baseline » fige les
  dates et les montants du jour.
- Chaque barre ayant bougé affiche ensuite un **fantôme creux** à sa position de
  référence, rouge si elle a glissé, vert si elle a avancé.
- Nouvelle vue **Drift** : nombre de livrables déplacés, restés au plan, plus grand
  glissement, delta d'effort, puis le détail ligne par ligne avec l'écart en jours
  sur le début, la fin, la durée et le montant. Signale aussi les livrables ajoutés
  depuis la référence et ceux qui ont quitté le graphique.

### Résolution des collisions **[v3]**

- Le badge de collisions ouvre un **aperçu** : cascade vers l'avant uniquement, qui
  décale ce qui chevauche en conservant chaque durée. Rien ne recule, donc la
  proposition ne peut pas inventer de la capacité qui n'existait pas.
- L'aperçu liste chaque déplacement avec son ampleur et le report final de chaque
  track, avant toute écriture.
- L'application se fait en **une seule écriture groupée** et s'annule en un seul
  `Ctrl+Z`.

## 4. Template (nouveau dossier `Template/`)

- `timeliner-planner-template.xlsx` : classeur de référence avec les cinq onglets
  lus par l'outil, un programme d'exemple 2026-2027 (26 lignes, 5 stages,
  19 tracks, 7 unités, 12 gates), en-têtes figés, listes déroulantes et mise en
  forme conditionnelle. Un onglet `README` reprend le schéma et un bloc de contrôle
  recalculé par formules.
- `Template/README.md` : documentation du schéma, lisible sur GitHub (le `.xlsx`
  étant binaire).
- `Template/build_template.py` : régénère le classeur, pour que les évolutions du
  format restent relisibles en diff.
- `README.md` racine : structure du dépôt et procédure d'installation.

---

## 5. Ce qui n'a pas changé

Conformément à la demande initiale, toutes les fonctions et la logique de
fonctionnement d'origine sont conservées :

- Les 9 fonctions backend publiques : `doGet`, `getSpreadsheet`, `getPlannerData`,
  `shiftAllDates`, `updateGateDate`, `updateTaskDetails`, `updateTaskDates`,
  `parseDateVal`, `formatDateISO`.
- Les noms d'onglets et la disposition des colonnes.
- Le regroupement par stage, une track par ligne de graphique, le stage d'une track
  défini par son premier livrable.
- La règle de collision, la coloration par densité de Mh/jour, les trois types de
  gates et leurs couleurs.
- La répartition uniforme de l'effort sur les jours et la courbe FTE mensuelle
  (seule la valeur du FTE a changé, voir 1.5).
- Les trois modes de la synthèse (par unité, par stage, détaillé) et le tableau des
  postes monétaires.
- La molette temporelle par glissement sur l'en-tête, le mode lecture seule, le
  mode démo.

---

## 6. Vérification

Ce qui a été testé :

- **[v2] Rafraîchissement automatique** : cadence tenue, **zéro redessin quand la
  feuille n'a pas changé**, prise en compte d'un changement réel, report effectif
  du sondage pendant un glissement (souris maintenue enfoncée sur une barre),
  pendant l'ouverture d'une boîte de dialogue et en onglet caché, reprise après
  levée des garde-fous, survie de l'historique d'annulation, et arrêt complet une
  fois désactivé.
- **[v2] Débordement des libellés** : mesures à quatre niveaux de zoom, en lecture
  seule et en mode éditable, vérification qu'aucun libellé interne n'est tronqué,
  qu'aucun libellé ne recouvre la barre qu'il décrit, et que le repli à gauche ne
  s'active que lorsqu'il tient réellement.
- **[v2] Exports CSV** : téléchargements réellement capturés dans le navigateur,
  en-têtes et totaux contrôlés, respect des filtres actifs, et vérification que la
  colonne FTE utilise bien 1580.
- **[v3] 22 tests backend supplémentaires** : écriture de champs multiples en une
  plage, champs omis laissés intacts, montants au format européen, ajout et refus
  d'un ajout sans dates, suppression douce réversible, écriture groupée, lecture de
  la capacité (lignes invalides écartées, intervalles cumulés), capture et relecture
  de la référence, et non-contamination de la référence par les modifications
  ultérieures.
- **[v3] Test bout en bout** : la vraie interface branchée sur le vrai `code.gs`
  au-dessus d'un simulacre de feuille, pour quatre formes de feuille (track
  renseignée, track vide avec référence, track explicite sans en-tête reconnu,
  aucune des deux) — déplacement puis rechargement, la track tient dans les quatre.
  Deux tests dédiés reproduisent la lecture périmée et l'écriture refusée.
  Au passage, ce travail a révélé que mes simulacres précédents partageaient un
  unique gestionnaire de succès là où `google.script.run` en renvoie un neuf à
  chaque appel ; corrigé, c'est ce qui a rendu la course reproductible.
- **[v3] Tests navigateur** : édition du montant/devise/unité, création, validation
  des saisies, suppression douce et son annulation, glissement vertical avec mise en
  évidence de la ligne cible et héritage du stage, non-régression du glissement
  purement horizontal, fantômes de référence tracés uniquement pour ce qui a bougé,
  table de dérive, aperçu puis application de la cascade de collisions en une
  écriture groupée annulable, et arithmétique de capacité vérifiée au FTE près.
- **36 tests unitaires backend** contre un simulacre de l'API Apps Script :
  analyse des dates sous tous les formats, résolution des colonnes, feuille
  étroite, permutation des dates inversées, aller-retour lecture/écriture,
  décalage global réversible, refus d'écriture sur la ligne d'en-tête.
- **Tests navigateur** (Chromium) : glissement, redimensionnement, annulation et
  rétablissement, éditeur et sa validation, échappement HTML, glissement de gate,
  repli de stage, filtres, recherche, zoom, repli GViz de bout en bout.
- **Quatre fuseaux horaires** pour le bug de décalage.
- **Template** : passé dans le vrai `getPlannerData()` (20 contrôles) puis rendu
  dans l'application. Backend, formules du classeur et panneau de synthèse
  concordent : 25 livrables tracés, 1 ignoré, 9 640 Mh (6,18 FTE-an), 225 000 €,
  du 2026-01-05 au 2027-12-31.
- **Formules du classeur** évaluées avec un moteur Python : les 9 sont correctes.

Ce qui n'a **pas** pu être vérifié dans l'environnement de développement :

- **Le code n'a jamais tourné dans un vrai projet Google Apps Script.** Les tests
  backend s'appuient sur un simulacre de `SpreadsheetApp` : le comportement réel de
  l'API Google n'est pas couvert. Un test sur une vraie feuille reste nécessaire.
- **Le rendu visuel des barres d'outils Tailwind** : le CDN était bloqué par le
  proxy. Seul le canevas du Gantt (piloté par la feuille de style du fichier) a été
  vérifié à l'écran. Le vocabulaire de classes d'origine a été conservé, aux deux
  noms invalides près.
- **Les valeurs en cache des formules du classeur** : LibreOffice est inutilisable
  dans cet environnement. Google Sheets et Excel recalculent à l'ouverture, les
  valeurs s'affichent donc normalement, mais un outil lisant uniquement le cache
  verra des cellules vides.
