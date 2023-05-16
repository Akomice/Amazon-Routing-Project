import pulp
import networkx as nwx
import matplotlib.pyplot as plt

# Votre chemin vers le cplex.exe
path_to_cplex = '/home/nathan/Documents/cplex/cplex/bin/x86-64_linux/cplex' 

# Génération d'un graphe complet orienté

def generate_full_digraph(n):
    G = nwx.DiGraph()
    G.add_nodes_from([i for i in range(1,n+1)])
    for i in range(1,n+1):
        for j in range(i+1,n+1):
            G.add_edge(i,j)
            G.add_edge(j,i)
    return G

class Solveur():

    def __init__(self,nb,p,val_ab=None,m_val=None):

        #On pose pour simplifier v0 = 0 et vf = n-1

        self.n = nb
        self.poids = p
        self.ab = val_ab
        self.t = [pulp.LpVariable(name=f"t{i}",cat=pulp.LpContinuous,lowBound=val_ab[i][0],upBound=val_ab[i][1]) for i in range(nb)]
        self.m = m_val

    def defineProblem(self):
        
        n = self.n
        self.problem = pulp.LpProblem('PL',pulp.LpMinimize)
        X = []
        for i in range(n):
            X.append([])
            for j in range(n):
                X_i_j = pulp.LpVariable(f'X_({i},{j})', cat=pulp.LpBinary)
                X[i].append(X_i_j)
        self.X = X

    def objectiveFunction(self):

        n = self.n
        e = []
        for i in range(n):
            for j in range(n):
                e.append((self.X[i][j],self.poids[i][j]))
        c = pulp.LpAffineExpression(e)
        self.problem.setObjective(c)
    
    def addConditions(self):

        X = self.X
        n = self.n

        #(B.2a)

        for i in range(n-1):
            l = []
            for j in range(n):
                l.append((X[i][j],1))
            cdt = pulp.LpAffineExpression(l)
            self.problem += cdt == 1

        #(B.2b)

        for j in range(1,n):
            l = []
            for i in range(n):
                l.append((X[i][j],1))
            cdt = pulp.LpAffineExpression(l)
            self.problem += cdt == 1

        #(B.2c)

        for i in range(1,n-1):
            l1 = []
            l2 = []
            for j in range(n):
                l1.append((X[i][j],1))
                l2.append((X[j][i],1))
            cdt_1 = pulp.LpAffineExpression(l1) 
            cdt_2 = pulp.LpAffineExpression(l2)
            self.problem += (cdt_1 == cdt_2)

        #(B.2d)

        l1 = []
        l2 = []
        i = 0
        for j in range(n):
            l1.append((X[i][j],1))
            l2.append((X[j][i],1))
        cdt_1 = pulp.LpAffineExpression(l1)
        cdt_2 = pulp.LpAffineExpression(l2)
        self.problem += ((cdt_1 - cdt_2) == 1)

        #(B.2e)

        l1 = []
        l2 = []
        i = n-1
        for j in range(n):
            l1.append((X[i][j],1))
            l2.append((X[j][i],1))
        cdt_1 = pulp.LpAffineExpression(l1)
        cdt_2 = pulp.LpAffineExpression(l2)
        self.problem += ((cdt_1 - cdt_2) == -1)

        #(B.2f)

        for i in range(n):
            self.problem += X[i][i] == 0

    def addMoreConditions(self):

        #(B.2g)

        n = self.n
        t = self.t
        P = self.poids
        M = self.m
        ab = self.ab
        X = self.X

        for i in range(n):
            for j in range(n):
                self.problem += (t[i] + P[i][j] - t[j]) <= (M * (1 - X[i][j]))

        #(B.2h)

        for i in range(n):
            self.problem += (ab[i][0] <= t[i]) and (t[i] <= ab[i][1])

        #(B.2i) 

        #Déjà fait par construction des X_i,j

    def solve(self):

        self.problem.writeLP("analyze.lp")
        solver = pulp.CPLEX_CMD(path=path_to_cplex,keepFiles=True,msg=False)
        self.problem.solve(solver)

    def main(self):

        self.defineProblem()
        self.objectiveFunction()
        self.addConditions()
        self.addMoreConditions()
        self.solve()

#solving = Solveur(nb=n,p=P,val_ab=ab,t_val=t,m_val=M)

#solving.main()









