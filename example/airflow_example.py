import airflow
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from datetime import timedelta
from airflow.utils.dates import days_ago


def my_func():
    print('welcome to Dezyre')
    return 'welcome to Dezyre'


args = {
    'owner': 'airflow',    
        #'start_date': airflow.utils.dates.days_ago(2),
        # 'end_date': datetime(),
        # 'depends_on_past': False,
        #'email': ['airflow@example.com'],
        #'email_on_failure': False,
        #'email_on_retry': False,
        # If a task fails, retry it once after waiting
        # at least 5 minutes
        #'retries': 1,
        'retry_delay': timedelta(minutes=5),}



dag_python = DAG(
    dag_id = "pythonoperator_demo",
	default_args=args,
	# schedule_interval='0 0 * * *',
	schedule_interval='@once',	
	dagrun_timeout=timedelta(minutes=60),
	description='use case of python operator in airflow',
	start_date = airflow.utils.dates.days_ago(1))

dummy_task = EmptyOperator(task_id='dummy_task', retries=3, dag=dag_python)
python_task = PythonOperator(task_id='python_task', python_callable=my_func, dag=dag_python)



dummy_task >> python_task

if __name__ == "__main__":
    dag_python.cli()