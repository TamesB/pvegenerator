DEFAULT_ERROR = "Er is iets fout gegaan. Neem contact op met de systeembeheerder: tames@tboon.nl"

PROJECT = "project"
USER = "gebruiker"
EMPLOYEE = "medewerker"
STAKEHOLDER = "stakeholder"
CLIENT = "klant"
ANNOTATION = "opmerking"
REPLY = "reactie"
STATUS = "status"
COSTS = "kosten"

FIRST_STATUS_ADD = "Eerste statusaanwijzing"
REPLY = "Uw beurt"

def DELETE_SUCCESS(obj): return f"{obj} succesvol verwijderd."
def DELETE_ERROR(obj): return f"Fout met {obj} verwijderen."

def ADDED_SUCCESS(obj): return f"{obj} succesvol toegevoegd."
def ADDED_ERROR(obj): return f"Fout met {obj} toevoegen."

def EDITED_SUCCESS(obj): return f"{obj} succesvol gewijzigd."
def EDITED_ERROR(obj): return f"Fout met {obj} wijzigen."


def EMAIL_STAKEHOLDER_ADDED_TO_PROJECT(project, client): return (
f"""



""")

def EMAIL_PROJECTMANAGER_ADDED_TO_PROJECT(project, client): return (
f"""



""")

def EMAIL_ANNOTATIONS_SENT(project, client): return (
f"""



""")