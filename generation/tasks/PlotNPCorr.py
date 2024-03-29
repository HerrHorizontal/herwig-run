
import luigi, law
from luigi.util import inherits
import os
import json

from subprocess import PIPE
from generation.framework.utils import run_command, rivet_env
from generation.framework.config import MCCHAIN_SCENARIO_LABELS, BINS, JETS

from generation.framework.tasks import Task, CommonConfig

from RivetMerge import RivetMerge
from DeriveNPCorr import DeriveNPCorr


@inherits(CommonConfig)
class PlotNPCorr(Task, law.LocalWorkflow):
    """
    Plotting class for NP-correction factor plots using the YODA API
    """

    # configuration variables
    mc_setting_full = luigi.Parameter(
        default="withNP",
        description="Scenario identifier for the full MC production, typically `withNP`. \
                Used to identify the output-paths for the full generation scenario."
    )
    mc_setting_partial = luigi.Parameter(
        default="NPoff",
        description="Scenario identifier for the partial MC production, typically `NPoff`, `MPIoff` or `Hadoff`. \
                Used to identify the output-paths for the partial generation scenario, \
                where parts of the generation chain are turned off."
    )
    match = luigi.Parameter(
        # significant=False,
        default=None,
        description="Require presence of analysis objects which names match this regex in the YODA files."
    )
    unmatch = luigi.Parameter(
        # significant=False,
        default=None,
        description="Require exclusion of analysis objects which names match this regex in the YODA files."
    )
    filter_label_pad_tuples = luigi.TupleParameter(
        default=((".*","","Observable","NP corr.","arb. units"),),
        description="Tuple of tuples containing four or five strings:\n \
            - the filter for identification of the analysis objects to plot, match and unmatch, \n\
            - the x- and y-axis labels for the ratio pad (showing i.e. the NP-correction), \n\
            - OPTIONAL: the label for a top pad showing the original distributions used to derive the ratio \n\
            ((\"match\", \"unmatch\", \"xlabel\", \"ylabel\", [\"origin-ylabel\"]), (...), ...)"
    )
    yrange = luigi.TupleParameter(
        default=[0.8,1.3],
        significant=False,
        description="Value range for the y-axis of the ratio plot."
    )

    exclude_params_req = {
        "source_script",
        "mc_setting_full",
        "mc_setting_partial",
        "filter_label_pad_dicts"
    }


    def workflow_requires(self):
        req = super(PlotNPCorr, self).workflow_requires()
        req["full"] = RivetMerge.req(
            self, 
            mc_setting = self.mc_setting_full
        )
        req["partial"] = RivetMerge.req(
            self,
            mc_setting = self.mc_setting_partial
        )
        req["ratio"] = DeriveNPCorr.req(
            self,
            mc_setting_full = self.mc_setting_full,
            mc_setting_partial = self.mc_setting_partial,
            match = self.match,
            unmatch = self.unmatch
        )
        return req


    def create_branch_map(self):
        bm = dict()
        for jobid, flp in enumerate(self.filter_label_pad_tuples):
            try:
                match, unmatch, xlabel, ylabel = flp
                bm[jobid] = dict(match=match, unmatch=unmatch, xlabel=xlabel, ylabel=ylabel)
            except ValueError as e:
                print("Acounted {}, trying with origin-y-label".format(e))
                match, unmatch, xlabel, ylabel, oylabel = flp
                bm[jobid] = dict(match=match, unmatch=unmatch, xlabel=xlabel, ylabel=ylabel, oylabel=oylabel)
        return bm

    
    def requires(self):
        req = dict()
        req["full"] = RivetMerge.req(
            self, 
            mc_setting = self.mc_setting_full
        )
        req["partial"] = RivetMerge.req(
            self,
            mc_setting = self.mc_setting_partial
        )
        req["ratio"] = DeriveNPCorr.req(
            self,
            mc_setting_full = self.mc_setting_full,
            mc_setting_partial = self.mc_setting_partial,
            match = self.match,
            unmatch = self.unmatch
        )
        return req


    def output(self):
        out = dict()
        out["single"] = self.local_target(
            "{full}-{partial}-Ratio-Plots/m-{match}-um-{unmatch}/single/".format(
                full = self.mc_setting_full,
                partial = self.mc_setting_partial,
                match=self.branch_data["match"],
                unmatch=self.branch_data["unmatch"]
            )
        )
        out["summary"] = self.local_target(
            "{full}-{partial}-Ratio-Plots/m-{match}-um-{unmatch}/summary/".format(
                full = self.mc_setting_full,
                partial = self.mc_setting_partial,
                match=self.branch_data["match"],
                unmatch=self.branch_data["unmatch"]
            )
        )
        return out


    def run(self):
        # ensure that the output directory exists
        outputs = self.output()
        for output in outputs.values():
            try:
                output.parent.touch()
            except IOError:
                print("Output target {} doesn't exist!".format(output.parent))
                output.makedirs()

        if len(self.yrange) != 2:
            raise ValueError("Argument --yrange takes exactly two values, but {} given!".format(len(self.yrange)))

        # actual payload:
        print("=======================================================")
        print("Starting NP-factor plotting with YODA")
        print("=======================================================")

        # localize the separate YODA files on grid storage
        print("Inputs: {}".format(self.input()))
        with self.input()["full"].localize('r') as _file:
            print("\tfull: {}".format(_file.path))
            input_yoda_file_full = _file.path
        with self.input()["partial"].localize('r') as _file:
            print("\tpartial: {}".format(_file.path))
            input_yoda_file_partial = _file.path
        with self.input()["ratio"].localize('r') as _file:
            print("\tratio: {}".format(_file.path))
            input_yoda_file_ratio = _file.path

        # assign paths for output YODA file and plots
        plot_dir_single = outputs["single"].parent.path
        plot_dir_summary = outputs["summary"].parent.path

        # execute the script deriving the NP correction plots and files
        executable = [
            "python", os.path.expandvars("$ANALYSIS_PATH/scripts/yodaPlotNPCorr.py"),
            "--full", "{}".format(input_yoda_file_full),
            "--partial", "{}".format(input_yoda_file_partial),
            "--ratio", "{}".format(input_yoda_file_ratio),
            "--plot-dir", "{}".format(plot_dir_single),
            "--yrange", "{}".format(self.yrange[0]), "{}".format(self.yrange[1]),
            "--splittings", "{}".format(json.dumps(BINS["all"])),
            "--full-label", "{}".format(MCCHAIN_SCENARIO_LABELS.get(self.mc_setting_full, self.mc_setting_full)),
            "--partial-label", "{}".format(MCCHAIN_SCENARIO_LABELS.get(self.mc_setting_partial, self.mc_setting_partial))
        ]
        executable += ["--match", "{}".format(self.branch_data["match"])] if self.branch_data["match"] else []
        executable += ["--unmatch", "{}".format(self.branch_data["unmatch"])] if self.branch_data["unmatch"] else []
        executable += ["--xlabel", "{}".format(self.branch_data["xlabel"])] if self.branch_data["xlabel"] else []
        executable += ["--ylabel", "{}".format(self.branch_data["ylabel"])] if self.branch_data["ylabel"] else []
        executable += ["--origin", "--origin-ylabel", "{}".format(self.branch_data["oylabel"])] if self.branch_data.get("oylabel", None) else []

        print("Executable: {}".format(" ".join(executable)))

        try:
            run_command(executable, env=rivet_env, cwd=os.path.expandvars("$ANALYSIS_PATH"))
        except RuntimeError as e:
            print("Individual bins' plots creation failed!")
            output["single"].remove()
            raise e
        
        if not os.listdir(plot_dir_single):
            output.remove()
            raise LookupError("Plot directory {} is empty!".format(plot_dir_single))

        print("=======================================================")
        print("Starting NP-factor summary plotting with YODA")
        print("=======================================================")

        # plot also summary plots
        executable_summary = [
            "python", os.path.expandvars("$ANALYSIS_PATH/scripts/yodaPlotNPCorrSummary.py"),
            "--ratio", "{}".format(input_yoda_file_ratio),
            "--plot-dir", "{}".format(plot_dir_summary),
            "--yrange", "{}".format(self.yrange[0]), "{}".format(self.yrange[1]),
            "--splittings", "{}".format(json.dumps(dict(YS0=BINS["YS0"],YB0=BINS["YB0"],YSYBAll=BINS["all"]))),
            "--jets", "{}".format(json.dumps(JETS)),
            "--full-label", "{}".format(MCCHAIN_SCENARIO_LABELS.get(self.mc_setting_full, self.mc_setting_full)),
            "--partial-label", "{}".format(MCCHAIN_SCENARIO_LABELS.get(self.mc_setting_partial, self.mc_setting_partial))
        ]
        executable_summary += ["--match", "{}".format(self.branch_data["match"])] if self.branch_data["match"] else []
        executable_summary += ["--unmatch", "{}".format(self.branch_data["unmatch"])] if self.branch_data["unmatch"] else []
        executable_summary += ["--xlabel", "{}".format(self.branch_data["xlabel"])] if self.branch_data["xlabel"] else []
        executable_summary += ["--ylabel", "{}".format(self.branch_data["ylabel"])] if self.branch_data["ylabel"] else []

        print("Executable: {}".format(" ".join(executable_summary)))

        try:
            run_command(executable_summary, env=rivet_env, cwd=os.path.expandvars("$ANALYSIS_PATH"))
        except RuntimeError as e:
            print("Summary plots creation failed!")
            output.remove()
            raise e
        
        if not os.listdir(plot_dir_summary):
            output.remove()
            raise LookupError("Plot directory {} is empty!".format(plot_dir_summary))

        print("-------------------------------------------------------")
