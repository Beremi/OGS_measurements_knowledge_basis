# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 11:42:02 2022

@author: Cajuhi.T
"""

import meshio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#%% mesh input
meshIn = 'bulk.vtu'
meshOut = 'bulk_w_projections.vtu'

#%% read input mesh
m = meshio.read(meshIn)

#%% poins and cells
points = m.points 
cells =  m.cells

#%% point data

point_data = {"point_data": np.ones(np.size([points],1)) }
number_elements = np.size([m.get_cells_type("triangle6")],1)

#%% create arrays
# get available material ids
ids = m.cell_data['MaterialIDs'][0]

x = np.ones(number_elements)
#y = np.ones(number_elements)
#z = np.ones(number_elements)


#%% generate random data
# for porosity n (consequently water content)

iso = 0.105
u_factor = 0.05 # ~ max value 
l_factor = 0.175 # ~ min value 

xrand = np.random.uniform(low=l_factor, high=u_factor, size=(np.size(x),))
x = np.where(ids==0, xrand, x)
x = np.where(ids==1, xrand, x)

n_rd = np.array([x])
n_rd = np.transpose(n_rd)

#%% generate random data
# for intrinsic permeability ki (using the values from hydraulic conductivity instead of isotropic equivalent)

iso = 1e-14
u_factor = 1e-13 # ~ max value 
l_factor = 1e-19 # ~ min value 

xrand = np.random.uniform(low=l_factor, high=u_factor, size=(np.size(x),))
x = np.where(ids==0, xrand, x)
x = np.where(ids==1, xrand, x)
x = np.where(ids==2, xrand, x)

k_i_rd = np.array([x])
k_i_rd = np.transpose(k_i_rd)

#%% cell data
cell_data = {"MaterialIDs": [ids], 
             "n_rd": [n_rd],
             "k_i_rd": [k_i_rd]
             }
#%% write mesh
meshio.write_points_cells(
    meshOut,  # str, os.PathLike, or buffer/open file
    points,
    cells,
    # file_format="vtk",  # optional if first argument is a path; inferred from extension
    # Optionally provide extra data on points, cells, etc.
    point_data=point_data,
    cell_data=cell_data,
    # field_data=field_data
)

