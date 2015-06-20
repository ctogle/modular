import modular_core.fundamental as lfu

import xml.dom.minidom
import numpy as np

from copy import deepcopy as copy

import pdb

__doc__ = '''Provides basic functions for vtk formatted io of python objects'''

if __name__ == 'libs.modular_core.mvtk':pass
    #if lfu.gui_pack is None: lfu.find_gui_pack()
    #lgm = lfu.gui_pack.lgm                                                 
    #lgd = lfu.gui_pack.lgd
    #lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'mvtk of modular_core.io'

def write_structuredpoints(data,filename,targets = []):
    raise NotImplemented
def write_structuredgrid(data,filename,targets = []):
    raise NotImplemented
def write_rectilineargrid(data,filename,targets = []):
    raise NotImplemented
def write_polygonaldata(data,filename,targets = []):
    raise NotImplemented
def write_polygonaldata(data,filename,targets = []):
    raise NotImplemented

def write_unstructuredgrid(data,filename,targets = []):
    '''Save modular data in \'data\' \'obj\' at \'filename.\'
    This file is readable by the program "paraview" as an unstructured grid.
    '''
    plot_targets = sort_data_by_type(data.data,targets)
    doc = xml.dom.minidom.Document()

    root_element = setup_element(doc, 'VTKFile', 
        {'type' : 'UnstructuredGrid',
        'version' : '0.1', 
        'byte_order' : 'LittleEndian'})
    doc.appendChild(root_element)

    dataType = doc.createElementNS('VTK', 'UnstructuredGrid')
    root_element.appendChild(dataType)

    piece = setup_element(doc, 'Piece', {
        'NumberOfPoints' : str(len(plot_targets['scalars'][
                        plot_targets['scalars'].keys()[0]])), 
        'NumberOfCells' : '0'})
    dataType.appendChild(piece)

    points = doc.createElementNS('VTK', 'Points')
    piece.appendChild(points)

    point_coords = setup_element(doc, 'DataArray', {
        'type' : 'Float32',
        'format' : 'ascii',
        'NumberOfComponents' : '3'})
    points.appendChild(point_coords)

    point_data = doc.createElementNS('VTK', 'PointData')
    piece.appendChild(point_data)
    if len(plot_targets['coords'].keys()) > 0:
        node = setup_element(doc, 'DataArray', {
            'Name' : 'Points', 
            'type' : 'Float32', 
            'format' : 'ascii'})
        point_data.appendChild(node)
        keydex = plot_targets['coords'].keys()[0]
        keydexes = plot_targets['coords'][keydex].keys()
        point_coords_string = coords_to_string(
            plot_targets['coords'][keydex][keydexes[0]],
            plot_targets['coords'][keydex][keydexes[1]],
            plot_targets['coords'][keydex][keydexes[2]])
        node_Data = doc.createTextNode(point_coords_string)
        node.appendChild(node_Data)

    elif len(plot_targets['scalars'].keys()) > 0:
        node = setup_element(doc, 'DataArray', {
            'Name' : 'Points', 
            'type' : 'Float32', 
            'format' : 'ascii'})
        point_data.appendChild(node)
        keydex = plot_targets['scalars'].keys()[0]
        point_coords_string = coords_to_string(
            plot_targets['scalars'][keydex],
            plot_targets['scalars'][keydex],
            plot_targets['scalars'][keydex])
        node_Data = doc.createTextNode(point_coords_string)
        node.appendChild(node_Data)     

    point_coords.appendChild(copy(node_Data))

    for key in plot_targets['scalars'].keys():
        node = setup_element(doc, 'DataArray', {
            'Name' : key, 
            'type' : 'Float32', 
            'format' : 'ascii'})
        point_data.appendChild(node)
        #string = lgeo.array_to_string(plot_targets['scalars'][key])
        #string = ldc.array_to_string(plot_targets['scalars'][key])
        string = array_to_string(plot_targets['scalars'][key])
        node_Data = doc.createTextNode(string)
        node.appendChild(node_Data)

    cell_data = doc.createElementNS("VTK", "CellData")
    piece.appendChild(cell_data)
        
    cells = doc.createElementNS("VTK", "Cells")
    piece.appendChild(cells)

    cell_connectivity = setup_element(doc, 'DataArray', {
        'type' : 'Int32', 
        'Name' : 'connectivity', 
        'format' : 'ascii'})
    cells.appendChild(cell_connectivity)

    connectivity = doc.createTextNode("0")
    cell_connectivity.appendChild(connectivity)

    cell_offsets = setup_element(doc, 'DataArray', {
        'type' : 'Int32', 
        'Name' : 'offsets', 
        'format' : 'ascii'})
    cells.appendChild(cell_offsets)
    offsets = doc.createTextNode("0")
    cell_offsets.appendChild(offsets)

    cell_types = setup_element(doc, 'DataArray', {
        'type' : 'UInt8', 
        'Name' : 'types', 
        'format' : 'ascii'})
    cells.appendChild(cell_types)
    types = doc.createTextNode("11")
    cell_types.appendChild(types)
    out_file = open('.'.join(filename.split('.')[:-1] + ['vtu']), 'w')
    doc.writexml(out_file, newl='\n')
    out_file.close()

def setup_element(doc, vtk_type = 'DataArray', attributes = {}):
    node = doc.createElementNS('VTK', vtk_type)
    for att in attributes.keys():
        node.setAttribute(att, attributes[att])

    return node

# SHOULD USE STRINGIO
def array_to_string(arr):
    string = ' '
    string = string.join([str(value) for value in arr])
    string += ' '
    return string

def coords_to_string(x, y, z):
    #concat = x + y + z
    concat = np.concatenate((x, y, z))
    array = [[concat[k], concat[k + len(x)], concat[k + 2*len(x)]] \
                                        for k in range(len(x))]
    array = [item for sublist in array for item in sublist]
    return array_to_string(array)

def quality_coords_to_string(x, y, z, Q, dims):
    string = str()
    xdim = int(dims[0]) + 1
    ydim = int(dims[1]) + 1
    zdim = int(dims[2]) + 1
    npts = xdim*ydim*zdim
    flat = ['0']*npts
    for j in range(len(Q)):
        try:
            flat[int(z[j])*xdim*ydim + int(y[j])*xdim + int(x[j])]=str(Q[j])

        except IndexError:
            print 'Youve got an indexing problem'
            pdb.set_trace()

    string = array_to_string(flat)
    return string

def sort_data_by_type(data, specifics = []):
    if not specifics: specifics = [dater.name for dater in data]
    sorted_data = {'scalars': {}, 'coords': {}}
    for dater in [dater for dater in data if dater.name in specifics]:
        if dater.tag == 'scalar':
            sorted_data['scalars'][dater.name] = dater.data

        elif dater.tag == 'coordinates':
            sorted_data['coords']['_'.join(dater.coords.keys())] = dater.coords

    return sorted_data










