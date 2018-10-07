'''
    Purpose:    Universal downloader for Sentinel data
    Version:    v1.0 10/2018
    Author:     Ben Loveday, Plymouth Marine Laboratory
    Notes:      This code is offered with no warranty and under the MIT licence.
    
    To come in future versions:
    - add filtering of downloads by regional flag coverage
    - initialise with config file (not arguments)
    
    Usage:
    /opt/local/bin/python3.6 Universal_Sentinel_Downloader.py -p <YOUR PASSWORD> -n <YOUR USERNAME> -i 50.0,-10.0:51.0,-9.0 -l Sentinel-3 -x OL_2_WFR* -f NOW-10 -u 'https://coda.eumetsat.int'

'''

import logging
import re
import requests
from lxml import etree
import os
from datetime import datetime, timedelta
from glob import glob
import tempfile
import optparse
import sys, os, shutil
import numpy as np

# ------------------------------------------------------------------------------
def Define_request(par,url_hub):
    # Define search request and set par['hub']
    url_str = url_hub + '/search?q='
   
    for key in par['req'].keys():
        if url_str[-3:]!='?q=': url_str += ' AND '
        url_str += '%s:%s'%(key,par['req'][key])
  
    url_str += '&rows=%i&start=0'%par['max_rows']
    par['hub']=url_hub

    return url_str,par

# ------------------------------------------------------------------------------
def parse_xml(xml_text):
    # this line is python version dependant!!
    if sys.version_info[0] == 3:
        xml_str = re.sub(b' xmlns="[^"]+"', b'', xml_text, count=1)
    else:
        xml_str = re.sub(' xmlns="[^"]+"', '', xml_text, count=1)

    root = etree.fromstring(xml_str)
    entry_list = root.xpath("//entry")
  
    res = []
    for ee in entry_list:
        dt = {
              'uuid': ee.xpath("str[@name='uuid']/text()")[0],
              'identifier': ee.xpath("str[@name='identifier']/text()")[0],
              'beginposition': ee.xpath("date[@name='beginposition']/text()")[0],
              'endposition': ee.xpath("date[@name='endposition']/text()")[0],
             }
        res.append(dt)
   
    return res

# ------------------------------------------------------------------------------
def process_request(par,logging):        

    # open requests session
    with requests.Session() as req_ses:

        # define transport adaptor
        adaptor = requests.adapters.HTTPAdapter(max_retries=par['Retries'])
         
        # define URL
        url_str,par = Define_request(par,par['url'])

        # ------------------------------------------------------------------------
        # Request available files
        logging.info("Processing request at specified data HUB ... ")

        # try to connect to primary hub first:
        req_ses.mount(par['hub'], adaptor)
        logging.info('Querying data at: ' + par['hub'])
        logging.info('Query: ' + url_str)
        r = req_ses.get(url_str, auth=(par['user'],par['pass']), timeout=par['Timeout'])
        logging.info('Code '+par['url']+': ' + str(r.status_code))

        if r.status_code != 200:
            req_ses.close()
            logging.error("Data query to "+par['hub']+" was not successful! ("+str(par['Retries'])+" retries)")

        logging.info("Done")
        if r.status_code == 200:
            # parse xml code: extract image names and UUID
            entries = parse_xml(r.content)
            if len(entries)>=par['max_rows']:
                logging.error("The number of scenes ("+str(len(entries))+") is greater than maximum ("+str(par['max_rows'])+"): increase max_rows!")
                req_ses.close()
                raise Exception("The number of scenes ("+str(len(entries))+") is greater than maximum ("+str(par['max_rows'])+"): increase max_rows!")
        else:
            entries = False

    return entries

# ------------------------------------------------------------------------------
def download_files(par,entries,logging):
    # open requests session
    with requests.Session() as req_ses:

        # ----------------------------------------------------------------------
        # Create temp_dir
        temp_dir = tempfile.mkdtemp(suffix='_esa_downloader')
        # ----------------------------------------------------------------------
        # download files
        logging.info("Started downloading %i files ..."%len(entries))
        for ee in entries:
            split_id = ee['identifier'].split('_')
            sensor   = split_id[0][:2]

            # check if the file already exists in the archive
            try:
                if sensor.lower()=='s1':
                    dtime = datetime.strptime(split_id[5], '%Y%m%dT%H%M%S')
                elif sensor.lower()=='s2':
                    # annoying date format change
                    try:
                        logging.info('Trying for old date format')
                        dtime = datetime.strptime(split_id[5], '%Y%m%dT%H%M%S')
                    except:
                        logging.info('Failed: Trying for new date format')
                        dtime = datetime.strptime(split_id[6], '%Y%m%dT%H%M%S')
                elif sensor.lower()=='s3':
                    dtime = datetime.strptime(ee['identifier'][16:31], '%Y%m%dT%H%M%S')
                else:
                    logging.error("Not a Sentinel file name!")
                    raise Exception("Not a Sentinel file name!")
            except:
                logging.warning('Unknown file format...skipping this url: '+ee['identifier'])
                continue

            if par['make_sub_dir']:
                arc_dir = os.path.join(par['root_dir'],dtime.strftime('%Y/%m/%d'))
            else:
                arc_dir = par['root_dir']
      
            fname = os.path.join(arc_dir,ee['identifier']+'*')
            fnames = glob(fname)

            # build url string & isolate file
            url_str = par['hub'] + "/odata/v1/Products('%s')/$value"%ee['uuid']
            try:
                r     = req_ses.get(url_str, auth=(par['user'], par['pass']), stream=True)
            except:
                logging.warning('Hub misbehaving, skipping this url')
                logging.info('>>> '+url_str)
                continue

            # check file size
            file_size=-1
            try:
                base_fname = r.headers['content-disposition'].split('=')[1].strip('"')
                file_size  = int(r.headers['content-range'].split('/')[1])
            except:
                logging.info('Hub misbehaving, skipping this url')
                logging.info('>>> '+url_str)
                continue

            # download file to temp dir
            temp_fname = os.path.join(temp_dir,base_fname)
            logging.info("Downloading %s ... "%base_fname)

            chunk_count = 0.
            chunk_size  = 1024
            iters=np.arange(0,110,10)
            niter=0
            with open(temp_fname, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    chunk_count = chunk_count + chunk_size
                    if chunk: # filter out keep-alive new chunks
                        percent_done = float(chunk_count)/float(file_size)*100.
                        if percent_done >= iters[niter]:
                            logging.info(str(int(percent_done))+'% complete')
                            logging.info(str(float(chunk_count/(1024.*1024.)))+' Mb downloaded')
                            niter = niter+1
                    f.write(chunk)
                f.flush()

            # get file timestamp
            timestamp  = os.stat(temp_fname).st_mtime
  
            # copy from temp to archive
            if not os.path.exists(arc_dir):
                os.makedirs(arc_dir)

            try:
                shutil.move(temp_fname,arc_dir)
            except:
                #remnant of old file:
                os.remove(arc_dir+'/'+os.path.basename(temp_fname))
                shutil.move(temp_fname,arc_dir)

        # delete temp_dir
        shutil.rmtree(temp_dir)
        logging.info("Finished downloading!")

    return

# ------------------------------------------------------------------------------
def default_param():
    par = {
           'Retries': 1,
           'Timeout': None,
           'url':'https://coda.eumetsat.int/',
           'hub':None,         # eventual hub used to download: one of the urls above.
           'max_rows': 99      # maximum number of rows to request, increase if need more: but hub limits at 100 (as of 28/10/2016)!
          }
          
    par['req'] = {}

    return par

# ------------------------------------------------------------------------------
def parse_date(date_str,midnight=False): 
    if date_str!='':
        if date_str[:3].upper()=='NOW':
            if len(date_str)==3:
                dt = datetime.now()
            elif date_str[3]=='-':
                dt = datetime.now() - timedelta(days=int(options.date_from[4:]))
            else:
                raise Exception("Incorrect date!")
        else:
            if len(date_str)==8:
                dt = datetime.strptime(date_str, '%Y%m%d')
                if midnight: dt += timedelta(hours=23,minutes=59,seconds=59.999)
            else:
                dt = datetime.strptime(date_str, '%Y%m%dT%H%M%S')
    else:
        raise Exception("Date not set!")

    return dt

# ------------------------------------------------------------------------------    
def parse_options(options):   
    # check options
    if options.footprint == '':
        raise Exception("no footprint selected, use --fprint option")

    if options.date_from=='' and options.date_to!='': options.date_from=options.date_to
    if options.date_to=='' and options.date_from!='': options.date_to=options.date_from

    if options.date_from=='' and options.date_to!='': options.date_from=options.date_to

    # set parameters
    par = default_param()
    
    if options.sensor_operational_mode!='': par['req']['sensoroperationalmode'] = options.sensor_operational_mode
    if options.product_type!='': par['req']['producttype'] = options.product_type
    if options.platform_name!='': par['req']['platformname'] = options.platform_name
    if options.polarisation_mode!='': par['req']['polarisationmode'] = options.polarisation_mode
    if options.relative_orbit!='': par['req']['relativeorbitnumber'] = options.relative_orbit
    if options.absolute_orbit!='': par['req']['orbitnumber'] = options.absolute_orbit
    if options.logfile!='': par['logfile'] = options.logfile

    if options.user!='':
        par['user'] = options.user
    else:
        raise Exception("no username provided, use --user option")

    if options.password!='':
        par['pass'] = options.password
    else:
        raise Exception("no username provided, use --pass option")
 
    if options.url!='': par['url'] = options.url

    if options.logfile!='': par['logfile'] = options.logfile

    if options.root_dir!='': par['root_dir'] = options.root_dir
    par['make_sub_dir'] = options.make_sub_dir

    if options.footprint!='':
        latlon = options.footprint.strip().split(':')
    
        latlon1 = latlon[0].strip().split(',')
        latlon2 = latlon[1].strip().split(',')
  
        lat1 = latlon1[0].strip()
        lon1 = latlon1[1].strip()

        lat2 = latlon2[0].strip()
        lon2 = latlon2[1].strip()

    par['req']['footprint'] = '"Intersects(POLYGON((%(lon1)s %(lat1)s,%(lon2)s %(lat1)s,%(lon2)s %(lat2)s,%(lon1)s %(lat2)s,%(lon1)s %(lat1)s)))"'%{'lon1':lon1,'lat1':lat1,'lon2':lon2,'lat2':lat2}

    # date-time
    if options.date_from!='':
        dt_from = parse_date(options.date_from)
        dt_to = parse_date(options.date_to,midnight=True)
  
        par['req']['beginPosition'] = '['+dt_from.strftime('%Y-%m-%dT%H:%M:%S')+dt_from.strftime('.%f')[:4]+'Z TO '+dt_to.strftime('%Y-%m-%dT%H:%M:%S')+dt_to.strftime('.%f')[:4]+'Z]'

    return par

# ======================================================================
# Simple search query: https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/3FullTextSearch

# Parsing command line
if __name__=="__main__":

    # Parse command line
    command_line_parser = optparse.OptionParser()

    command_line_parser.add_option("--date_from", "-f", dest="date_from", default = 'NOW-1',
                                  help="Request from date: YYYYMMDD, YYYYMMDDTHHMMSS, NOW, NOW-xdays")

    command_line_parser.add_option("--date_to", "-t", dest="date_to", default = 'NOW',
                                  help="Request to date: YYYYMMDD (will be the end of day), YYYYMMDDTHHMMSS, NOW, NOW-xdays")

    command_line_parser.add_option("--dir","-d", dest="root_dir", default = './',
                                  help="Main directory of archive (root_dir/yyyy/mm/dd/*)")

    command_line_parser.add_option("--make_subdir","-s", dest="make_sub_dir", action="store_true",
                                  help="Add subdirectory (../yyyy/mm/dd/*)",
                                  default=False)

    command_line_parser.add_option("--plat","-l", dest="platform_name", default = 'Sentinel-3',
                                  help="Platform name: Sentinel-1, Sentinel-2, Sentinel-3")

    command_line_parser.add_option("--prod","-x", dest="product_type", default = 'OL_2_WFR*',
                                  help="Product type: OL_2_WFR*, OL_1_EFR*, SL_1_RBT*, SL_2_WST*, SLC, GRD, OCN etc")

    command_line_parser.add_option("--mode","-m", dest="sensor_operational_mode", default = '',
                                  help="Sensor operational mode: SM,IW,EW,WV ")

    command_line_parser.add_option("--pol","-o", dest="polarisation_mode", default = '',
                                  help="Sensor polarisation mode: HH,VV,HV,VH ")

    command_line_parser.add_option("--relorb","-r", dest="relative_orbit", default = '',
                                  help="Relative orbit number: NN, 'NN_0 TO NN_1' ")

    command_line_parser.add_option("--absorb","-b", dest="absolute_orbit", default = '',
                                  help="Absolute orbit number: NN, 'NN_0 TO NN_1' ")

    command_line_parser.add_option("--fprint","-i", dest="footprint", default = '',
                                  help="Image footprint: lat1,lon1:lat2,lon2 ")

    command_line_parser.add_option("--logfile","-z", dest="logfile",
                                  default="Download_log",
                                  help="Log file")
   
    command_line_parser.add_option("--pass", "-p", dest="password",
                                  default="",
                                  help="Password")
       
    command_line_parser.add_option("--user", "-n", dest="user",
                               default="",
                               help="Username")

    command_line_parser.add_option("--url", "-u", dest="url",
                               default="",
                               help="Username")
    
    options,arguments = command_line_parser.parse_args()

#-------------------------------------------------------------------------------
#-main----
if __name__ == "__main__":
    # ---------------------------------------------------------------------------
    # parse options
    par = parse_options(options)
    logfile = par["logfile"]+"_"+datetime.now().strftime('%Y%m%d_%H%M%S')+".log"
 
    # set file logger
    try:
        if os.path.exists(logfile):
            os.remove(logfile)
        logging.basicConfig(filename=logfile,level=logging.INFO)
        print("Logging to: "+logfile)
    except:
        raise Exception("Failed to set logger")

    # off we go
    entries = process_request(par,logging)

    if entries:
        download_files(par,entries,logging)

    logging.info("Done")

#-EOF
