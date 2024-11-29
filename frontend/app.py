import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Definir a URL base do backend
backend_url = "http://api:5000"  # Substitua pela URL real do seu backend se diferente

# Inicializar o estado da sessão
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


# Função para navegar entre as telas
def navigate_to(page):
    if page not in st.session_state.pages:
        st.session_state.pages.append(page)  # Adiciona a página se não existir
    st.session_state.page = page
    st.rerun()


# Adicionar as telas à barra lateral sem separadores
selected_page = st.sidebar.radio(
    "Navegação",
    st.session_state.pages,
    index=st.session_state.pages.index(st.session_state.page)
)


# Função da tela "Home"
def home():
    st.title("Bem-vindo ao Sistema de Processamento de Dados")
    st.header("Verificando a saúde do backend...")
    # Fazer o health-check automaticamente
    try:
        response = requests.get(f"{backend_url}/health")
        if response.status_code == 200:
            data = response.json()
            st.success(f"Status: {data['status']}")
            st.write(f"Versão do Orion: {data.get('orion_version', 'N/A')}")
        else:
            st.error(f"Erro: {response.status_code}")
            st.write(response.json())
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

    st.subheader("Selecione o tipo de processo")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Processo Simplificado"):
            st.info("Processo Simplificado selecionado.")
            # Implementar lógica do processo simplificado se necessário
            navigate_to('Attribute Selection')
    with col2:
        if st.button("Processo Detalhado"):
            st.info("Processo Detalhado selecionado.")
            navigate_to('Attribute Selection')


# Função da tela "Attribute Selection"
def attribute_selection():
    st.title("Seleção de Atributos")

    # Verificar se os dados já foram coletados
    if 'mapping_data' not in st.session_state:
        st.write("Obtendo mapeamento de atributos...")
        try:
            response = requests.get(f"{backend_url}/attribute-mapping")
            if response.status_code == 200:
                mapping_data = response.json()
                st.session_state.mapping_data = mapping_data
                st.success("Mapeamento de atributos obtido com sucesso.")
            else:
                st.error(f"Erro: {response.status_code}")
                st.write(response.json())
                return
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
            return
    else:
        mapping_data = st.session_state.mapping_data

    # Remover a mensagem após os dados serem coletados
    st.empty()

    # Verificar se os dados foram realmente obtidos
    if not mapping_data or 'entities' not in mapping_data or not mapping_data['entities']:
        st.warning("Nenhum dado foi retornado pela API. Verifique se o backend está retornando dados corretamente.")
        return

    # Preparar dados para exibição na tabela
    attributes_list = []
    for entity in mapping_data.get('entities', []):
        entity_id = entity.get('entity_id')
        entity_type = entity.get('entity_type', 'type_unknown')  # Ajuste conforme necessário
        for attribute in entity.get('attributes', []):
            attributes_list.append({
                'Extract': False,
                'Attribute': attribute,
                'Entity': entity_id,
                'Type': entity_type
            })

    # Converter para DataFrame
    df_attributes = pd.DataFrame(attributes_list)

    if df_attributes.empty:
        st.warning("Nenhum atributo disponível para exibição.")
        return

    # Adicionar opção de selecionar/deselecionar todos
    select_all = st.checkbox("Selecionar/Deselecionar Todos", value=False)

    # Atualizar a coluna 'Extract' com base no checkbox 'select_all'
    df_attributes['Extract'] = select_all

    # Exibir tabela com checkboxes
    edited_df = st.data_editor(df_attributes, use_container_width=True)

    st.session_state.attributes = edited_df[edited_df['Extract']].to_dict('records')

    # Campo para limite de entidades oculto inicialmente
    with st.expander("Não vieram todas as entidades?"):
        limit = st.number_input("Informe um limite maior de entidades", min_value=1, value=100, step=1)
        if st.button("Mapear novamente"):
            try:
                params = {'limit': limit}
                response = requests.get(f"{backend_url}/attribute-mapping", params=params)
                if response.status_code == 200:
                    mapping_data = response.json()
                    st.session_state.mapping_data = mapping_data
                    st.rerun()
                else:
                    st.error(f"Erro: {response.status_code}")
                    st.write(response.json())
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")

    # Campos de data inicial e final
    st.subheader("Selecione o intervalo de datas para extração")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        date_from = st.date_input("Data Inicial", value=datetime(2016, 1, 1))
    with date_col2:
        date_to = st.date_input("Data Final", value=datetime(2025, 1, 31))

    # Botão para extrair dados
    if st.button("Extrair Dados"):
        if not st.session_state.attributes:
            st.error("Por favor, selecione pelo menos um atributo para extrair.")
        else:
            # Montar o payload para a API de extração
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

            # Salvar os parâmetros de extração no session_state
            st.session_state.extraction_payload = extraction_payload

            # Converter datas para ISO 8601
            date_from_str = date_from.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            date_to_str = date_to.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            st.session_state.extraction_params = {'date_from': date_from_str, 'date_to': date_to_str}

            st.session_state.extraction_finished = False
            st.session_state.extraction_in_progress = False

            # Atualizar extracted_attributes com o formato concatenado
            st.session_state.extracted_attributes = [f"{attr['Entity']}_{attr['Attribute']}" for attr in st.session_state.attributes]

            # Navegar para a tela "Wait Extraction"
            navigate_to('Wait Extraction')


# Função da tela "Wait Extraction"
def wait_extraction():
    st.title("Aguardando Extração de Dados")

    if not st.session_state.get('extraction_in_progress', False) and not st.session_state.extraction_finished:
        st.session_state.extraction_in_progress = True

        # Fazer a chamada à API de extração
        extraction_payload = st.session_state.extraction_payload
        params = st.session_state.extraction_params
        headers = {'Content-Type': 'application/json'}

        try:
            with st.spinner("Extraindo dados, por favor aguarde..."):
                response = requests.post(f"{backend_url}/extract-data", params=params, headers=headers, json=extraction_payload)
                if response.status_code == 200:
                    data = response.json()
                    st.success(data.get('message', 'Dados extraídos com sucesso.'))
                    st.session_state.extraction_finished = True
                else:
                    st.error(f"Erro: {response.status_code}")
                    st.write(response.json())
                    st.session_state.extraction_finished = False
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
            st.session_state.extraction_finished = False

        st.session_state.extraction_in_progress = False

    if st.session_state.extraction_finished:
        if st.button("Continuar"):
            navigate_to('Data Preprocessing')
    else:
        st.warning("A extração ainda não foi concluída.")
        if st.button("Voltar"):
            navigate_to('Attribute Selection')


# Função da tela "Data Preprocessing"
def data_preprocessing():
    st.title("Pré-processamento de Dados")

    if not st.session_state.extracted_attributes:
        st.error("Nenhum dado extraído encontrado. Por favor, retorne à etapa anterior.")
        return

    # Opções para cada coluna
    missing_values_options = ['interpolate', 'drop', 'mean', 'median', 'ffill', 'bfill']
    outliers_options = ['', 'remove', 'cap']
    scaling_options = ['', 'minmax', 'standard']

    st.write("Selecione as opções de tratamento para cada atributo:")
    treatment_options = {}
    for attribute in st.session_state.extracted_attributes:
        st.subheader(f"Atributo: {attribute}")
        missing_value_method = st.selectbox(
            f"Como tratar valores ausentes para {attribute}",
            missing_values_options,
            key=f"missing_{attribute}"
        )
        outlier_method = st.selectbox(
            f"Como tratar outliers para {attribute}",
            outliers_options,
            key=f"outlier_{attribute}"
        )
        scaling_method = st.selectbox(
            f"Como escalar os dados para {attribute}",
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

        # Usar o nome concatenado como chave
        treatment_options[attribute] = treatment

    # Botão para tratar dados
    if st.button("Tratar Dados"):
        payload = {'treatment_options': treatment_options}
        headers = {'Content-Type': 'application/json'}

        # Fazer a chamada à API de pré-processamento
        try:
            response = requests.post(f"{backend_url}/preprocess-data", headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                st.success("Dados pré-processados com sucesso.")
                st.json(data.get('analysis', {}))
                st.session_state.data_preprocessed = True
            else:
                st.error(f"Erro: {response.status_code}")
                st.write(response.json())
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")

    # Botão para finalizar tratamento
    if st.button("Finalizar Tratamento de Dados"):
        # Verificar se o tratamento já foi realizado
        if not st.session_state.data_preprocessed:
            # Antes de prosseguir, verificar se o tratamento de missing_values foi especificado
            missing_values_specified = all(
                'missing_values' in treatment_options[attr] and treatment_options[attr]['missing_values']
                for attr in treatment_options
            )
            if not missing_values_specified:
                st.error("Por favor, especifique o tratamento para valores ausentes antes de prosseguir.")
            else:
                # Chamar a API para realizar o tratamento
                payload = {'treatment_options': treatment_options}
                headers = {'Content-Type': 'application/json'}

                # Fazer a chamada à API de pré-processamento
                try:
                    response = requests.post(f"{backend_url}/preprocess-data", headers=headers, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        st.success("Dados pré-processados com sucesso.")
                        st.json(data.get('analysis', {}))
                        st.session_state.data_preprocessed = True
                        navigate_to('XGBoost Train')
                    else:
                        st.error(f"Erro: {response.status_code}")
                        st.write(response.json())
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")
        else:
            navigate_to('XGBoost Train')


# Função da tela "XGBoost Train"
def xgboost_train():
    st.title("Treinamento do Modelo XGBoost")

    if not st.session_state.extracted_attributes:
        st.error("Nenhum dado extraído encontrado. Por favor, retorne à etapa anterior.")
        return

    st.subheader("Parâmetros de Treinamento do Modelo")

    # Campo para nome da variável alvo com selectbox
    target_name = st.selectbox("Nome da Variável Alvo", st.session_state.extracted_attributes)

    # Horizonte de previsão
    forecast_horizon = st.number_input("Horizonte de Previsão (horas)", min_value=1, value=1, step=1)

    # Campos opcionais
    allowed_deviation = st.number_input("Desvio Permitido", value=0.0, step=0.1, format="%.2f")
    threshold_max = st.number_input("Valor Máximo Permitido", value=0.0, step=0.1, format="%.2f")
    threshold_min = st.number_input("Valor Mínimo Permitido", value=0.0, step=0.1, format="%.2f")

    # Temporal Parameters (ocultos por padrão)
    with st.expander("Parâmetros Temporais"):
        feature_flags = {}
        feature_flags['hour'] = st.checkbox("Hora", value=True)
        feature_flags['minute'] = st.checkbox("Minuto", value=True)
        feature_flags['second'] = st.checkbox("Segundo", value=True)
        feature_flags['millisecond'] = st.checkbox("Milissegundo", value=True)
        feature_flags['day_of_year'] = st.checkbox("Dia do Ano", value=True)
        feature_flags['week_of_year'] = st.checkbox("Semana do Ano", value=True)
        feature_flags['month'] = st.checkbox("Mês", value=True)
        feature_flags['year'] = st.checkbox("Ano", value=True)
        feature_flags['day_of_week'] = st.checkbox("Dia da Semana", value=True)
        feature_flags['quarter'] = st.checkbox("Trimestre", value=True)
        feature_flags['is_weekend'] = st.checkbox("É Fim de Semana", value=True)
        feature_flags['trend'] = st.checkbox("Tendência", value=True)
        feature_flags['seasonality'] = st.checkbox("Sazonalidade", value=True)
        feature_flags['denoise'] = st.checkbox("Remover Ruído", value=True)
        feature_flags['cycles'] = st.checkbox("Ciclos", value=True)

    # XGBoost Hyperparameters (ocultos por padrão)
    with st.expander("Hiperparâmetros do XGBoost"):
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

    # Botão para treinar modelo
    if st.button("Treinar Modelo XGBoost"):
        if not target_name:
            st.error("O Nome da Variável Alvo é obrigatório.")
        else:
            params = {
                "target_name": target_name,
                "allowed_deviation": allowed_deviation if allowed_deviation != 0.0 else None,
                "threshold_max": threshold_max if threshold_max != 0.0 else None,
                "threshold_min": threshold_min if threshold_min != 0.0 else None,
                "feature_flags": feature_flags,
                "xgboost_hyperparameters": xgboost_hyperparameters
            }
            # Remover chaves com valor None
            params = {k: v for k, v in params.items() if v is not None}
            headers = {'Content-Type': 'application/json'}
            try:
                response = requests.post(f"{backend_url}/train-xgboost-model", headers=headers, json=params)
                if response.status_code == 200:
                    data = response.json()
                    st.success("Modelo treinado com sucesso.")
                    st.json(data)
                    navigate_to('Prediction and Anomaly Detection')
                else:
                    st.error(f"Erro: {response.status_code}")
                    st.write(response.json())
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")


# Função da tela "Prediction and Anomaly Detection"
def prediction_and_anomaly_detection():
    st.title("Predição e Detecção de Anomalias")

    if not st.session_state.extracted_attributes:
        st.error("Nenhum dado extraído encontrado. Por favor, retorne à etapa anterior.")
        return

    st.subheader("Parâmetros de Predição")

    # Campo para nome da variável alvo com selectbox
    target_name = st.selectbox("Nome da Variável Alvo", st.session_state.extracted_attributes)

    # Horizonte de previsão
    forecast_horizon = st.number_input("Horizonte de Previsão (horas)", min_value=1, value=1, step=1)

    # Campos opcionais
    allowed_deviation = st.number_input("Desvio Permitido", value=0.0, step=0.1, format="%.2f")
    threshold_max = st.number_input("Valor Máximo Permitido", value=0.0, step=0.1, format="%.2f")
    threshold_min = st.number_input("Valor Mínimo Permitido", value=0.0, step=0.1, format="%.2f")

    # Campos de data inicial e final
    st.subheader("Intervalo de Datas")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        date_from = st.date_input("Data Inicial", value=datetime.now() - timedelta(days=30))
    with date_col2:
        date_to = st.date_input("Data Final", value=datetime.now())

    # Botão para realizar predição
    if st.button("Realizar Predição e Detecção de Anomalias"):
        if not target_name:
            st.error("O Nome da Variável Alvo é obrigatório.")
        else:
            # Converter datas para ISO 8601
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
            # Remover chaves com valor None
            params = {k: v for k, v in params.items() if v is not None}
            headers = {'Content-Type': 'application/json'}

            try:
                response = requests.post(f"{backend_url}/predict-and-anomaly-detection", headers=headers, json=params)
                if response.status_code == 200:
                    result = response.json()
                    data = result.get('data', [])

                    # Converter os dados em um DataFrame
                    final_data = pd.DataFrame(data)

                    # Verificar se o DataFrame não está vazio
                    if final_data.empty:
                        st.warning("Nenhum dado retornado pela API para o intervalo especificado.")
                    else:
                        # Converter 'timestamp' para datetime com consciência de fuso horário
                        final_data['timestamp'] = pd.to_datetime(final_data['timestamp'], utc=True)

                        # Separar dados históricos e futuros
                        historical_data = final_data[final_data['actual_data'].notnull()]
                        future_data = final_data[final_data['actual_data'].isnull()]

                        # Criar gráfico interativo
                        fig = go.Figure()

                        # Adicionar linha para dados reais
                        fig.add_trace(go.Scatter(
                            x=historical_data['timestamp'],
                            y=historical_data['actual_data'],
                            mode='lines',
                            name='Dados Reais',
                            line=dict(color='blue')
                        ))

                        # Adicionar linha para predições nos dados históricos
                        fig.add_trace(go.Scatter(
                            x=historical_data['timestamp'],
                            y=historical_data['predicted_data'],
                            mode='lines',
                            name='Predições',
                            line=dict(color='green')
                        ))

                        # Adicionar pontos para alertas de anomalias nos dados históricos
                        anomalies_hist = historical_data[historical_data['anomaly_alert']]
                        if not anomalies_hist.empty:
                            fig.add_trace(go.Scatter(
                                x=anomalies_hist['timestamp'],
                                y=anomalies_hist['actual_data'],
                                mode='markers',
                                name='Anomalias',
                                marker=dict(color='red', size=10, symbol='x')
                            ))

                        # Adicionar linha para predições futuras
                        fig.add_trace(go.Scatter(
                            x=future_data['timestamp'],
                            y=future_data['predicted_data'],
                            mode='lines',
                            name='Predições Futuras',
                            line=dict(color='orange')
                        ))

                        # Adicionar pontos para alertas de anomalias nas predições futuras
                        anomalies_future = future_data[future_data['anomaly_alert']]
                        if not anomalies_future.empty:
                            fig.add_trace(go.Scatter(
                                x=anomalies_future['timestamp'],
                                y=anomalies_future['predicted_data'],
                                mode='markers',
                                name='Anomalias Futuras',
                                marker=dict(color='red', size=10, symbol='x')
                            ))

                        # Configurar layout do gráfico
                        fig.update_layout(
                            title='Dados Reais, Predições e Anomalias',
                            xaxis_title='Timestamp',
                            yaxis_title='Valor da Variável',
                            legend_title='Legenda',
                            hovermode='x unified',
                            template='plotly_white',
                            autosize=True
                        )

                        # Exibir o gráfico no Streamlit
                        st.plotly_chart(fig, use_container_width=True)

                        # Exibir a tabela de dados abaixo do gráfico
                        st.dataframe(final_data)
                else:
                    st.error(f"Erro: {response.status_code}")
                    st.write(response.json())
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")


# Exibir a tela selecionada
if selected_page == "Home":
    home()
elif selected_page == "Attribute Selection":
    attribute_selection()
elif selected_page == "Wait Extraction":
    wait_extraction()
elif selected_page == "Data Preprocessing":
    data_preprocessing()
elif selected_page == "XGBoost Train":
    xgboost_train()
elif selected_page == "Prediction and Anomaly Detection":
    prediction_and_anomaly_detection()