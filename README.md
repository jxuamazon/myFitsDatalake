
# Welcome to FITS Data lake project. 

This project is built with AWS CDK with Python

## About CDK

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the .env
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!


## FIT Datalake Project

![](images/science_datalake.png)

```
$ mkdir resoures_layer
$ mkdir python
$ pip install aws_cdk.aws_lambda aws_cdk.aws_s3
$ pip install astropy --target python
$ zip -r9 resources_layer/astropy.zip python
```
use resources_layer/astropy.zip to create a new later

Astropy depends on Numpy package, furtunately AWS has a public layer available (arn:aws:lambda:us-east-1:668099181075:layer:AWSLambda-Python37-SciPy1x:22)

```
$ cdk list # list stacks
$ cdk deploy  myfitsdatalakeFitsExtractor64052F10 -y
```
