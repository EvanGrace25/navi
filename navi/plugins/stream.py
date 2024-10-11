import click
from flask import Flask, jsonify, request
from flasgger import Swagger
from .dbconfig import new_db_connection
from .database import db_query
import os
import subprocess
from .find import exploit

#Sample data
items = [
    {'id':1,'name':'Item 1'},
    {'id':2,'name':'Item 2'},
    {'id':3,'name':'Item 3'}
]

#More Sample Data
food = [
    {'name':'hot dog'},
    {'name':'corn dog'},
    {'name':'hamburger'},
    {'name':'lasagna'}
]

@click.group(help="Start a Rest API Service so that a different device can pull data for a dashboard")
def stream():
    pass


@stream.command(help="Start the API Service on port 5000, or designate your own port with the --port option")
@click.option("--port", default=5000, help="Specify what port you want the API to run on. The default port is 5000. You need elevated privileges to run it on a port at 1024 or below. Choose a port above that.")
def startapiservice(port):
    app = Flask(__name__)
    swagger = Swagger(app)
    #Sample data
    items = [
        {'id':1,'name':'Item 1'},
        {'id':2,'name':'Item 2'},
        {'id':3,'name':'Item 3'}
    ]

    database = r'navi.db'
    new_conn = new_db_connection(database)
    
    # GET endpoint to retrieve data (items_)
    @app.route('/items',methods=['GET'])
    def get_items():
        return jsonify(items)

    # GET endpoint to retrieve food data
    @app.route('/food',methods=['GET'])
    def get_food():
        return jsonify(food)

    #GET endpoint to retrieve number of exploitable assets
    @app.route('/exploitable_assets',methods=['GET'])
    def get_exploitable_assets():
        plugin_data = db_query("SELECT asset_uuid from vulns LEFT JOIN"
                           " assets ON asset_uuid = uuid where exploit = 'True';")
        asset_count = len(set(plugin_data))
        return f"{asset_count}"

    #GET endpoint to retrieve number of exploitable vulnerabilities
    @app.route('/exploitable_vulns',methods=['GET'])
    def get_exploitable_vulns():
        plugin_data = db_query("SELECT asset_uuid from vulns LEFT JOIN"
                           " assets ON asset_uuid = uuid where exploit = 'True';")
        vuln_count = len(plugin_data)
        return f"{vuln_count}"

    #GET endpoint to retrieve number of total assets
    @app.route('/total_assets',methods=['GET'])
    def get_total_assets():
        plugin_data = db_query("SELECT asset_uuid from vulns LEFT JOIN"
                           " assets ON asset_uuid = uuid;")
        asset_count = len(set(plugin_data))
        return f"{asset_count}"

    #POST endpoint to update database
    @app.route('/update_db',methods=['POST'])
    def update_db():
        command = "navi update full"
        try:
            result = subprocess.check_output(command, shell=True, text=True)
        except subprocess.CalledProcessError as e:
            result = f"Error executing command: {e}"

        return result

    print(f"Starting API on port {port}...")
    app.run(port=port, debug=True)

