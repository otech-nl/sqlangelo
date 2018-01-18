from tests.models import db, Group, Company, Employee

########################################

db.drop_all()
db.create_all()


########################################

hrm = Group.create(abbr='HRM')
rd = Group.create(abbr='R&D')
otech = Company.create(name='OTech BV')
steets = Employee.create(email='steets@otech.nl', company=otech)
secr = Employee.create(email='office@otech.nl', company=otech)
secr.groups.append(hrm)
steets.groups.append(rd)

print(otech)
