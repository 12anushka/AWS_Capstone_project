from database.db import donors, blood_stock
def add_activity(email, activity):
    if email not in donor_activities:
        donor_activities[email] = []

    donor_activities[email].append(activity)


def get_activities(email):
    return donor_activities.get(email, [])

def add_donor(data):
    donors.append(data)
    blood_stock[data["blood_group"]] += 1

def get_all_donors():
    return donors

def find_donors(blood_group, location):
    return [
        d for d in donors
        if d["blood_group"] == blood_group and d["location"] == location
    ]
def get_donor_by_email(email):
    donors = get_all_donors()
    for donor in donors:
        if donor.get("email") == email:
            return donor
    return None
# services/donor_service.py

donors = []
donor_activities = {}

def add_donor(donor):
    donors.append(donor)

def get_all_donors():
    return donors


# -------- ACTIVITY FUNCTIONS --------
def add_activity(email, activity):
    if email not in donor_activities:
        donor_activities[email] = []
    donor_activities[email].append(activity)

def get_activities(email):
    return donor_activities.get(email, [])
