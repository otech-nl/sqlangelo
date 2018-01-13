from tests.models import db, Group, Company, Employee

########################################

db.drop_all()
db.create_all()


########################################

office = Group.create(abbr='Off')
rd = Group.create(abbr='R&D')
otech = Company.create(name='OTech BV')
steets = Employee.create(email='steets@otech.nl', company=otech)
secr = Employee.create(email='office@otech.nl', company=otech)
secr.groups.append(office)
steets.groups.append(rd)

print(otech)
