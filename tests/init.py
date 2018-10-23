''' creates a test database '''
from tests.models import db, Group, Company, Employee
from faker import Faker

########################################

fake = Faker()
db.drop_all()
db.create_all()


########################################

GROUP1 = Group.create(abbr='HRM')
GROUP2 = Group.create(abbr='R&D')
COMPANY = Company.create(name=fake.company())
PERSON1 = Employee.create(email=fake.simple_profile()['mail'], company=COMPANY)
PERSON2 = Employee.create(email=fake.simple_profile()['mail'], company=COMPANY)
PERSON1.groups.append(GROUP1)
PERSON2.groups.append(GROUP2)

print(COMPANY)
