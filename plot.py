import matplotlib
#matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import numpy as np
import pandas as pd
from pandas import Series, DataFrame

import utils

# TODO: Symmetrization and Antisymmetrization. Take negative eigenvalues under 
# time reversal into account
# TODO: this does not work if I work with the column indices directly rather 
# than the config numbers. Using np.random.randint and iloc should be 
# considerably faster
def bootstrap(df, bootstrapsize):
  """
  Apply the bootstrap method to randomly resample gauge configurations

  Parameters
  ----------
  df : pd.DataFrame
      Lattice data with arbitrary rows and columns cnfg x T.
  bootstrapsize : int
      The number of bootstrap samles being drawn from `df`

  Returns
  -------
  boot : pd.DataFrame
      Lattice data with rows like `df` and columns boot x T. The number of
      level0 column entries is `bootstrapsize` and it contains the mean of
      nb_cnfg randomly drawn configurations.
  """
  np.random.seed(1227)
  idx = pd.IndexSlice

  # list of all configuration numbers
  cnfgs = df.columns.levels[0].values
  rnd_samples = np.array([np.random.choice(cnfgs, len(cnfgs)*bootstrapsize)]).\
                                            reshape((bootstrapsize, len(cnfgs)))
  # writing the mean value in the first sample
  rnd_samples[0] = cnfgs

  # Also I have to use a list comprehension rather than rnd directly...
  boot =  pd.concat([df.loc[:,idx[[r for r in rnd]]].mean(axis=1, level=1) for rnd in rnd_samples], axis=1, keys=range(bootstrapsize))

  return boot

def mean_and_std(df, bootstrapsize):
  """
  Mean and standard deviation over all configurations/bootstrap samples

  Parameters
  ----------
  df : pd.DataFrame
      Table with purely real entries (see Notes) and hierarchical columns where
      level 0 is the gauge configuration/bootrstrap sample number and level 1
      is the lattice time
  bootstrapsize : int
      The number of bootstrap samles being drawn from `df`

  Returns:
  --------
  pd.DataFrame
      Table with identical indices as `df` The column level 0 is replaced by 
      mean and std while level 1 remains unchanged

  Notes
  -----
  Must be taken for real and imaginary part seperately because that apparently 
  breaks pandas.
  """

  boot = bootstrap(df, bootstrapsize)
  mean = boot[0]
  std = boot.std(axis=1, level=1)

  return pd.concat([mean, std], axis=1, keys=['mean', 'std'])

def plot_gevp_el(data, label_template):
  """
  Plot all rows of given pd.DataFrame into a single page as seperate graphs

  data : pd.DataFrame
      
      Table with any quantity as rows and multicolumns where level 0 contains
      {'mean', 'std'} and level 1 contains 'T'
  
  label_template : string

      Format string that will be used to label the graphs. The format must fit
      the index of `data`
  """

  symbol = ['v', '^', '<', '>', 's', 'p', '*', 'h', 'H', 'D', 'd', '8']
    
  rows = data.index.values

  # iterrows() returns a tuple (index, series) 
  # index is a string (the index of data must be strings for this to work). In
  # data has a MultiIndex, index is a tuple of strings
  # series contains the mean and std for every timeslice
  for counter, (index, series) in enumerate(data.iterrows()):

    T = series.index.levels[1].values
    mean = series['mean'].values
    std = series['std'].values

    # prepare parameters for plot design
    if len(rows) == 1:
      cmap_brg=['r']
    else:
      cmap_brg = plt.cm.brg(np.asarray(range(len(rows))) * 256/(len(rows)-1))
    shift = 2./5/len(rows)

    label = label_template % index

    # plot
    plt.errorbar(T+shift*counter, mean, std, 
                     fmt=symbol[counter%len(symbol)], color=cmap_brg[counter], \
                     label=label, markersize=3, capsize=3, capthick=0.5, \
                     elinewidth=0.5, markeredgecolor=cmap_brg[counter], \
                                                                linewidth='0.0')


def avg_row_sum_mom(gevp_data, bootstrapsize, pdfplot, logscale=False, \
                                                                 verbose=False):
  """
  Create a multipage plot with a page for every element of the rho gevp

  Parameters
  ----------

  gevp_data : pd.DataFrame

      Table with a row for each gevp element (sorted by gevp column running
      faster than gevp row) and hierarchical columns for gauge configuration 
      number and timeslice

  bootstrapsize : int

      The number of bootstrap samples being drawn from `gevp_data`.

  pdfplot : mpl.PdfPages object
      
      Plots will be written to the path `pdfplot` was created with.

  See also
  --------

  utils.create_pdfplot()
  """

  gevp_data = mean_and_std(gevp_data, bootstrapsize)

  for gevp_el_name, gevp_el_data in gevp_data.iterrows():

    if verbose:
      print '\tplotting ', gevp_el_name[0], ' - ', gevp_el_name[1]

    # prepare data to plot
    T = gevp_el_data.index.levels[1].astype(int)
    mean = gevp_el_data['mean'].values
    std = gevp_el_data['std'].values

    # prepare parameters for plot design
    plt.title(r'Gevp Element ${} - {}$'.format(gevp_el_name[0], gevp_el_name[1]))
    plt.xlabel(r'$t/a$', fontsize=12)
    plt.ylabel(r'$C(t/a)$', fontsize=12)

    if logscale:
      plt.yscale('log')

    # plot
    plt.errorbar(T, mean, std, fmt='o', color='black', markersize=3, \
                 capsize=3, capthick=0.75, elinewidth=0.75, \
                                       markeredgecolor='black', linewidth='0.0')

    pdfplot.savefig()
    plt.clf()

  return 

# does not make sence for CMF C2 because there i just one momentum
def sep_rows_sep_mom(data, diagram, bootstrapsize, pdfplot, logscale=False, \
                                                                 verbose=False):
#  # discard imaginary part (noise)
#  data = data.apply(np.real)
  # sum over all gamma structures to get the full Dirac operator transforming 
  # like a row of the desired irrep
  data = data.sum(level=[0,1,2,3,5])

  data = mean_and_std(data, bootstrapsize)

  # create list of gevp elements to loop over
  gevp_index = list(set([(g[0],g[1]) for g in data.index.values]))
  for gevp_el_name in gevp_index:

    if verbose:
      print '\tplotting ', gevp_el_name[0], ' - ', gevp_el_name[1]

    # prepare plot
    plt.title(r'Gevp Element ${} - {}$'.format(gevp_el_name[0], gevp_el_name[1]))
    plt.xlabel(r'$t/a$', fontsize=12)
    plt.ylabel(r'$%s(t/a)$' % diagram, fontsize=12)

    if logscale:
      plt.yscale('log')

    # prepare data to plot
    gevp_el = data.xs(gevp_el_name, level=[0,1])

    # plot
    plot_gevp_el(gevp_el, r'$\mu = %i, p_{so} = %s - p_{si} = %s$')

    # clean up for next plot
    plt.legend(numpoints=1, loc='best', fontsize=6)
    pdfplot.savefig()
    plt.clf()


def sep_rows_sum_mom(data, diagram, bootstrapsize, pdfplot, logscale=False, \
                                                                 verbose=False):
  """
  Create a multipage plot with a page for every element of the rho gevp. Each
  page contains one graph for each row of the irrep, summed over all momenta.

  Parameters
  ----------

  data : pd.DataFrame

      Table with physical quantum numbers as rows 'gevp_row' x 'gevp_col' x \
      '\mu' x 'p_{so}' x '\gamma_{so}' x 'p_{si}' x '\gamma_{si}' and columns
      'cnfg' x 'T'.
      Contains the linear combinations of correlation functions transforming
      like what the parameters qn_irrep was created with, i.e. the subduced 
      data

  diagram : string
      The diagram as it will appear in the plot labels.

  bootstrapsize : int

      The number of bootstrap samples being drawn from `gevp_data`.

  pdfplot : mpl.PdfPages object
      
      Plots will be written to the path `pdfplot` was created with.

  See also
  --------

  utils.create_pdfplot()
  """

  # discard imaginary part (noise)
  data = data.apply(np.real)
  # sum over all gamma structures to get the full Dirac operator transforming 
  # like a row of the desired irrep
  data = data.sum(level=[0,1,2,3,5])
  # sum over equivalent momenta
  data = data.sum(level=[0,1,2])

  data = mean_and_std(data, bootstrapsize)

  # create list of gevp elements to loop over
  gevp_index = list(set([(g[0],g[1]) for g in data.index.values]))
  for gevp_el_name in gevp_index:

    if verbose:
      print '\tplotting ', gevp_el_name[0], ' - ', gevp_el_name[1]

    # prepare plot
    plt.title(r'Gevp Element ${} - {}$'.format(gevp_el_name[0], gevp_el_name[1]))
    plt.xlabel(r'$t/a$', fontsize=12)
    plt.ylabel(r'$%s(t/a)$' % diagram, fontsize=12)

    if logscale:
      plt.yscale('log')

    # prepare data to plot
    gevp_el = data.xs(gevp_el_name, level=[0,1])

    # plot
    plot_gevp_el(gevp_el, r'$\mu = %i$')

    # clean up for next plot
    plt.legend(numpoints=1, loc='best', fontsize=6)
    pdfplot.savefig()
    plt.clf()

def avg_rows_sep_mom(data, diagram, bootstrapsize, pdfplot, logscale=False, \
                                                                 verbose=False):
  """
  Create a multipage plot with a page for every element of the rho gevp. Each
  page contains one graph for each momentum, averaged over all rows of the 
  irrep. 

  Parameters
  ----------

  data : pd.DataFrame

      Table with physical quantum numbers as rows 'gevp_row' x 'gevp_col' x \
      '\mu' x 'p_{so}' x '\gamma_{so}' x 'p_{si}' x '\gamma_{si}' and columns
      'cnfg' x 'T'.
      Contains the linear combinations of correlation functions transforming
      like what the parameters qn_irrep was created with, i.e. the subduced 
      data

  diagram : string
      The diagram as it will appear in the plot labels.

  bootstrapsize : int

      The number of bootstrap samples being drawn from `gevp_data`.

  pdfplot : mpl.PdfPages object
      
      Plots will be written to the path `pdfplot` was created with.

  See also
  --------

  utils.create_pdfplot()
  """

  # discard imaginary part (noise)
  data = data.apply(np.real)
  # sum over all gamma structures to get the full Dirac operator transforming 
  # like a row of the desired irrep
  data = data.sum(level=[0,1,2,3,5])
  # average over rows
  data = data.mean(level=[0,1,3,4])
 
  data = mean_and_std(data, bootstrapsize)

  gevp_index = list(set([(g[0],g[1]) for g in data.index.values]))
  for gevp_el_name in gevp_index:

    if verbose:
      print 'plotting ', gevp_el_name[0], ' - ', gevp_el_name[1]

    # prepare plot
    plt.title(r'Gevp Element ${} - {}$'.format(gevp_el_name[0], gevp_el_name[1]))
    plt.xlabel(r'$t/a$', fontsize=12)
    plt.ylabel(r'$%s(t/a)$' % diagram, fontsize=12)

    if logscale:
      plt.yscale('log')

    # prepare data to plot
    gevp_el = data.xs(gevp_el_name, level=[0,1])

    # plot
    plot_gevp_el(gevp_el, r'$p_{so} = %s - p_{si} = %s$')

    # clean up for next plot
    plt.legend(numpoints=1, loc='best', fontsize=6)
    pdfplot.savefig()
    plt.clf()

def quick_view(data, bootstrapsize, pdfplot, logscale=False, \
                                                                 verbose=False):
  # TODO: pass data as list
  # calculate mean and std for every list member
  # concat along columns with identifier A1 and E2
  # can do that clean with merge but just a quick and dirty version vor new
  # copy paste plt command in loop to plot next to eahc other
  # normalize to timelice something. 7 or so.
  data = mean_and_std(data, bootstrapsize)

  for gevp_el_name, gevp_el_data in data.iterrows():

    if verbose:
      print '\tplotting ', gevp_el_name[0], ' - ', gevp_el_name[1]

    # prepare data to plot
    T = gevp_el_data.index.levels[1].astype(int)
    mean = gevp_el_data['mean'].values
    std = gevp_el_data['std'].values

    A1 = (df4.ix[3]/df4.iloc[3,7]).mean(level=1)
    # prepare parameters for plot design
    plt.title(r'Gevp Element ${} - {}$'.format(gevp_el_name[0], gevp_el_name[1]))
    plt.xlabel(r'$t/a$', fontsize=12)
    plt.ylabel(r'$C(t/a)$', fontsize=12)

    if logscale:
      plt.yscale('log')

    # plot
    plt.errorbar(T, mean, std, fmt='o', color='black', markersize=3, \
                 capsize=3, capthick=0.75, elinewidth=0.75, \
                                       markeredgecolor='black', linewidth='0.0')

    pdfplot.savefig()
    plt.clf()

  return 


