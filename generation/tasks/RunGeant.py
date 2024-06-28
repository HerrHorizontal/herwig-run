

import law
import luigi
from luigi.util import inherits
import os, shutil
import random
import glob

from subprocess import PIPE
from generation.framework.utils import run_command, set_environment_variables

from generation.framework.tasks import GenRivetTask, GenerationScenarioConfig
from generation.framework.htcondor import HTCondorWorkflow

from .HerwigRun import HerwigRun
from .SherpaRun import SherpaRun
from .RivetBuild import RivetBuild

from law.logger import get_logger


logger = get_logger(__name__)


class RunGeant(HTCondorWorkflow, law.LocalWorkflow):
    """
    TODO
    """

    # allow outputs in nested directory structure
    output_collection_cls = law.NestedSiblingFileCollection

    # configuration variables
    mc_setting = "withNP"

    files_per_job = luigi.IntParameter(
        default=1,
        description="Number of HepMC files taken as an input for GEANT. \
                TODO"
    )
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation."
    )
    # TODO: other GEANT parameters, e.g. GEANT model file/configuration, etc.

    exclude_params_req = {
        "files_per_job",
        "bootstrap_file", 
        "htcondor_walltime", "htcondor_request_memory", 
        "htcondor_requirements", "htcondor_request_disk",
        #TODO: add exclude parameters
    }


    def workflow_requires(self):
        reqs = super(RunGeant, self).workflow_requires()
        # analyzing requires successfully generated events
        # require the parent workflow and inform it about the branches to produce by passing
        # the "branches" parameter and simultaneously preventing {start,end}_branch being used
        branches = sum(self.branch_map.values(), [])
        if str(self.mc_generator).lower() == "herwig":
            reqs["MCRun"] = HerwigRun.req(
                self,
                branches=branches,
                _exclude=[
                    "start_branch", "end_branch",
                    "bootstrap_file",
                    "htcondor_walltime", "htcondor_request_memory",
                    "htcondor_requirements", "htcondor_request_disk"
                    ]
                )
        elif str(self.mc_generator).lower() == "sherpa":
            reqs["MCRun"] = SherpaRun.req(
                self,
                branches=branches,
                _exclude=[
                    "start_branch", "end_branch",
                    "bootstrap_file",
                    "htcondor_walltime", "htcondor_request_memory",
                    "htcondor_requirements", "htcondor_request_disk"
                    ]
                )
        else:
            raise ValueError("Unknown MC generator: {}".format(self.mc_generator))
        #TODO: additional GEANT requirements
        # reqs["..."] = ...
        return reqs


    def create_branch_map(self):
        # each analysis job analyzes a chunk of HepMC files
        if str(self.mc_generator).lower() == "herwig":
            branch_chunks = HerwigRun.req(self).get_all_branch_chunks(self.files_per_job)
        elif str(self.mc_generator).lower() == "sherpa":
            branch_chunks = SherpaRun.req(self).get_all_branch_chunks(self.files_per_job)
        else:
            raise ValueError("Unknown MC generator: {}".format(self.mc_generator))
        # one by one job to inputfile matching
        return {
            jobnum: branch_chunk 
            for jobnum, branch_chunk in enumerate(branch_chunks)
        }


    def requires(self):
        # each branch task requires existent HEPMC files to further simulate
        req = dict()
        if str(self.mc_generator).lower() == "herwig":
            req["MCRun"] = [
                    HerwigRun.req(self, branch=b)
                    for b in self.branch_data
                ]
        elif str(self.mc_generator).lower() == "sherpa":
            req["MCRun"] = [
                    SherpaRun.req(self, branch=b)
                    for b in self.branch_data
                ]
        #TODO: additional GEANT requirements
        # req["GEANTConfig"] = ...
        return req


    def remote_path(self, *path):
        parts = (self.__class__.__name__,str(self.mc_generator).lower(),self.campaign) + path
        #TODO: think about directory structure
        return os.path.join(*parts)


    def output(self):
        #TODO: think about directory structure
        dir_number = int(self.branch)/1000
        return self.remote_target("{DIR_NUMBER}/{GEANT_FILE_NAME}job{JOB_NUMBER}.yoda".format(
            DIR_NUMBER=int(dir_number),
            GEANT_FILE_NAME=str(some_geant_identifier),
            JOB_NUMBER=str(self.branch)
            ))


    def run(self):
        # branch data
        #TODO: get relevant branch data and configuration variables

        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            logger.error("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("TODO ")
        print("=======================================================")

        # set environment variables
        my_env = set_environment_variables("$ANALYSIS_PATH/setup/setup_geant.sh")

        # identify and get the HEPMC files for analyzing
        logger.info("Input events: {}".format(self.input()['MCRun']))
        for target in self.input()['MCRun']:
            with target.localize('r') as input_file:
                os.system('tar -xvjf {}'.format(input_file.path))

        input_files = glob.glob('*.hepmc')
        output_file = #TODO

        # run GEANT
        #TODO: write GEANT call
        

        logger.info('Executable: {}'.format(" ".join(_rivet_exec + _rivet_args)))
        try:
            run_command(geant_exe, env=my_env)
        except RuntimeError as e:
            output.remove()
            raise e

        _output_file = os.path.abspath(output_file)

        if os.path.exists(_output_file):
            output.copy_from_local(_output_file)
        else:
            raise IOError("Could not find output file {}!".format(_output_file))


        print("=======================================================")
