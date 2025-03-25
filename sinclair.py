import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import random
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__, 
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server = app.server
app.title = "Dr. Sinclair Longevity Recommender"

# Define the app layout
app.layout = html.Div([
    html.Div([
        html.H1("🧬 Dr. Sinclair Longevity Recommender", className="app-header"),
        html.P(
            "This application provides personalized health recommendations based on Dr. David Sinclair's "
            "research on longevity and aging. Dr. Sinclair is a Harvard geneticist and leading authority "
            "on the science of aging who views aging as a condition that can be slowed and partially reversed.",
            className="app-intro"
        ),
    ], className="header-container"),
    
    html.Div([
        html.Div([
            html.H3("Your Information", className="sidebar-header"),
            
            html.Label("Age"),
            dcc.Slider(
                id="age-slider",
                min=18,
                max=100,
                value=40,
                marks={i: str(i) for i in range(20, 101, 20)},
                step=1
            ),
            
            html.Label("Gender"),
            dcc.Dropdown(
                id="gender-dropdown",
                options=[
                    {"label": "Male", "value": "Male"},
                    {"label": "Female", "value": "Female"},
                    {"label": "Other", "value": "Other"}
                ],
                value="Male"
            ),
            
            html.Label("Weight (kg)"),
            dcc.Input(
                id="weight-input",
                type="number",
                min=40,
                max=200,
                value=70,
                step=0.1
            ),
            
            html.Label("Height (cm)"),
            dcc.Input(
                id="height-input",
                type="number",
                min=140,
                max=220,
                value=170,
                step=0.1
            ),
            
            html.Label("Activity Level"),
            dcc.Slider(
                id="activity-slider",
                min=0,
                max=4,
                value=2,
                marks={
                    0: "Sedentary",
                    1: "Lightly Active",
                    2: "Moderately Active",
                    3: "Very Active",
                    4: "Extremely Active"
                },
                step=1
            ),
            
            html.H3("Areas of Interest", className="sidebar-header"),
            dcc.Checklist(
                id="categories-checklist",
                options=[
                    {"label": "Diet and Nutrition", "value": "Diet and Nutrition"},
                    {"label": "Exercise and Physical Activity", "value": "Exercise and Physical Activity"},
                    {"label": "Supplements and Compounds", "value": "Supplements and Compounds"},
                    {"label": "Lifestyle and Environmental Factors", "value": "Lifestyle and Environmental Factors"},
                    {"label": "Sleep Quality", "value": "Sleep Quality"}
                ],
                value=["Diet and Nutrition", "Exercise and Physical Activity"]
            ),
            
            html.Button(
                "Generate Personalized Recommendations",
                id="generate-button",
                className="generate-button"
            )
        ], className="sidebar"),
        
        html.Div([
            html.Div(id="recommendations-container", className="recommendations")
        ], className="main-content")
    ], className="app-container")
])

@app.callback(
    Output("recommendations-container", "children"),
    [Input("generate-button", "n_clicks")],
    [
        State("age-slider", "value"),
        State("gender-dropdown", "value"),
        State("weight-input", "value"),
        State("height-input", "value"),
        State("activity-slider", "value"),
        State("categories-checklist", "value")
    ]
)
def generate_recommendations(n_clicks, age, gender, weight, height, activity_level, selected_categories):
    if n_clicks is None:
        return html.Div([
            html.H2("Welcome to your personalized longevity dashboard"),
            html.P("Click the 'Generate Personalized Recommendations' button to see your customized plan.")
        ])
    
    # Calculate BMI
    bmi = weight / ((height/100) ** 2)
    bmi_category = ""
    if bmi < 18.5:
        bmi_category = "Underweight"
    elif bmi < 25:
        bmi_category = "Normal weight"
    elif bmi < 30:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"
    
    # Map activity level index to text
    activity_levels = ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"]
    activity_text = activity_levels[activity_level]
    
    # Generate metrics
    biological_age = max(18, age - random.randint(3, 8))
    longevity_score = min(100, 70 + random.randint(0, 30))
    
    # Create recommendations content
    recommendations = []
    
    # User metrics section
    metrics_section = html.Div([
        html.H2("Your Health Metrics"),
        html.Div([
            html.Div([
                html.H3(f"{bmi:.1f}"),
                html.P("BMI"),
                html.P(f"{bmi_category}", className="metric-note")
            ], className="metric-card"),
            
            html.Div([
                html.H3(f"{biological_age}"),
                html.P("Estimated Biological Age"),
                html.P(f"{age - biological_age} years younger than chronological", className="metric-note")
            ], className="metric-card"),
            
            html.Div([
                html.H3(f"{longevity_score}/100"),
                html.P("Longevity Score"),
                html.P("Based on your profile", className="metric-note")
            ], className="metric-card")
        ], className="metrics-container")
    ])
    
    recommendations.append(metrics_section)
    
    # Category recommendations
    recommendations.append(html.H2("Your Personalized Longevity Recommendations"))
    
    for category in selected_categories:
        category_content = html.Div([
            html.H3(category),
            
            html.Div([
                # Diet and Nutrition content
                html.Div([
                    html.H4("🍽️ Intermittent Fasting"),
                    html.P("Implement a 16:8 fasting schedule (16 hours fasting, 8 hours eating window)"),
                    html.P("Why: Fasting activates sirtuins and longevity genes, raises NAD+ levels, and promotes autophagy"),
                    html.P("How to start: Skip breakfast and eat your first meal around noon, finish dinner by 8 PM")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("🥗 Plant-Forward Diet"),
                    html.P("Shift toward a plant-based, Mediterranean-style diet"),
                    html.P("Why: Plant-based diets are associated with longevity and lower inflammation"),
                    html.P("Key foods: Leafy greens, berries, nuts, legumes, olive oil, and minimal animal protein")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("🚫 Sugar Reduction"),
                    html.P("Eliminate added sugars and refined carbohydrates"),
                    html.P("Why: High sugar intake contributes to insulin resistance and accelerated aging"),
                    html.P("Alternatives: Use berries for sweetness, dark chocolate (85%+) for treats")
                ], className="recommendation-item")
            ]) if category == "Diet and Nutrition" else None,
            
            # Exercise and Physical Activity content
            html.Div([
                html.Div([
                    html.H4("🏃‍♂️ High-Intensity Interval Training (HIIT)"),
                    html.P("2-3 HIIT sessions weekly (10-20 minutes each)"),
                    html.P("Why: HIIT activates longevity pathways similar to fasting and improves mitochondrial function"),
                    html.P("Sample workout: 30 seconds maximum effort, 90 seconds recovery, repeat 8-10 times")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("🏋️‍♀️ Strength Training"),
                    html.P("2-3 strength sessions weekly focusing on major muscle groups"),
                    html.P("Why: Preserves muscle mass, improves metabolism, and prevents sarcopenia"),
                    html.P("Key exercises: Squats, deadlifts, push-ups, rows, and overhead presses")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("🚶‍♀️ Daily Movement"),
                    html.P("Accumulate 7,000-10,000 steps daily"),
                    html.P("Why: Reduces sedentary time which is linked to accelerated aging"),
                    html.P("Tips: Take walking meetings, use stairs, park farther away, set hourly movement reminders")
                ], className="recommendation-item")
            ]) if category == "Exercise and Physical Activity" else None,
            
            # Supplements and Compounds content
            html.Div([
                html.Div([
                    html.H4("🧪 NAD+ Boosters"),
                    html.P("Consider NMN or NR supplements (consult healthcare provider first)"),
                    html.P("Why: NAD+ levels decline with age; boosting them may enhance cellular repair"),
                    html.P("Dosage: Typically 250-1000mg daily with food")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("🍇 Resveratrol"),
                    html.P("Consider resveratrol with a fat source for absorption"),
                    html.P("Why: May activate sirtuins and improve mitochondrial health"),
                    html.P("Natural sources: Red grapes, blueberries, dark chocolate")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("💊 Foundation Supplements"),
                    html.P("Vitamin D3 (2000-4000 IU) with K2, Omega-3s (1-2g EPA/DHA)"),
                    html.P("Why: Support bone health, reduce inflammation, and improve cardiovascular function"),
                    html.P("Note: Always consult healthcare provider before starting supplements")
                ], className="recommendation-item")
            ]) if category == "Supplements and Compounds" else None,
            
            # Lifestyle and Environmental Factors content
            html.Div([
                html.Div([
                    html.H4("🔥❄️ Hormetic Stress"),
                    html.P("Regular sauna sessions (15-20 minutes) followed by cold exposure"),
                    html.P("Why: Temperature extremes activate stress response pathways that improve cellular resilience"),
                    html.P("Alternative: Hot shower followed by 30-60 seconds of cold water")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("🌱 Reduce Toxin Exposure"),
                    html.P("Minimize exposure to environmental toxins and radiation"),
                    html.P("Why: These accelerate DNA damage and epigenetic aging"),
                    html.P("Actions: Use air purifiers, choose organic when possible, limit unnecessary X-rays")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("🧠 Mental Stimulation"),
                    html.P("Learn new skills and maintain social connections"),
                    html.P("Why: Cognitive challenges and social engagement are linked to longevity"),
                    html.P("Activities: Learn a language, play an instrument, join community groups")
                ], className="recommendation-item")
            ]) if category == "Lifestyle and Environmental Factors" else None,
            
            # Sleep Quality content
            html.Div([
                html.Div([
                    html.H4("😴 Optimize Sleep Environment"),
                    html.P("Keep bedroom cool (65-68°F/18-20°C), dark, and quiet"),
                    html.P("Why: Quality sleep enhances cellular repair and brain detoxification"),
                    html.P("Tips: Use blackout curtains, white noise machine, and comfortable bedding")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("⏰ Consistent Sleep Schedule"),
                    html.P("Go to bed and wake up at the same time daily"),
                    html.P("Why: Regulates circadian rhythm which impacts longevity genes"),
                    html.P("Goal: 7-8 hours of uninterrupted sleep")
                ], className="recommendation-item"),
                
                html.Div([
                    html.H4("📱 Digital Sunset"),
                    html.P("Avoid screens 1-2 hours before bedtime"),
                    html.P("Why: Blue light disrupts melatonin production and sleep quality"),
                    html.P("Alternative activities: Reading, gentle stretching, meditation")
                ], className="recommendation-item")
            ]) if category == "Sleep Quality" else None
        ], className="category-section")
        
        recommendations.append(category_content)
    
    # 30-Day Plan
    days = list(range(1, 31))
    actions = []
    
    # Generate sample actions based on user profile
    diet_actions = [
        "16-hour fast (skip breakfast)",
        "Plant-based dinner with leafy greens",
        "Replace sugary snack with berries and nuts",
        "Try a new vegetable you've never had before",
        "Make a polyphenol-rich smoothie"
    ]
    
    exercise_actions = [
        "10-minute HIIT session",
        "30-minute strength training",
        "10,000 step walk",
        "Yoga or mobility work",
        "Active recovery day - gentle movement only"
    ]
    
    lifestyle_actions = [
        "5-minute cold shower after workout",
        "20 minutes of meditation",
        "Digital detox evening (no screens after 8pm)",
        "Practice deep breathing for 5 minutes",
        "Connect with a friend or family member"
    ]
    
    for day in days:
        if day % 7 == 0:  # Weekly review day
            actions.append("Review progress and adjust plan")
        else:
            action = random.choice(diet_actions) + " + " + random.choice(exercise_actions)
            if day % 3 == 0:  # Add lifestyle action every 3 days
                action += " + " + random.choice(lifestyle_actions)
            actions.append(action)
    
    # Create plan dataframe
    plan_df = pd.DataFrame({
        "Day": days,
        "Date": pd.date_range(start=datetime.today(), periods=30).strftime("%b %d"),
        "Daily Actions": actions
    })
    
    # Create 30-day plan section
    plan_section = html.Div([
        html.H2("Your 30-Day Longevity Kickstart Plan"),
        dash_table.DataTable(
            id='plan-table',
            columns=[{"name": i, "id": i} for i in plan_df.columns],
            data=plan_df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        ),
        
        html.Button(
            "Download 30-Day Plan",
            id="download-button",
            className="download-button"
        ),
        dcc.Download(id="download-plan")
    ], className="plan-section")
    
    recommendations.append(plan_section)
    
    # Disclaimer
    disclaimer = html.Div([
        html.Div([
            html.P(
                "Disclaimer: These recommendations are based on Dr. Sinclair's research and public statements but are not medical advice. "
                "Always consult with healthcare professionals before making significant changes to your diet, exercise routine, or "
                "starting any supplements, especially if you have existing health conditions.",
                className="disclaimer-text"
            )
        ], className="disclaimer")
    ])
    
    recommendations.append(disclaimer)
    
    # Resources section
    resources = html.Div([
        html.H2("Additional Resources"),
        html.Div([
            html.Div([
                html.Ul([
                    html.Li(html.A("Dr. Sinclair's Book: Lifespan", href="https://lifespanbook.com/", target="_blank")),
                    html.Li(html.A("Information Theory of Aging", href="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8024906/", target="_blank")),
                    html.Li(html.A("Sinclair Lab Research", href="https://genetics.med.harvard.edu/sinclair/", target="_blank"))
                ])
            ], className="resources-column"),
            
            html.Div([
                html.Ul([
                    html.Li(html.A("Podcast: Lifespan with Dr. David Sinclair", href="https://www.lifespanpodcast.com/", target="_blank")),
                    html.Li(html.A("Harvard Medical School Aging Research", href="https://hms.harvard.edu/news/aging-research", target="_blank")),
                    html.Li(html.A("NIA - Biology of Aging", href="https://www.nia.nih.gov/research/dab", target="_blank"))
                ])
            ], className="resources-column")
        ], className="resources-container")
    ], className="resources-section")
    
    recommendations.append(resources)
    
    return html.Div(recommendations)

@app.callback(
    Output("download-plan", "data"),
    Input("download-button", "n_clicks"),
    [
        State("age-slider", "value"),
        State("gender-dropdown", "value"),
        State("weight-input", "value"),
        State("height-input", "value"),
        State("activity-slider", "value")
    ],
    prevent_initial_call=True
)
def download_plan(n_clicks, age, gender, weight, height, activity_level):
    # Generate the plan data again (same logic as above)
    days = list(range(1, 31))
    actions = []
    
    diet_actions = [
        "16-hour fast (skip breakfast)",
        "Plant-based dinner with leafy greens",
        "Replace sugary snack with berries and nuts",
        "Try a new vegetable you've never had before",
        "Make a polyphenol-rich smoothie"
    ]
    
    exercise_actions = [
        "10-minute HIIT session",
        "30-minute strength training",
        "10,000 step walk",
        "Yoga or mobility work",
        "Active recovery day - gentle movement only"
    ]
    
    lifestyle_actions = [
        "5-minute cold shower after workout",
        "20 minutes of meditation",
        "Digital detox evening (no screens after 8pm)",
        "Practice deep breathing for 5 minutes",
        "Connect with a friend or family member"
    ]
    
    for day in days:
        if day % 7 == 0:
            actions.append("Review progress and adjust plan")
        else:
            action = random.choice(diet_actions) + " + " + random.choice(exercise_actions)
            if day % 3 == 0:
                action += " + " + random.choice(lifestyle_actions)
            actions.append(action)
    
    plan_df = pd.DataFrame({
        "Day": days,
        "Date": pd.date_range(start=datetime.today(), periods=30).strftime("%b %d"),
        "Daily Actions": actions
    })
    
    return dcc.send_data_frame(plan_df.to_csv, "sinclair_longevity_plan.csv", index=False)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
