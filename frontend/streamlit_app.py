import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8001/evaluate"

st.set_page_config(page_title="Decision Companion System", layout="wide")

st.title("⚖️ Decision Companion System")
st.markdown("Evaluate real-world decisions using Weighted Multi-Criteria Decision Making (WMCDM).")

# Initialize session state for dynamic lists
if 'criteria' not in st.session_state:
    st.session_state.criteria = [{"name": "", "weight": 1.0}]
if 'options' not in st.session_state:
    st.session_state.options = [{"name": ""}]

st.header("1. Decision Profile")
decision_name = st.text_input("Decision Name", placeholder="e.g., Choosing a New Apartment")

st.header("2. Criteria & Weights")
st.markdown("Define the criteria that matter to you and assign a weight (> 0) to each.")

# Show criteria input
for i, crit in enumerate(st.session_state.criteria):
    cols = st.columns([3, 1, 1])
    with cols[0]:
        crit["name"] = st.text_input(f"Criterion {i+1} Name", value=crit["name"], key=f"crit_name_{i}")
    with cols[1]:
        crit["weight"] = st.number_input(f"Weight", value=crit["weight"], min_value=0.1, step=0.1, key=f"crit_weight_{i}")
    with cols[2]:
        if st.markdown("<br>", unsafe_allow_html=True) and st.button("Remove", key=f"remove_crit_{i}"):
            st.session_state.criteria.pop(i)
            st.rerun()

if st.button("➕ Add Criterion"):
    st.session_state.criteria.append({"name": "", "weight": 1.0})
    st.rerun()

st.header("3. Options & Scoring")
st.markdown("Add options and score them from 0 to 10 for each criterion.")

# Filter out empty criteria names for table
valid_criteria = [c["name"] for c in st.session_state.criteria if c["name"].strip()]

for i, opt in enumerate(st.session_state.options):
    st.subheader(f"Option {i+1}")
    cols = st.columns([3, 1])
    with cols[0]:
        opt["name"] = st.text_input("Option Name", value=opt["name"], key=f"opt_name_{i}")
    with cols[1]:
        if st.button("Remove Option", key=f"remove_opt_{i}"):
            st.session_state.options.pop(i)
            st.rerun()
            
    if valid_criteria:
        if "scores" not in opt:
            opt["scores"] = {}
            
        score_cols = st.columns(len(valid_criteria))
        for j, crit_name in enumerate(valid_criteria):
            current_score = opt["scores"].get(crit_name, 5.0)
            with score_cols[j]:
                opt["scores"][crit_name] = st.slider(
                    f"Score: {crit_name}", 
                    min_value=0.0, max_value=10.0, value=float(current_score), step=0.5,
                    key=f"score_{i}_{j}"
                )
    else:
        st.info("Add criteria above to score this option.")

if st.button("➕ Add Option"):
    st.session_state.options.append({"name": "", "scores": {}})
    st.rerun()

st.markdown("---")
# Submit section
if st.button("🚀 Evaluate Decision", type="primary"):
    if not decision_name.strip():
        st.error("Please enter a decision name.")
    elif len(valid_criteria) == 0:
        st.error("Please add at least one valid criterion.")
    elif not all(opt["name"].strip() for opt in st.session_state.options) or len(st.session_state.options) == 0:
        st.error("Please add at least one valid option with a name.")
    else:
        # Build payload
        payload = {
            "decision_name": decision_name,
            "criteria": [{"name": c["name"], "weight": c["weight"]} for c in st.session_state.criteria if c["name"].strip()],
            "options": []
        }
        
        for opt in st.session_state.options:
            if opt["name"].strip():
                # ensure we only send scores for valid criteria
                clean_scores = {c: opt["scores"].get(c, 0.0) for c in valid_criteria}
                payload["options"].append({
                    "name": opt["name"],
                    "scores": clean_scores
                })
                
        with st.spinner("Evaluating..."):
            try:
                response = requests.post(API_URL, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    st.success("Evaluation Complete!")
                    
                    st.header(f"Results: {data['decision_name']}")
                    
                    # Display Results
                    ranking = data["ranking"]
                    
                    # Create result DataFrame
                    df_data = []
                    for rank in ranking:
                        row = {
                            "Rank": rank["rank"],
                            "Option": rank["option_name"],
                            "Final Score": f"{rank['final_score']:.2f}"
                        }
                        # Add contributions
                        for crit, cont in rank["contributions"].items():
                            row[f"Contrib: {crit}"] = f"{cont:.2f}"
                        df_data.append(row)
                        
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    st.subheader("Explanations")
                    for rank in ranking:
                        with st.expander(f"#{rank['rank']} - {rank['option_name']} (Score: {rank['final_score']:.2f})", expanded=(rank['rank']==1)):
                            st.write(rank["explanation"])
                            
                else:
                    try:
                        error_detail = response.json().get('detail', 'Unknown error')
                    except requests.exceptions.JSONDecodeError:
                        error_detail = f"Server responded with status {response.status_code} and non-JSON content. (Please ensure you are connected to the correct API_URL)"
                    st.error(f"Error from backend: {error_detail}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend. Is the FastAPI server running?")
