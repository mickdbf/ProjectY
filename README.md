
# ToDo after cloning:
Enter the commands in the terminal to create and 
activate the virtual environment for the project.
Then install the requirements.

# Create a virtual environment
python -m venv .venv
or
py -m venv .venv

# Activate the virtual environment
source .venv/bin/activate   # (Linux/Mac)
.venv\Scripts\activate      # (Windows)

# Install the requirements
pip install -r requirements.txt

# Make sure your Python interpreter is using the virtual environment
Check IDE settings -> ProjectName -> Python Interpreter (make sure you are using the .venv)
