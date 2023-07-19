import boto3
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

s3 = boto3.client('s3')


def generate_and_save_plot(pdf_pages, data, x, y, title, hue=None, style=None, bar_plot= False):
    plt.figure(figsize=(12, 8))
    if bar_plot:
        sns.barplot(data=data, x=x, y=y, hue=hue)
    else:
        sns.lineplot(data=data, x=x, y=y, hue=hue, style=style)
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.tight_layout()
    pdf_pages.savefig(bbox_inches='tight')
    plt.close()


def analyse_and_plot_to_pdfs(file_name, data):
    if file_name == "transformed_economy_data.csv":
        economy_data_pdf = PdfPages('economy_data_summary.pdf')
        generate_and_save_plot(pdf_pages=economy_data_pdf, data=data, x='Year', y='Total', title='Total Percentage Change in Consumer Prices')
        economy_data_pdf.close()
        return "economy_data_summary.pdf"

    elif file_name == "transformed_income_data.csv":
        data = data.drop(columns=["Unnamed: 0"])
        income_data_melted = data.melt(id_vars='Income source', var_name='Year and Gender', value_name='Income')
        income_data_melted[['Year', 'Gender']] = income_data_melted['Year and Gender'].str.split(' ', n=1, expand=True)
        income_data_melted['Year'] = income_data_melted['Year'].astype(int)
        average_income = income_data_melted.groupby(['Year', 'Gender', 'Income source'], as_index=False)[
            'Income'].mean()

        income_data_pdf = PdfPages('income_data_summary.pdf')

        generate_and_save_plot(pdf_pages=income_data_pdf, data=average_income, x='Year', y='Income',
                               title='Income Trends by Source and Gender',
                               hue='Income source', style='Gender')

        generate_and_save_plot(pdf_pages=income_data_pdf, data=income_data_melted, x='Year', y='Income',
                           title='Income Trends by Gender', hue='Gender')
        income_data_pdf.close()
        return "income_data_summary.pdf"

    elif file_name == "transformed_employment_data.csv":
        employment_data_pdf = PdfPages('employment_data_summary.pdf')

        data['Year'] = data['Year'].astype(int)
        average_earnings_over_years = data.groupby(['Year', 'Major group of occupation'], as_index=False)[
            'Average gross monthly earnings'].mean()
        generate_and_save_plot(employment_data_pdf, average_earnings_over_years, x='Year',
                               y='Average gross monthly earnings',
                               title='Average Gross Monthly Earnings by Major Group of Occupation Over the Years', hue='Major group of occupation')

        generate_and_save_plot(employment_data_pdf, data, x='Average gross monthly earnings',
                               y='Major group of occupation',
                               title='Average Gross Monthly Earnings by Major Group of Occupation', hue='Sex',
                               bar_plot=True)
        employment_data_pdf.close()
        return "employment_data_summary.pdf"

    elif file_name == "transformed_education_data.csv":
        education_data_pdf = PdfPages('education_data_summary.pdf')
        generate_and_save_plot(education_data_pdf, data, x='Year',
                               y='People Count', title='Total Count of People by Type and Level of Education', hue='Type and level of education')

        return "education_data_summary.pdf"


def lambda_handler(_event=None, _context=None):
    bucket = 'estonia-silver'
    transformed_csv_files = ['transformed_economy_data.csv', 'transformed_income_data.csv',
                             'transformed_employment_data.csv', 'transformed_education_data.csv']

    for file in transformed_csv_files:
        try:
            response = s3.get_object(Bucket=bucket, Key=file)
            data = pd.read_csv(BytesIO(response['Body'].read()))
            pdf_filename = analyse_and_plot_to_pdfs(file, data)
            s3.upload_file(pdf_filename, 'estonia-gold', f'summary_from {pdf_filename}')
            print(f"Successfully analysed {file} and saved the pdf")

        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
