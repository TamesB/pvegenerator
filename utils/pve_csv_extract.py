import csv
from app import models
from project.models import Beleggers

#ADD THIS CODE IN A VIEW AND RUN IT TO ADD A VERSION OF PVE FROM THE PVE.CSV
#WILL ADD ALL LINES OF PVE.CSV OF BELEGGER SYNTRUS
#CAUTION: IF THE VERSION ALREADY EXISTS IT WILL GET OVERWRITTEN
#
#versie = "ADD_VERSION_NAME_HERE"
#
# if models.PVEVersie.objects.filter(versie=versie):
#   versie_obj = models.PVEVersie.objects.filter(versie=versie).first()
#   pveitems = models.PVEItem.objects.filter(versie=versie_obj).all().delete()
#   pvehoofdstuk = models.PVEHoofdstuk.objects.filter(versie=versie_obj).all().delete()
#   pveparagraaf = models.PVEParagraaf.objects.filter(versie=versie_obj).all().delete()
#   print("done_deleting")
#
#extract = pve_csv_extract.ExtractPVE(versie)
#extract.read_pve()
#extract.organize_pve()
#extract.put_in_db()

class Hoofdstuk:
    def __init__(self):
        self.naam = ""

    def set_name(self, string):
        self.naam = string


class Paragraaf:
    def __init__(self):
        self.naam = ""

    def set_name(self, string):
        self.naam = string


class Item:
    def __init__(self, hoofdstuk, paragraaf):
        self.hoofdstuk = hoofdstuk
        self.paragraaf = paragraaf
        self.inhoud = ""
        # see order at the top
        self.parameters = [False,False,False,False,False,False,False,False,False,False,False,False,False]

    def set_parameter(self, index):
        self.parameters[index] = True


class ExtractPVE:
    def __init__(self, versie):
        if models.PVEVersie.objects.filter(versie=versie):
            self.versie = models.PVEVersie.objects.filter(versie=versie).first()
        else:
            versie_obj = models.PVEVersie()
            versie_obj.versie = versie
            versie_obj.belegger = Beleggers.objects.filter(naam="Syntrus").first()
            versie_obj.save()
            self.versie = versie_obj

        self.pve_book = []
        self.hoofdstuk_namen = []
        self.paragraaf_namen = []

        self.hoofdstuk_objects = []
        self.paragraaf_objects = []
        self.item_objects = []

    def read_pve(self):
        with open('pve.csv', newline='', encoding="utf8") as File:  
            reader = csv.reader(File, delimiter=";")
            for row in reader:
                self.pve_book.append(row)

    def organize_pve(self):
        paragraaf_was_last = False

        for index in range(len(self.pve_book)):
            if index > 0:
                # check if line is paragraaf or hoofdstuk
                if (self.pve_book[index][0] is ""
                    and ((self.pve_book[index - 1][0] != self.pve_book[index + 1][0])) and (self.pve_book[index - 1][0] != "")):
                    self.hoofdstuk_namen.append(self.pve_book[index][1])
                    hoofdstuk = Hoofdstuk()
                    hoofdstuk.set_name(self.hoofdstuk_namen[-1])
                    self.hoofdstuk_objects.append(hoofdstuk)
                    paragraaf_was_last = False

                if (self.pve_book[index - 1][0] is "" and self.pve_book[0] is "") or (self.pve_book[index][0] is "" and (self.pve_book[index - 1][0] == self.pve_book[index + 1][0])):
                    self.paragraaf_namen.append(self.pve_book[index][1])
                    paragraaf = Paragraaf()
                    paragraaf.set_name(self.paragraaf_namen[-1])
                    self.paragraaf_objects.append(paragraaf)
                    paragraaf_was_last = True

            # is an item if zeroeth cell not empty and 1st cell also not empty
            if (self.pve_book[index][0] != "" and self.pve_book[index][1] != ""):
                if len(self.paragraaf_objects) > 0 and paragraaf_was_last:
                    item = Item(self.hoofdstuk_objects[-1], self.paragraaf_objects[-1])
                else:
                    item = Item(self.hoofdstuk_objects[-1], None)

                item.inhoud = self.pve_book[index][1]

                # index 3 to 15 is parameters
                for par_index in range(3, 16):
                    if self.pve_book[index][par_index] == "x":
                        item.set_parameter(par_index - 3)
                
                self.item_objects.append(item)
            
        for item in self.item_objects:
            if item.paragraaf:
                print(f"Hoofdstuk:{item.hoofdstuk.naam}\nParagraaf:{item.paragraaf.naam}\nInhoud: {item.inhoud}\nParameters:{item.parameters}\n")
            else:
                print(f"Hoofdstuk:{item.hoofdstuk.naam}\nInhoud: {item.inhoud}\nParameters:{item.parameters}\n")

    # input = self.versie object
    def put_in_db(self):
        for item in self.item_objects:
            pve_item = models.PVEItem()
            pve_item.versie = self.versie

            if item.hoofdstuk:
                if not models.PVEHoofdstuk.objects.filter(versie=self.versie, hoofdstuk=item.hoofdstuk.naam):
                    hoofdstuk = models.PVEHoofdstuk()
                    hoofdstuk.hoofdstuk = item.hoofdstuk.naam
                    hoofdstuk.versie = self.versie
                    hoofdstuk.save()
                else:
                    hoofdstuk = models.PVEHoofdstuk.objects.filter(versie=self.versie, hoofdstuk=item.hoofdstuk.naam).first()
                
                pve_item.hoofdstuk = hoofdstuk

            if item.paragraaf:
                if not models.PVEParagraaf.objects.filter(versie=self.versie, paragraaf=item.paragraaf.naam):
                    paragraaf = models.PVEParagraaf()
                    paragraaf.paragraaf = item.paragraaf.naam
                    paragraaf.hoofdstuk = models.PVEHoofdstuk.objects.filter(versie=self.versie, hoofdstuk=item.hoofdstuk.naam).first()
                    paragraaf.versie = self.versie
                    paragraaf.save()
                else:
                    paragraaf = models.PVEParagraaf.objects.filter(versie=self.versie, paragraaf=item.paragraaf.naam).first()
                
                pve_item.paragraaf = paragraaf

            # set inhoud
            pve_item.inhoud = item.inhoud
            pve_item.save()

            #parameters
            bouwsoort_set = item.parameters[0:4]
            typeobject_set = item.parameters[4:9]
            doelgroep_set = item.parameters[9:13]

            for set_index in range(len(bouwsoort_set)):
                if bouwsoort_set[set_index]:
                    if set_index == 0:
                        if not models.Bouwsoort.objects.filter(versie=self.versie, parameter="Nieuwbouw"):
                            model = models.Bouwsoort()
                            model.versie = self.versie
                            model.parameter = "Nieuwbouw"
                            model.save()

                        parameter_model = models.Bouwsoort.objects.filter(versie=self.versie, parameter="Nieuwbouw").first()
                    if set_index == 1:
                        if not models.Bouwsoort.objects.filter(versie=self.versie, parameter="Transformatie"):
                            model = models.Bouwsoort()
                            model.versie = self.versie
                            model.parameter = "Transformatie"
                            model.save()

                        parameter_model = models.Bouwsoort.objects.filter(versie=self.versie, parameter="Transformatie").first()
                    if set_index == 2:
                        if not models.Bouwsoort.objects.filter(versie=self.versie, parameter="Commercieel"):
                            model = models.Bouwsoort()
                            model.versie = self.versie
                            model.parameter = "Commercieel"
                            model.save()

                        parameter_model = models.Bouwsoort.objects.filter(versie=self.versie, parameter="Commercieel").first()
                    if set_index == 3:
                        if not models.Bouwsoort.objects.filter(versie=self.versie, parameter="Levensloop Bestendig"):
                            model = models.Bouwsoort()
                            model.versie = self.versie
                            model.parameter = "Levensloop Bestendig"
                            model.save()

                        parameter_model = models.Bouwsoort.objects.filter(versie=self.versie, parameter="Levensloop Bestendig").first()
                    
                    pve_item.Bouwsoort.add(parameter_model)

                    if pve_item.Bouwsoort.count() == 4:
                        pve_item.basisregel = True
                        pve_item.save()

            for set_index in range(len(typeobject_set)):
                if typeobject_set[set_index]:
                    if set_index == 0:
                        if not models.TypeObject.objects.filter(versie=self.versie, parameter="Grondgebonden woning"):
                            model = models.TypeObject()
                            model.versie = self.versie
                            model.parameter = "Grondgebonden woning"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(versie=self.versie, parameter="Grondgebonden woning").first()
                    if set_index == 1:
                        if not models.TypeObject.objects.filter(versie=self.versie, parameter="Appartement 0-50 m2"):
                            model = models.TypeObject()
                            model.versie = self.versie
                            model.parameter = "Appartement 0-50 m2"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(versie=self.versie, parameter="Appartement 0-50 m2").first()
                    if set_index == 2:
                        if not models.TypeObject.objects.filter(versie=self.versie, parameter="Appartement 50-70 m2"):
                            model = models.TypeObject()
                            model.versie = self.versie
                            model.parameter = "Appartement 50-70 m2"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(versie=self.versie, parameter="Appartement 50-70 m2").first()
                    if set_index == 3:
                        if not models.TypeObject.objects.filter(versie=self.versie, parameter="Appartement 70-100 m2"):
                            model = models.TypeObject()
                            model.versie = self.versie
                            model.parameter = "Appartement 70-100 m2"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(versie=self.versie, parameter="Appartement 70-100 m2").first()
                    if set_index == 4:
                        if not models.TypeObject.objects.filter(versie=self.versie, parameter="Appartement >100 m2"):
                            model = models.TypeObject()
                            model.versie = self.versie
                            model.parameter = "Appartement >100 m2"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(versie=self.versie, parameter="Appartement >100 m2").first()

                    pve_item.TypeObject.add(parameter_model)


            for set_index in range(len(doelgroep_set)):
                if doelgroep_set[set_index]:
                    if set_index == 0:
                        if not models.Doelgroep.objects.filter(versie=self.versie, parameter="Sociaal / Studenten"):
                            model = models.Doelgroep()
                            model.versie = self.versie
                            model.parameter = "Sociaal / Studenten"
                            model.save()

                        parameter_model = models.Doelgroep.objects.filter(versie=self.versie, parameter="Sociaal / Studenten").first()
                    if set_index == 1:
                        if not models.Doelgroep.objects.filter(versie=self.versie, parameter="Light (Starters / Young proffessionals)"):
                            model = models.Doelgroep()
                            model.versie = self.versie
                            model.parameter = "Light (Starters / Young proffessionals)"
                            model.save()

                        parameter_model = models.Doelgroep.objects.filter(versie=self.versie, parameter="Light (Starters / Young proffessionals)").first()
                    if set_index == 2:
                        if not models.Doelgroep.objects.filter(versie=self.versie, parameter="Basis (modaal gezin)"):
                            model = models.Doelgroep()
                            model.versie = self.versie
                            model.parameter = "Basis (modaal gezin)"
                            model.save()

                        parameter_model = models.Doelgroep.objects.filter(versie=self.versie, parameter="Basis (modaal gezin)").first()
                    if set_index == 3:
                        if not models.Doelgroep.objects.filter(versie=self.versie, parameter="Luxe (high end)"):
                            model = models.Doelgroep()
                            model.versie = self.versie
                            model.parameter = "Luxe (high end)"
                            model.save()

                        parameter_model = models.Doelgroep.objects.filter(versie=self.versie, parameter="Luxe (high end)").first()

                    pve_item.Doelgroep.add(parameter_model)