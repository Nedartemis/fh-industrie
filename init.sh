export PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
export PYTHONPATH="${PYTHONPATH}:${PWD}/tests"
echo "PYTHONPATH set"

source keys.sh
echo "Environnement variables set"

source /home/secouss/repos/fh-industrie/.venv/bin/activate
echo "Virtual environnement set"