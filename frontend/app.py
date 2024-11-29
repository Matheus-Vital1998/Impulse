import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Define the backend URL
backend_url = "http://api:5000"  # Replace with your actual backend URL if different

# Initialize session state
if 'pages' not in st.session_state:
    st.session_state.pages = ["Home"]

if 'page' not in st.session_state:
    st.session_state.page = 'Home'

if 'attributes' not in st.session_state:
    st.session_state.attributes = []

if 'extraction_finished' not in st.session_state:
    st.session_state.extraction_finished = False

if 'extracted_attributes' not in st.session_state:
    st.session_state.extracted_attributes = []

if 'data_preprocessed' not in st.session_state:
    st.session_state.data_preprocessed = False

if 'model_trained' not in st.session_state:
    st.session_state.model_trained = False

if 'prediction_made' not in st.session_state:
    st.session_state.prediction_made = False

if 'trained_model_info' not in st.session_state:
    st.session_state.trained_model_info = {}

if 'prediction_info' not in st.session_state:
    st.session_state.prediction_info = {}

# Function to update available pages based on step completion
def update_pages():
    pages = ["Home", "Attribute Selection"]
    
    if st.session_state.get('extraction_finished', False):
        pages.append("Data Preprocessing")
    else:
        # Reset subsequent flags
        st.session_state.data_preprocessed = False
        st.session_state.model_trained = False
        st.session_state.prediction_made = False
    
    if st.session_state.get('data_preprocessed', False):
        pages.append("XGBoost Train")
    else:
        st.session_state.model_trained = False
        st.session_state.prediction_made = False
    
    if st.session_state.get('model_trained', False):
        pages.append("Prediction and Anomaly Detection")
    else:
        st.session_state.prediction_made = False
    
    st.session_state.pages = pages

# Function to navigate between pages
def navigate_to(page):
    st.session_state.page = page
    update_pages()
    st.rerun()

# Update pages initially
update_pages()

# Sidebar navigation
selected_page = st.sidebar.radio(
    "Navigation",
    st.session_state.pages,
    index=st.session_state.pages.index(st.session_state.page)
)

# Function for "Home" page
def home():
    st.title("Welcome to the Data Processing System")
    st.header("Checking backend health...")
    # Perform health-check automatically
    try:
        response = requests.get(f"{backend_url}/health")
        if response.status_code == 200:
            data = response.json()
            st.success(f"Status: {data['status']}")
            st.write(f"Orion Version: {data.get('orion_version', 'N/A')}")
        else:
            st.error(f"Error: {response.status_code}")
            st.write(response.json())
    except Exception as e:
        st.error(f"An error occurred: {e}")

    st.subheader("Select the process type")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Simplified Process"):
            st.info("Simplified Process selected.")
            # Implement simplified process logic if needed
            navigate_to('Attribute Selection')
    with col2:
        if st.button("Detailed Process"):
            st.info("Detailed Process selected.")
            navigate_to('Attribute Selection')

# Function for "Attribute Selection" page
def attribute_selection():
    st.title("Attribute Selection")

    # If user re-executes this step, reset subsequent steps
    st.session_state.extraction_finished = False
    st.session_state.data_preprocessed = False
    st.session_state.model_trained = False
    st.session_state.prediction_made = False
    update_pages()

    # Check if mapping data is already fetched
    if 'mapping_data' not in st.session_state:
        st.write("Fetching attribute mapping...")
        try:
            response = requests.get(f"{backend_url}/attribute-mapping")
            if response.status_code == 200:
                mapping_data = response.json()
                st.session_state.mapping_data = mapping_data
                st.success("Attribute mapping fetched successfully.")
            else:
                st.error(f"Error: {response.status_code}")
                st.write(response.json())
                return
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return
    else:
        mapping_data = st.session_state.mapping_data

    # Clear message after data is fetched
    st.empty()

    # Verify if data is obtained
    if not mapping_data or 'entities' not in mapping_data or not mapping_data['entities']:
        st.warning("No data returned by the API. Check if the backend is returning data correctly.")
        return

    # Prepare data for display in table
    attributes_list = []
    for entity in mapping_data.get('entities', []):
        entity_id = entity.get('entity_id')
        entity_type = entity.get('entity_type', 'type_unknown')  # Adjust if necessary
        for attribute in entity.get('attributes', []):
            attributes_list.append({
                'Extract': False,
                'Attribute': attribute,
                'Entity': entity_id,
                'Type': entity_type
            })

    # Convert to DataFrame
    df_attributes = pd.DataFrame(attributes_list)

    if df_attributes.empty:
        st.warning("No attributes available for display.")
        return

    # Add select/deselect all option
    select_all = st.checkbox("Select/Deselect All", value=False)

    # Update 'Extract' column based on 'select_all' checkbox
    df_attributes['Extract'] = select_all

    # Display table with checkboxes
    edited_df = st.data_editor(df_attributes, use_container_width=True)

    st.session_state.attributes = edited_df[edited_df['Extract']].to_dict('records')

    # Field for entity limit, hidden initially
    with st.expander("Didn't get all entities?"):
        limit = st.number_input("Specify a higher entity limit", min_value=1, value=100, step=1)
        if st.button("Remap"):
            try:
                params = {'limit': limit}
                response = requests.get(f"{backend_url}/attribute-mapping", params=params)
                if response.status_code == 200:
                    mapping_data = response.json()
                    st.session_state.mapping_data = mapping_data
                    st.rerun()
                else:
                    st.error(f"Error: {response.status_code}")
                    st.write(response.json())
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Date range fields
    st.subheader("Select the date range for extraction")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        date_from = st.date_input("Start Date", value=datetime(2016, 1, 1))
    with date_col2:
        date_to = st.date_input("End Date", value=datetime(2025, 1, 31))

    # Button to extract data
    if st.button("Extract Data"):
        if not st.session_state.attributes:
            st.error("Please select at least one attribute to extract.")
        else:
            # Build payload for extraction API
            entities = {}
            for item in st.session_state.attributes:
                entity_id = item['Entity']
                entity_type = item['Type']
                key = (entity_id, entity_type)
                if key not in entities:
                    entities[key] = set()
                entities[key].add(item['Attribute'])

            entities_list = []
            for (entity_id, entity_type), attrs in entities.items():
                entities_list.append({
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "attributes": list(attrs)
                })

            extraction_payload = {
                "entities": entities_list
            }

            # Save extraction parameters in session_state
            st.session_state.extraction_payload = extraction_payload

            # Convert dates to ISO 8601
            date_from_str = date_from.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            date_to_str = date_to.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            st.session_state.extraction_params = {'date_from': date_from_str, 'date_to': date_to_str}

            st.session_state.extraction_finished = False
            st.session_state.extraction_in_progress = True

            # Update pages
            update_pages()

            # Update extracted_attributes with concatenated format
            st.session_state.extracted_attributes = [f"{attr['Entity']}_{attr['Attribute']}" for attr in st.session_state.attributes]

            # Start extraction directly on this screen
            st.write("Starting data extraction...")
            extraction_payload = st.session_state.extraction_payload
            params = st.session_state.extraction_params
            headers = {'Content-Type': 'application/json'}

            try:
                with st.spinner("Extracting data, please wait..."):
                    response = requests.post(f"{backend_url}/extract-data", params=params, headers=headers, json=extraction_payload)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(data.get('message', 'Data extracted successfully.'))
                        st.session_state.extraction_finished = True
                        st.session_state.extraction_in_progress = False
                        # Update pages after successful extraction
                        update_pages()
                        # Navigate to "Data Preprocessing" screen
                        navigate_to('Data Preprocessing')
                    else:
                        st.error(f"Error: {response.status_code}")
                        st.write(response.json())
                        st.session_state.extraction_finished = False
                        st.session_state.extraction_in_progress = False
                        update_pages()
                st.session_state.extraction_in_progress = False
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.extraction_finished = False
                st.session_state.extraction_in_progress = False
                update_pages()

# Function for "Data Preprocessing" page
def data_preprocessing():
    st.title("Data Preprocessing")

    if not st.session_state.extracted_attributes:
        st.error("No extracted data found. Please return to the previous step.")
        return

    # If user re-executes this step, reset subsequent steps
    st.session_state.model_trained = False
    st.session_state.prediction_made = False
    update_pages()

    # On entering the screen, send a request to the API with empty treatment options
    # to get initial preprocessing information
    if 'preprocessing_info' not in st.session_state:
        # Build an empty treatment_options dictionary with attributes
        treatment_options = {attr: {} for attr in st.session_state.extracted_attributes}
        payload = {'treatment_options': treatment_options}
        headers = {'Content-Type': 'application/json'}
        try:
            with st.spinner("Fetching preprocessing information..."):
                response = requests.post(f"{backend_url}/preprocess-data", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.preprocessing_info = data.get('analysis', {})
                else:
                    st.error(f"Error: {response.status_code}")
                    st.write(response.json())
                    return
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return

    # Options for each column
    missing_values_options = ['interpolate', 'drop', 'mean', 'median', 'ffill', 'bfill']
    outliers_options = ['', 'remove', 'cap']
    scaling_options = ['', 'minmax', 'standard']

    st.write("Select treatment options for each attribute:")
    treatment_options = {}
    for attribute in st.session_state.extracted_attributes:
        st.subheader(f"Attribute: {attribute}")
        missing_value_method = st.selectbox(
            f"How to treat missing values for {attribute}",
            missing_values_options,
            key=f"missing_{attribute}"
        )
        outlier_method = st.selectbox(
            f"How to treat outliers for {attribute}",
            outliers_options,
            key=f"outlier_{attribute}"
        )
        scaling_method = st.selectbox(
            f"How to scale data for {attribute}",
            scaling_options,
            key=f"scaling_{attribute}"
        )
        # Build the dictionary for this attribute
        treatment = {}
        treatment['missing_values'] = missing_value_method
        if outlier_method != '':
            treatment['outliers'] = outlier_method
        if scaling_method != '':
            treatment['scaling'] = scaling_method

        # Use concatenated name as key
        treatment_options[attribute] = treatment

    # Display the table with the preprocessing_info
    # Remove the 'timestamp' entry if present
    preprocessing_info = st.session_state.preprocessing_info.copy()
    preprocessing_info.pop('timestamp', None)

    # Convert the data to a DataFrame
    df = pd.DataFrame.from_dict(preprocessing_info, orient='index')
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Attribute'}, inplace=True)

    # Display the table
    st.subheader("Preprocessing Information")
    st.table(df)

    # Button to process data
    if st.button("Process Data"):
        payload = {'treatment_options': treatment_options}
        headers = {'Content-Type': 'application/json'}

        # Call preprocessing API
        try:
            with st.spinner("Processing data, please wait..."):
                response = requests.post(f"{backend_url}/preprocess-data", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    st.success("Data preprocessed successfully.")
                    # Update the preprocessing_info with the new data
                    st.session_state.preprocessing_info = data.get('analysis', {})
                    # Update the table with new preprocessing information
                    preprocessing_info = st.session_state.preprocessing_info.copy()
                    preprocessing_info.pop('timestamp', None)
                    df = pd.DataFrame.from_dict(preprocessing_info, orient='index')
                    df.reset_index(inplace=True)
                    df.rename(columns={'index': 'Attribute'}, inplace=True)
                    st.table(df)
                    st.session_state.data_preprocessed = True
                    update_pages()
                else:
                    st.error(f"Error: {response.status_code}")
                    st.write(response.json())
        except Exception as e:
            st.error(f"An error occurred: {e}")

    # Button to finalize data processing
    if st.button("Finalize Data Processing"):
        # Proceed to the next step without checking if data has been processed
        navigate_to('XGBoost Train')

# Function for "XGBoost Train" page
def xgboost_train():
    st.title("XGBoost Model Training")

    if not st.session_state.extracted_attributes:
        st.error("No extracted data found. Please return to the previous step.")
        return

    # If user re-executes this step, reset subsequent steps
    st.session_state.model_trained = False
    st.session_state.prediction_made = False
    update_pages()

    st.subheader("Model Training Parameters")

    # Field for target variable name with selectbox
    target_name = st.selectbox("Target Variable Name", st.session_state.extracted_attributes)

    # Forecast horizon
    forecast_horizon = st.number_input("Forecast Horizon (hours)", min_value=1, value=1, step=1)

    # Optional fields
    allowed_deviation = st.number_input("Allowed Deviation", value=0.0, step=0.1, format="%.2f")
    threshold_max = st.number_input("Maximum Allowed Value", value=0.0, step=0.1, format="%.2f")
    threshold_min = st.number_input("Minimum Allowed Value", value=0.0, step=0.1, format="%.2f")

    # Temporal Parameters (hidden by default)
    with st.expander("Temporal Parameters"):
        feature_flags = {}
        feature_flags['hour'] = st.checkbox("Hour", value=True)
        feature_flags['minute'] = st.checkbox("Minute", value=True)
        feature_flags['second'] = st.checkbox("Second", value=True)
        feature_flags['millisecond'] = st.checkbox("Millisecond", value=True)
        feature_flags['day_of_year'] = st.checkbox("Day of Year", value=True)
        feature_flags['week_of_year'] = st.checkbox("Week of Year", value=True)
        feature_flags['month'] = st.checkbox("Month", value=True)
        feature_flags['year'] = st.checkbox("Year", value=True)
        feature_flags['day_of_week'] = st.checkbox("Day of Week", value=True)
        feature_flags['quarter'] = st.checkbox("Quarter", value=True)
        feature_flags['is_weekend'] = st.checkbox("Is Weekend", value=True)
        feature_flags['trend'] = st.checkbox("Trend", value=True)
        feature_flags['seasonality'] = st.checkbox("Seasonality", value=True)
        feature_flags['denoise'] = st.checkbox("Denoise", value=True)
        feature_flags['cycles'] = st.checkbox("Cycles", value=True)

    # XGBoost Hyperparameters (hidden by default)
    with st.expander("XGBoost Hyperparameters"):
        xgboost_hyperparameters = {}
        xgboost_hyperparameters['n_estimators'] = st.number_input("n_estimators", min_value=1, value=100, step=1)
        xgboost_hyperparameters['learning_rate'] = st.number_input("learning_rate", min_value=0.0, max_value=1.0, value=0.1)
        xgboost_hyperparameters['max_depth'] = st.number_input("max_depth", min_value=1, value=6, step=1)
        xgboost_hyperparameters['subsample'] = st.number_input("subsample", min_value=0.0, max_value=1.0, value=1.0)
        xgboost_hyperparameters['colsample_bytree'] = st.number_input("colsample_bytree", min_value=0.0, max_value=1.0, value=1.0)
        xgboost_hyperparameters['gamma'] = st.number_input("gamma", min_value=0.0, value=0.0)
        xgboost_hyperparameters['reg_alpha'] = st.number_input("reg_alpha", min_value=0.0, value=0.0)
        xgboost_hyperparameters['reg_lambda'] = st.number_input("reg_lambda", min_value=0.0, value=1.0)
        xgboost_hyperparameters['min_child_weight'] = st.number_input("min_child_weight", min_value=0.0, value=1.0)

    # Button to train model
    if st.button("Train XGBoost Model"):
        if not target_name:
            st.error("Target Variable Name is required.")
        else:
            params = {
                "target_name": target_name,
                "allowed_deviation": allowed_deviation if allowed_deviation != 0.0 else None,
                "threshold_max": threshold_max if threshold_max != 0.0 else None,
                "threshold_min": threshold_min if threshold_min != 0.0 else None,
                "feature_flags": feature_flags,
                "xgboost_hyperparameters": xgboost_hyperparameters
            }
            # Remove keys with None values
            params = {k: v for k, v in params.items() if v is not None}
            headers = {'Content-Type': 'application/json'}
            try:
                with st.spinner("Training the model, please wait..."):
                    response = requests.post(f"{backend_url}/train-xgboost-model", headers=headers, json=params)
                    if response.status_code == 200:
                        data = response.json()
                        st.success("Model trained successfully.")
                        st.session_state.trained_model_info = data
                        st.session_state.model_trained = True
                        # Update pages after successful training
                        update_pages()
                        # Display detailed report
                        st.subheader("Training Report")
                        # Extract metrics from response
                        metrics = data.get('metrics', {})
                        st.write(f"**RMSE:** {metrics.get('rmse', 'N/A')}")
                        st.write(f"**MAPE:** {metrics.get('mape', 'N/A')}%")
                        st.write(f"**Anomalies Detected:** {metrics.get('anomalies_detected', 'N/A')}")
                        # Feature Importances
                        feature_importances = data.get('feature_importances', {})
                        if feature_importances:
                            # Convert to DataFrame
                            df_importances = pd.DataFrame.from_dict(feature_importances, orient='index', columns=['Importance'])
                            df_importances = df_importances.sort_values(by='Importance', ascending=False)
                            # Pie Chart
                            fig = go.Figure(data=[go.Pie(labels=df_importances.index, values=df_importances['Importance'])])
                            fig.update_layout(title='Feature Importance')
                            st.plotly_chart(fig)
                        # Automatically navigate to the next screen
                        navigate_to('Prediction and Anomaly Detection')
                    else:
                        st.error(f"Error: {response.status_code}")
                        st.write(response.json())
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Function for "Prediction and Anomaly Detection" page
def prediction_and_anomaly_detection():
    st.title("Prediction and Anomaly Detection")

    if not st.session_state.extracted_attributes:
        st.error("No extracted data found. Please return to the previous step.")
        return

    st.subheader("Prediction Parameters")

    # Field for target variable name with selectbox
    target_name = st.selectbox("Target Variable Name", st.session_state.extracted_attributes)

    # Forecast horizon
    forecast_horizon = st.number_input("Forecast Horizon (hours)", min_value=1, value=1, step=1)

    # Optional fields
    allowed_deviation = st.number_input("Allowed Deviation", value=0.0, step=0.1, format="%.2f")
    threshold_max = st.number_input("Maximum Allowed Value", value=0.0, step=0.1, format="%.2f")
    threshold_min = st.number_input("Minimum Allowed Value", value=0.0, step=0.1, format="%.2f")

    # Date range fields
    st.subheader("Date Range")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        date_from = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with date_col2:
        date_to = st.date_input("End Date", value=datetime.now())

    # Button to perform prediction
    if st.button("Perform Prediction and Anomaly Detection"):
        if not target_name:
            st.error("Target Variable Name is required.")
        else:
            # Convert dates to ISO 8601
            date_from_str = date_from.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            date_to_str = date_to.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            params = {
                "target_name": target_name,
                "forecast_horizon": int(forecast_horizon),
                "allowed_deviation": allowed_deviation if allowed_deviation != 0.0 else None,
                "threshold_max": threshold_max if threshold_max != 0.0 else None,
                "threshold_min": threshold_min if threshold_min != 0.0 else None,
                "date_from": date_from_str,
                "date_to": date_to_str
            }
            # Remove keys with None values
            params = {k: v for k, v in params.items() if v is not None}
            headers = {'Content-Type': 'application/json'}

            try:
                with st.spinner("Performing prediction and anomaly detection..."):
                    response = requests.post(f"{backend_url}/predict-and-anomaly-detection", headers=headers, json=params)
                    if response.status_code == 200:
                        result = response.json()
                        data = result.get('data', [])
                        st.session_state.prediction_info = result.get('metrics', {})
                        st.session_state.prediction_made = True
                        # Update pages
                        update_pages()

                        # Display precision metrics if available
                        if st.session_state.prediction_info:
                            st.subheader("Precision Metrics")
                            st.write(f"**RMSE:** {st.session_state.prediction_info.get('rmse', 'N/A')}")
                            st.write(f"**MAPE:** {st.session_state.prediction_info.get('mape', 'N/A')}%")
                            st.write(f"**Anomalies Detected:** {st.session_state.prediction_info.get('anomalies_detected', 'N/A')}")

                        # Convert data to DataFrame
                        final_data = pd.DataFrame(data)

                        # Check if DataFrame is not empty
                        if final_data.empty:
                            st.warning("No data returned by the API for the specified interval.")
                        else:
                            # Convert 'timestamp' to datetime with timezone awareness
                            final_data['timestamp'] = pd.to_datetime(final_data['timestamp'], utc=True)

                            # Separate historical and future data
                            historical_data = final_data[final_data['actual_data'].notnull()]
                            future_data = final_data[final_data['actual_data'].isnull()]

                            # Create interactive plot
                            fig = go.Figure()

                            # Add line for actual data
                            fig.add_trace(go.Scatter(
                                x=historical_data['timestamp'],
                                y=historical_data['actual_data'],
                                mode='lines',
                                name='Actual Data',
                                line=dict(color='blue')
                            ))

                            # Add line for predictions on historical data
                            fig.add_trace(go.Scatter(
                                x=historical_data['timestamp'],
                                y=historical_data['predicted_data'],
                                mode='lines',
                                name='Predictions',
                                line=dict(color='green')
                            ))

                            # Add markers for anomaly alerts on historical data
                            anomalies_hist = historical_data[historical_data['anomaly_alert']]
                            if not anomalies_hist.empty:
                                fig.add_trace(go.Scatter(
                                    x=anomalies_hist['timestamp'],
                                    y=anomalies_hist['actual_data'],
                                    mode='markers',
                                    name='Anomalies',
                                    marker=dict(color='red', size=10, symbol='x')
                                ))

                            # Add line for future predictions
                            fig.add_trace(go.Scatter(
                                x=future_data['timestamp'],
                                y=future_data['predicted_data'],
                                mode='lines',
                                name='Future Predictions',
                                line=dict(color='orange')
                            ))

                            # Add markers for anomaly alerts on future predictions
                            anomalies_future = future_data[future_data['anomaly_alert']]
                            if not anomalies_future.empty:
                                fig.add_trace(go.Scatter(
                                    x=anomalies_future['timestamp'],
                                    y=anomalies_future['predicted_data'],
                                    mode='markers',
                                    name='Future Anomalies',
                                    marker=dict(color='red', size=10, symbol='x')
                                ))

                            # Configure plot layout
                            fig.update_layout(
                                title='Actual Data, Predictions, and Anomalies',
                                xaxis_title='Timestamp',
                                yaxis_title='Variable Value',
                                legend_title='Legend',
                                hovermode='x unified',
                                template='plotly_white',
                                autosize=True
                            )

                            # Display plot in Streamlit
                            st.plotly_chart(fig, use_container_width=True)

                            # Display data table below the plot
                            with st.expander("View Data"):
                                st.dataframe(final_data)
                    else:
                        st.error(f"Error: {response.status_code}")
                        st.write(response.json())
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Display the selected page
if selected_page == "Home":
    home()
elif selected_page == "Attribute Selection":
    attribute_selection()
elif selected_page == "Data Preprocessing":
    data_preprocessing()
elif selected_page == "XGBoost Train":
    xgboost_train()
elif selected_page == "Prediction and Anomaly Detection":
    prediction_and_anomaly_detection()
