# Subscription Intelligence Agent

Live Multi-Touch Attribution dashboard built on the real PCB/Criteo dataset.
original source data:  https://www.kaggle.com/datasets/sharatsachin/criteo-attribution-modeling

## Features
• Ask questions in plain English (“Top 10 last-touch campaigns” or “Which journey length has highest conversion rate?”)  
• Powered by Llama 3.1 8B via Groq (instant responses)  
• Journey-length analysis, Last-Touch, First-Touch, and Markov Chain attribution  
• Zero setup—runs entirely on DuckDB (single file)  

## How to run locally
1. Clone repo  
2. `pip install streamlit duckdb groq plotly pandas channel-attribution`  
3. Add your Groq key to `.streamlit/secrets.toml`  
   `GROQ_API_KEY = "gsk_..."`
4. Run mta-project.ipynb    
5. `streamlit run app.py`  

## Screen shots
<img width="3374" height="1008" alt="image" src="https://github.com/user-attachments/assets/b2170660-841f-4a08-b60e-92da737c828d" />


Built by James Hopper – 17+ years scaling analytics at FOX, The Arena Group, Hearst, iHeartMedia.
