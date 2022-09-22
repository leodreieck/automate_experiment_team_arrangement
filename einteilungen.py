from gurobipy import * 
import pandas as pd
import numpy as np
import time

# INPUT DATA
nSeminars_input = 2
nTeamer_input = 14

persons_per_seminar = {"Frischling": 1,#3,
                        "Mittelbau": 2,#3,
                        "Co-Leitung": 1,
                        "Leitung": 1}
persons_per_seminar_total = 5



'''pref = np.load("input/pref.npy", allow_pickle=True) # pref[s,t]
gender = np.load("input/gender.npy", allow_pickle=True) # gender[t]
pol = np.load("input/pol.npy", allow_pickle=True) # pol[t]
exp = np.load("input/exp.npy", allow_pickle=True) # exp[t]
'''

rueckmeldungen = pd.read_excel('input/einteilung_survey_results.xlsx')
pref = np.array(rueckmeldungen[["s1","s2"]]).transpose() # pref[s,t]
gender = np.array(rueckmeldungen["Geschlecht"]) # gender[t]
pol = np.array(rueckmeldungen["leitung?"]) # pol[t]
exp = np.array(rueckmeldungen["Erfahrung"]) # exp[t]
prio = np.array(rueckmeldungen["Prio"]) # prio[t]: 1, if potential frischling was not chosen last year
# country = np.load("input/country.npy") # how to handle people with multiple countries?
# nicht eingeteilt letztes mal

# x[s,t] = pos # per seminar
# w[t,pol,g,c] # per teamer

#Model
mod = Model("Model")


#SETS
nSeminars = range(nSeminars_input) # Seminare
nTeamers = range(nTeamer_input) # Teamer
roles = ["Leitung", "Co-Leitung", "Mittelbau", "Frischling"]
pref_options_seminar = [0,1,2] # [nein, bei engpaessen, ja]
pref_options_leitung = [0,1,2,3,4] #[nein, bei engp. co-l., co-l., bei engp. l., l.]
gender_dict = {"w":0, "m":1, "d":0.5}
countries = ["Frankreich", "USA", "Irland"]
cluster = {"Nordamerika": ["USA", "Kanada"],
            "Übersee": ["Ecuador", "Suedafrika", "Argentinien", "Australien", "Neuseeland"],
            "Europa": ["Irland", "Frankreich", "Spanien", "Italien", "England"]}


#DECLARATION OF DECISION VARIABLES
y = {}
z = {}

#OTHER PARAMETERS
#bigM = 999

# Create decision variables 
for s in nSeminars:
    for t in nTeamers:
        for r in roles:
            y[s, t, r] = mod.addVar(vtype = 'B', name = 'y[%s,%s,%s]'%(s, t, r))
#print(y)
            
for s in nSeminars:
    for r in roles:
        z[s, r] = mod.addVar(vtype = 'I', name = 'z[%s,%s]'%(s, t))
#        et[i,j] = mod.addVar(lb = 0, vtype = 'I', name = 'st[%s,%s]'%(i,j))

        
#CONSTRAINTS
# 1 #
# each role must be filled
for s in nSeminars:
    for r in roles:
        mod.addConstr(quicksum(y[s,t,r] for t in nTeamers) + z[s,r] == persons_per_seminar[r])


# 2 # 
# at least one m/w per seminar
#for s in nSeminars:
#    mod.addConstr(quicksum(y[s,t,r] * gender_dict[gender[t]] for t in nTeamers for r in roles) >= 2)
#    mod.addConstr(quicksum(y[s,t,r] * gender_dict[gender[t]] for t in nTeamers for r in roles) <= persons_per_seminar_total-2)
#

# 3 #
# frischling -> experience=0
# leitung + co-leitung need pol
for s in nSeminars:
    for t in nTeamers:
        mod.addConstr(y[s,t,"Frischling"] * exp[t] == 0) # y can only be 1, if exp=0
        mod.addConstr(y[s,t,"Mittelbau"] <= exp[t] * 50) # y can only be 1, if exp=0
        mod.addConstr(y[s,t,"Co-Leitung"] <= pol[t]) # if pol=0, y cannot be 1
        mod.addConstr(y[s,t,"Leitung"] * 3 <= pol[t]) # if pol<3, y cannot be 1

# 4 #
# each teamer can only team once per season
# TODO: or per weekend?
for t in nTeamers:
    mod.addConstr(quicksum(y[s,t,r] for s in nSeminars for r in roles) <= 1)

# 5 #
# teamer preferences
#print(pref)
for s in nSeminars:
    for t in nTeamers:
        mod.addConstr(quicksum(y[s,t,r] for r in roles) <= pref[s,t])
    


#OBJECTIVE FUNCTION
# prio 1
# punish bad country enforcement - ist das überhaupt vorher bekannt? oder sollte man nicht lieber clustern?
# punish "bei engpässen" *check*
# punish empty slots *check*

# prio 2
# punish bad gender distribution

# prio 3
# punish very homogeneously experienced teams (all very young, all very old)
# much much later: punish distances to seminar

mod.setObjective(quicksum(y[s,t,r] * pref[s,t] for t in nTeamers for s in nSeminars for r in roles)             # punish bei engpässen (pref)
                    + quicksum(y[s,t,r] * pol[t] for t in nTeamers for s in nSeminars for r in roles[:2])       # punish bei engpässen (pol) (only if they were chosen as leitung or co-leitung)
                    + quicksum(y[s,t,r] * prio[t] for t in nTeamers for s in nSeminars for r in roles) * 2      # encourage choosing people who were not chosen last year
                    - quicksum(z[s,r] for s in nSeminars for r in roles) * 10
                    , GRB.MAXIMIZE)

mod.optimize()


#PRINTING SOLUTION
with open('output/einteilung_solution_'+ time.strftime('%Y%m%d_%H%M%S') + ".txt",'w') as f:
    f.write('# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #\n')
    f.write('# solution created on:,\t'+time.strftime('%d.%m.%Y %H:%M:%S')+'\n')
    #f.write('# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #\n')
    f.write('# solving time:,\t'+'%.4f'%mod.Runtime+' s\n')
    f.write('# objective:,\t'+'%.2f'%mod.ObjVal+'\n')
    f.write('# GAP:,\t'+'%.4f'%mod.MIPGap+'\n')
    f.write('# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #\n')
    for seminar in nSeminars:
        f.write('\nSeminar: {}\n'.format(seminar))
        for role in roles:
            for teamer in nTeamers:
                if y[seminar,teamer,role].x:
                    f.write('{},{},{},{},{},{}\n'.format(rueckmeldungen["Vorname"].iloc[teamer], rueckmeldungen["Nachname"].iloc[teamer], rueckmeldungen["Geschlecht"].iloc[teamer], rueckmeldungen["Ausreisejahr"].iloc[teamer], rueckmeldungen["Gastland"].iloc[teamer], role))
            if z[seminar, role].x:
                f.write('NA,NA,NA,NA,NA,{}\n'.format(role))

    f.write('\nNicht eingeteilt: \n')
    for teamer in nTeamers:
        sum = 0
        for seminar in nSeminars:
            for role in roles:
                if y[seminar,teamer,role].x:
                    sum += 1
        if sum==0:
            f.write('{},{},{},{},{}\n'.format(rueckmeldungen["Vorname"].iloc[teamer], rueckmeldungen["Nachname"].iloc[teamer], rueckmeldungen["Geschlecht"].iloc[teamer], rueckmeldungen["Ausreisejahr"].iloc[teamer], rueckmeldungen["Gastland"].iloc[teamer]))