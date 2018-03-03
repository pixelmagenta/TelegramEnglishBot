import json
import os
from datetime import date
from playhouse.db_url import connect

db = connect(os.environ.get['DATABASE'])


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
    data = JSONField()

    class Meta:
        database = db


def create_tables():
    Topic.create_table()
    Task.create_table()
    Student.create_table()
    Submission.create_table()

def create_users():
    Student.create(name='Eugenia', group=151, invite_code='ABC123')
    Student.create(name='Anna', group=151, invite_code='321CBA')

if __name__ == '__main__':
    create_tables()
    create_users()
