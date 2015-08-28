from fileParser import fileParser
from numpy import ndarray

class TableFile(fileParser):
    def __init__(self):
        super(TableFile, self).__init__()
        self.tableHeader = []

    def _parseHeader(self):
        super(TableFile, self)._parseHeader()
        while True:
            line = self.fileObj.readline()

            if line.isspace():
                pass
            else:
                strip = line.strip()
                self.tableHeader = strip.split('\t')
                self._dataOffset = self.fileObj.tell()
                break

    def readline(self, lineNum = None):
        line = self._readRawLine(lineNum)

        # strip whitespace on both sides of the line read
        dataList = line.strip().split('\t')

        # create a dictionary based on the data contained in the line
        dataDict = dict()
        for i, item in enumerate(dataList):
            if item == '':
                break
            dataDict[self.tableHeader[i]] = item
        return dataDict

    def _readRawLine(self, lineNum = None):
        # if the internal class data, such as tableHeader is not set,
        # then set the internal class data
        if self.tableHeader == []:
            self.fileObj.seek(0)
            self._parseHeader()
        
        # if lineNum has been passed, go to the begining of the data in
        # the file, and stop on the line requested and read the line.
        # Otherwise, read the next line.
        if lineNum >=0:
            self.fileObj.seek(self._dataOffset)
            for i in range(self.totalLines):
                line = self.fileObj.readline()
                if i==lineNum:
                    break
        else:
            line = self.fileObj.readline()

        return line

    def _appendline(self, data):
        # don't parse the header if the file is empty
        sep = '\t'
        if self.empty:
            if self.comments == []:
                ## The comments within the file as a list.
                self.comments = ['# A space for comments']
            if self.meta == {}:
                ## The meta data of the file as a dictionary.
                self.meta = {'metaExample':10}
            if self.tableHeader == []:
                for i, item in enumerate(data):
                    self.tableHeader.append('e{0}'.format(i+1))
            for comment in self.comments:
                self.fileObj.write(comment + '\n')
            for name, value in self.meta.iteritems():
                self.fileObj.write(name + '='+ str(value) + '\n')
            for item in self.tableHeader:
                self.fileObj.write(item + sep)
            self.fileObj.write('\n')
            self._dataOffset = self.fileObj.tell()
            ## A boolean file that is true if the file is empty,
            #  and false otherwise.
            self.empty = False
        else:
            #print 'file not empty'
            if self._dataOffset < 0:
                self.fileObj.seek(0)
                self._parseHeader()
            # Move to the end of the file to append.
            self.fileObj.seek(0,2)

        line = sep.join(data) + '\n'
        self.fileObj.write(line)

    def appendline(self, data):
        stringData = []
        if type(data) == ndarray:
            for i in data:
                stringData.append(repr(i))
        elif type(data) == list:
            if type(data[0]) == str:
                stringData = data
            elif type(data[0]) == float or type(data[0]) == int:
                for i in data:
                    stringData.append(repr(i))
            else:
                raise TypeError('The datatype is not supported.')
        elif type(data) == dict:
            defaultValue = str(0)
            values = data.values()
            keys = data.keys()
            if self.tableHeader == []:
                self.tableHeader = keys
                self.tableHeader.sort()
                '''
            if type(values[0]) == str:
                for item in self.tableHeader:
                    if data.has_key(item):
                        stringData.append(data[item])
                    else:
                        stringData.append(defaultValue)
            '''
            if type(values[0]) == float or type(values[0]) == int or type(values[0]) == str:
                for item in self.tableHeader:
                    if data.has_key(item):
                        stringData.append(str(data[item]))
                    else:
                        stringData.append(defaultValue)
            elif type(values[0])==ndarray:
                for item in self.tableHeader:
                    if data.has_key(item):
                        stringData.append(str(data[item][0]))
                    else:
                        stringData.append(defaultValue)
            elif type(values[0])==float64:
                for item in self.tableHeader:
                    if data.has_key(item):
                        stringData.append(str(data[item]))
                    else:
                        stringData.append(defaultValue)
            else:
                raise TypeError('The datatype is not supported.')
        else:
            raise TypeError('The datatype is not supported.')

        self._appendline(stringData)
