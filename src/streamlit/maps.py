import streamlit as st
from streamlit.components.v1 import html
import pandas as pd

df = pd.read_csv("data/final_data.csv")
data = df[["Широта", "Долгота"]].dropna().values.tolist()
info = [
    f"{row['Адрес']}<br><a href='{row['Ссылка на объявление']}' target='_blank'>Перейти к объявлению</a>"
    for _, row in df.iterrows()
]  

points = [{"coords": [row[0], row[1]], "info": info[i]} for i, row in enumerate(data)]

yandex_map_html = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://api-maps.yandex.ru/2.1/?lang=ru_RU" type="text/javascript"></script>
    <style>
        html, body, #map {{
            width: 100%; 
            height: 100%; 
            margin: 0; 
            padding: 0;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        ymaps.ready(init);
        function init() {{
            var myMap = new ymaps.Map("map", {{
                center: [55.751244, 37.618423], // Центр карты (Москва)
                zoom: 10
            }});

            // Данные меток
            var points = {points};

            // Добавление меток на карту
            points.forEach(function(point) {{
                var placemark = new ymaps.Placemark(point.coords, {{
                    balloonContent: point.info  // Информация при клике на метку
                }});
                myMap.geoObjects.add(placemark);
            }});
        }}
    </script>
</body>
</html>
"""

st.title("Яндекс.Карты с объявлениями и ссылками")
html(yandex_map_html, height=500)
