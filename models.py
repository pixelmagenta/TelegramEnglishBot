from peewee import *

db = SqliteDatabase('students.db')

class Student(Model):
    user_id = IntegerField(null=True)
    name = CharField()
    invite_code = CharField(unique=True)

class Meta:
        database = db

def create_tables():
    Student.create_table()

def create_users():
    Student.create(name='Eugenia', invite_code='ABC123')
    Student.create(name='Anna', invite_code='321CBA')

if __name__ == '__main__':
    create_tables()
    create_users()