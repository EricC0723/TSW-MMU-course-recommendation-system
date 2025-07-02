from flask import Flask, request, jsonify
from rdflib import Graph, Literal, Namespace, URIRef
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allow cross-origin requests from all sources. For production, restrict this to your frontend domain.

# --- Load RDF Graph Globally ---
# This graph 'g' will be loaded once when the Flask app starts.
g = Graph()
EX = Namespace("http://example.org/fist/") # Define your namespace

try:
    g.parse("merged_courses.ttl", format="turtle")
    print("✅ TTL file loaded successfully!")
    g.bind("ex", EX) # Bind prefix for cleaner queries if needed elsewhere, though f-strings handle it
except Exception as e:
    print(f"❌ Error loading TTL file: {e}")
    # Consider how to handle this error more gracefully in a production app
    # For now, exiting might be okay for development if the app can't run without it.
    exit()

# --- API Endpoints ---

@app.route('/api/courses', methods=['GET'])
def get_courses_by_major():
    major_param = request.args.get('major')

    if not major_param:
        return jsonify({"error": "Major parameter is required"}), 400

    sparql_query = f"""
    PREFIX ex: <http://example.org/fist/>

    SELECT ?courseName ?courseCode ?courseType ?creditHour
    WHERE {{
    ?course a ex:Course ;
            ex:belongsToMajor ex:{major_param} ;
            ex:name ?courseName ;
            ex:code ?courseCode .
    
    OPTIONAL {{ ?course ex:creditHour ?creditHour . }}
    OPTIONAL {{ ?course ex:courseType ?typeUri . }}

    BIND(REPLACE(STR(?typeUri), STR(ex:), "") AS ?courseTypeRaw)

    BIND(
        IF(BOUND(?typeUri),
        IF(?courseTypeRaw = "FreeElective", "Free Elective Subject",
            IF(?courseTypeRaw = "CoreComputing", "Core Computing Subject",
            IF(?courseTypeRaw = "IndustrialTraining", "Industrial Training",
            ?courseTypeRaw))),
        "Major Subject"
        ) AS ?courseType
    )
    }}
    ORDER BY ?courseType ?courseName
    """
    results = g.query(sparql_query)#IF(?courseTypeRaw = "FinalYearProject", "FinalYearProject",

    grouped_courses = {}
    for row in results:
        course_name = str(row.courseName)
        course_code = str(row.courseCode)
        course_type = str(row.courseType)
        # UPDATE: Safely get the credit hour.
        credit_hour = int(row.creditHour) if row.creditHour else 0

        if course_type not in grouped_courses:
            grouped_courses[course_type] = []

        # UPDATE: Add creditHour to the course object.
        course_info = {
            "name": course_name,
            "code": course_code,
            "creditHour": credit_hour
        }
        if course_info not in grouped_courses[course_type]:
            grouped_courses[course_type].append(course_info)

    return jsonify(grouped_courses)

@app.route('/api/recommended_courses', methods=['POST'])
def recommend_courses():
    data = request.json
    major = data.get('major')
    if not major:
        return jsonify({"error": "Major parameter is required"}), 400

    completed_course_codes = data.get('completed', [])
    grouped_recommendations = {}

    # Case 1: No courses completed (your existing logic for this is fine)
    if not completed_course_codes:
        # This part of your code can remain the same, just ensure it groups results.
        # For brevity, I'll omit repeating the no-courses-completed query here.
        # ... your existing query for when completed_course_codes is empty ...
        pass # Placeholder for your existing logic
    
    # Case 2: Courses have been completed. Calculate credits and run the main query.
    else:
        # --- Step 1: Calculate total completed credit hours ---
        total_credits = 0
        completed_literals_for_credits = ", ".join([f'"{code}"' for code in completed_course_codes])
        
        credit_query = f"""
        PREFIX ex: <{str(EX)}>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT (SUM(xsd:integer(?credit)) AS ?totalCredits)
        WHERE {{
            ?course ex:code ?code ;
                    ex:creditHour ?credit .
            FILTER(?code IN ({completed_literals_for_credits}))
        }}
        """
        try:
            credit_results = g.query(credit_query)
            for row in credit_results:
                if row.totalCredits:
                    total_credits = int(row.totalCredits)
            print(f"✅ Calculated Total Credits: {total_credits}") # For debugging
        except Exception as e:
            print(f"❌ Error calculating credits: {e}")
            return jsonify({"error": "Failed to calculate credit hours"}), 500

        # --- Step 2: Build and execute the main recommendation query ---
        completed_iris_str = ", ".join([f'ex:{code}' for code in completed_course_codes])
        completed_literals_str = ", ".join([f'"{code}"' for code in completed_course_codes])

        sparql_query = f"""
        PREFIX ex: <{str(EX)}>

        SELECT DISTINCT ?recommendedName ?recommendedCode ?courseType
        WHERE {{
            ?recommendedCourse a ex:Course ;
                               ex:belongsToMajor ex:{major} ;
                               ex:name ?recommendedName ;
                               ex:code ?recommendedCode .
            
            # Get course type for grouping results
            OPTIONAL {{ ?recommendedCourse ex:courseType ?typeUri . }}
            BIND(REPLACE(STR(?typeUri), STR(ex:), "") AS ?courseTypeRaw)
            BIND(
                IF(BOUND(?typeUri),
                IF(?courseTypeRaw = "FreeElective", "Free Elective Subject",
                    IF(?courseTypeRaw = "CoreComputing", "Core Computing Subject",
                    IF(?courseTypeRaw = "IndustrialTraining", "Industrial Training",
                    ?courseTypeRaw))),
                "Major Subject"
                ) AS ?courseType
            )

            # Filter 1: Exclude courses already completed.
            FILTER (?recommendedCode NOT IN ({completed_literals_str}))

            # Filter 2: Handle standard prerequisites.
            # A course is valid if it does NOT have a prerequisite that is NOT in the completed list.
            # We also explicitly ignore the 'ex:60CH' requirement here, as it's handled next.
            FILTER NOT EXISTS {{
                ?recommendedCourse ex:requires ?prereq .
                FILTER(?prereq != ex:60CH && ?prereq NOT IN ({completed_iris_str}))
            }}

            # Filter 3: Handle the special 60-credit-hour requirement.
            # A course is valid if it does NOT require 'ex:60CH' while the student has less than 60 credits.
            FILTER NOT EXISTS {{
                ?recommendedCourse ex:requires ex:60CH .
                FILTER({total_credits} < 60)
            }}
        }}
        ORDER BY ?courseType ?recommendedName
        """

    # --- Process results (this part is the same for both cases) ---
    try:
        # Note: If completed_course_codes is empty, you should use your original "no-prereq" query here.
        # This example assumes the main `sparql_query` variable is set correctly in the if/else block.
        results = g.query(sparql_query) 
        for row in results:
            name = str(row.recommendedName)
            code = str(row.recommendedCode)
            course_type = str(row.courseType)

            if course_type not in grouped_recommendations:
                grouped_recommendations[course_type] = []
            
            course_info = { "name": name, "code": code }
            if course_info not in grouped_recommendations[course_type]:
                grouped_recommendations[course_type].append(course_info)

    except Exception as e:
        print(f"❌ Error during SPARQL query execution: {e}")
        return jsonify({"error": "Failed to query recommendations", "details": str(e)}), 500

    return jsonify(grouped_recommendations)

# --- Run Application ---
if __name__ == '__main__':
    print("🚀 Flask backend starting...")
    app.run(debug=True, port=5000)