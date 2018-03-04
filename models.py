import json
import os
from datetime import date
from playhouse.db_url import connect
from playhouse.postgres_ext import *

db = connect(os.environ['DATABASE_URL'])


class Topic(Model):
    name = CharField()

    class Meta:
        database = db


class Task(Model):
    text = TextField()
    data = JSONField()
    topic = ForeignKeyField(Topic, on_delete='CASCADE', backref='tasks')
    available_at = DateField()
    due_to = DateField()

    class Meta:
        database = db


class Student(Model):
    user_id = IntegerField(null=True)
    name = CharField()
    group = IntegerField()
    invite_code = CharField(unique=True)
    on_task = ForeignKeyField(Task, null=True)
    on_stage = IntegerField(null=True)

    class Meta:
        database = db


class Submission(Model):
    student = ForeignKeyField(Student, on_delete='CASCADE', backref='submissions')
    task = ForeignKeyField(Task)
    answers = ArrayField(CharField)

    class Meta:
        database = db


def create_tables():
    Topic.create_table()
    Task.create_table()
    Student.create_table()
    Submission.create_table()

if __name__ == '__main__':
    # create_tables()
    Submission.create_table()
