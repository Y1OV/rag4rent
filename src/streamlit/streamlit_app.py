import streamlit as st

main_page = st.Page("main.py", title="Главная"
# , icon=":material/add_circle:"
)
bot_page = st.Page("bot2.py", title="Чат-бот"
# , icon=":material/delete:"
)
maps_page = st.Page("maps.py", title="Карта"
# , icon=":material/delete:"
)

pg = st.navigation(
    {
            "Main": [main_page, bot_page, maps_page],
            # "Reports": []
        }
)
st.set_page_config(page_title="House bot"
# , page_icon=":material/edit:"
)
pg.run()




