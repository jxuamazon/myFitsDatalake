#!/usr/bin/env python3

from aws_cdk import core

from my_fits_datalake.my_fits_datalake_stack import MyFitsDatalakeStack

source_bucket_name = "jxu-fits-datalake"
glue_database_name = "fits_datalake"

app = core.App()

MyFitsDatalakeStack(app, "my-fits-datalake", source_bucket_name=source_bucket_name, glue_database_name=glue_database_name)

app.synth()
