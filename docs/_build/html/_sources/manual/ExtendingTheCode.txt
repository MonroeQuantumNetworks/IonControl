.. include:: inlineImages.include

.. _ExtendingTheCode:

Extending the Code
==================

Adding Hardware
---------------

External Parameters
~~~~~~~~~~~~~~~~~~~

Voltage Controllers
~~~~~~~~~~~~~~~~~~~

AWGs
~~~~

Adding Evaluations
------------------

The evaluations are defined in \IonControl\scan\CountEvaluation.py, and listed in \IonControl\scan\EvaluationAlgorithms.py. Each evaluation is a class which inherits from EvaluationBase, and is listed in EvaluationAlgorthms.py. An evaluation class must provide:

   - A name
   - A tooltip
   - Any settings that define the evaluation, and their type (defined in the method "children")
   - the method "evaluate" that takes in the data, and returns a 3-tuple:

      (evaluated value, (upper error bar size, lower error bar size), raw value)

      Raw value is typically the value not scaled by the number of experiments, i.e. if 100 experiments were performed and in 43 of them the ion is bright, the evaluated value would be 0.43 and the raw value would be 43.

Here is a relatively simple example:

.. code-block:: Python

    class ThresholdEvaluation(EvaluationBase):
        """
        simple threshold state detection: if more than threshold counts are observed
        the ion is considered bright. For threshold photons or less it is considered
        dark.
        """
        name = "Threshold"
        tooltip = "Above threshold is bright"
        def __init__(self,settings=None):
            EvaluationBase.__init__(self,settings)

        def setDefault(self):
            self.settings.setdefault('threshold',1)
            self.settings.setdefault('invert',False)

        def evaluate(self, data, evaluation, expected=None, ppDict=None, globalDict=None ):
            countarray = evaluation.getChannelData(data)
            if not countarray:
                return 0, None, 0
            N = float(len(countarray))
            if self.settings['invert']:
                discriminated = [ 0 if count > self.settings['threshold'] else 1 for count in countarray ]
            else:
                discriminated = [ 1 if count > self.settings['threshold'] else 0 for count in countarray ]
            if evaluation.name:
                data.evaluated[evaluation.name] = discriminated
            x = numpy.sum( discriminated )
            p = x/N
            # Wilson score interval with continuity correction
            # see http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
            rootp = 3-1/N -4*p+4*N*(1-p)*p
            top = min( 1, (2 + 2*N*p + math.sqrt(rootp))/(2*(N+1)) ) if rootp>=0 else 1
            rootb = -1-1/N +4*p+4*N*(1-p)*p
            bottom = max( 0, (2*N*p - math.sqrt(rootb))/(2*(N+1)) ) if rootb>=0 else 0
            return p, (p-bottom, top-p), x

        def children(self):
            return [{'name':'threshold','type':'int','value':self.settings['threshold']},
                    {'name':'invert', 'type': 'bool', 'value':self.settings['invert'] }]


Adding Fits
-----------

The fits are defined in \IonControl\fit\FitFunctions.py. Each fit is a class which inherits from FitFunctionBase. At a bare minimum, the fit must provide:

    - a name
    - a function string to display
    - a list of parameters
    - default values
    - the method "functionEval" which defines how to evaluate the function.

Here is a minimal example:

.. code-block:: Python

    class SinSqGaussFit(FitFunctionBase):
        name = "Sin2 Gaussian Decay"
        functionString =  'A * exp(-x^2/tau^2) * sin^2(pi/(2*T)*x+theta) + O'
        parameterNames = [ 'A', 'T', 'theta', 'O', 'tau' ]
        def __init__(self):
            FitFunctionBase.__init__(self)
            self.parameters = [1,100,0,0, 1000]
            self.startParameters = [1,100,0,0, 1000]

        def functionEval(self, x, A, T, theta, O, tau ):
            return A*numpy.exp(-numpy.square(x/tau))*numpy.square(numpy.sin(numpy.pi/2/T*x+theta))+O

Fits can also provide:

    - an 'update' method for updating other variables which are not fit variables
    - a 'smartStartValues' method for guessing good start values based on the data

see the existing fit functions for more examples.