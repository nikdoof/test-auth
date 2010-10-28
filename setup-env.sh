rm -rf ./env
virtualenv -q --distribute env
. ./env/bin/activate
pip install -q -r requirements.txt
