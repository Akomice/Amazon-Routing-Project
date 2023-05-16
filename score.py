#Une fonction qui prend en argument un dictionnaire de valeurs ordonnées et qui renvoie les couples de valeurs consécutives

import json
from routes import Route,travtimes,routedata,package

def consec_dict(d):
    keys = list(d.keys())
    n = max( [d[key] for key in keys])
    c = []
    for i in range(n-1):
        i1=0
        i2=0
        for i1 in range(n):
            if (d[keys[i1]] == i):
                for i2 in range(n):
                    if (d[keys[i2]] == i+1):
                        c.append((keys[i1],keys[i2]))
    return c

def eval_score(sol_route,amazon_route,traveltimes):
    temps_sol = 0
    temps_amazon = 0
    aretes_sol = consec_dict(sol_route)
    aretes_amazon = consec_dict(amazon_route)
    for i in range(min(len(aretes_sol),len(aretes_amazon))):
        sol_i,sol_j = aretes_sol[i] 
        temps_sol += traveltimes[sol_i][sol_j]
        amazon_i,amazon_j = aretes_amazon[i]
        temps_amazon += traveltimes[amazon_i][amazon_j]
    return (temps_sol,temps_amazon)

# with open('drive/model_build_inputs/model_build_inputs/package_data.json','r') as f:
#     package_data = json.load(f)

# with open('drive/model_build_inputs/model_build_inputs/travel_times.json','r') as f:
#     travel_times = json.load(f)
    
# with open('drive/model_build_inputs/model_build_inputs/route_data.json','r') as f:
#     route_data = json.load(f)

with open('drive/model_build_inputs/model_build_inputs/actual_sequences.json','r') as f:
    results = json.load(f)
    
routeids = list(routedata.keys())
routeid = routeids[1]

optimize_route_0 = Route(travtimes[routeid],routedata[routeid],package[routeid])
result = optimize_route_0.main()
#print(result)
print(eval_score(result,results[routeid]['actual'],travtimes[routeid]))