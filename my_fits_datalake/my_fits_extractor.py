from aws_cdk import (core, aws_s3 as s3, aws_lambda as lambda_,  aws_iam as iam_, aws_s3_notifications as s3_notifications) 
#from aws_cdk import aws_lambda_event_sources as ales
from aws_cdk import custom_resources as custom_resources_
from aws_cdk import aws_glue as glue_ 
from aws_cdk import aws_lakeformation as lakeformation_
import uuid

source_bucket_name = "jxu-fits-datalake"
glue_database_name = "fits_datalake"

class MyFitsExtractor(core.Stack):

    def __init__(self, scope: core.Construct, id: str):
        super().__init__(scope, id)

        # get the source bucket
        source_bucket = s3.Bucket.from_bucket_name(self, "MySourceBucket", bucket_name=source_bucket_name)

        # create the new destination bucket
        target_bucket = s3.Bucket(self, "FITSSTORE_BUCKET")

        #Add the astropy and numpy layers
        layer_astropy = lambda_.LayerVersion(self, 'AstroFitsioLayer', 
            code=lambda_.Code.from_asset("resources_layer/astropy.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_7]
        )
        # use an AWS provided layer for numpy
        layer_numpy = lambda_.LayerVersion.from_layer_version_arn(self, "NumpyLayer", "arn:aws:lambda:us-east-1:668099181075:layer:AWSLambda-Python37-SciPy1x:22")

        # create the FITS header extractor
        handler = lambda_.Function(self, "FITSHeaderExtractorHandler", 
                    runtime=lambda_.Runtime.PYTHON_3_7,
                    code=lambda_.Code.asset("resources"),
                    handler="fits_header_extractor.fits_header_extractor_handler",
                    environment=dict(
                        FITSSTORE_BUCKET=target_bucket.bucket_name
                    ),
                    layers=[layer_astropy, layer_numpy]
                )
        # grant read access to handler on source bucket
        source_bucket.grant_read(handler)
        # Give the lambda resource based policy 
        # both source_arn and source_account is needed for security reason
        handler.add_permission('s3-trigger-lambda-s3-invoke-function',
                              principal=iam_.ServicePrincipal('s3.amazonaws.com'),
                              action='lambda:InvokeFunction',
                              source_arn=source_bucket.bucket_arn,
                              source_account=self.account) 

        # grant access to the handler    - this is a lot easier than adding policies, but not all constructs support this
        target_bucket.grant_read_write(handler)


        # map the put event to hanlder - this doesn't work as source_bucket is not really a Bucket object (IBucketProxy)
        #notification = s3_notifications.LambdaDestination(handler)
        #source_bucket.add_object_created_notification(self, notification )

        # use custom resource to add an event trigger on the destnation bucket - 
        custom_s3_resource = custom_resources_.AwsCustomResource(self, 's3-putobject-custom-notification-resource',
            policy = custom_resources_.AwsCustomResourcePolicy.from_statements (
                [
                    iam_.PolicyStatement(
                        effect=iam_.Effect.ALLOW,
                        resources = ['*'],
                        actions=['s3:PutBucketNotification']
                    )
                ]
            ),
            on_create=custom_resources_.AwsSdkCall(
                service="S3",
                action="putBucketNotificationConfiguration",
                parameters={
                    "Bucket": source_bucket.bucket_name,
                    "NotificationConfiguration": {
                        "LambdaFunctionConfigurations": [
                            {
                                "Events": ['s3:ObjectCreated:*'],
                                "LambdaFunctionArn": handler.function_arn,
                                "Filter": {
                                    "Key": {
                                        "FilterRules": [
                                            {'Name': 'suffix',
                                            'Value': 'fits'}]
                                    }
                                }
                            }
                        ]
                    }
                },
                physical_resource_id=custom_resources_.PhysicalResourceId.of(
                    f's3-notification-resource-{str(uuid.uuid1())}'),region=self.region
                )
            )
        custom_s3_resource.node.add_dependency(handler.permissions_node.find_child('s3-trigger-lambda-s3-invoke-function'))
       
       
        # create a glue crawler to build the data catalog
        glue_role = iam_.Role(self, "glue_role", 
            assumed_by=iam_.ServicePrincipal('glue.amazonaws.com'),
            managed_policies= [iam_.ManagedPolicy.from_managed_policy_arn(self, 'MyFitsCrawlerGlueRole', managed_policy_arn='arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole')]
        )
        # glue role needs "*" read/write - otherwise crawler will not be able to create tables (and no error messages in crawler logs)
        glue_role.add_to_policy(iam_.PolicyStatement( actions=['s3:GetObject', 's3:PutObject', 'lakeformation:GetDataAccess'], effect=iam_.Effect.ALLOW, resources=['*']))
        
        # create a database in data catalog
        db=glue_.Database(self, "MyFitsDatabase", database_name=glue_database_name)
        crawler = glue_.CfnCrawler(self, "fits-datalake-crawler", 
            database_name= glue_database_name,
            role=glue_role.role_arn,
            targets={"s3Targets": [{"path":  target_bucket.bucket_name}]}, 
        )
        # in order for the crawler to run, we need to add some permissions to lakeformation

        #lake_setting = lakeformation_.CfnDataLakeSettings(self, "MyFitsDatalakeSetting")
        location_resource = lakeformation_.CfnResource(self, "MyFitsDatalakeLocationResource", 
                resource_arn= target_bucket.bucket_arn, 
                use_service_linked_role=True
        )
        lakeformation_.CfnPermissions(self, "MyFitsDatalakeDatabasePermission",
                data_lake_principal=lakeformation_.CfnPermissions.DataLakePrincipalProperty(data_lake_principal_identifier=glue_role.role_arn),
                resource=lakeformation_.CfnPermissions.ResourceProperty(database_resource=lakeformation_.CfnPermissions.DatabaseResourceProperty(name=db.database_name)),
                permissions=["ALTER", "DROP", "CREATE_TABLE"],
#                permissions_with_grant_option=["ALTER","CREATE_TABLE", "DROP"]
            )
        location_permission = lakeformation_.CfnPermissions(self, "MyFitsDatalakeLocationPermission",
                data_lake_principal=lakeformation_.CfnPermissions.DataLakePrincipalProperty(data_lake_principal_identifier=glue_role.role_arn),
                resource=lakeformation_.CfnPermissions.ResourceProperty(data_location_resource=lakeformation_.CfnPermissions.DataLocationResourceProperty(s3_resource=target_bucket.bucket_arn)),
                permissions=["DATA_LOCATION_ACCESS"],
            )
        location_permission.node.add_dependency(location_resource)
        