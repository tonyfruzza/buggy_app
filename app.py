import os
import os.path
import boto3
from os.path import exists
from flask import Flask, render_template, request, redirect, send_file
from werkzeug.utils import secure_filename
import cryptocode
import pymysql
from pymysql.constants import CLIENT

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"

@app.route("/")
def home():
    return render_template('index.html', d=check_for_actions_completed())

def check_for_actions_completed():
    data_set = {
        "pico_symlink_created": os.path.islink('/usr/bin/pico'),
        "file_is_uploaded": check_for_upload()/1024/1024 > 1,
        "touch_me_exists": exists('/tmp/me'),
        "parameter_value": read_parameter_secret("/top/training/the_secret_thing"),
        "decoded_value": cryptocode.decrypt(read_parameter_secret("/top/training/the_secret_thing"), get_account_id()),
        "rds_endpoint": get_cfn_output('top-training-rds-instance', 'RdsDatabaseInstance'),
        "rds_login": get_cfn_output('top-training-rds-instance', 'RdsMasterUsername'),
        "age_checked": check_age()
    }
    return data_set

def check_age():
    conn = pymysql.connect(host=get_cfn_output('top-training-rds-instance', 'RdsDatabaseInstance'),
                           port=3306,
                           user='root',
                           passwd=read_parameter_secret('/top/training/rds_password'),
                           database='backtothefutureparody',
                           client_flag=CLIENT.MULTI_STATEMENTS
                           )
    cursor = conn.cursor()
    cursor.execute('select name, age, true from characters where name="Rick Sanchez" and age = 70')
    ret = cursor.fetchone()
    return ret != None

def get_cfn_output(stack, output):
    cfn = boto3.client('cloudformation', region_name="us-west-1")
    ret = cfn.describe_stacks(StackName=stack)
    for out in ret['Stacks'][0]['Outputs']:
        if out['OutputKey'] == output:
            return out['OutputValue']
    return Null

def check_for_upload():
    size = 0
    for path, dirs, files in os.walk(UPLOAD_FOLDER):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size
def read_parameter_secret(ps_key_name):
    ssm_client = boto3.client('ssm', region_name="us-west-1")
    res = ssm_client.get_parameter(Name=ps_key_name, WithDecryption=True)
    return str(res['Parameter']['Value'])

def get_account_id():
    sts_client = boto3.client('sts', region_name="us-west-1")
    res = sts_client.get_caller_identity()
    return str(res['Account'])

@app.route("/upload", methods=['POST'])
def upload():
    if request.method == "POST":
        f = request.files['file']
        f.save(os.path.join(UPLOAD_FOLDER, secure_filename(f.filename)))
        return redirect("/")

@app.route("/health")
def health_check():
    checks_ret = check_for_actions_completed()
    if checks_ret['pico_symlink_created'] and checks_ret['file_is_uploaded'] and checks_ret['touch_me_exists']:
        return("OKAY")
    else:
        return("FATAL", 500)


@app.route("/debug")
def debugger():
    if 'elb.amazonaws.com' not in  request.headers['Host']:
       return "Failure to use Load balancer."
    return "<pre>Hello"

if __name__ == '__main__':
    app.run(debug=True)
