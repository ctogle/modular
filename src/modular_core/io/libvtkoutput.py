#import libs.modular_core.libfundamental as lfu
#import libs.modular_core.libgeometry as lgeo

import modular_core.libfundamental as lfu

import modular_core.data.libdatacontrol as ldc

import xml.dom.minidom
from copy import deepcopy as copy

import pdb

if __name__ == 'libs.modular_core.libvtkoutput':
    if lfu.gui_pack is None: lfu.find_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd

if __name__ == '__main__': print 'this is a library!'

def write_image(system, vtk_filename, specifics = []):
    plot_targets = sort_data_by_type(system.data, specifics)
    doc = xml.dom.minidom.Document()
    
    pdb.set_trace()
    vtktype = 'ImageData'
    root_element = doc.createElementNS("VTK", "VTKFile")
    root_element.setAttribute("type", vtktype)
    root_element.setAttribute("version", "0.1")
    root_element.setAttribute("byte_order", "LittleEndian")
    doc.appendChild(root_element)

    #ImageData Element
    #tempExtent = lgeo.array_to_string(['0', viewdims[0], 
    tempExtent = ldc.array_to_string(['0', viewdims[0], 
                    '0', viewdims[1], '0', viewdims[2]])
    dataType = doc.createElementNS("VTK", vtktype)
    dataType.setAttribute("WholeExtent", tempExtent)
    dataType.setAttribute("Origin", "0 0 0")
    dataType.setAttribute("Spacing", "1 1 1")
    root_element.appendChild(dataType)

    # Piece 0 (only one)
    piece = doc.createElementNS("VTK", "Piece")
    piece.setAttribute("Extent", tempExtent)
    piece.setAttribute("NumberOfPoints", str(len(data[data.keys()[0]])))
    piece.setAttribute("NumberOfCells", "0")
    dataType.appendChild(piece)

    ### Points ####
    points = doc.createElementNS("VTK", "Points")
    piece.appendChild(points)

    # Point location data
    point_coords = doc.createElementNS("VTK", "DataArray")
    point_coords.setAttribute("type", "Float32")
    point_coords.setAttribute("format", "ascii")
    point_coords.setAttribute("NumberOfComponents", "3")
    points.appendChild(point_coords)

    point_coords_string = coords_to_string(data['time'], \
        data['time'], [0.0]*len(data['time']))
    point_coords_data = doc.createTextNode(point_coords_string)
    point_coords.appendChild(point_coords_data)

    #### Data at Points ####
    point_data = doc.createElementNS("VTK", "PointData")
    piece.appendChild(point_data)

    # Array Data
    for key in data.keys():
        if key == 'time':
            node= doc.createElementNS("VTK", "DataArray")
            node.setAttribute("Name", "Points")
            node.setAttribute("type", "Float32")
            node.setAttribute("format", "ascii")
            point_data.appendChild(node)
            node_Data = doc.createTextNode(point_coords_string)
            node.appendChild(node_Data)
            
        elif key == 'probability' or key == 'reaction_history':
            continue
            
        else:
            node= doc.createElementNS("VTK", "DataArray")
            node.setAttribute("Name", key)
            node.setAttribute("type", "Int32")
            node.setAttribute("format", "ascii")
            point_data.appendChild(node)
            #string = lgeo.array_to_string(data[key])
            string = ldc.array_to_string(data[key])
            node_Data = doc.createTextNode(string)
            node.appendChild(node_Data)

    #### Cell data (dummy) ####
    cell_data = doc.createElementNS("VTK", "CellData")
    piece.appendChild(cell_data)
        
    #### Cells ####
    cells = doc.createElementNS("VTK", "Cells")
    piece.appendChild(cells)
        
    # Cell locations
    cell_connectivity = doc.createElementNS("VTK", "DataArray")
    cell_connectivity.setAttribute("type", "Int32")
    cell_connectivity.setAttribute("Name", "connectivity")
    cell_connectivity.setAttribute("format", "ascii")
    cells.appendChild(cell_connectivity)

    # Cell location data
    connectivity = doc.createTextNode("0")
    cell_connectivity.appendChild(connectivity)

    cell_offsets = doc.createElementNS("VTK", "DataArray")
    cell_offsets.setAttribute("type", "Int32")
    cell_offsets.setAttribute("Name", "offsets")
    cell_offsets.setAttribute("format", "ascii")
    cells.appendChild(cell_offsets)
    offsets = doc.createTextNode("0")
    cell_offsets.appendChild(offsets)

    cell_types = doc.createElementNS("VTK", "DataArray")
    cell_types.setAttribute("type", "UInt8")
    cell_types.setAttribute("Name", "types")
    cell_types.setAttribute("format", "ascii")
    cells.appendChild(cell_types)
    types = doc.createTextNode("11")
    cell_types.appendChild(types)

    outFile = open(vtk_filename, 'w')
    doc.writexml(outFile, newl='\n')
    outFile.close()

def write_unstructured(system, vtk_filename, specifics = []):
    plot_targets = sort_data_by_type(system.data, specifics)
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
        string = ldc.array_to_string(plot_targets['scalars'][key])
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
    out_file = open('.'.join(vtk_filename.split('.')[:-1] + ['vtu']), 'w')
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
            sorted_data['scalars'][dater.name] = dater.scalars

        elif dater.tag == 'coordinates':
            sorted_data['coords']['_'.join(dater.coords.keys())] = dater.coords

    return sorted_data










