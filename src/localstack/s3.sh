#!/bin/sh
echo "Init localstack s3"
# bucket to store imagery data
# can be used to store initial imagery
awslocal s3 mb s3://fashion-datasets
# bucket to store tasks results
awslocal s3 mb s3://fashion-tasks

#awslocal s3 sync /tmp/localstack/dataset s3://fashion-datasets/dataset-v1