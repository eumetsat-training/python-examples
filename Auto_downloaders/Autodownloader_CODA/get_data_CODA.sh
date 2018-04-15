#!/bin/bash

#OS: sets your operating system: choices are 'Linux', 'OSx', 'Windows'
OS='Linux'

#CMD_PATH: this is the path to where the dhusget.sh command is. dhusget.sh (or variant) is
#the ROOT_CMD (the downloader we are going to call).
CMD_PATH='./'
ROOT_CMD='dhusget.sh'

#USERNAME: your CODA username
USERNAME='benloveday'

#PASSWORD: your CODA password
PASSWORD='S4v41123'

# this is where you specify the path where you want data downloaded: e.g. /test/test. The actual storage
# path will be /test/test/<SENSOR>/<YEAR>/<MONTH>/<DAY>/
OUT_ROOT='./Data/'

# this is where you selecr which sensor you want: choices are 'OLCI','SLSTR' or 'SRAL'
SENSOR='SLSTR'

# this is where you set the dates you want to download: start and end in the following format: 'YYYY-MM-DD'
DATE_START='2018-03-25'
DATE_END='2018-03-25'

# this sets the number of downloads to attempt at the same time; CONCUR > 1 only for DPROD='DATA'
CONCUR='1'

# this sets the number of download retries
RETRIES='5'

# this sets the maximum number of products to download per day; it should be left at 100
NUM_PROD='100'

# this sets the geographical coordinates for the download area. Any tile that touches this box will
# be downloaded, even if most of the data is outside of the box. Unavoidable at this stage, but may be
# improved in the future. Format should be 'lon1,lat1:lon2,lat2'. E.g. for west africa: -10.0,-4.0:12.5, 8.0'
COORDS='30.00,-9.00:44.00,21.00'

# this option decides if you should download data or just test if it is present"
# DOPTION='DATA' < downloads all data
# DOPTION='TEST' < download manifests only
# DOPTION='PROD' < downloads specific products only
DOPTION='DATA'

# use if PROD is selected for products
DPROD=('xfdumanifest.xml' 'chl_nn.nc' 'tie_geo_coordinates.nc' 'wqsf.nc' 'time_coordinates.nc' 'instrument_data.nc')

# additional string options: run dhusget.sh -help to see how to use these options.
# some examples of how these can be used:
# TOPTION is used to quickly refine the data you want to download, e.g. Level 1 or NRT only
# -----------
# TOPTION='*NT*'   : will only download NRT data
# TOPTION='*OL_2*' : will only download OLCI Level 2 data
# -----------
# FOPTION is used to construct more specific arguments for downloads, again, see
# dhusget.sh -help for more information
# FOPTION='filename:S3A_OL_2*WRR*NT*'
FOPTION='filename:S3A_SL_2*NR*'

#####################################
# NO USER PARAMETERS BELOW HERE; DO NOT EDIT
#####################################
OPTIONS=" -u $USERNAME -p $PASSWORD -i $SENSOR -c $COORDS -n $CONCUR -l $NUM_PROD -N $RETRIES"

if [ "$DOPTION" == "DATA" ]; then
  OPTIONS=$OPTIONS' -o product'
else
  OPTIONS=$OPTIONS' -o manifest'
fi

if [ "$TOPTION" == "" ]; then
  echo 'No extra -T options'
else
  OPTIONS=$OPTIONS" -T $TOPTION"
fi

if [ "$FOPTION" == "" ]; then
  echo 'No extra -F options'
else
  OPTIONS=$OPTIONS" -F $FOPTION"
fi

if [ "$OS" == "OSx" ]; then
  date_cmd='gdate'
else
  date_cmd='date'
fi

echo "-------------------------------------------------------------------------"
echo "---------------------------------OPTIONS---------------------------------"
echo $OPTIONS
echo "-------------------------------------------------------------------------"
echo "-------------------------------------------------------------------------"

if [ "$DOPTION" != "PROD" ]; then
  DPROD=('All')
fi

DATE_ROLL=$DATE_START

DATE_END=$($date_cmd -d "$DATE_END + 1 day")
YEAR=$($date_cmd -d "$DATE_END" '+%Y')
MONTH=$($date_cmd -d "$DATE_END" '+%m')
DAY=$($date_cmd -d "$DATE_END" '+%d')
DATE_END=$YEAR'-'$MONTH'-'$DAY


# loop through days
while [ "$DATE_ROLL" != $DATE_END ]; do
  echo $DATE_ROLL
  YEAR=$($date_cmd -d "$DATE_ROLL" '+%Y')
  MONTH=$($date_cmd -d "$DATE_ROLL" '+%m')
  DAY=$($date_cmd -d "$DATE_ROLL" '+%d')
  OUT_DIR=$OUT_ROOT'/'$SENSOR'/'$YEAR'/'$MONTH'/'$DAY'/'

  # create output directory if it does not exist
  if [ ! -d $OUT_DIR ]; then
    mkdir -p $OUT_DIR
  fi
  # launch command for this date
  for prod in "${DPROD[@]}"; do
    echo "-------------------------------------------------------------------------"
    echo "-----------------------------------PROD----------------------------------"
    echo $prod
    echo "-------------------------------------------------------------------------"
    echo "-------------------------------------------------------------------------"
    echo $CMD_PATH'/'$ROOT_CMD $OPTIONS -S $YEAR'-'$MONTH'-'$DAY'T00:00:00.000Z' -E $YEAR'-'$MONTH'-'$DAY'T23:59:59.000Z' -O $OUT_DIR -Z $prod
    exit
  done

  DATE_ROLL=$($date_cmd -d "$DATE_ROLL + 1 day")
  # reconstruct date format at -I option not always available
  YEAR=$($date_cmd -d "$DATE_ROLL" '+%Y')
  MONTH=$($date_cmd -d "$DATE_ROLL" '+%m')
  DAY=$($date_cmd -d "$DATE_ROLL" '+%d')
  DATE_ROLL=$YEAR'-'$MONTH'-'$DAY
done

