from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.operators.email_operator import EmailOperator

from datacleaner import data_cleaner

yesterday_date = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')

default_args = {
    'owner': 'Airflow',
    'start_date': datetime(2023, 6, 17),
    'retries': 1,
    'retry_delay': timedelta(seconds=5)
}

# template_searchpath, set the path for in a DAG
with DAG('store_dag', default_args=default_args, schedule_interval='@daily', template_searchpath=['/usr/local/airflow/sql_files'], catchup=True) as dag:

    t1=BashOperator(task_id='check_file_exists', bash_command='shasum ~/store_files_airflow/raw_store_transactions.csv', retries=1, retry_delay=timedelta(seconds=10))
        # shasum will only return a shasum value if the file exists, otherwise: an error
        # ~ represents Airflow home path
 
    t2 = PythonOperator(task_id='clean_raw_csv', python_callable=data_cleaner)

    # Before running this task we have to create connection to MySQL, hostname, port,login pass
    # Admin > connections > create
    t3 = MySqlOperator(task_id='create_mysql_table', mysql_conn_id="mysql_conn", sql="create_table.sql") # creat connections (mysql_conn) in UI

    t4 = MySqlOperator(task_id='insert_into_table', mysql_conn_id="mysql_conn", sql="insert_into_table.sql")

    t5 = MySqlOperator(task_id='select_from_table', mysql_conn_id="mysql_conn", sql="select_from_table.sql")
    
    # rename the files
    t6 = BashOperator(task_id='move_file1', bash_command='cat ~/store_files_airflow/location_wise_profit.csv && mv ~/store_files_airflow/location_wise_profit.csv ~/store_files_airflow/location_wise_profit_%s.csv' % yesterday_date)

    t7 = BashOperator(task_id='move_file2', bash_command='cat ~/store_files_airflow/store_wise_profit.csv && mv ~/store_files_airflow/store_wise_profit.csv ~/store_files_airflow/store_wise_profit_%s.csv' % yesterday_date)

    # t8 = EmailOperator(task_id='send_email',
    #     to='adelhany1234@gmail.com',
    #     subject='Daily report generated',
    #     html_content=""" <h1>My store reports are ready :D.</h1> """,
    #     files=['/usr/local/airflow/store_files_airflow/location_wise_profit_%s.csv' % yesterday_date,
    #             '/usr/local/airflow/store_files_airflow/store_wise_profit_%s.csv' % yesterday_date] )

    t9 = BashOperator(task_id='rename_raw', bash_command='mv ~/store_files_airflow/raw_store_transactions.csv ~/store_files_airflow/raw_store_transactions_%s.csv' % yesterday_date)

    #t1 >> t2 >> t3 >> t4 >> t5 >> [t6,t7] >> t8 >> t9
    t1 >> t2 >> t3 >> t4 >> t5 >> [t6,t7] >> t9