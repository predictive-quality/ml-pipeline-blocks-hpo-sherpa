# Copyright (c) 2022 RWTH Aachen - Werkzeugmaschinenlabor (WZL)
# Contact: Simon Cramer, s.cramer@wzl-mq.rwth-aachen.de

from absl import flags, app, logging
import json
import socket
from s3_smart_open import read_txt, to_json
from runner import run_hpo
import os

flags.DEFINE_string('run_name',None,'Name to identify the optimization run and output path. Further it´s used to enable filtering for subsidiary container in argo.')
flags.DEFINE_string('input_path',None,'Path where input files are stored')
flags.DEFINE_string('output_path',None,'Path where output files will be stored')
flags.DEFINE_string('default_parameter',None,'Parameter that are neccessary to run the model that will be optimized or a flagfile which includes these parameters.')
flags.DEFINE_string('hpo_parameter',None,'Optimization Parameter')
flags.DEFINE_enum('algorithm',None,['GridSearch','RandomSearch','GPyOpt','SuccessiveHalving','LocalSearch','PopulationBasedTraining'],'Sherpa Algorithm for the optimization.')
flags.DEFINE_string('algo_parameter',None,'Parameters for the HPO algorithm which should match to the algorithm set though the FLAG "algorithm" ')
flags.DEFINE_string('objective',None,'During training send_metrics is used every iteration to return objective values (only one metric as objectiv) to SHERPA.')
flags.DEFINE_string('filename_objective',None,'Filename of the json-file that contains the objective value which was created within a trial run. e.g model_xy_metrics.json')
flags.DEFINE_boolean('lower_is_better',True,'Whether lower objective values are better')
flags.DEFINE_string('workflowtemplate',None,'Define which Argo Workflowtemplate to use as the trail execution. Workflowtemplate should include train and evaluate')
flags.DEFINE_string('entrypoint',None,'Define the entrypoint from the Argo Workflowtemplate. e.g. fit ')
flags.DEFINE_integer('max_concurrent',1,'The number of trials that will be evaluated in parallel')
flags.DEFINE_boolean('resubmit_failed_trials',False,' Whether to resubmit a trial if it failed')
flags.DEFINE_boolean('verbose',True,'Whether to print submit messages')
flags.DEFINE_enum('storage_strategy','keep',['keep','delete','best','continue'],'Keep all Model files in s3 storage. Delete all files. Keep the files with the best result. Keep the files required for continuing training.')
flags.DEFINE_string('argo_ip','134.130.7.172','Argo server ip of the kubernetes cluster for the api requests.')
flags.DEFINE_string('argo_port','32529','Argo server port of the kubernetes cluster for the api requests.')
flags.DEFINE_string('k8_namespace','orakel','Name of the kubernetes namespace where the trial containers should be executed')



flags.mark_flag_as_required('input_path')
flags.mark_flag_as_required('output_path')
flags.mark_flag_as_required('algorithm')
flags.mark_flag_as_required('objective')
flags.mark_flag_as_required('filename_objective')
flags.mark_flag_as_required('workflowtemplate')
flags.mark_flag_as_required('entrypoint')

FLAGS = flags.FLAGS

def main(argv):
    """Run sherpa hp optimization with argo workflows

    """

    del argv
    # eval parameter and add further default parameter

    if FLAGS.default_parameter.endswith('.txt'):
        trial_run_parameter = read_txt(FLAGS.input_path,FLAGS.default_parameter)
    else:
        trial_run_parameter = FLAGS.default_parameter
       
    algo_parameter = eval(FLAGS.algo_parameter)
    hpo_parameter = eval(FLAGS.hpo_parameter)
    
    command = FLAGS.workflowtemplate + ' ' + FLAGS.entrypoint

    # Set run_name = container name / Argo workflow name when not given in order to extend the output path 
    if not FLAGS.run_name:
        run_name = socket.gethostname()
    else:
        run_name = FLAGS.run_name

    default_parameter = {}
    default_parameter['run_name'] = run_name
    default_parameter['input_path'] = FLAGS.input_path 
    default_parameter['output_path'] = os.path.join(FLAGS.output_path,run_name)
    to_json(default_parameter['output_path'],'optimization_parameters.json',hpo_parameter)


    verbose = int(FLAGS.verbose)

    run_hpo(run_name=FLAGS.run_name,
            default_parameter=default_parameter,
            trial_run_parameter=trial_run_parameter,
            hpo_parameter=hpo_parameter,
            algorithm=FLAGS.algorithm,
            storage_strategy=FLAGS.storage_strategy,
            max_concurrent=FLAGS.max_concurrent,
            command=command,
            verbose=verbose,
            lower_is_better=FLAGS.lower_is_better,
            output_path=default_parameter['output_path'],
            algo_arguments=algo_parameter,
            objective=FLAGS.objective,
            filename_objective=FLAGS.filename_objective,
            argo_ip=FLAGS.argo_ip,
            argo_port=FLAGS.argo_port,
            k8_namespace=FLAGS.k8_namespace)


if __name__ == '__main__':
    app.run(main) 
