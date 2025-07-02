import os
import xml.etree.ElementTree as ET
from rdflib import Graph, Literal, RDF, Namespace

XML_FILES = [
    "assets/fist_AI.xml",
    "assets/fist_ST.xml",
    "assets/fist_DCN.xml",
    "assets/fist_BIA.xml",
    "assets/fist_core_computing.xml",
    "assets/fist_intern.xml",
    "assets/fist_FYP.xml",
    "assets/fist_free_elective.xml"
]

EX = Namespace("http://example.org/fist/")

def collect_all_majors(xml_files):
    majors = set()
    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        major_elem = root.find("Major")
        if major_elem is not None:
            name = major_elem.get("name")
            if name:
                majors.add(name)
    return list(majors)

all_majors = collect_all_majors(XML_FILES)

def xml_file_to_rdf(xml_file, all_majors):
    g = Graph()
    g.bind("ex", EX)
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    major_elem = root.find("Major")
    if major_elem is not None:
        major_name = major_elem.get("name")
        for section_tag in ["DisciplineCoreCourses", "SpecialisationCourses"]:
            section = major_elem.find(section_tag)
            if section is not None:
                for course in section.findall("Course"):
                    code = course.find("Code").text
                    name = course.find("Name").text
                    credit = course.find("CreditHour").text
                    prereq = course.find("PreRequisite").text

                    course_uri = EX[code]

                    g.add((course_uri, RDF.type, EX.Course))
                    g.add((course_uri, EX.code, Literal(code)))
                    g.add((course_uri, EX.name, Literal(name)))
                    g.add((course_uri, EX.creditHour, Literal(credit)))
                    g.add((course_uri, EX.belongsToMajor, EX[major_name]))
                    
                    if prereq and prereq != "NONE":
                        g.add((course_uri, EX.requires, EX[prereq]))
    else:
        # if no Major element, assume it belongs to all majors
        course_type = None
        if "fist_core_computing.xml" in xml_file:
            course_type = "CoreComputing"
        elif "fist_intern.xml" in xml_file:
            course_type = "IndustrialTraining"
        elif "fist_free_elective.xml" in xml_file:
            course_type = "FreeElective"
        elif "fist_FYP.xml" in xml_file:
            course_type = "FinalYearProject"
        
        for course in root.findall(".//Course"):
            code = course.find("Code").text
            name = course.find("Name").text
            credit = course.find("CreditHour").text
            prereq = course.find("PreRequisite").text
            
            course_uri = EX[code]

            g.add((course_uri, RDF.type, EX.Course))
            g.add((course_uri, EX.code, Literal(code)))
            g.add((course_uri, EX.name, Literal(name)))
            g.add((course_uri, EX.creditHour, Literal(credit)))
            g.add((course_uri, EX.courseType, EX[course_type]))
            for major_name in all_majors:
                g.add((course_uri, EX.belongsToMajor, EX[major_name]))

            if prereq and prereq != "NONE":
                g.add((course_uri, EX.requires, EX[prereq]))

    return g


all_majors = collect_all_majors(XML_FILES)

merged_graph = Graph()
merged_graph.bind("ex", EX)

for xml_file in XML_FILES:
    print(f"Processing: {xml_file}")
    merged_graph += xml_file_to_rdf(xml_file, all_majors)

merged_graph.serialize(destination="merged_courses.ttl", format="turtle")
print("✅ combination completed, saved the information to merged_courses.ttl")
