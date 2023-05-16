import json
from math import *
import pandas as pd
from sklearn.cluster import KMeans
import re
import cplex
import pulp

with open('travel_times_solo.json') as f:
    travtimes = json.load(f)

with open('route_data_solo.json') as f:
    routedata = json.load(f)

with open('package_data_solo.json') as f:
    package = json.load(f)

def length_lofl(ll):
    return sum(list(map(len,ll)))

def swap_values(t,i,j):
    tmp = t[i]
    t[i] = t[j]
    t[j] = tmp
    return t

def get_index(t,e):
    for i in range(len(t)):
        if t[i] == e: 
            return i
    return -1

def hours_to_sec(s):
    h,m,sec=s.split(':')
    return int(h)*3600 + int(m)*60 + int(sec)

def ab_to_values(t_ab):
    ab=[]
    for val_ab in t_ab:
        a = hours_to_sec(val_ab[0].split(' ')[1])
        b = hours_to_sec(val_ab[1].split(' ')[1])
        ab.append((a,b))
    return ab

def max_of_max(p):
    val = []
    for l in p:
        val.append(max(l))
    return max(val)

def add_value(d,e):
    keys = list(d.keys())
    key_max = keys[0]
    val_max = d[key_max]
    for key in keys:
        if d[key] > val_max:
            val_max = d[key]
            key_max = key
    d[e] = val_max
    d[key_max]+=1
    return d

class Route():

    def __init__(self,travel_times,route_data,package_data):
        self.travel_times = travel_times
        self.route_data = route_data
        self.package_data = package_data

    def distances_sommets(self,centers):
        centers_0=centers[:,0]
        centers_1=centers[:,1]
        
        #print(centers_0[1])
        
        #on calcule la distance de chaque sommet envers tous les autres -> on pourra trouver le v0 excentré
        
        number_cluster = len(centers_0)
        
        dist=[]
        
        for i in range(number_cluster):
            dist_i=[]
            for j in range(number_cluster):
                x_j=centers_0[j]
                x_i=centers_0[i]
                y_j=centers_1[j]
                y_i=centers_1[i]
                dist_i.append(sqrt((x_j - x_i)**2 + (y_j - y_i)**2))
            dist.append(dist_i)
            
        return dist

    def find_v0(self,centers):
        dist=self.distances_sommets(centers)
        
        maxi = 0
        v0=0

        sums=[0 for i in range(len(centers[:,0]))]
        
        for i in range(len(centers[:,0])):
            #on vérifie que l'on ne prend pas le sommet le plus éloigné en comparaison
            for j in range(len(centers[:,0])):
                sums[j]=sums[j]+dist[j][i]
            
        sommet_comparant=sums.index(min(sums))
            
        for i in range(len(centers[:,0])):      
            if centers[sommet_comparant][i]>maxi:
                maxi=centers[sommet_comparant][i]
                v0=i
            
        return v0

    #on crée l'ordre de parcours des clusters
    def ordre_parcours_cluster(self,centers):
        dist=self.distances_sommets(centers)
        v0=self.find_v0(centers)
        
        #liste des clusters pour ne pas mettre le même 2 fois)
        list_centers = [i for i in range(len(centers[:,0]))]
        list_centers.remove(v0)
            
        #liste de l'ordre parcouru
        list_parcours = [v0]
        
        for i in range(len(centers[:,0])):
            dist[i][v0]=100000.0
            
        for i in range(len(centers[:,0])-1):
            #print(list_parcours[-1])
            dist_last_sommet = dist[list_parcours[-1]]
            #print(dist_last_sommet)
            next_sommet=dist_last_sommet.index(min(dist_last_sommet))
            #print(next_sommet)
            
            #condition qui ne nous fera pas passer plusieurs fois par le même sommet
            for j in range(len(centers[:,0])):
                dist[j][next_sommet]=100000.0
                
            list_parcours.append(next_sommet)
            #list_centers.remove(next_sommet)

            
        return list_parcours    

    def make_clusters(self):

        dt2 = pd.DataFrame(self.travel_times)

        df2 = pd.DataFrame(self.route_data['stops']).T

        number_stops = len(dt2)
        number_cluster = number_stops//10

        kmeans = KMeans(n_clusters=number_cluster)
        kmeans.fit(dt2)
        df2["Cluster"]=kmeans.labels_
        df2.head()

        centers=kmeans.cluster_centers_

        order_clusters=self.ordre_parcours_cluster(centers)

        def first_and_last_in_cluster(l, order):
        
            
            list_clusters=[]
            for i in range(number_cluster):
                list_clusters.append(df2[df2['Cluster']==i].index.values)
                
            v0=list_clusters[order[0]][0]
            #2 listes : la liste des premiers éléments de chaque cluster et celle des derniers
            firsts=[]
            lasts=[v0]
            #un seul element dans le cluster contenant v0
            
            #on récupère le premier élément du 2e cluster
            next_cluster=order[1]
                #print(next_cluster)
            mini = 100000.0
            list_next=list_clusters[next_cluster][0]
            first_next_cluster = l[next_cluster][0][0]
                
            #distance dans dt2 : colonne vers ligne
            for j in range(len(l[next_cluster])):
                if dt2[lasts[-1]][l[next_cluster][j]]<mini:
                    mini=dt2[lasts[-1]][l[next_cluster][j]]
                    first_next_cluster= l[next_cluster][j]
                #print(first_next_cluster)
                
                #on ajoute le first du cluster suivant à la liste des first (la liste sera dans l'ordre de parcours des clusters)
            firsts.append(first_next_cluster)
            
            #trouve les 2 plus rapprochés entre 2 clusters
            for i in range(1, number_cluster-1):
                list_index_min=[]
                list_min=[]
                dist_tot=[]
                for j in range(len(list_clusters[order[i]])):
                    dist_j=[]
                    if (list_clusters[order[i]][j]==firsts[-1] or list_clusters[order[i]][j]==first_next_cluster):
                        dist_j=[1000000.0 for i in range(len(list_clusters[order[i+1]]))]
                    else:
                        for k in range(len(list_clusters[order[i+1]])):
                            dist_j.append(dt2[list_clusters[order[i]][j]][list_clusters[order[i+1]][k]])
                    list_min.append(min(dist_j))
                    list_index_min.append(dist_j.index(min(dist_j)))
                    dist_tot.append(dist_j)
                min_global=min(list_min)
                index_min_j=list_min.index(min_global)
                
                index_min_k=list_index_min[index_min_j]
                
                lasts.append(list_clusters[order[i]][index_min_j])
                firsts.append(list_clusters[order[i+1]][index_min_k])
                
            return firsts,lasts
            
        list_clusters=[]
        for i in range(number_cluster):
            list_clusters.append(df2[df2['Cluster']==i].index.values)

        list_clusters = list(map(list,list_clusters))
        
        clusters_ordered = []
        for i in range(len(list_clusters)):
            clusters_ordered.append(list_clusters[order_clusters[i]])

        first_clusters,last_clusters = first_and_last_in_cluster(list_clusters,order_clusters)

        #On met les arrêts dans les clusters dans l'ordre (pour v0 et vf)

        for i in range(len(first_clusters)-1):
            first_cluster_i = first_clusters[i]
            last_cluster_i = last_clusters[i+1]
            index_first_cluster = get_index(clusters_ordered[i+1],first_cluster_i)
            
            if index_first_cluster != 0:
                clusters_ordered[i+1] = swap_values(clusters_ordered[i+1],0,index_first_cluster)
            
            index_end = len(clusters_ordered[i+1])-1
            index_last_cluster = get_index(clusters_ordered[i+1],last_cluster_i)

            if index_last_cluster != index_end:
                clusters_ordered[i+1] = swap_values(clusters_ordered[i+1],index_end,index_last_cluster)

        i = len(first_clusters)-1

        first_cluster_last = first_clusters[i]
        index_first = get_index(clusters_ordered[i+1],first_cluster_last)

        if index_first != 0:
            clusters_ordered[i+1] = swap_values(clusters_ordered[i+1],0,index_first)
        
        return clusters_ordered
    
    def generate_p_for_cluster(self,cluster):

        list_of_stops = cluster

        n = len(list_of_stops)

        P = [[0 for i in range(n)] for i in range(n)]

        for i in range(n):
            stop_i = list_of_stops[i]
            for j in range(n):
                stop_j = list_of_stops[j]
                P[i][j] = self.travel_times[stop_i][stop_j]
            
        return P
    
    def generate_ab(self):

        stops = list(self.package_data)
        #print(len(stops))
        stop_time=[]
        a=[]
        b=[]
        day=[]
        for j in range (len(stops)):
            a_min_stops = 'NaN'
            b_max_stops = 'NaN'
            package = list(self.package_data[stops[j]])
            #print(package)
            for k in range (len(package)):
                time_window=self.package_data[stops[j]][package[k]]['time_window']
                #print(time_window)
                time_interval=list(time_window.values())
                #print(time_interval)
                stop_time.extend(time_interval)
                #print(stop_time)
            dates_valides = [date for date in stop_time if isinstance(date, str)]

            #si on a une date valide au sein d'une route
            if dates_valides:
                date_min = min(dates_valides)
                date_max = max(dates_valides)
                day=date_min[0:10]
                #print(date_min)
                #print(date_max)            
                if (date_min[8:10] != date_max[8:10]): #cad date sur 2 jrs entre le debut du travail et la fin (debut a 23h par exemple et fin à 16h du lendemain)
                    #si dates sur 2 jours : on aura les dates max de la forme '2018-02-26 25:00:00' à la place de '2018-02-27 01:00:00'
                    date_max = date_min[0:10] + date_max[10:]
                    date_max = date_max[:11] + str(int(date_max[11:13])+24) + date_max[13:]
                    #print(date_max)
                    #somme des minutes 
                    sum_min = int(date_min[14:16]) + int(date_max[14:16])
                    #print(sum_min)
                    #on ajoute les minutes : si la somme des minutes est >=1h : on ajoute fait un super calculer avec une retenue lol
                    if (sum_min >59) :
                        date_max = date_max[:11] + str(int(date_max[11:13])+1) + date_max[13] + str(sum_min-60) + date_max[16:]
                    else :
                        date_max = date_max[:14] + str(sum_min) + date_max[16:]
                                        
                a.append(date_min)
                b.append(date_max)
                
                if (a_min_stops == 'NaN') :
                    a_min_stops = date_min
                    b_max_stops = date_max
                    
                elif (int(a_min_stops[11:13]) > int(date_min[11:13]) and int(b_max_stops[11:13]) < int(date_max[11:13])):
                    a_min_stops = date_min
                    b_max_stops = date_max
                    
            #si on a un NaN
            else :
                a.append('NaN')
                b.append('NaN')
                
                
            #on remplace les NaN par ce qu'il faut
            if (j==len(stops)-1):
                str_a = ','.join(a)
                str_b = ','.join(b)
                
                if (a_min_stops != 'NaN'):
                    str_a=re.sub('NaN', a_min_stops, str_a)
                    str_b=re.sub('NaN', b_max_stops, str_b)                
                else :
                    str_a=re.sub('NaN', day + ' 00:00:00', str_a)
                    str_b=re.sub('NaN', day + ' 47:59:59', str_b)
                
                a = str_a.split(sep=',')
                b = str_b.split(sep=',')
                
        return a,b

    def list_of_stops(self):
        return list(self.package_data)
    
    def associate_a_b_to_stops(self):
        d = {}
        list_of_stops = self.list_of_stops()
        a,b = self.generate_ab()
        c = []
        for i in range(len(a)):
            c.append((a[i],b[i]))
        c = ab_to_values(c)
        for i in range(len(list_of_stops)):
            stop_i = list_of_stops[i]
            d[stop_i] = {}
            d[stop_i]['a'] = c[i][0]
            d[stop_i]['b'] = c[i][1]
        return d
    
    def apply_PL_to_cluster(self,cluster):
        if len(cluster)<=2:
            return None
        P = self.generate_p_for_cluster(cluster)
        ab = []
        d = self.associate_a_b_to_stops()
        for stop in cluster:
            a = d[stop]['a']
            b = d[stop]['b']
            ab.append((a,b))
        max_1 = max([d[stop]['a'] for stop in cluster])
        max_2 = max([d[stop]['b'] for stop in cluster])
        M = max_of_max(P) + max_1 + max_2 + 1
        solveme = testcplex.Solveur(nb=len(cluster),p=P,val_ab=ab,m_val=M + 1000)
        solveme.main()
        return solveme

    def get_results_of_PL(self,cluster):
        results = self.apply_PL_to_cluster(cluster)
        n=len(cluster)
        j = 0
        d = {}
        d[cluster[0]] = 0
        d[cluster[n-1]] = n-1
        curr = 1
        while curr < n-1:
            for i in range(1,n):
                if int(pulp.value(results.X[j][i])+0.05) == 1:
                    d[cluster[i]] = curr
                    curr+=1
                    j = i
                    break
            if j == n-1:
                break
        return d
    
    def transform_little_tab(self,cluster):
        d = {}
        if len(cluster)==1:
            d[cluster[0]] = 0
        if len(cluster) == 2:
            d[cluster[0]] = 0
            d[cluster[1]] = 1
        if len(cluster) == 3:
            d[cluster[0]] = 0
            d[cluster[1]] = 1
            d[cluster[2]] = 2
        return d
    
    def res_to_export(self,res):
        curr = 0
        d = {}
        for dict in res:
            i = 0
            keys = list(dict.keys())
            while i < len(keys):
                j = 0
                while dict[keys[j]] != i:
                    j+=1
                d[keys[j]] = curr
                curr += 1
                i+=1
        return d
    
    def main(self):
        clusters = self.make_clusters()
        res = []
        for cluster in clusters:
            if len(cluster)<=3:
                res.append(self.transform_little_tab(cluster))
            else:
                d = self.get_results_of_PL(cluster)
                # while len(list(d.keys())) < len(cluster):
                #     for stop in cluster:
                #         if stop not in list(d.keys()):
                #             d = add_value(d,stop)     
                res.append(d)
        return self.res_to_export(res)
    
# routeid = 'RouteID_00143bdd-0a6b-49ec-bb35-36593d303e77'
# optimize_route_0 = Route(travtimes[routeid],routedata[routeid],package[routeid])
# result = optimize_route_0.main()
# print(result)