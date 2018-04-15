#!/usr/bin/env python
'''
    Purpose:    Wrapper script for calling Python motu client for CMEMS downloading
    Version:    v1.0 02/2018
    Author:     Ben Loveday, Plymouth Marine Laboratory
    Notes:      Require opython-motu client
'''
#-imports-----------------------------------------------------------------------
import os, sys, shutil
import argparse
import logging
import datetime
import subprocess


#-functions---------------------------------------------------------------------
def download_data(Command, logging, verbose=False):
    
    processed_state = 'Downloaded ok'
    logging.info('Launching download CMD:  '+Command)
    
    try:
        process = subprocess.Popen(CMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        process.wait()
        
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() is not None:
                break
            if nextline !='':
                logging.info(nextline)
            if 'Error' in nextline:
                processed_state = nextline
            sys.stdout.flush()
    
        output   = process.communicate()[0]
        exitCode = process.returncode
        
        if (exitCode == 0):
            logging.info('Downloading successful')
            processed_flag = True
        else:
            logging.error('Something went wrong in downloading: see above')
            processed_flag = False
    except:
        logging.info('Downloading unsuccessful')
        processed_flag = False
        processed_state = 'Unknown Error'
    
    return processed_flag, processed_state

#-default parameters------------------------------------------------------------
DEFAULT_LOG_PATH    = os.getcwd()
DEFAULT_CFG_FILE    = os.path.join(os.getcwd(),'CMEMS_download.cfg')
DEFAULT_MOTU_PATH   = os.getcwd()
DEFAULT_OUT_DIR     = os.path.join(os.getcwd(),'DATA')

#-args--------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username",\
                    type=str,\
                    help="username")
parser.add_argument("-p", "--password",\
                    type=str,\
                    help="password")
parser.add_argument("-c", "--config_file",\
                    type=str,\
                    default=DEFAULT_CFG_FILE,\
                    help="Config file to use")
parser.add_argument("-log", "--log_path",\
                    type=str,\
                    default=DEFAULT_LOG_PATH,\
                    help="Log file path")
parser.add_argument("-motu", "--motu_path",\
                    type=str,\
                    default=DEFAULT_MOTU_PATH,\
                    help="Motu client file path")
parser.add_argument("-o", "--output_dir",\
                    type=str,\
                    default=DEFAULT_OUT_DIR,\
                    help="Output directory")
parser.add_argument('-v', "--verbose",\
                    action='store_true',\
                    help="Switch to turn on verbose mode")
args = parser.parse_args()

#-main--------------------------------------------------------------------------
if __name__ == "__main__":
    # preliminary stuff
    logfile = os.path.join(args.log_path,"CMEMS_DOWNLOAD_"+datetime.datetime.now().strftime('%Y%m%d_%H%M')+".log")
    verbose=args.verbose
    
    # set file logger
    try:
        if os.path.exists(logfile):
            os.remove(logfile)
        print("logging to: "+logfile)
        logging.basicConfig(filename=logfile,level=logging.DEBUG)
    except:
        print("Failed to set logger")
    
    # read config file    
    config_dict = {}
    try:
        logging.info("Reading configuration file...")
        with open(args.config_file) as myfile:
            for line in myfile:
                if '#' in line:
                    continue
                else:
                    name, var = line.partition("=")[::2]
                    config_dict[name.strip()] = str(var.replace('\n',''))
    except:
        logging.warning("Failed to read configuration file")
        sys.exit()

    # set our variables
    motu_path  = args.motu_path
    username   = args.username
    password   = args.password
    outdir     = args.output_dir
    product_id = config_dict["product_id"]
    service_id = config_dict["service_id"]
    date_min   = datetime.datetime.strptime(config_dict["date_min"],'%Y-%m-%d')
    date_max   = datetime.datetime.strptime(config_dict["date_max"],'%Y-%m-%d')
    lonmin     = config_dict["lonmin"]
    lonmax     = config_dict["lonmax"]
    latmin     = config_dict["latmin"]
    latmax     = config_dict["latmax"]
    variables  = config_dict["variables"].split(',')

    # clear the output directory and make a new one
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)
    
    # set variables
    v_string=' --variable '
    all_variables = ' '
    for vv in variables:
        all_variables=v_string+"'"+vv+"'"+all_variables

    print all_variables
    # loop through dates
    this_date = date_min
    while this_date <= date_max:
        date_format=this_date.strftime('%Y-%m-%d')
        outname = product_id+'_'+date_format+'.nc'
        print('Saving to: '+outname)
        this_date = this_date + datetime.timedelta(days=1)
        CMD="python "+motu_path+"/motu-client-python/motu-client.py --user '"+username+"' --pwd '"+password+"' --motu 'http://motu.sltac.cls.fr/motu-web/Motu' --service-id '"+service_id+"' --product-id '"+product_id+"' --longitude-min '"+str(lonmin)+" ' --longitude-max '"+str(lonmax)+"' --latitude-min '"+str(latmin)+"' --latitude-max '"+str(latmax)+"' --date-min '"+date_format+"' --date-max '"+date_format+"' "+all_variables+" --out-dir '"+outdir+"' --out-name '"+outname+"'"
        if verbose:
            print CMD
        flag, state = download_data(CMD,logging)
