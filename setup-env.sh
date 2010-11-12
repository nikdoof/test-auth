rm -rf ./env
virtualenv --distribute env
. ./env/bin/activate
pip install -r requirements.txt
