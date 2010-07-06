from scipy import *
from scipy.linalg import expm
from sets import ImmutableSet as iset

from intervals import *
from statespace_generator import BasicCoalSystem
from scc import build_scc, SCCGraph
from tree import *
from emission_matrix import *

#print genRateMatrix(states,edges,C=1.0,R=1.0e-4)
def genRateMatrix(states,edges,**mapping):
    def f(t):
        return mapping[t]

    n_states = len(states)
    print n_states
    M = zeros((n_states, n_states))
    M.shape = n_states, n_states
    for (a,t,b) in edges:
        M[a,b] = f(t)
    for i in xrange(n_states):
        row = M[i, :]
        M[i,i] = -sum(row)

    M = matrix(M)
    return M

def prettify_state(s):
    """Convert a coal system state to something nicer.
    
    example:
      iset([(iset([3]), iset([3])),
            (iset([1]), iset([1])),
            (iset([2]), iset([2]))])
    to:
      {3, 1, 2}, {3, 1, 2}
    """
    def f(s, side, d):
        if d == 0:
            tmp = [f(sub, side, d+1) for sub in s if len(s) > 0]
            return ", ".join([x for x in tmp if x.strip() != ""])
        elif d == 1:
            return "".join(sorted([str(x) for x in s[side] if len(s[side]) > 0]))
    return "{" + f(s, 0, 0) + "}, {" + f(s, 1, 0) + "}"


x = BasicCoalSystem([0,1,2])
states, edges = x.compute_state_space()

G = SCCGraph(states, edges)
G.add_transitive_edges()

if False:
    f = file("graph", "w")
    f.write("digraph {\n")
    for a in xrange(len(G.E)):
        f.write('%i [label="%s"]\n' % (a, prettify_state(G.state(a))))
        for b in G.E[a]:
            f.write("%i -> %i\n" % (a, b))
    f.write("}\n")
    f.close()

def set_filler(Sa, Sb):
    pairs = set()
    def f(s):
        ta = make_tree(G, s, 0)
        tb = make_tree(G, s, 1)
        Sa.add(ta)
        Sb.add(tb)
        assert (ta, tb) not in pairs
        pairs.add((ta,tb))
    return f

unique_L = set()
unique_R = set()
def dfs(a, S, E):
    S.append(a)
    if len(E[a]) == 0:
        do_on_all_distributions(S, 5, set_filler(unique_L, unique_R))
    for b in E[a]:
        dfs(b, S, E)
    S.pop()

dfs(len(G.V)-1, [], G.E)
print len(unique_L), len(unique_R)
for l,r in zip(unique_L, unique_R):
    print tree_to_newick(l), tree_to_newick(r)

theta = 20000.0 * 20 * 1e-9
interval_times = [0.0, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
#test_tree = (4, iset([iset([1]), (2, iset([iset([0]), iset([2])]))]))

#Em, tmap = build_emission_matrix(unique_L, 3, interval_times, theta)

#print Em[0,:]
#print "sum :", sum(Em[0,:])

