import boto3
import pandas as pd
from io import StringIO
from botocore.vendored import requests

s3 = boto3.client('s3')


def transform_data(file_name, data):
    if file_name == "economy_data.csv":
        for col in data.columns[1:]:
            data[col] = pd.to_numeric(data[col], errors='coerce')

    elif file_name == "income_data.csv":
        data.rename(columns={data.columns[0]: "Income source"}, inplace=True)
        income_source_translation = {
            "Sissetulekuallikas": "Income source",
            "Netosissetulek kokku": "Net income total",
            "Sissetulek palgatööst": "Income from paid work",
            "Tulu individuaalsest töisest tegevusest": "Income from individual work activities",
            "Omanditulu": "Ownership income",
            "Siirded": "Transfers",
            "..pension": "pension",
            "..lapsetoetus": "child support",
            "Muu sissetulek": "Other income",
            "Mitterahaline sissetulek": "Non-monetary income"
        }
        data['Income source'] = data['Income source'].replace(income_source_translation)
        gender_translation = {
            "Mehed ja naised": "Males and Females",
            "Mehed": "Males",
            "Naised": "Females"
        }

        data.columns = data.columns.to_series().replace(gender_translation, regex=True)

    elif file_name == "employment_data.csv":
        for col in data.columns[3:]:
            data[col] = pd.to_numeric(data[col], errors='coerce')

    elif file_name == "education_data.csv":
        data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
        data = data.melt(id_vars='Type and level of education', var_name='Year',
                                             value_name='People Count')
        data['Year'] = pd.to_numeric(data['Year'], errors='coerce')
        data['People Count'] = pd.to_numeric(data['People Count'], errors='coerce')
        data = data.dropna(subset=['People Count'])

    return data


def lambda_handler(_event=None, _context=None):
    bucket = 'estonia-bronze'
    csv_files = ['economy_data.csv', 'income_data.csv', 'employment_data.csv', 'education_data.csv']

    for file in csv_files:
        try:
            response = s3.get_object(Bucket=bucket, Key=file)
            data = pd.read_csv(response['Body'])

            transformed_data = transform_data(file, data)
            csv_buffer = StringIO()
            transformed_data.to_csv(csv_buffer)
            s3.put_object(Body=csv_buffer.getvalue(), Bucket='estonia-silver', Key=f'transformed_{file}')
            print(f"Successfully transformed and saved {file}")

        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
