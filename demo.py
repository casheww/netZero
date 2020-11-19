import db.interface

# and for demo purposes:
import json
import time


# initialise the database connection
db = db.interface.DataConnection()

# add a new organisation
org_id = db.add_organisation("exampleOrg", "example.org")
# add a new user to the organisation
user_id = db.add_user(org_id, "Jon", "hejon@example.org")

print(json.dumps(db.organisations, indent=4))
time.sleep(5)

# add 100 points to an organisation for planting 25 trees
db.change_organisation_points(org_id, 100)
# add 20 points to a user for biking into work instead of driving
db.change_user_points(user_id, 20)

print(json.dumps(db.organisations, indent=4))
time.sleep(5)

# delete the new organisation and its users from the database
db.del_organisation(org_id)

print(json.dumps(db.organisations, indent=4))
time.sleep(5)
