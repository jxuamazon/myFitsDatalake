#!/usr/bin/env python3

from aws_cdk import core

from my_fits_datalake.my_fits_datalake_stack import MyFitsDatalakeStack


app = core.App()
MyFitsDatalakeStack(app, "my-fits-datalake")

app.synth()
