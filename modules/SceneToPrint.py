'''
Created on Jul 8, 2014

@author: pmaunz
'''
import pyqtgraph

class SceneToPrint:
    def __init__(self, widget, linewidth):
        self.widget = widget
        self.linewidth = linewidth
    
    def __enter__(self):
        self.widget.graphicsView.hideAllButtons(True)
        
        self.pencache = dict()
        self.curveitemcache = dict()
        for item in self.widget.graphicsView.scene().items():
            if hasattr(item, 'pen'):
                pen = item.pen()
                self.pencache[item] = pen.width()
                pen.setWidth( pen.width()*self.linewidth )  
                item.setPen( pen )      
            elif isinstance( item, pyqtgraph.graphicsItems.PlotCurveItem.PlotCurveItem ):  #@UndefinedVariable
                shadowPen = item.opts['shadowPen']
                pen = item.opts['pen']
                self.curveitemcache[item] = (shadowPen.width() if shadowPen else None, pen.width() if pen else None)
                if shadowPen:
                    shadowPen.setWidth( shadowPen.width()*self.linewidth )
                if pen:        
                    pen.setWidth( pen.width()*self.linewidth )        
            elif isinstance( item, pyqtgraph.graphicsItems.ScatterPlotItem.ScatterPlotItem ) or isinstance( item, pyqtgraph.graphicsItems.ErrorBarItem.ErrorBarItem ):  #@UndefinedVariable
                pen = item.opts['pen']
                self.curveitemcache[item] = (None, pen.width() if pen else None)
                if pen:        
                    pen.setWidth( pen.width()*self.linewidth )        
        return self.widget

    def __exit__(self, exittype, value, traceback):
        for item, width in self.pencache.iteritems():
            pen = item.pen()
            pen.setWidth( width )  
            item.setPen( pen )              
              
        for item,(shadowWidth,width) in self.curveitemcache.iteritems():
            if shadowWidth is not None:
                item.opts['shadowPen'].setWidth(shadowWidth)
            if width is not None:
                item.opts['pen'].setWidth(width)
