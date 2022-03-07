# Copyright (c) 2022 RWTH Aachen - Werkzeugmaschinenlabor (WZL)
# Contact: Simon Cramer, s.cramer@wzl-mq.rwth-aachen.de

from absl import logging
import sherpa
from s3_smart_open import to_s3, to_json
from argo_scheduler import ArgoScheduler
from population_based_training import PopulationBasedTraining
import os

def create_hpo_parameter(hpo_p,algorithm):
    """Creates a list with sherpa hyper parameter

    Args:
        hpo_tuple (tuple[dicts]): Tuple that includes all hp for the optimization on their 'real' position. 
        Example: ({'epochs':{'type':...}},{'optimizer_config': 'config': {'learning_rate':{'type':...}}},{'optimzer_config': {'class': {'type': ...,'range':..}}})

    Returns:
        hpo_parameter [list]: Sherpa Hyper Parameter
        storage_for_rebuild [dict]: key value pairs in order to merge the hp into the parameter which will be submitted with the argo workflow
    """
    hpo_parameter = []

    for key, val in hpo_p.items():

        if 'type' in val:
            sherpa_parameter = None
            if val['type'] == 'Continuous':
                if 'scale' in val:
                    sherpa_parameter = sherpa.Continuous(name=key, range=val['range'], scale=val['scale'])
                else: 
                    sherpa_parameter = sherpa.Continuous(name=key, range=val['range'])

            elif val['type'] == 'Ordinal':
                sherpa_parameter = sherpa.Ordinal(name=key, range=val['range'])

            elif val['type'] == 'Discrete':
                if 'scale' in val:
                    if algorithm == 'GPyOpt':
                        assert val['scale'] != 'log',  'GPyOpt does not accept Discrete variables with the option scale=log for Parameter {}'.format(key)
                    else:
                        sherpa_parameter = sherpa.Discrete(name=key, range=val['range'], scale=val['scale'])
                else: 
                    sherpa_parameter = sherpa.Discrete(name=key, range=val['range'])

            elif val['type'] == 'Choice':
                sherpa_parameter = sherpa.Choice(name=key, range=val['range'])

            else:
                logging.warning('No Sherpa parameter type was defined for parameter {}'.format(key))
                    
            if sherpa_parameter != None:
                hpo_parameter.append(sherpa_parameter)

        else:
            logging.warning('HPO parameter {} has no key: type '.format(key))
    
    logging.info('Returning following Parameter for HPO:')
    for p in hpo_parameter:
        logging.info(p.name)
    return hpo_parameter


def run_hpo(run_name,default_parameter,trial_run_parameter,hpo_parameter,algorithm,storage_strategy,objective,filename_objective,verbose,lower_is_better,max_concurrent,command,output_path,algo_arguments,argo_ip,argo_port,k8_namespace):
    """Runs a hyper parameter optimization in parallel mode with argo

    Args:
        run_name (str): Name to identify the optimization run and output path. Further it´s used to enable filtering for subsidiary container in argo 
        default_parameter (dict): Parameter that will be submitted with the argo workflow in a kind of input flags.
        hpo_parameter (tuple[dicts]): Tuple that includes all hp for the optimization on their 'real' position. 
        algorithm (str): Name of sherpa optimization algorithm
        storage_strategy (str): What to do with trial files. Wether to keep all files, delete all files or keep the files from the best opimization run.
        objective (str): Name of the objective that will be optimized for. Must be a key/name from the metrics that were generated within a trial run.
        filename_objective (str): Filename of the file that contains the objective value which was created within a trial run.
        verbose (int): whether to print submit messages. 1 = True, 0 = False
        lower_is_better (bool): whether to minimize or maximize the objective
        max_concurrent (int): The number of trials that will be evaluated in parallel
        command (list[str]): command (list[str]): List that contains ['Argo WorkflowTemplate','Entrypoint of that Argo WorkflowTemplate]
        output_path (str): S3 storage Path where results will be saved and trial files will be stored
        algo_arguments (dict): Arguments for sherpa optimization alogrithm
        argo_ip (str): Argo server ip
        argp_port (str): Argo server port
        k8_namespace (str): Name of the kubernetes namespace where the trial container should be executed.

    Raises:
        Exception: GPyOpt does not accept Discrete variables with the option scale=log for Parameter. 

    Returns:
        [dict]: Configuration of the best trial run.
    """    
    hpo_parameters = create_hpo_parameter(hpo_parameter,algorithm)
    
    if algorithm != None:
        if algorithm == 'GridSearch':
            alg = sherpa.algorithms.GridSearch(**algo_arguments)

        elif algorithm == 'RandomSearch':
            alg = sherpa.algorithms.RandomSearch(**algo_arguments)

        elif algorithm == 'GPyOpt':
            
            if 'max_concurrent' in algo_arguments:
                algo_arguments['max_concurrent']= max_concurrent
                logging.warning('Algorithm parameter was set to max_concurrent.')
            else:
                algo_arguments['max_concurrent']= max_concurrent
            alg = sherpa.algorithms.GPyOpt(**algo_arguments)
        
        elif algorithm == 'SuccessiveHalving':
            alg = sherpa.algorithms.SuccessiveHalving(**algo_arguments)

        elif algorithm == 'LocalSearch':
            if 'seed_configuration' not in algo_arguments:
                raise Exception('No seed configuartion provided. Please provide parameters to start with.')

            alg = sherpa.algorithms.LocalSearch(**algo_arguments)

        elif algorithm == 'PopulationBasedTraining':
            alg = PopulationBasedTraining(**algo_arguments)

    logging.info('---------- Started optimization ----------')
    
    output_dir = './data'
    os.makedirs(output_dir, exist_ok=True)
    port = 27017
    os.environ['SHERPA_DB_HOST'] = "127.0.0.1"
    os.environ['SHERPA_DB_PORT'] = str(port)
    os.environ['SHERPA_OUTPUT_DIR'] = output_dir
    scheduler = ArgoScheduler(default_parameter,trial_run_parameter,lower_is_better,objective,filename_objective,argo_ip,argo_port,k8_namespace,storage_strategy)
    study = sherpa.optimize(parameters=hpo_parameters,
                       algorithm=alg,
                       lower_is_better=lower_is_better,  
                       command=command,
                       max_concurrent=max_concurrent,
                       verbose=verbose,
                       output_dir=output_dir,
                       scheduler=scheduler,
                       mongodb_args={"port":str(port)},
                       db_port=int(port)
                       )
    
    logging.info('Best results : {}'.format(study))

    # Numpy data types cant be serialized 
    for k, v in study.items():
        study[k] = str(v)

    if os.path.exists(os.path.join(output_dir,'config.pkl')):
        to_s3(output_path,'config.pkl',os.path.join(output_dir,'config.pkl'))
    if os.path.exists(os.path.join(output_dir,'results.csv')):
        to_s3(output_path,'results.csv',os.path.join(output_dir,'results.csv'))
    to_json(output_path,'best_result.json',study)
