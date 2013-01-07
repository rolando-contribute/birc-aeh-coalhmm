from scipy import *
from scipy.stats import expon
from model import build_simple_model, build_epoch_seperated_model
from fasta_parser import readAlignment
from mini_hmm import *
from scipy.optimize import fmin
import sys
import os.path
import time
from itertools import izip

def readObservations(filename, seq_names):
    alignments = readAlignment(filename)
    srcs = [(i, alignments[name]) for i, name in enumerate(seq_names)]

    legal = set(['A', 'C', 'G', 'T', 'N', '-'])
    col_map = dict()
    first = alignments[seq_names[0]]
    #obs = Sequence(len(first))
    obs = array([0]*len(first), dtype=int16)
    tmp = [0 for n in seq_names]
    for i in xrange(len(first)):
        for j, src in srcs:
            s = src[i]
            tmp[j] = s in legal and s or 'N'
        col = tuple(tmp)
        v = col_map.setdefault(col, len(col_map))
        obs[i] = v
    return obs, col_map

def copyTable(dst, src):
   for i in xrange(src.shape[0]):
       for j in xrange(src.shape[1]): 
           dst[i,j] = src[i,j]

def default_bps(model, c, r, t):
    noBrPointsPerEpoch = model.nbreakpoints
    nleaves = model.nleaves
    nepochs = len(noBrPointsPerEpoch)
    ebps = []
    bps = []
    for e in xrange(0, nepochs):
        theta = 1.0 / c[e]
        nbps = noBrPointsPerEpoch[e]
        if e == nepochs - 1:
            new_bps = [(x*theta+t[e]) for x in expon.ppf([float(i)/nbps for i in xrange(nbps)])]
        else:
            new_bps = linspace(t[e], t[e+1], nbps+1)[:nbps]
        ebps.append(new_bps)
        bps.extend(new_bps)
    return bps, ebps


def logLikelihood(model, obs, col_map, c, r, m, t, posterior_decoding=False):
    noBrPointsPerEpoch = model.nbreakpoints
    nleaves = model.nleaves
    nepochs = len(noBrPointsPerEpoch)
    all_time_breakpoints, time_breakpoints = default_bps(model, c, r, t)

    M = []
    for e in xrange(len(noBrPointsPerEpoch)):
        newM = identity(nleaves)
        newM[:] = m[e]
        M.append(newM)

    pi, T, E = model.run(r, c, time_breakpoints, M, col_map=col_map)
    assert not any(isnan(pi))
    assert not any(isnan(T))
    assert not any(isnan(E))
    logL = inline_forward_scaled(
            array((pi), dtype=float64),
            array((T), dtype=float64),
            array((E), dtype=float64), obs)
    assert logL == logL
    return logL

def mini_hmm_forward(pi, T, E, obs):
    return inline_forward_scaled(pi, T, E, obs)

def mini_hmm_prepare(pi, T, E):
    return (array(pi, dtype=float64),
            array(T, dtype=float64),
            array(E, dtype=float64))

def logL_multiseq(model, all_obs, col_map, c, r, m, t, prepare_matrices=mini_hmm_prepare, single_logL=mini_hmm_forward):
    noBrPointsPerEpoch = model.nbreakpoints
    nleaves = model.nleaves
    nepochs = len(noBrPointsPerEpoch)
    all_time_breakpoints, time_breakpoints = default_bps(model, c, r, t)

    M = []
    for e in xrange(len(noBrPointsPerEpoch)):
        newM = identity(nleaves)
        newM[:] = m[e]
        M.append(newM)

    pi, T, E = model.run(r, c, time_breakpoints, M, col_map=col_map)
    assert not any(isnan(pi))
    assert not any(isnan(T))
    assert not any(isnan(E))
    pi, T, E = prepare_matrices(pi,T,E)
    logL = 0.0
    for obs in all_obs:
        logL += single_logL(pi,T,E,obs)
    assert logL == logL
    return logL

