import streamlit as st
import pandas as pd
import json
import bigjson
from owlready2 import *
import pickle
import psycopg2
import ast
import pandas.io.sql as psql
st.write("Here's our first attempt at using data to create a table:")


@st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

@st.cache_data(ttl=600)
def run_query(query):
    print(query)
    with conn.cursor() as cur:
        cur.execute(query)
        res = cur.fetchall()
        return res, [desc[0] for desc in cur.description]


@st.cache_data(ttl=600)
def get_pubmed_data():
    return json.load(open("../Data/pubmed_search_results_100.json","r"))

#@st.cache_data
def get_ontology_data():
    #ordo_onto = get_ontology("../ordo.owl").load()
    human_onto = get_ontology("../HumanDO.owl").load()
    sync_reasoner()
    st.write("ontology reading done")
    return human_onto 

disease = {}
common_entities = set()

def get_entity_property(x):
    #df = pd.DataFrame(columns = df_col_list)
    temp = {}
    for prop in x.get_properties(x):
        
        #print(prop.name,prop.label, "=", prop[x])
        key = prop.label.first()
        #print(key)
        if key == None:
            temp["disease_name"] = prop[x]
            print(prop[x])
        else:
            temp[key] = prop[x]
    #print(temp)
        if key == "database_cross_reference":
            print(prop[x])
            for data_id in prop[x]:
                #print("human_onto", x.id[0])
                ordo_entity = ordo_onto.search(hasDbXref = data_id).first()
                if x.id[0] == ordo_entity.id.first():
                    #print("yes")
                    common_entities.add(ordo_entity)
    return temp

def get_entity(entity):
    temp = []
    for subclass_of_mental_health in list(entity.subclasses()):
        x = subclass_of_mental_health
        if len(list(x.descendants(include_self = False))) == 0:
            #print("getting prop of", x)
            temp.append(get_entity_property(x))
        else:
            #print(x.label)
            disease[str(x.label[0])] =get_entity(x)

    return temp



@st.cache_data
def get_rare_disease_data():
    df = pd.read_csv("../Rare_Disease.csv")
    return  df.set_index("Disease_Name")

def load_rare_disease():
    df = get_rare_disease_data()
    if not disease_name:
        st.errors("Please select atleast one disease name")
    else:
        data = df.loc[disease_name]
        #st.write("### Details of the disease", data.sort_index())
        #print(data.to_dict())
        data_dict = data.to_dict()
        for key, value in data_dict.items():
            print(key)
            if value == value:
                cols = st.columns(2)
                cols[0] = st.write(f"## {key.capitalize()}")
                cols[1] = st.write("\n \n ".join(ast.literal_eval(value)))
        #show_ontogy_details(disease_name)
        #get_pubmed_data(disease_name[0])

def show_ontogy_details():
    #st.write(f'<iframe src="https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=C84525"></iframe>',unsafe_allow_html=True,   ) 
    human_onto = get_ontology_data()
    for name in disease_name:
        st.write(name)
        human_results = human_onto.search(label =name , _case_sensitive = False)
        for res in human_results:
            st.write("# ",res)

            for prop in res.get_properties(res):
                st.write(prop)
                st.write(prop[res])

        #st.write(ordo_results)
    #st.write("COmpleted",ordo_results)


def get_pubmed_data():
    rows,column_name = run_query(f"SELECT * from rare_disease where query_term like '%{disease_name}%' limit 10")
    print("pubmed_called")
    st.write("# Pubmed Search")

    
    for i,row in enumerate(rows):
        expander = st.expander(f"Result {i+1} for {disease_name}")
        with expander:

            for key, value in zip(column_name, row):
                if not value:
                    continue
                col = st.columns(2,gap = "small")
                col[0].write(key.replace("_"," ").capitalize())
                col[1].write(value)
#@st.cache_data
def get_mined_data():
    with st.spinner("Wait, we are fetching data"):
        st.write("## Text Mining")
        textminig_df = psql.read_sql_query(f"select * from human_disease_text_mining_channel where disease_name ilike \'{disease_name}\' limit 10 ", conn)
        st.write(textminig_df)
        
        st.write("## Knowledge")
        knowledge_df = psql.read_sql(f"select * from human_disease_knowledge_channel where disease_name ilike \'{disease_name}\' limit 10; ", conn)
        st.write(knowledge_df)

        st.write("## Experiments")
        knowledge_df = psql.read_sql(f"select * from human_disease_experiment_channel where disease_name ilike \'{disease_name}\' limit 10; ", conn)
        st.write(knowledge_df)
    st.success('Done!')


def create_tab(tab_names):
    return st.tabs(tab_names)


df = get_rare_disease_data()
disease_name = st.selectbox("Choose Disease Name", tuple(df.index))



if __name__ == "__main__":
    #st.write( get_pubmed_data())

    #human_onto,ordo_onto = get_ontology_data()
    tabs = create_tab(["Nord","Pubmed","Mined From Literature"])
    for  i,tab in enumerate(tabs):
        if i==0:
            with tab:
                load_rare_disease()
        if i==1:
            with tab:
                get_pubmed_data()

        if i == 2:
            with tab:
                get_mined_data()
        if i == 3:
            with tab:
                show_ontogy_details()
