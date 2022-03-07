# SHERPA: A Python Hyperparameter Optimization Library
SHERPA is a Python library for hyperparameter tuning of machine learning models.

It provides:

 - hyperparameter optimization for machine learning researchers
 - a choice of hyperparameter optimization algorithms
 - parallel computation that can be fitted to the user’s needs
 - a live dashboard for the exploratory analysis of results.

Its goal is to provide a platform in which recent hyperparameter optimization algorithms can be used interchangeably while running on a laptop or a cluster.

If you are looking for the similarly named package “Sherpa” for modelling and fitting data go here: https://parameter-sherpa.readthedocs.io/

## Installation

Clone the repository and install all requirements using `pip install -r requirements.txt` .


## Usage

The code should not be run locally. Use a k8s cluster with argo. \
Furthermore the neccessary "Block" WorkflowTemplates have to exist.

e.g. Working with 3 Templates

 - Sherpa template (executes the sherpa optimization)
   - model_dag template (dag of copy, feature scaling, feature selection, train and evaluation...)
      - template copy
      - tempalte fit and evaluate
      - template feature scaling
      - template feature selection
      - ...

Please note that PBT cannot perturb the number of units, even though the results.csv file displays a perturbation. 

### Input Flags/Arguments

#### --run_name 

Name to identify the optimization run and output path. Further it´s used to enable filtering for subsidiary container in argo.
See output_path for more information
#### --input_path

Path where input files are stored. Only S3 paths are supported at the moment.

#### --output_path

Path where output files will be stored. Only S3 paths are supported at the moment. \
The final storage path for sherpa results will be `Flags.output_path/FLAGS.run_name` and for trial files it will be `Flags.output_path/FLAGS.run_name/Sherpa_trial_id`


#### --default_parameter


Parameter that are neccessary to run the model that will be optimized. 
These parameter include the optimization parameter as well. Insert `tp['Name of the parameter that is used in --hpo_parameter']` for the value. \
Can be parameters like filenames, batch_size, units, callbacks, buffer_size, loss, metrics, optimizer_config... \
When you use a file, save it to the input path. Take a look at `trial_run_paramter.txt` for an example.

1. Pass them as key, value pairs as command line flag:
 - `--default_parameter={"batch_size": tp['batch_size'], "units": str(tp["units_1"])+","+str(tp["units_2"]), "optimizer_config": {"class_name": "adam"}}`
2. or store them in a txt file at the input path and pass the filename (Recommended):
 - `--default_parameter=trial_run_parameter.txt`


#### --hpo_parameter

Hyperparameters are defined via sherpa.Parameter objects. Available are
 - sherpa.Continuous: Represents continuous parameters such as weight-decay multiplier. Can also be thought of as float.
 - sherpa.Discrete: Represents discrete parameters such as number of hidden units in a neural network. Can also be thought of as int.
 - sherpa.Ordinal: Represents categorical ordered parameters. For example minibatch size could be an ordinal parameter taking values 8, 16, 32, etc. Can also be thought of as list.
 - sherpa.Choice: Represents unordered categorical parameters such as activation function in a neural network. Can also be thought of as a set.

Example Parameter.  \
e.g. 
```
{"batch_size": {"type": "Discrete", "range": [8,16,32]}},
{"learning_rate" : {"type":"Continuous","range":[0.01,0.1]}},
{"units_1": {"type": "Discrete", "range": [8,16,32]}},
{"units_2": {"type": "Discrete", "range": [8,16,32]}},


```

[Getting started guide](https://parameter-sherpa.readthedocs.io/en/latest/gettingstarted/guide.html)

#### --algorithm

Choose one of the sherpa optimization algorithm.
 - GridSearch
 - RandomSearch
 - GPyOpt
 - SuccessiveHalving (Not supported yet)
 - LocalSearch
 - PopulationBasedTraining (Not supported yet)

[Sherpa Algorithms](https://parameter-sherpa.readthedocs.io/en/latest/algorithms/algorithms.html)

#### --algo_parameter      

Parameters for the shepra optimization algorithm which should match to the algorithm set through the FLAG "algorithm"
 - [GridSearch](https://parameter-sherpa.readthedocs.io/en/latest/algorithms/algorithms.html#grid-search)
 - [RandomSearch](https://parameter-sherpa.readthedocs.io/en/latest/algorithms/algorithms.html#random-search)
 - [GPyOpt](https://parameter-sherpa.readthedocs.io/en/latest/algorithms/algorithms.html#bayesian-optimization-with-gpyopt)
 - [SuccessiveHalving](https://parameter-sherpa.readthedocs.io/en/latest/algorithms/algorithms.html#asynchronous-successive-halving-aka-hyperband)
 - [LocalSearch](https://parameter-sherpa.readthedocs.io/en/latest/algorithms/algorithms.html#local-search)
 - [PopulationBasedTraining](https://parameter-sherpa.readthedocs.io/en/latest/algorithms/algorithms.html#population-based-training)

#### --objective

During training send_metrics is used every iteration to return objective values (only one metric as objectiv) to SHERPA. \
Objective is the name of the metric or loss which the model will use to train. \
It has the be equal to the name inside the metrics_file. \

e.g. `--objective=mean_squared_error`

#### --filename_objective

Filename of the file which includes the objective/metrics. \
The objective with the relating metrics will be downloaded from s3 storage after a job has succeded.


#### --lower_is_better

Whether lower objective values are better. \
True = lower is better \
Defaults to True.

#### --workflowtemplate

Define which Argo Workflowtemplate to use as the trial execution. Workflowtemplate should include train and evaluate (and sometimes copy)

#### --entrypoint

Define the entrypoint from the Argo Workflowtemplate. e.g. fit 

#### --max_concurrent

The number of trials that will be trained/evaluated in parallel.

#### --resubmit_failed_trials

Whether to resubmit a trial if it has failed.

#### --verbose

Whether to print submit messages.
True = print submit messages

#### --storage_strategy

Choose one of the following.
 - keep
 - delete
 - best

Wether to keep all files, delete all files, keep the files with the best result. \
Storage strategy inscribed only files which are created by the trial runs. \
The study_results.csv, study_config.pkcl and best_result.json will be stored in any case. 

#### --argo_ip

Argo server ip of the kubernetes cluster for the api requests.


#### --argo_port

Argo server port of the kubernetes cluster for the api requests.

#### --k8_namespace

Name of the kubernetes namespace where the trial containers should be executed.

## Example

The example files are not coordinated to execute an example run. Rather to provide some guidance for own usecases.
The flag.txt includes and example of input arguments for the argo sherpa template. \
`template_sherpa.yaml` is the execution template which runs the shera algorithm and scheduler. \
`dag_hpo_trial_run.yaml` is an example for a trial template which includes multiple steps.
The model files will be saved to the trial input path aswell.

## Data Set

The data set was recorded with the help of the Festo Polymer GmbH. The features (`x.csv`) are either parameters explicitly set on the injection molding machine or recorded sensor values. The target value (`y.csv`) is a crucial length measured on the parts. We measured with a high precision coordinate-measuring machine at the Laboratory for Machine Tools (WZL) at RWTH Aachen University.
