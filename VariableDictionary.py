
from modules.SequenceDict import SequenceDict
from modules.Expression import Expression
from networkx import DiGraph, simple_cycles, dfs_postorder_nodes, dfs_preorder_nodes
from modules.magnitude import Magnitude
import logging

class CyclicDependencyException(Exception):
    pass


class VariableDictionaryView(object):
    """View on VariableDictionary that combines the local dictionary with the global dictionary
    the returnvalue is the evaluated value for both dictionaries"""
    def __init__(self, variableDictionary ):
        self.variableDictionary = variableDictionary
        
    def __getitem__(self, key):
        """if the key is in the local dictionary return the value, 
        if it is in the global dictionary return that value,
        otherwise raise KeyError"""
        if key in self.variableDictionary:
            return self.variableDictionary[key].value
        if key in self.variableDictionary.globaldict:
            return self.variableDictionary.globaldict.get(key)
        raise KeyError()
    
    def iteritems(self):
        return [ (key, var.value if var.enabled else 0 ) for key, var in self.variableDictionary.iteritems() ]
    
    def __contains__(self, key):
        return key in self.variableDictionary or key in self.variableDictionary.globaldict       
    
 
class VariableDictionary(SequenceDict):
    """Ordered Dictionary to hold variable values. It maintains a dependency graph
    to check for cycles and to recalculate the necessary values when one of the fields is updated"""   
    def __init__(self, variabledict, globaldict):
        super(VariableDictionary,self).__init__()
        self.dependencyGraph = DiGraph()
        self.expression = Expression()
        self.globaldict = globaldict
        self.valueView = VariableDictionaryView(self)
        for name,var in variabledict.iteritems():
            if var.type in ['parameter','address']:
                super(VariableDictionary,self).__setitem__(name, var)
        for name, var in self.iteritems():
            if hasattr(var,'strvalue'):
                var.value, dependencies = self.expression.evaluate(var.strvalue, self.valueView, listDependencies=True)
                self.addDependencies(self.dependencyGraph, dependencies, name)
        self.recalculateAll()
        
    def __setitem__(self, key, value):
        super(VariableDictionary,self).__setitem__(key, value)
        if hasattr(value,'strvalue'):
            self.setStrValue( key, value.strvalue )

                
    def addDependencies(self, graph, dependencies, name):
        """add all the dependencies to name"""
        for dependency in dependencies:
            self.addEdgeNoCycle(graph, dependency, name)        
                
    def addEdgeNoCycle(self, graph, first, second ):
        """add the dependency to the graph, raise CyclicDependencyException in case of cyclic dependencies"""
        graph.add_edge(first, second)
        cycles = simple_cycles( graph )
        for cycle in cycles:
            raise CyclicDependencyException(cycle)
                
    def setStrValueIndex(self, index, strvalue):
        return self.setStrValue( self.keyAt(index), strvalue)
        
    def setStrValue(self, name, strvalue):
        """update the variable value with strvalue and recalculate as necessary"""  
        var = self[name]
        result, dependencies = self.expression.evaluate(strvalue, self.valueView, listDependencies=True )
        graph = self.dependencyGraph.copy()            # make a copy of the graph. In case of cyclic dependencies we do not want o leave any changes
        for edge in list(graph.in_edges([name])):      # remove all the inedges, dependencies from other variables might be gone
            graph.remove_edge(*edge)
        self.addDependencies(graph, dependencies, name) # add all new dependencies
        if isinstance(result, Magnitude) and result.dimensionless():
            result.output_prec(0)
        var.value = result
        var.strvalue = strvalue
        self.dependencyGraph = graph
        return self.recalculateDependent(name)
        
    def setEncodingIndex(self, index, encoding):
        self.at(index).encoding = None if encoding == 'None' else str(encoding)
    
    def setEnabledIndex(self, index, enabled):
        self.at(index).enabled = enabled
       
    def recalculateDependent(self, node):
        if self.dependencyGraph.has_node(node):
            generator = dfs_preorder_nodes(self.dependencyGraph,node)
            next(generator )   # skip the first, that is us
            nodelist = list(generator)  # make a list, we need it twice 
            for node in nodelist:
                self.recalculateNode(node)
            return nodelist     # return which ones were re-calculated, so gui can be updated 
        return list()

    def recalculateNode(self, node):
        if node in self:
            var = self[node]
            if hasattr(var,'strvalue'):
                var.value = self.expression.evaluate(var.strvalue, self.valueView)
            else:
                logging.getLogger(__name__).warning("variable {0} does not have strvalue.".format(var))
            
    def recalculateAll(self):
        g = self.dependencyGraph.reverse()
        for node, indegree in g.in_degree_iter():
            if indegree==0:
                for calcnode in dfs_postorder_nodes(g, node):
                    self.recalculateNode(calcnode)
                    
    def bareDictionaryCopy(self):
        return SequenceDict( self )

if __name__=="__main__":
    class variable:
        def __init__(self,name,strvalue):
            self.strvalue = strvalue
            self.value = 0
            self.type = 'parameter'
            self.name = name
    
    globaldict = { 'G1': 1, 'G2': 8 }
    
    vd = VariableDictionary( { 'L1': variable('L1','G1*23+G2'), 'L2': variable('L2','2*L1'), 'L3': variable('L3','3*L2+L1') }, globaldict)
    
    for name, var in vd.iteritems():
        print name, var.value
    
    vd.setStrValue('L1', '17*pi')
    print
    vd.setStrValue('L2', '17*pi')
    print
    vd.setStrValue('L3', '17*pi')
    print
    vd.setStrValue('L3', '17*pi*L1+L2')
    print
    vd.setStrValue('L1', '12')
    print
    vd.setStrValue('L2', '1')
    
    print vd.valueView['L1']
    print vd.iteritems()
    
  
    