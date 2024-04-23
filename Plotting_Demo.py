import streamlit as st
import pandas as pd
import altair as alt
from urllib.error import URLError

st.set_page_config(page_title="DataFrame Demo", page_icon="📊")

st.markdown("# DataFrame Demo")
st.sidebar.header("DataFrame Demo")
st.write(
    """This demo shows how to use `st.write` to visualize Pandas DataFrames.
(Data courtesy of the [UN Data Explorer](http://data.un.org/Explorer.aspx).)"""
)


@st.cache_data
def get_UN_data():
    df = pd.read_csv("pages/ky_strawberry2.csv", encoding='cp949')
    return df.set_index("수집일")


try:
    df = get_UN_data()
    countries = st.multiselect(
        "일자 선택", list(df.index), ["2024-01-01", "2024-01-02"]
    )
    if not countries:
        st.error("일자를 선택하세요.")
    else:
        data = df.loc[countries]
        st.write("### 경기도 딸기 스마트팜(시설원예) ICT, 생육 융복합 정보", data.sort_index())

        data = data.T.reset_index()
        data = pd.melt(data, id_vars=["index"]).rename(
            columns={"수집일": "외부습도", "value": "경기도 딸기 스마트팜(시설원예) ICT, 생육 융복합 정보"}
        )
        chart = (
            alt.Chart(data)
            .mark_area(opacity=0.3)
            .encode(
                x="외부습도:T",
                y=alt.Y("경기도 딸기 스마트팜(시설원예) ICT, 생육 융복합 정보:Q", stack=None),
                color="index:N",
            )
        )
        st.altair_chart(chart, use_container_width=True)
except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
        % e.reason
    )
