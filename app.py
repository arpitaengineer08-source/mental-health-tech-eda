import streamlit as st
import pickle
import pandas as pd

# Load the trained model
with open("diabetes_model.pkl", "rb") as f:
    model = pickle.load(f)

# Page config
st.set_page_config(
    page_title="Diabetes Prediction App",
    page_icon="💉",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Title and description
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>💉 Diabetes Prediction App</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Enter your health details below to check diabetes risk</p>", unsafe_allow_html=True)
st.markdown("---")

# Input section in columns
st.subheader("Patient Information")
col1, col2 = st.columns(2)

with col1:
    pregnancies = st.number_input("Number of Pregnancies", min_value=0, max_value=20, value=0)
    glucose = st.number_input("Glucose Level", min_value=0, max_value=300, value=120)
    blood_pressure = st.number_input("Blood Pressure", min_value=0, max_value=200, value=70)
    skin_thickness = st.number_input("Skin Thickness", min_value=0, max_value=100, value=20)

with col2:
    insulin = st.number_input("Insulin Level", min_value=0, max_value=900, value=79)
    bmi = st.number_input("BMI", min_value=0.0, max_value=70.0, value=25.0)
    dpf = st.number_input("Diabetes Pedigree Function", min_value=0.0, max_value=3.0, value=0.5)
    age = st.number_input("Age", min_value=0, max_value=120, value=33)

st.markdown("---")

# Predict button
if st.button("Predict"):
    input_data = pd.DataFrame([[pregnancies, glucose, blood_pressure, skin_thickness,
                                insulin, bmi, dpf, age]],
                              columns=["Pregnancies","Glucose","BloodPressure",
                                       "SkinThickness","Insulin","BMI","DiabetesPedigreeFunction","Age"])
    
    prediction = model.predict(input_data)[0]

    if prediction == 1:
        st.error("⚠️ The model predicts: **Diabetic**")
        st.markdown("<p style='color: red;'>Please consult a doctor immediately for proper diagnosis.</p>", unsafe_allow_html=True)
    else:
        st.success("✅ The model predicts: **Not Diabetic**")
        st.markdown("<p style='color: green;'>Keep a healthy lifestyle to maintain your health!</p>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Developed by Arpita Sharma | 2026</p>", unsafe_allow_html=True)