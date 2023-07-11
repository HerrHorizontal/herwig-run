#!/bin/sh

# source grid environment
source /cvmfs/grid.cern.ch/centos7-wn-4.0.5-1_umd4v1/etc/profile.d/setup-c7-wn-example.sh

# setup SHERPA
source /cvmfs/cms.cern.ch/slc7_amd64_gcc700/external/gcc/7.0.0-pafccj/etc/profile.d/init.sh
export SHERPA_INCLUDE_PATH=/cvmfs/etp.kit.edu/MC_generator/Sherpa/SHERPA-MC-2.2.12/include/SHERPA-MC
export SHERPA_SHARE_PATH=/cvmfs/etp.kit.edu/MC_generator/Sherpa/SHERPA-MC-2.2.12/share/SHERPA-MC
export SHERPA_LIBRARY_PATH=/cvmfs/etp.kit.edu/MC_generator/Sherpa/SHERPA-MC-2.2.12/lib/SHERPA-MC
export LD_LIBRARY_PATH=$SHERPA_LIBRARY_PATH:$LD_LIBRARY_PATH
export PATH=/cvmfs/etp.kit.edu/MC_generator/Sherpa/SHERPA-MC-2.2.12/bin:$PATH
