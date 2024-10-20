import streamlit as st
import requests
import time
from constants import API_URL, DOWNLOAD_LINK


def start_calculate(*, base_file: bytes, secondary_file: bytes | None, use_secondary_file: bool, N: int) -> str|None:
    files = {
        'base_file': base_file,
        'secondary_file': secondary_file if use_secondary_file else None
    }
    data = {
        'use_secondary_file': str(use_secondary_file).lower(),
        'N': N
    }
    response = requests.post(f"{API_URL}/calculate/", files=files, data=data)
    if response.status_code == 200:
        return response.json()["calculate_id"]
    else:
        st.error("Ошибка при попытке расчета.")
        return None


def check_calculate_status(*, calculate_id: str) -> dict[str, str]:
    response = requests.get(f"{API_URL}/check-calculate-status/{calculate_id}")
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Ошибка при запросе статуса расчета.")
        return {"status": "error"}


st.title("Рекомендационная система")

base_file = st.file_uploader("Загрузите основной файл", type=["txt"])
st.write("""Каждая строка должна содержать данные в формате 'ID ID_друга 1, ID_друга 2',\nнапример:""")
st.code("""
    1 1, 3
    2 3
    3 1
""")

use_secondary_file = st.checkbox("Использовать файл с дополнительными параметрами?")

numbers_of_recomended = st.slider('Укажите количество рекомендованых друзей в итоговом файле',
                                  min_value=1,
                                  max_value=10,
                                  value=1)

secondary_file = None
if use_secondary_file:
    secondary_file = st.file_uploader("Загрузите файл с дополнительными параметрами", type=["txt"])
    st.write("""Каждая строка должна содержать данные в формате 'ID , Пол, Возраст, Город, Наличие высшего образования', 
    \nнапример:""")
    st.code("""
        1 1, 18, 0, 1
        2 0, 25, 1, 0
    """)

if st.button("Запустить расчет"):
    if base_file:
        calculate_id = start_calculate(base_file=base_file,
                                       secondary_file=secondary_file,
                                       use_secondary_file=use_secondary_file,
                                       N=numbers_of_recomended)
        if calculate_id:
            st.write(f"ID расчета: {calculate_id}")
            status_placeholder = st.empty()
            status = "in_progress"
            file_url = None
            while status == "in_progress":
                calculate_status = check_calculate_status(calculate_id=calculate_id)
                status = calculate_status["status"]
                if status == "completed":
                    file_url = calculate_status.get("file_url")
                status_placeholder.text(f"Статус расчета: {status}")
                time.sleep(2)
            if file_url:
                download_link = f"{DOWNLOAD_LINK}{calculate_id}"
                st.success(f"Расчет {calculate_id} завершен!")
                st.markdown(f"[Скачать результат]( {download_link} )")
    else:
        st.error("Пожалуйста, загрузите основной файл.")
