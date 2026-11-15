# GUIDE P4 : comprendre et livrer ton travail (Decision Engine)

## 0. Où placer chaque fichier

| Fichier du paquet | À copier vers |
|---|---|
| `backend/lunanav/decision/__init__.py`, `verdict.py`, `explain.py`, `ranking.py` | même chemin dans le dépôt `Luna-Nav/` |
| `backend/tests/decision/` (4 tests + conftest) | même chemin |
| `docs/explainers/*.md` (5 fichiers) | `docs/explainers/` |
| `docs/methodology_P4_section.md` | **coller à la fin** de `docs/methodology.md` (ne rien supprimer) |
| `docs/decisions_P4_lines.md` | coller les lignes dans `docs/decisions.md` |
| `mock_data/astro/*.json` | **ne pas copier** : ils existent déjà dans le dépôt (copie ici seulement pour tester) |

Test : `py -m pytest backend/tests/decision -v` (58 cas, tous réussis chez moi ; le fichier `conftest.py` ajoute `backend/` au chemin Python et lit les JSON de P3).

## 1. Les critères (colonnes du tableau de décision)

| Critère | Unité | Sens | Pourquoi |
|---|---|---|---|
| sunlight_pct | % | plus = mieux | énergie solaire |
| longest_darkness_h | h | moins = mieux | dimensionner batterie et chauffage |
| earth_visibility_pct | % | plus = mieux | communication directe |
| longest_comms_gap_h | h | moins = mieux | plus longue coupure radio |
| power_and_comms_pct | % | plus = mieux | soleil ET Terre en même temps |
| vertical_panel_energy_kwh_m2 | kWh/m2 | plus = mieux | énergie récoltée |

Le verdict n'utilise que les 4 premiers. Le classement utilise les 6. (Le « temps avant le coucher du soleil » n'est pas dans `metrics`, il est dans `sun_countdown` : l'utiliser demanderait un changement de contrat, donc je l'ai laissé de côté.)

## 2. Le verdict en une image

On pose les questions dans cet ordre : **d'abord « est-ce éliminatoire ? »**, puis « est-ce tout bon ? », sinon c'est « marginal ».

Exemple réel, Connecting Ridge : soleil 100 % (bon), nuit 0 h (bon), Terre 48 % (< 50 : raté), coupure 347 h (> 72 : raté). Rien d'éliminatoire, mais pas tout bon → **marginal**.
Malapert : nuit de 269 h > 100 h → **not_viable** immédiatement.

## 3. La normalisation : pourquoi et comment

Problème : on ne peut pas additionner des % et des heures (100 % + 269 h n'a pas de sens). On ramène chaque critère entre **0 (le pire) et 1 (le meilleur)**.

- Critère « plus = mieux » : `(x - min) / (max - min)`
- Critère « moins = mieux » : `(max - x) / (max - min)` (on inverse)

Exemple sur les 4 sites, sunlight : min = 40,09 (IM-1), max = 100 (Connecting Ridge). Malapert : (53,27 - 40,09) / (100 - 40,09) = **0,22**.
Nuit la plus longue : max = 274,1 (Apollo 11), min = 0. Malapert : (274,1 - 269,3) / 274,1 = **0,017** (presque le pire).

Si tous les scénarios ont la même valeur, le critère ne départage personne : on met 1.

## 4. WSM (somme pondérée)

Score = somme de (poids × valeur normalisée). Exemple, Malapert avec le profil *engineering* :
0,15×0,22 + 0,25×0,017 + 0,10×1 + 0,25×1 + 0,15×1 + 0,10×0,31 = **0,568**.
Simple et lisible, mais un très mauvais critère peut être compensé par de bons autres.

## 5. TOPSIS

Idée : le meilleur scénario est **le plus proche d'un scénario idéal imaginaire** (le meilleur de chaque critère) et **le plus loin d'un scénario catastrophe** (le pire de chaque critère).
Étapes : normaliser (division par la norme de la colonne), multiplier par les poids, trouver l'idéal et l'anti-idéal, calculer les distances `d+` et `d-`, puis `C = d- / (d+ + d-)` (entre 0 et 1, plus grand = mieux).

## 6. Profils Science / Engineering

Hypothèses d'équipe (à valider) : *science* veut du temps productif (soleil, énergie, soleil+Terre) ; *engineering* veut limiter les pires cas (nuit la plus longue, coupure la plus longue). Les poids sont dans `WEIGHT_PROFILES` et modifiables.

## 7. Analyse de sensibilité : ce que ça a révélé sur les vraies données

On modifie les poids de ±25 %, on tire 200 jeux de poids au hasard, et on compare les deux profils.
Résultat sur `compare_four_sites.json` : **sensible**. Science classe Connecting Ridge 1er, Engineering classe Malapert 1er (devant IM-1 pour 0,0001 point) et Connecting Ridge dernier.

Deux points à présenter à l'équipe :
1. **Un classement n'est pas un verdict.** Avec le profil engineering, le seul site « marginal » finit dernier, et Malapert, « not_viable », finit 1er. Le texte généré le dit explicitement. Option si l'équipe préfère : toujours afficher le verdict en premier et n'utiliser le classement que pour départager des scénarios de même niveau (à décider ensemble).
2. **Rappel :** ce périmètre (WSM/TOPSIS) est écarté par le README ; il est optionnel et séparé du verdict.

## 8. Intégration P5 (P4 ne crée aucune route)

```python
from lunanav.decision import verdict
for row in rows:                       # lignes de compare_scenarios / date_sweep
    row["verdict"] = verdict(row["metrics"])   # {level, reasons, summary, thresholds}
```
Les erreurs sont de type `DecisionInputError` (sous-classe de `ValueError`, avec un attribut `code`) : P5 peut les transformer en HTTP 422. Optionnel : `rank_scenarios(rows)`, `sensitivity_analysis(rows)`, `explain_comparison(rows)`, `explain_ranking(...)`.

## 9. Avant de présenter à l'équipe

- [ ] Confirmer que WSM/TOPSIS/profils sont attendus (README dit non).
- [ ] Valider les seuils : sur les données actuelles **aucun scénario n'est « viable »** (coupure radio > 72 h toute l'année).
- [ ] Valider les poids Science/Engineering.
- [ ] Branche `p4/decision`, puis `git add backend/lunanav/decision backend/tests/decision docs/explainers`.
