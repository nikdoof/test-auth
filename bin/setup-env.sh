rm -rf ./env
virtualenv --distribute --no-site-packages env
. ./env/bin/activate
pip install -r requirements.txt