# Copyright (c) 2022 RWTH Aachen - Werkzeugmaschinenlabor (WZL)
# Contact: Simon Cramer, s.cramer@wzl-mq.rwth-aachen.de

import sherpa 
from sherpa.core import AlgorithmState
import pandas 

class PopulationBasedTraining(sherpa.algorithms.PopulationBasedTraining):
    """
    Extension of Sherpa's Population Based Training (PBT) algorithm as introduced by Jaderberg et al. 2017, to function properly
    in parallel.
    """
    def get_suggestion(self, parameters, results, lower_is_better):
        """
        Extension of Sherpa's implementation in lines 18-20:
        Wait for current generaton to finish, before submitting new trials to the next generation.
        """
        self.count += 1
        self.generation = (self.count - 1)//self.population_size + 1

        if not results.empty and len(results.query("Status == 'COMPLETED'")) < (self.generation-1) * self.population_size:
            self.count -= 1
            return AlgorithmState.WAIT


        if self.generation == 1:
            trial = self.random_sampler.get_suggestion(parameters,
                                                       results, lower_is_better)
            trial['lineage'] = ''
            trial['load_from'] = ''
            trial['save_to'] = str(self.count)
        elif self.generation > self.num_generations:
            return AlgorithmState.DONE
        else:
            trial = self._truncation_selection(parameters=parameters,
                                               results=results,
                                               lower_is_better=lower_is_better)
            trial['load_from'] = str(int(trial['save_to']))
            trial['save_to'] = str(int(self.count))
            trial['lineage'] += trial['load_from'] + ','
        trial['generation'] = self.generation
        return trial
