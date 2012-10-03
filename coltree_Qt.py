# helpers.py
#
# Defines few utilities used throughout the code
################################################################################
#import gtk
#import gobject
from numpy import numarray
import os
from PyQt4 import QtCore, QtGui

CONFIG_FILE = "config.ddscon"

################################################################################
# class typical_ncol_tree
#
# Generates a GTK tree (a table), with column header and data type determined
# by the passed arguments. For an example how it looks like, see any of my logics
################################################################################
class typical_table_Qt:
    def __init__(self, GUI):#, tree_def):
        self.model = QtGui.QStandardItemModel()#gtk.ListStore(*map(lambda x:x[0], tree_def))
        self.ParentGui = GUI
        self.defs = {}

	# Create a TableView
        self.table = QtGui.QTableView()
        self.model.setHorizontalHeaderLabels(['Parameter Name','Parameter Value'])
        self.table.setModel(self.model)
##        # Add all the columns
##        for col in range(len(tree_def)):
##            # New renderer for the column
##            renderer = gtk.CellRendererText()
##            (type, name, c_edit) = tree_def[col]
##            # should the column be editable?
##            if (c_edit > 0):
##                renderer.connect('edited', self.cell_edited_callback, col)
##                renderer.set_property('editable', True)
##            # If the cell is not float, render it as text
##            if (type != gobject.TYPE_DOUBLE and type != gobject.TYPE_FLOAT):
##                self.treeview.insert_column_with_attributes(-1, name, renderer, text=col)
##            # If the cell is float/double, use a custom renderer
##            else:
##                tvcol = gtk.TreeViewColumn(name, renderer)
##                tvcol.set_cell_data_func(renderer, self.render_floats, col)
##                self.treeview.append_column(tvcol)
##    ###############################################################################
##    # cell_edited_callback
##    #
##    # called anytime data is changed in the tree. Changes the data in
##    # underlying model
##    ###############################################################################
##    def cell_edited_callback(self, cell, path, text, col=0):
##        iter = self.model.get_iter(path)
##        self.set_data_from_text(iter, col, text)
##        return gtk.TRUE

    ##############################################################################
    # add_row
    #
    # add a row to the tree, the row_data tuple must match columns data types
    # saves a pointer to the new row in self.defs
    ##############################################################################
    def add_row(self, *row_data):
        name = QtGui.QStandardItem(row_data[0])
        value = QtGui.QStandardItem(row_data[1])

        self.model.appendRow([name, value])
        self.defs[row_data[0]] = row_data[1]
        return

    ##############################################################################
    # get_data
    #
    # Retrieve data from a specified row/column
    ##############################################################################
    def get_data(self, name, col):
        #iter = self.defs[name]
        self.update_defs()
        return self.defs[name]#self.model.get_value(iter, col)

    ##############################################################################
    # set_data
    #
    # Retrieve data from a specified row/column
    ##############################################################################
    def set_data(self, name, col, value):
##        iter = self.defs[name]
##        return self.model.set_value(iter, col, value)
        name_found = False
        for n in range(self.model.rowCount()):
            if (name == str(self.model.item(n,0).text()) or name == str(self.model.item(n,0).text()).lower()):
                name_found = True
                valitem = QtGui.QStandardItem(str(value))
                self.model.setItem(n, 1, valitem)
                self.update_defs()
                break
        if (name_found == False):
            print "No variable named %s found" %name

    ##############################################################################
    # set_data_from_text
    #
    # Parses the text in a cell as an int, float or str, and changes the value in
    # underlying model
    #############################################################################
    def set_data_from_text(self, row, col, text):
##        type = self.model.get_column_type(col)
        try:
##            if (type in [gobject.TYPE_INT, gobject.TYPE_UINT]):
##                val = int(text)
##            elif (type in [gobject.TYPE_DOUBLE, gobject.TYPE_FLOAT]):
##                val = float(text)
##            elif (type == gobject.TYPE_STRING):
##                val = text
##                if (col == 0):
##                    name = self.model.get_value(iter, col)
##                    self.rows.pop(name)
##                    self.rows[text] = iter
            item = QtGui.QStandardItem(str(text))
            self.model.setItem(row, col, item)
            self.update_defs()

            return  #self.model.set_value(iter, col, val)
        except:
            print ("Invalid value passed to table!")
        return

##    #############################################################################
##    # render_floats
##    #
##    # Converts a float to a text value, and updates the cell text
##    #############################################################################
##    def render_floats(self, column, cell, model, iter, col_no = None):
##        value = model.get_value(iter, col_no)
##        return cell.set_property('text', "%.8g"%value)
    #############################################################################
    # update_defs
    #
    # update the defs from the model
    #############################################################################
    def update_defs(self):
        self.defs = {}
        for n in range(self.model.rowCount()):
            param_name = str(self.model.item(n,0).text())
            param_value = str(self.model.item(n,1).text())
            if (param_name != '' and param_value != ''):
                self.defs[param_name] = param_value
    #############################################################################
    # save_params
    #
    # saves all the values in the tree to a file using save_to_config
    #############################################################################
    def save_params(self, root):
        self.update_defs()
        text_to_save = ''
        for key in sorted(self.defs.iterkeys()):
            #for col in range(1, self.model.get_n_columns()):
            col = 1
            text_to_save = text_to_save + root + ':tree:' + key + ':' + str(col) + ':' + str(self.defs[key]) + '\n'
        save_to_config(text_to_save,'w')
        return

##    #############################################################################
##    # restore_state
##    #
##    # restores all the values from file using read_from_config
##    #############################################################################
##    def restore_state(self, root):
##        for row, key in enumerate(self.defs):
##            self.set_data_from_text(row, 0, key)
##            for col in range(self.model.columnCount()):
##                val = read_from_config(root + ':tree:' + key + ':' + str(col))
##                if (val): self.set_data_from_text(row, col, val)
##        return

######################################################################
# save_to_config
#
# saves a value to a CONFIG_FILE file, under header root. It either
# updates the value, if such header is already present, or adds
# both the header and value
######################################################################
def save_to_config(text, op):
    #if (os.access(CONFIG_FILE, os.F_OK) == 1):
    fd = file(CONFIG_FILE, op)
    #else:
    #    fd = file(CONFIG_FILE, "w")

    fd.seek(0,0)
    filesize = fd.tell()

    fd.seek(0,0)

#    newtext = root + ":" + str(value) + '\n'
    # save all after the header root
##    oldcontent = fd.read(filesize - end)
##    fd.seek(start)
    # truncate the file at the header root
##    fd.truncate(start)
    # Write new data, and rest of file
    # (effectively replacing old data with new)
    #Not preserving oldcontent at this point CWC 08302012
    fd.write(text)# + oldcontent)
    fd.close()

################################################################
# read_from_config
#
# Reads the value saved under header root from CONFIG_FILE
################################################################
def read_from_config(root_key_col):
    if (os.access(CONFIG_FILE, os.F_OK) == 0): return
    fd = file(CONFIG_FILE, "r")
    for line in fd:
        if line.startswith(root_key_col + ':'):
            fd.close()
            return line[len(root_key_col + ':'):-1]

    fd.close()
    return

################################################################
# list_keys_from_config
#
# Lists the variable names saved under header root from CONFIG_FILE
################################################################
def list_keys_from_config(root):
    if (os.access(CONFIG_FILE, os.F_OK) == 0): return
    fd = file(CONFIG_FILE, "r")
    rv = []
    for line in fd:
        if line.startswith(root + ':'):
            rv = rv + [line[len(root + ':'):-1].split(':')[0]]

    fd.close()
    return rv

################################################################
# read_defs_from_config
#
# Reads the variable names and values saved under header root from CONFIG_FILE
################################################################
def read_defs_from_config(root):
    defs = {}
    keys = list_keys_from_config(root)
    for key in keys:
        val = read_from_config(root + ':' + key + ':' + str(1))
        defs[key] = val
    return defs


################################################################
# read_state_from_config
#
# Reads the DDS, DAC, and SHUTR settings saved under header root from CONFIG_FILE
################################################################
def read_state_from_config(root):
    state = {}
    keys = list_keys_from_config(root)
    for key in keys:
        val = read_from_config(root + ':' + key)
        state[key] = val
    return state

#############################################################################
# save_state
#
# saves all the state shown on the panel to a file using save_to_config
#############################################################################
def save_state(root, state):
    text_to_save = ''
    for key in sorted(state.iterkeys()):
        text_to_save = text_to_save + root + ':'+key + ':' + str(state[key]) + '\n'
    save_to_config(text_to_save, 'a')
    return