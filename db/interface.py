import sqlite3
from typing import Tuple

"""
Code for database handling. We used SQLite here for quick set up,
but postgres would be a more stable and faster in production.
https://xkcd.com/327/ 
"""


class DataConnection:
    def __init__(self):
        self.leaderboard_connection = sqlite3.connect("db/leaderboards.db")
        self.organisations = {}
        self.total_user_count = 0

        self._cache_data()

    def _cache_data(self):
        """
        Caches the leaderboard data to a dict for faster response.
        """
        c = self.leaderboard_connection.cursor()
        c.execute("SELECT * FROM Organisations;")

        # iterate through organisations
        for org in c.fetchall():
            org_id, org_name, org_domain, user_count, org_points = \
                    org[0], org[1], org[2], org[3], org[4]
            self.total_user_count += user_count

            # select users in the current organisation and sort by points - lowest to highest
            c.execute("SELECT * FROM Users WHERE orgId=? ORDER BY points DESC;", (org_id,))
            raw_leaderboard_data = c.fetchall()
            leaderboard = []

            for user in raw_leaderboard_data:
                user_id, user_name, email, points = user[0], user[1], user[2], user[4]

                leaderboard.append({
                    "id": user_id,
                    "name": user_name,
                    "email": email,
                    "points": points
                })

            # store all collected data in a class var
            self.organisations[org_id] = {
                "name": org_name,
                "user_count": user_count,
                "points": org_points,
                "leaderboard": leaderboard
            }

    def add_organisation(self, name: str, email_domain: str) -> int:
        """
        Adds an organisation entry to the database. Returns the new org's ID.
        """
        # add to cache
        new_id = len(self.organisations.keys()) + 1
        self.organisations[new_id] = {
            "name": name,
            "user_count": 0,
            "points": 0,
            "leaderboard": []
        }

        c = self.leaderboard_connection.cursor()
        c.execute("INSERT INTO Organisations (id, name, emailDomain, userCount, points) "
                  "VALUES (?, ?, ?, ?, ?);", (new_id, name, email_domain, 0, 0))
        self.leaderboard_connection.commit()

        return new_id

    def del_organisation(self, organisation_id: int):
        """
        Remove an organisation and all its members from the database.
        """
        c = self.leaderboard_connection.cursor()
        c.execute("DELETE FROM Organisations WHERE id=?;", (organisation_id,))
        c.execute("DELETE FROM Users WHERE orgId=?;", (organisation_id,))
        self.leaderboard_connection.commit()

        # remove from cache
        try:
            del self.organisations[organisation_id]
        except KeyError:
            raise InvalidOrganisation

    def add_user(self, organisation_id: int, name: str, email_address: str) -> int:
        """
        Checks if the organisation ID is valid and if the given email address is not present in the DB.
        If these are met, adds a user entry to the database.
        Returns the new user ID.
        """
        # check organisation ID
        if organisation_id not in self.organisations.keys():
            raise InvalidOrganisation

        # check email address
        for org in self.organisations.values():
            for user in org["leaderboard"]:
                if user["email"] == email_address:
                    raise EmailAlreadyRegistered

        self.organisations[organisation_id]["user_count"] += 1
        new_user_count = self.organisations[organisation_id]["user_count"]

        # add to cache
        new_id = self.total_user_count + 1
        self.organisations[organisation_id]["leaderboard"].append( {
            "id": new_id,
            "name": name,
            "email": email_address,
            "points": 0
        })
        self.total_user_count += 1

        # dump data to db
        c = self.leaderboard_connection.cursor()
        c.execute("INSERT INTO Users (name, email, orgId, points) VALUES (?, ?, ?, ?);",
                  (name, email_address, organisation_id, 0))
        c.execute("UPDATE Organisations SET userCount=? WHERE id=?;",
                  (new_user_count, organisation_id))
        self.leaderboard_connection.commit()

        return new_id

    def del_user(self, user_id: int):
        """
        Removes a user from the database.
        """
        # clear from cache
        users_org_id, user_index = self.get_user_organisation(user_id)

        self.organisations[users_org_id]["leaderboard"].pop(user_index)
        self.organisations[users_org_id]["user_count"] -= 1
        new_user_count = self.organisations[users_org_id]["user_count"]

        c = self.leaderboard_connection.cursor()
        c.execute("DELETE FROM Users WHERE id=?;", (user_id,))
        c.execute("UPDATE Organisations SET userCount=? WHERE id=?;",
                  (new_user_count, users_org_id))
        self.leaderboard_connection.commit()

    def get_user_organisation(self, user_id: int) -> Tuple[int, int]:
        """
        Returns a tuple of the organisation ID tied to the user and
        the index of the user in the leaderboard.
        Raises InvalidUsers if not found.
        """
        user_found_in_cache = False
        for org_id in self.organisations.keys():
            org = self.organisations[org_id]
            print(org)
            index = 0

            for user in org["leaderboard"]:
                if user["id"] == user_id:
                    index = org["leaderboard"].index(user)
                    user_found_in_cache = True
                    break

            if user_found_in_cache:
                return org_id, index

        if not user_found_in_cache:
            raise InvalidUser

    def change_organisation_points(self, organisation_id: int, points: int) -> int:
        """
        Modifies stored points for an organisation and returns the new points value.
        Org may need to be changed directly for org achievements.
        """
        try:
            self.organisations[organisation_id]["points"] += points
            new_points = self.organisations[organisation_id]["points"]
        except KeyError:
            raise InvalidOrganisation

        c = self.leaderboard_connection.cursor()
        c.execute("UPDATE Organisations SET points=? WHERE id=?",
                  (new_points, organisation_id))
        self.leaderboard_connection.commit()

        return new_points

    def change_user_points(self, user_id: int, points: int) -> int:
        """
        Modifies stored points for a user, the corresponding organisation,
        and returns the new points value.
        """
        users_org_id, user_index = self.get_user_organisation(user_id)

        self.organisations[users_org_id]["leaderboard"][user_index]["points"] += points
        new_points = self.organisations[users_org_id]["leaderboard"][user_index]["points"]
        self.change_organisation_points(users_org_id, points)

        c = self.leaderboard_connection.cursor()
        c.execute("UPDATE Users SET points=? WHERE id=?",
                  (new_points, user_id))
        self.leaderboard_connection.commit()

        return new_points


class InvalidOrganisation(Exception):
    ...

class InvalidUser(Exception):
    ...

class EmailAlreadyRegistered(Exception):
    ...
