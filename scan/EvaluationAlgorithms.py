'''
Created on Sep 23, 2014

@author: pmaunz
'''

from CountEvaluation import MeanEvaluation, ThresholdEvaluation, RangeEvaluation, DoubleRangeEvaluation
from CountEvaluation import NumberEvaluation, FidelityEvaluation, ParityEvaluation, TwoIonEvaluation
from CountEvaluation import FeedbackEvaluation
from scan.FitHistogramsEvaluation import FitHistogramEvaluation

EvaluationAlgorithms = { MeanEvaluation.name: MeanEvaluation, 
                         ThresholdEvaluation.name: ThresholdEvaluation,
                         RangeEvaluation.name: RangeEvaluation,
                         DoubleRangeEvaluation.name: DoubleRangeEvaluation,
                         NumberEvaluation.name: NumberEvaluation,
                         FidelityEvaluation.name: FidelityEvaluation,
                         ParityEvaluation.name: ParityEvaluation,
                         TwoIonEvaluation.name: TwoIonEvaluation,
                         FitHistogramEvaluation.name: FitHistogramEvaluation,
                         FeedbackEvaluation.name: FeedbackEvaluation }
