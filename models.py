import json
from datetime import date
from playhouse.postgres_ext import *

db = PostgresqlExtDatabase('telegrambotdb', user='pixelmagenta', register_hstore=False)


class Student(Model):
    user_id = IntegerField(null=True)
    name = CharField()
    invite_code = CharField(unique=True)

    class Meta:
        database = db


class Task(Model):
    text = TextField()
    data = JSONField()
    available_at = DateField()
    due_to = DateField()

    class Meta:
        database = db


def create_tables():
    Student.create_table()
    Task.create_table()

def create_task():
    with open('text_ex1.json', 'r') as file:
        data = json.loads(file.read())

    with open('text_ex1.json', 'r') as file:
        text = open('text1.txt', 'r').read()
   
    Task.create(text=text, data=data, available_at=date(2018, 2, 14), due_to=date(2018, 2, 24))


def create_users():
    Student.create(name='Eugenia', invite_code='ABC123')
    Student.create(name='Anna', invite_code='321CBA')

if __name__ == '__main__':
    create_tables()
    create_users()
    create_task()
