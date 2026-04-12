#!/bin/bash
set -e
BASE=http://localhost:3001

ID=$(curl -s -X POST $BASE/estimates/my_estimate | jq -r .estimation_id)
echo "Estimate ID: $ID"

add() {
  local group=$1 service=$2 instance=$3 data=$4
  local url="$BASE/estimates/$ID/services/$service${instance:+/$instance}?group=$group"
  curl -s -X PUT "$url" -H 'Content-Type: application/json' -d "$data" | jq -r '.success'
}

# ============================================================
# PROD (100%)
# ============================================================
echo "Adding Prod services..."

add Prod amazonPersonalize MLModel '{
  "region":"eu-west-1","description":"ML Model",
  "Average_amount_of_data_ingested":{"value":"8","unit":"gb|month"},
  "Average_Training_hours_per_month":"128",
  "Number_of_recommendation_for_batch":"1200000",
  "Tps_hours_for_real_time":"4500000"
}'

add Prod amazonApiGateway GetRecommendations '{
  "region":"eu-west-1","description":"GetRecommendations",
  "RESTMult":"1000000","numberOfRESTRequests":{"value":"4.5","unit":"perMonth"},
  "cacheSize":"[ZERO_COST]"
}'

add Prod amazonApiGateway PutUser '{
  "region":"eu-west-1","description":"PutUser",
  "RESTMult":"1000000","numberOfRESTRequests":{"value":"4.5","unit":"perMonth"},
  "cacheSize":"[ZERO_COST]"
}'

add Prod amazonApiGateway PutEvent '{
  "region":"eu-west-1","description":"PutEvent",
  "RESTMult":"1000000","numberOfRESTRequests":{"value":"9","unit":"perMonth"},
  "cacheSize":"[ZERO_COST]"
}'

add Prod aWSLambda Compute '{
  "region":"eu-west-1","description":"Compute",
  "selectArchitectureRequests":"2","selectArchitectureConcurrency":"2",
  "lambdaFunctionIncludeFreeTier_lambdaInvokeMode":"0",
  "numberOfRequests":{"value":"19","unit":"millionPerMonth"},
  "durationOfEachRequest":"1000",
  "sizeOfMemoryAllocated":{"value":"512","unit":"mb|NA"},
  "storageAmountEphemeral":{"value":"512","unit":"mb|NA"}
}'

add Prod AmazonCloudWatch Logs '{
  "region":"eu-west-1","description":"Logs",
  "totalNumberOfMetrics":"10",
  "sizeOfStandardLogsDataIngested":{"value":"10","unit":"gb|NA"},
  "numberOfLambdaFunctions":"3",
  "numberOfLambdaInvokes":{"value":"1000","unit":"perHour"},
  "numberOfDashboards":"3"
}'

add Prod awsEtlJobsAndDevelopmentEndpoints GlueETL '{
  "region":"eu-west-1","description":"Glue ETL",
  "numberOfDPUsForPythonShell":"4",
  "durationForPythonShellJob":{"value":"960","unit":"min"}
}'

add Prod standardTopics SNS '{
  "region":"eu-west-1","description":"SNS",
  "numberOfRequests":{"value":"1","unit":"millionPerMonth"},
  "numberOfHTTPNotifications":{"value":"1","unit":"millionPerMonth"}
}'

add Prod amazonSimpleQueueService SQS '{
  "region":"eu-west-1","description":"SQS",
  "standardQueueRequests":{"value":"1","unit":"perMonth"}
}'

add Prod sageMakerOnDemandNotebookInstances Notebook '{
  "region":"eu-west-1","description":"Notebook",
  "DataScientistsPerMonth":"1",
  "NotebooksPerMonth":"1",
  "NotebookHrsPerDay":"1",
  "NotebookDaysPerMonth":"20",
  "columnFormIPM":{"value":"ml.t3.medium","type":"autoSuggest"},
  "SM_storageType":"General Purpose",
  "SM_storageAmount":{"value":"5","unit":"gb|NA"}
}'

add Prod stepFunctionStandard StepFunctions '{
  "region":"eu-west-1","description":"Step Functions",
  "numberOfExecutions":{"value":"10","unit":"perMonth"},
  "stateTransition":"10"
}'

add Prod amazonS3 Storage '{
  "region":"eu-west-1","description":"S3 Storage",
  "s3Services_generated_0":{"value":"1","unit":"tb|NA"},
  "s3Services_generated_1":"10000",
  "s3Services_generated_2":"100000"
}'

# ============================================================
# DEV (20%)
# ============================================================
echo "Adding Dev services..."

add Dev amazonPersonalize MLModel '{
  "region":"eu-west-1","description":"ML Model",
  "Average_amount_of_data_ingested":{"value":"1.6","unit":"gb|month"},
  "Average_Training_hours_per_month":"26",
  "Number_of_recommendation_for_batch":"240000",
  "Tps_hours_for_real_time":"900000"
}'

add Dev amazonApiGateway GetRecommendations '{
  "region":"eu-west-1","description":"GetRecommendations",
  "RESTMult":"1000000","numberOfRESTRequests":{"value":"0.9","unit":"perMonth"},
  "cacheSize":"[ZERO_COST]"
}'

add Dev amazonApiGateway PutUser '{
  "region":"eu-west-1","description":"PutUser",
  "RESTMult":"1000000","numberOfRESTRequests":{"value":"0.9","unit":"perMonth"},
  "cacheSize":"[ZERO_COST]"
}'

add Dev amazonApiGateway PutEvent '{
  "region":"eu-west-1","description":"PutEvent",
  "RESTMult":"1000000","numberOfRESTRequests":{"value":"1.8","unit":"perMonth"},
  "cacheSize":"[ZERO_COST]"
}'

add Dev aWSLambda Compute '{
  "region":"eu-west-1","description":"Compute",
  "selectArchitectureRequests":"2","selectArchitectureConcurrency":"2",
  "lambdaFunctionIncludeFreeTier_lambdaInvokeMode":"0",
  "numberOfRequests":{"value":"3.8","unit":"millionPerMonth"},
  "durationOfEachRequest":"1000",
  "sizeOfMemoryAllocated":{"value":"512","unit":"mb|NA"},
  "storageAmountEphemeral":{"value":"512","unit":"mb|NA"}
}'

add Dev AmazonCloudWatch Logs '{
  "region":"eu-west-1","description":"Logs",
  "totalNumberOfMetrics":"10",
  "sizeOfStandardLogsDataIngested":{"value":"2","unit":"gb|NA"},
  "numberOfLambdaFunctions":"3",
  "numberOfLambdaInvokes":{"value":"200","unit":"perHour"},
  "numberOfDashboards":"3"
}'

add Dev awsEtlJobsAndDevelopmentEndpoints GlueETL '{
  "region":"eu-west-1","description":"Glue ETL",
  "numberOfDPUsForPythonShell":"4",
  "durationForPythonShellJob":{"value":"192","unit":"min"}
}'

add Dev standardTopics SNS '{
  "region":"eu-west-1","description":"SNS",
  "numberOfRequests":{"value":"200000","unit":"perMonth"},
  "numberOfHTTPNotifications":{"value":"200000","unit":"perMonth"}
}'

add Dev amazonSimpleQueueService SQS '{
  "region":"eu-west-1","description":"SQS",
  "standardQueueRequests":{"value":"0.2","unit":"perMonth"}
}'

add Dev sageMakerOnDemandNotebookInstances Notebook '{
  "region":"eu-west-1","description":"Notebook",
  "DataScientistsPerMonth":"1",
  "NotebooksPerMonth":"1",
  "NotebookHrsPerDay":"1",
  "NotebookDaysPerMonth":"4",
  "columnFormIPM":{"value":"ml.t3.medium","type":"autoSuggest"},
  "SM_storageType":"General Purpose",
  "SM_storageAmount":{"value":"5","unit":"gb|NA"}
}'

add Dev stepFunctionStandard StepFunctions '{
  "region":"eu-west-1","description":"Step Functions",
  "numberOfExecutions":{"value":"2","unit":"perMonth"},
  "stateTransition":"10"
}'

add Dev amazonS3 Storage '{
  "region":"eu-west-1","description":"S3 Storage",
  "s3Services_generated_0":{"value":"200","unit":"gb|NA"},
  "s3Services_generated_1":"2000",
  "s3Services_generated_2":"20000"
}'

# ============================================================
echo ""
echo "=== Generating shareable URL ==="
curl -s "$BASE/estimates/$ID?type=sharable_url" | jq .
