#!/usr/bin/python


# Copyright 2023 Intel Corporation
# SPDX-License-Identifier: MIT License

#Author: Kartik Lakhotia


import sys
import re
import os
import string
import copy
import random
import math
import time
import argparse

from enum import Enum

#CREATE PARSER
parser  = argparse.ArgumentParser(
    description = 'run sweep over injection rate for a particular configuration',
    epilog      = 'sst sweep'
)

subparser       = parser.add_subparsers(help='topology', dest='topo')
topology_parsers= []

#Polarfly
parser_pf       = subparser.add_parser('polarfly', help='simulates polarfly')
parser_pf.add_argument('-q', dest='q', type=int, required=True, help='prime power')
parser_pf.add_argument('-rf', dest='rf', type=str, choices=['MINIMAL', 'VALIANT', 'UGAL', 'UGAL_PF'], default='MINIMAL', help='routing function')
topology_parsers.append(parser_pf)

#Polarstar
parser_ps       = subparser.add_parser('polarstar', help='simulates polarstar')
parser_ps.add_argument('-d', dest='d', type=int, required=True, help='network radix')
parser_ps.add_argument('-sn', dest='sn', type=str, choices=['iq', 'paley', 'max'], default='max', help='supernode topology')
parser_ps.add_argument('-pfq', dest='pfq', type=int, default=-1, help='structure graph (polarfly) prime power parameter')
parser_ps.add_argument('-snq', dest='snq', type=int, default=-1, help='supernode topology parameter') 
parser_ps.add_argument('-rf', dest='rf', type=str, choices=['MINIMAL', 'VALIANT', 'UGAL'], default='MINIMAL', help='routing function')
topology_parsers.append(parser_ps)

#Fat-tree
parser_ft       = subparser.add_parser('fattree', help='simulates fattree')
parser_ft.add_argument('-sh', dest='shape', type=str, required=True, help='fattree shape (e.g.2,2:2,2:4)')
parser_ft.add_argument('-rf', dest='rf', type=str, choices=['deterministic', 'adaptive'], default='deterministic', help='routing function')  
topology_parsers.append(parser_ft)

#HyperX
parser_hx       = subparser.add_parser('hyperx', help='simulates hyperx')
parser_hx.add_argument('-sh', dest='shape', type=str, required=True, help='hyperx shape (e.g. 4x4x4)')
parser_hx.add_argument('-rf', dest='rf', type=str, choices=["DOR", "MIN-A"], default="DOR", help='routing function')
parser_hx.add_argument('-w', dest='w', type=str, required=True, help='width of links in each dimension (eg.g. 2x1x2)')
topology_parsers.append(parser_hx)

for sub in topology_parsers:
    sub.add_argument('-sat', dest='sat', type=float, default=1000, help='saturation latency cutoff (in ns)')
    sub.add_argument('-o', dest='opfile', type=str, required=True, help='output csv file')
    sub.add_argument('-k', dest='k', type=int, help='num endpoints per router (not needed for fat-tree)')
    sub.add_argument('-fm', dest='fine_max', type=float, help='maxmimum value for fine grained simulations')
    sub.add_argument('-t', dest='traffic', type=str, choices=['UNIFORM', 'SHIFT'], required=True, help='traffic pattern')
    sub.add_argument('-cstep', dest='coarse_incr', type=float, default=0.1, help='coarse simulation step (load increments)')

    sub.add_argument('-fstep', dest='fine_incr', type=float, default=0.01, help='fine simulation step (load increments)')
    sub.add_argument('-lmin', dest='min_rate', type=float, default=0.0, help='minimum injection load')
    sub.add_argument('-lmax', dest='max_rate', type=float, default=1.0, help='maximum injection load')


args            = parser.parse_args()

#CREATE DIRECTORIES AND DEFINE PATHS
dir_demarc      = '/'
sst_exec        = 'sst -v'
sst_elements    = os.getenv('SST_ELEMENTS_ROOT') + dir_demarc + 'src/sst/elements/'
merlin_path     = sst_elements + dir_demarc + 'merlin'
tests_path      = merlin_path + dir_demarc + 'tests/'
template_suffix = '_configfile_template.py'
config_template = tests_path + dir_demarc + args.topo + template_suffix
logs_path       = tests_path + dir_demarc + 'logs/'
config_file_path= tests_path + dir_demarc + 'sweep_configs'

if (not os.path.isdir(logs_path)):
    os.mkdir(logs_path)
if (not os.path.isdir(config_file_path)):
    os.mkdir(config_file_path)

timestamp       = time.time()
logs_path       = logs_path + dir_demarc + str(timestamp) + dir_demarc
print("--> Logs in " + logs_path)
config_file_path= config_file_path + dir_demarc + str(timestamp) + dir_demarc
print("--> COnfig files in " + config_file_path)

print('Logs stored at : ' + logs_path)
print('Config file stored at : ' + config_file_path)

if (not os.path.isdir(logs_path)):
    os.mkdir(logs_path)
if (not os.path.isdir(config_file_path)):
    os.mkdir(config_file_path)

new_config_temp = config_file_path +  dir_demarc + args.topo + template_suffix 
os.system('cp ' + config_template + ' ' + new_config_temp)
print('Config file template : ' + new_config_temp)


def generate_config_file(args, load, template, output):
    q_str   = "specified_q="
    q       = None
    k       = None
    rf_str  = 'specified_algo='
    pat_str = 'specified_traffic=' 
    load_str= 'specified_load=' 
    k_str   = 'specified_k='
    shp_str = 'specified_shape='
    w_str   = 'specified_width='
    
    if (args.topo == 'polarfly'):
        q       = args.q
        k       = args.k if args.k is not None else (q+1)//2
    elif (args.topo == 'polarstar'):
        q_str   = 'specified_d='
        q       = args.d
        k       = args.k if args.k is not None else q//3
    elif (args.topo == 'fattree'):
        pass
    elif (args.topo == 'hyperx'):
        k       = args.k
    else:
        raise Exception("I do not understand how to simulate " + args.topo)

    f       = open(template, 'r')
    lines   = f.readlines()
    op      = open(output, 'w')

    for line in lines:
        if q_str in line:
                opline  = line.replace(q_str, q_str+str(q))
        elif shp_str in line:
            opline  = line.replace(shp_str, shp_str+"'"+args.shape+"'")
        elif w_str in line:
            opline  = line.replace(w_str, w_str+"'"+args.w+"'")
        elif rf_str in line:
            opline  = line.replace(rf_str, rf_str+"'"+args.rf+"'")
        elif load_str in line:
            opline  = line.replace(load_str, load_str+str(load))
        elif pat_str in line:
            opline  = line.replace(pat_str, pat_str+"'"+args.traffic+"'")
        elif k_str in line:
            opline  = line.replace(k_str, k_str+str(k))
        else:
            opline  = line
        op.write(opline)

    f.close()
    op.close()


def analyze_log(log_file):
    str1        = 'Offered   Average'
    str2        = 'Load    Latency'

    units_scale = {'ps':0.001, 'ns':1.0, 'us':1000, 'ms':1000000}
    units       = list(units_scale.keys())
    for key in units:
        keystar                 = key+'*'
        units_scale[keystar]    = units_scale[key]
        

    class states(Enum):
        str1_search = str1
        str2_search = str2
        stat_search = 'stat'

    load        = None
    lat         = None
    state       = states.str1_search

    f           = open(log_file, 'r')
    for line in f.readlines():
        elems   = line.strip().split()
        if (state == states.str1_search):
            if (state.value in line):
                state   = states.str2_search 
        elif (state == states.str2_search):
            if (state.value in line):
                state   = states.stat_search
        elif (state == states.stat_search):
            load    = float(elems[0].strip())
            lat     = float(elems[1].strip())*units_scale[elems[2].strip()]
            state   = states.str1_search
            break
        else:
            raise Exception("unrecognized state when analyzing log file")

    f.close()
                 
    return load, lat
             


def run_sim_s(min_rate, max_rate, incr, args, logs_path, config_file_path, new_config_temp):
    saturation_lat  = args.sat 
    num_steps       = int((max_rate - min_rate + 0.000001)/incr) + 1
    exec_cmd        = 'sst -v '
    load_vs_lat     = {}

    for i in range(num_steps):
        inj_rate= min_rate + i*incr
        if (inj_rate <= max_rate):
            if (inj_rate <= 0):
                inj_rate    = 0.01
            print('Simulating with load = ' + str(inj_rate))
            config_file = config_file_path + '/' + args.topo + '_load_' + str(inj_rate) + '.py'
            generate_config_file(args, inj_rate, new_config_temp, config_file)

            log_file    = logs_path + '/' + args.topo + '_load_' + str(inj_rate) + '.log'
            run_cmd     = exec_cmd + config_file + " > " + log_file
            os.system(run_cmd) 

            load, lat               = analyze_log(log_file)
            load_vs_lat[load]       = lat 
            
            if (lat > saturation_lat):
                return load, load_vs_lat

    return max_rate, load_vs_lat

         
print("--> RUNNING COARSE GRANULARITY SIMULATIONS")
coarse_incr     = args.coarse_incr
min_rate        = max(args.min_rate, 0.0)
max_rate        = min(args.max_rate, 1.0)
assert(coarse_incr > 0)
assert(max_rate >= min_rate)

coarse_max, coarse_results  = run_sim_s(min_rate, max_rate, coarse_incr, args, logs_path, config_file_path, new_config_temp)

fine_incr       = args.fine_incr
fine_min        = max(fine_incr, coarse_max - 2*coarse_incr)
fine_max        = max(coarse_max - fine_incr, fine_min)
assert(fine_incr > 0)

print("--> RUNNING FINE GRANULARITY SIMULATIONS")
fine_max, results           = run_sim_s(fine_min, coarse_max, fine_incr, args, logs_path, config_file_path, new_config_temp)

results.update(coarse_results)

print("--> WRITING RESULTS")
op              = open(args.opfile, 'w')
op.write('Load, Latency\n')
for key in sorted(results):
    op.write(str(key) + ', ' + str(results[key]) + '\n')
op.close()
