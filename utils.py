# Helper functions for IO to store intermediate results of subduction code on
# hard disk
# TODO: could be restructured as table format to access individual files and 
# allow appending, but speed is uncritical
import os

import numpy as np
import pandas as pd
from pandas import Series, DataFrame
import gmpy

import matplotlib
matplotlib.use('Agg') 
from matplotlib.backends.backend_pdf import PdfPages

################################################################################
# checks if the directory where the file will be written does exist
def ensure_dir(f):
  """Helper function to create a directory if it does not exis"""
  if not os.path.exists(f):
    os.makedirs(f)

def read_hdf5_correlators(path, key):
  """
  Read pd.DataFrame from hdf5 file

  Parameters
  ----------
  path : string
      Path to the hdf5 file
  key : string
      The hdf5 groupname to access the given data under. 

  Returns
  -------
  data : pd.DataFrame
      The data contained in the hdf5 file under the given key
  """

  data = pd.read_hdf(path, key)
  
  return data
  
def write_hdf5_correlators(path, filename, data, key, verbose=False):
  """
  write pd.DataFrame as hdf5 file

  Parameters
  ----------
  path : string
      Path to store the hdf5 file
  filename : string
      Name to save the hdf5 file as
  data : pd.DataFrame
      The data to write
  key : string
      The hdf5 groupname to access the given data under. Specifying multiple 
      keys, different data can be written to the same file
  """

  ensure_dir(path)
  data.to_hdf(path+filename, key, mode='w')
 
  if verbose:
    print '\tfinished writing', filename

################################################################################
# TODO: write that for a pandas dataframe with hierarchical index nb_cnfg x T
def write_data_ascii(data, filename, verbose=False):
  """
  Writes the data into a file.
  
  Parameters
  ----------
  filename: string
      The filename of the file.
  data: np.array
      A 2d numpy array with data. shape = (nsamples, T)

  Notes
  -----
  Taken from Christians analysis-code https://github.com/chjost/analysis-code

  The file is written to have L. Liu's data format so that the first line
  has information about the number of samples and the length of each sample.
  """
  if verbose:
    print("saving to file " + str(filename))
  
  # in case the dimension is 1, treat the data as one sample
  # to make the rest easier we add an extra axis
  if len(data.shape) == 1:
    data = data.reshape(1, -1)
  # init variables
  nsamples = data.shape[0]
  T = data.shape[1]
  L = int(T/2)
  # write header
  head = "%i %i %i %i %i" % (nsamples, T, 0, L, 0)
  # prepare data and counter
  #_data = data.flatten()
  _data = data.reshape((T*nsamples), -1)
  _counter = np.fromfunction(lambda i, *j: i%T,
                             (_data.shape[0],) + (1,)*(len(_data.shape)-1), dtype=int)
  _fdata = np.concatenate((_counter,_data), axis=1)
  # generate format string
  fmt = ('%.0f',) + ('%.14f',) * _data[0].size
  # write data to file
  np.savetxt(filename, _fdata, header=head, comments='', fmt=fmt)

def pd_series_to_np_array(series):
  """
  Converts a pandas Series to a numpy array

  Parameters
  ----------
  series : pd.Series
      Written for data with 1 column and a 2-level hierarchical index
  
  Returns
  -------
  np.array
      In the case of a Series with 2-level hierarchical index this will be a 
      2d array with the level 0 index as rows and the level 1 index as columns
  """

  return np.asarray(series.values).reshape(series.unstack().shape)

def write_ascii_correlators(path, filename, data, verbose):
  """
  write pd.DataFrame as ascii file in Liuming's format

  Parameters
  ----------
  path : string
      Path to store the hdf5 file
  filename : string
      Name to save the hdf5 file as
  data : pd.DataFrame
      The data to write
  """

  ensure_dir(path)
  fname = os.path.join(path, filename)
  write_data_ascii(np.asarray(pd_series_to_np_array(data)), fname, verbose)

def write_ascii_gevp(path, data, p_cm, irrep, verbose):

  assert np.all(data.notnull()), 'Gevp contains null entires'
  assert gmpy.is_square(len(data.index)), 'Gevp is not a square matrix'

  data_size = gmpy.sqrt(len(data.index))

  if verbose:
    print 'creating a %d x %d Gevp' % (data_size, data_size)

  for counter in range(len(data.index)):

    ensure_dir(path)
    #filename = 'Rho_Gevp_p%1d_%s.%d.%d.dat' % (p_cm, irrep, \
    filename = 'Pipi_Gevp_p%1d_%s.%d.%d.dat' % (p_cm, irrep, \
                                           counter/data_size, counter%data_size)

    # TODO: with to_csv this becomes a onliner but Liumings head format will 
    # be annoying. Also the loop can probably run over data.iterrows()
    write_ascii_correlators(path, filename, data.ix[counter], verbose)

def create_pdfplot(path, filename):
  """
  Helper function to create a pdfplot object and ensure existence of the path
  """

  ensure_dir(path)
  pdfplot = PdfPages(path+filename)

  return pdfplot
