#!/usr/bin/env python

# Copyright 2009-2022 NTESS. Under the terms
# of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Copyright (c) 2009-2022, NTESS
# All rights reserved.
#
# Portions are copyright of other developers:
# See the file CONTRIBUTORS.TXT in the top level directory
# of the distribution for more information.
#
# This file is part of the SST software package. For license
# information, see the LICENSE file in the top level directory of the
# distribution.

# Copyright 2023 Intel Corporation
# SPDX-License-Identifier: MIT License

# Authors: Kartik Lakhotia, Sai Prabhakar Rao Chenna 

import sst
from sst.merlin.base import *
from sst.merlin.endpoint import *
from sst.merlin.interface import *
from sst.merlin.targetgen import *
from sst.merlin.topology import *


if __name__=="__main__":
    ### Configuration
    specified_shape=
    specified_algo= 
    specified_load= 
    specified_traffic= 


    ### Setup the topology
    topo                        = topoFatTree()
    topo.routing_alg            = specified_algo
    topo.shape                  = specified_shape


    # Set up the routers
    router                      = hr_router()
    router.link_bw              = "1GB/s"
    router.flit_size            = "8B"
    router.xbar_bw              = "1GB/s"
    router.input_latency        = "2ns"
    router.output_latency       = "2ns"
    router.input_buf_size       = "2kB"
    router.output_buf_size      = "2kB"
    router.num_vns              = 1
    router.xbar_arb             = "merlin.xbar_arb_lru"
    router.oql_track_port       = True

    topo.router                 = router
    topo.link_latency           = "3ns"

    ### set up the endpoint
    networkif                   = LinkControl()
    networkif.link_bw           = "1GB/s"
    networkif.input_buf_size    = "2kB"
    networkif.output_buf_size   = "2kB"

    #jobId, # endpoints
    ep                          = OfferedLoadJob(0,topo.getNumNodes())
    ep.network_interface        = networkif  
    ep.offered_load             = specified_load
    ep.link_bw                  = "1GB/s"
    ep.warmup_time              = "5us"
    ep.collect_time             = "100us"
    ep.drain_time               = "10us"
    ep.message_size             = "64B"

    pat                         = UniformTarget()
    pat_traffic                 = specified_traffic
    if (pat_traffic=="SHIFT"):
        pat                     = ShiftTarget() 
        pat.shift               = topo.getNumNodes()//2
    elif (pat_traffic=="BIT_COMPLEMENT"):
        pat                     = BitComplementTarget()
    ep.pattern                  = pat

    system                      = System()
    system.setTopology(topo)
    system.allocateNodes(ep,"linear")
    system.build() 


    sst.setStatisticLoadLevel(9)
    sst.enableAllStatisticsForAllComponents()
    fname                       = "./run_stats_fattree.csv"

    sst.setStatisticOutput("sst.statOutputCSV", {"filepath" : fname, "separator" : ", " } )

