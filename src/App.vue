<template>
  <div class="container">
    <h1>MMU FIST Degree Course Recommendation System</h1>

    <div class="section">
      <label for="major">Please select major:</label>
      <div class="select-wrapper">
        <select
          id="major"
          v-model="selectedMajor"
          @change="loadCourses"
        >
          <option disabled value="">Please select your major</option>
          <option value="AI">Bachelor of Computer Science (Honours) (Artificial Intelligence)</option>
          <option value="BIA">Bachelor of Information Technology (Honours) (Business Intelligence and Analytics)</option>
          <option value="DCN">Bachelor of Information Technology (Honours) (Data Communications and Networking)</option>
          <option value="ST">Bachelor of Information Technology (Honours) (Security Technology)</option>
        </select>
        <span class="select-arrow"></span>
      </div>
    </div>

    <div v-if="selectedMajor" class="section">
      <h2>Select Courses You've Taken:</h2>
      <div v-for="(coursesOfType, typeName) in groupedCourses" :key="typeName" class="course-group">
        <h3>{{ typeName }} Courses</h3>
        <div class="course-list">
          <div v-for="course in coursesOfType" :key="course.code" class="course-item">
            <input
              type="checkbox"
              :id="course.code"
              v-model="selectedCourses"
              :value="course"
            />
            <label :for="course.code">{{ course.name }} <span>({{ course.code }})</span></label>
          </div>
        </div>
      </div>
      <p v-if="Object.keys(groupedCourses).length === 0 && selectedMajor" class="info-message">
        No course information available for this major. Please select another major.
      </p>
    </div>

    <button @click="recommend" :disabled="!selectedMajor || !hasSelectedCourses">
      Recommend Courses
    </button>

<div v-if="Object.keys(recommendations).length" class="recommendations-box">
  <h2>Recommended Courses:</h2>
  <div v-for="(courses, type) in recommendations" :key="type" class="recommendation-group">
    <h3>{{ type }}</h3>
    <ul>
      <li v-for="course in courses" :key="course.code">
        {{ course.name }} <span>({{ course.code }})</span>
      </li>
    </ul>
  </div>
</div>
  </div>
</template>

<script>
export default {
  name: 'HelloWorld',
  props: {
    msg: String
  },
  data() {
    return {
      selectedMajor: '',
      groupedCourses: {},
      selectedCourses: [],
      recommendations: [],
      allCoursesForMajor: [],
    };
  },
  computed: {
    hasSelectedCourses() {
      return this.selectedCourses.length > 0;
    }
  },
  methods: {
    async loadCourses() {
      this.selectedCourses = [];
      this.recommendations = [];
      this.groupedCourses = {};
      this.allCoursesForMajor = [];

      const major = this.selectedMajor;
      if (!major) {
        return;
      }

      try {
        const response = await fetch(`http://localhost:5000/api/courses?major=${major}`);

        if (!response.ok) {
          throw new Error(`HTTP Error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Courses data fetched from backend:', data);

        this.groupedCourses = data;

        for (const typeName in this.groupedCourses) {
            if (Object.hasOwnProperty.call(this.groupedCourses, typeName)) {
                this.allCoursesForMajor.push(...this.groupedCourses?.[typeName] || []);
            }
        }

      } catch (error) {
        console.error('Error fetching course data from backend API:', error);
        alert('Failed to fetch course data. Please ensure the backend service is running and your network connection is stable.');
      }
    },
    recommend() {
    const completedCourseCodes = this.selectedCourses.map(course => course.code);

    console.log('Completed course codes:', completedCourseCodes);

    fetch("http://localhost:5000/api/recommended_courses", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ major: this.selectedMajor,completed: completedCourseCodes })
    })
      .then(response => response.json())
      .then(data => {
        this.recommendations = data;
        console.log("Recommendations received:", this.recommendations);
      })
      .catch(error => {
        console.error("Error fetching recommendations:", error);
      });
  }
  },
};
</script>

<style scoped>
/* -------------------- General Layout & Container -------------------- */
.container {
  max-width: 600px; /* Limit content width */
  margin: 40px auto; /* Center the container with top/bottom margin */
  padding: 30px;
  background-color: #ffffff; /* White background */
  border-radius: 8px; /* Slightly rounded corners */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); /* Soft shadow for depth */
  font-family: Arial, sans-serif; /* Clean, readable font */
  color: #333; /* Default text color */
}

h1 {
  text-align: center;
  color: #2c3e50;
  font-size: 2em; /* Larger title */
  margin-bottom: 30px;
  border-bottom: 2px solid #eee; /* Subtle separator */
  padding-bottom: 15px;
}

h2 {
  color: #34495e;
  font-size: 1.5em;
  margin-bottom: 20px;
  padding-top: 10px;
}

h3 {
  color: #2980b9; /* A shade of blue for section titles */
  font-size: 1.2em;
  margin-bottom: 15px;
  border-bottom: 1px dotted #ccc; /* Dotted separator */
  padding-bottom: 8px;
}

/* -------------------- Sections & Spacing -------------------- */
.section {
  margin-bottom: 25px; /* Spacing between main sections */
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0; /* Light separator for sections */
}

.section:last-of-type {
  border-bottom: none; /* No border for the last section */
  padding-bottom: 0;
  margin-bottom: 0;
}

/* -------------------- Dropdown (Select Major) -------------------- */
label {
  display: block; /* Ensures label is on its own line */
  margin-bottom: 8px;
  font-weight: bold;
  color: #555;
}

.select-wrapper {
  position: relative;
  display: inline-block; /* Allows the arrow to position relative to select */
  width: 100%; /* Make it full width */
}

select {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ccc;
  border-radius: 5px;
  background-color: #f9f9f9;
  font-size: 1em;
  -webkit-appearance: none; /* Remove default browser styling for select */
  -moz-appearance: none;
  appearance: none;
  padding-right: 30px; /* Make space for custom arrow */
}

select:focus {
  outline: none;
  border-color: #3498db; /* Blue border on focus */
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2); /* Soft blue glow on focus */
}

.select-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  pointer-events: none; /* Allows clicks to pass through to select */
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid #666; /* Simple down arrow */
}


/* -------------------- Course List & Checkboxes -------------------- */
.course-group {
  margin-bottom: 25px; /* Spacing between different course types */
  padding-bottom: 15px;
  border-bottom: 1px dashed #e0e0e0; /* Dashed separator for groups */
}

.course-group:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
}

.course-list {
  display: grid; /* Use CSS Grid for a clean two-column layout */
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); /* Responsive two columns */
  gap: 15px; /* Spacing between grid items */
}

.course-item {
  display: flex; /* Align checkbox and label horizontally */
  align-items: center; /* Vertically center them */
  background-color: #f4f4f4; /* Light background for each course item */
  padding: 10px 15px;
  border-radius: 5px;
  border: 1px solid #eee;
  transition: background-color 0.2s ease;
}

.course-item:hover {
  background-color: #e9e9e9; /* Slight hover effect */
}

.course-item input[type="checkbox"] {
  margin-right: 10px; /* Space between checkbox and label */
  /* Basic checkbox styling, could be enhanced with custom CSS */
  width: 18px;
  height: 18px;
  accent-color: #3498db; /* Sets the color of the checkbox */
}

.course-item label {
  font-weight: normal; /* Labels within list items don't need bold */
  margin-bottom: 0; /* Override default label margin */
  cursor: pointer;
  color: #444;
  flex-grow: 1; /* Allow label to take available space */
}

.course-item label span {
  font-size: 0.9em; /* Smaller font for course codes */
  color: #777; /* Lighter color for course codes */
}

.info-message {
  text-align: center;
  color: #777;
  font-style: italic;
  margin-top: 20px;
  padding: 10px;
  background-color: #f0f8ff; /* Light blue background */
  border: 1px solid #cceeff;
  border-radius: 5px;
}

/* -------------------- Button -------------------- */
button {
  display: block; /* Make button take full width */
  width: 100%;
  padding: 12px 20px;
  background-color: #3498db; /* Blue button */
  color: white;
  border: none;
  border-radius: 25px; /* Pill-shaped button */
  font-size: 1.1em;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
  margin-top: 30px; /* Space above button */
}

button:hover {
  background-color: #2980b9; /* Darker blue on hover */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15); /* Subtle shadow on hover */
}

button:disabled {
  background-color: #cccccc; /* Grayed out when disabled */
  cursor: not-allowed;
  box-shadow: none;
}

/* -------------------- Recommendations Box -------------------- */
.recommendations-box {
  margin-top: 30px;
  padding: 20px;
  background-color: #eaf6fc; /* Light blue background for recommendations */
  border: 1px solid #b3e0ff; /* Blue border */
  border-radius: 8px;
}

.recommendations-box h2 {
  color: #2980b9;
  margin-bottom: 15px;
  border-bottom: 1px solid #cceeff; /* Light blue separator */
  padding-bottom: 10px;
}

.recommendations-box ul {
  list-style: disc inside; /* Standard bullet points */
  padding-left: 0; /* Remove default padding */
}

.recommendations-box li {
  margin-bottom: 8px;
  color: #444;
}

.recommendations-box li span {
  font-size: 0.9em;
  color: #777;
}

/* -------------------- Basic Global Styles  -------------------- */
/* You might put these in src/assets/main.css or a global CSS file */
body {
  margin: 0;
  padding: 20px;
  background-color: #f0f2f5; /* Light grey background for the whole page */
}
</style>