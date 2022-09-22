# automate_experiment_team_arrangement
Automate the Experiment e.V. "Seminareinteilung" using linear optimization

## Prerequisites
- gurobi (https://www.gurobi.com/, I use the free academic licence)
- python environment cf. requirements.txt
- some form of survey results as .xlsx

## Goal
So far, creating the "Seminareinteilung" is a complex and tedious job. Using a linear program to generate a preliminary proposal to be optimized by hand might speed up the process and lead to an even fairer (and potentially more sustainable) "Einteilung".

### MVP
- automate the "Einteilung" following the given preferences
- allow for empty slots
- encourage country clustering ("USA/Kanada", "Europa", "Übersee")
- punish bad gender distribution

### Improvement Ideas
- incorporate experience and soft knowledge (e.g. talkativeness etc...)
- incorporate distance to seminars, minimizing costs for Experiment 
