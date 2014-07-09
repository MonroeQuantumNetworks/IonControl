'''
Created on Jul 8, 2014

@author: pmaunz
'''
import pyqtgraph

class SceneToPrint:
    def __init__(self, widget, gridLinewidth=1, curveLinewidth=1):
        self.widget = widget
        self.gridLinewidth = gridLinewidth
        self.curveLinewidth = curveLinewidth
    
    def __enter__(self):
        self.widget.graphicsView.hideAllButtons(True)
        self.pencache = dict()
        self.curveitemcache = dict()
        if self.gridLinewidth!=1 or self.curveLinewidth!=1:
            for item in self.widget.graphicsView.scene().items():
                if hasattr(item, 'pen'):
                    pen = item.pen()
                    self.pencache[item] = pen.width()
                    pen.setWidth( pen.width()*self.gridLinewidth )  
                    item.setPen( pen )      
                elif hasattr(item, 'opts'):
                    shadowPen = item.opts.get('shadowPen')
                    pen = item.opts.get('pen')
                    self.curveitemcache[item] = (shadowPen.width() if shadowPen else None, pen.width() if pen else None)
                    if shadowPen:
                        shadowPen.setWidth( shadowPen.width()*self.curveLinewidth )
                    if pen:        
                        pen.setWidth( pen.width()*self.curveLinewidth )                       
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
