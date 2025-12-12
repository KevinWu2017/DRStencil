import itertools
from functools import reduce
import os
import random
import sys
import pickle
import datetime
import time
maxThreadsPerBlockLg2 = 10 # 1024
maxShmPerBlockLg2 = 15 # 32K
order = 1

def FilterParams(spaceVector):
    step, dist, blockSize, sn, s_unroll, blockMergeX, mergeFactorX, blockMergeY, mergeFactorY, m_threshold, prefetch = spaceVector
    shmemUsage = (step * order + 1) * (mergeFactorX * blockSize[0]) * (mergeFactorY * blockSize[1])
    if shmemUsage > 2 ** (maxShmPerBlockLg2 - 3):
        return False
    if dist > step * order or dist < (step - 1) * order:
        return False
    if step * order * 2 >= min(blockSize[0] * mergeFactorX, blockSize[1] * mergeFactorY):
        return False
    if blockSize[0] <= 8:
        return False
    if blockMergeX and mergeFactorX == 1:
        return False
    if blockMergeY and mergeFactorY == 1:
        return False
    return True


def cfgToCommandLine(spaceVector):
    step, dist, blockSize, sn, s_unroll, blockMergeX, mergeFactorX, blockMergeY, mergeFactorY, m_threshold, prefetch = spaceVector
    cmd = " --bx {0} --by {1} --sn {2} --stream-unroll {3}".format(blockSize[0], blockSize[1], sn, s_unroll)
    cmd += " --step {0} --dist {1}".format(step, dist)

    if blockMergeX:
        cmd += " --block-merge-x {0}".format(mergeFactorX)
    else:
        cmd += " --cyclic-merge-x {0}".format(mergeFactorX)
    if blockMergeY:
        cmd += " --block-merge-y {0}".format(mergeFactorY)
    else:
        cmd += " --cyclic-merge-y {0}".format(mergeFactorY)
    cmd += " --merge-forward {0}".format(m_threshold)
    if prefetch:
        cmd += " --prefetch"

    return cmd


def cfgToString(spaceVector):
    step, dist, blockSize, sn, s_unroll, blockMergeX, mergeFactorX, blockMergeY, mergeFactorY, m_threshold, prefetch = spaceVector
    cmd = "fu{0}d{1}bx{2}y{3}sn{4}u{5}".format(step, dist, blockSize[0], blockSize[1], sn, s_unroll)
    if blockMergeX:
        cmd += "bmx{0}".format(mergeFactorX)
    else:
        cmd += "cmx{0}".format(mergeFactorX)
    if blockMergeY:
        cmd += "bmy{0}".format(mergeFactorY)
    else:
        cmd += "cmy{0}".format(mergeFactorY)
    cmd += "mf{0}".format(m_threshold)
    if prefetch:
        cmd += "p"

    return cmd


def getElapsedTime (start, end):
    return (end - start).seconds + (end - start).microseconds / 1e6


def getMetrics(stencilName, startTime, best, fuse_steps):
    logfile = open('prof/'+str(stencilName)+'.csv', 'r')
    idx = -1
    counter = 0
    for line in logfile:
        if line.find('Metric Value') > -1:
            idx = line.split(',').index('"Metric Value"')
        elif idx > -1 :
            seg = line.split('",')
            if idx < len(seg) and seg[idx-2].find("Duration") > -1:
                duration = seg[idx][1:].replace(',','')
                if duration.isdigit():
                    if int(best) > int(duration):
                        best = int(duration)
                        durationLog = open(f'duration_{fuse_steps}.log', 'a')
                        currentTime = datetime.datetime.now()
                        durationLog.write (str((currentTime-startTime).seconds) + ' s, ' + str(best) + '\n')
                        durationLog.close()
                counter += 1
                break

    logfile.close()
    return best


def searchSpace(fuse_steps: int):

    startTime = datetime.datetime.now()
    best = 1e12
    paras = []

    blockSize = itertools.product([2**i for i in range(3, 7)], repeat=2)
    for paraVector in filter(FilterParams, itertools.product(
      [fuse_steps], # time steps to fuse
      [dist for dist in range (1, fuse_steps + 1)], # Dist
      filter(lambda x: x[0] * x[1] <= 2 ** (maxThreadsPerBlockLg2),
        blockSize),
      [2 ** sn for sn in range (3, 7)],
      [4, 8],
      [False, True],
      [2 ** mFactorLg2 for mFactorLg2 in range (0, 3)],
      [False, True],
      [2 ** mFactorLg2 for mFactorLg2 in range (0, 3)],
      [5],
      [False, True],
     )):
        paras.append (paraVector)

    random.shuffle (paras)
    cnt = 0
    for paraVector in paras:
        cnt += 1
        config = cfgToCommandLine(paraVector)
        conf_str = cfgToString(paraVector)
        cmd = " ".join(["./drstencil --3d", \
          config, " -o ./cu/"+conf_str+".cu 3d27pt_box.stc"])
        os.system(cmd)
        
        print ("{0}/{1}: {2}".format(cnt, len(paras), conf_str))
        os.system("./compile_run.sh " + conf_str)
        best = getMetrics (conf_str, startTime, best, fuse_steps)

        currentTime = datetime.datetime.now()
        if (currentTime-startTime).seconds > 3600:
            break

    durationLog = open(f'duration_{fuse_steps}.log', 'a')
    currentTime = datetime.datetime.now()
    durationLog.write (str((currentTime-startTime).seconds) + ' s, ' + str(best) + '\n')
    durationLog.close()


if __name__ == '__main__':
    for fuse_steps in range(1, 9):
        print(f"starting search for fuse steps = {fuse_steps}")
        searchSpace(fuse_steps)
