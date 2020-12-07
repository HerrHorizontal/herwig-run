# Herwig event generation

Repository for tracking the development of distributable MC event generation with [Herwig7](https://herwig.hepforge.org/).


## Herwig Docker image

This repository provides a Docker image for running standalone Herwig. 
See also the linked [Docker hub](https://hub.docker.com/repository/docker/mhorzela/herwig-standalone). 
This image contains a full installation of Herwig with all necessary linked software components. 
Since the size of the docker image is quite big (aprox. 8.5GiB) it might not be the best option 
to use for distributed execution in a batch system. 


## LAW setup

For automated and distributed production of HEP-particle-collision events with Herwig, 
exploiting all functionality, an implementation of the workflow using [LAW](https://github.com/riga/law) is provided.

### Software dependencies
In the following the setup of needed software is explained.

#### Herwig7
The necessary [Herwig7](https://herwig.hepforge.org/) software is loaded from CVMFS (`/cvmfs/pheno.egi.eu/Herwig`) in the `setup/setup_herwig.sh` script 
for local execution and `Law-Setup/generation/setup_lawherwig.sh` for remote jobs.
If you want to load the Herwig7 software differently, you need to change the according lines in **both** scripts.

#### Law, Luigi, Six and Enum34
The necessary software for LAW is on one hand loaded as `git submodules` in `Law-Setup/law`, `Law-Setup/luigi` and `Law-Setup/six`. 
These can be loaded by executing 
```bash
git submodule init
git submodule update
```
or setting the submodules while cloning the repository with the  `--recurse-submodules` option.

On the other hand Enum34 is included in `Law-Setup/enum34-1.1.10` as part of the repository and will be cloned as such.


### Running the generation

#### Framework
An HTCondor and file-IO interface for LAW are specified in `Law-Setup/generation/framework.py`. 
There the HTCondor system and the file IO are interfaced to LAW.
LAW also provides support for other file and batch systems, but you need to define these by your own, in case you need it.

#### Tasks and Workflows
Running Herwig7 automatically and distributed on a batch system involves four steps:
First, in a *build* step the necessary matrix elements (MEs) libraries for the hard scattering process are generated and compiled. 
Moreover the handling to the further generation steps is configured and further steps are prepared. This is run locally.
Second, grids for the prepared MEs are *integrate*d for a convergent phase-space integration. 
Since this can be computationally quite expensive, this is distributedly executed on the batch system for a given subprocess splitting.
Third, the splitted integration grids are *merge*d to a single integration grid, which can be used for the last step. This is run locally.
Fourth and last, the fully prepared integration grid is used to *run* the phase-space integration and generate events.

The according code for these tasks and workflows is defined in `Law-Setup/generation/tasks`.

#### Configuration
All important parameters for the execution of the automated generation are set in `Law-Setup/luigi.cfg`. 
Make sure to adjust the following parameters before starting the generation:

*Grid parameters*. In case you want to run the setup on the grid you will need to set the following parameters:
- `wlcg_path`: Since the intermediate and final outputs of the tasks are gathered on a grid storage you will specify here, you need to set the path to your personally reachable one.
- `htcondor_user_proxy`: To establish your identity on the grid, you need to specify your valid VOMS grid proxy.

*HTCondor parameters*. Depending on the configuration of your HTCondor batch system you will need to set the according parameters:
- `htcondor_accounting_group`: In case you have accounting groups configured, make sure to set this to yours.
Set these to a higher value than you expect a single *integrate* or *run* job to run:
- `htcondor_walltime`: This is the (maximum) time your jobs are allowed to run on a batch node. 
- `htcondor_request_memory`: This is the (maximum) amount of memory in MiB your job is allowed to access on the remote node.
- `htcondor_request_disk`: This is the (maximum) number of disk space your job is allowed to occupy.
Additional requirements for selecting worker nodes:
- `htcondor_requirements`: Here you can specify additional requirements on your target machines. 

*Run specific parameters*. Set these to your desired values, to configure your personal generation of events.
- `config_path`: This is the path to the directory, which includes your Herwig inputfile. If not set, this defaults to `inputfiles`
- `input_file_name`: This is the name of your Herwig inputfile **AND** corresponding runfile (this usually needs some configuration in the `saverun` command of your Herwig input file) without the file extensions.
- `mc_setting`: You can set this parameter, if you want to specify further splitting in subdirectories for your outputs for different runs.
- `integration_maxjobs`: With this you specify the splitting of the subprocesses and therefore the number of distinct integration jobs.
- `number_of_jobs`: Set the number of jobs generating MC events with this parameter. Each job will be executed seperately on the batch system.
- `events_per_job`: Overwrite the number of events generated with each generation job.
- `start_seed`: Currently not used. Purposed for the use of randomly generated seeds for generation jobs.

#### Executing LAW
You are now ready to run your configured generation workflow. Set the law environment by `source Law-Setup/setup.sh`.
To index the available LAW tasks and workflows, first execute `law index`, which will also enable autocompletion. 
To start the generation you can now simply run
```
law run HerwigRun
```
This will start all previous steps in the necessary order and produce `.hepmc` files according to your configuration.
Alternatively you can also run each step seperately in the following order,
```
law run HerwigBuild
law run HerwigIntegrate
law run HerwigMerge
law run HerwigRun
```
which will effectively give the same results.
