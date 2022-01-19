#!/usr/bin/env python

import pathlib # for a join
import shutil
import os
from functools import partial  # for setting Run_Number. In Jonathan Future World, Run_Number is set by dtk_pre_proc based on generic param_sweep_value...

# idmtools ...
from idmtools.assets import Asset, AssetCollection  #
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools_models.templated_script_task import get_script_wrapper_unix_task

# emodpy
from emodpy.emod_task import EMODTask
import emodpy.emod_task as emod_task
from emodpy.utils import EradicationBambooBuilds
from emodpy.bamboo import get_model_files
from emodpy_tbhiv.reporters.plugin import Report_TBHIV_ByAge

import params
import set_config
import manifest

# ****************************************************************
# Features to support:
#
#  Read experiment info from a json file
#  Add Eradication.exe as an asset (Experiment level)
#  Add Custom file as an asset (Simulation level)
#  Add the local asset directory to the task
#  Use builder to sweep simulations
#  How to run dtk_pre_process.py as pre-process
#  Save experiment info to file
# ****************************************************************

def update_sim_bic(simulation, value):
    simulation.task.config.parameters.Base_Infectivity_Constant  = value*0.1
    return {"Base_Infectivity": value}

def update_sim_random_seed(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}


def print_params():
    """
    Just a useful convenience function for the user.
    """
    # Display exp_name and nSims
    # TBD: Just loop through them
    print("exp_name: ", params.exp_name)
    print("nSims: ", params.nSims)

def set_param_fn(config): 
    """
    This function is a callback that is passed to emod-api.config to set parameters The Right Way.
    """
    config = set_config.set_config( config )

    config.parameters.x_Other_Mortality =  0.34
    config.parameters.x_Birth =  1.43

    config.parameters.TB_MDR_Fitness_Multiplier =  1.0 #no fitness cost worst case

    #config.parameters.Simulation_Duration =  params.burn_initial + params.burn_predots + params.To_end_from_DOTS
    config.parameters.Simulation_Duration =  3650
    config.parameters.TB_Smear_Negative_Infectivity_Multiplier = 0.34604
    config.parameters.TB_Presymptomatic_Rate = 0.01165
    config.parameters.TB_Active_Presymptomatic_Infectivity_Multiplier = 0.34604*0.3318

    #config.parameters.Base_Population_Scale_Factor =  1000
    config.parameters.TB_Slow_Progressor_Rate =  0.007/365.0
    #config.parameters.Serialization_Times = [ 365 ]
    config.parameters.pop( "Serialized_Population_Filenames" )

    config.parameters.Report_Event_Recorder_Events = ["TBActivationPresymptomatic","Hello","Oh_No_I_Have_HIV","Yay"]
    config.parameters["logLevel_Individual"] = "INFO"

    return config

def build_camp():
    """
    Build a campaign input file for the DTK using emod_api.
    Right now this function creates the file and returns the filename. If calling code just needs an asset that's fine.
    """
    import emod_api.campaign as camp
    import emod_api.interventions.outbreak as ob
    import emod_api.interventions.utils as utils
    import emodpy_tbhiv as tbhiv
    import emodpy_tbhiv.interventions.art as art
    import emodpy_tbhiv.interventions.bcg as bcg
    import emodpy_tbhiv.interventions.active_diagnostic as ad
    import emodpy_tbhiv.interventions.hiv_diag as hd

    # This isn't desirable. Need to think about right way to provide schema (once)
    camp.schema_path = manifest.schema_file
    
    #print( f"Telling emod-api to use {manifest.schema_file} as schema." )
    
    # importation pressure
    from emodpy_tbhiv.interventions import purge_campaign_event
    seed = ob.seed_by_coverage( camp, 40, 0.5 )
    purge_campaign_event( seed )
    camp.add( seed, first=True )

    camp.add( art.ART( camp, ["TBActivationPresymptomatic"], start_day=10 ) )
    camp.add( bcg.BCG( camp, ["TBActivationPresymptomatic"], start_day=10 ) )
    camp.add( ad.ActiveDiagnostic( camp, ["TBActivationPresymptomatic"], start_day=1, pos_event="Hello" ) )
    camp.add( hd.HIVDiagnostic( camp, ["TBActivationPresymptomatic"], start_day=1, pos_event="Oh_No_I_Have_HIV", neg_event="Yay" ) )
    return camp


def build_demog():
    """
    Build a demographics input file for the DTK using emod_api.
    Right now this function creates the file and returns the filename. If calling code just needs an asset that's fine.
    Also right now this function takes care of the config updates that are required as a result of specific demog settings. We do NOT want the emodpy-disease developers to have to know that. It needs to be done automatically in emod-api as much as possible.
    TBD: Pass the config (or a 'pointer' thereto) to the demog functions or to the demog class/module.

    """
    import emodpy_tbhiv.demographics.TBHIVDemographics as Demographics # OK to call into emod-api
    import emod_api.demographics.DemographicsTemplates as DT

    demog = Demographics.fromData( pop=10000, filename_male=manifest.males, filename_female=manifest.females )
    
    return demog

def ep4_fn(task):
    task = emod_task.add_ep4_from_path(task, manifest.ep4_dir)
    return task

def run_test( erad_path ):
    """
    This function is designed to be a parameterized version of the sequence of things we do 
    every time we run an emod experiment. 
    """
    print_params()

    # Create a platform
    # Show how to dynamically set priority and node_group
    platform = Platform("SLURM", node_group="idm_48cores", priority="Highest")

    #pl = RequirementsToAssetCollection( platform, requirements_path=manifest.requirements )

    # create EMODTask 
    print("Creating EMODTask (from files)...")
    report = Report_TBHIV_ByAge()
    report.configure_report(200, 0, 0, 200, ["HappyBirthday","Hello","Oh_No_I_Have_HIV", "Yay", "ArtDistributed", "BcgDistributed"])
    
    report.asset_dir = manifest.plugins_folder

    task = EMODTask.from_default2(
            config_path="my_config.json",
            eradication_path=None, # manifest.eradication_path,
            campaign_builder=build_camp,
            schema_path=manifest.schema_file,
            param_custom_cb=set_param_fn,
            ep4_custom_cb=ep4_fn,
            demog_builder=build_demog,
            plugin_report=report
        )

    #demog_path = build_demog()
    #task.common_assets.add_asset( demog_path )

    print("Adding asset dir...")
    task.common_assets.add_directory(assets_directory=manifest.assets_input_dir)

    task.set_sif( manifest.sif )
    # Set task.campaign to None to not send any campaign to comps since we are going to override it later with
    # dtk-pre-process.
    print("Adding local assets (py scripts mainly)...")

    # Create simulation sweep with builder
    builder = SimulationBuilder()
    builder.add_sweep_definition( update_sim_random_seed, range(params.nSims) )

    # create experiment from builder
    print( f"Prompting for COMPS creds if necessary..." )
    experiment  = Experiment.from_builder(builder, task, name=params.exp_name) 

    #other_assets = AssetCollection.from_id(pl.run())
    #experiment.assets.add_assets(other_assets)

    # The last step is to call run() on the ExperimentManager to run the simulations.
    experiment.run(wait_until_done=True, platform=platform)

    # Check result
    if not experiment.succeeded:
        print(f"Experiment {experiment.uid} failed.\n")
        exit()

    print(f"Experiment {experiment.uid} succeeded.")

    # Save experiment id to file
    with open("COMPS_ID", "w") as fd:
        fd.write(experiment.uid.hex)
    print()
    print(experiment.uid.hex) 
    


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # parser.add_argument('-v', '--use_vpn', action='store_true',
    #                     help='get model files from Bamboo(needs VPN)')
    parser.add_argument('-v', '--use_vpn', type=str, default='No', choices=['No', "Yes"],
                        help='get model files from Bamboo(needs VPN) or Pip installation(No VPN)')
    args = parser.parse_args()
    if args.use_vpn.lower() == "yes":
        plan = EradicationBambooBuilds.TBHIV
        get_model_files( plan, manifest, False )
    else:
        import emod_tbhiv.bootstrap as dtk
        dtk.setup(pathlib.Path(manifest.eradication_path).parent)

    run_test( manifest.eradication_path )
