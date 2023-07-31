#!/bin/sh

action(){
    SPAWNPOINT=$(pwd)

    # source grid environment
    source /cvmfs/grid.cern.ch/centos7-wn-4.0.5-1_umd4v1/etc/profile.d/setup-c7-wn-example.sh

    # untar tarball
    tar -xzf generation*.tar.gz
    rm generation*.tar.gz

    # setup law
    export LAW_HOME="$PWD/.law"
    export LAW_CONFIG_FILE="$PWD/law.cfg"
    export LUIGI_CONFIG_PATH="$PWD/luigi.cfg"

    export ANALYSIS_PATH="$PWD"
    export ANALYSIS_DATA_PATH="$ANALYSIS_PATH"

    export PATH="$PWD/law/bin:$PWD/luigi/bin:$PATH"
    export PYTHONPATH="$PWD/enum34-1.1.10:$PWD/law:$PWD/luigi:$PWD/six:$PWD:$PYTHONPATH"

    # setup SHERPA
    # source /cvmfs/sft.cern.ch/lcg/views/LCG_102/x86_64-centos7-gcc11-opt/setup.sh
    source /cvmfs/cms.cern.ch/slc7_amd64_gcc700/external/gcc/7.0.0-pafccj/etc/profile.d/init.sh
    export SHERPA_INCLUDE_PATH=/cvmfs/etp.kit.edu/MC_generator/Sherpa/SHERPA-MC-2.2.12/include/SHERPA-MC
    export SHERPA_SHARE_PATH=/cvmfs/etp.kit.edu/MC_generator/Sherpa/SHERPA-MC-2.2.12/share/SHERPA-MC
    export SHERPA_LIBRARY_PATH=/cvmfs/etp.kit.edu/MC_generator/Sherpa/SHERPA-MC-2.2.12/lib/SHERPA-MC
    export LD_LIBRARY_PATH=$SHERPA_LIBRARY_PATH:$LD_LIBRARY_PATH
    export PATH=/cvmfs/etp.kit.edu/MC_generator/Sherpa/SHERPA-MC-2.2.12/bin:$PATH
}

action "$@"
