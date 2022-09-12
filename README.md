# vodwatch_backend

## Installation
Clone the vodwatch_backend repository from https://github.com/vodwatch/vodwatch_backend.git, and open the project directory in the terminal. Use the `pip install -r requirements.txt` command.

## How to run code?
Open the project directory in the terminal and run the `python src/main.py` command to run the application locally. To run the application on Heroku server, use the `heroku create` command to create a new Heroku app, and then use the `git push heroku main` command to push the code to the Heroku server. Than run the `heroku ps:scale web=1` command. To see the logs, use the `heroku logs --tail` command. 

The server will be running on the `https://vodwatch-backend.herokuapp.com` URL.

## How to run tests?
Open the project directory in two terminals. In the first, run the server with the `python src/main.py` command, and in the second, run the tests with the `pytest` or `python -m pytest` command. This command will run all test files. To run a specific test file, use `pytest file_name.py`, and to run a specific test, use `pytest file_name.py::test_name`.
