
Dependencies
python 
numpy
scipy
grib_api (via pygrib)
libjasper-dev

"""
grib_api
tar xvf gribXXX
cd gribXXX
./configure --enable-python
make
make install
export PYTHONPATH="$PYTHONPATH:/usr/local/lib/python2.7/dist-packages/grib_api"
cp all lib-files from "grib_api_dir/lib" to "usr/lib"
"""
