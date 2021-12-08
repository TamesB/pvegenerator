import csv
from app import models
from project.models import Beleggers

#ADD THIS CODE IN A VIEW AND RUN IT TO ADD A VERSION OF PVE FROM THE PVE.CSV
#WILL ADD ALL LINES OF PVE.CSV OF BELEGGER PVETool
#CAUTION: IF THE VERSION ALREADY EXISTS IT WILL GET OVERWRITTEN
#
#version = "ADD_VERSION_NAME_HERE"
#
# if models.PVEVersie.objects.filter(version=version):
#   versie_obj = models.PVEVersie.objects.filter(version=version).first()
#   pveitems = models.PVEItem.objects.filter(version=versie_obj).all().delete()
#   pvechapter = models.PVEHoofdstuk.objects.filter(version=versie_obj).all().delete()
#   pveparagraaf = models.PVEParagraaf.objects.filter(version=versie_obj).all().delete()
#   print("done_deleting")
#
#extract = pve_csv_extract.ExtractPVE(version)
#extract.read_pve()
#extract.organize_pve()
#extract.put_in_db()

class Hoofdstuk:
    def __init__(self):
        self.name = ""

    def set_name(self, string):
        self.name = string


class Paragraaf:
    def __init__(self):
        self.name = ""

    def set_name(self, string):
        self.name = string


class Item:
    def __init__(self, chapter, paragraph):
        self.chapter = chapter
        self.paragraph = paragraph
        self.inhoud = ""
        # see order at the top
        self.parameters = [False,False,False,False,False,False,False,False,False,False,False,False,False]

    def set_parameter(self, index):
        self.parameters[index] = True


class ExtractPVE:
    def __init__(self, version):
        if models.PVEVersie.objects.filter(version=version):
            self.version = models.PVEVersie.objects.filter(version=version).first()
        else:
            versie_obj = models.PVEVersie()
            versie_obj.version = version
            versie_obj.client = Beleggers.objects.filter(name="PVETool").first()
            versie_obj.save()
            self.version = versie_obj

        self.pve_book = []
        self.chapter_namen = []
        self.paragraaf_namen = []

        self.chapter_objects = []
        self.paragraaf_objects = []
        self.item_objects = []

    def read_pve(self):
        with open('pve_new.csv', newline='', encoding="utf8") as File:  
            reader = csv.reader(File, delimiter=";")
            for row in reader:
                self.pve_book.append(row)

    def organize_pve(self):
        paragraaf_was_last = False

        for index in range(len(self.pve_book)):
            if index > 0:
                # check if line is paragraph or chapter
                if (self.pve_book[index][0] == ""
                    and ((self.pve_book[index - 1][0] != self.pve_book[index + 1][0])) and (self.pve_book[index - 1][0] != "")):
                    self.chapter_namen.append(self.pve_book[index][1])
                    chapter = Hoofdstuk()
                    chapter.set_name(self.chapter_namen[-1])
                    self.chapter_objects.append(chapter)
                    paragraaf_was_last = False

                if (self.pve_book[index - 1][0] == "" and self.pve_book[index][0] == "") or (self.pve_book[index][0] == "" and (self.pve_book[index - 1][0] == self.pve_book[index + 1][0])):
                    self.paragraaf_namen.append(self.pve_book[index][1])
                    paragraph = Paragraaf()
                    paragraph.set_name(self.paragraaf_namen[-1])
                    self.paragraaf_objects.append(paragraph)
                    paragraaf_was_last = True

            # is an item if zeroeth cell not empty and 1st cell also not empty
            if (self.pve_book[index][0] != "" and self.pve_book[index][1] != ""):
                if len(self.paragraaf_objects) > 0 and paragraaf_was_last:
                    item = Item(self.chapter_objects[-1], self.paragraaf_objects[-1])
                else:
                    item = Item(self.chapter_objects[-1], None)

                item.inhoud = self.pve_book[index][1]

                # index 3 to 15 is parameters
                for par_index in range(3, 16):
                    if self.pve_book[index][par_index] == "x":
                        item.set_parameter(par_index - 3)
                
                self.item_objects.append(item)
            
        for item in self.item_objects:
            if item.paragraph:
                print(f"Hoofdstuk:{item.chapter.name}\nParagraaf:{item.paragraph.name}\nInhoud: {item.inhoud}\nParameters:{item.parameters}\n")
            else:
                print(f"Hoofdstuk:{item.chapter.name}\nInhoud: {item.inhoud}\nParameters:{item.parameters}\n")

    # input = self.version object
    def put_in_db(self):
        for item in self.item_objects:
            pve_item = models.PVEItem()
            pve_item.version = self.version

            if item.chapter:
                if not models.PVEHoofdstuk.objects.filter(version=self.version, chapter=item.chapter.name).exists():
                    chapter = models.PVEHoofdstuk()
                    chapter.chapter = item.chapter.name
                    chapter.version = self.version
                    chapter.save()
                else:
                    chapter = models.PVEHoofdstuk.objects.filter(version=self.version, chapter=item.chapter.name).first()
                
                pve_item.chapter = chapter

            if item.paragraph:
                if not models.PVEParagraaf.objects.filter(version=self.version, chapter=chapter, paragraph=item.paragraph.name).exists():
                    paragraph = models.PVEParagraaf()
                    paragraph.paragraph = item.paragraph.name
                    paragraph.chapter = chapter
                    paragraph.version = self.version
                    paragraph.save()
                else:
                    paragraph = models.PVEParagraaf.objects.filter(version=self.version, chapter=chapter, paragraph=item.paragraph.name).first()
                
                pve_item.paragraph = paragraph

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
                        if not models.Bouwsoort.objects.filter(version=self.version, parameter="Nieuwbouw").exists():
                            model = models.Bouwsoort()
                            model.version = self.version
                            model.parameter = "Nieuwbouw"
                            model.save()

                        parameter_model = models.Bouwsoort.objects.filter(version=self.version, parameter="Nieuwbouw").first()
                    if set_index == 1:
                        if not models.Bouwsoort.objects.filter(version=self.version, parameter="Transformatie").exists():
                            model = models.Bouwsoort()
                            model.version = self.version
                            model.parameter = "Transformatie"
                            model.save()

                        parameter_model = models.Bouwsoort.objects.filter(version=self.version, parameter="Transformatie").first()
                    if set_index == 2:
                        if not models.Bouwsoort.objects.filter(version=self.version, parameter="Commercieel").exists():
                            model = models.Bouwsoort()
                            model.version = self.version
                            model.parameter = "Commercieel"
                            model.save()

                        parameter_model = models.Bouwsoort.objects.filter(version=self.version, parameter="Commercieel").first()
                    if set_index == 3:
                        if not models.Bouwsoort.objects.filter(version=self.version, parameter="Levensloop Bestendig").exists():
                            model = models.Bouwsoort()
                            model.version = self.version
                            model.parameter = "Levensloop Bestendig"
                            model.save()

                        parameter_model = models.Bouwsoort.objects.filter(version=self.version, parameter="Levensloop Bestendig").first()
                    
                    pve_item.Bouwsoort.add(parameter_model)

                    if pve_item.Bouwsoort.count() == 4:
                        pve_item.basisregel = True
                        pve_item.save()

            for set_index in range(len(typeobject_set)):
                if typeobject_set[set_index]:
                    if set_index == 0:
                        if not models.TypeObject.objects.filter(version=self.version, parameter="Grondgebonden woning").exists():
                            model = models.TypeObject()
                            model.version = self.version
                            model.parameter = "Grondgebonden woning"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(version=self.version, parameter="Grondgebonden woning").first()
                    if set_index == 1:
                        if not models.TypeObject.objects.filter(version=self.version, parameter="Appartement 0-50 m2").exists():
                            model = models.TypeObject()
                            model.version = self.version
                            model.parameter = "Appartement 0-50 m2"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(version=self.version, parameter="Appartement 0-50 m2").first()
                    if set_index == 2:
                        if not models.TypeObject.objects.filter(version=self.version, parameter="Appartement 50-70 m2").exists():
                            model = models.TypeObject()
                            model.version = self.version
                            model.parameter = "Appartement 50-70 m2"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(version=self.version, parameter="Appartement 50-70 m2").first()
                    if set_index == 3:
                        if not models.TypeObject.objects.filter(version=self.version, parameter="Appartement 70-100 m2").exists():
                            model = models.TypeObject()
                            model.version = self.version
                            model.parameter = "Appartement 70-100 m2"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(version=self.version, parameter="Appartement 70-100 m2").first()
                    if set_index == 4:
                        if not models.TypeObject.objects.filter(version=self.version, parameter="Appartement >100 m2").exists():
                            model = models.TypeObject()
                            model.version = self.version
                            model.parameter = "Appartement >100 m2"
                            model.save()

                        parameter_model = models.TypeObject.objects.filter(version=self.version, parameter="Appartement >100 m2").first()

                    pve_item.TypeObject.add(parameter_model)


            for set_index in range(len(doelgroep_set)):
                if doelgroep_set[set_index]:
                    if set_index == 0:
                        if not models.Doelgroep.objects.filter(version=self.version, parameter="Sociaal / Studenten").exists():
                            model = models.Doelgroep()
                            model.version = self.version
                            model.parameter = "Sociaal / Studenten"
                            model.save()

                        parameter_model = models.Doelgroep.objects.filter(version=self.version, parameter="Sociaal / Studenten").first()
                    if set_index == 1:
                        if not models.Doelgroep.objects.filter(version=self.version, parameter="Light (Starters / Young proffessionals)").exists():
                            model = models.Doelgroep()
                            model.version = self.version
                            model.parameter = "Light (Starters / Young proffessionals)"
                            model.save()

                        parameter_model = models.Doelgroep.objects.filter(version=self.version, parameter="Light (Starters / Young proffessionals)").first()
                    if set_index == 2:
                        if not models.Doelgroep.objects.filter(version=self.version, parameter="Basis (modaal gezin)").exists():
                            model = models.Doelgroep()
                            model.version = self.version
                            model.parameter = "Basis (modaal gezin)"
                            model.save()

                        parameter_model = models.Doelgroep.objects.filter(version=self.version, parameter="Basis (modaal gezin)").first()
                    if set_index == 3:
                        if not models.Doelgroep.objects.filter(version=self.version, parameter="Luxe (high end)").exists():
                            model = models.Doelgroep()
                            model.version = self.version
                            model.parameter = "Luxe (high end)"
                            model.save()

                        parameter_model = models.Doelgroep.objects.filter(version=self.version, parameter="Luxe (high end)").first()

                    pve_item.Doelgroep.add(parameter_model)