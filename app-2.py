import streamlit as st
import requests

BASE_URL = "http://localhost:8000" # unicorn -> restapi
#BASE_URL = "127.0.0.1:8000" # alternative IP

'''
def login():
    st.write("## Login")
    with st.form(key="login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            response = requests.post(f"{BASE_URL}/users/authenticate", json={'username': username, 'password': password})
            if response.status_code == 200:
                userdata = response.json()
                st.session_state["user"] = userdata
                st.success(f"Angemeldet {userdata['username']}") # json kein python objekt
                st.session_state["is_logged_in"] = True
                st.rerun()
            else:
                st.error(f"Fehler {response.status_code}")
                #st.info(f"Fehler {response.text})
'''

def welcome():
    user = st.session_state.get("User")
    id = user["id"]

    st.title("User Client")
    st.text(id)
    '''    
    task = st.text_input("Task")
    description = st.text_area("Description")
    deadline = st.date_input("Deadline", format="DD.MM.YYYY")
    state = st.selectbox("State", ["OPEN", "IN_PROGRESS", "DONE"])

    json_params = {
        #"username": username,
        #"password": password,
        "task": task,
        "description": description,
        "deadline": deadline.isoformat(),
        "state": state
    }

    try:
        if st.button("Todo erstellen"):
            response = requests.post(f"{BASE_URL}/todo/{user_id}/todos/", json=json_params)
            if response.status_code == 200:
                st.success("Todo erstellt")
                #st.json(response.json())
            else:
                st.error(f"Fehler {response.status_code}")
                #st.info(f"Fehler {response.text})
    
    except requests.exceptions.RequestException as e:
        st.error(f"Fehler mit Server:\n {e}")

st.session_state.setdefault( "is_logged_in", False)
'''
if st.session_state["user"]:
    welcome()

#if st.session_state["is_logged_in"] and "user" in st.session_state:
 #   welcome()
#else:
#    login()