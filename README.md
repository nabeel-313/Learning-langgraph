
# Create env
```
conda create --prefix ./langgraph python=3.12
```
# Activate env
```
conda activate ./langgraph
```
# Generate requirement.txt file
```
pip install pip-tools
pip-compile --resolver=backtracking pyproject.toml --output-file=requirements.txt
```
# Install required packages
```
pip install requirement.txt
pip install -e .
pip install pytest black
```