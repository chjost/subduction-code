#!/usr/bin/python

import numpy as np

import sys

import utils
#sys.stdout = open('./boot.out', 'w')

################################################################################
# Parameters ###################################################################

################################################################################
bootstrap_original_data = False

p = 0         # momentum

nb_bins = 1
nb_boot = 500

################################################################################
# Functions ####################################################################

################################################################################
# prebinning
def prebinning(X, binsize):
  print X.shape
  nb_bins = int(X.shape[-1]/binsize)
  if X.shape[-1] % binsize > 0:
    nb_bins = nb_bins+1
  print nb_bins
  bins = np.zeros(X[...,0].shape + (nb_bins,))
  for i in range(0, nb_bins-1):
    bins[...,i] = np.mean(X[...,i*binsize:(i+1)*binsize], axis=-1)
  bins[...,nb_bins-1] = np.mean(X[...,(nb_bins-1)*binsize:], axis=-1)
  return bins

################################################################################
# bootstrap an arbitrary array with nb_cnfg as last dimension
def bootstrap(X, boot_size):
  np.random.seed(1227)
  boot = np.zeros(X[...,0].shape + (boot_size, ), dtype=float)
  length = X.shape[-1]
  # writing the mean value in the first sample
  boot[...,0] = np.mean(X, axis=-1) 
  # doing all other samples
  for i in range(1, boot_size): 
    if i % (boot_size/10) == 0:
      print '\tbootstrap sample %i' % i
    rnd = np.random.random_integers(0, high=length-1, size=length)
    boot[...,i] = np.mean(X[...,rnd], axis=-1)
  return boot

################################################################################
# Bootstrap routine ############################################################

def bootstrap_ensembles(p, nb_bins, nb_boot, bootstrap_original_data):
  ################################################################################
  # read original data and call bootrap procedure
  if bootstrap_original_data:
    path = './readdata/p%1i/C20_p%1i.npy' % (p, p)
    data = np.load(path)
    path = './readdata/p%1i/C20_p%1i_quantum_numbers.npy' % (p, p)
    qn_data = np.load(path)
    if ( (qn_data.shape[0] != data.shape[0])):
      print '\tBootstrapped operators do not aggree with expected operators'
      exit(0)

    binned_data = prebinning(data.real, nb_bins)
    print 'Bootstrapping original data for p = %1i. Real part:' % p
    boot_real = bootstrap(binned_data, nb_boot)
    print 'Bootstrapping original data. Imaginary part:'
    binned_data = prebinning(data.imag, nb_bins)
    boot_imag = bootstrap(binned_data, nb_boot)
    print boot_real.shape
    
    if (boot_real.shape[0] != boot_imag.shape[0]):
      print '\tSomething went wrong in splitting real from imaginary part.'
      exit(0)
    print '\tfinished bootstrapping original data'
  
  ################################################################################
  # read subduced data and call bootrap procedure
  path = './readdata/p%1i/C20_p%1i_subduced.npy' % (p, p)
  data = np.load(path)
  data = data[...,:251]
  path = './readdata/p%1i/C20_p%1i_subduced_qn.npy' % (p, p)
  qn_subduced = np.load(path)
  qn_subduced = qn_subduced[...,:251]
  if ( (qn_subduced.shape[0] != data.shape[0])):
    print 'Bootstrapped operators do not aggree with expected operators'
    exit(0)
  
  binned_data = prebinning(data, nb_bins)
  print 'Bootstrapping subduced data:'
  boot = bootstrap(binned_data, nb_boot)
  print '\tfinished bootstrapping subduced operators'
  
  ################################################################################
  # Write data to disc ###########################################################
  
  ################################################################################
  utils.ensure_dir('./bootdata')
  utils.ensure_dir('./bootdata/p%1i' % p)
  utils.ensure_dir('./bootdata/p%1i/raw' % p)
  utils.ensure_dir('./bootdata/p%1i/subduced' % p)
  utils.ensure_dir('./bootdata/p%1i/avg' % p)
  
  ################################################################################
  # write original data if it was bootstraped before
  
  if bootstrap_original_data:
    # write all operators
    path = './bootdata/p%1i/C20_p%1i_real' % (p, p)
    np.save(path, boot_real)
    path = './bootdata/p%1i/C20_p%1i_imag' % (p, p)
    np.save(path, boot_imag)
    path = './bootdata/p%1i/C20_p%1i_quantum_numbers' % (p, p)
    np.save(path, qn_data)
  
    # write every operator seperately
    for i in range(0, qn_data.shape[0]):
      path = './bootdata/p%1i/raw/%s_real' % \
              (p, qn_data[i][-1])
      np.save(path, boot_real[i])
      path = './bootdata/p%1i/raw/%s_imag' % \
              (p, qn_data[i][-1])
      np.save(path, boot_imag[i])
   
  ################################################################################
  # write subduced correlators

  # write all subduced correlators
  path = './bootdata/p%1i/C20_p%1i_subduced' % (p, p)
  print boot.shape
  np.save(path, boot)
  path = './bootdata/p%1i/C20_p%1i_subduced_qn' % (p, p)
  np.save(path, qn_subduced)

  # write means over all operators subducing into same irrep row
  path = './bootdata/p%1i/C20_p%1i_subduced_avg_vecks' % (p, p)
  # TODO: mp.mean or np.sum?
  avg = np.mean(boot, axis=4)
  print avg.shape

  qn_avg = np.empty_like(qn_subduced[...,0,:])
  for i in np.ndindex(qn_subduced[...,0,0].shape):
    qn_avg[i] = np.insert( np.insert( \
                  qn_subduced[i][0,-3:], 
                    np.dot(qn_subduced[i+(0,1)], qn_subduced[i+(0,1)]), 0, \
                                                                       axis=-1), 
                      np.dot(qn_subduced[i+(0,0)], qn_subduced[i+(0,0)]), 0, \
                                                                        axis=-1)
  print qn_avg.shape
  np.save(path, avg)
  path = './bootdata/p%1i/C20_p%1i_subduced_avg_vecks_qn' % (p, p)
  np.save(path, qn_avg)

   # write means over all operators subducing into same irrep
  path = './bootdata/p%1i/C20_p%1i_subduced_avg_rows' % (p, p)
  avg = np.mean(avg, axis=3)
  print avg.shape
  np.save(path, avg)
  qn_avg = qn_avg[...,0,:]
  path = './bootdata/p%1i/C20_p%1i_subduced_avg_rows_qn' % (p, p)
  np.save(path, qn_avg)

   # write the subduced correlators for each irrep, row and gamma seperately
  for i in np.ndindex(qn_subduced[...,0].shape):
    path = './bootdata/p%1i/subduced/C20_uu_%s_%1i_p%1i%1i%1i.d000.%s_' \
                                                   'p%1i%1i%1i.d000.%s' % \
            (p, qn_subduced[i][-1], i[-2], qn_subduced[i][0][0], qn_subduced[i][0][2], \
             qn_subduced[i][0][2], qn_subduced[i][2], \
             qn_subduced[i][1][0], qn_subduced[i][1][1], \
             qn_subduced[i][1][2], qn_subduced[i][3])
    np.save(path, boot[i])
 
#  # write means over all operators subducing into same irrep
#  if p not in [1,3,4]:
#    path = './bootdata/p%1i/C20_p%1i_avg_subduced' % (p, p)
#    np.save(path, np.mean(boot, axis=2) )
#    path = './bootdata/p%1i/C20_p%1i_avg_subduced_quantum_numbers' % (p, p)
#    np.save(path, qn_subduced[...,0,-3:])
#  else:
#    # if p in [1,3,4], the 2dim E2 irrep appears. Both rows can be averaged, thus
#    # the average is taken and appended in the end for plotting
#    path = './bootdata/p%1i/C20_p%1i_avg_subduced' % (p, p)
#    E2 = np.zeros((1,) + np.mean(boot, axis=2)[0].shape)
#    for j in range(0,boot.shape[1]):
#      E2[0,j] = np.mean(np.vstack((boot[1,j], boot[2,j])), axis=0)
#    np.save(path, np.vstack((np.mean(boot, axis=2), E2 )) )
#    path = './bootdata/p%1i/C20_p%1i_avg_subduced_quantum_numbers' % (p, p)
#    E2_qn = np.zeros((1,qn_subduced.shape[1], qn_subduced[...,-3:].shape[-1]), \
#                                                                  dtype=((str,256)))
#    E2_qn[0] = qn_subduced[0,:,0,-3:]
#    for j in range(0,boot.shape[1]):
#      E2_qn[0,j,-1] = 'E2'
#    np.save(path, np.vstack((qn_subduced[...,0,-3:], E2_qn)) )

  print '\tfinished writing'

bootstrap_ensembles(p, nb_bins, nb_boot, bootstrap_original_data)
