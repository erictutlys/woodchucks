import streamlit as st
import plotly.express as px
import pandas as pd
import duckdb
import random
##
# Grab some population data (not verified)
##
st.header('How much wood? :wood:')
st.subheader('A Woodchuck Population Simulator built in Streamlit')
st.error("Attention! This is a woodchuck population simulator. Use with Caution!")
st.write("""
You can choose a state to release wild woodchucks, and how long to run the simulation.
""")
states = pd.read_csv('states.csv')
neighbors = pd.read_csv('state_neighbors.csv')

col1, col2, col3 = st.columns(3)

starting_state = col1.selectbox('Choose starting state', options=states['state'])
starting_number = col2.number_input('Starting Woodchucks',
                                  min_value=10, value=10, step=10)
spread_threshold = 20
reproduction_rate = 1.2
with st.expander("Advanced settings"):
    spread_threshold = st.number_input('Woodchucks required to spread states',
                                    min_value=10, value=20, step=1)
    reproduction_rate = round(st.number_input('Reproduction rate of woodchucks',
                                    min_value=1.0, value=1.5, step=0.1), 2)


latest = duckdb.query("""
    SELECT 
        state, 
        0 as day, 
        case when state = '{}' then {} else 0 end as population 
    FROM states
    """.format(starting_state, starting_number)).to_df()


def simulation(df, day):
    new_day = day + 1
    random_factor = random.randint(100, 200) * 1.0 / 100
    new_day_data = duckdb.query("""
        SELECT 
            df.state, 
            {0} as day,
            max(
                case 
                    when n.state is not null and df.population = 0 then {1}
                    when n.state is not null and df.population > 0 and df.population < 1000 then cast(population * {2} * {3} as int)
                    when n.state is null and df.population < 1000 then cast(df.population * {2} as int)
                    else df.population
                end
                ) as population,
        FROM df 
            left join 
                (
                    select
                        n1.state_neighbor as state
                    from
                        df d
                        left join neighbors n1 on d.state = n1.state
                    where
                        d.population > 20
                    group by 1
                    union all
                    select
                        n1.state as state
                    from
                        df d
                        left join neighbors n1 on d.state = n1.state_neighbor
                    where
                        d.population > 20
                    group by 1
                ) -- States that are neighboring a state with n>50
                 n on 
                n.state = df.state
        group by 1,2
        """.format(new_day, spread_threshold, reproduction_rate, random_factor)).to_df()
    return new_day_data


days = col3.number_input('Days to Simulate', min_value = 10, value=10, step = 10)

if st.button('Run Simulation'):
    for i in range(0, days):
        next_day = simulation(latest, int(latest['day'].max()))
        latest = pd.concat([latest, next_day])
        # if i % 10 == 0:
        #     st.write('Day ' + str(i))
        # st.write(next_day)
        end_check = duckdb.query("""
            SELECT
                min(population) as min_pop
            FROM next_day
        """).to_df().iloc[0]['min_pop']
        # st.write(end_check)
        if int(end_check) >= 1000:
            st.header('The Woodchucks Took Over On Day {}'.format(i))
            break
else:
    st.stop()

animated_viz = px.choropleth(latest, 
              locations = 'state',
              color="population", 
              animation_frame="day",
              color_continuous_scale="Earth",
              locationmode='USA-states',
              scope="usa",
              range_color=(0, 100), # latest['population'].max()*1.1),
              title='Woodchucks over time',
              height=600
             )
st.plotly_chart(animated_viz)
# st.write(latest)

line = px.line(latest, x='day', y=['population'], color='state')
st.plotly_chart(line)

st.header("How much wood did the woodchucks chuck?")

cola, colb, colc = st.columns(3)

total = duckdb.query("""
    SELECT 
        sum(population) * 700 as wood-- 700 lbs per day
    FROM latest
    """).to_df().iloc[0]['wood']

chucks = duckdb.query("""
    SELECT 
        sum(population) as chucks
    FROM latest
    where day = (select max(day) from latest)
    """).to_df().iloc[0]['chucks']
cola.metric(label="Pounds of Wood Chucked", value=total)
colb.metric(label="Woodchuck Final Population", value=chucks)
colc.header(":evergreen_tree:")
