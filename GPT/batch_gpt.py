import os
from os import path, listdir, system
# CONFIG
# set up the environment, path to your gpt processor
gptProcessor = '/usr/local/snap6/bin/gpt'

# define your graph xml, and input and output directory paths
c2rcc_xml = path.join(os.getcwd(),'olci_c2rcc.xml')
input_dir = path.join(os.getcwd(),'L1_subset')
output_dir = path.join(os.getcwd(),'L2_batch')

# INPUTS
# make a list of all the input files in your input directory, only taking the .dim files
input_files = [f for f in sorted(listdir(input_dir)) if
               path.isfile(path.join(input_dir, f)) and path.basename(f).endswith('.dim')]

# MAIN
# this is the loop where the magic happens :-)
# the loop goes over each input file in the input_files list
for input_file in input_files:
    # for gpt, you need the full path to the file (or you need to set your working environment)
    input = path.join(input_dir, input_file)
    print(input)
    # the output file is named from the input file with the _C2RCCC suffix.
    # Here you will write a netcdf file. this can be changed
    output_product = path.join(output_dir, path.splitext(input_file)[0] + '_C2RCC.nc')
    print(output_product)
    # the processing call is a follows below. Make sure that you have the necessary spaces in between the calls
    c2rcc_processingCall = gptProcessor + ' ' + c2rcc_xml + ' -SsourceProduct=' + input + ' -t ' + output_product
    # useful to check that the command call is correct before launching the call (comment / uncomment the next line)
    print(c2rcc_processingCall)
    # python call, uncomment when the printed call satisfies your requirements
    system(c2rcc_processingCall)



