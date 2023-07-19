# socioeconomic-trends-estonia

This is a simple task to analyse socioeconomic trends in Estonia and using AWS Lambda and S3 to perform some transformations and storing result files.

I chose 4 datasets from https://andmed.stat.ee/en/stat.

The datasets I picked are:
1. ST07 : Disposable income per household member in a month by source of income, year and sex
2. HTG03: Enrollment in formal education by type and level of education and year
3. PA621: Gross monthly earnings of full time employees by Year, Major group of
occupation and Indicator
4. IA001: Consumer price index by Year and Commodity group


## Installation And Set Up

I followed the steps for creating a new AWS account.

1. Created an account on https://aws.amazon.com
2. Signed up as root user and after that added 2FA with Google Authenticator
3. Created user group and roles for myself and for this assignment and added necessary
permissions to access S3 and AWS Lambda

And installed AWS CLI locally. I pulled the docker image using

`docker pull bitnami/aws-cli:latest`

I exported some environment variables as follows, for the region I set up `eu-north-1` as it is the closest to where I am located.

`export AWS_ACCESS_KEY_ID

export AWS_SECRET_ACCESS_KEY

export AWS_DEFAULT_REGION`

## Setting up S3 Buckets

Once my account and CLI was set up, I created S3 buckets, I created 3 buckets

- estonia-bronze
- estonia-silver
- estonia-gold

named buckets with the following CLI commands.

 - `docker run --rm -it -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY
 -e AWS_DEFAULT_REGION bitnami/aws-cli:latest s3 mb
 s3://estonia-bronze`

 -` docker run --rm -it -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY
 -e AWS_DEFAULT_REGION bitnami/aws-cli:latest s3 mb
 s3://estonia-silver`

 - `docker run --rm -it -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY
 -e AWS_DEFAULT_REGION bitnami/aws-cli:latest s3 mb
 s3://estonia-gold`


I ran into some errors like “failed: s3://estonia-bronze An error occurred (AccessDenied)” but I fixed them by managing security settings in the AWS management console.


## Transformation Logic: Moving Data from Bronze to Silver Bucket


After making sure all the files are present in S3 bucket estonia-bronze, I wrote the transformation logic to clean up and process the data before moving it to estonia-silver The script can be found here.


Some of the transformations and logic reasoning for :
- economy_data.csv: Converted columns values to numeric values for analysis in later stage
- income_data.csv: The csv file had columns for both income source and gender in Estonian language, I used google translate to translate them to English and made necessary replace statements within the code using Pandas.
- employment_data.csv : Some columns were not numeric but it was needed to convert them to numeric values for further analysis
- education_data.csv: This csv file had a couple of issues including ‘Unnamed’ columns, null as well as non numeric values, so the transformation logic fixed that.


Once transformations are done, the data is moved to another bucket with lambda_handler code that is also present in the same script.


The steps done in CLI for moving data and invoking lambda function are:

1. Created a dependencies folder including the processing and transform script and uploaded that to S3 with the following commands and steps
a. mkdir transform
b. cd transform
c. copied process_and_transform.py file here and made sure it's in the root level
d. pip install boto3 pandas -t .
e. cd..
f. zip -r transform.zip transform

2. Uploaded the transform.zip file to S3
aws s3 cp transform.zip s3://estonia-bronze/

3. Created a lambda function called ProcessAndTransform and used Lambda handler from the processing script
`aws lambda create-function \
--function-name ProcessAndTransform \
--runtime python3.8 \
--role arn:aws:iam::my-account-id:role/my-role \
--handler process_and_transform.lambda_handler \
--code S3Bucket="estonia-bronze",S3Key="transform.zip" \
--timeout 900 \
--memory-size 1024
`
4. Invoked the lambda function with

`aws lambda invoke \
  --function-name ProcessAndTransform \
  --region eu-north-1 \
  logs.txt
`

In the process I had to manage some permissions and policies to add trusted relationships.

After following these steps, I had my transferred files in the second bucket. The transformed files from estonia-silver bucket can be found here.


## Summary Logic: Moving Data from Silver to Gold Bucket


Finally I wrote an analysis script that can be found in scripts/analysis.py and ran it using following commands:


- Created a dependencies folder including analysis script
    - mkdir  analysis_dir
    - cd analysis_dir
    - copied analysis.py file here and made sure it's in the root level
    - pip install boto3 pandas seaborn matplotlib -t .
    - cd ..
    - zip -r analysis_dir.zip analysis_dir

- Created Lambda function
`    aws lambda create-function --function-name AnalyseEstoniaData \
    --runtime python3.8 --role arn:aws:iam::my-account-id:role/service-role/my-role \
    --zip-file fileb://analysis_dir.zip --handler analysis.lambda_handler
`


- Invoke Lambda Function

   ` aws lambda invoke --function-name AnalyseEstoniaData --invocation-type Event silver_to_gold_layer_logs.txt`




Talking about the summaries itself, the code performs some analysis and plots them based on the transformed csv files. The helper function `generate_and_save_plot` is written to avoid repeating the same lines of code and creating plots based on request params.

All the plots and pdf files can be found in `summary_pds`.


Some of the summaries derived from the data are as follows:

- Total Percentage Change in Consumer Prices over Years
- Income Trends by Source and Gender
- Income Trends by Gender
- Average Gross Monthly Earnings by Major Group of Occupation Over the Years(Line Plot)
- Average Gross Monthly Earnings by Major Group of Occupation(Bar plot)
- Total Count of People by Type and Level of Education



## Future Possible Work

There is more than can be done to expand on this task. Below are some points I can think of right away:

- Setting up cron jobs or processes to fetch latest data from the APIs and website in a timely manner and ingesting it in S3 buckets automatically

- Using AWS EMR as the data volume will increase over time and we want more robust
operations

- We can write a script with the set of commands to run in terminal instead of running the commands one by one

- We can also use Lambda Layers to manage dependencies for the Lambda functions

- For Analysis, we can gather more insights in terms of numbers and percentages along with more plots and charts

- We can also expand the project idea more with including more data files and finding more trends in Estonia on top of the socioeconomic trends that we already did

